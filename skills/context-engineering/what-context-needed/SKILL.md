---
name: what-context-needed
description: >-
  Makes the agent list the files it needs to see before answering a question about the codebase,
  instead of guessing. Use when a question depends on code the agent has not read yet, or when earlier
  answers were confidently wrong about the code.
source: "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering"
attribution: "muratcankoylan/Agent-Skills-for-Context-Engineering by Muratcan Koylan"
license: MIT
---

> **Attribution:** Sourced from [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) by [Muratcan Koylan](https://github.com/muratcankoylan).

# What Context Do You Need?

Before answering my question, tell me what files you need to see.

## My Question

{{question}}

## Instructions

1. Based on my question, list the files you would need to examine
2. Explain why each file is relevant
3. Note any files you've already seen in this conversation
4. Identify what you're uncertain about

## Output Format

```markdown
## Files I Need

### Must See (required for accurate answer)
- `path/to/file.ts` — [why needed]

### Should See (helpful for complete answer)
- `path/to/file.ts` — [why helpful]

### Already Have
- `path/to/file.ts` — [from earlier in conversation]

### Uncertainties
- [What I'm not sure about without seeing the code]
```

After I provide these files, I'll ask my question again.
