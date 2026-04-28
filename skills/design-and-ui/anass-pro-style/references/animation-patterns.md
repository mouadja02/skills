# Animation patterns

Six interaction recipes. All in vanilla ES6+, no dependencies. Each is independent — you can implement just `cursor` + `reveal` for a stripped-down version, or all six for the full experience.

## 1. Custom cursor (dot + ring)

Two divs that follow the mouse with different smoothing rates: a fast small dot and a slower large ring. The native cursor is hidden via `cursor:none`. Disabled on touch.

```html
<div id="cur"></div>
<div id="curring"></div>
```

```css
body { cursor: none; }
@media (max-width: 768px), (hover: none) {
  body { cursor: auto; }
  #cur, #curring { display: none; }
}

#cur {
  position: fixed; width: 9px; height: 9px;
  background: var(--purple); border-radius: 50%;
  pointer-events: none; z-index: 9999;
  transform: translate(-50%, -50%);
  mix-blend-mode: screen;
  transition: transform .1s ease;
}
#cur.lk {
  transform: translate(-50%, -50%) scale(3.5);
  background: var(--purhi);
}
#curring {
  position: fixed; width: 30px; height: 30px;
  border: 1px solid rgba(123,79,224,.3); border-radius: 50%;
  pointer-events: none; z-index: 9998;
  transform: translate(-50%, -50%);
}
```

```js
const cur = document.getElementById('cur');
const ring = document.getElementById('curring');
let mx=0, my=0, cx=0, cy=0, rx=0, ry=0;
document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });
(function tick() {
  cx += (mx - cx) * .2;  cy += (my - cy) * .2;   // dot — fast (lerp .2)
  rx += (mx - rx) * .08; ry += (my - ry) * .08;  // ring — slow (lerp .08)
  cur.style.left  = cx + 'px'; cur.style.top  = cy + 'px';
  ring.style.left = rx + 'px'; ring.style.top = ry + 'px';
  requestAnimationFrame(tick);
})();
document.querySelectorAll('a, button, .nd').forEach(el => {
  el.addEventListener('mouseenter', () => cur.classList.add('lk'));
  el.addEventListener('mouseleave', () => cur.classList.remove('lk'));
});
```

The `mix-blend-mode: screen` is what makes the dot look "luminous" against dark backgrounds. Don't drop it.

## 2. Top scroll progress bar

```html
<div id="prog"></div>
```

```css
#prog {
  position: fixed; top: 0; left: 0;
  height: 2px; width: 0%;
  background: linear-gradient(90deg, var(--wa), var(--wb));
  z-index: 1000;
  box-shadow: 0 0 10px var(--purple);
  transition: width .1s linear;
}
```

```js
const pb = document.getElementById('prog');
window.addEventListener('scroll', () => {
  const h = document.documentElement.scrollHeight - window.innerHeight;
  pb.style.width = (window.scrollY / h * 100) + '%';
}, { passive: true });
```

## 3. Right-side dot navigation

```html
<nav id="nav">
  <div class="nd on" data-s="0"></div>
  <div class="nd"    data-s="1"></div>
  <!-- one .nd per scene, data-s matches the section's data-s -->
</nav>
```

```css
#nav {
  position: fixed; top: 50%; right: 2rem;
  transform: translateY(-50%);
  display: flex; flex-direction: column; gap: .55rem;
  z-index: 100; opacity: 0;
  animation: fi .5s ease 2s forwards;   /* fades in 2s after page load */
}
.nd {
  width: 5px; height: 5px; border-radius: 50%;
  background: rgba(123,79,224,.2);
  cursor: none; transition: all .2s ease;
}
.nd.on, .nd:hover {
  background: var(--purple);
  box-shadow: 0 0 8px var(--purple);
  transform: scale(1.5);
}
@media (max-width: 768px) { #nav { display: none; } }
@keyframes fi { from{opacity:0} to{opacity:1} }
```

```js
const scenes = document.querySelectorAll('[data-s]');
const dots   = document.querySelectorAll('.nd');

const navObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const idx = +e.target.dataset.s;
      dots.forEach((d, i) => d.classList.toggle('on', i === idx));
    }
  });
}, { threshold: 0.4 });

scenes.forEach(s => navObs.observe(s));
dots.forEach(d => d.addEventListener('click', () => {
  const idx = +d.dataset.s;
  if (scenes[idx]) scenes[idx].scrollIntoView({ behavior: 'smooth' });
}));
```

## 4. Scroll reveal (`.rv` and `.rv.split`)

Two flavors:

- `.rv` — fade up the whole element when 10% in view.
- `.rv.split` — split title into per-word `<span class="sw">`s and stagger them.

```css
.rv { opacity: 0; transform: translateY(24px); transition: opacity .65s ease, transform .65s ease; }
.rv.in { opacity: 1; transform: none; }

/* Stagger delays for child reveals */
.d1 { transition-delay: .1s; }
.d2 { transition-delay: .2s; }
.d3 { transition-delay: .3s; }
.d4 { transition-delay: .4s; }

/* Word-by-word version */
.rv.split { opacity: 1; transform: none; transition: none; }
.rv.split .sw {
  display: inline-block;
  opacity: 0; transform: translateY(.45em);
  transition: opacity .7s var(--ease-out), transform .7s var(--ease-out);
  transition-delay: calc(var(--i, 0) * 45ms);
  will-change: opacity, transform;
}
.rv.split.in .sw { opacity: 1; transform: none; }

/* Smaller stagger for closing copy (so it doesn't feel slow at the end of a scene) */
.rv.split.mclose .sw { transition-delay: calc(var(--i, 0) * 25ms); }

/* Gradient-clipped words inside a split */
.rv.split .grad .sw {
  background: linear-gradient(135deg, var(--wa), var(--wb));
  -webkit-background-clip: text; background-clip: text;
}
```

```js
// 4a — generic reveal
const rvObs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); rvObs.unobserve(e.target); } });
}, { threshold: .1, rootMargin: '0px 0px -50px 0px' });
document.querySelectorAll('.rv').forEach(el => rvObs.observe(el));

// 4b — per-word splitter (call before observers fire)
function splitWords(el) {
  const collect = (node) => {
    if (node.nodeType === 3) {
      const text = node.textContent;
      if (!text || !text.trim()) return [node];
      const out = [];
      text.split(/(\s+)/).forEach(part => {
        if (!part) return;
        if (/^\s+$/.test(part)) {
          out.push(document.createTextNode(part));
        } else {
          const span = document.createElement('span');
          span.className = 'sw';
          span.textContent = part;
          out.push(span);
        }
      });
      return out;
    }
    if (node.nodeType !== 1 || node.tagName === 'BR') return [node];
    const newChildren = [];
    Array.from(node.childNodes).forEach(c => collect(c).forEach(n => newChildren.push(n)));
    while (node.firstChild) node.removeChild(node.firstChild);
    newChildren.forEach(n => node.appendChild(n));
    return [node];
  };

  const replaced = [];
  Array.from(el.childNodes).forEach(c => collect(c).forEach(n => replaced.push(n)));
  while (el.firstChild) el.removeChild(el.firstChild);
  replaced.forEach(n => el.appendChild(n));

  el.querySelectorAll('.sw').forEach((w, i) => w.style.setProperty('--i', i));
  el.classList.add('split');
}

// Apply to display headings only — never to body paragraphs
document.querySelectorAll('.sec-title.rv, .rev-hl.rv, .chl.rv, .mclose.rv').forEach(splitWords);
```

## 5. Typewriter with audio

A small `Typer` class that types into an element, character by character, firing the `key` SFX on every printed character. Punctuation pauses are baked in.

```css
.hcursor {
  display: inline-block;
  width: 3px; height: .85em;
  background: var(--purple);
  vertical-align: middle;
  margin-left: 3px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
```

```js
class Typer {
  constructor(el) { this.el = el; }

  async type(parts, opts = {}) {
    const speed   = opts.speed   ?? 38;     // ms per char
    const jitter  = opts.jitter  ?? 8;      // ±ms randomness
    const startDelay = opts.delay ?? 0;
    if (startDelay) await new Promise(r => setTimeout(r, startDelay));

    this.el.innerHTML = '';
    const cursor = document.createElement('span');
    cursor.className = 'hcursor';

    for (const part of parts) {
      const seg = document.createElement('span');
      if (part.cls) seg.className = part.cls;       // e.g. 'pu' for purple
      this.el.appendChild(seg);
      this.el.appendChild(cursor);                  // cursor stays last child

      for (let i = 0; i < part.text.length; i++) {
        seg.appendChild(document.createTextNode(part.text[i]));
        this.el.appendChild(cursor);                // re-pin cursor

        const ch = part.text[i];
        if (ch !== ' ' && ch !== '\n' && ch !== '\t') SFX.play('key');

        let dt = speed + (Math.random() * 2 * jitter - jitter);
        if (ch === ',' || ch === '—' || ch === ';') dt += 140;
        else if (ch === '.' || ch === '!' || ch === '?') dt += 220;
        await new Promise(r => setTimeout(r, Math.max(10, dt)));
      }
      if (part.pauseAfter) await new Promise(r => setTimeout(r, part.pauseAfter));
    }
    cursor.remove();
  }
}

// Usage:
await new Typer(document.getElementById('hl1')).type([
  { text: 'You did ' },
  { text: '500 wallets', cls: 'pu', pauseAfter: 180 },
  { text: ' at GITEX.' }
], { speed: 36, delay: 200 });
```

The `parts` array model is what lets you mid-stream switch into a `.pu` (purple) span, pause, then continue in default ink. Punctuation pauses are intentional — they make the text feel *thought*, not *generated*.

## 6. Animated counter (rises with audio ticks + final ding)

For the "8.6M views" counter in the Hook scene.

```js
async function runCounter(elNumber, target, dur = 2000, locale = 'en-US') {
  const start = performance.now();
  const tickStep = target / 18;       // ~18 audible ticks across the rise
  let lastTick = 0;

  await new Promise(res => {
    function step(now) {
      const t = Math.min((now - start) / dur, 1);
      const e = 1 - Math.pow(1 - t, 3);   // cubic ease-out
      const current = e * target;
      elNumber.textContent = Math.floor(current).toLocaleString(locale);
      if (current - lastTick >= tickStep) {
        SFX.play('tick');
        lastTick = current;
      }
      t < 1 ? requestAnimationFrame(step) : res();
    }
    requestAnimationFrame(step);
  });

  SFX.play('ding');
}
```

Trigger when the section comes into view:

```js
const hookObs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) runHookSequence(); });
}, { threshold: .3 });
hookObs.observe(document.getElementById('s-hook'));
```

## 7. Magnetic CTA (desktop pointer only)

The CTA gently translates toward the cursor when within 160px. Disabled on touch.

```js
(function magnetCTA() {
  const btn = document.querySelector('.cta');
  if (!btn) return;
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
  if (!fine.matches) return;

  const STRENGTH = 0.32;
  const RANGE    = 160;
  const EASE     = 0.18;

  let bx=0, by=0, tx=0, ty=0, active=false;

  document.addEventListener('mousemove', e => {
    const r = btn.getBoundingClientRect();
    if (r.width === 0) return;          // hidden
    const cx = r.left + r.width / 2;
    const cy = r.top  + r.height / 2;
    const dx = e.clientX - cx, dy = e.clientY - cy;
    const dist = Math.hypot(dx, dy);
    if (dist < RANGE) {
      const falloff = 1 - dist / RANGE;
      tx = dx * STRENGTH * falloff;
      ty = dy * STRENGTH * falloff;
      active = true;
    } else if (active) {
      tx = 0; ty = 0; active = false;
    }
  }, { passive: true });

  document.addEventListener('mouseleave', () => { tx = 0; ty = 0; });

  (function loop() {
    bx += (tx - bx) * EASE;
    by += (ty - by) * EASE;
    if (Math.abs(bx) < 0.05 && Math.abs(by) < 0.05 && tx === 0 && ty === 0) {
      btn.style.transform = '';
    } else {
      btn.style.transform = `translate(${bx.toFixed(2)}px, ${by.toFixed(2)}px)`;
    }
    requestAnimationFrame(loop);
  })();
})();
```

`STRENGTH` 0.32 is the tuned value — higher and the button feels skittish; lower and the effect goes unnoticed.

## 8. Persistent character buddy (cross-section pixel sprite)

A small canvas pinned at body-level. After the user scrolls past 45% of the first viewport, the buddy "appears" by jumping with a parabolic arc to whichever section is currently most visible. Click any dot, the buddy hops to it.

Architecture:

- One `<canvas id="anass-buddy">` element absolutely positioned, transformed via `translate(...)`.
- A buddy state object: `{x, y, facingR, walking, frame, frameT, jumpFrom, jumpTo, jumpStart, jumpDur}`.
- `requestAnimationFrame` loop draws an 8-frame walking sprite at `(x, y)`.
- `IntersectionObserver` on each section: when a section becomes most-visible, call `jumpToSection(section)`, which sets a new `jumpFrom`/`jumpTo` and starts a 850ms parabolic interpolation.

```js
const BW = 88, BH = 144;            // buddy canvas size
const buddyCanvas = document.getElementById('anass-buddy');
buddyCanvas.width = BW; buddyCanvas.height = BH;
const bctx = buddyCanvas.getContext('2d');

const buddy = {
  x: -200, y: -200,
  facingR: true, walking: false,
  frame: 0, frameT: 0, t: 0, lastT: 0,
  jumpFrom: null, jumpTo: null, jumpStart: 0, jumpDur: 850,
  visible: false, currentSection: null
};

function pickTarget(section) {
  const r = section.getBoundingClientRect();
  if (window.innerWidth < 768) {
    const idx = sections.indexOf(section);
    return { x: idx % 2 === 0 ? 50 : window.innerWidth - 50, y: window.innerHeight - 80 };
  }
  return {
    x: Math.max(60, Math.min(window.innerWidth - 70, r.right - 90)),
    y: Math.max(80, Math.min(window.innerHeight - 30, r.top + r.height * 0.78))
  };
}

function jumpToSection(section) {
  if (!section || section === buddy.currentSection) return;
  const target = pickTarget(section);
  buddy.jumpFrom = { x: buddy.x, y: buddy.y };
  buddy.jumpTo   = target;
  buddy.jumpStart = performance.now();
  buddy.facingR  = target.x >= buddy.x;
  buddy.walking  = true;
  buddy.currentSection = section;
}

function loop(now) {
  if (getComputedStyle(buddyCanvas).display === 'none') {
    buddy.lastT = now; requestAnimationFrame(loop); return;
  }
  const dt = buddy.lastT ? Math.min((now - buddy.lastT) / 1000, .05) : 0.016;
  buddy.lastT = now; buddy.t += dt;

  if (buddy.jumpFrom) {
    const elapsed = now - buddy.jumpStart;
    const p = Math.min(1, elapsed / buddy.jumpDur);
    const ep = p < 0.5 ? 4*p*p*p : 1 - Math.pow(-2*p + 2, 3) / 2;  // ease-in-out cubic
    let bx = buddy.jumpFrom.x + (buddy.jumpTo.x - buddy.jumpFrom.x) * ep;
    let by = buddy.jumpFrom.y + (buddy.jumpTo.y - buddy.jumpFrom.y) * ep;
    const arcH = Math.min(140, Math.max(60, Math.abs(buddy.jumpTo.x - buddy.jumpFrom.x) * 0.35 + 50));
    by -= Math.sin(p * Math.PI) * arcH;
    buddy.x = bx; buddy.y = by;
    if (p >= 1) { SFX.play('jumpLand'); buddy.jumpFrom = null; buddy.walking = false; buddy.frame = 0; }
  }

  if (buddy.walking) {
    buddy.frameT += dt;
    if (buddy.frameT > 1/8) { buddy.frameT = 0; buddy.frame = (buddy.frame + 1) % 8; }
  }

  buddyCanvas.style.transform = `translate(${buddy.x - BW/2}px, ${buddy.y - BH + 10}px)`;
  bctx.clearRect(0, 0, BW, BH);
  drawSprite(bctx, BW/2, BH - 10, buddy);   // see references/pixel-game-canvas.md
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
```

The "appearance" (visible after first scroll past 45vh) lives in a separate scroll listener; see `templates/starter.html` for the full wiring.

## 9. Reduced motion

This single rule disables every transition/animation in the document:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Add this **at the top** of your styles, before the rest. Reveal classes still fire (they're toggled by JS), so users who prefer reduced motion still see all content — they just don't see it animate in.

For the canvas-based pieces (game, character buddy, waves), check the media query in JS too:

```js
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reducedMotion) {
  // Render game in a static "final state" pose; skip animation loop
}
```

## Quick reference: which class does what

| Class | Job |
|---|---|
| `.rv` | Fade up when in view |
| `.rv .d1`–`.d4` | Stagger delay 100/200/300/400ms |
| `.rv.split` | Per-word fade-up; `splitWords()` injects `<span class="sw" style="--i:N">` |
| `.sw` | One word inside a `.rv.split`; stagger via `--i` index |
| `.pu` | Inline purple-ink emphasis |
| `.grad` | Inline gradient-clipped emphasis (one per scene max) |
| `.cs-arr` | SVG-mask arrow (right-pointing); use `.cs-arr-down`/`.cs-arr-up`/`.cs-arr-upright` for rotations |
| `.hcursor` | Blinking cursor for typewriter |
| `.nd` / `.nd.on` | Right-side nav dot / active state |
| `.lk` (on `#cur`) | Cursor scale-up state when hovering links/buttons |
| `.show` (on overlay buttons) | Make `#next-cue` / `#back-top` / `#moi-cta` visible |
| `.is-watching` (on `#next-cue`) | "Watch" pre-game state with animated bars |
