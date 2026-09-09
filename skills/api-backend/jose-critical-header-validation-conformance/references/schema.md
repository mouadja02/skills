# Input Schema

The validator accepts a single JSON object with one of two mutually exclusive
inputs plus an optional capability list:

```json
{
  "header": {"alg": "HS256", "crit": ["x-custom"], "x-custom": true},
  "supported_extensions": ["x-custom"]
}
```

- `header` — a decoded JOSE protected header object (recommended). `crit` is read exactly as given.
- `token` — (alternative) a synthetic compact JWS string; the validator decodes only the first segment.
- `supported_extensions` — optional list of header-parameter names the recipient understands. `[]`/absent means no extensions are understood, so every extension name in `crit` is rejected (fail closed).

Output keys: `ok`, `classification` (`ready` | `blocked` | `not_applicable`), `crit_entries`, `findings`, `violations` (each with `id` and `detail`).

Exit codes: `0` = `ready`/`not_applicable`, `1` = `blocked`, `2` = input handling failed.
