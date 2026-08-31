# Evidence and Scope

Accessed 2026-08-31.

## Canonical documentation

- npm CLI v11, **package-lock.json**: <https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json>
- npm CLI v11, **package.json** (`os`, `cpu`, `optionalDependencies`): <https://docs.npmjs.com/cli/v11/configuring-npm/package-json>

These references describe npm metadata. They do not define this skill's family manifest or release target policy.

## Independent problem reports

- npm/cli #4828, **Platform-specific optional dependencies not being included in package-lock.json when reinstalling with node_modules present**: <https://github.com/npm/cli/issues/4828> (closed; factual historical behavior and reproduction boundary)
- Bitwarden clients #13350, **Optional Deps Not Included in package-lock.json**: <https://github.com/bitwarden/clients/issues/13350> (open when rechecked)
- Tailwind CSS #20324, **npm ci fails ... due to missing optional dependencies**: <https://github.com/tailwindlabs/tailwindcss/issues/20324> (closed)
- Hermes Agent #53089, **Windows installer ... esbuild binary ... missing from lockfile**: <https://github.com/NousResearch/hermes-agent/issues/53089> (closed)

Issue state does not erase the recurring cross-project failure class. Revalidate npm behavior before using the workflow to make a time-sensitive resolver claim.

## Licensing

This package contains original MIT-licensed instructions, Python code, and synthetic fixtures. No issue prose or upstream implementation code is copied. npm/cli and Bitwarden GitHub license metadata was not relied upon for redistribution; Tailwind CSS and Hermes Agent are MIT. All issue records are used only as factual evidence.
