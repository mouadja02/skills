// Loads docs/app.js into a node:vm context with a permissive DOM stub so tests
// can call its top-level functions (sdMdToHtml, openSkillDetail, ...) without a
// browser. Any DOM property is another stub and any call returns one; the
// browser objects a test cares about (`history`, `location`) are passed in.
//
// fetch never resolves, so init() parks at the manifest request and the
// catalog is never rendered unless a test drives it directly.

import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.join(here, '..', '..');
// SKILLS_APP_JS points the tests at another copy of app.js, to confirm a test
// fails against an older version (`git show origin/main:docs/app.js > old.js`).
const source = readFileSync(process.env.SKILLS_APP_JS || path.join(REPO_ROOT, 'docs', 'app.js'), 'utf8');

export function stub(label) {
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

export function loadApp({ history, location } = {}) {
  const attrs = new Map();
  const listeners = {};
  const document = new Proxy({
    documentElement: {
      setAttribute(k, v) { attrs.set(k, String(v)); },
      getAttribute(k) { return attrs.has(k) ? attrs.get(k) : null; },
    },
    querySelector: (sel) => stub(sel),
    querySelectorAll: () => [],
    addEventListener() {},
  }, {
    get(target, prop) {
      return prop in target ? target[prop] : stub(`document.${String(prop)}`);
    },
  });

  const context = {
    console,
    DOMException,
    URL,
    URLSearchParams,
    navigator: { platform: 'Win32', userAgent: 'node-test' },
    document,
    fetch: () => new Promise(() => {}),
    matchMedia: () => ({ matches: false, addEventListener() {} }),
    requestAnimationFrame: (fn) => fn(),
    setTimeout,
    clearTimeout,
    addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
    ...(history ? { history } : {}),
    ...(location ? { location } : {}),
  };
  context.window = context;
  vm.createContext(context);
  // Same denied-storage setup as test-app-storage: the catalog must not need it.
  vm.runInContext(`
    Object.defineProperty(globalThis, 'localStorage', {
      get() { throw new DOMException('Access is denied for this document.', 'SecurityError'); },
    });
  `, context);
  vm.runInContext(source, context, { filename: 'docs/app.js' });

  // Evaluate an expression inside the page's global scope, with a time limit so
  // a runaway loop fails the test instead of hanging it.
  function run(code, timeout = 2000) {
    return vm.runInContext(code, context, { timeout });
  }
  function call(fn, args = [], timeout = 2000) {
    context.__args = args;
    try {
      return vm.runInContext(`${fn}(...__args)`, context, { timeout });
    } finally {
      delete context.__args;
    }
  }
  function fire(type, event = {}) {
    for (const fn of listeners[type] ?? []) fn(event);
  }

  return { context, run, call, fire };
}
