# Section recipes

Each scene is a `<section>` with: a kicker label, a title, optional content blocks, and `data-s` for the dot-nav. All scenes (except the hero) use class `.scene` for shared layout.

```css
.scene {
  min-height: 100vh; min-height: 100dvh;
  display: flex; flex-direction: column; justify-content: center;
  padding: 7rem 8vw;
  position: relative; overflow: hidden;
  border-top: 1px solid var(--border);
}
.sec-label { font-family: var(--fm); font-size: var(--xs); letter-spacing: var(--lsc); text-transform: uppercase; color: var(--purple); margin-bottom: 1.2rem; }
.sec-title { font-family: var(--fc); font-weight: 800; font-size: clamp(2.8rem, 6vw, 5rem); line-height: 1; letter-spacing: -.01em; margin-bottom: .6rem; }
.sec-sub   { font-family: var(--fb); font-weight: 300; font-style: italic; font-size: var(--lg); color: var(--ink2); margin-bottom: 3.5rem; max-width: 540px; line-height: 1.7; }
```

## Scene 0 — Hero (game)

The hero scene is unique: no headings, no `.scene` class. It's a full-viewport stage.

```html
<section id="game-hero" data-s="0">
  <canvas id="game-canvas"></canvas>

  <div id="game-hud">
    <div class="hud-top">
      <div class="hud-brand">
        <img class="hud-logo" src="logo.png" alt="BRAND NAME">
        <div class="hud-name">BRAND <strong>NAME</strong></div>
      </div>
      <div class="hud-tag">For [Recipient Name] — [Their Role]</div>
    </div>
  </div>

  <div id="narr"></div>

  <a id="moi-cta" href="https://linkedin.com/in/you" target="_blank" rel="noopener" aria-hidden="true">
    <span>Hire me!</span>
    <span class="cs-arr"></span>
  </a>

  <div id="game-title">
    <div class="game-title-roles">
      Engineer · Builder · Operator
    </div>
    <div class="game-title-tagline">
      The one who opens the doors that code alone cannot close.
    </div>
  </div>

  <div id="intro-card">
    <img class="ic-bull" src="logo.png" alt="" aria-hidden="true">
    <div class="ic-line"></div>      <!-- typed in by JS -->
  </div>

  <div id="card-stack" aria-label="Past cards — click to replay"></div>
</section>
```

If the project skips the game (constrained scope), replace the canvas with a static animated illustration:

```html
<section id="game-hero" data-s="0" style="position:relative;height:100vh;height:100dvh;overflow:hidden;background:var(--bg)">
  <canvas id="hero-stars"></canvas>      <!-- WaveRenderer-style stars + city silhouette -->
  <div id="game-hud">…same HUD…</div>
  <div id="narr"><!-- big title written here as static HTML --></div>
  <a id="moi-cta" class="show" …>…</a>   <!-- shows immediately, no game gate -->
</section>
```

The HUD copy must address the recipient by name. The CTA is hidden initially (`aria-hidden="true"`); reveal it after the user finishes scrolling once and comes back.

## Scene 1 — Hook

Typewriter-driven introduction that names the analogy: the reader's work ↔ this site.

```html
<section id="s-hook" class="scene" data-s="1">
  <div class="hook-brand-bar">
    <img class="hook-brand-logo" src="logo.png" alt="BRAND">
    <div class="hook-brand-name">BRAND <strong>NAME</strong></div>
    <div class="hook-sep"></div>
    <div class="hook-tag">Application — Reserved for [Recipient Name]</div>
  </div>

  <div id="hook-lines">
    <div class="hook-line" id="hl1"></div>     <!-- typed by Typer -->
    <div class="hook-line" id="hl2"></div>
    <div class="hook-line" id="hl3"></div>
    <div id="hblink" class="hook-line" style="opacity:0">
      <span class="hcursor"></span>            <!-- blinking cursor while counter runs -->
    </div>
  </div>

  <div id="hook-counter">
    <div id="hook-n">0</div>                   <!-- counts up to a target -->
    <div id="hook-lbl">views generated<br>by one well-executed<br>idea</div>
  </div>

  <p id="hook-aside">It impressed me. <em>And I wasn't the only one.</em></p>
</section>
```

Copy formula:
- **Line 1:** "You did [specific big thing]." Highlight the number with `<span class="pu">…</span>`.
- **Line 2:** "I do [scaled-down analogous thing] — for you alone." Highlight `seule URL` / `one URL`.
- **Line 3:** "The principles are *exactly* the same." Highlight `exactly`.

The counter's target should be a number from the recipient's own work (their views, their revenue, their followers). Format it for the recipient's locale (`toLocaleString('fr-FR')`). The aside underneath is in italic Fraunces — quiet credit, not boast.

## Scene 2 — Mirror

Two-column compare table. Left column: their move. Right column: your move using the same psychological mechanism.

```html
<section id="s1" class="scene" data-s="2">
  <img class="mirror-deco rv" src="mirror.png" alt="" aria-hidden="true">
  <div class="sec-label rv">01 — The Mirror</div>
  <h2 class="sec-title rv d1">You used<br>500 wallets.</h2>
  <p class="sec-sub rv d2">I use one URL. The principles are identical.</p>
  <p class="mirror-tagline rv d3">I reflect your ideas back.</p>

  <div class="mirror-table rv d3">
    <div class="mirror-header">
      <div class="mhc">Your campaign — 500 wallets</div>
      <div class="mhc">This site — same architecture</div>
    </div>
    <div class="mrow">
      <div class="mc"><span class="mct">Visual capture</span>A bill sticking out. Impossible to ignore. The reptile brain takes over.</div>
      <div class="mc"><span class="mct">Cognitive capture</span>A game where you play your own story. The founder brain detects: someone gets me.</div>
    </div>
    <div class="mrow">
      <div class="mc"><span class="mct">Differentiation</span>5–6 variants. Each person thinks they found "their" version. Difference creates conversation.</div>
      <div class="mc"><span class="mct">Uniqueness</span>One application. This site exists only for you. Nobody else got it.</div>
    </div>
    <div class="mrow">
      <div class="mc"><span class="mct">Conversion</span>QR code on the flyer. Curiosity becomes a measurable action.</div>
      <div class="mc"><span class="mct">Conversion</span>One button at the end. Curiosity leads directly to a LinkedIn exchange.</div>
    </div>
  </div>
</section>
```

Required CSS for the table (the visual rhythm depends on the borders being hairline, not heavy):

```css
.mirror-table { border: 1px solid var(--border); margin-top: 1rem; }
.mirror-header { display: grid; grid-template-columns: 1fr 1fr; border-bottom: 1px solid var(--border); }
.mhc { padding: 1rem 2rem; font-family: var(--fm); font-size: var(--xs); letter-spacing: var(--lsc); text-transform: uppercase; }
.mhc:first-child { color: var(--dim); border-right: 1px solid var(--border); }
.mhc:last-child  { color: var(--purple); }
.mrow { display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid var(--border); transition: background .2s; }
.mrow:hover { background: rgba(123,79,224,.04); }
.mc { padding: 1.75rem 2rem; font-size: var(--md); line-height: 1.75; }
.mc:first-child { border-right: 1px solid var(--border); color: var(--ink2); font-style: italic; font-weight: 300; }
.mc:last-child  { color: var(--purhi); }
.mct { font-family: var(--fm); font-size: var(--xs); letter-spacing: var(--lsw); text-transform: uppercase; color: var(--dim); display: block; margin-bottom: .6rem; }
```

The decorative `<img class="mirror-deco">` floats top-right with a glow filter and a slow float animation. Drop it on mobile.

## Scene 3 — Method

A pull-quote from the recipient + 3 expandable steps explaining the psychology of the experience the user just had.

```html
<section id="s2" class="scene" data-s="3">
  <div class="sec-label rv">02 — The Method</div>
  <blockquote class="mquote rv d1">
    "The idea is worth nothing, the execution is everything."
    <cite>— [Recipient Name], [Their Brand]</cite>
  </blockquote>
  <div class="steps rv d2">
    <article class="step t1">
      <span class="step-num" aria-hidden="true">01</span>
      <div class="step-t">Second 0–3</div>
      <div class="step-h">Primitive Capture</div>
      <div class="step-b">You saw your own name in a game. Your brain processed: <em>someone targeted me personally.</em> Dopamine fired before the rest of the page even loaded.</div>
    </article>
    <article class="step t2">
      <span class="step-num" aria-hidden="true">02</span>
      <div class="step-t">Second 3–60</div>
      <div class="step-h">Cognitive Rupture</div>
      <div class="step-b">You expected a CV. You played your own story. <em>Predictive break.</em> The prefrontal cortex lights up. Curiosity replaces defense.</div>
    </article>
    <article class="step t3">
      <span class="step-num" aria-hidden="true">03</span>
      <div class="step-t">Now</div>
      <div class="step-h">Positive Reappraisal</div>
      <div class="step-b">You're re-evaluating the whole sequence. The expected reward (another applicant) just transformed. <em>You want to know who did this.</em></div>
    </article>
  </div>
  <p class="mclose rv d3">This isn't the same as sending "Hello, I'm interested in a position." Those profiles never understood what you do. <strong>I do — and I know how to build it.</strong></p>
</section>
```

CSS — the magic is `.step:hover { flex: 1.5 }` which lets the hovered card grow at the others' expense:

```css
.steps { display: flex; gap: 1px; margin-bottom: 4rem; background: var(--border); border: 1px solid var(--border); min-height: 340px; }
.step { flex: 1; position: relative; overflow: hidden; background: var(--bg); padding: 2.4rem 2rem 2.2rem; display: flex; flex-direction: column;
  transition: flex .7s var(--ease-out), background .35s ease; cursor: pointer; }
.step::before { content: ''; position: absolute; inset: 0; opacity: .35; transition: opacity .55s ease; z-index: 0; pointer-events: none; }
.step.t1::before { background: radial-gradient(circle at 30% 20%, rgba(200,55,45,.22), transparent 65%); }
.step.t2::before { background: radial-gradient(circle at 50% 25%, rgba(91,159,216,.22), transparent 65%); }
.step.t3::before { background: radial-gradient(circle at 70% 25%, rgba(160,126,240,.28), transparent 65%); }
.step:hover { flex: 1.5; background: var(--bg2); }
.step-num { position: absolute; top: 1rem; right: 1.4rem; font-family: var(--fs); font-style: italic; font-size: 5.5rem; opacity: .14; }
.step:hover .step-num { opacity: .5; transform: translateY(-3px) scale(1.05); }
```

Each step has a different radial-gradient atmosphere (`t1` warm/red, `t2` cool/blue, `t3` brand purple). Don't put all 3 in the brand color — the contrast is what makes the row read as a sequence.

## Scene 4 — Reveal

This is the pivot scene. Centered, lower density. Italic gradient title that names the technique. A glowing watermark logo behind everything.

```html
<section id="s3" class="scene" data-s="4">
  <img class="bull-wm" src="logo.png" alt="" aria-hidden="true">
  <div class="rev-label rv">The Reveal</div>
  <h2 class="rev-hl rv d1">
    What you just<br>experienced is<br>
    <span class="grad">behavioral<br>engineering.</span>
  </h2>
  <div class="rule" style="margin: 2rem auto"></div>
  <p class="rev-body rv d2">No magic. No accident. A precise architecture. Every detail — the game, the doors, the anonymous character — was designed to produce a measurable neurological effect. Exactly like your 500 wallets.</p>
  <p class="rev-quote rv d3">"When theory and data converge, the debate is over."</p>
</section>
```

CSS:

```css
#s3 { background: var(--bg2); align-items: center; text-align: center; position: relative; }
.bull-wm { position: absolute; width: 500px; height: 500px; opacity: .04; pointer-events: none;
  left: 50%; top: 50%; transform: translate(-50%,-50%);
  filter: drop-shadow(0 0 0 rgba(123,79,224,0));
  transition: opacity 1.6s ease, filter 1.6s ease; }
#s3.bull-lit .bull-wm {
  opacity: .22;
  filter: drop-shadow(0 0 40px rgba(123,79,224,.85)) drop-shadow(0 0 90px rgba(168,85,247,.45));
  animation: bullPulse 4.5s ease-in-out 1.6s infinite;
}
@keyframes bullPulse {
  0%,100% { opacity:.22; filter:drop-shadow(0 0 40px rgba(123,79,224,.85)) drop-shadow(0 0 90px rgba(168,85,247,.45)); }
  50%     { opacity:.32; filter:drop-shadow(0 0 60px rgba(160,126,240,1))  drop-shadow(0 0 130px rgba(168,85,247,.7)); }
}
.rev-hl { font-family: var(--fc); font-weight: 900; font-size: clamp(2.2rem, 5.5vw, 4.5rem); line-height: 1.1; max-width: 880px; margin: 0 auto 2rem; }
.rev-body { font-family: var(--fb); font-weight: 300; font-size: var(--lg); color: var(--ink2); max-width: 600px; margin: 0 auto 3.5rem; line-height: 1.85; }
.rev-quote { font-family: var(--fc); font-weight: 300; font-style: italic; font-size: clamp(1.2rem, 2.5vw, 1.7rem); color: var(--purhi); max-width: 640px; margin: 0 auto; line-height: 1.55; }
```

Wire the watermark to glow on first scroll-in:

```js
const s3Section = document.getElementById('s3');
if (s3Section) {
  const bullObs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { s3Section.classList.add('bull-lit'); bullObs.unobserve(s3Section); }
    });
  }, { threshold: .25 });
  bullObs.observe(s3Section);
}
```

## Scene 5 — Person

2-column grid. Left: identity + stats. Right: bio + skill chips + project tiles.

```html
<section id="s4" class="scene" data-s="5">
  <div class="sec-label rv">03 — The Candidate</div>
  <div class="pgrid">
    <div>
      <div class="pname rv">A. R.</div>
      <div class="prole rv d1">QA Engineer by day.<br>Builder by night.</div>
      <div class="stats rv d2">
        <div class="stat"><div class="stat-n">10<sup>+</sup></div><div class="stat-l">Years of software experience</div></div>
        <div class="stat"><div class="stat-n">2<sup>×</sup></div><div class="stat-l">Countries — Morocco, France</div></div>
        <div class="stat"><div class="stat-n">1<sup>×</sup></div><div class="stat-l">AI Hackathon — 1st prize</div></div>
        <div class="stat"><div class="stat-n">0</div><div class="stat-l">Generic applications sent</div></div>
      </div>
    </div>
    <div>
      <p class="pbio rv">[Recipient], you proved your ideas work. […] I'm a software engineer with 10 years of experience. I automate what wastes time. I build what impresses.<br><br><strong>I'm not looking for a job. I'm looking for a partnership.</strong></p>

      <div class="skills rv d1">
        <span class="chip">TypeScript</span><span class="chip">Java</span><span class="chip">React / Next.js</span>
        <span class="chip">Python</span><span class="chip">Node.js</span><span class="chip">QA</span>
        <span class="chip">Automation</span><span class="chip">AI Workflows</span>
      </div>

      <div class="rv d2">
        <div class="blabel">Projects built end-to-end</div>
        <div class="bgrid">
          <a href="https://example.com" target="_blank" rel="noopener" class="bi">
            <span class="bi-tag">Open-source AI <span class="cs-arr cs-arr-upright"></span></span>
            <div class="bi-name">QA Orchestra — multi-task agents</div>
          </a>
          <!-- … 3 more tiles -->
        </div>
      </div>

      <div class="rv d3 bgroup-gap">
        <div class="blabel">Projects I contributed to</div>
        <div class="bgrid">
          <!-- 4 government / enterprise tiles -->
        </div>
      </div>
    </div>
  </div>
</section>
```

CSS for the project tiles (`.bgrid` is a 2-column grid with hairline `1px` background showing through to make the borders):

```css
.pgrid { display: grid; grid-template-columns: 1fr 2fr; gap: 6rem; align-items: start; }
.pname { font-family: var(--fc); font-weight: 800; font-size: clamp(2.2rem, 4vw, 3.8rem); line-height: 1; }
.prole { font-family: var(--fb); font-weight: 300; font-style: italic; font-size: var(--lg); color: var(--purhi); margin-bottom: 2.5rem; }

.stats { border-top: 1px solid var(--border); }
.stat { padding: 1rem 0; border-bottom: 1px solid var(--border); }
.stat-n { font-family: var(--fc); font-weight: 700; font-size: 1.8rem; color: var(--ink); line-height: 1; }
.stat-n sup { color: var(--purple); font-size: .9em; }
.stat-l { font-family: var(--fm); font-size: var(--xs); letter-spacing: var(--lsw); text-transform: uppercase; color: var(--dim); margin-top: .25rem; }

.skills { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: 3rem; }
.chip { font-family: var(--fm); font-size: var(--xs); letter-spacing: var(--lsw); text-transform: uppercase;
  padding: .35rem .8rem; border: 1px solid rgba(123,79,224,.22); color: rgba(236,234,244,.5); transition: all .2s; }
.chip:hover { border-color: var(--purple); color: var(--purhi); background: rgba(123,79,224,.08); }

.bgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--border); border: 1px solid var(--border); }
.bi { background: var(--bg); padding: .9rem 1.1rem; transition: background .2s; }
.bi:hover { background: var(--bg2); }
.bi-tag { font-family: var(--fm); font-size: var(--xs); letter-spacing: var(--lsw); text-transform: uppercase; color: var(--purple); display: block; margin-bottom: .2rem; }
.bi-name { font-family: var(--fb); font-size: var(--base); color: var(--ink2); }
```

Stats: include "0 generic applications sent" or an equivalent provocative-zero stat. It signals the format itself.

## Scene 6 — Close

The ask. One CTA. Italic Fraunces sign-off.

```html
<section id="s5" class="scene" data-s="6">
  <canvas id="close-cv"></canvas>      <!-- WaveRenderer in the background -->
  <div id="s5in">
    <div class="ckicker rv">The Close</div>
    <h2 class="chl rv d1">
      Now you know<br>what I do<br>when I want
      <span class="grad">something.</span>
    </h2>
    <p class="cbody rv d2">You have the ideas, the clients, the impact. The tech piece is what's missing. I build what you can't delegate to just anyone.</p>
    <a href="https://linkedin.com/in/you" target="_blank" rel="noopener" class="cta rv d3">
      <span>Find out who I am</span>
      <span class="arr cs-arr"></span>
    </a>
    <div class="cmeta rv d4">
      <div class="cmi">Reply<strong>to discover who I am</strong></div>
    </div>
    <p class="csig rv d4">
      This site was<br>
      <span>designed only for you.</span>
    </p>
  </div>
</section>
```

CSS for the CTA (gradient + magnetic + hover-glow):

```css
.cta {
  display: inline-flex; align-items: center; gap: 1rem;
  font-family: var(--fc); font-weight: 600; font-size: var(--base);
  letter-spacing: var(--lsw); text-transform: uppercase;
  color: var(--ink); background: linear-gradient(135deg, var(--wa), var(--wb));
  padding: 1.1rem 2.4rem; text-decoration: none;
  border: none; cursor: none; position: relative; overflow: hidden;
  transition: all .2s;
}
.cta::before { content:''; position:absolute; inset:0; background: linear-gradient(135deg, var(--wb), var(--wa)); opacity:0; transition: opacity .25s; }
.cta:hover::before { opacity: 1; }
.cta:hover { box-shadow: 0 0 32px rgba(123,79,224,.5); transform: translateY(-2px); }
.cta span, .cta .arr { position: relative; z-index: 1; }
.cta:hover .arr { transform: translateX(7px); }

.csig {
  font-family: var(--fs); font-style: italic; font-weight: 300;
  font-size: clamp(1.3rem, 2.4vw, 1.85rem);
  line-height: 1.35;
  color: var(--ink2);
  margin-top: 3.5rem; max-width: 520px;
  padding: .4rem 0 .5rem 1.8rem;
  border-left: 1px solid rgba(168,126,240,.45);
  font-variation-settings: "opsz" 96;
  position: relative;
}
.csig::before {
  content: ''; position: absolute; left: -1px; top: 50%;
  width: 3px; height: 36%;
  background: linear-gradient(180deg, var(--wa), var(--wb));
  transform: translateY(-50%); border-radius: 2px;
}
.csig span { display: block; color: var(--purhi); font-weight: 500; margin-top: .15rem; }
```

The `.csig` is the *last* impression. Two lines, Fraunces italic, breaking right after "This site was". The line break is what makes it feel handwritten. Don't merge them.

## Scaffold-level fixed elements (outside scenes)

These five elements live at the body level, persistent across all scenes. They appear once in the markup (after all `<section>`s).

```html
<!-- Custom cursor (desktop only) -->
<div id="cur"></div>
<div id="curring"></div>

<!-- Top scroll progress bar -->
<div id="prog"></div>

<!-- Right-side dot navigation -->
<nav id="nav">
  <div class="nd on" data-s="0"></div>
  <div class="nd"    data-s="1"></div>
  <div class="nd"    data-s="2"></div>
  <div class="nd"    data-s="3"></div>
  <div class="nd"    data-s="4"></div>
  <div class="nd"    data-s="5"></div>
  <div class="nd"    data-s="6"></div>
</nav>

<!-- Persistent character buddy (canvas) -->
<canvas id="anass-buddy" aria-hidden="true"></canvas>

<!-- Sound toggle -->
<button id="sfx-toggle" type="button" aria-label="Enable sounds" aria-pressed="false">
  <span class="sfx-icon" aria-hidden="true"></span>
</button>

<!-- "Continue ↓" pill, bottom-center, hides on last scene -->
<button id="next-cue" type="button" class="is-watching show" aria-label="Animation in progress">
  <span class="nc-bars"><span></span><span></span><span></span></span>
  <span class="nc-text">Watch</span>
  <span class="nc-arrow cs-arr cs-arr-down"></span>
</button>

<!-- "Back to top" pill, bottom-right, only at very bottom -->
<button id="back-top" type="button" aria-label="Back to top">
  <span class="bt-arrow cs-arr cs-arr-up"></span>
  <span>Back</span>
</button>

<!-- Live region for screen readers -->
<div id="al" aria-live="polite" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)"></div>
```

The complete markup + CSS for these elements is already in `templates/starter.html`.
