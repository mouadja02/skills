---
name: python-free-threaded-extension-readiness
description: Use when auditing a CPython C/C++/Cython/Rust extension for free-threaded Python, a `t`-suffixed ABI wheel, GIL opt-out, native race, callback crash, or free-threaded release gate.
version: "1.0.0"
license: MIT
---

# Python Free-Threaded Extension Readiness

## When to Use

- A native Python extension must support a free-threaded CPython build.
- A project is considering `cp313t`/`cp314t` wheels or a GIL opt-out declaration.
- Import works but stress, callback, teardown, or ThreadSanitizer runs fail.
- A release needs evidence that native code and dependencies are safe without the GIL.

Do **not** activate for pure-Python thread-pool tuning, ordinary asyncio debugging, or a package that explicitly does not plan to publish free-threaded support. For pure-Python compatibility, use CPython's free-threading Python HOWTO instead.

## Prerequisites

- A regular CPython build and a matching free-threaded build.
- The project's normal native build and test toolchain.
- A small workload that crosses the extension boundary from at least two threads.
- Optional: a ThreadSanitizer-instrumented build for C/C++ race detection.

Never infer readiness from import success, a wheel tag, or a module GIL declaration alone. Run this workflow in disposable CI or a clean worktree; sanitizers and stress tests can be slow and nondeterministic.

## Quick Reference

| Evidence | Minimum release-gate interpretation |
| --- | --- |
| `sysconfig.get_config_var("Py_GIL_DISABLED")` | Confirms the test interpreter is free-threaded |
| `Py_mod_gil` / `PyUnstable_Module_SetGIL` / binding equivalent | Declares whether import may leave the GIL disabled; it does not prove safety |
| Regular + free-threaded matrix | Separates ordinary regressions from no-GIL failures |
| Repeated multithread fixture | Exercises shared state, callbacks, and teardown |
| Dependency inventory | Prevents an unsafe transitive native module from being overlooked |
| ThreadSanitizer | Strong supplementary race evidence; investigate every finding |

Helper:

```bash
python3 scripts/audit_free_threaded.py evidence.json
python3 scripts/audit_free_threaded.py --require-tsan evidence.json
```

The helper reads local JSON only, makes no network calls, writes nothing, rejects malformed/non-finite input, and exits `0` for `ready` or `not_applicable`, `1` for an incomplete/unsafe gate, and `2` for invalid evidence. See [`references/evidence-schema.md`](references/evidence-schema.md).

## Workflow

### 1. Freeze the claim and matrix

Write down the exact supported Python versions, platforms, architectures, extension modules, wheel tags, and whether each module claims it can run with the GIL disabled. Test the same source commit in both builds. Do not turn on a GIL opt-out merely to make the interpreter stay free-threaded.

Completion criteria:

- The regular and free-threaded interpreter identities are captured.
- Every shipped native module and native transitive dependency is listed.
- The release claim says either **ready**, **GIL-required**, or **experimental**.

### 2. Prove interpreter and module mode

Capture these values in each environment:

```bash
python - <<'PY'
import sys, sysconfig
print(sys.version)
print(sys.implementation.cache_tag)
print(sysconfig.get_config_var("Py_GIL_DISABLED"))
PY
```

For a multi-phase C extension, inspect the `Py_mod_gil` slot. For a single-phase extension, inspect the guarded `PyUnstable_Module_SetGIL()` call. Use the binding framework's documented equivalent where applicable. If a module does not explicitly support free-threading, retain its GIL requirement and record that limitation.

**Sourced fact:** CPython's extension HOWTO requires an explicit declaration for a module that supports running with the GIL disabled; otherwise importing the extension can enable the GIL. The declaration is a promise by the extension, not a runtime verifier. [CPython extension HOWTO](https://docs.python.org/3/howto/free-threading-extensions.html)

### 3. Audit unsafe API classes before stress testing

Inspect each path that executes without the GIL:

1. Replace unsafe borrowed-reference patterns with documented strong-reference alternatives when another thread can mutate the container.
2. Protect mutable C/C++ globals, registries, caches, lazy initialization, and reference-count-adjacent state.
3. Review Python-object access from foreign threads and every callback into Python.
4. Review object finalization, TLS destructors, interpreter shutdown, module teardown, and fork behavior.
5. Follow free-threaded allocator requirements; do not assume ordinary `pymalloc` behavior.
6. Use CPython critical sections only according to their documented semantics; they are not a blanket substitute for application locking.

**Sourced facts:** CPython documents borrowed-reference hazards, container locking, critical sections, allocator rules, and thread-state handling for free-threaded extensions. [CPython extension HOWTO](https://docs.python.org/3/howto/free-threading-extensions.html)

### 4. Exercise the failure boundary

Use one fixture per shared-state boundary. Each fixture should:

- synchronize at least two workers so calls overlap;
- repeat enough times to cover creation, mutation, callbacks, exceptions, and teardown;
- use deterministic invariants (counts, values, ownership, and clean exit), not timing alone;
- run under the ordinary and free-threaded builds;
- run in a subprocess when a crash or deadlock is plausible, with a timeout and captured exit status.

A crash, hang, invariant failure, sanitizer finding, or GIL unexpectedly becoming enabled is a failed gate. After a fix, prove the original fixture fails on the unfixed revision (when safe) and passes repeatedly on the fixed revision.

### 5. Add sanitizer evidence

When the native toolchain supports it, build CPython and the extension with compatible ThreadSanitizer settings, then run the focused overlap fixtures before the broad suite. Preserve the sanitizer report and symbolized stacks outside the source tree. Classify suppressions narrowly; never suppress an unknown race to make CI green.

**Recommendation:** TSan is optional for an initial experimental claim but should be required for a strong free-threaded claim involving mutable native state. The helper enforces this policy only with `--require-tsan`.

### 6. Gate dependencies and wheels

For every native dependency, record a version and an explicit support result (`yes`, `no`, or `unknown`). Build wheels from the same reviewed commit and verify them in clean regular and free-threaded environments. Do not relabel an ordinary wheel or treat a `t` suffix as behavioral proof.

Run the evidence helper after the real tests:

```bash
python3 scripts/audit_free_threaded.py --require-tsan evidence.json
```

Release only when the report is `ready`. If the report is `blocked`, either fix the evidence boundary or publish with the GIL required. An `unknown` dependency, missing matrix leg, untested stress path, or unreviewed sanitizer finding is not evidence of readiness.

## Failure Recovery

- **Import enables the GIL:** remove or defer the no-GIL claim, inspect the module declaration and every imported native dependency, then rerun from a fresh process.
- **Only the free-threaded leg fails:** minimize to one shared-state boundary; add barriers and subprocess timeouts before changing synchronization.
- **TSan reports a race:** retain the full stack, reproduce with the smallest fixture, fix ownership/synchronization, and rerun both matrix legs.
- **Callback or shutdown crashes:** isolate callback entry, thread-state attachment, TLS destruction, finalizers, and interpreter teardown in separate subprocess fixtures.
- **Dependency support is unknown:** pin a version with documented/tested support or keep the GIL-required publication path.
- **Evidence JSON is invalid:** fix collection; do not reinterpret a parser/I/O error as an unsafe result.

## Objective Verification

A release candidate is complete only when:

- both regular and free-threaded builds passed from the same source revision;
- the free-threaded identity was measured, not inferred from a filename;
- every native module's GIL declaration matches its claim;
- overlapping stress fixtures completed repeatedly with zero failures;
- all native dependencies have explicit positive support evidence;
- TSan is clean when policy requires it;
- the ordinary build remains green; and
- the helper reports `ready` with exit `0`.

## Evaluation Prompts

1. **Normal:** “Audit this two-module `cp314t` wheel. Both matrix legs passed, both modules opt out of the GIL, 50 four-thread stress runs passed, dependencies are supported, and TSan is clean.”
2. **Difficult edge:** “Import succeeds, but one module's declaration is unknown, callbacks were tested once, a dependency's support is unknown, and TSan found a race. Can we ship `cp314t`?”
3. **Should not activate:** “Tune an asyncio HTTP client's connection pool; the project has no native extensions and makes no free-threaded wheel claim.”

## Sources and Scope

- [PEP 703 — Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [CPython: C API Extension Support for Free Threading](https://docs.python.org/3/howto/free-threading-extensions.html)
- [CPython: Python Support for Free Threading](https://docs.python.org/3/howto/free-threading-python.html)
- [py-free-threading guide](https://py-free-threading.github.io/)
- [NumPy issue: TSan race under free-threading](https://github.com/numpy/numpy/issues/31179)
- [pybind11 issue: free-threaded type registry races](https://github.com/pybind/pybind11/issues/5421)
- [pybind11 issue: free-threaded callback crash](https://github.com/pybind/pybind11/issues/5894)
- [Meta engineering report on Python free-threading adoption](https://engineering.fb.com/2025/05/05/developer-tools/enhancing-the-python-ecosystem-with-type-checking-and-free-threading/)

The CPython documents and PEP define behavior. Project issues demonstrate failure modes but are not normative. This skill and helper are original MIT-licensed synthesis; no source code or prose was copied from those sources.
