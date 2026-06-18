---
name: nasa-inspired-coding-rules
description: Use when writing, reviewing, or refactoring production code where reliability, portability, maintainability, explicit contracts, resource safety, and cross-language coding standards matter across Python, TS/JS, C, C++, Rust, or Go.
---

# NASA-Inspired Coding Rules

Use these rules to make code harder to break and easier to maintain. They are generalized from NASA Glenn Research Center's NPARC Alliance programming guideline for Fortran 90:
https://www.grc.nasa.gov/www/winddocs/guidelines/pgmstds.pdf

Source note: the linked document is language-specific and Fortran-oriented. Apply the practices, not the syntax. Do not present this skill as an official NASA standard for every language.

## Priority Order

When rules compete, optimize in this order:

1. Maintainability: another engineer can understand, modify, and extend it.
2. Portability: it behaves consistently across supported platforms, runtimes, compilers, and dependency versions.
3. Efficiency: it uses CPU, memory, IO, and network resources responsibly after correctness is protected.

Do not trade maintainability for clever speed unless profiling proves it is necessary and tests protect the behavior.

## Core Rules

### 1. Stay Inside Standard, Supported Language Features

- Prefer standard language features and mature library APIs over compiler, runtime, or framework-specific extensions.
- Isolate unavoidable platform-specific code behind a small interface.
- Document any compiler directive, build flag, unsafe block, FFI bridge, reflection trick, monkey patch, or runtime-specific behavior with why it exists and where it is valid.
- Avoid obsolete features, deprecated APIs, legacy control flow, and compatibility shims in new code.

Language cues:

| Language | Prefer | Avoid unless isolated |
| --- | --- | --- |
| Python | Current stable syntax, typing, stdlib protocols | Runtime monkey-patching, broad metaclass tricks |
| TS/JS | Strict TypeScript, standard Web/Node APIs | `any`, prototype mutation, nonstandard globals |
| C | C11/C17-compatible code per project policy | Compiler-only extensions in shared logic |
| C++ | Modern standard C++, RAII, standard containers | Raw ownership, preprocessor-heavy logic |
| Rust | Safe Rust, explicit feature flags | `unsafe` without a narrow proof and tests |
| Go | Standard library conventions, `go vet` clean code | Build tags that hide divergent behavior |

### 2. Organize by Purpose and Keep Modules Small

- Write modular code with cohesive files, packages, crates, or modules.
- Name files and directories for their domain purpose, not implementation accidents.
- Put related code together, but keep public interfaces small.
- Prefer one primary abstraction per file unless the local ecosystem convention says otherwise.
- Make dependency direction clear; low-level utilities should not import application workflows.

Good modules can be tested in isolation and explained in one sentence.

### 3. Make Types, Shapes, and Interfaces Explicit

- Declare variables, fields, parameters, return values, and data shapes explicitly where the language supports it.
- Treat implicit coercion as a risk. Convert deliberately at boundaries.
- Match function calls to declarations in argument count, order, type, and meaning.
- Use named constants for values that may change, encode domain rules, or are easy to mistype.
- For public APIs, encode input/output contracts with types, schemas, validators, or documentation close to the interface.

Language cues:

| Language | Contract tools |
| --- | --- |
| Python | Type hints, dataclasses, Pydantic or validators at IO boundaries |
| TS/JS | `strict`, discriminated unions, runtime validation for external data |
| C | Header declarations, fixed-width types, explicit casts, `const` |
| C++ | `const`, references, RAII types, concepts or static assertions when useful |
| Rust | Strong domain types, `Result`, `Option`, traits with clear bounds |
| Go | Small interfaces, struct tags used deliberately, explicit error returns |

### 4. Control Ownership, Memory, and Resources

- Allocate memory and other resources as late as practical; release them as soon as ownership ends.
- Prefer language-native lifetime management: `with`/context managers, `try/finally`, RAII, `defer`, destructors, `Drop`.
- Bound buffers, arrays, slices, maps, queues, and caches. Validate indices and lengths before access.
- Do not hide global mutable state behind convenience helpers. Pass dependencies explicitly or use a controlled context object.
- Treat files, sockets, database handles, locks, timers, workers, and subscriptions as resources that need a lifecycle.

Review question: "What owns this, and when is it released?"

### 5. Keep Functions Boring, Single-Entry, and Side-Effect-Aware

- Prefer functions with one clear purpose, explicit inputs, and explicit outputs.
- Avoid hidden side effects in functions that look like pure computation.
- Mark mutation at the interface: naming, types, `mut`, pointer/reference use, or documentation.
- Keep argument lists coherent. If several parameters travel together, introduce a value object, struct, dataclass, or options type.
- Replace long conditional sections with named helper functions when that makes the main path easier to read.

Functions should be easy to test without constructing the whole system.

### 6. Make Control Flow Obvious

- Use structured control flow: loops, early returns, pattern matching, guard clauses, and small helpers.
- Avoid `goto`, labeled jumps, fallthrough-heavy switches, callback pyramids, and deeply nested conditionals unless they are the clearest option in that language.
- Label or comment the end of long blocks only when extraction is not practical.
- Never put multiple meaningful statements on one line.
- For error paths, make cleanup and propagation explicit.

If a reader has to simulate the control flow to understand it, simplify.

### 7. Handle Input, Output, and Errors Deliberately

- Validate external input at the boundary before it reaches domain logic.
- Check errors from IO, parsing, network, database, subprocess, and serialization operations.
- Preserve enough context in errors to diagnose failures without leaking secrets.
- Use recoverable error types for expected failures and fail fast for invariant violations.
- Make retry, timeout, idempotency, and partial-write behavior explicit for IO-heavy code.

Language cues:

| Language | Error discipline |
| --- | --- |
| Python | Catch narrow exceptions; use context-rich errors; avoid bare `except` |
| TS/JS | Handle rejected promises; validate unknown JSON before trust |
| C | Check return codes; define ownership on error paths |
| C++ | Define exception policy; keep destructors safe; avoid partial states |
| Rust | Use `?` with contextual errors; reserve `panic!` for invariants |
| Go | Check `err`; wrap with context; avoid swallowing errors |

### 8. Prefer Readable Formatting and Naming

- Follow the project's formatter and linter. If none exists, add or propose one before style grows inconsistent.
- Keep line length reasonable for the codebase and language.
- Indent block contents consistently; avoid tabs unless the language convention requires them.
- Use descriptive names that match domain terminology.
- Do not reuse names that shadow important imports, globals, types, or outer variables.
- Use whitespace to reveal structure, not to create decorative alignment that is hard to maintain.

Readable code should make domain intent visible before implementation mechanics.

### 9. Comment Intent, Constraints, and Surprises

- Comment why code exists, why an unusual approach is necessary, and which constraint it satisfies.
- Do not repeat what the next line already says.
- Put public API documentation near the API.
- Document key local variables only when their role is not obvious from name and type.
- Add source notes for numerical formulas, protocol details, compatibility hacks, and security-sensitive decisions.

A good comment prevents a future "cleanup" from reintroducing the bug.

### 10. Compile, Analyze, and Test With Production-Like Settings

- Test with the same optimization, runtime mode, feature flags, and platform assumptions used in production.
- During development, also run stricter diagnostics: warnings as errors where practical, sanitizers, race detectors, type checks, linters, formatters, and runtime bounds checks.
- Keep build and test commands repeatable through standard project tooling.
- Add regression tests for fixed defects and risky rules.
- Treat warning growth as quality debt, not background noise.

Minimum tool expectations:

| Language | Baseline checks |
| --- | --- |
| Python | tests, type checker if used, linter/formatter |
| TS/JS | tests, `tsc --noEmit`, linter/formatter |
| C | compiler warnings, tests, sanitizer or static analysis for risky code |
| C++ | compiler warnings, tests, sanitizer or static analysis for risky code |
| Rust | `cargo test`, `cargo clippy`, `cargo fmt` |
| Go | `go test`, `go vet`, `gofmt` |

## Review Checklist

Use this checklist before merging reliability-sensitive code:

- Is the code modular, named by purpose, and easy to test in isolation?
- Are external interfaces, data shapes, ownership, and lifetimes explicit?
- Are conversions, casts, nullability, optionality, and error paths deliberate?
- Are arrays, slices, buffers, and collection accesses bounded?
- Are resources closed, released, cancelled, or deallocated on every path?
- Are functions free of surprising side effects?
- Is control flow structured and shallow enough to read without simulation?
- Are constants named and close to the domain rule they represent?
- Are comments explaining intent rather than restating syntax?
- Was the change tested with production-like settings plus strict diagnostics?

## Common Mistakes

| Mistake | Safer practice |
| --- | --- |
| "This helper is small, so hidden global state is fine." | Pass dependencies explicitly until a real lifecycle owner emerges. |
| "The type checker knows enough." | Validate untrusted runtime data before converting it into trusted types. |
| "The test passed in debug mode." | Re-test with production flags, optimization, feature gates, and concurrency settings. |
| "The language has memory safety." | Still manage files, sockets, locks, tasks, cancellations, caches, and subscriptions. |
| "The code is self-documenting." | Self-documenting code still needs comments for domain constraints and non-obvious tradeoffs. |

## Output Pattern

When applying this skill, structure feedback as:

1. Reliability risks: concrete breakage risks first.
2. Portability and build risks: platform, runtime, compiler, and dependency assumptions.
3. Maintainability issues: naming, organization, contracts, comments, and complexity.
4. Recommended changes: minimal edits that improve safety without over-engineering.
5. Verification: exact tests, static checks, or runtime diagnostics to run.
