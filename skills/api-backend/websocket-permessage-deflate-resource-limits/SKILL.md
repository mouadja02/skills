---
name: websocket-permessage-deflate-resource-limits
description: Use when validating WebSocket permessage-deflate implementations for decompressed-size, compressed-size, expansion-ratio, fragmentation, timeout, or context-takeover resource boundaries.
version: "1.0.0"
license: MIT
---

# WebSocket permessage-deflate Resource Limits

## When to Use

- A WebSocket endpoint negotiates `permessage-deflate` and must prove that compressed messages cannot outrun memory or CPU limits.
- A configured message-size limit appears to apply only before or after decompression.
- Fragmentation or context takeover changes limit accounting or inflater lifetime.
- A bounded, offline regression fixture is needed after a decompression resource-exhaustion report.

Do **not** activate for deployments that never negotiate compression, generic WebSocket framing bugs, ordinary HTTP content encoding, or production traffic probing. First prove negotiation at every relevant hop. Keep ordinary uncompressed message-size limits even when this workflow does not activate.

## Prerequisites

- Python 3.9+ with the standard-library `zlib` module for the packaged analyzer.
- Synthetic payloads only; do not copy production messages, cookies, tokens, or captured frames into fixtures.
- An owned ephemeral endpoint if implementation-level verification is required.
- Explicit compressed-byte, decompressed-byte, ratio, fragment-count, and wall-clock budgets.

## Quick Reference

| Boundary | Required invariant | Typical failure action |
| --- | --- | --- |
| Negotiation | Decode only when `permessage-deflate` was actually negotiated | Reject unexpected RSV1 as a protocol error |
| Compressed input | Count payload bytes across the whole logical message | Abort before accepting the next fragment |
| Inflated output | Limit every incremental inflater read | Discard tentative output; close with configured policy, commonly `1009` |
| Expansion ratio | Apply in addition to an absolute output cap | Reject at the first exceeded boundary |
| Fragmentation | One compression state and one budget per message, not per frame | Never reset counters on continuation frames |
| Context takeover | Preserve directional history only when negotiated | Close on ambiguous/corrupt state; do not guess-reset and continue |
| Application delivery | Commit only after FIN, inflate, size, and payload validation succeed | Deliver no partial oversized message |

## Procedure

### 1. Freeze the tested tuple

Record the client and server implementation/version, direction, HTTP hop path, negotiated extension response, window bits, `client_no_context_takeover` / `server_no_context_takeover`, configured message limit, and close-code policy. Compression state is directional; never share client-to-server and server-to-client conclusions.

If the handshake does not negotiate `permessage-deflate`, stop the decompression test. Verify extension rejection at each hop, reject RSV1-bearing data frames, and retain ordinary uncompressed limits.

### 2. Define limits before generating fixtures

Choose small test-only ceilings. At minimum define:

- compressed payload bytes per logical message;
- decompressed bytes per logical message;
- expansion ratio;
- fragments per message and messages per connection;
- wall-clock deadline and, where exposed, allocator/process-memory ceiling.

The absolute output limit is the authoritative memory boundary. A ratio limit is supplemental: a small valid compressed message can legitimately expand substantially. Never generate an unbounded “bomb”; use a tiny payload whose known output crosses a deliberately low test ceiling by one bounded chunk.

### 3. Model one logical compressed message

Compression applies to a message, not each frame. Set RSV1 only on the first data frame; continuation frames use opcode `0x0` and carry the same message state. Count compressed and output bytes cumulatively across every fragment. Supply the RFC 7692 DEFLATE tail exactly once at message completion.

Hold all decompressed bytes as tentative. Commit to the application only after FIN, DEFLATE processing, output/ratio limits, framing, and text UTF-8 validation all pass. A rejection must deliver neither a complete message nor a prefix.

### 4. Prove context-takeover behavior

Run two fresh-connection cases:

1. **Takeover:** compress two messages with one directional compressor and decode with one directional inflater. Preserve history only after message 1 commits.
2. **No context takeover:** use a fresh compressor and inflater for each message.

Make message 2 depend on message 1's dictionary in the takeover case so an accidental reset is observable. On malformed compressed data, resource rejection, or dictionary ambiguity, close the connection. Resetting and continuing can leave peers with divergent histories.

### 5. Run the offline analyzer

The helper accepts data-only JSON and performs no network access. Each fragment is strict Base64 containing raw compressed **message payload** bytes; exclude WebSocket framing and the removed `00 00 ff ff` sync-flush tail.

```json
{
  "version": 1,
  "permessage_deflate_negotiated": true,
  "context_takeover": "no_context_takeover",
  "limits": {
    "compressed_bytes": 128,
    "output_bytes": 2048,
    "ratio": 64,
    "milliseconds": 1000,
    "fragments": 8
  },
  "messages": [
    {"id": "bounded-oversize", "compressed": true, "fragments": ["<base64>"]}
  ]
}
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/analyze_trace.py trace.json
```

Exit `0` means the trace was analyzed, including an intentional policy rejection. Exit `2` means malformed input or output failure. Inspect the JSON `status`, per-message `reason`, `application_delivered`, `close_connection`, and `close_code`; do not infer pass/fail from process exit alone.

The helper is a bounded oracle, not a WebSocket frame parser, performance benchmark, vulnerability scanner, or proof of a target library's allocator behavior. Its millisecond check is cooperative between bounded inflate calls, not a preemptive process deadline. Put implementation fixtures under an external hard timeout and prove the child exited after timeout. Compare the oracle's expected transition with instrumentation from the actual owned implementation.

### 6. Verify the real implementation

Use an ephemeral loopback client/server and the same synthetic messages. Verify:

1. the exact extension parameters were negotiated;
2. counters span continuation frames and reset only at a message boundary;
3. inflation stops when the next output chunk would cross the output or ratio budget;
4. peak process memory remains within the predeclared test allowance;
5. no partial application callback fires;
6. the configured close code is emitted and no later message is processed on that connection;
7. a fresh connection can process the safe boundary control;
8. takeover and no-takeover cases produce their distinct expected transitions.

Test equality and one-unit-over controls for every integer limit. Keep time and memory observations separate from the helper's deterministic byte accounting.

## Failure Recovery

- **Malformed trace:** fix schema/Base64; a parse or I/O error is not evidence that an expected-invalid protocol fixture passed.
- **Output or ratio rejection:** discard tentative output and close. Do not deliver a prefix or continue the same compressed connection.
- **Unexpected dictionary failure:** compare negotiated takeover parameters in the tested direction, then recreate the fixture from a fresh connection.
- **Timeout:** prove the test process exited, preserve counters, and reduce fixture size. Do not raise the deadline until the boundary disappears.
- **Target differs from oracle:** localize the first fragment/callback where counters diverge. Do not weaken the oracle merely to match post-inflate checking.

## Pitfalls and Safety

- Checking `max_message_size` only after full inflation does not bound allocation or CPU work.
- Resetting byte counters per continuation frame makes fragmentation a limit bypass.
- Applying only a ratio limit can reject legitimate small inputs and still permit large absolute allocation.
- Context takeover state is per connection and direction, not global and not per frame.
- `1009` is a common local message-too-big policy; assert the implementation's documented exact code rather than treating every disconnect as success.
- Never run bomb payloads against third-party or production endpoints. No network scanning, exploit generation, or credential-bearing captures belong in this workflow.

## Objective Verification

From this installed package, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Completion requires all packaged tests to pass, an analyzer result that rejects a bounded over-limit fixture without application delivery, safe equality controls that pass, and implementation evidence showing the same failure boundary and closed-connection recovery transition.

## Evaluation Prompts

1. **Normal:** A 34-byte compressed message expands to 4096 bytes under 128-byte compressed, 2048-byte output, and 64x ratio limits. Decide and verify.
2. **Difficult edge:** Test a three-fragment compressed message followed by a dictionary-dependent second message in takeover and no-takeover modes.
3. **Should not activate:** Compression is disabled and every extension offer is rejected; scope the recommendation without generating a decompression fixture.

## Sources

Sourced facts:

- RFC 7692 defines permessage-deflate negotiation, message-level framing, and context-takeover parameters: https://www.rfc-editor.org/rfc/rfc7692.html
- WebSocket++ issue 1191 reports decompressed output exceeding its configured message limit before rejection: https://github.com/zaphoyd/websocketpp/issues/1191
- GitHub Advisory GHSA-gv2g-7h3v-q5f3 records a libsoup permessage-deflate resource-exhaustion flaw: https://github.com/advisories/GHSA-gv2g-7h3v-q5f3
- Nixpkgs issue 544160 tracks the corresponding libsoup vulnerability: https://github.com/NixOS/nixpkgs/issues/544160

The specific budgets, fail-closed oracle, test matrix, and recovery recommendations are original operational guidance, not requirements quoted from those sources.
