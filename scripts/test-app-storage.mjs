// Regression test: the catalog script must still start when the browser
// refuses access to localStorage (blocked site data, some privacy modes).
//
// Run with:
//   node --test scripts/test-app-storage.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const source = readFileSync(path.join(here, '..', 'docs', 'app.js'), 'utf8');

// A permissive DOM stub: any property is another stub, any call returns one.
function stub(label) {
  const fn = function () { return stub(`${label}()`); };
  return new Proxy(fn, {
    get(target, prop) {
      if (Object.hasOwn(target, prop)) return target[prop];
      if (prop === Symbol.iterator) return function* () {};
      if (prop === Symbol.toPrimitive) return () => '';
      if (prop === 'then') return undefined;
      if (prop === 'matches') return false;
      return stub(`${label}.${String(prop)}`);
    },
    set(target, prop, value) { target[prop] = value; return true; },
  });
}

function loadApp() {
  const attrs = new Map();
  const handlers = {};
  const toggle = stub('themeToggle');
  Object.assign(toggle, {
    addEventListener(type, fn) { handlers[type] = fn; },
    setAttribute() {},
  });
  const documentElement = {
    setAttribute(k, v) { attrs.set(k, String(v)); },
    getAttribute(k) { return attrs.has(k) ? attrs.get(k) : null; },
  };
  const fetchCalls = [];
  const document = new Proxy({
    documentElement,
    querySelector: (sel) => (sel === '#themeToggle' ? toggle : stub(sel)),
    querySelectorAll: () => [],
  }, {
    get(target, prop) {
      return prop in target ? target[prop] : stub(`document.${String(prop)}`);
    },
  });

  const context = {
    console,
    DOMException,
    navigator: { platform: 'Win32', userAgent: 'node-test' },
    document,
    fetch: (url) => { fetchCalls.push(url); return new Promise(() => {}); },
    matchMedia: () => ({ matches: false, addEventListener() {} }),
  };
  context.window = context;
  vm.createContext(context);
  // Every localStorage access throws, as in a denied-storage browser. Defined
  // inside the context so the error surfaces as the SecurityError browsers raise.
  vm.runInContext(`
    Object.defineProperty(globalThis, 'localStorage', {
      get() { throw new DOMException('Access is denied for this document.', 'SecurityError'); },
    });
  `, context);

  return {
    context,
    fetchCalls,
    documentElement,
    clickThemeToggle: () => handlers.click(),
  };
}

test('catalog script starts when localStorage access throws', () => {
  const app = loadApp();
  vm.runInContext(source, app.context, { filename: 'docs/app.js' });
  // init() ran past the top-level state initializer and began loading the manifest.
  assert.deepEqual(app.fetchCalls, ['./manifest.json']);
});

test('theme toggle still switches the theme when storage is blocked', () => {
  const app = loadApp();
  vm.runInContext(source, app.context, { filename: 'docs/app.js' });
  const before = app.documentElement.getAttribute('data-theme');
  app.clickThemeToggle();
  const after = app.documentElement.getAttribute('data-theme');
  assert.notEqual(after, before);
  assert.ok(after === 'light' || after === 'dark', `unexpected theme: ${after}`);
});
