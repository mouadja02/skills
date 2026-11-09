// Every example selector shown on the site, in the installer help and in the
// SkillBot prompt must resolve against the checked-in manifest, using the same
// rules as the installers: exact install_path, then category, then glob.
// Selectors are extracted from the files themselves, so a stale example fails
// whether or not it is still present in a hand-maintained list.
//
//   node --test scripts/test-examples.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const manifest = JSON.parse(read('docs/manifest.json'));
const installPaths = manifest.skills.map((s) => s.install_path);
const categories = new Set(manifest.skills.map((s) => s.category));

// A selector token: a path or category, optionally with glob characters.
const SHAPE = /^[a-z0-9*?][a-z0-9*?._/-]*$/i;

function resolves(selector) {
  if (installPaths.includes(selector)) return true;
  if (categories.has(selector)) return true;
  if (/[*?]/.test(selector)) {
    const re = new RegExp(
      '^' + selector.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*').replace(/\?/g, '.') + '$',
    );
    return installPaths.some((p) => re.test(p));
  }
  return false;
}

function unquote(tok) {
  return tok.replace(/^["']|["']$/g, '');
}

// Argument tokens of installer invocations, skipping flags and their values.
function invocationSelectors(lines, commandRe) {
  const out = [];
  for (const line of lines) {
    if (line.includes('`')) continue; // prose mentioning a command, not an invocation
    const m = line.match(commandRe);
    if (!m) continue;
    let skipNext = false;
    // Only the command's own arguments: stop at a pipe, chain or comment.
    const args = m[1].split(/\s*(?:\||&&|#)/)[0];
    for (const raw of args.split(/\s+/)) {
      if (skipNext) { skipNext = false; continue; }
      if (/^(-d|--dest|-dest|-Dest)$/.test(raw)) { skipNext = true; continue; }
      const tok = unquote(raw);
      if (SHAPE.test(tok)) out.push(tok);
    }
  }
  return out;
}

// Selectors from the hero "anatomy" block in docs/app.js.
function heroSelectors() {
  const src = read('docs/app.js');
  const block = src.slice(src.indexOf('const ANATOMY = {'), src.indexOf('function bindAnatomy'));
  return [...block.matchAll(/selector:\s*(["'])(.*?)\1/g)].map((m) => unquote(m[2]));
}

// install.sh: the SELECTORS help block plus install.sh invocations.
function installShSelectors() {
  const lines = read('install.sh').split('\n');
  const start = lines.findIndex((l) => l === 'SELECTORS');
  const end = lines.findIndex((l) => l.startsWith('  All skills'));
  const help = [];
  for (const l of lines.slice(start, end)) {
    const m = l.match(/^ {6}(\S+)/);
    if (m && SHAPE.test(unquote(m[1]))) help.push(unquote(m[1]));
  }
  return [...help, ...invocationSelectors(lines, /^\s{2,}(?:bash\s+)?install\.sh\s+(.*)$/)];
}

// install.ps1: the .DESCRIPTION selector block plus Install-Skill / $installer calls.
function installPs1Selectors() {
  const lines = read('install.ps1').split('\n');
  const start = lines.findIndex((l) => l.trim() === '.DESCRIPTION');
  const end = lines.findIndex((l, i) => i > start && l.includes('For single-skill mode'));
  const help = [];
  for (const l of lines.slice(start, end)) {
    if (!/^ {12}\S/.test(l)) continue;
    for (const tok of l.trim().split(/\s+/)) {
      if (SHAPE.test(unquote(tok))) help.push(unquote(tok));
    }
  }
  return [
    ...help,
    ...invocationSelectors(lines, /^\s*(?:&\s+\$installer|Install-Skill|\$installer)\s+(.*)$/),
  ];
}

// docs/chat.js: backticked selectors in the SkillBot selector-format and style lines.
function chatSelectors() {
  const lines = read('docs/chat.js').split('\n');
  const out = [];
  for (const l of lines) {
    if (!/Single skill|Whole category|Glob pattern|exact selector/.test(l)) continue;
    // The prompt lives in a template literal, so its backticks are escaped.
    for (const m of l.matchAll(/\\`(.+?)\\`/g)) {
      const tok = unquote(m[1]);
      if (SHAPE.test(tok)) out.push(tok);
    }
  }
  return out;
}

const EXAMPLE_SOURCES = {
  'install.sh': installShSelectors,
  'install.ps1': installPs1Selectors,
  'docs/chat.js': chatSelectors,
};

test('hero example selectors in docs/app.js resolve', () => {
  const selectors = heroSelectors();
  assert.ok(selectors.length >= 3, 'expected hero ANATOMY selectors to be extracted');
  for (const sel of selectors) {
    assert.ok(resolves(sel), `example selector "${sel}" in docs/app.js does not resolve to any skill`);
  }
});

for (const [file, extract] of Object.entries(EXAMPLE_SOURCES)) {
  test(`example selectors in ${file} resolve`, () => {
    const selectors = extract();
    assert.ok(selectors.length >= 3, `expected example selectors to be extracted from ${file}`);
    for (const sel of selectors) {
      assert.ok(resolves(sel), `example selector "${sel}" in ${file} does not resolve to any skill`);
    }
  });
}
