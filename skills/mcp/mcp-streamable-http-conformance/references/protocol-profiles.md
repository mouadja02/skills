# Protocol Profiles and Transcript Format

Accessed 2026-07-19. Profiles are conservative, explicit snapshots. Re-open the linked specification before production use.

## `stable-2025-11-25`

Normative source: [MCP 2025-11-25 Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).

The validator checks a bounded subset of the stable Streamable HTTP rules:

- POST `Accept` lists `application/json` and `text/event-stream`.
- `MCP-Protocol-Version` is exactly `2025-11-25` on POST.
- GET is available for a standalone SSE stream and for resumption.
- `Mcp-Session-Id` is permitted; the validator does not assess entropy or authentication.
- `Last-Event-ID` resumption uses GET, not replay of the original POST.
- split SSE chunks are buffered until a blank-line event boundary;
- exact duplicate JSON-RPC payloads on different overlapping streams are reported as possible broadcasting; duplicates with a JSON-RPC ID are errors, while ID-less notifications require manual correlation and are warnings.

The helper does not prove every lifecycle, authorization, Origin, or SSE requirement. Use it as a transcript preflight, then test the exact client, server, and intermediary.

## `draft-2026-07-28`

**Non-normative draft snapshot. Do not present it as a released protocol.**

Source snapshot: [draft Streamable HTTP at modelcontextprotocol/modelcontextprotocol commit `26897cc322f356487da89113451bd16b520b9288`](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/26897cc322f356487da89113451bd16b520b9288/docs/specification/draft/basic/transports/streamable-http.mdx). The repository file labels the proposed revision `2026-07-28`; this skill was checked on 2026-07-19, before that date.

The bundled draft profile checks only the transition relevant to this workflow:

- POST-only MCP endpoint; standalone GET and DELETE are rejected.
- protocol-level `Mcp-Session-Id`, resumable SSE event IDs, and `Last-Event-ID` are rejected.
- `MCP-Protocol-Version`, `Mcp-Method`, and `params._meta.io.modelcontextprotocol/protocolVersion` must agree with the profile.
- a disconnected request is never automatically replayed. The report permits a manual fresh-ID reissue only when the fixture explicitly says `"idempotent": true`; otherwise it says `do-not-replay`.

Accepted [SEP-2567](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2567) and [SEP-2575](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2575) establish the direction of the draft changes. They do not turn a draft profile into a stable release.

## Normalized Transcript JSON

```json
{
  "profile": "stable-2025-11-25",
  "exchanges": [
    {
      "id": "tool-call-1",
      "concurrent_group": "overlap-1",
      "idempotent": false,
      "request": {
        "method": "POST",
        "headers": {
          "Accept": "application/json, text/event-stream",
          "MCP-Protocol-Version": "2025-11-25"
        },
        "body": {"jsonrpc": "2.0", "id": 41, "method": "tools/call"}
      },
      "response": {
        "status": 200,
        "headers": {"Content-Type": "text/event-stream"},
        "chunks": [
          "id: e-1\ndata: {\"jsonrpc\":\"2.0\",\"id\":41,",
          "\"result\":{}}\n\n"
        ],
        "disconnected": true
      }
    }
  ]
}
```

Rules for fixtures:

- Store redacted metadata only. Replace credentials, cookies, authorization headers, tool arguments, and user content before creating the file.
- Header names are compared case-insensitively; duplicate case variants fail.
- `chunks` are strings in observed order. Preserve chunk boundaries to test buffering, but redact event data.
- Set the same `concurrent_group` only on exchanges whose SSE streams overlapped; cross-stream duplicate detection is scoped to that group.
- `idempotent` is an explicit operator assertion, not inferred from the tool name or HTTP method.
- A parse/I/O error exits `2`; a parsed but non-conforming transcript exits `1`; a conforming transcript exits `0`.
- Strict JSON is required. `NaN`, `Infinity`, malformed shapes, unknown profiles, and incomplete SSE events fail closed.

## Known Limits

- This is not a packet-capture parser and never opens a socket.
- Exact duplicate payload detection is conservative. Review whether two byte-identical messages are legitimately distinct before treating it as confirmed broadcast.
- The helper does not validate all JSON-RPC schemas, OAuth, HTTP caching, proxies, TLS, or application semantics.
- Profile changes require source review, a version bump, regression fixtures, and a dated citation update.
