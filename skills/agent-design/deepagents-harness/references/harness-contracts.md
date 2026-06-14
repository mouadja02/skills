# Harness Contracts

## State Shape

```yaml
task:
  request: ""
  constraints: []
plan:
  steps: []
  current_step: ""
artifacts:
  root: ".agent-artifacts/"
  files: []
approvals:
  required_for:
    - "shell"
    - "network"
    - "delete"
    - "external_write"
memory:
  durable_rules: []
  invalidated_rules: []
trace:
  run_id: ""
  checkpoints: []
```

## Subagent Prompt Skeleton

```markdown
You are the [role] subagent for [task].

Goal:
- [specific deliverable]

Allowed context:
- [files]
- [commands]

Allowed tools:
- [tool list]

Write outputs to:
- [artifact path]

Return one status only:
- DONE
- DONE_WITH_CONCERNS
- NEEDS_CONTEXT
- BLOCKED
```

## Approval Gate Examples

- Shell command that writes outside the workspace.
- Network call that sends repository content.
- Delete, move, or irreversible migration.
- Credential lookup.
- Production deployment or user-visible notification.
