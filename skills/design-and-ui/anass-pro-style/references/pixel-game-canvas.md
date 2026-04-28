# Pixel-art canvas hero

The hero on anass.pro is a side-scrolling pixel-art game in HTML Canvas 2D. It is the format's signature element. If the project has time/budget, build it. If not, the section "Lightweight fallback" at the end of this file shows a static substitute.

## Why this exists

The hero scene must demonstrate, in the first 5 seconds, that the sender can build something the reader cannot trivially commission. A pixel game running in 200 lines of vanilla JS is exactly that proof. A still image isn't.

## Architecture overview

```
GameEngine
├── canvas: <canvas id="game-canvas"> (full viewport)
├── update(now)         — phase machine + character physics
├── render()
│   ├── _drawSky()      — vertical gradient
│   ├── _drawWaves()    — sine-wave ambient lines
│   ├── _drawStars()    — 120 procedural stars
│   ├── _drawBuildings()— 3 parallax layers (city silhouette)
│   ├── _drawGround()   — road + dashed centre line
│   ├── _drawBosses()   — 3 enemy archetypes
│   ├── _drawCharacter()— 8-frame walking sprite (hero + AR.)
│   ├── _drawParticles()— 60-particle explosion
│   ├── _drawVignette() — radial darken
│   └── _drawArrow()    — bezier pointer arrow
└── phase: 0=walk-in → 1/2/3=boss fights → 4=victory walk → 7=final reveal
```

Total game code is ~2000 lines but it's mostly drawing primitives. The architecture is straightforward.

## Class skeleton

```js
class GameEngine {
  constructor() {
    this.cv = document.getElementById('game-canvas');
    this.ctx = this.cv.getContext('2d');
    this.t = 0; this.dt = 0; this.last = 0;

    this.phase = 0;
    this.phaseT = 0;
    this.W = 0; this.H = 0;
    this.camX = 0;
    this.scale = 1;        // 0.65 on mobile

    // Hero (the recipient's avatar — purple)
    this.karim = {
      wx: 80, wy: 0,
      walking: true, facingR: true,
      frame: 0, frameT: 0,
      color: '#7B4FE0',
      glowColor: 'rgba(123,79,224,0.4)'
    };

    // Sender (slides in during boss 1, stays for the reveal)
    this.sil = {
      wx: 9999, wy: 0,
      walking: false, facingR: false,
      frame: 0, frameT: 0,
      visible: false, alpha: 0,
      color: 'rgba(200,210,255,0.9)',
      glowColor: 'rgba(100,150,255,0.5)'
    };

    this._resize();
    window.addEventListener('resize', () => this._resize());

    this.buildings = this._genBuildings();
    this.stars = Array.from({length: 120}, () => ({
      x: Math.random() * 8000,
      y: Math.random() * .45,
      r: .5 + Math.random() * 1.2,
      op: .05 + Math.random() * .4,
      tw: .4 + Math.random() * 1.2,
      ph: Math.random() * Math.PI * 2
    }));

    // Three boss archetypes (one per recurring problem)
    this.bosses = [
      { name: 'RECRUITMENT',  color: '#C8372D', state: 'idle', alpha: 0, hp: 1 /* … */ },
      { name: 'DEVELOPMENT',  color: '#D4A843', state: 'idle', alpha: 0, hp: 1 /* … */ },
      { name: 'TECHNOLOGY',   color: '#7B4FE0', state: 'idle', alpha: 0, hp: 1 /* … */ }
    ];

    this.spells = [];
    this.particles = [];
    this.paused = false;
  }

  _resize() {
    const dpr = window.devicePixelRatio || 1;
    const W = this.cv.offsetWidth, H = this.cv.offsetHeight;
    this.cv.width  = W * dpr;
    this.cv.height = H * dpr;
    this.ctx.scale(dpr, dpr);
    this.W = W; this.H = H;
    this.gYr = W < 768 ? .82 : .72;          // ground line ratio
    this.scale = W < 768 ? 0.65 : 1;
  }

  start() {
    const tick = (now) => {
      this.update(now);
      this.render();
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
}
```

## Procedural buildings (3 parallax layers)

Three depth layers, sorted far-to-near. Layers `0.3`, `0.6`, `1.0` give good parallax separation. The mid-layer holds branded signs.

```js
_genBuildings() {
  const blds = [];
  const rnd = (a, b) => a + Math.random() * (b - a);

  // Far layer — silhouettes
  for (let i = 0; i < 14; i++) {
    blds.push({
      wx: i * 520 + rnd(0, 180),
      h: rnd(.28, .48), w: rnd(90, 150),
      layer: .3, color: '#0E0B18'
    });
  }

  // Mid layer — labeled buildings
  for (let i = 0; i < 16; i++) {
    blds.push({
      wx: i * 380 + rnd(0, 120),
      h: rnd(.16, .32), w: rnd(65, 110),
      layer: .6, color: '#130F1E',
      sign: ['BIG EVENT','8.6M VIEWS','BRAND','METHOD','500 ITEMS'][i % 5],
      hasSign: i % 4 === 0
    });
  }

  // Near layer — windowed buildings
  for (let i = 0; i < 24; i++) {
    blds.push({
      wx: i * 260 + rnd(0, 80),
      h: rnd(.14, .30), w: rnd(55, 95),
      layer: 1, color: '#1A1724',
      windowRows: Math.floor(rnd(2, 6)),
      hasSign: i % 5 === 1,
      sign: ['BIG EVENT','500 ITEMS','8.6M VIEWS','METHOD','BRAND'][i % 5]
    });
  }

  return blds;
}

_drawBuildings(ctx, W, H, gY, camX, t) {
  const sorted = [...this.buildings].sort((a, b) => a.layer - b.layer);
  sorted.forEach(b => {
    const sx = W * 0.5 + (b.wx - camX) * b.layer;
    const bh = b.h * gY;
    const by = gY - bh;
    if (sx + b.w < -100 || sx > W + 100) return;       // cull off-screen

    // Body
    ctx.fillStyle = b.color;
    ctx.fillRect(sx, by, b.w, bh);

    // Windows (animated glow)
    if (b.windowRows) {
      const cols = 3, colW = b.w / cols;
      for (let r = 0; r < b.windowRows; r++) {
        for (let c = 0; c < cols; c++) {
          const lit = Math.sin(t * .3 + (r + c) + b.wx * .01) > .4;
          ctx.fillStyle = lit ? 'rgba(123,79,224,0.18)' : 'rgba(100,120,200,0.06)';
          ctx.fillRect(sx + c * colW + 4, by + 8 + r * 12, colW - 8, 6);
        }
      }
    }

    // Sign (mono font, all caps, faint)
    if (b.hasSign && b.sign) {
      ctx.save();
      ctx.font = `bold 9px 'JetBrains Mono', monospace`;
      ctx.fillStyle = `rgba(123,79,224,${0.45 * b.layer})`;
      ctx.textAlign = 'center';
      ctx.fillText(b.sign, sx + b.w/2, by + 16);
      ctx.restore();
    }
  });
}
```

## Procedural walking sprite

8-frame walk cycle drawn entirely with `ctx.fillRect`. No sprite sheet. Body proportions are fixed; arm and leg positions cycle through 8 frames.

The sprite is drawn at *feet position* `(x, y)` so that the same call works whether the character is standing or jumping.

```js
_drawCharacter(ctx, x, y, ch, isShadow, t) {
  const s = this.scale;
  const flip = ch.facingR ? 1 : -1;
  const bob = ch.walking ? Math.sin(t * 8) * 0.5 : 0;

  ctx.save();
  ctx.translate(x, y - 80*s + bob);     // feet anchor

  // Glow
  ctx.shadowColor = ch.glowColor;
  ctx.shadowBlur = 12 * s;

  // Body color (flipped if isShadow)
  ctx.fillStyle = ch.color;

  // Pixel-art primitive: a row of fillRects per body part
  // Frames 0-7: feet alternate, arms swing.
  // Each "pixel" is 4*s wide.
  const frame = ch.frame;
  const armPhase = [0, 1, 2, 3, 4, 3, 2, 1][frame];   // 0..4..0
  const legPhase = [0, 1, 2, 1, 0, -1, -2, -1][frame];

  // — Body —
  ctx.fillRect(-8*s, -50*s, 16*s, 28*s);      // torso

  // — Head —
  ctx.fillRect(-7*s, -68*s, 14*s, 16*s);

  // — Arms —
  ctx.fillRect(-12*s + armPhase*s*flip, -42*s, 4*s, 18*s);
  ctx.fillRect(8*s   - armPhase*s*flip, -42*s, 4*s, 18*s);

  // — Legs —
  ctx.fillRect(-6*s, -22*s, 4*s, 22*s + legPhase*s);
  ctx.fillRect(2*s,  -22*s, 4*s, 22*s - legPhase*s);

  // — Hair / hat / eyes (purple highlights) —
  ctx.fillStyle = isShadow ? 'rgba(160,126,240,0.4)' : '#A07EF0';
  ctx.fillRect(-7*s, -68*s, 14*s, 4*s);       // hairline
  ctx.fillRect(-3*s * flip, -60*s, 2*s, 2*s); // eye

  ctx.restore();
}
```

This is a stripped-down version — anass.pro's actual sprite is more detailed (jacket lapels, beard, etc.) but the architecture is identical: 8 frames, all `fillRect` calls, mirrored via `flip = ±1`.

## Phase machine

The hero is *cinematic* — it plays an automatic sequence, not a free game.

```
phase 0  → Karim walks in (camera scrolls right)
phase 1  → Boss 1 (RECRUITMENT) walks in from right edge, monster sound, narrative line
            sender's avatar (sil) slides in, dialogue cards play
            both characters fire spells, boss explodes after ~2.6s
phase 4  → Victory walk (camera scrolls right again)
phase 2  → Boss 2 (DEVELOPMENT)
phase 4  → Victory walk
phase 3  → Boss 3 (TECHNOLOGY)
phase 4  → Victory walk
phase 7  → Final reveal: characters stop, narrative shows full identity,
            CTA appears, page auto-scrolls to next section
```

```js
update(now) {
  if (this.paused) { this.last = now; return; }
  this.dt = Math.min((now - this.last) / 1000, .05);
  this.last = now;
  this.t += this.dt;
  this.phaseT += this.dt;

  // Walk frame advance
  [this.karim, this.sil].forEach(ch => {
    if (ch.walking) {
      ch.frameT += this.dt;
      if (ch.frameT > 1/8) { ch.frameT = 0; ch.frame = (ch.frame + 1) % 8; }
    } else { ch.frame = 0; }
  });

  // Per-phase logic — see "Phase logic" section below
  switch (this.phase) {
    case 0: { /* walk in for 0.9s */ break; }
    case 1: case 2: case 3: { /* boss fight */ break; }
    case 4: { /* victory walk */ break; }
    case 7: { /* final reveal */ break; }
  }

  // Particles update
  this.particles.forEach(p => {
    p.x += p.vx * this.dt; p.y += p.vy * this.dt;
    p.vy += 200 * this.dt;
    p.life -= p.decay;
  });
  this.particles = this.particles.filter(p => p.life > 0);

  // Spells update
  this.spells.forEach(s => { s.x += s.vx * this.dt; s.y += s.vy * this.dt; s.life -= this.dt; });
  this.spells = this.spells.filter(s => s.life > 0);
}
```

## Boss fight phase

```js
case 1: case 2: case 3: {
  const bi = this.phase - 1;
  const boss = this.bosses[bi];

  // Camera advances only while boss approaches
  if (boss.state === 'idle') this.camX += 20 * this.dt;
  this.karim.wx = this.camX + this.W * .3;

  if (boss.state === 'idle') {
    // Boss walks in from right
    this.karim.walking = true;
    this.karim.facingR = true;
    boss.alpha = Math.min(1, boss.alpha + this.dt * 3);
    boss.sx = Math.max(this.W * .72, boss.sx - 180 * this.dt);

    if (boss.alpha >= 1 && boss.sx <= this.W * .72) {
      boss.state = 'alive';
      boss.aliveT = 0;
      if (!boss.roarPlayed) {
        boss.roarPlayed = true;
        SFX.play('monster');
        this._showNarr(boss.pendingNarr, 99999);
      }
    }
  }

  if (boss.state === 'alive') {
    boss.aliveT += this.dt;
    this.karim.walking = false;

    // Sender's avatar slides in once during boss 1
    if (boss.aliveT > 0.2 && !this.sil.visible) {
      this.sil.visible = true; this.sil.alpha = 0;
      this.sil.wx = this.karim.wx + this.W * .45;
      this.sil.walking = true;
      this.sil.facingR = false;
    }

    // Fire spell volleys every 0.3s
    if (boss.aliveT > 0.3 && (boss.aliveT - boss.lastShotT) > 0.3) {
      this._fireSpells(this.karim.wx - this.camX, boss.sx, this.H * this.gYr);
      boss.lastShotT = boss.aliveT;
    }

    // Boss dies after 2.6s of being alive
    if (boss.aliveT > 2.6) {
      boss.state = 'dying';
      boss.deathT = 0;
      this._bossExplode(boss);
      this._hideNarr();
    }
  }

  if (boss.state === 'dying' && boss.deathT > 0.9) {
    boss.state = 'dead';
    this._advancePhase();        // → phase 4 (victory walk)
  }

  break;
}
```

## Speech-bubble dialogue cards

The bottom-left card stack and the top-center "intro card" both use the same engine: a typewriter into a div, hold for `holdMs`, then animate the card into the side stack.

```js
async _showCard(html, holdMs, pointTo) {
  this.paused = true;
  this.cardLineEl.innerHTML = '';
  this.cardEl.classList.add('show');
  await this._typeHTML(this.cardLineEl, html);
  await new Promise(r => setTimeout(r, holdMs));
  this.cardEl.classList.remove('show');
  this._addToCardStack(html, pointTo);
  this.paused = false;
}
```

The card stack uses CSS transforms to make each card fan out at a different rotation:

```css
#card-stack { position: absolute; top: 32%; left: 1.6rem; display: flex; flex-direction: column; }
.stack-card { width: 230px; padding: .6rem .95rem;
  background: rgba(9,8,12,.78); border: 1px solid rgba(123,79,224,.28);
  margin-top: -30px;     /* overlap stacked */
  font-family: var(--fc); font-style: italic; font-size: .78rem;
  transform-origin: center;
  transition: transform .45s var(--ease-out), margin-top .45s var(--ease-out);
}
.stack-card:nth-child(6n+1) { transform: rotate(2deg); }
.stack-card:nth-child(6n+2) { transform: rotate(3.5deg); }
.stack-card:nth-child(6n+3) { transform: rotate(1deg); }
.stack-card:nth-child(6n+4) { transform: rotate(4deg); }
.stack-card:nth-child(6n+5) { transform: rotate(2.5deg); }
.stack-card:nth-child(6n)   { transform: rotate(3deg); }

/* Hover the stack to fan it out */
#card-stack:hover .stack-card {
  margin-top: .3rem;
  transform: rotate(0) translateX(0);
  background: rgba(9,8,12,.92);
}
```

Click any past card to replay its typewriter animation. The stack functions as both decoration and an "I missed that" affordance.

## Bezier pointer arrow

When a dialogue card mentions a character, draw a curved dashed line from the card to the character. Drawn last in `render()`, sits above vignette.

```js
_drawArrow(ctx, W, H, gY, camX) {
  if (!this.pointTo) return;

  const aboveHeadY = gY - 145 * this.scale;
  let tx, ty;
  if (this.pointTo === 'karim')      { tx = this.karim.wx - camX; ty = aboveHeadY; }
  else if (this.pointTo === 'anass') { tx = this.sil.wx - camX;  ty = aboveHeadY; }

  const sx = W * 0.5 + (this.pointTo === 'karim' ? -110 : 110);
  const sy = H * 0.14 + 92;
  const sweep = this.pointTo === 'karim' ? 1 : -1;
  const c1x = sx + sweep * 80, c1y = (sy + ty) / 2 - 10;
  const c2x = tx,              c2y = ty - 55;

  // Animate progress from card → character
  if (!this.arrowStartT) this.arrowStartT = performance.now();
  const elapsed = performance.now() - this.arrowStartT;
  const progress = 1 - Math.pow(1 - Math.min(1, elapsed / 1000), 3);

  const N = 64;
  const drawTo = Math.max(1, Math.floor(progress * N));

  ctx.save();
  ctx.strokeStyle = '#A07EF0';
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.shadowColor = '#A07EF0'; ctx.shadowBlur = 12;
  ctx.lineWidth = 2.5; ctx.setLineDash([7, 6]);
  ctx.beginPath(); ctx.moveTo(sx, sy);
  for (let i = 1; i <= drawTo; i++) {
    const t = i / N, om = 1 - t;
    const px = om*om*om * sx  + 3*om*om*t * c1x + 3*om*t*t * c2x + t*t*t * tx;
    const py = om*om*om * sy  + 3*om*om*t * c1y + 3*om*t*t * c2y + t*t*t * ty;
    ctx.lineTo(px, py);
  }
  ctx.stroke();

  // Arrowhead at end
  if (progress >= 1) {
    const ang = Math.atan2(ty - c2y, tx - c2x);
    ctx.beginPath();
    ctx.moveTo(tx, ty);
    ctx.lineTo(tx - 12*Math.cos(ang - 0.45), ty - 12*Math.sin(ang - 0.45));
    ctx.moveTo(tx, ty);
    ctx.lineTo(tx - 12*Math.cos(ang + 0.45), ty - 12*Math.sin(ang + 0.45));
    ctx.stroke();
  }
  ctx.restore();
}
```

## Wave background (canvas)

Reusable for both the game's ambient sky-waves and the Close scene's full-section wave.

```js
class WaveRenderer {
  constructor(id, o = {}) {
    this.c = document.getElementById(id);
    if (!this.c) return;
    this.x = this.c.getContext('2d');
    this.t = 0;
    this.o = {
      lines: o.lines || 20,
      spd:   o.spd   || .006,
      amp:   o.amp   || .07,
      freq:  o.freq  || 2.8,
      alpha: o.alpha || .55
    };
    this._resize();
    window.addEventListener('resize', () => this._resize());
  }

  _resize() {
    const d = window.devicePixelRatio || 1;
    const W = this.c.offsetWidth, H = this.c.offsetHeight;
    this.c.width = W * d; this.c.height = H * d;
    this.x.scale(d, d);
    this.W = W; this.H = H;
  }

  draw() {
    if (!this.x) return;
    const { x, W, H, o } = this;
    x.clearRect(0, 0, W, H);
    for (let i = 0; i < o.lines; i++) {
      const p = i / (o.lines - 1);
      const yb = H * (.1 + p * .8);
      const r = Math.round(91 + (168-91) * p);
      const g = Math.round(109 + (85-109) * p);
      const b = Math.round(224 + (247-224) * p);
      x.strokeStyle = `rgba(${r},${g},${b},${o.alpha * (.25 + p*.75)})`;
      x.lineWidth = .7;
      x.beginPath();
      for (let px = 0; px <= W; px += 3) {
        const nx = px / W;
        const y = yb
          + Math.sin(nx * o.freq * Math.PI + this.t + p * Math.PI * 1.3) * o.amp * H
          + Math.sin(nx * o.freq * 1.6 * Math.PI + this.t * 1.2 + p * .8) * o.amp * .35 * H;
        px === 0 ? x.moveTo(px, y) : x.lineTo(px, y);
      }
      x.stroke();
    }
    this.t += o.spd;
  }
}

const waveClose = new WaveRenderer('close-cv', { lines: 22, amp: .065, spd: .007, alpha: .5 });
(function loop() { waveClose.draw(); requestAnimationFrame(loop); })();
```

The color is interpolated from `(91,109,224)` (the cyan-purple `--wa`) to `(168,85,247)` (the magenta-purple `--wb`) — same gradient as the rest of the design system.

## Lightweight fallback (no game)

If the project skips the full game, the hero scene can still feel alive with just stars + buildings + city silhouette + waves. ~150 lines:

```js
class StaticHero {
  constructor() {
    this.cv = document.getElementById('game-canvas');
    this.ctx = this.cv.getContext('2d');
    this._resize();
    window.addEventListener('resize', () => this._resize());
    this.t = 0;
    this.stars = Array.from({length: 80}, () => ({
      x: Math.random(), y: Math.random() * 0.6,
      r: 0.5 + Math.random() * 1.2,
      ph: Math.random() * Math.PI * 2
    }));
    this.buildings = Array.from({length: 18}, (_, i) => ({
      x: i * 80 + Math.random() * 30,
      h: 0.15 + Math.random() * 0.35,
      w: 50 + Math.random() * 50
    }));
  }
  _resize() {
    const d = devicePixelRatio || 1;
    const W = this.cv.offsetWidth, H = this.cv.offsetHeight;
    this.cv.width = W*d; this.cv.height = H*d;
    this.ctx.scale(d, d);
    this.W = W; this.H = H;
  }
  draw() {
    const { ctx, W, H, t } = this;
    ctx.clearRect(0, 0, W, H);

    // Sky gradient
    const sky = ctx.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, '#08060F');
    sky.addColorStop(0.7, '#0E0B1A');
    sky.addColorStop(1, '#141020');
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    // Stars
    this.stars.forEach(s => {
      ctx.globalAlpha = 0.3 + Math.sin(t + s.ph) * 0.25;
      ctx.fillStyle = '#ECEAF4';
      ctx.beginPath();
      ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;

    // City silhouette
    ctx.fillStyle = '#1A1724';
    this.buildings.forEach(b => {
      ctx.fillRect(b.x, H - b.h * H, b.w, b.h * H);
    });

    // Vignette
    const vig = ctx.createRadialGradient(W/2, H/2, H * .1, W/2, H/2, H * .85);
    vig.addColorStop(0, 'rgba(0,0,0,0)');
    vig.addColorStop(1, 'rgba(0,0,0,.65)');
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, W, H);

    this.t += 0.02;
  }
  start() {
    const tick = () => { this.draw(); requestAnimationFrame(tick); };
    tick();
  }
}
new StaticHero().start();
```

This still feels like the same world; it just doesn't have characters or bosses. Pair with a static title overlay and the persistent CTA pill, and the format still works.
