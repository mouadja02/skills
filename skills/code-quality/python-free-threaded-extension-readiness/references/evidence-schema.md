# Evidence JSON Schema (Operational Contract)

The helper intentionally uses a small, strict JSON contract rather than probing or importing untrusted wheels.

```json
{
  "schema_version": 1,
  "project": "example",
  "claim": "ready",
  "native_extensions": [
    {
      "name": "example._core",
      "gil_declaration": "not-used",
      "stress": {"runs": 50, "threads": 4, "completed": true, "failures": 0},
      "tsan": "clean"
    }
  ],
  "builds": [
    {"mode": "gil", "passed": true, "py_gil_disabled": false},
    {"mode": "free-threaded", "passed": true, "py_gil_disabled": true}
  ],
  "dependencies": [
    {"name": "native-dependency", "version": "1.2.3", "free_threaded_support": "yes"}
  ]
}
```

## Fields

- `schema_version`: must be integer `1` (booleans are rejected as integers).
- `project`: non-empty string.
- `claim`: `ready`, `experimental`, `gil-required`, or `not-applicable`.
- `native_extensions`: array. An empty array returns `not_applicable` only with claim `not-applicable` and empty `builds`/`dependencies`; use this only when no native extension is shipped.
- `builds`: exactly one effective `gil` and one `free-threaded` record. Duplicate modes are invalid.
- `passed`: boolean test result.
- `py_gil_disabled`: boolean measured from the interpreter. It must be `false` for `gil` and `true` for `free-threaded`.
- `gil_declaration`: `not-used`, `used`, or `unknown`. A readiness claim requires `not-used`.
- `stress`: requires integer `runs >= 10`, integer `threads >= 2`, `completed: true`, and `failures: 0`.
- `tsan`: `clean`, `findings`, or `not-run`. Findings always block. `not-run` blocks only with `--require-tsan`.
- `dependencies`: array of non-empty name/version strings and `free_threaded_support` set to `yes`, `no`, or `unknown`. Readiness requires `yes`.

Unknown keys are rejected so collector drift cannot silently weaken the gate. JSON constants such as `NaN` and `Infinity` are rejected. Parse and I/O errors exit `2`; they are not converted into a valid blocked report.
