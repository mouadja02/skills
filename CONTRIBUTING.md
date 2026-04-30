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
   ---

   # My Skill

   The body explains how the assistant should behave when this skill triggers.
   Lead with concrete steps. Link to other files in the folder if you need
   templates, references, or example outputs.
   ```

   Frontmatter rules:

   - `name` must match the folder name.
   - `description` is what the model sees when deciding whether to load the
     skill. Lead with the trigger phrase ("Use when…", "Activate when…").
     Keep it under ~300 chars; long descriptions get truncated in lists.
   - You can add any other key (e.g. `tags`, `version`) — extra keys are
     preserved in the manifest but not required.

4. Drop any supporting files (templates, references, scripts) in the same
   folder. They ship with the skill when users install it.

5. Update [`skills/<category>/README.md`](./skills) if the category README
   maintains a hand-curated table. Otherwise the generated
   [`SKILLS.md`](./SKILLS.md) and [`docs/manifest.json`](./docs/manifest.json)
   are enough.

## Editing an existing skill

Just edit the file. The CI regenerates `docs/manifest.json`,
`docs/manifest.tsv`, `SKILLS.md`, and the per-skill ZIP archive on every
push to `main`.

## Local preview

```bash
npm install        # one time
npm run build      # regenerates manifest + zips into docs/
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
- **Self-contained** — every file referenced by `SKILL.md` should live in
  the same folder, or be installable separately. Skills installed with
  `install.sh` only get their own folder, nothing else.
- **No secrets** — anything you commit gets shipped to every consumer.

## Repo layout cheat sheet

```
skills/<category>/<skill>/SKILL.md     each skill
scripts/build-manifest.mjs             generates docs/manifest.{json,tsv} + SKILLS.md
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
