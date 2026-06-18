---
name: anti-ai-slop
description: Use when writing, editing, or reviewing code, READMEs, docs, commits, changelogs, or any repo content. Pre-2020 human style — terse, opinionated, restrained, with project voice. Blocks the LLM tics: emoji headers, "leverage", "robust", "seamless", "delve", defensive bloat, type-hint overkill, marketing prose, "Whether you're X or Y", verbose error messages, and the rest of the AI tells catalogued from cpython, requests, flask, git, ripgrep, express, kubernetes, serde, go stdlib, and other pre-2020 reference repos. Triggers on "anti-ai", "human-style", "professional code", "clean code", "no slop", "write it like a human", or any time the agent is producing code/docs that should look hand-written.
---

# Anti-AI-Slop

A practical, opinionated guide for writing code, docs, and repo content that reads as if a thoughtful human wrote it before 2020. Built from a forensic scan of `cpython`, `requests`, `flask`, `sqlalchemy`, `httpx`, `git`, `linux`, `curl`, `ripgrep`, `serde`, `tokio`, `express`, `kubernetes`, `moby`, `sinatra`, `django`, `sindresorhus/*`, and 50+ other pre-AI reference repos.

## Activation

This skill is **always active** when the agent produces any of:

- Source code (Python, JS/TS, Go, Rust, C, shell, SQL, etc.)
- README, CONTRIBUTING, CHANGELOG, design docs
- Commit messages, PR descriptions, issue text, code-review replies
- API error messages, log strings, docstrings, type stubs
- Test code, fixture data, examples, tutorials
- Project metadata (`pyproject.toml`, `package.json`, `Cargo.toml` descriptions)
- Comments, inline docs, JSDoc, reST, doc-comments

If the user says "write it like a human", "no AI slop", "professional", "clean", "ship it", or anything implying craftsmanship — this skill applies in full force.

## Core principles (read these first)

1. **Restraint beats completeness.** A real maintainer deletes more than they add. A 30-line README with one code example beats a 300-line one with badges, a TOC, and emoji headers.
2. **Pointers, not explanations.** Docs say "see X" instead of "X is a comprehensive solution that…". Changelogs say "(#1234)" instead of restating the diff in prose.
3. **Project voice, not product voice.** "It is under active development" beats "Welcome to Remix 3, the future of…".
4. **Imperfection is human.** Typos, commented-out code, `XXX` markers, `TODO`s, inconsistent quoting. AI code is too clean; the absence of imperfection is itself a tell.
5. **Stance, not neutrality.** Real maintainers have opinions. "We don't support Windows" is human. "Cross-platform compatibility considerations are evaluated on a case-by-case basis" is AI.
6. **Brevity is respect.** The reader is technically competent. Skip the onboarding theatre.
7. **The name is the documentation.** `def factorial(n): return 1 if n == 0 else n * factorial(n-1)` needs no comment. Comments are for *why*, never for *what*.

## Mandatory rules — apply to every line you write

### Banned words and phrases

These phrases appear **zero times** across the surveyed pre-2020 reference repos. If you use one, delete it and rewrite the sentence.

**Marketing / hype:** `leverage`, `seamless`, `seamlessly`, `robust`, `cutting-edge`, `state-of-the-art`, `blazing fast`, `lightning fast`, `next-generation`, `best-in-class`, `world-class`, `production-grade`, `battle-tested`, `modern web`, `modern development`, `highly performant`, `scales seamlessly`, `drop-in replacement`, `out of the box`, `supercharge`, `turbocharge`, `revolutionize`, `transformative`, `empower`, `unlock the power`, `harness the power`, `elevate your workflow`.

**Filler:** `delve into`, `delve deeper`, `navigate the complexities`, `navigate the intricacies`, `in today's fast-paced world`, `in the realm of`, `in the world of`, `it is worth noting that`, `it's important to note`, `furthermore`, `moreover`, `tapestry`, `myriad of`, `plethora of`, `whether you're a beginner or an expert`, `whether you're X or Y`, `everything you need to know about`, `a comprehensive guide to`, `with just a few lines of code`, `in just a few clicks`.

**Closing flourishes:** `happy coding!`, `that's it! now go build something amazing!`, `and there you have it!`, `let's dive in!`, `buckle up!`, `let's get started!`.

**Replacements:**
- `leverage` → `use`
- `robust` → (delete; say what makes it robust) or `handles X, Y, Z`
- `seamless` → (delete) or `without re-implementing X`
- `utilize` → `use`
- `facilitate` → `help`, `let`, or (delete)
- `in order to` → `to`

### Banned structures

- **Emoji in section headers** (`## 🚀 Quick Start`, `## ✨ Features`, `## 📚 Documentation`, `## 🤝 Contributing`, `## 🔧 Configuration`, `## 🛠️ Installation`, `## 💡 Examples`, `## ⚡ Performance`, `## 🔒 Security`, `## ❤️ Sponsors`, `## ⭐ Star History`). None of these appear in the surveyed pre-2020 READMEs. Use plain `##` headings.
- **The "Why X?" sales section** with 5–8 emoji-bulleted items. Real maintainers don't write these.
- **Three-tier "Sponsors: 🥇 🥈 🥉" blocks.** Post-2022 marketing.
- **The "Comparison with {Competitor}" table in the README.** Real maintainers let users decide.
- **"Show your support ⭐ this repo!" sections.**
- **Stacked adjectives in descriptions:** `A modern, powerful, flexible, lightweight, blazing-fast framework…` — one or two adjectives max.
- **The verb `delve` in any tense.**
- **Tutorials that begin "In this tutorial, we will explore…"** — start with the code or the question.
- **Marketing-suffix closings on sections:** "And that's how easy it is!" — just stop.
- **Verbose `# Arrange / # Act / # Assert` comments in tests.**
- **The `def main(): ...; if __name__ == "__main__": main()` wrapper in scripts under ~50 lines** that don't need it.
- **`try/except Exception` (or `except:`) followed by `pass` or `return None` with a comment** like "Silently ignore errors." Either re-raise, log, or fix the call site.
- **Triple-nested defensive `is not None` chains** when a guard clause or a single early return would do.

### Tone rules

- **Open with a factual one-sentence definition.** `requests: A simple, yet elegant, HTTP library.` `pydantic: Data validation using Python type hints.` `ripgrep: ripgrep is a line-oriented search tool that recursively searches the current directory for a regex pattern.` No adjectives stacked before the noun.
- **Use imperative mood in subject lines and instructions.** "Add a handler" not "Adds a handler" or "Added a handler".
- **Use first-person plural sparingly and only for the project speaking as a whole** ("We don't support Windows"), not as filler.
- **Prefer contractions when natural.** `don't`, `won't`, `it's` — these read more naturally than `do not`/`will not`/`it is` and they're what humans type.
- **Don't apologize in error messages.** No "Please double-check your input and try again." Just state the failure.
- **Don't summarize what the code does in a docstring** — name the function clearly, write a one-line summary in the imperative, and stop.
- **Reference issues and PRs by number**, not by narrative. `#3761`, `(#1234)`, `:pr:`5648` — the entry is a pointer, not a story.

### Code rules

- **No comments that paraphrase the code.** `# Loop through items` above `for item in items:` is noise. Comments are for *why* (gotcha, RFC, performance, link to issue).
- **Tight variable names in small scopes.** `i, j, k, n, p, x, m, h` are fine in 5-line functions. Verbose names (`element_index`, `mapping_dictionary`) are noise.
- **Reuse the same name across transformations of one concept** instead of inventing `parsed_url_components` → `initial_host_value` → `final_host_value_without_port` → `normalized_host_string`.
- **One assertion per test** is the rule, not the ideal. Spell out the expected value as a tuple/dict, not as a re-computation.
- **Test names describe the *case*, not the *function*.** `test_raises_on_empty_input` not `test_function_behavior`.
- **`assert` is for internal invariants**; `raise ValueError` is for public input validation. Never `assert` user input.
- **Use `from __future__ import annotations` only when you actually need forward refs.** Not by default.
- **Type-annotate the public API, leave internals untyped.** `requests/api.py` ships with zero type hints. `flask/ctx.py` types the `AppContext` fields but not the helper methods.
- **One docstring style per file.** Pick Sphinx-style, Google-style, or NumPy-style, and stick to it. Don't mix `Args:` with `:param:` in the same file.
- **Imports are at the top *unless* there's a reason** (circular dependency, deferred-cost optimization, optional feature). Don't sprinkle them throughout unless the reason is documented.
- **Errors are values, not exceptions of last resort.** Use sentinel returns (`None`, `""`, `-1`) when the caller already checks; raise only when the situation is genuinely exceptional.
- **No `**kwargs` forwarding unless a real second caller needs it.** Add it when there's pressure to, not preemptively.
- **Local imports to break circular deps** — humans do this; AI hoists everything to the top.

### Repository / meta rules

- **Don't generate these files by default** — humans only add them with a real reason:
  - `.github/ISSUE_TEMPLATE/` (zero mature pre-2024 repos have these)
  - `.github/PULL_REQUEST_TEMPLATE.md` (rare)
  - `.github/dependabot.yml` (most pre-2024 repos use Renovate or nothing)
  - `.devcontainer/` (mostly 2020+)
  - `SECURITY.md` (only when you have a real disclosure process)
  - `CODE_OF_CONDUCT.md` (Contributor Covenant verbatim is fine, but don't generate one unsolicited)
  - `CHANGELOG.md` (use whatever convention the project already has; if none, hand-write entries rather than auto-generating)
- **Do not normalize file casing retroactively.** `Readme.md`, `readme.md`, `History.md`, `HISTORY.md` all coexist in the wild. Pick a style and *commit to it*; don't rename later.
- **Use a small, opinionated file set.** Pre-2020 repos typically have: `LICENSE`, `README`, a CHANGELOG of *some* name, `CONTRIBUTING` (sometimes), `.gitignore`, and the build file. That's it.
- **One-line `description` fields.** Compare:
  - Human: `A simple, yet elegant, HTTP library.`
  - Human: `Node version management`
  - Human: `A command line tool and library for transferring data with URL syntax, supporting DICT, FILE, FTP, FTPS, GOPHER, GOPHERS, HTTP, HTTPS, IMAP, IMAPS, LDAP, LDAPS, MQTT, MQTTS, POP3, POP3S, RTSP, SCP, SFTP, SMB, SMBS, SMTP, SMTPS, TELNET, TFTP, WS and WSS.`
  - AI: `A modern, powerful, and flexible HTTP library designed to streamline your API development workflow.`
  - The human ones name the project and stop. The AI one stacks adjectives and adds a value claim.
- **Don't add `keywords = ["fast", "modern", "lightweight"]`.** Use specific, technical terms: `["async", "non-blocking", "io"]`.

## Pre-flight checklist (run before submitting any output)

Before you finish writing, scan your own output for these tells. If any are present, fix them.

1. **Emoji scan.** Are there `🚀`, `✨`, `🔥`, `📦`, `📚`, `🤝`, `🔧`, `💡`, `🛠️`, `⚡`, `🔒`, `❤️`, `⭐` in section headers or list bullets? Strip them.
2. **Banned-word scan.** Search for: `leverage`, `robust`, `seamless`, `delve`, `cutting-edge`, `modern`, `production-grade`, `battle-tested`, `world-class`, `next-generation`, `best-in-class`, `state-of-the-art`, `in today's`, `furthermore`, `moreover`, `myriad`, `plethora`, `whether you're`. Zero hits.
3. **"Whether you're X or Y" scan.** If present, delete the sentence and write a single direct one.
4. **Closing-flourish scan.** Strip `happy coding!`, `let's dive in`, `that's it!`, `buckle up`, `and there you have it`.
5. **Description-length scan.** One-line descriptions must be < 12 words. Project one-liners must be < 25 words.
6. **Tutorial-opening scan.** No "In this tutorial, we will…" or "Welcome to…". Start with the code, the question, or the definition.
7. **Docstring-paraphrase scan.** Read every docstring; if it says what the function name already says, delete it.
8. **Comment-paraphrase scan.** Read every comment; if it says what the next line of code does, delete it.
9. **Type-hint density scan.** Public APIs: annotated. Helpers and internals: not annotated. If a file has 10+ type hints in a row, ask whether every one is load-bearing.
10. **Test name scan.** Names describe the case, not the function. `test_raises_on_empty_input` is good; `test_function_behavior` is AI.
11. **Error-message scan.** Strip "Please try again" / "Please contact support" / "double-check your input". State the actual failure.
12. **Default `main()` wrapper scan.** If a script has one `main()` and one `if __name__`, and the script is < 50 lines, drop the wrapper and put the code at module level.
13. **Triple-nested `if x is not None: if y is not None: if z is not None:`** scan. Replace with a single early return.
14. **"I built this to…"** scan. Project voice speaks as the project, not as a personal blog.
15. **"Whether you're a beginner or an expert"** scan. The user is the user; let them decide their level.

## Reference files — load on demand

- **[`references/prose.md`](./references/prose.md)** — The voice catalog. 50+ opening lines from real repos, banned-phrase lexicon, section-heading patterns, transformation examples. Load when writing README, docs, blog, or any prose.
- **[`references/code.md`](./references/code.md)** — Per-language code tells. Python, JS/TS, Go, Rust, C. The "Test of Humanity" 50-question checklist, with human/AI code pairs. Load when writing or reviewing source.
- **[`references/meta.md`](./references/meta.md)** — Repository structure, file inventory, metadata fields, `pyproject.toml`/`package.json`/`Cargo.toml` patterns, license files, CI config, the "Restraint Checklist". Load when setting up or auditing a repo.
- **[`references/references.md`](./references/references.md)** — All source citations, repo URLs, file paths, and line numbers from the original research. Load to verify a claim or dig deeper.

Also at the repo root, see **[`AGENTS.md`](./AGENTS.md)** for the mandatory-use contract that any AI agent working in this repo must follow.

## Quick transformations (cheat sheet)

| AI-slop input | Human rewrite |
|---|---|
| `Welcome to FastApp! In this comprehensive guide, we will explore the powerful features and capabilities of our cutting-edge framework. Whether you're a beginner or an experienced developer, FastApp has something for everyone. Let's dive in!` | `FastApp is a web framework.` |
| `## 🚀 Quick Start` | `## Install` or `## Getting started` |
| `This function calculates the factorial of a number using recursion. It takes an integer n and returns n! Args: n (int): ... Returns: int: ...` | `def factorial(n): return 1 if n == 0 else n * factorial(n - 1)` |
| `raise ValueError("We encountered an issue while trying to process your request. The value you provided appears to be invalid. Please double-check your input and try again. If the problem persists, please don't hesitate to reach out to our support team for assistance.")` | `raise ValueError(f"invalid input: {value!r}")` |
| `# Increment counter by 1`<br>`counter += 1` | (delete the comment) |
| `# Loop through all the methods in the handler's directory`<br>`for method_name in dir(handler):` | `for meth in dir(handler):` |
| `logger.info(f"Processing request {request_id} for user {user.name}")` | `logger.info("Processing request %s for user %s", request_id, user.name)` |
| `def fetch_user(user_id: UserId, *, include_orders: bool = False, session: Optional[Session] = None) -> UserDict: ...` | `def fetch_user(user_id, *, include_orders=False, session=None): ...` |
| `try: ... except (ConnectionError, TimeoutError, OSError, socket.gaierror) as e: ...` | `try: ... except OSError as e: ...` |
| `if user is not None: if user.profile is not None: if user.profile.avatar is not None: if user.profile.avatar.url is not None: return user.profile.avatar.url`<br>`return DEFAULT_AVATAR_URL` | `return (user and user.profile and user.profile.avatar and user.profile.avatar.url) or DEFAULT_AVATAR_URL` |
| `def main():` + `if __name__ == "__main__": main()` around a 10-line script | top-level code; no wrapper |
| `def calculate_total_price(items: List[Item], tax_rate: float) -> float:` + 4-line docstring paraphrasing the body | `def price(items, tax): return sum(i.price for i in items) * (1 + tax)` |
| `# Issue #1288: Test that automatic options are not added` | `# Issue 1288: Test that automatic options are not added` (no period after the number) |
| `2.0.0 (2025-11-15) 🎉` | `2.0.0 (2025-11-15)` |
| `We are thrilled to introduce a brand new caching mechanism that will revolutionize performance!` | `Added caching to Client.send. (#1234)` |
| `def save_user(user: User) -> None: ... return None # Success` | `def save_user(user): db.save(user)` (no `return None` needed) |

## Final reminder

A piece of content feels human-written when it satisfies five things: **brevity** (30–100 lines for a README, one-sentence docstrings, no marketing prose), **specificity** (real error messages, real PR numbers, real edge cases), **stance** (the author has opinions), **imperfection** (typos, commented-out code, dead `print` statements, `XXX` markers), and **pointers** (docs say "see X" instead of explaining X).

If a sentence could appear in any project's README, it's probably AI-slop. If it could only appear in *this* project, by *this* person, it's probably real.
