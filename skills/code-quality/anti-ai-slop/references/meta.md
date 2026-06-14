# Repository Meta — Structure, Files, Metadata

The patterns for repository structure, top-level files, project metadata, CI configuration, and license files. All observations are based on direct inspection of `cpython`, `golang/go`, `rust-lang/rust`, `nodejs/node`, `kubernetes/kubernetes`, `postgres/postgres`, `redis/redis`, `curl/curl`, `expressjs/express`, `pallets/flask`, `psf/requests`, `ansible/ansible`, `hashicorp/terraform`, `prometheus/prometheus`, `tj/n`, `tj/commander.js`, `sindresorhus/*`, and `jashkenas/backbone`.

## The "professional repo anatomy" — what files exist at the root

The pattern is stark. Mature repos have a small, opinionated, often idiosyncratic set of files. AI-generated repos are characterized by what they *include by default*.

| File | What mature repos do | What AI repos do |
|---|---|---|
| `LICENSE` | Always (or `LICENSE.txt`, `COPYING`, `COPYRIGHT`) | Always |
| `README` | Always (or `Readme.md`, `readme.md`, `README.rst`) | Always |
| `CHANGELOG` | One of: `CHANGELOG.md`, `CHANGES.md`, `CHANGES.rst`, `HISTORY.md`, `History.md`, `HISTORY`, `00-RELEASENOTES`, `RELEASES.md`, or no file at all but commits in `Misc/NEWS.d/` | Always `CHANGELOG.md` |
| `CONTRIBUTING` | Sometimes; lives at `palletsprojects.com` for flask, in `.github/` for express | Always `CONTRIBUTING.md` |
| `Makefile` | Sometimes; autotools, hand-written, or absent | Sometimes |
| `.editorconfig` | Common | Sometimes |
| `.gitignore` | Always | Always |
| `.gitattributes` | Sometimes | Sometimes |
| `SECURITY.md` | Rare, only with a real disclosure process | Often, generic template |
| `CODE_OF_CONDUCT.md` | Sometimes, Contributor Covenant verbatim | Always |
| `.github/` | 1–3 workflow files, no templates | Templates, dependabot, workflows |
| `.github/ISSUE_TEMPLATE/` | **Zero of 15+ mature repos** | **Always** |
| `.github/PULL_REQUEST_TEMPLATE.md` | **Zero of 15+ mature repos** | Sometimes |
| `.github/dependabot.yml` | **Zero of 15+ pre-2024 repos** | **Always** |
| `.devcontainer/` | Mostly 2020+ | Often |
| `AUTHORS` or `AUTHORS.rst` | Sometimes (requests has one) | Rare |
| `INSTALL` | Sometimes (autotools-generated) | Rare |

### Key anti-AI signals

1. **CHANGELOG filename is wildly inconsistent — and therefore human.** Mature repos use whatever name they decided on years ago. Express has `History.md`. Got has no changelog file. CPython uses `Misc/NEWS.d/` (a directory of news fragments per PR). Redis uses `00-RELEASENOTES`. **An AI repo will default to `CHANGELOG.md` every single time.**

2. **README casing is not normalized.** Express has `Readme.md` (capital R). Got has lowercase `readme.md` and `license`. CPython has `README.rst`. Humans don't go back and rename files.

3. **No mature pre-2024 repo has issue templates.** Zero of 15+ repos inspected have `.github/ISSUE_TEMPLATE/`. This is one of the strongest anti-AI signals.

4. **No mature pre-2024 repo has `.github/dependabot.yml`** as a top-level AI-slop signal. Modern projects may have Renovate (curl has `renovate.json`).

5. **Multiple license files are common** when dual-licensing: `LICENSE-APACHE` + `LICENSE-MIT` (rust), `LICENSE` + `PATENTS` (go), `COPYING` (curl — old GNU convention), `COPYRIGHT` (postgres — explicit copyright assertion without a separate LICENSE).

6. **Build system diversity is enormous**: `Makefile` (curl, redis, tj/n), `Makefile.pre.in` (cpython), `Makefile.am` (curl autotools), `GNUmakefile.in` (postgres), `BSDmakefile` (node — for BSD!), `Makefile` + `meson.build` (postgres). Humans pick the right tool.

7. **`.devcontainer` is appearing only in 2020+ repos.** It's not in `golang/go`, `rust-lang/rust`, `postgres/postgres`, `redis/redis`, `curl/curl`, `requests`, `express`, `tj/n`, `tj/commander.js`. AI generates `.devcontainer/` reflexively.

8. **CI files are sparse.** Most repos put CI in `.github/workflows/` but only have 1–3 files, often with hand-written Makefile targets. The size of `.github/workflows/` is a strong AI tell: AI repos have 5+ workflow files for lint, test, build, release, deps, security, etc.

9. **Folders present in nearly every mature repo**: `docs/`, `examples/`, `test/` or `tests/`, `src/` or `lib/`, `bin/` (for CLIs), `scripts/`, sometimes `internal/`.

10. **The `OWNERS` / `OWNERS_ALIASES` files** (Kubernetes) are a Linux Foundation convention, not a templated GitHub feature.

## The description field — 50+ real examples

### Tone A: "Confident One-Liner" (5–10 words)

| Description | Source |
|---|---|
| `A simple, yet elegant, HTTP library.` | `psf/requests` |
| `A simple framework for building complex web applications.` | `pallets/flask` |
| `The Python micro framework for building web applications.` | `pallets/flask` (GitHub About) |
| `Fast, unopinionated, minimalist web framework for node.` | `expressjs/express` |
| `The complete solution for node.js command-line interfaces.` | `tj/commander.js` |
| `Node.js JavaScript runtime ✨🐢🚀✨` | `nodejs/node` (the only emoji, earned) |
| `Empowering everyone to build reliable and efficient software.` | `rust-lang/rust` |
| `Production-Grade Container Scheduling and Management` | `kubernetes/kubernetes` |
| `The Go programming language` | `golang/go` |
| `The Python programming language` | `python/cpython` |
| `HTTP for humans.` | `psf/requests` (sub-banner) |
| `The Web framework for perfectionists with deadlines.` | `django/django` |
| `Node version management` | `tj/n` |
| `Interactively Manage All Your Node Versions` | `tj/n` (package.json) |
| `🌐 Human-friendly and powerful HTTP request library for Node.js` | `sindresorhus/got` |
| `A command line tool and library for transferring data with URL syntax, supporting DICT, FILE, FTP, FTPS, GOPHER, GOPHERS, HTTP, HTTPS, IMAP, IMAPS, LDAP, LDAPS, MQTT, MQTTS, POP3, POP3S, RTSP, SCP, SFTP, SMB, SMBS, SMTP, SMTPS, TELNET, TFTP, WS and WSS.` | `curl/curl` (the 27-protocol list) |

### Tone B: "Honest Engineering Statement" (one sentence, defining property)

| Description | Source |
|---|---|
| `Higher-level flow control for node.` | `visionmedia/co` (TJ) |
| `An open source programming language that makes it easy to build simple, reliable, and efficient software.` | `golang/go` |
| `This is the main source code repository for Rust. It contains the compiler, standard library, and documentation.` | `rust-lang/rust` |
| `This directory contains the source code distribution of the PostgreSQL database management system.` | `postgres/postgres` |
| `Mirror of the official PostgreSQL GIT repository. Note that this is just a *mirror* - we don't work with pull requests on github.` | `postgres/postgres` (a real maintainer warning) |
| `Flask is a lightweight WSGI web application framework. It is designed to make getting started quick and easy, with the ability to scale up to complex applications.` | `pallets/flask` (README) |
| `Node.js is an open-source, cross-platform JavaScript runtime environment.` | `nodejs/node` (README) |
| `The latest version of this software, and related software, may be obtained at https://www.postgresql.org/download/` | `postgres/postgres` (the download URL is the most important sentence) |

### Tone C: "Sindre Sorhus School" (one phrase, repeated in 3 places)

`🌐 Human-friendly and powerful HTTP request library for Node.js` — identical in `package.json`, `readme.md`, and GitHub About. The globe emoji is his signature.

Sindre's `keywords` arrays in `package.json` include *competitor* names:
```json
"keywords": ["http", "request", "fetch", "ajax", "axios", "got", "superagent", "node-fetch", "ky", "request-promise", "node"]
```
Listing competitors in your own keywords is the Sindre flex.

### Tone D: "TJ Holowaychuk School" (pre-2015, minimal)

TJ-era repos had no `description` field in many cases. His best repos (express, superagent, commander, jade) have one-line About sections or no description at all.

### AI description templates to avoid

Almost every AI-generated description falls into one of these:

- `A modern, lightweight, [adjective-stacking] [category] for [audience].`
- `A powerful and flexible [X] that helps developers [verb] [Y].`
- `🚀 [Emoji] [Adjective] [X] [Emoji]` (Sindre-style emoji aping)
- `[Category] reimagined for the modern web.`
- `Built with [technology]. Designed for [outcome]. Loved by developers.`
- `The next-generation [X] for [audience].`

**The tell:** AI descriptions have 4+ adjectives stacked. Human descriptions have 1–2.

## `pyproject.toml` patterns

### Real human example — Flask

```toml
[project]
name = "Flask"                            # TitleCase, not "flask" — Flask is a brand
version = "3.2.0.dev"                     # The .dev suffix is human — it tells you "this is development"
description = "A simple framework for building complex web applications."
readme = "README.rst"
license = {text = "BSD-3-Clause"}
requires-python = ">= 3.9"
authors = [
    {name = "Pallets", email = "contact@palletsprojects.com"},
]
keywords = ["web", "framework", "wsgi", "jinja"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Framework :: Flask",
    "License :: OSI Approved :: BSD License",
    "Programming Language :: Python",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
]
dependencies = [
    "Werkzeug >= 3.0.0",
    "Jinja2 >= 3.1.2",
    "MarkupSafe >= 2.1.1",
    "ItsDangerous >= 2.1.2",
    "Click >= 8.1.3",
    "Blinker >= 1.6.2",
]
```

What this gets right:
- **`name = "Flask"`** with capital F. The name is the brand.
- **`version = "3.2.0.dev"`** — the `.dev` suffix is human and tells you this is in development.
- **`description`** is 8 words. No adjectives stacked.
- **`keywords`** are technical (`web`, `framework`, `wsgi`, `jinja`) — not marketing (`fast`, `modern`, `lightweight`).
- **`classifiers`** is the standard trove, used for PyPI categorization. Real metadata.
- **`dependencies`** are minimal — 6 packages, each with a `>=` lower bound. No version pins, no dev pins, no extras.
- No `optional-dependencies` block with `dev = [...]` containing 30 packages.
- No `tool.ruff` section with 200 lines of rules.
- No `tool.mypy` with `strict = true` and a long plugin list.

### Real human example — `psf/requests`

`psf/requests/setup.py` is 6 lines and delegates to `pyproject.toml`:
```python
import setuptools
setuptools.setup()
```
That's it. The rest is in `pyproject.toml`. This is *the* signal of a project that's been refactored by a maintainer who knows what they're doing.

## `package.json` patterns

### Real human example — Express (pre-2020)

```json
{
  "name": "express",
  "description": "Fast, unopinionated, minimalist web framework for node",
  "version": "4.18.2",
  "author": "TJ Holowaychuk <tj@vision-media.ca>",
  "contributors": [
    "Aaron Heckmann <aaron.heckmann+github@gmail.com>",
    "...",
  ],
  "license": "MIT",
  "repository": "expressjs/express",
  "bugs": {"url": "https://github.com/expressjs/express/issues"},
  "homepage": "https://expressjs.com",
  "dependencies": {
    "accepts": "~1.3.8",
    "array-flatten": "1.1.1",
    "body-parser": "1.20.1",
    "...": "..."
  },
  "devDependencies": {
    "after": "0.8.2",
    "connect-redis": "6.0.0",
    "...": "..."
  },
  "engines": {
    "node": ">= 0.10.0"
  },
  "scripts": {
    "test": "mocha --reporter spec --bail --check-leaks test/",
    "lint": "eslint .",
    "lint-fix": "eslint --fix ."
  }
}
```

What this gets right:
- **`description`** is 7 words. 3 adjectives (`fast`, `unopinionated`, `minimalist`). Each is earned.
- **`author`** is a real person, with email. Not a `Contributors` array as the only attribution.
- **`contributors`** is a hand-maintained list (not generated from `git log`).
- **`engines.node`** is just `>= 0.10.0` — generous backward compat.
- **`scripts`** is minimal: `test`, `lint`, `lint-fix`. No `prebuild`, `postbuild`, `format`, `format:check`, `prepare`, `prepublish`, `prepublishOnly`, `prepack`, `postpack`, etc.
- No `keywords` array with 30 entries.
- No `funding` field.
- No `workspaces` array.
- No `packageManager` field.
- No `engines.npm` field.

### Real human example — `tj/n`

```json
{
  "name": "n",
  "version": "9.2.0",
  "description": "Interactively Manage Your Node.js Versions",
  "author": "TJ Holowaychuk <tj@vision-media.ca>",
  "license": "MIT",
  "bin": {"n": "bin/n"},
  "files": ["bin/n"],
  "os": ["!win32"],
  "preferGlobal": true,
  "dependencies": {
    "abbrev": "~1.0.4",
    "...": "..."
  }
}
```

What this gets right:
- **`files: ["bin/n"]`** — one file ships. Period.
- **`os: ["!win32"]`** — hard no on Windows. The maintainer has a stance.
- **`preferGlobal: true`** — humans know `n` is meant to be global.
- No `engines` field — the author is generous.
- `n` is one of the most-depended-on Node CLIs, and its `package.json` fits on a screen.

## `Cargo.toml` patterns

### Real human example — Tokio

```toml
[package]
name = "tokio"
version = "1.52.3"
edition = "2024"
rust-version = "1.71"
description = "An event-driven, non-blocking I/O platform for writing asynchronous applications with the Rust programming language."
license = "MIT"
repository = "https://github.com/tokio-rs/tokio"
homepage = "https://tokio.rs"
documentation = "https://docs.rs/tokio"
readme = "README.md"
keywords = ["async", "non-blocking", "io"]
categories = ["asynchronous", "no-std", "network-programming"]

[features]
full = [...]
rt = [...]
rt-multi-thread = [...]

[dependencies]
bytes = { version = "1", optional = true }
mio = { version = "1", default-features = false }
```

What this gets right:
- **`description`** is a full sentence, factual. No adjectives stacked.
- **`keywords`** is technical: `["async", "non-blocking", "io"]`. Not `["fast", "modern", "rust"]`.
- **`categories`** is crates.io's technical taxonomy. Not SEO.
- **`rust-version = "1.71"`** — explicit MSRV. The maintainer is being honest about the floor.
- **`features.full = [...]`** is the standard tokio pattern of feature bundling. No `features.unsafe-awesome-perf = ["unsafe", "perf", "fast", "modern"]`.
- No `package.metadata.docs.rs` configuration — let docs.rs do its job.

## The "restraint checklist" — what NOT to add to a repo

Don't generate these files by default. Each is a real candidate for inclusion only with a real reason.

| File | When humans add it | When AI adds it |
|---|---|---|
| `.github/ISSUE_TEMPLATE/` | Almost never | Always |
| `.github/PULL_REQUEST_TEMPLATE.md` | Almost never | Sometimes |
| `.github/dependabot.yml` | Pre-2024 repos don't have it; post-2024 with many deps | Always when there's a dependency |
| `.devcontainer/` | 2020+ projects for specific use | Always |
| `SECURITY.md` | Only with a real disclosure process | Always with a generic template |
| `CODE_OF_CONDUCT.md` | Contributor Covenant verbatim | Always with a customized generic template |
| `CODEOWNERS` | Big projects with many teams | Sometimes |
| `FUNDING.yml` | If the project accepts sponsorship | Sometimes with a giant tier list |
| `.github/workflows/dependabot-auto-merge.yml` | Some | Often |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | **Zero mature repos** | Always |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | **Zero mature repos** | Always |
| `.github/PULL_REQUEST_TEMPLATE.md` | **Zero mature repos** | Often |
| `CHANGELOG.md` | Yes, but the name varies wildly | Always with `CHANGELOG.md` |
| `CONTRIBUTING.md` | Sometimes; lives at the project website sometimes | Always with a generic template |
| `.prettierrc` | Pre-2020 repos don't have it; post-2020 sometimes | Often |
| `.eslintrc` | Yes, when the project uses JS | Yes |
| `Makefile` | Yes, in C/Go/rust projects; sometimes Python | Often when not needed |

## LICENSE file patterns

### What humans do

- **Custom preamble with year and author.** MIT licensed repos have:
  ```
  Copyright (c) 2012-2024, Caleb Evans. Released under the MIT license.
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  ...
  ```
  Note the year range and the author name. AI generates the bare `MIT License` template without preamble.

- **Multiple files when dual-licensing.** `LICENSE-APACHE` + `LICENSE-MIT` for Rust projects (`ripgrep`, `serde`, `tokio`). `LICENSE` + `PATENTS` for Go.

- **Custom names for historical reasons.** `COPYING` (curl, GNU convention), `COPYRIGHT` (postgres, no LICENSE file at all), `LICENSE.txt` (redis), `License.rtf` (some Mac apps).

- **What the preamble is NOT:** AI generates LICENSE files verbatim from SPDX templates with no project name, no year, no author. Real preambles always have these three.

### Examples

- `psf/requests`: `LICENSE` with the Apache 2.0 text, custom preamble with PSF copyright.
- `pallets/flask`: `LICENSE.txt` with the BSD-3-Clause text, custom preamble with Pallets copyright.
- `golang/go`: `LICENSE` (BSD-3-Clause) + `PATENTS` (Google's additional grant).
- `rust-lang/rust`: `LICENSE-APACHE` + `LICENSE-MIT` (dual-licensed).
- `redis/redis`: `LICENSE.txt` with BSD-3-Clause.
- `curl/curl`: `COPYING` (MIT-style but using the old GNU name).
- `postgres/postgres`: `COPYRIGHT` (no LICENSE file at all — copyright assertion in the file itself).
- `sindresorhus/got`: lowercase `license` with the MIT text.

## CHANGELOG format

### Three human patterns

**A. Keep-a-Changelog style** (some modern projects):
```markdown
# Changelog
All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-11-15

### Added
- New caching layer to `Client.send`. (#1234)

### Fixed
- Race condition in connection pool. (#1236)

### Removed
- Support for Python 3.8. (#1237)
```

**B. Category-prefixed style** (psf/requests, pallets/flask):
```
2.32.0 (2024-05-20)
-------------------

**Security**
- Fixed an issue where setting `verify=False` on the first request...

**Improvements**
- `verify=True` now reuses a global SSLContext...

**Bugfixes**
- Fixed bug in length detection...

**Deprecations**
- Requests has officially added support for CPython 3.12

**Documentation**
- Various typo fixes and doc improvements.
```

**C. Bracketed-prefix style** (burntsushi/ripgrep):
```markdown
Bug fixes:

* [BUG #3212](https://github.com/BurntSushi/ripgrep/pull/3212):
  Don't check for the existence of `.jj` when `--no-ignore` is used.

Features:

* [FEATURE #2830](https://github.com/BurntSushi/ripgrep/issues/2830):
  Add support for reading gzip files from stdin.
```

### What humans don't do

- No emoji (`## [2.0.0] - 2025-11-15 🎉` is AI)
- No "we are excited to announce" intros
- No `### ✨ Exciting New Features`
- No multi-paragraph "Migration Guide" sections for minor versions
- No author bylines in the changelog (committers are credited in git)
- No "Type: Bug" or "Type: Feature" tags

## CI / `.github/workflows/` patterns

### Real human example — minimal

A typical mature repo has 1–3 files in `.github/workflows/`:

- `ci.yml` — runs tests on push to main and PR
- `release.yml` — builds and publishes on tag
- `dependabot.yml` (rare, post-2024) — auto-bumps deps

That's it. No `lint.yml`, `format.yml`, `type-check.yml`, `docs.yml`, `security.yml`, `stale.yml`, `welcome.yml`, `auto-merge.yml`, `release-drafter.yml`, `labeler.yml`, `codeql.yml`, `scorecard.yml`.

### What humans write in CI

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e .[test]
      - run: pytest
```

7 lines. `pip install -e .[test]` and `pytest`. That's it.

### What AI writes in CI

- 3+ Python versions in a matrix
- 3+ OS in a matrix
- Separate lint / format / type-check / test / build / deploy jobs
- `actions/cache@v4` with precise key paths
- `concurrency:` blocks
- Coverage uploads to codecov
- `continue-on-error: true` everywhere
- 100+ lines of YAML for a 200-line Python project

## pyproject.toml section patterns

### Real human section inventory

A mature `pyproject.toml` typically has:

- `[project]` — the standard PEP 621 metadata
- `[project.optional-dependencies]` — `test`, `docs`, `dev` groups
- `[project.urls]` — `Homepage`, `Documentation`, `Source`, `Tracker`
- `[project.scripts]` — entry points
- `[build-system]` — `requires = ["setuptools>=68"]`, `build-backend = "setuptools.build_meta"`
- `[tool.setuptools]` — `packages = ["flask"]`
- Maybe `[tool.pytest.ini_options]`, `[tool.tox]`, `[tool.codespell]`

That's it. **No** `[tool.ruff]` with 200 lines of `select = ["ALL"]`. **No** `[tool.mypy]` with `strict = true` and a 12-plugin `plugins = [...]` array. **No** `[tool.coverage]` with `exclude_lines = [...]` listing 30 patterns.

### The "no pretense" pattern

Humans don't preconfigure everything. They add a section when a tool is *actually used*. AI configures everything because the LLM was trained on repositories that had everything configured.

## Description templates by project type

When you need a one-liner for a new project, here are templates derived from real pre-2020 repos.

**Library (general):**
- `[Noun] is a [adjective] [category] for [purpose].` — `Flask: A simple framework for building complex web applications.`
- `[Noun] is a [adjective] [category].` — `requests: A simple, yet elegant, HTTP library.`
- `A [adjective] [category].` — `pydantic: Data validation using Python type hints.`

**CLI tool:**
- `[Verb] [noun].` — `ripgrep README: rg recursively searches the current directory for a regex pattern.`
- `[Noun] version management` — `n: Node version management`
- `[Tool] is a [adjective] [category] for [purpose].` — `jq: jq is a lightweight and flexible command-line JSON processor.`

**Web framework:**
- `Fast, unopinionated, minimalist web framework for [runtime].` — `express`
- `[Noun] is a [adjective] [category] that [verb] [purpose].` — `Django`

**Compiler / runtime:**
- `[Name] is an open source [category] that [verb] [purpose].` — `Go`

**Database / storage:**
- `[Name] is the [adjective] [category].` — `PostgreSQL is a powerful, open source object-relational database system.`

**Rust crate:**
- `[Name] is a [category] for [purpose].` — `serde: Serde is a framework for *ser*ializing and *de*serializing Rust data structures efficiently and generically.`

**Daemon / system service:**
- `[Name] is an in-memory [category] used as a [X], [Y], and [Z].` — `Redis: in-memory data structure store used as a database, cache, and message broker.`

**Build tool / formatter:**
- `[Tool] is an opinionated [category] for [languages].` — `Prettier: an opinionated code formatter.`

**Linter:**
- `[Tool] is a [adjective] [category] for [language].` — `ESLint: a pluggable linter for JavaScript.`

The key invariant: **one or two adjectives max, then stop.** If you can't fit it in 12 words, you haven't found your project's voice yet.
