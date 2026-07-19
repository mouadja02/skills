# Contributing

Thanks for considering a contribution. Skills here can be used by **Claude
Code**, **Cursor**, and any other client that walks a directory tree of
`SKILL.md` files. The bar is low: one file is enough.

## Adding a skill

1. Pick the right category under [`skills/`](./skills). If nothing fits,
   open an issue and propose a new one — don't invent a category in your PR.
2. Create a folder named in `kebab-case`. The folder name becomes the
   skill name shown in clients.

   ```
   skills/<category>/<my-skill>/SKILL.md
   ```

3. Add a `SKILL.md` with YAML frontmatter. Two fields are required:

   ```markdown
   ---
   name: my-skill
   description: Use when the user wants X — short, action-oriented, written in third person.
   version: "1.0.0"
   ---

   # My Skill

   ## When to Use

   - Bullet list of activation triggers and use cases
   - Helps the model decide when to load vs skip this skill

   The body explains how the assistant should behave when this skill triggers.
   Lead with concrete steps. Link to other files in the folder if you need
   templates, references, or example outputs.
   ```

   Frontmatter rules:

   - `name` must match the folder name.
   - `description` is what the model sees when deciding whether to load the
     skill. Lead with the trigger phrase ("Use when…", "Activate when…").
     Keep it under ~300 chars; long descriptions get truncated in lists.
   - `version` — semantic version string (e.g. `"1.0.0"`). Required for
     all new skills. Bump on meaningful changes.
   - `platform` — set when the skill only works on specific platforms.
     Values: `macos` (macOS-only CLI tools), `apple` (macOS/iOS/Xcode/Swift
     development), `windows`, `linux`. Omit for cross-platform skills.
   - `license` — SPDX identifier (e.g. `MIT`, `Apache-2.0`). Recommended.
   - `source` — URL of the upstream repo when the skill is sourced from
     another project.
   - `attribution` — human-readable credit line for sourced skills.

   Body structure:

   - Start with a `## When to Use` section listing bullet-pointed activation
     criteria. This helps the model decide when to load the skill *and*
     when not to.
   - Follow with workflow steps, code examples, and guardrails.
   - If the skill overlaps with another, add a `**Related skill:**` link.

4. Drop any supporting files (templates, references, scripts) in the same
   folder. They ship with the skill when users install it.

5. Run `npm run build:manifest`. This regenerates
   [`SKILLS.md`](./SKILLS.md), [`docs/manifest.json`](./docs/manifest.json),
   [`docs/manifest.tsv`](./docs/manifest.tsv), [`skills/README.md`](./skills/README.md),
   every top-level category README, and the catalog blocks in [`README.md`](./README.md).
   Do not edit generated category READMEs by hand.

## Editing an existing skill

Just edit the file. Regenerate and commit the manifests, root indexes, and
category READMEs with `npm run build:manifest`. Pull-request CI verifies those
generated files are current and validates every ZIP before merge. Deployment
builds the downloadable archives from a clean checkout after merge.

## Local preview

```bash
npm install        # one time
npm run build      # regenerates docs, audits coverage, builds and checks zips
npm run preview    # serves docs/ at http://localhost:4173
```

The preview shows exactly what the public site at
[mouadja02.github.io/skills](https://mouadja02.github.io/skills) will look
like, including the per-skill `.zip` download buttons.

## Style guide

- **Naming** — folders use `kebab-case`. Avoid uppercase, underscores,
  spaces, or emoji in folder names.
- **Trigger language** — descriptions should read like a router rule, not
  marketing copy. "Use when…" / "Activate when…" / "Apply when…" all work.
- **"When to Use" section** — every skill should have a `## When to Use`
  section near the top with 3–5 bullet points describing activation
  triggers. This is separate from the frontmatter `description`.
- **Platform declaration** — if a skill only works on macOS, iOS, or a
  specific OS, set `platform:` in frontmatter so users can filter.
- **Version tracking** — include `version: "1.0.0"` in frontmatter.
  Bump on meaningful updates so consumers can track changes.
- **Cross-linking** — if two skills overlap (e.g. both cover xctrace
  profiling), add a `**Related skill:**` note pointing to the other.
- **No project-specific skills** — skills should be generally useful.
  Tools tied to a single person's infrastructure or private project
  don't belong in the shared repo.
- **Self-contained** — every file referenced by `SKILL.md` should live in
  the same folder, or be installable separately. Skills installed with
  `install.sh` only get their own folder, nothing else.
- **No secrets** — anything you commit gets shipped to every consumer.

## Repo layout cheat sheet

```
skills/<category>/<skill>/SKILL.md     each skill
scripts/build-manifest.mjs             generates docs/manifest.{json,tsv} + SKILLS.md
                                      + root/category README indexes
scripts/check-docs.mjs                 audits documentation coverage and links
scripts/build-zips.mjs                 generates docs/zips/*.zip (CI / preview)
scripts/preview.mjs                    static server for docs/
install.sh / install.ps1               one-line installers (root for curl URL)
docs/                                  GitHub Pages site
.github/workflows/                     CI: build-manifest + deploy-pages
```

## License

Each skill folder may carry its own license (`LICENSE` or noted in the
SKILL.md frontmatter). Submitting a PR means you agree to publish your
contribution under whatever license its parent skill folder declares.
