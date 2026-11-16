// Regression tests for the skill detail panel's Markdown renderer (sdMdToHtml
// in docs/app.js): it must always finish, and the links it emits must be safe
// and point at the right file on GitHub.
//
// Run with:
//   node --test scripts/test-skill-detail-renderer.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { loadApp, REPO_ROOT } from './lib/app-vm.mjs';

const app = loadApp();
const BASE = { repo: 'octo/skills', branch: 'main', path: 'skills/cat/demo/SKILL.md' };
const BLOB = 'https://github.com/octo/skills/blob/main/';

// The renderer runs on the page's main thread, so a runaway loop freezes the
// tab. A per-call time limit turns that into a test failure.
const LIMIT_MS = 1500;
function render(md, base = BASE) {
  return app.call('sdMdToHtml', [md, base], LIMIT_MS);
}
const hrefs = (html) => [...html.matchAll(/<a href="([^"]*)"/g)].map((m) => m[1]);
const unescapeAttr = (s) => s
  .replaceAll('&quot;', '"').replaceAll('&#39;', "'")
  .replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&amp;', '&');

// ── Progress: a "|" line that is not a table must render as text ───────────

test('a lone "|" line renders as text instead of hanging', () => {
  const html = render('| a');
  assert.match(html, /<p class="sd-p">\| a<\/p>/);
});

test('"|" lines that are not tables render as text between other blocks', () => {
  for (const md of [
    'intro\n\n| Col | Col |\nmore',
    '    | Col | Col |',
    '| a |\n| b |',
    'text\n| a\ntext',
  ]) {
    const html = render(md);
    assert.ok(html.length > 0, JSON.stringify(md));
    assert.doesNotMatch(html, /<table/, JSON.stringify(md));
  }
});

test('long lines of unmatched brackets and backticks finish quickly', () => {
  // The renderer runs on the page's main thread: a hostile line must cost a
  // bounded scan per character, not a scan to the end of the line.
  for (const md of ['['.repeat(40000), '[`'.repeat(40000), '[a](b '.repeat(20000), '| a\n'.repeat(20000)]) {
    const start = performance.now();
    render(md);
    const ms = performance.now() - start;
    assert.ok(ms < 1000, `${JSON.stringify(md.slice(0, 12))}… took ${Math.round(ms)} ms`);
  }
});

test('a link label over the length bound is shown as text, not as a link', () => {
  const html = render(`[${'a'.repeat(1200)}](references/a.md) [ok](references/a.md)`);
  assert.equal(hrefs(html).length, 1);
  assert.match(html, /a{1200}\]\(references\/a\.md\)/);
});

test('real tables still render as tables, including after a stray "|" line', () => {
  const table = '| a | b |\n|---|---|\n| 1 | 2 |';
  assert.match(render(table), /<table class="sd-table">.*<th>a<\/th>.*<td>2<\/td>/s);
  assert.match(render(`| stray\n\n${table}`), /<p class="sd-p">\| stray<\/p>[\s\S]*<table/);
  assert.match(render(`intro\n${table}`), /<p class="sd-p">intro<\/p>\n<div class="sd-table-wrap">/);
});

// Every tracked Markdown file under skills/ is something a visitor can open in
// the panel (SKILL.md directly, bundled files through the file tree).
const tracked = execFileSync('git', ['ls-files', '-z', 'skills'], {
  cwd: REPO_ROOT, encoding: 'utf8', maxBuffer: 1 << 28,
}).split('\0').filter(Boolean);
const trackedSet = new Set(tracked);
const trackedDirs = new Set(tracked.flatMap((f) => {
  const parts = f.split('/');
  return parts.slice(1, -1).map((_, i) => parts.slice(0, i + 2).join('/'));
}));
const markdown = tracked.filter((f) => /\.md$/i.test(f));

test('the renderer finishes on every tracked Markdown file under skills/', () => {
  assert.ok(markdown.length > 1000, `expected the full catalog, found ${markdown.length} files`);
  const hung = [];
  for (const file of markdown) {
    const md = readFileSync(path.join(REPO_ROOT, file), 'utf8');
    try {
      render(md, { ...BASE, path: file });
    } catch (err) {
      hung.push(`${file}: ${err.code ?? err.message}`);
    }
  }
  assert.deepEqual(hung, []);
});

// ── Links: scheme allowlist, one round of escaping, repository-relative ────

test('relative links open the file on GitHub, including names with underscores', () => {
  assert.deepEqual(hrefs(render('[ref](references/my_file_name.md)')),
    [`${BLOB}skills/cat/demo/references/my_file_name.md`]);
  assert.deepEqual(hrefs(render('[s](./scripts/run.sh)')), [`${BLOB}skills/cat/demo/scripts/run.sh`]);
  assert.deepEqual(hrefs(render('[up](../other/SKILL.md)')), [`${BLOB}skills/cat/other/SKILL.md`]);
  assert.deepEqual(hrefs(render('[f](references/a.md#part)')), [`${BLOB}skills/cat/demo/references/a.md#part`]);
  assert.doesNotMatch(render('[ref](references/my_file_name.md)'), /<em>/);
});

test('links in a bundled file resolve against that file, not the skill root', () => {
  const base = { ...BASE, path: 'skills/cat/demo/references/deep.md' };
  assert.deepEqual(hrefs(render('[a](sibling.md) [b](../SKILL.md)', base)), [
    `${BLOB}skills/cat/demo/references/sibling.md`,
    `${BLOB}skills/cat/demo/SKILL.md`,
  ]);
});

test('same-file anchors keep the GitHub URL and name the heading to jump to', () => {
  const html = render('[Install](#Install Steps)');
  assert.match(html, new RegExp(`<a href="${BLOB.replaceAll('.', '\\.')}skills/cat/demo/SKILL\\.md#Install%20Steps" data-sd-anchor="install-steps"`));
});

test('URLs are escaped exactly once', () => {
  const html = render('[go](https://example.com/p?a=1&b=2) and [Tom & Jerry](https://example.com/x)');
  assert.ok(html.includes('href="https://example.com/p?a=1&amp;b=2"'), html);
  assert.ok(html.includes('>Tom &amp; Jerry</a>'), html);
  assert.doesNotMatch(html, /&amp;amp;/);
});

test('only http, https and mailto links become anchors', () => {
  assert.deepEqual(hrefs(render('[a](http://example.com/a) [b](https://example.com/b) [c](mailto:me@example.com)')), [
    'http://example.com/a', 'https://example.com/b', 'mailto:me@example.com',
  ]);
  for (const url of [
    'javascript:alert(1)',
    'JavaScript:alert(1)',
    ' javascript:alert(1)',
    'java\tscript:alert(1)',
    'data:text/html,hi',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
    'blob:https://example.com/x',
    '//evil.example/x',
    '/etc/passwd',
    '../../../../../../../../../etc/passwd',
    '..\\..\\..\\..\\..\\..\\..\\..\\etc\\passwd',
    '%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd',
  ]) {
    const html = render(`[label](${url})`);
    assert.doesNotMatch(html, /<a /, `${JSON.stringify(url)} became an anchor: ${html}`);
    assert.match(html, /label/, `${JSON.stringify(url)} lost its link text`);
  }
});

test('without a base, relative links are text and absolute ones still work', () => {
  const html = app.call('sdMdToHtml', ['[r](references/a.md) [x](https://example.com)'], LIMIT_MS);
  assert.deepEqual(hrefs(html), ['https://example.com/']);
  assert.match(html, /r <a /);
});

test('links keep working inside emphasis, headings, lists and tables; code spans stay code', () => {
  assert.match(render('**[bold](https://example.com)**'), /<strong><a href="https:\/\/example\.com\/"[^>]*>bold<\/a><\/strong>/);
  assert.match(render('## See [the guide](references/guide.md)'), /<h2[^>]*>See <a href="[^"]*references\/guide\.md"/);
  assert.match(render('- [item](references/x.md)'), /<li><a href="[^"]*references\/x\.md"/);
  assert.match(render('| h |\n|---|\n| [cell](references/x.md) |'), /<td><a href="[^"]*references\/x\.md"/);
  assert.match(render('[`code`](references/x.md)'), /<a [^>]*><code class="sd-ic">code<\/code><\/a>/);
  assert.doesNotMatch(render('`[a](references/b.md)`'), /<a /);
});

test('link titles and angle brackets do not leak into the target', () => {
  assert.deepEqual(hrefs(render('[t](references/a.md "Title") [u](<references/b.md>)')), [
    `${BLOB}skills/cat/demo/references/a.md`,
    `${BLOB}skills/cat/demo/references/b.md`,
  ]);
});

test('text that imitates the renderer\'s internal placeholders is not expanded', () => {
  // Spans are lifted out of a line behind private-use markers; Markdown that
  // contains those markers itself must not be able to pull a lifted span out.
  const open = String.fromCharCode(0xe000);
  const close = String.fromCharCode(0xe001);
  const html = render(`${open}0${close} \`code\` ${open}1${close} [l](https://example.com)`);
  assert.equal((html.match(/<code/g) || []).length, 1);
  assert.equal(hrefs(html).length, 1);
  assert.ok(!html.includes(open) && !html.includes(close), 'markers must not survive into the output');
  assert.match(html, /0 <code class="sd-ic">code<\/code> 1 <a /);
});

test('the emitted anchor opens in a new tab without an opener', () => {
  assert.match(render('[x](https://example.com)'), /<a href="https:\/\/example\.com\/" target="_blank" rel="noopener">x<\/a>/);
});

// ── Links in the real catalog ──────────────────────────────────────────────
// check-skills guarantees that relative links in a SKILL.md resolve inside the
// repository. The panel must therefore render each of them as a link to that
// exact file. The expected targets come from a separate, simpler extractor
// (prose only: fenced blocks, inline code and images are skipped).

function proseLinkTargets(md) {
  // A fence opens and closes on lines that start with ``` (an unbalanced file
  // is code from its last fence to the end, as on GitHub and in the panel).
  const prose = [];
  let fenced = false;
  for (const line of md.replace(/^---[\s\S]*?---\n?/, '').split('\n')) {
    if (line.trim().startsWith('```')) { fenced = !fenced; continue; }
    if (!fenced) prose.push(line);
  }
  return [...prose.join('\n')
    .replace(/`[^`\n]*`/g, '')
    .matchAll(/(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)/g)].map((m) => m[1]);
}

test('every relative link in every tracked SKILL.md renders as a link to its file', (t) => {
  const problems = [];
  let expected = 0;
  for (const file of tracked.filter((f) => f.endsWith('/SKILL.md'))) {
    const md = readFileSync(path.join(REPO_ROOT, file), 'utf8');
    const html = render(md, { ...BASE, path: file });
    const rendered = new Set(hrefs(html).map((h) => {
      const u = new URL(unescapeAttr(h));
      return u.href.startsWith(BLOB)
        ? decodeURIComponent(u.pathname).replace('/octo/skills/blob/main/', '').replace(/\/$/, '')
        : null;
    }).filter(Boolean));

    for (const h of hrefs(html)) {
      const url = unescapeAttr(h);
      if (!/^(https?:|mailto:)/i.test(url)) problems.push(`${file}: non-absolute href ${url}`);
    }

    for (const raw of proseLinkTargets(md)) {
      if (/^[a-z][a-z0-9+.-]*:/i.test(raw) || raw.startsWith('#') || raw.startsWith('/')) continue;
      const target = raw.split(/[#?]/)[0];
      if (!target) continue;
      const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(file), target)).replace(/\/$/, '');
      if (!trackedSet.has(resolved) && !trackedDirs.has(resolved)) continue; // placeholder, not a real file
      expected++;
      if (!rendered.has(resolved)) problems.push(`${file}: [${raw}] did not render as a link to ${resolved}`);
    }
  }
  t.diagnostic(`checked ${expected} relative links that resolve to tracked files`);
  assert.ok(expected > 1000, `expected a large sample of relative links, found ${expected}`);
  assert.deepEqual(problems.slice(0, 20), []);
});
