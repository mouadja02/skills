# Trace Schema

The helper accepts one UTF-8 JSON object:

```json
{
  "schema_version": 1,
  "kind": "grpc_deadline_trace",
  "rpc_type": "unary",
  "missing_deadline_policy": "block",
  "initial_timeout": "2S",
  "server_max_ns": 3000000000,
  "hops": [
    {"name": "proxy", "elapsed_ns": 250000000, "forwarded_timeout": "1750m"}
  ],
  "server": {
    "elapsed_since_initial_ns": 1450000000,
    "work_active": false,
    "cancellation_observed": false,
    "status": "OK"
  }
}
```

`rpc_type` is `unary`, `client_streaming`, `server_streaming`, or `bidi_streaming`. Durations ending in `_ns` are non-negative JSON integers; booleans and floats are rejected. `server_max_ns`, `server`, and `initial_timeout` are optional. If `initial_timeout` is absent, `missing_deadline_policy` controls classification and hops are not evaluated.

The helper is data-only: it does not contact a server, parse payloads, or change clocks/processes. `input_error` means the document could not establish protocol evidence. A parsed trace with invalid timeout metadata is instead `blocked` with `invalid_timeout`.
