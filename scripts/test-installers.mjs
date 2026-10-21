// End-to-end checks for install.sh and install.ps1 against a synthetic catalog
// served from loopback. Nothing is fetched from GitHub, Pages, or S3.
//
//   node --test scripts/test-installers.mjs
//
// Each scenario runs once per available shell (bash, pwsh, and Windows
// PowerShell on win32) and asserts on the installed tree, not on log text.
import assert from 'node:assert/strict';
import { execFile, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import AdmZip from 'adm-zip';

const root = process.env.SKILLS_TEST_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// Every fixture skill ships a reference file so a nested or partial copy
// shows up as an unexpected or missing path.
const BASE_SKILLS = ['alpha/one', 'alpha/two', 'beta/rag-tool', 'beta/rag-helper', 'beta/plain'];
const PROBE = 'alpha/probe';

function commandAvailable(command, args) {
  try {
    execFileSync(command, args, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

const shells = [];
if (commandAvailable('bash', ['-c', 'command -v unzip && command -v curl'])) shells.push('bash');
if (commandAvailable('pwsh', ['-NoProfile', '-Command', 'exit 0'])) shells.push('pwsh');
if (process.platform === 'win32' && commandAvailable('powershell.exe', ['-NoProfile', '-Command', 'exit 0'])) {
  shells.push('powershell.exe');
}

function skillFiles(ip) {
  return {
    'SKILL.md': `---\nname: ${path.posix.basename(ip)}\ndescription: Synthetic fixture for ${ip}.\n---\n\n# ${ip}\n`,
    'references/notes.md': `notes for ${ip}\n`,
  };
}

function manifestFor(ips, generatedAt) {
  const skills = ips.map((ip) => ({
    name: path.posix.basename(ip),
    category: ip.split('/')[0],
    install_path: ip,
    path: `skills/${ip}`,
    description: `Synthetic fixture for ${ip}.`,
  }));
  const tsv = ['install_path\tcategory\tname\tdescription',
    ...skills.map((s) => `${s.install_path}\t${s.category}\t${s.name}\t${s.description}`)].join('\n') + '\n';
  return { json: JSON.stringify({ generated_at: generatedAt, skills }, null, 2) + '\n', tsv };
}

function writeTree(dir, ips) {
  for (const ip of ips) {
    for (const [rel, body] of Object.entries(skillFiles(ip))) {
      const file = path.join(dir, ...ip.split('/'), ...rel.split('/'));
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, body);
    }
  }
}

function writeZip(outPath, entries) {
  const zip = new AdmZip();
  for (const [localDir, zipDir] of entries) zip.addLocalFolder(localDir, zipDir);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  zip.writeZip(outPath);
  const sha = createHash('sha256').update(fs.readFileSync(outPath)).digest('hex');
  fs.writeFileSync(`${outPath}.sha256`, `${sha}  ${path.basename(outPath)}\n`);
}

// Builds the three endpoints the installers read:
//   raw/main/docs/manifest.{tsv,json}   source manifest (raw.githubusercontent.com)
//   pages/{manifest.*,zips/**}          the deployed snapshot (GitHub Pages)
//   tarball/main                        codeload tarball of the source tree
function buildFixture(t, { raw, pages, archived = pages, tarball = raw, pagesManifest = true }) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'skills-installer-'));
  assert.equal(path.dirname(dir), path.resolve(os.tmpdir()));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));

  const rawManifest = manifestFor(raw, '2026-02-02T00:00:00.000Z');
  fs.mkdirSync(path.join(dir, 'raw/main/docs'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'raw/main/docs/manifest.json'), rawManifest.json);
  fs.writeFileSync(path.join(dir, 'raw/main/docs/manifest.tsv'), rawManifest.tsv);

  const pagesDir = path.join(dir, 'pages');
  const pagesSnapshot = manifestFor(pages, '2026-01-01T00:00:00.000Z');
  fs.mkdirSync(path.join(pagesDir, 'zips'), { recursive: true });
  if (pagesManifest) {
    fs.writeFileSync(path.join(pagesDir, 'manifest.json'), pagesSnapshot.json);
    fs.writeFileSync(path.join(pagesDir, 'manifest.tsv'), pagesSnapshot.tsv);
  }
  fs.writeFileSync(path.join(pagesDir, 'zips/_summary.json'), JSON.stringify({
    generated_at: '2026-01-01T00:00:00.000Z',
    public_base_url: null,
  }, null, 2) + '\n');

  const archiveSrc = path.join(dir, 'archive-src/skills');
  writeTree(archiveSrc, archived);
  for (const ip of archived) {
    writeZip(path.join(pagesDir, 'zips/skill', `${ip}.zip`), [[path.join(archiveSrc, ip), path.posix.basename(ip)]]);
  }
  for (const category of new Set(archived.map((ip) => ip.split('/')[0]))) {
    writeZip(path.join(pagesDir, 'zips/category', `${category}.zip`), [[path.join(archiveSrc, category), category]]);
  }
  writeZip(path.join(pagesDir, 'zips/all.zip'), [[archiveSrc, 'skills']]);

  const tarSrc = path.join(dir, 'tar-src');
  fs.mkdirSync(path.join(tarSrc, 'skills-main/skills'), { recursive: true });
  writeTree(path.join(tarSrc, 'skills-main/skills'), tarball);
  fs.mkdirSync(path.join(dir, 'tarball'));
  execFileSync('tar', ['-czf', '../tarball/main', 'skills-main'], { cwd: tarSrc });

  return dir;
}

async function serve(t, dir) {
  const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(dir, '.' + rel);
    if (!file.startsWith(dir + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404).end('not found');
      return;
    }
    const types = { '.json': 'application/json; charset=utf-8', '.tsv': 'text/tab-separated-values; charset=utf-8' };
    res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  return `http://127.0.0.1:${server.address().port}`;
}

function shellPath(shell, p) {
  return shell === 'bash' && process.platform === 'win32' && path.isAbsolute(p) ? p.replace(/\\/g, '/') : p;
}

const POWERSHELL_FLAGS = {
  '-d': '-Dest', '--all': '-All', '--dry-run': '-DryRun', '--flat': '-Flat', '--force': '-Force', '--list': '-List',
};

// args use install.sh spelling; PowerShell gets the equivalent parameters.
function runInstaller(shell, base, args) {
  const env = {
    ...process.env,
    SKILLS_RAW_BASE: `${base}/raw`,
    SKILLS_PAGES_BASE: `${base}/pages`,
    SKILLS_TARBALL_BASE: `${base}/tarball`,
  };
  delete env.SKILLS_DOWNLOAD_BASE;
  delete env.SKILLS_BRANCH;
  if (shell !== 'bash' && process.platform === 'win32' && process.env.SystemRoot) {
    // Match a normal PowerShell session: System32 tar.exe before any GNU tar
    // inherited from Git Bash, which misreads "C:\..." as a remote host.
    const pathKey = Object.keys(env).find((key) => key.toLowerCase() === 'path') || 'Path';
    env[pathKey] = `${path.join(process.env.SystemRoot, 'System32')};${env[pathKey]}`;
    // A PSModulePath inherited from PowerShell 7 hides Windows PowerShell's
    // own modules (Get-FileHash); a fresh session rebuilds it.
    for (const key of Object.keys(env)) if (key.toLowerCase() === 'psmodulepath') delete env[key];
  }
  const argv = shell === 'bash'
    ? [shellPath(shell, path.join(root, 'install.sh')), ...args.map((arg) => shellPath(shell, arg))]
    : ['-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', path.join(root, 'install.ps1'),
      ...args.map((arg) => POWERSHELL_FLAGS[arg] || arg)];
  return new Promise((resolve) => {
    execFile(shell, argv, { env, timeout: 120000 }, (error, stdout, stderr) => {
      resolve({ code: error ? (error.code ?? 1) : 0, stdout, output: `${stdout}\n${stderr}` });
    });
  });
}

function listTree(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  (function walk(current, prefix) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory()) walk(path.join(current, entry.name), rel);
      else out.push(rel);
    }
  })(dir, '');
  return out.sort();
}

// Expected installed files for a map of { targetRelativePath: installPath }.
function expectedTree(dest, targets) {
  const files = [];
  for (const [target, ip] of Object.entries(targets)) {
    for (const [rel, body] of Object.entries(skillFiles(ip))) {
      files.push(`${target}/${rel}`);
      assert.equal(fs.readFileSync(path.join(dest, ...target.split('/'), ...rel.split('/')), 'utf8'), body,
        `${target}/${rel} should be the published copy of ${ip}`);
    }
  }
  return files.sort();
}

function scratchDest(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'skills-installer-dest-'));
  assert.equal(path.dirname(dir), path.resolve(os.tmpdir()));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return path.join(dir, 'skills');
}

for (const shell of shells) {
  test(`${shell}: glob selector installs every match from per-skill ZIPs`, async (t) => {
    const base = await serve(t, buildFixture(t, { raw: BASE_SKILLS, pages: BASE_SKILLS }));
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['*rag*', '-d', dest, '--flat']);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), expectedTree(dest, { 'rag-tool': 'beta/rag-tool', 'rag-helper': 'beta/rag-helper' }));
  });

  test(`${shell}: plan comes from the deployed snapshot when the source manifest is newer`, async (t) => {
    // Between a merge and its deploy: raw main lists a skill the archives lack.
    const base = await serve(t, buildFixture(t, { raw: [...BASE_SKILLS, PROBE], pages: BASE_SKILLS }));
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['alpha', '-d', dest]);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), expectedTree(dest, { one: 'alpha/one', two: 'alpha/two' }));
  });

  test(`${shell}: an archive missing a planned skill falls back to the tarball before writing`, async (t) => {
    const all = [...BASE_SKILLS, PROBE];
    const base = await serve(t, buildFixture(t, { raw: all, pages: all, archived: BASE_SKILLS }));
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['alpha', '-d', dest]);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), expectedTree(dest, { one: 'alpha/one', probe: PROBE, two: 'alpha/two' }));
  });

  test(`${shell}: a missing per-skill ZIP falls back to the tarball before writing`, async (t) => {
    const all = [...BASE_SKILLS, 'beta/rag-zzz'];
    const base = await serve(t, buildFixture(t, { raw: all, pages: all, archived: BASE_SKILLS }));
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['*rag*', '-d', dest, '--flat']);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), expectedTree(dest, {
      'rag-helper': 'beta/rag-helper', 'rag-tool': 'beta/rag-tool', 'rag-zzz': 'beta/rag-zzz',
    }));
  });

  test(`${shell}: a skill missing from every source fails without writing anything`, async (t) => {
    const all = [...BASE_SKILLS, PROBE];
    const base = await serve(t, buildFixture(t, { raw: all, pages: all, archived: BASE_SKILLS, tarball: BASE_SKILLS }));
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['alpha', '-d', dest]);
    assert.notEqual(result.code, 0, result.output);
    assert.match(result.output, /alpha\/probe/);
    assert.equal(fs.existsSync(dest), false, `nothing should be written:\n${listTree(dest).join('\n')}`);
  });

  test(`${shell}: without a deployed manifest the source manifest and tarball are used together`, async (t) => {
    const all = [...BASE_SKILLS, PROBE];
    const base = await serve(t, buildFixture(t, { raw: all, pages: BASE_SKILLS, pagesManifest: false }));
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['alpha', '-d', dest]);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), expectedTree(dest, { one: 'alpha/one', probe: PROBE, two: 'alpha/two' }));
  });

  test(`${shell}: single skill and --all install from their scoped ZIPs`, async (t) => {
    // The tarball lacks every skill, so passing proves the ZIP route was used.
    const base = await serve(t, buildFixture(t, { raw: BASE_SKILLS, pages: BASE_SKILLS, tarball: [] }));
    const single = scratchDest(t);
    fs.mkdirSync(single, { recursive: true });
    let result = await runInstaller(shell, base, ['beta/plain', '-d', single]);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(single), expectedTree(single, { plain: 'beta/plain' }));

    const everything = scratchDest(t);
    result = await runInstaller(shell, base, ['--all', '-d', everything]);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(everything), expectedTree(everything, Object.fromEntries(BASE_SKILLS.map((ip) => [ip, ip]))));
  });

  test(`${shell}: --force replaces an existing install and --dry-run writes nothing`, async (t) => {
    const base = await serve(t, buildFixture(t, { raw: BASE_SKILLS, pages: BASE_SKILLS }));
    const dest = scratchDest(t);
    fs.mkdirSync(path.join(dest, 'one'), { recursive: true });
    fs.writeFileSync(path.join(dest, 'one', 'STALE.md'), 'old version\n');

    let result = await runInstaller(shell, base, ['alpha', '-d', dest]);
    assert.notEqual(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), ['one/STALE.md']);

    result = await runInstaller(shell, base, ['alpha', '-d', dest, '--force', '--dry-run']);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), ['one/STALE.md']);

    result = await runInstaller(shell, base, ['alpha', '-d', dest, '--force']);
    assert.equal(result.code, 0, result.output);
    assert.deepEqual(listTree(dest), expectedTree(dest, { one: 'alpha/one', two: 'alpha/two' }));
  });

  test(`${shell}: a checksum mismatch aborts without falling back or writing`, async (t) => {
    const fixture = buildFixture(t, { raw: BASE_SKILLS, pages: BASE_SKILLS });
    fs.writeFileSync(path.join(fixture, 'pages/zips/category/alpha.zip.sha256'), `${'0'.repeat(64)}  alpha.zip\n`);
    const base = await serve(t, fixture);
    const dest = scratchDest(t);
    const result = await runInstaller(shell, base, ['alpha', '-d', dest]);
    assert.notEqual(result.code, 0, result.output);
    assert.match(result.output, /checksum mismatch/);
    assert.doesNotMatch(result.output, /tarball/);
    assert.equal(fs.existsSync(dest), false);
  });

  test(`${shell}: --list shows the deployed snapshot the installer resolves against`, async (t) => {
    const base = await serve(t, buildFixture(t, { raw: [...BASE_SKILLS, PROBE], pages: BASE_SKILLS }));
    const result = await runInstaller(shell, base, ['--list']);
    assert.equal(result.code, 0, result.output);
    assert.match(result.stdout, /alpha\/one/);
    assert.doesNotMatch(result.stdout, /alpha\/probe/);
  });
}

test('at least one installer shell is available', () => {
  assert.ok(shells.length > 0, 'install bash (with curl and unzip) or PowerShell to run installer tests');
});
