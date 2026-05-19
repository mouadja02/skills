# creative-thinking

**8 skills** for bold ideation, lateral reasoning, and peak creative productivity.

These skills break conventional thinking patterns. They are designed to be used when the standard approach produces predictable, incremental, or uninspired output — and you need something genuinely different.

## Skills

| Skill | When to use |
| --- | --- |
| [`bold-ideas-generator`](./bold-ideas-generator/SKILL.md) | When you need 10x-scale ideas. Bans incremental thinking, enforces the Audacity Test, applies moon-shot/caveman columns and "Yes, And" escalation. |
| [`first-principles-deconstruction`](./first-principles-deconstruction/SKILL.md) | When you're trapped in convention. Strips problems to bedrock truths, classifies all other constraints as conventions, rebuilds from scratch. |
| [`lateral-thinking-engine`](./lateral-thinking-engine/SKILL.md) | When all obvious solutions have been tried. Applies de Bono's full toolkit: Random Entry, Provocation (Po), Challenge, Alternatives, Concept Extraction, Stepping Stones. |
| [`reverse-brainstorm`](./reverse-brainstorm/SKILL.md) | When forward brainstorming produces only obvious answers. Inverts the goal, builds a failure map, flips each failure mode into unconventional solutions. |
| [`idea-velocity`](./idea-velocity/SKILL.md) | When you need many ideas fast. 50-idea zero-judgment sprint, then triage → combination → champion. Suspends evaluation during generation. |
| [`cognitive-frame-shift`](./cognitive-frame-shift/SKILL.md) | When a decision feels obvious and needs stress-testing. Rotates through six lenses: Child, Alien, Domain Expert, Contrarian, Future Self, Hostile User. |
| [`deep-focus-protocol`](./deep-focus-protocol/SKILL.md) | When deep creative or intellectual work needs protection from fragmentation. Defines scope, batches cognitive modes, enforces the momentum principle and shutdown ritual. |
| [`creative-constraints`](./creative-constraints/SKILL.md) | When unlimited freedom is producing generic output. Applies SCAMPER (7 transformations), artificial constraints, and forced association to drive invention. |

## Install the whole category

**bash / zsh:**
```bash
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \
  | bash -s -- creative-thinking -d ~/.claude/skills/creative-thinking
```

**PowerShell:**
```powershell
$content = irm https://raw.githubusercontent.com/mouadja02/skills/main/install.ps1
iex $content
Install-Skill creative-thinking -Dest $HOME\.claude\skills\creative-thinking
```

## How these skills work together

The eight skills form a complete creative workflow:

1. **Frame the problem differently** — `first-principles-deconstruction` + `cognitive-frame-shift`
2. **Generate raw material** — `idea-velocity` (50+ ideas) or `bold-ideas-generator` (10 bold ideas)
3. **Find non-obvious paths** — `lateral-thinking-engine` or `reverse-brainstorm`
4. **Push ideas further** — `creative-constraints` (SCAMPER transformations)
5. **Execute without fragmentation** — `deep-focus-protocol`

They can be used individually on demand, or chained for a full creative sprint.
