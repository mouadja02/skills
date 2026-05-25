---
name: html-slides-creator
description: Generate polished reveal.js HTML presentations from a codebase — analyses repo, plans narrative, writes slides with branding, code demos, architecture diagrams, and speaker notes. Invoke when user says "create slides", "build a presentation", "generate a deck", "make slides for this tool/project".
source: "https://github.com/hakimel/reveal.js"
attribution: "reveal.js by Hakim El Hattab — HTML presentation framework"
---

# HTML Slides Creator

Generate production-quality **reveal.js** presentations from a codebase. The agent reads the repo, plans a narrative, and outputs a self-contained `slides.html` the user can open in any browser.

---

## Phase 1 — Gather Context

Before writing a single slide, collect:

```
1. CODEBASE        — attached files, folder structure, or README path
2. PRESENTATION PURPOSE
   - Who is the audience? (devs, execs, investors, customers, conference)
   - What is the goal? (demo, pitch, onboarding, tutorial, architecture review)
   - How long? (5 min ≈ 8-10 slides, 15 min ≈ 15-20, 30 min ≈ 25-35)
3. BRANDING (optional)
   - Primary color (hex), secondary color, accent color
   - Font preference (or "use defaults")
   - Logo URL or path (or skip)
   - Company/project name
4. SPECIAL REQUIREMENTS (optional)
   - Live code demo slides?
   - Architecture diagrams (Mermaid)?
   - Before/after comparisons?
   - Speaker notes?
   - PDF export needed?
```

If the user hasn't provided all of this, ask for items 1 and 2 at minimum. Items 3–4 are optional — use tasteful defaults.

---

## Phase 2 — Codebase Analysis

Read the codebase systematically to extract slide-worthy content:

### What to look for

| Source | Extract |
|--------|---------|
| `README.md` | Problem statement, features, quick-start, architecture overview |
| `package.json` / `pyproject.toml` | Stack, dependencies, version |
| Folder structure | Architecture layers, module boundaries |
| Key source files | Core algorithms, API surface, design patterns |
| `CHANGELOG.md` / `HISTORY.md` | Evolution, milestones, key releases |
| `docs/` | Existing diagrams, ADRs, usage examples |
| `examples/` / `demos/` | Code snippets to showcase |
| `tests/` | What behaviors are guaranteed |
| CI/CD config | Quality signals (coverage, linting, deployment) |

### Analysis output (internal — don't show to user)

```
PROJECT: [name] — [one-line description]
PROBLEM: [what pain it solves]
SOLUTION: [how it solves it uniquely]
TECH STACK: [languages, frameworks, key deps]
ARCHITECTURE: [components and how they connect]
KEY FEATURES: [3-7 bullets]
CODE HIGHLIGHTS: [2-3 interesting code snippets with explanations]
METRICS/PROOF: [tests, perf numbers, usage stats]
AUDIENCE FIT: [what this crowd cares about]
```

---

## Phase 3 — Narrative Planning

Map content to a proven presentation arc before writing HTML:

### Narrative templates

**Developer / Conference deck**
```
1. Hook — surprising fact or live demo first
2. Problem — pain the audience recognizes
3. Solution overview — 30-second pitch
4. Architecture — how it works
5. Code deep-dive — 2-3 highlight snippets
6. Demo / Live walkthrough
7. Results — benchmarks, adoption, proof
8. Getting started — install + first example
9. Roadmap / Contributing
10. Q&A / Links
```

**Executive / Investor pitch**
```
1. Vision — one powerful statement
2. Problem & market size
3. Our solution
4. Demo / screenshot tour
5. Business value / ROI
6. Technical differentiation
7. Team / traction
8. Ask / next steps
```

**Internal onboarding / tutorial**
```
1. What this tool is
2. When to use it (vs alternatives)
3. Architecture — how it fits the system
4. Quick start — run it in 3 steps
5. Core concepts — 3-5 key abstractions
6. Common patterns — recipes
7. Gotchas & troubleshooting
8. Where to get help
```

---

## Phase 4 — Generate Slides

### Boilerplate — copy-paste base

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{PROJECT_NAME}}</title>

  <!-- reveal.js from CDN — no install required -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/{{THEME}}.css" id="theme">
  <!-- highlight.js syntax theme -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/monokai.css">

  <style>
    /* ── Brand overrides ───────────────────────────── */
    :root {
      --brand-primary:   {{PRIMARY_COLOR}};
      --brand-secondary: {{SECONDARY_COLOR}};
      --brand-accent:    {{ACCENT_COLOR}};
    }

    .reveal h1, .reveal h2 { color: var(--brand-primary); }
    .reveal .accent        { color: var(--brand-accent); }
    .reveal .highlight-box {
      background: rgba(255,255,255,0.08);
      border-left: 4px solid var(--brand-accent);
      padding: 0.5em 1em;
      border-radius: 4px;
    }
    .reveal .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2em;
      align-items: start;
    }
    .reveal .three-col {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 1.5em;
    }
    .reveal .card {
      background: rgba(255,255,255,0.06);
      border-radius: 8px;
      padding: 1em;
    }
    .reveal .tag {
      display: inline-block;
      background: var(--brand-accent);
      color: #000;
      font-size: 0.5em;
      padding: 0.2em 0.6em;
      border-radius: 99px;
      vertical-align: middle;
      font-weight: bold;
    }
    .reveal .logo { position: absolute; top: 1em; right: 1em; height: 40px; }
    .reveal pre { box-shadow: none; }
    .reveal pre code { max-height: 480px; }
    /* ── Mermaid diagram centering ─────────────────── */
    .mermaid { display: flex; justify-content: center; }
  </style>
</head>
<body>

<div class="reveal">
  <!-- LOGO (optional) -->
  <!-- <img class="logo" src="{{LOGO_URL}}" alt="logo"> -->

  <div class="slides">

    <!-- ════════════════════════════════════════════════
         SLIDES GO HERE
         ════════════════════════════════════════════════ -->

  </div>
</div>

<!-- reveal.js core -->
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<!-- plugins -->
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/markdown/markdown.js"></script>
<!-- Mermaid for architecture diagrams -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>

<script>
  // Initialize Mermaid BEFORE Reveal (dark theme for diagrams)
  mermaid.initialize({ startOnLoad: false, theme: 'dark' });

  Reveal.initialize({
    hash: true,
    slideNumber: 'c/t',
    transition: 'slide',          // none | fade | slide | convex | concave | zoom
    transitionSpeed: 'default',   // default | fast | slow
    controls: true,
    progress: true,
    center: true,
    autoAnimate: true,            // enables data-auto-animate between slides
    plugins: [ RevealNotes, RevealHighlight, RevealMarkdown ]
  });

  // Render Mermaid diagrams after Reveal is ready
  Reveal.on('ready', () => {
    document.querySelectorAll('.mermaid').forEach(el => {
      mermaid.render('mermaid-' + Math.random().toString(36).slice(2), el.textContent)
        .then(({ svg }) => { el.innerHTML = svg; });
    });
  });
</script>
</body>
</html>
```

---

## Slide Type Library

Use these battle-tested templates for each slide. Mix and match.

### Title / Hero slide
```html
<section data-background-gradient="linear-gradient(135deg, {{PRIMARY_COLOR}} 0%, {{SECONDARY_COLOR}} 100%)">
  <h1 class="r-fit-text">{{PROJECT_NAME}}</h1>
  <p style="font-size: 1.3em; opacity: 0.9">{{TAGLINE}}</p>
  <p style="opacity: 0.6; font-size: 0.7em">{{PRESENTER}} · {{DATE}}</p>
  <aside class="notes">Welcome. Introduce yourself. State the goal of the talk.</aside>
</section>
```

### Problem statement
```html
<section>
  <h2>The Problem</h2>
  <div class="highlight-box">
    <p>💬 "{{PAIN_QUOTE_FROM_USER_OR_ISSUE}}"</p>
  </div>
  <ul>
    <li class="fragment">{{PAIN_POINT_1}}</li>
    <li class="fragment">{{PAIN_POINT_2}}</li>
    <li class="fragment">{{PAIN_POINT_3}}</li>
  </ul>
  <aside class="notes">Make audience nod. They know this pain.</aside>
</section>
```

### Two-column feature overview
```html
<section>
  <h2>What {{PROJECT_NAME}} Does</h2>
  <div class="two-col">
    <div>
      <h3>Before</h3>
      <ul style="font-size: 0.75em">
        <li class="fragment">{{BEFORE_1}}</li>
        <li class="fragment">{{BEFORE_2}}</li>
      </ul>
    </div>
    <div>
      <h3>After <span class="tag">✓</span></h3>
      <ul style="font-size: 0.75em">
        <li class="fragment accent">{{AFTER_1}}</li>
        <li class="fragment accent">{{AFTER_2}}</li>
      </ul>
    </div>
  </div>
</section>
```

### Architecture diagram (Mermaid)
```html
<section>
  <h2>Architecture</h2>
  <div class="mermaid" style="font-size: 0.8em">
    graph LR
      A[Client] --> B[API Gateway]
      B --> C[{{SERVICE_1}}]
      B --> D[{{SERVICE_2}}]
      C --> E[(Database)]
      D --> E
  </div>
  <aside class="notes">Walk through data flow left to right.</aside>
</section>
```

### Code highlight — step-by-step
```html
<section>
  <h2>{{CODE_SLIDE_TITLE}}</h2>
  <pre><code class="{{LANGUAGE}}" data-trim data-line-numbers="1-3|5-8|10-14">
{{CODE_SNIPPET}}
  </code></pre>
  <p class="fragment" style="font-size: 0.75em">{{KEY_INSIGHT}}</p>
  <aside class="notes">Lines 1-3: setup. Lines 5-8: the interesting part. Lines 10-14: result.</aside>
</section>
```

### Auto-animate code evolution (two slides)
```html
<!-- slide A -->
<section data-auto-animate>
  <h2 data-id="code-title">Before: Manual wiring</h2>
  <pre data-id="code-block"><code class="python" data-trim>
def process(data):
    result = []
    for item in data:
        if item.valid:
            result.append(transform(item))
    return result
  </code></pre>
</section>
<!-- slide B — same data-id attrs, Reveal animates between them -->
<section data-auto-animate>
  <h2 data-id="code-title">After: One line <span class="tag">NEW</span></h2>
  <pre data-id="code-block"><code class="python" data-trim>
def process(data):
    return [transform(i) for i in data if i.valid]
  </code></pre>
</section>
```

### Three-column feature cards
```html
<section>
  <h2>Key Features</h2>
  <div class="three-col">
    <div class="card fragment">
      <h3>{{ICON_1}} {{FEATURE_1}}</h3>
      <p style="font-size: 0.7em">{{FEATURE_1_DESC}}</p>
    </div>
    <div class="card fragment">
      <h3>{{ICON_2}} {{FEATURE_2}}</h3>
      <p style="font-size: 0.7em">{{FEATURE_2_DESC}}</p>
    </div>
    <div class="card fragment">
      <h3>{{ICON_3}} {{FEATURE_3}}</h3>
      <p style="font-size: 0.7em">{{FEATURE_3_DESC}}</p>
    </div>
  </div>
</section>
```

### Metrics / proof slide
```html
<section>
  <h2>Results</h2>
  <div class="three-col" style="text-align: center">
    <div class="fragment">
      <p style="font-size: 3em; font-weight: bold; color: var(--brand-accent)">{{METRIC_1_NUM}}</p>
      <p style="font-size: 0.8em">{{METRIC_1_LABEL}}</p>
    </div>
    <div class="fragment">
      <p style="font-size: 3em; font-weight: bold; color: var(--brand-accent)">{{METRIC_2_NUM}}</p>
      <p style="font-size: 0.8em">{{METRIC_2_LABEL}}</p>
    </div>
    <div class="fragment">
      <p style="font-size: 3em; font-weight: bold; color: var(--brand-accent)">{{METRIC_3_NUM}}</p>
      <p style="font-size: 0.8em">{{METRIC_3_LABEL}}</p>
    </div>
  </div>
</section>
```

### Quick-start / Getting started
```html
<section>
  <h2>Get Started in 60 Seconds</h2>
  <pre><code class="bash" data-trim data-line-numbers="1|3|5">
# 1. Install
{{INSTALL_COMMAND}}

# 2. Initialize
{{INIT_COMMAND}}

# 3. Run
{{RUN_COMMAND}}
  </code></pre>
  <div class="fragment highlight-box" style="margin-top: 1em; font-size: 0.8em">
    📖 Full docs at <strong>{{DOCS_URL}}</strong>
  </div>
</section>
```

### Vertical drill-down (nested slides)
```html
<!-- Parent slide — horizontal nav -->
<section>
  <section>
    <h2>{{TOPIC}}</h2>
    <p>Press ↓ to dive deeper</p>
  </section>
  <section>
    <h3>{{SUBTOPIC_1}}</h3>
    <p>{{DETAIL_1}}</p>
  </section>
  <section>
    <h3>{{SUBTOPIC_2}}</h3>
    <p>{{DETAIL_2}}</p>
  </section>
</section>
```

### Call to action / closing
```html
<section data-background-gradient="linear-gradient(135deg, {{PRIMARY_COLOR}} 0%, {{SECONDARY_COLOR}} 100%)">
  <h2>{{CALL_TO_ACTION}}</h2>
  <div class="two-col" style="margin-top: 1.5em">
    <div>
      <p>🔗 <a href="{{REPO_URL}}">{{REPO_URL}}</a></p>
      <p>📦 <code>{{INSTALL_COMMAND}}</code></p>
      <p>📖 <a href="{{DOCS_URL}}">{{DOCS_URL}}</a></p>
    </div>
    <div>
      <p>🐦 {{TWITTER_HANDLE}}</p>
      <p>💬 {{COMMUNITY_LINK}}</p>
      <p>⭐ Star us on GitHub!</p>
    </div>
  </div>
  <aside class="notes">Leave repo URL visible. Ask for questions.</aside>
</section>
```

---

## Branding Guide

### Built-in themes (pick one or override)

| Theme | Mood | Best for |
|-------|------|----------|
| `black` | Dark, professional | Tech talks, developer conferences |
| `white` | Clean, minimal | Corporate, executive demos |
| `night` | Dark, bold | Product pitches, dramatic reveals |
| `dracula` | Dark purple | Developer-centric, IDE feel |
| `sky` | Bright blue | Educational, friendly |
| `moon` | Dark blue, elegant | Startups, investor decks |
| `league` | Gray, serious | Government, finance |
| `solarized` | Warm, readable | Long tutorials |

### Custom branding — CSS variables

Override in `<style>` block after the theme link:

```css
:root {
  --r-background-color: #0f0f23;      /* slide background */
  --r-main-color: #e2e8f0;            /* body text */
  --r-heading-color: #7c3aed;         /* h1, h2 — use brand primary */
  --r-link-color: #a78bfa;            /* links */
  --r-selection-color: #7c3aed;       /* text selection */
  --r-main-font: 'Inter', sans-serif; /* body font */
  --r-heading-font: 'Inter', sans-serif; /* heading font */
}
```

### Logo placement

```html
<!-- Fixed logo overlay — paste inside <div class="reveal"> before <div class="slides"> -->
<img src="{{LOGO_URL}}"
     style="position:fixed; top:16px; right:20px; height:36px; z-index:99; opacity:0.85">
```

---

## Multi-Agent Pipeline (for large codebases)

For repos with 50+ files, delegate with sub-agents:

```
Orchestrator:
  1. Dispatch "codebase-analyst" agent
     → Input: file tree + key files
     → Output: PROJECT_ANALYSIS (structure above)
  
  2. Dispatch "narrative-planner" agent
     → Input: PROJECT_ANALYSIS + AUDIENCE + DURATION
     → Output: SLIDE_OUTLINE (numbered list of slides with content notes)
  
  3. Dispatch "slide-writer" agent (per section or all at once)
     → Input: SLIDE_OUTLINE + BRANDING + SLIDE_TEMPLATES
     → Output: complete HTML sections
  
  4. Assemble + validate final HTML
     → Open in browser for preview
```

---

## Quality Checklist

Before handing the file to the user, verify:

- [ ] **Opens in browser** — no missing CDN links, valid HTML5
- [ ] **Slide count** matches requested duration (use 1 slide ≈ 90 seconds rule)
- [ ] **No wall-of-text slides** — max 5 bullet points per slide
- [ ] **Code blocks** have `data-trim` and appropriate `data-line-numbers`
- [ ] **Speaker notes** exist on all content slides (`<aside class="notes">`)
- [ ] **Fragment animations** are used for progressive reveal (not all at once)
- [ ] **Branding colors** applied consistently — heading, accent, gradient
- [ ] **Mermaid diagrams** render (test by searching for unclosed tags)
- [ ] **Title slide** has project name, tagline, presenter, date
- [ ] **Closing slide** has repo URL, install command, and call to action
- [ ] **File is self-contained** — CDN URLs only, no local deps

---

## Output Instructions

1. Write the complete `slides.html` to the project root (or a `docs/slides/` subfolder)
2. Print a short summary:
   ```
   ✅ slides.html — N slides, ~X min at 90s/slide
   Sections: {{SECTION_LIST}}
   Theme: {{THEME}} + custom brand colors
   Open with: open slides.html   (macOS)
              start slides.html  (Windows)
   Export PDF: add ?print-pdf to URL, then Ctrl+P → Save as PDF
   ```
3. If the user asks for changes, apply inline — don't regenerate the whole file

---

## References

- **reveal.js docs**: https://revealjs.com
- **Themes**: https://revealjs.com/themes/
- **Auto-Animate**: https://revealjs.com/auto-animate/
- **Code highlighting**: https://revealjs.com/code/
- **Layout helpers**: https://revealjs.com/layout/
- **Config options**: https://revealjs.com/config/
- **CDN**: https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/
- **Mermaid diagrams**: https://mermaid.js.org/syntax/flowchart.html
- **zarazhangrui/frontend-slides** (style patterns): https://github.com/zarazhangrui/frontend-slides
- **AI presentation generator example**: https://github.com/nooqta/ai-presentation
- **visual-explainer skill** (HTML diagram patterns): https://github.com/nicobailon/visual-explainer
