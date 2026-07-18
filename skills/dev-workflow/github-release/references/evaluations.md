# Evaluation Prompts

Use these prompts to verify routing and workflow behavior after changing this skill.

## Normal: release PR on the default branch

**Prompt**

> Prepare the next release PR for this single-package GitHub library. It has stable
> version tags and a changelog, and I want you to propose the SemVer bump before
> changing files.

**Expected behavior**

- Detect the repository's default branch rather than assuming `main`.
- Synchronize it with fetch plus a fast-forward-only merge.
- Derive the proposal from public API changes and ask for confirmation before creating
  a release branch.
- Create the PR body in a file and pass it with `gh pr create --body-file`.

## Difficult edge: misleading tags and a non-main default branch

**Prompt**

> This repository's default branch is `trunk`. Its tags include `v1.9.0`, `v1.10.0`,
> `v2.0.0-rc.1`, and `release-3.0.0`. Prepare a stable release without modifying
> unrelated local history.

**Expected behavior**

- Select `v1.10.0` as the latest stable `v?MAJOR.MINOR.PATCH` tag.
- Reject the prerelease and non-version-prefix tags from the stable-tag filter.
- Stop rather than merge or rebase if `trunk` cannot fast-forward to `origin/trunk`.

## Should not activate: independently versioned monorepo

**Prompt**

> Publish the next package versions in this Changesets monorepo and let the existing
> release workflow create tags and GitHub releases.

**Expected behavior**

- Do not apply this single-package manual release workflow.
- Follow the repository's Changesets and CI release policy instead.

## Regression assertions

A maintained copy should satisfy all of these checks:

1. `SKILL.md` decodes as strict UTF-8.
2. Frontmatter includes a trigger-oriented description and semantic version.
3. The Bash PR example is enclosed in a four-backtick fence so its generated PR body
   can contain ordinary three-backtick Markdown fences.
4. The Bash PR example passes `bash -n` when extracted without executing it.
5. Neither Bash nor PowerShell examples contradict the `--body-file` requirement.
6. The stable-tag regex rejects suffixes such as `-rc.1` and arbitrary trailing text.
