# Context Evolution Contract

Use this contract when editing long-lived prompts, memories, instructions, or skill docs.

## Patch Template

```yaml
claim: "Use structured evidence packs before changing retrieval defaults."
evidence:
  - "eval/rag-results-2026-06-14.json showed answerability +7.2%"
scope:
  applies_to:
    - "domain RAG over internal support docs"
  does_not_apply_to:
    - "small static FAQ bots"
owner:
  files:
    - "skills/agent-eval/rag-evaluation-matrix/SKILL.md"
expiry: "Review after next embedding model migration"
conflicts:
  supersedes:
    - "Use cosine-only retrieval by default"
  notes: "Hybrid retrieval became better after query expansion was added."
```

## Review Checklist

- Does the update preserve concrete commands, file names, model IDs, metrics, and failure modes?
- Is the evidence stronger than a single unverified model opinion?
- Is the scope narrow enough that a future agent will not overapply it?
- Are superseded instructions marked explicitly?
- Can the old version be reconstructed from git history if the new rule fails?

## Invalidation Note

```markdown
> Superseded on YYYY-MM-DD: [old rule]. Reason: [evidence]. Replacement: [new rule].
```
