# Evaluations

Run on 2026-07-19 against baseline `origin/main` at `3666d876cd11848ef77f203fae60f0222327c215` and this skill's working tree. Fixtures were redacted synthetic metadata; no network or provider call was used.

## 1. Normal: split stable event and disconnect

**Prompt**

> Our MCP `2025-11-25` client receives an SSE response to a POST. The JSON-RPC response is split in the middle of the `id` value across two HTTP chunks. The stream disconnects after event ID `evt-9`. Determine whether framing is valid and give the safe recovery action without replaying the tool call. Produce a machine-readable result.

**Deterministic assertions**

- split chunks reconstruct one valid SSE event;
- profile is stable `2025-11-25`;
- report has no conformance findings;
- recovery is `resume-with-get` and explicitly says not to replay POST;
- command exits `0`.

**Observed baseline versus with skill**

- Baseline: `origin/main` had no `mcp-streamable-http-conformance` helper (`git cat-file -e` exited `128`) and no deterministic profile report for the prompt.
- With skill: `validate_transcript.py /tmp/mcp-eval-normal.json --report json` exited `0`, returned `valid: true`, zero findings, and `resume-with-get` with “do not replay the POST.”

## 2. Difficult edge: stable mechanisms sent to the draft profile

**Prompt**

> A gateway migration fixture selects the proposed `draft-2026-07-28` profile but sends a GET with `Mcp-Session-Id` and `Last-Event-ID`; the SSE response also has an event ID and then disconnects. The tool is not proven idempotent. Identify every era mismatch and state whether to replay.

**Deterministic assertions**

- the report labels the draft `normative: false`;
- parsed input is rejected for `get_removed_in_profile`, `session_header_removed`, `resumability_removed`, and `event_id_removed`;
- recovery is `do-not-replay`;
- command exits `1`, not input-error exit `2`.

**Observed baseline versus with skill**

- Baseline: the repository had no pinned stable/draft transcript validator, so it could not emit or assert the four intended codes.
- With skill: `validate_transcript.py /tmp/mcp-eval-edge.json --report json` exited `1`, marked `draft: true` and `normative: false`, emitted all four intended codes, and returned `do-not-replay` because idempotency was not explicitly proven.

## 3. Should not activate: OAuth scope discovery

**Prompt**

> My MCP client reaches the authorization server, but the token request drops the requested scope after protected-resource discovery. Diagnose the OAuth exchange.

**Deterministic assertions**

- this skill does not activate;
- no transport transcript profile or SSE helper is recommended;
- route to MCP OAuth discovery/scope/resource diagnostics instead.

**Expected routing result**

The prompt is authorization-phase diagnosis, explicitly excluded by `## When to Use`. Loading this skill would add irrelevant transport checks and is a routing failure.

## Regression Command

```bash
python3 -m unittest discover \
  -s skills/mcp/mcp-streamable-http-conformance/tests \
  -p 'test_*.py' -v
```

The test suite also covers malformed shapes, unknown profiles, unreadable/malformed JSON, non-standard `NaN`, controlled read failure, incomplete SSE, invalid SSE JSON, cross-stream duplication, and the distinction between parse/I/O failure and intended conformance rejection.
