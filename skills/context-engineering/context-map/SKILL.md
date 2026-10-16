---
name: context-map
description: >-
  Maps the files relevant to a task before any edit: files to modify, dependencies that may need
  updates, test files, reference patterns to follow, and risks such as API, migration, or config
  changes. Use at the start of a non-trivial change in an unfamiliar codebase.
source: "https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering"
attribution: "muratcankoylan/Agent-Skills-for-Context-Engineering by Muratcan Koylan"
license: MIT
---

> **Attribution:** Sourced from [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) by [Muratcan Koylan](https://github.com/muratcankoylan).

# Context Map

Before implementing any changes, analyze the codebase and create a context map.

## Task

{{task_description}}

## Instructions

1. Search the codebase for files related to this task
2. Identify direct dependencies (imports/exports)
3. Find related tests
4. Look for similar patterns in existing code

## Output Format

```markdown
## Context Map

### Files to Modify
| File | Purpose | Changes Needed |
|------|---------|----------------|
| path/to/file | description | what changes |

### Dependencies (may need updates)
| File | Relationship |
|------|--------------|
| path/to/dep | imports X from modified file |

### Test Files
| Test | Coverage |
|------|----------|
| path/to/test | tests affected functionality |

### Reference Patterns
| File | Pattern |
|------|---------|
| path/to/similar | example to follow |

### Risk Assessment
- [ ] Breaking changes to public API
- [ ] Database migrations needed
- [ ] Configuration changes required
```

Do not proceed with implementation until this map is reviewed.
