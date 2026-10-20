import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { Page } from '../skills/design-and-ui/design-taste-frontend/scripts/lib/cdp.mjs';

const root = process.env.SKILLS_TEST_ROOT || path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { isGeneratedFile } = await import(pathToFileURL(path.join(root,
  'skills/design-and-ui/impeccable/scripts/is-generated.mjs')));

test('CDP evaluation preserves argument serialization and returned values', async () => {
  let request;
  const page = Object.create(Page.prototype);
  page.send = async (...args) => {
    request = args;
    return { result: { value: { ok: true } } };
  };
  const argument = 'quotes" and \\ paths';
  const fn = (value) => value.length;
  assert.deepEqual(await page.evaluate(fn, argument), { ok: true });
  assert.equal(request[0], 'Runtime.evaluate');
  assert.equal(request[1].expression, `(${fn.toString()})(${JSON.stringify(argument)})`);
  assert.equal(request[1].awaitPromise, true);
  assert.equal(request[1].returnByValue, true);
  assert.equal(request[2], 30000);
});

test('CDP evaluation passes expressions through and propagates browser exceptions', async () => {
  const page = Object.create(Page.prototype);
  page.send = async (_method, params) => {
    assert.equal(params.expression, 'document.title');
    return { exceptionDetails: { text: 'browser error' } };
  };
  await assert.rejects(page.evaluate('document.title'), /browser error/);
});

function temporaryProject(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'skills-subprocess-'));
  assert.equal(path.dirname(dir), path.resolve(os.tmpdir()));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

test('git ignore detection treats shell substitutions as literal filenames', (t) => {
  const cwd = temporaryProject(t);
  execFileSync('git', ['init', '--quiet', cwd]);
  fs.writeFileSync(path.join(cwd, '.gitignore'), '*.js\n');
  const filename = '$(touch SCANNER_INJECTION_SENTINEL).js';
  fs.writeFileSync(path.join(cwd, filename), '// normal source\n');
  assert.equal(isGeneratedFile(filename, { cwd }), true);
  assert.equal(fs.existsSync(path.join(cwd, 'SCANNER_INJECTION_SENTINEL')), false);
  fs.writeFileSync(path.join(cwd, 'source.txt'), 'normal source\n');
  assert.equal(isGeneratedFile('source.txt', { cwd }), false);
});

test('brand generator runs from paths containing spaces and shell metacharacters', (t) => {
  const dir = temporaryProject(t);
  const cwd = path.join(dir, 'brand project & literal $tokens');
  fs.mkdirSync(path.join(cwd, 'docs'), { recursive: true });
  fs.mkdirSync(path.join(cwd, 'assets'));
  fs.writeFileSync(path.join(cwd, 'docs/brand-guidelines.md'), [
    '| Primary Color | #112233 (Ocean) |',
    '| Secondary Color | #445566 (Stone) |',
    '| Accent Color | #778899 (Sky) |',
  ].join('\n'));
  fs.writeFileSync(path.join(cwd, 'assets/design-tokens.json'), '{"primitive":{"color":{}}}');
  const generatorDir = path.join(cwd, '.claude/skills/design-system/scripts');
  fs.mkdirSync(generatorDir, { recursive: true });
  fs.writeFileSync(path.join(generatorDir, 'generate-tokens.cjs'),
    "require('node:fs').writeFileSync('generator-args.json', JSON.stringify(process.argv.slice(2)));\n");
  execFileSync(process.execPath, [path.join(root, 'skills/design-and-ui/brand/scripts/sync-brand-to-tokens.cjs')], { cwd, env: { ...process.env, PATH: dir } });
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(cwd, 'generator-args.json'), 'utf8')),
    ['--config', 'assets/design-tokens.json', '-o', 'assets/design-tokens.css']);
});

test('live CLI launches its helper from a skill path containing spaces and dollar signs', (t) => {
  const dir = temporaryProject(t);
  const cwd = path.join(dir, 'project');
  const scripts = path.join(dir, 'skill scripts $literal');
  fs.mkdirSync(cwd);
  fs.cpSync(path.join(root, 'skills/design-and-ui/impeccable/scripts'), scripts, { recursive: true });
  const output = execFileSync(process.execPath, [path.join(scripts, 'live.mjs')], {
    cwd,
    encoding: 'utf8',
    env: { ...process.env, PATH: dir },
    timeout: 20000,
  });
  const result = JSON.parse(output);
  assert.equal(result.ok, false);
  assert.equal(result.error, 'config_missing');
});
