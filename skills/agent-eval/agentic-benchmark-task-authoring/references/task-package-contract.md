# Task package contract

The package format below is the Harbor directory contract (documented at <https://docs.harborframework.com/tasks/overview>, <https://docs.harborframework.com/tasks/configuration>, <https://docs.harborframework.com/tasks/verifier>, <https://docs.harborframework.com/tasks/separate-verifier>, <https://docs.harborframework.com/tasks/artifacts>). Any runner that implements the same layout — instruction, environment spec, solution, and a verifier that writes a reward file — accepts it unchanged. Harbor is Apache-2.0; this package redistributes no Harbor code.

## Layout

```
my-task/
├── instruction.md          # agent-facing contract only
├── task.toml               # configuration and metadata
├── environment/
│   ├── Dockerfile          # agent environment (or docker-compose.yaml / Apptainer .def)
│   └── .dockerignore
├── solution/
│   └── solve.sh            # oracle, executable, non-interactive
└── tests/
    ├── Dockerfile          # optional dedicated verifier image
    ├── test.sh             # verifier entrypoint
    └── test_outputs.py     # content assertions (any language)
```

`tests/.harborignore` excludes local development files from sandbox uploads, publication, and content hashes. Supply `.dockerignore` as well when using a separate verifier.

## task.toml fields that change behavior

| Field | Effect | Authoring rule |
|---|---|---|
| `schema_version` | Task format version | Pin it (`"1.4"` at time of writing) |
| `artifacts` (top level, before any section header) | Paths collected after the agent runs and copied into the verifier | Declare every agent-produced path the grader reads |
| `[verifier].timeout_sec` | Verifier wall clock | Set explicitly; unbounded runs hide hangs |
| `[verifier].environment_mode` | `shared`, `separate`, or omitted | Use `separate` for graded benchmarks |
| `[verifier].environment.network_mode` | Verifier egress baseline, defaults to `public` | `no-network`, or `allowlist` + exact `allowed_hosts` |
| `[agent].timeout_sec` | Agent wall clock | Set explicitly |
| `[environment].network_mode` | Agent egress baseline, defaults to `public` | `no-network` unless the workflow needs pinned hosts |
| `[environment].build_timeout_sec` | Image build budget | Raise for heavy images |
| `[metadata]` | Free-form author metadata | Record category, difficulty rationale, and source terms |

### Mode resolution (verifier)

| `environment_mode` | `[verifier.environment]` | Result |
|---|---|---|
| omitted | omitted | `shared` |
| omitted | present | `separate` |
| `separate` | omitted | `separate`, copy of top-level `[environment]` |
| `separate` | present | `separate` with verifier-specific resources |
| `shared` | present | configuration error |

Image selection order: `[verifier.environment].docker_image`, then `tests/Dockerfile`/`tests/docker-compose.yaml`, then `[environment].docker_image`, then `environment/Dockerfile`. When the verifier inherits the agent environment, Harbor uploads `tests/` to `/tests/`; dedicated verifier images must bundle the tests themselves.

## Reward contract

The verifier writes exactly one reward channel:

- `/logs/verifier/reward.txt` — a single number, normally `1` or `0`
- `/logs/verifier/reward.json` — labeled numeric metrics; preferred when both exist

Default the reward to 0 and promote it to 1 only after every assertion passed. A grader that writes the reward before asserting can award credit for a failed run.

## Trust boundary

The verifier is a separate principal from the agent:

1. **Isolation.** `shared` verification runs the grader inside the agent's container, where the agent may have left a modified interpreter, a hostile `PATH` entry, or a writable `/tests`. Use `separate` mode for anything published.
2. **Egress.** A verifier with `public` network can be steered by fetched content and is not reproducible. Keep it `no-network`, or allowlist exact hosts.
3. **Artifact transfer.** Undeclared outputs do not reach a separate verifier. Declared artifacts are packed, extracted with a path-safe filter, stripped of setuid/setgid bits and out-of-tree symlinks, and restored at their original source path.
4. **Untrusted content.** Artifact contents are still agent-authored bytes: parse strictly, never `eval`, never execute an artifact as a grader.
5. **Answer separation.** Graders, expected outputs, and reference solutions stay outside the agent image, mounts, and instruction. If the full authoring bundle is public, its fixtures are no longer held-out evidence.

The package validator enforces the artifact contract mechanically: every sandbox path a grader script touches must be declared, except paths whose basename ships inside `environment/` (read-only inputs baked into the agent image, which the verifier's environment copy already contains).

## Failure modes worth testing every time

- Output present but empty, or present with the wrong schema.
- Output written to a different path than the instruction specifies.
- Correct answer produced by copying an expected fixture visible in the environment.
- Verifier run twice against the same trial producing different rewards (nondeterministic ordering, timestamps, or network dependence).
- Absolute path that only exists on one runtime (for example a host-specific `/home/...` path inside `test.sh`).
