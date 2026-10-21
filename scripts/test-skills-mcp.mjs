// Stdio checks for the local MCP server's install route against a synthetic
// Git checkout. Nothing is read from or written to the real catalog.
//
//   node --test scripts/test-skills-mcp.mjs
//
// Each test starts the server with --no-auto-refresh, speaks JSON-RPC over
// stdin/stdout, and asserts on the installed tree.
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = process.env.SKILLS_TEST_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const server = path.join(root, 'scripts', 'skills-mcp.mjs');

const SKILLS = [
  { name: 'dotnet-mcp-builder', category: 'mcp', install_path: 'mcp/dotnet-mcp-builder' },
  { name: 'tdd', category: 'coding', install_path: 'coding/tdd' },
];

// Tracked files. scripts/.coverage is tracked residue that no package ships.
const TRACKED = {
  'skills/mcp/dotnet-mcp-builder/SKILL.md': '---\nname: dotnet-mcp-builder\ndescription: Fixture.\n---\n',
  'skills/coding/tdd/SKILL.md': '---\nname: tdd\ndescription: Fixture.\n---\n',
  'skills/coding/tdd/references/guide.md': 'guide\n',
  'skills/coding/tdd/scripts/run.sh': 'echo run\n',
  'skills/coding/tdd/scripts/.coverage': 'SQLite format 3\n',
  '.gitignore': '__pycache__/\nnode_modules/\n',
};

// Local residue: untracked, or ignored by .gitignore.
const RESIDUE = {
  'skills/coding/tdd/.env': 'EXAMPLE_SETTING=local-only\n',
  'skills/coding/tdd/notes.md': 'local draft\n',
  'skills/coding/tdd/__pycache__/sentinel.cpython-312.pyc': 'pyc\n',
  'skills/coding/tdd/node_modules/sentinel/index.js': 'module.exports = 1;\n',
};

const PUBLISHED_TDD = ['SKILL.md', 'references/guide.md', 'scripts/run.sh'];

function tempDir(t, prefix) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), prefix));
  assert.equal(path.dirname(dir), path.resolve(os.tmpdir()));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

function writeFiles(dir, files) {
  for (const [rel, body] of Object.entries(files)) {
    const file = path.join(dir, ...rel.split('/'));
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, body);
  }
}

function buildRepo(t, { git = true } = {}) {
  const dir = tempDir(t, 'skills-mcp-');
  const manifest = {
    repo: 'example/skills',
    count: SKILLS.length,
    categories: ['coding', 'mcp'],
    counts_by_category: { coding: 1, mcp: 1 },
    skills: SKILLS.map((skill) => ({ ...skill, path: `skills/${skill.install_path}`, description: 'Fixture.' })),
  };
  writeFiles(dir, { ...TRACKED, 'docs/manifest.json': JSON.stringify(manifest, null, 2) + '\n' });
  if (git) {
    execFileSync('git', ['init', '-q'], { cwd: dir });
    // -f: a global excludes file may ignore .coverage; the fixture tracks it on purpose.
    execFileSync('git', ['-c', 'core.autocrlf=false', 'add', '-f', '--', ...Object.keys(TRACKED), 'docs/manifest.json'], { cwd: dir });
  }
  writeFiles(dir, RESIDUE);
  return dir;
}

function listTree(dir) {
  const out = [];
  (function walk(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) walk(full);
      else out.push(path.relative(dir, full).split(path.sep).join('/'));
    }
  })(dir);
  return out.sort();
}

// Sends initialize plus one tools/call per entry, then returns the tool
// results in order. Every stdout line must be a JSON-RPC message.
function callTools(repo, calls) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [server, '--no-auto-refresh'], {
      env: { ...process.env, SKILLS_REPO_ROOT: repo },
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', () => {
      try {
        const messages = stdout.split('\n').filter(Boolean).map((line) => JSON.parse(line));
        assert.equal(messages.length, calls.length + 1, `unexpected responses; stderr: ${stderr}`);
        resolve(messages.slice(1).map((message) => {
          const result = message.result;
          const text = result.content[0].text;
          return { isError: result.isError, text, value: result.isError ? null : JSON.parse(text) };
        }));
      } catch (error) {
        reject(error);
      }
    });
    const send = (id, method, params) => child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    send(0, 'initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'test', version: '0' } });
    calls.forEach(([name, args], index) => send(index + 1, 'tools/call', { name, arguments: args }));
    child.stdin.end();
  });
}

test('install_skill refuses a substring match and names the candidates', async (t) => {
  const repo = buildRepo(t);
  const dest = path.join(tempDir(t, 'skills-mcp-dest-'), 'skills');
  const [fuzzy, exactPath, exactName] = await callTools(repo, [
    ['install_skill', { skill: 'mcp-builder', destination: dest }],
    ['install_skill', { skill: 'mcp/dotnet-mcp-builder', destination: path.join(dest, 'by-path') }],
    ['install_skill', { skill: 'dotnet-mcp-builder', destination: path.join(dest, 'by-name') }],
  ]);
  assert.equal(fuzzy.isError, true);
  assert.match(fuzzy.text, /mcp\/dotnet-mcp-builder/);
  assert.equal(exactPath.isError, false, exactPath.text);
  assert.equal(exactName.isError, false, exactName.text);
  assert.deepEqual(fs.readdirSync(dest).sort(), ['by-name', 'by-path']);
  assert.deepEqual(listTree(path.join(dest, 'by-path', 'dotnet-mcp-builder')), ['SKILL.md']);
});

test('read tools report how a skill reference was matched', async (t) => {
  const repo = buildRepo(t);
  const [fuzzy, exact] = await callTools(repo, [
    ['get_skill', { skill: 'mcp-builder', preview_chars: 0 }],
    ['read_skill_doc', { skill: 'coding/tdd' }],
  ]);
  assert.equal(fuzzy.value.skill.install_path, 'mcp/dotnet-mcp-builder');
  assert.equal(fuzzy.value.matched_by, 'substring');
  assert.equal(exact.value.matched_by, 'exact');
});

test('install_skill copies only the published files of a Git checkout', async (t) => {
  const repo = buildRepo(t);
  const dest = tempDir(t, 'skills-mcp-dest-');
  const [result] = await callTools(repo, [['install_skill', { skill: 'coding/tdd', destination: dest }]]);
  assert.equal(result.isError, false, result.text);
  assert.equal(result.value.file_selection, 'git-index');
  assert.deepEqual(listTree(path.join(dest, 'tdd')), PUBLISHED_TDD);
  assert.ok(result.value.skipped_untracked.includes('notes.md'));
  assert.deepEqual(fs.readdirSync(dest), ['tdd']);
});

test('install_skill overwrite replaces the folder instead of merging', async (t) => {
  const repo = buildRepo(t);
  const dest = tempDir(t, 'skills-mcp-dest-');
  const stale = path.join(dest, 'tdd', 'STALE-FROM-OLD-VERSION.md');
  const [first] = await callTools(repo, [['install_skill', { skill: 'coding/tdd', destination: dest }]]);
  assert.equal(first.isError, false, first.text);
  fs.writeFileSync(stale, 'old\n');

  const [refused, replaced] = await callTools(repo, [
    ['install_skill', { skill: 'coding/tdd', destination: dest }],
    ['install_skill', { skill: 'coding/tdd', destination: dest, overwrite: true }],
  ]);
  assert.equal(refused.isError, true);
  assert.match(refused.text, /Destination exists/);
  assert.equal(replaced.isError, false, replaced.text);
  assert.deepEqual(listTree(path.join(dest, 'tdd')), PUBLISHED_TDD);
  assert.deepEqual(fs.readdirSync(dest), ['tdd'], 'no staging or backup folder left behind');
});

test('install_skill refuses a destination that overlaps the skill source', async (t) => {
  const repo = buildRepo(t);
  // The first target is the source folder itself; the second sits inside it.
  const [sameFolder, insideSource] = await callTools(repo, [
    ['install_skill', { skill: 'coding/tdd', destination: path.join(repo, 'skills', 'coding'), overwrite: true }],
    ['install_skill', { skill: 'coding/tdd', destination: path.join(repo, 'skills', 'coding', 'tdd'), overwrite: true }],
  ]);
  assert.equal(sameFolder.isError, true);
  assert.match(sameFolder.text, /overlaps the skill source/);
  assert.equal(insideSource.isError, true);
  assert.match(insideSource.text, /overlaps the skill source/);
  assert.ok(fs.existsSync(path.join(repo, 'skills', 'coding', 'tdd', 'notes.md')), 'source left untouched');
  assert.ok(!fs.existsSync(path.join(repo, 'skills', 'coding', 'tdd', 'tdd')));
});

test('install_skill applies the exclusion policy outside a Git checkout', async (t) => {
  const repo = buildRepo(t, { git: false });
  const dest = tempDir(t, 'skills-mcp-dest-');
  const [result] = await callTools(repo, [['install_skill', { skill: 'coding/tdd', destination: dest }]]);
  assert.equal(result.isError, false, result.text);
  assert.equal(result.value.file_selection, 'exclusion-policy');
  assert.deepEqual(listTree(path.join(dest, 'tdd')), [...PUBLISHED_TDD, 'notes.md'].sort());
});
