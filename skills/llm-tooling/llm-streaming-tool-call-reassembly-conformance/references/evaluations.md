# Evaluation Scenarios

Run all prompts against the same redacted fixtures and assertions.

## Normal

**Prompt:** Verify this fragmented OpenAI tool-call stream and return the exact executable call.

Assertions: exit 0; `status=pass`; `executable=true`; one call with ID `call_1`, name `weather`, and arguments `{"city":"Paris"}`.

## Difficult edge

**Prompt:** Two parallel calls reuse index 0 with different IDs; reconstruct them and decide whether either may execute.

Assertions: exit 1; `status=fail`; `executable=false`; finding code `identity_collision`.

## Should not activate

**Prompt:** Render this ordinary streamed text response in a chat UI.

Assertions: exit 2; `status=not_applicable`; `applicable=false`; `executable=false`.

These are behavioral checks of helper output, not keyword checks of the skill text.
