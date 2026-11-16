// Regression tests for how the skill detail panel meets the browser's address
// bar and Back button: a ?skill= link opens the panel, opening it is a history
// step, and Back/Forward/Escape/close all agree.
//
// The page's real openSkillDetail / closeSkillDetail / applyUrlState / popstate
// code runs against an in-memory model of history and location. Layout, focus
// order and real browser traversal are checked by hand; see the PR notes.
//
// Run with:
//   node --test scripts/test-skill-detail-history.mjs

import test from 'node:test';
import assert from 'node:assert/strict';
import { loadApp, stub } from './lib/app-vm.mjs';

const ORIGIN = 'https://skills.example';
const PATHNAME = '/skills/';

// Minimal session history: a list of entries, pushState/replaceState, and
// back()/forward() that deliver popstate asynchronously, as browsers do.
function createBrowser(initialSearch = '', initialState = null) {
  const entries = [{ search: initialSearch, state: initialState }];
  let index = 0;
  let backCalls = 0;
  let onPopstate = () => {};
  const traverse = (delta) => queueMicrotask(() => {
    const next = index + delta;
    if (next < 0 || next >= entries.length) return;
    index = next;
    onPopstate();
  });
  const parse = (url) => {
    const u = new URL(url, ORIGIN + PATHNAME);
    assert.equal(u.pathname, PATHNAME, 'the page must stay on its own path');
    return u.search;
  };
  return {
    history: {
      get length() { return entries.length; },
      get state() { return entries[index].state; },
      pushState(state, _title, url) {
        entries.splice(index + 1);
        entries.push({ search: parse(url), state: structuredClone(state) });
        index++;
      },
      replaceState(state, _title, url) {
        entries[index] = { search: url === undefined ? entries[index].search : parse(url), state: structuredClone(state) };
      },
      back() { backCalls++; traverse(-1); },
      forward() { traverse(1); },
    },
    get backCalls() { return backCalls; },
    location: {
      get search() { return entries[index].search; },
      get pathname() { return PATHNAME; },
      get origin() { return ORIGIN; },
    },
    get index() { return index; },
    get length() { return entries.length; },
    get search() { return entries[index].search; },
    set onPopstate(fn) { onPopstate = fn; },
  };
}

// The detail panel, as far as the page's own logic can observe it.
function createPanel() {
  const classes = new Set();
  const attrs = new Map();
  let inert = false;
  return new Proxy(stub('skillDetail'), {
    get(target, prop) {
      if (prop === 'classList') {
        return {
          add: (c) => classes.add(c),
          remove: (c) => classes.delete(c),
          contains: (c) => classes.has(c),
          toggle: (c, on) => (on ? classes.add(c) : classes.delete(c)),
        };
      }
      if (prop === 'setAttribute') return (k, v) => attrs.set(k, String(v));
      if (prop === 'getAttribute') return (k) => (attrs.has(k) ? attrs.get(k) : null);
      if (prop === 'inert') return inert;
      if (prop === 'isOpen') return classes.has('open');
      return Reflect.get(target, prop);
    },
    set(target, prop, value) {
      if (prop === 'inert') inert = value; else target[prop] = value;
      return true;
    },
  });
}

const MANIFEST = {
  repo: 'octo/skills',
  default_branch: 'main',
  count: 3,
  categories: ['testing', 'docs'],
  skills: [
    { name: 'alpha', category: 'testing', install_path: 'testing/alpha', path: 'skills/testing/alpha', description: 'Alpha skill.' },
    { name: 'beta', category: 'testing', install_path: 'testing/beta', path: 'skills/testing/beta', description: 'Beta skill.' },
    { name: 'gamma', category: 'docs', install_path: 'docs/gamma', path: 'skills/docs/gamma', description: 'Gamma skill.' },
  ],
};

const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

function setup({ search = '', state = null } = {}) {
  const browser = createBrowser(search, state);
  const app = loadApp({ history: browser.history, location: browser.location });
  const panel = createPanel();
  const focused = [];
  const cards = new Map(); // install_path -> fake "open" button
  const browseSection = { id: 'browse', attrs: new Map(), isConnected: true,
    hasAttribute(k) { return this.attrs.has(k); }, setAttribute(k, v) { this.attrs.set(k, v); },
    focus() { focused.push('#browse'); }, scrollIntoView() {} };
  const { document } = app.context;
  document.getElementById = (id) => (id === 'skillDetail' ? panel : stub(id));
  document.body = { classList: { add() {}, remove() {} } };
  document.activeElement = document.body; // nothing focused, as on a fresh page
  document.querySelector = (sel) => {
    if (sel === '#browse') return browseSection;
    const card = sel.match(/data-skill-path="([^"]+)"/);
    if (card) return cards.get(card[1].replace(/\\/g, '')) ?? null;
    return stub(sel);
  };

  app.run(`state.manifest = ${JSON.stringify(MANIFEST)};`);
  app.run('render = () => updateUrl();'); // the grid is not under test; the address it writes is
  browser.onPopstate = () => app.fire('popstate');
  app.run('bindSkillDetail();');

  const opener = (label) => ({ label, isConnected: true, focus() { focused.push(label); } });
  const skill = (path) => app.run(`findSkill(${JSON.stringify(path)})`);
  return {
    browser, app, panel, focused, cards, opener, skill,
    open: (path) => app.call('openSkillDetail', [skill(path)]),
    close: () => app.run('closeSkillDetail()'),
    apply: () => app.run('applyUrlState()'),
    shownSkill: () => app.run('sdSkill?.install_path ?? null'),
  };
}

test('opening a ?skill= link shows that skill and leaves the filters alone', () => {
  const t = setup({ search: '?skill=testing%2Falpha' });
  t.apply();
  assert.equal(t.panel.isOpen, true);
  assert.equal(t.browser.length, 1);
  assert.equal(t.shownSkill(), 'testing/alpha');
  assert.equal(t.browser.search, '?skill=testing%2Falpha', 'the address keeps the skill');
  assert.equal(t.app.run('state.filterText'), '', 'no text search is applied');
  assert.equal(t.panel.inert, false);
  assert.equal(t.panel.getAttribute('aria-hidden'), 'false');
});

test('the Link button URL round-trips: following it opens the same skill', () => {
  const first = setup();
  first.open('docs/gamma');
  const shared = first.app.call('getSkillShareUrl', [first.skill('docs/gamma')]);
  const url = new URL(shared);

  const recipient = setup({ search: url.search });
  recipient.apply();
  assert.equal(recipient.shownSkill(), 'docs/gamma');
});

// Browsers may skip history entries a page adds before any user activation, and
// a link landing has had none. So the panel must not push an entry there, and
// closing it must not depend on a Back that could leave the site.
test('landing on ?skill= adds no history entry and closing it never calls Back', async () => {
  const t = setup({ search: '?skill=testing%2Falpha' });
  t.apply();
  assert.equal(t.browser.length, 1, 'the panel takes over the landing entry');
  assert.equal(t.browser.history.state?.skillDetail, 'landed');

  t.close();
  await tick();
  assert.equal(t.panel.isOpen, false);
  assert.equal(t.panel.inert, true);
  assert.equal(t.browser.backCalls, 0, 'closing in place, not by going Back');
  assert.equal(t.browser.length, 1);
  assert.equal(t.browser.index, 0);
  assert.equal(t.browser.search, '', 'the address no longer names the skill');
  assert.equal(t.browser.history.state, null, 'the landing marker is cleared');
});

test('opening from a card pushes an entry: Back closes the panel, Forward reopens it', async () => {
  const t = setup();
  t.apply();
  t.open('testing/alpha');
  assert.equal(t.browser.length, 2, 'the panel is its own history entry');
  assert.equal(t.browser.history.state?.skillDetail, 'pushed');

  t.browser.history.back();
  await tick();
  assert.equal(t.panel.isOpen, false);
  assert.equal(t.browser.index, 0, 'still on the catalog entry, not off the site');
  assert.equal(t.browser.search, '');
  assert.equal(t.panel.inert, true);

  t.browser.history.forward();
  await tick();
  assert.equal(t.panel.isOpen, true);
  assert.equal(t.shownSkill(), 'testing/alpha');
});

test('opening from a filtered grid pushes one entry; Back restores the previous filters', async () => {
  const t = setup({ search: '?cat=testing&q=al' });
  t.apply();
  const before = t.browser.length;
  t.open('testing/alpha');
  assert.equal(t.browser.length, before + 1);
  assert.equal(new URLSearchParams(t.browser.search).get('skill'), 'testing/alpha');
  assert.equal(new URLSearchParams(t.browser.search).get('cat'), 'testing', 'filters stay in the address');

  t.browser.history.back();
  await tick();
  assert.equal(t.panel.isOpen, false);
  assert.equal(t.browser.search, '?cat=testing&q=al');
});

test('the close button, overlay and Escape all end like Back and add no entry', async () => {
  for (const path of ['close button', 'overlay', 'escape']) {
    const t = setup({ search: '?cat=testing' });
    t.apply();
    t.open('testing/beta');
    const length = t.browser.length;
    t.close(); // all three call closeSkillDetail
    await tick();
    assert.equal(t.panel.isOpen, false, path);
    assert.equal(t.browser.length, length, `${path} must not add a history entry`);
    assert.equal(t.browser.index, length - 2, `${path} steps back over the panel's entry`);
    assert.equal(t.browser.search, '?cat=testing', path);
  }
});

test('closing twice in a row goes back once, not out of the catalog', async () => {
  const t = setup({ search: '?cat=testing' });
  t.apply();
  t.open('testing/alpha');
  t.close();
  t.close();
  await tick();
  assert.equal(t.browser.index, 0);
  assert.equal(t.browser.search, '?cat=testing');
});

test('changing filters while the panel is open keeps the skill in the address and Back still closes it', async () => {
  const t = setup();
  t.apply();
  t.open('testing/alpha');
  t.app.run('state.filterCategory = "docs"; updateUrl();'); // what a re-render does
  const params = new URLSearchParams(t.browser.search);
  assert.equal(params.get('skill'), 'testing/alpha');
  assert.equal(params.get('cat'), 'docs');
  assert.equal(t.browser.history.state?.skillDetail, 'pushed', 'the entry keeps its marker');

  t.browser.history.back();
  await tick();
  assert.equal(t.panel.isOpen, false);
  assert.equal(t.browser.index, 0);
});

test('reloading an entry the panel owns reopens it in place and keeps its kind', () => {
  for (const kind of ['pushed', 'landed']) {
    const t = setup({ search: '?cat=testing&skill=testing%2Falpha', state: { skillDetail: kind } });
    t.apply();
    assert.equal(t.shownSkill(), 'testing/alpha', kind);
    assert.equal(t.browser.length, 1, kind);
    assert.equal(t.browser.history.state?.skillDetail, kind, `${kind} entry keeps its marker`);
    assert.equal(new URLSearchParams(t.browser.search).get('skill'), 'testing/alpha', kind);
    assert.equal(new URLSearchParams(t.browser.search).get('cat'), 'testing', kind);
  }
});

test('an unknown ?skill= opens nothing and adds no entry', () => {
  const t = setup({ search: '?skill=nope%2Fnothing' });
  t.apply();
  assert.equal(t.panel.isOpen, false);
  assert.equal(t.browser.length, 1);
  assert.equal(t.browser.search, '');
});

test('?skills= and ?skill= together: the grid is filtered and the panel opens', () => {
  const t = setup({ search: '?skills=testing%2Falpha,docs%2Fgamma&skill=docs%2Fgamma' });
  t.apply();
  assert.equal(t.app.run('JSON.stringify(state.recommendedSkillNames)'), '["alpha","gamma"]');
  assert.equal(t.shownSkill(), 'docs/gamma');
});

test('popstate events that do not change the skill (hash links, same entry) are ignored', async () => {
  const t = setup();
  t.apply();
  t.open('testing/alpha');
  t.app.fire('popstate');
  assert.equal(t.panel.isOpen, true);
  assert.equal(t.shownSkill(), 'testing/alpha');

  t.browser.history.back();
  await tick();
  t.app.fire('popstate');
  assert.equal(t.panel.isOpen, false);
});

test('opening another skill after Back replaces the forward entry', async () => {
  const t = setup();
  t.apply();
  t.open('testing/alpha');
  t.browser.history.back();
  await tick();
  t.open('testing/beta');
  assert.equal(t.shownSkill(), 'testing/beta');
  assert.equal(t.browser.length, 2, 'the alpha entry is gone, as with any new navigation');

  t.browser.history.back();
  await tick();
  assert.equal(t.shownSkill(), null);
  t.browser.history.forward();
  await tick();
  assert.equal(t.shownSkill(), 'testing/beta');
});

test('focus returns to what opened the panel, then to the skill card, then to the catalog', async () => {
  // 1. A card opened it: focus goes back to that card.
  let t = setup();
  t.apply();
  const card = t.opener('card');
  t.app.context.document.activeElement = card;
  t.open('testing/alpha');
  t.close();
  await tick();
  assert.deepEqual(t.focused, ['card']);

  // 2. A link opened it and the skill's card is on screen: focus that card.
  t = setup({ search: '?skill=testing%2Falpha' });
  t.cards.set('testing/alpha', t.opener('alpha card'));
  t.apply();
  t.close();
  await tick();
  assert.deepEqual(t.focused, ['alpha card']);

  // 3. A link opened it and the card is not rendered: focus the catalog section.
  t = setup({ search: '?skill=testing%2Fbeta' });
  t.apply();
  t.close();
  await tick();
  assert.deepEqual(t.focused, ['#browse']);
});
