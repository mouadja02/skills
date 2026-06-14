---
name: anti-ai-slop
description: Mandatory-use contract for any AI agent in this repo. Before writing code, docs, comments, commits, READMEs, or repo structure, load `SKILL.md` and the relevant file in `references/`. Produces pre-2020 human-style output — terse, opinionated, with project voice. Blocks AI tells: emoji headers, "leverage", "robust", "seamless", "delve", defensive bloat, type-hint overkill, marketing prose, "Whether you're X or Y", verbose error messages.
---

# anti-ai-slop

This repo is governed by the **anti-ai-slop** skill. Every file you produce (code, docs, comments, commits, READMEs, changelogs, repo structure) must follow it.

## 1. Before you write anything

1. **Read the project first.** Open `README`, `LICENSE`, the existing `CHANGELOG`/`HISTORY`/`CHANGES` (whatever it is named), and the project's metadata file (`pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod`). Read 2–3 source files for style.
2. **Load the skill:** read `SKILL.md` in full.
3. **Load the relevant reference** for what you're about to produce:

   | Producing… | Load |
   |---|---|
   | Prose (README, docs, comments, error messages, commits, changelogs, docstrings) | `references/prose.md` |
   | Source code (Python, JS/TS, Go, Rust, C, shell, SQL) | `references/code.md` |
   | Repo files (top-level, metadata, CI, license, structure, descriptions) | `references/meta.md` |
   | Verifying a citation or pattern | `references/references.md` |

## 2. Use the project's existing commands

Don't invent commands. Read the lockfile, `scripts` in `package.json`/`pyproject.toml`, and CI config. Use what the project already runs (e.g., `npm test`, `pytest`, `cargo test`, `go test ./...`).

## 3. Code style (the five rules)

1. **Comments explain *why*, not *what*.** No paraphrasing the next line. No `# oops` apologetics.
2. **Tight names in small scopes.** `i, j, k, n, p` are fine; `element_index_counter` is not. Reuse the same name across transformations.
3. **Type-annotate the public API, leave internals untyped.** Don't preemptively add hints.
4. **One docstring style per file.** No `# Arrange / # Act / # Assert` in tests. One assert per test. Test names describe the *case* (`test_raises_on_empty_input`), not the *function*.
5. **No `assert` for input validation.** No silent `except: pass`. No `**kwargs` preemptively. No `main()` wrapper for scripts < 50 lines. No triple-nested `is not None` chains.

Full catalog in `references/code.md`.

## 4. Prose style

- Open with a factual one-sentence definition. No adjective stacking.
- Imperative mood. Contractions. No apologies in errors.
- Reference issues by number, not narrative.
- One-line `description` fields. < 12 words. Technical `keywords` only.
- Imperfection is human — `XXX` markers, typos, commented-out code, dead `print`s are fine.
- **Zero emoji in section headers or list bullets.** The banned-word list, full opening-line catalog, and section-header patterns are in `references/prose.md`.

## 5. Repo structure

- Don't generate by default: `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/dependabot.yml`, `.devcontainer/`, `SECURITY.md`, auto-generated `CHANGELOG.md`. Add only with a real reason.
- Don't normalize file casing retroactively (`Readme.md` and `readme.md` both exist in the wild).
- Hand-write changelog entries with PR/issue numbers, not marketing prose.
- Full inventory in `references/meta.md`.

## 6. Git

- **Subject:** imperative, ≤ 72 chars, no period. `Add caching to Client.send`.
- **Body:** wrapped at 75 cols. Reference issues with `(#1234)` or `Fixes #N`.
- **PR description:** 2–3 sentences, then `Fixes #N`, then optional checklist. No marketing prose.
- **Changelog entries:** short verb phrase, optional bullet, PR/issue ref. No emoji. No "we are thrilled to announce."

## 7. Boundaries

**Always:** load the relevant `references/` file before producing output. Run the pre-flight checklist in `SKILL.md` §"Pre-flight checklist". Match the project's existing voice and tooling. Cite issues by number. Use imperative mood and contractions. Hand-write changelogs.

**Ask first:** adding a new dependency. Modifying CI/CD. Changing a public API. Adding a top-level directory. Touching `vendor/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.venv/`, or any vendored/generated directory. Writing in a language/framework not already in the project. Generating any of the `.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`, `dependabot.yml`, `.devcontainer/`, `SECURITY.md`, or auto-generated `CHANGELOG.md`.

**Never:**

- Use these words in any output: `leverage`, `seamless`, `seamlessly`, `robust`, `cutting-edge`, `state-of-the-art`, `blazing fast`, `lightning fast`, `next-generation`, `best-in-class`, `world-class`, `production-grade`, `battle-tested`, `modern web`, `highly performant`, `drop-in replacement`, `out of the box`, `supercharge`, `turbocharge`, `revolutionize`, `transformative`, `empower`, `unlock the power`, `harness the power`, `elevate your workflow`, `utilize`, `facilitate`, `delve into`, `delve deeper`, `navigate the complexities`, `navigate the intricacies`, `in today's fast-paced world`, `in the realm of`, `it is worth noting that`, `it's important to note`, `furthermore`, `moreover`, `tapestry`, `myriad of`, `plethora of`, `whether you're a beginner or an expert`, `whether you're X or Y`, `a comprehensive guide to`, `with just a few lines of code`, `in just a few clicks`, `a wide range of`, `a variety of`, `numerous`, `in order to`, `happy coding!`, `let's dive in!`, `buckle up!`, `and there you have it!`.
- Use emoji in section headers or list bullets (`🚀`, `✨`, `🔥`, `📦`, `📚`, `🤝`, `🔧`, `💡`, `🛠️`, `⚡`, `🔒`, `❤️`, `⭐`, `🌟`, `🎉`).
- Use `assert` for input validation. Use `try/except: pass`. Use `**kwargs` preemptively. Wrap a < 50-line script in `main() + if __name__`. Use triple-nested `is not None`.
- Generate `### ✨ Exciting New Features`, `We are thrilled to announce...`, or any marketing changelog.
- Stack 4+ adjectives in a `description` field. Add emoji-bullet "Why X?" sales sections. Add competitor comparison tables. Add `Made with ❤️ by [Author]` badges.
- Commit secrets or `.env` files. Edit `vendor/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, or generated dirs.

## 8. Pre-flight checklist (run before submitting)

1. No emoji in headers or list bullets.
2. Zero hits for banned words.
3. No "Whether you're X or Y" or "happy coding!" closings.
4. Descriptions ≤ 12 words. Project one-liners ≤ 25 words.
5. No "In this tutorial, we will..." openings.
6. No docstring or comment that paraphrases what the name/next-line already says.
7. Type-hint density is moderate (not 10+ in a row).
8. Test names describe the *case*, not the *function*.
9. No "Please try again" / "Please contact support" in errors.
10. No `main()` wrapper around < 50-line scripts.
11. No triple-nested `is not None` chains.
12. Project voice in third person, not personal blog.

If you fail 3+ items, regenerate from scratch with the relevant `references/` file reloaded.

## 9. When in doubt

- "Make it sound more polished" / "more professional" = write like a thoughtful human maintainer, **not** add corporate vocabulary. Adding `leverage`, `robust`, `seamless`, or emojis is the opposite of professional.
- If the user asks for an AI-style README, ask once whether they want a human-style version instead.
- If the user explicitly conflicts with this contract (e.g., "use a 🚀 emoji header"), confirm with them and document the override.

A piece of content feels human-written when it has **brevity** (30–100 lines for a README, one-sentence docstrings), **specificity** (real PR numbers, real edge cases), **stance** (the author has opinions), **imperfection** (`XXX` markers, typos, commented-out code), and **pointers** (docs say "see X", not explanations of X). If a sentence could appear in any project's README, it's AI-slop. If it could only appear in *this* project, by *this* person, it's real.
