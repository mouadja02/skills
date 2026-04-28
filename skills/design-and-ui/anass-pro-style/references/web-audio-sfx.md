# Procedural Web Audio SFX

Every sound in anass.pro is synthesized at runtime via the Web Audio API. **No audio files are loaded.** This is fundamental to the format's "all-craft, single-file" identity. It also keeps total bundle size under 200 KB.

## The SFX module

A single closure exposing `play(type)`, `toggle()`, and `enabled`. It lazily creates the `AudioContext` on first use (browsers require a user gesture before audio plays — never autoplay).

```js
const SFX = (() => {
  let ctx = null;
  let enabled = true;
  try { if (localStorage.getItem('sfxMuted') === '1') enabled = false; } catch(e) {}

  function _ensure() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === 'suspended') ctx.resume();
  }

  // Helper: oscillator with frequency ramp + amplitude envelope
  function _envOsc(type, freq, ramp, dur, vol) {
    const t = ctx.currentTime;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (ramp != null) o.frequency.exponentialRampToValueAtTime(ramp, t + dur);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    o.connect(g).connect(ctx.destination);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  function play(type) {
    if (!enabled) return;
    _ensure();
    const t = ctx.currentTime;
    SOUND_RECIPES[type]?.(ctx, t);   // see below
  }

  function toggle() {
    enabled = !enabled;
    try {
      if (enabled) localStorage.removeItem('sfxMuted');
      else         localStorage.setItem('sfxMuted', '1');
    } catch(e) {}
    if (enabled) { _ensure(); play('click'); }
    return enabled;
  }

  return { play, toggle, get enabled() { return enabled; } };
})();
```

## Sound recipes

Each recipe is a function `(ctx, t) => void` where `t` is the AudioContext's current time. Drop them into `SOUND_RECIPES`.

### `click` — UI confirmation

A single short sine tone. Sounds like a soft tap.

```js
click: (ctx, t) => {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'sine';
  o.frequency.setValueAtTime(660, t);
  g.gain.setValueAtTime(0.05, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.06);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.08);
}
```

### `key` — typewriter keystroke

Two layers: a high-frequency click (the strike) + a low damped sine (the bottom-out). Slight randomness gives organic variation.

```js
key: (ctx, t) => {
  // Strike — short HF noise burst
  const clickBuf = ctx.createBuffer(1, ctx.sampleRate * 0.01, ctx.sampleRate);
  const cd = clickBuf.getChannelData(0);
  for (let i = 0; i < cd.length; i++) cd[i] = (Math.random()*2-1) * Math.pow(1 - i/cd.length, 3);
  const cs = ctx.createBufferSource(); cs.buffer = clickBuf;
  const cf = ctx.createBiquadFilter(); cf.type = 'highpass';
  cf.frequency.value = 2200 + Math.random()*800;
  const cg = ctx.createGain();
  cg.gain.setValueAtTime(0.045, t);
  cg.gain.exponentialRampToValueAtTime(0.001, t + 0.014);
  cs.connect(cf).connect(cg).connect(ctx.destination);
  cs.start(t);

  // Thud — damped sine (key bottoms out)
  const thud = ctx.createOscillator();
  thud.type = 'sine';
  const f = 95 + Math.random()*55;
  thud.frequency.setValueAtTime(f, t);
  thud.frequency.exponentialRampToValueAtTime(f * 0.55, t + 0.045);
  const tg = ctx.createGain();
  tg.gain.setValueAtTime(0.065, t);
  tg.gain.exponentialRampToValueAtTime(0.001, t + 0.06);
  thud.connect(tg).connect(ctx.destination);
  thud.start(t); thud.stop(t + 0.08);
}
```

### `tick` — counter pulse

A very short square-wave blip with frequency randomization. Sounds like a stopwatch.

```js
tick: (ctx, t) => {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'square';
  o.frequency.setValueAtTime(2400 + Math.random()*400, t);
  g.gain.setValueAtTime(0.025, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.015);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.02);
}
```

### `ding` — counter completion / success

Two-pitch sine: hits A5 (880 Hz), then jumps to E6 (1318.5 Hz) after 80ms. Reads as a positive "got it" chime.

```js
ding: (ctx, t) => {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'sine';
  o.frequency.setValueAtTime(880, t);
  o.frequency.setValueAtTime(1318.5, t + 0.08);
  g.gain.setValueAtTime(0.08, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.55);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.6);
}
```

### `cta` — CTA hover/click

A rising triangle tone — half-octave glissando upward. Reads as "go forward".

```js
cta: (ctx, t) => {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'triangle';
  o.frequency.setValueAtTime(523, t);   // C5
  o.frequency.exponentialRampToValueAtTime(1046, t + 0.22);   // C6
  g.gain.setValueAtTime(0.07, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.22);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.24);
}
```

### `phase` — phase transition (game)

Square 440 → 880, fast pitch sweep. Use when phases change in any sequenced animation.

```js
phase: (ctx, t) => {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'square';
  o.frequency.setValueAtTime(440, t);
  o.frequency.exponentialRampToValueAtTime(880, t + 0.18);
  g.gain.setValueAtTime(0.05, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.2);
}
```

### `spell` — game projectile

Square 880 Hz with downward sweep. The pew-pew of a magic spell.

```js
spell: (ctx, t) => {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'square';
  o.frequency.setValueAtTime(880, t);
  o.frequency.exponentialRampToValueAtTime(220, t + 0.18);
  g.gain.setValueAtTime(0.06, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.2);
}
```

### `explosion` — game boss death

White noise through a lowpass that sweeps from 1200 Hz to 80 Hz. Sounds like an impact + boom.

```js
explosion: (ctx, t) => {
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.55, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) {
    d[i] = (Math.random()*2 - 1) * Math.pow(1 - i/d.length, 2);
  }
  const s = ctx.createBufferSource(); s.buffer = buf;
  const f = ctx.createBiquadFilter(); f.type = 'lowpass';
  f.frequency.setValueAtTime(1200, t);
  f.frequency.exponentialRampToValueAtTime(80, t + 0.5);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.18, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.55);
  s.connect(f).connect(g).connect(ctx.destination);
  s.start(t);
}
```

### `monster` — boss arrival (4-layer)

The signature scary sound. Four parallel layers:

1. **Thud** — sub-bass sine descending 95→38 Hz
2. **Drone** — two detuned sawtooths (slight beating from 115 vs 118 Hz) descending
3. **Tension** — high sine sliding 660→220 Hz
4. **Whoosh** — bandpass-filtered noise swelling

```js
monster: (ctx, t) => {
  // 1 — Thud (impact)
  const thud = ctx.createOscillator(); thud.type = 'sine';
  thud.frequency.setValueAtTime(95, t);
  thud.frequency.exponentialRampToValueAtTime(38, t + 0.45);
  const tg = ctx.createGain();
  tg.gain.setValueAtTime(0.45, t);
  tg.gain.exponentialRampToValueAtTime(0.001, t + 0.55);
  thud.connect(tg).connect(ctx.destination);
  thud.start(t); thud.stop(t + 0.6);

  // 2 — Drone (dual detuned saws → menace)
  const d1 = ctx.createOscillator(); d1.type = 'sawtooth';
  d1.frequency.setValueAtTime(115, t); d1.frequency.exponentialRampToValueAtTime(72, t + 1.6);
  const d2 = ctx.createOscillator(); d2.type = 'sawtooth';
  d2.frequency.setValueAtTime(118, t); d2.frequency.exponentialRampToValueAtTime(74, t + 1.6);
  const dg = ctx.createGain();
  dg.gain.setValueAtTime(0.001, t);
  dg.gain.linearRampToValueAtTime(0.2, t + 0.12);
  dg.gain.setValueAtTime(0.2, t + 1.1);
  dg.gain.exponentialRampToValueAtTime(0.001, t + 1.7);
  const dlp = ctx.createBiquadFilter(); dlp.type = 'lowpass';
  dlp.frequency.setValueAtTime(900, t);
  dlp.frequency.linearRampToValueAtTime(380, t + 1.4);
  d1.connect(dg); d2.connect(dg); dg.connect(dlp).connect(ctx.destination);
  d1.start(t); d1.stop(t + 1.75); d2.start(t); d2.stop(t + 1.75);

  // 3 — Tension sine (high → low)
  const ts = ctx.createOscillator(); ts.type = 'sine';
  ts.frequency.setValueAtTime(660, t);
  ts.frequency.exponentialRampToValueAtTime(220, t + 1.5);
  const tsg = ctx.createGain();
  tsg.gain.setValueAtTime(0.001, t);
  tsg.gain.linearRampToValueAtTime(0.05, t + 0.25);
  tsg.gain.exponentialRampToValueAtTime(0.001, t + 1.5);
  ts.connect(tsg).connect(ctx.destination);
  ts.start(t); ts.stop(t + 1.55);

  // 4 — Whoosh (bandpass noise swell)
  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.55, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random()*2 - 1);
  const sw = ctx.createBufferSource(); sw.buffer = buf;
  const swF = ctx.createBiquadFilter(); swF.type = 'bandpass';
  swF.frequency.setValueAtTime(2200, t);
  swF.frequency.exponentialRampToValueAtTime(420, t + 0.45);
  swF.Q.value = 2;
  const swG = ctx.createGain();
  swG.gain.setValueAtTime(0.001, t);
  swG.gain.linearRampToValueAtTime(0.09, t + 0.1);
  swG.gain.exponentialRampToValueAtTime(0.001, t + 0.5);
  sw.connect(swF).connect(swG).connect(ctx.destination);
  sw.start(t);
}
```

### `jumpLand` — character lands after a jump

A short low sine (impact) + a tiny noise tap (feet on ground).

```js
jumpLand: (ctx, t) => {
  const o = ctx.createOscillator();
  o.type = 'sine';
  o.frequency.setValueAtTime(115, t);
  o.frequency.exponentialRampToValueAtTime(48, t + 0.12);
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.1, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.13);
  o.connect(g).connect(ctx.destination);
  o.start(t); o.stop(t + 0.15);

  const buf = ctx.createBuffer(1, ctx.sampleRate * 0.04, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random()*2-1) * Math.pow(1 - i/d.length, 4);
  const s = ctx.createBufferSource(); s.buffer = buf;
  const f = ctx.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = 600;
  const ng = ctx.createGain();
  ng.gain.setValueAtTime(0.06, t);
  ng.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
  s.connect(f).connect(ng).connect(ctx.destination);
  s.start(t);
}
```

## Wiring the mute toggle

Default to *muted-but-armed* — the toggle reads "Enable sounds" on first load. The first user gesture (`pointerdown`/`keydown`/`touchstart`/`click`) primes the audio context. After that, the user can click the toggle to flip on/off; the state persists in `localStorage`.

```html
<button id="sfx-toggle" type="button" aria-label="Enable sounds" aria-pressed="false">
  <span class="sfx-icon" aria-hidden="true"></span>
</button>
```

```css
#sfx-toggle {
  position: fixed; top: 5rem; right: 2.5rem;
  width: 38px; height: 38px;
  display: inline-flex; align-items: center; justify-content: center;
  background: rgba(9,8,12,.78);
  border: 1px solid rgba(123,79,224,.28); border-radius: 50%;
  color: rgba(236,234,244,.55);
  cursor: none; z-index: 80;
  -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);
  transition: background .25s, border-color .25s, color .25s, transform .25s;
}
#sfx-toggle:hover {
  background: rgba(123,79,224,.16);
  border-color: rgba(123,79,224,.55);
  color: var(--ink);
  transform: scale(1.05);
}
#sfx-toggle.on { color: var(--purhi); border-color: rgba(160,126,240,.55); }

.sfx-icon {
  width: 16px; height: 16px;
  background-color: currentColor;
  -webkit-mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4zM2 4l18 18-1.4 1.4L1 5.4 2 4z'/></svg>");
          mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4zM2 4l18 18-1.4 1.4L1 5.4 2 4z'/></svg>");
  -webkit-mask-size: contain; mask-size: contain;
  -webkit-mask-position: center; mask-position: center;
  -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
}
#sfx-toggle.on .sfx-icon {
  /* swap mask to "speaker on" icon */
  -webkit-mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4zm-2.5-7v2.06a7 7 0 0 1 0 13.88V21a9 9 0 0 0 0-18z'/></svg>");
          mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4zm-2.5-7v2.06a7 7 0 0 1 0 13.88V21a9 9 0 0 0 0-18z'/></svg>");
}
```

```js
(function wireSfxToggle() {
  const btn = document.getElementById('sfx-toggle');
  if (!btn) return;
  let primed = false, unlockTs = 0;

  function applyButton() {
    const showOn = SFX.enabled && primed;
    btn.classList.toggle('on', showOn);
    btn.setAttribute('aria-pressed', String(showOn));
    btn.setAttribute('aria-label', showOn ? 'Mute sounds' : 'Enable sounds');
  }
  applyButton();

  const unlockEvents = ['pointerdown', 'keydown', 'touchstart', 'click'];
  function prime() {
    if (primed) return;
    primed = true; unlockTs = performance.now();
    if (SFX.enabled) SFX.play('key');
    applyButton();
    unlockEvents.forEach(ev => document.removeEventListener(ev, prime, true));
  }
  unlockEvents.forEach(ev => document.addEventListener(ev, prime, true));

  btn.addEventListener('click', () => {
    // First click also unlocks (deduped by 250ms window)
    if (performance.now() - unlockTs < 250) {
      if (!SFX.enabled) { SFX.toggle(); SFX.play('click'); }
      applyButton();
      unlockTs = 0;
      return;
    }
    SFX.toggle();
    applyButton();
  });
})();
```

## When to skip SFX

- The site embeds inside an iframe where audio is disruptive
- The recipient explicitly works in shared/quiet environments
- The brief asks for a "quiet" / "editorial" tone

In those cases, drop the SFX module entirely and replace `SFX.play('key')` calls with no-ops. The visual experience still works — the typewriter still types, the counter still counts. It just plays silently.

## Volume tuning notes

These gains are tuned for headphones at moderate volume. If the user complains the SFX is too loud:

- `key` thud `0.065` → `0.04`
- `tick`         `0.025` → `0.015`
- `ding`         `0.08`  → `0.05`
- `monster` thud `0.45`  → `0.28` (it's the most-likely-to-startle layer)

Lower together, not just one. The mix is balanced.
