# Security policy

## Supported versions

Security fixes target the current `main` branch. Installed skills are snapshots;
review upstream changes and reinstall affected skills to receive fixes.

## Reporting a vulnerability

Do not post credentials, exploit payloads, or sensitive data in public issues.
For a sensitive report, open a minimal issue at
https://github.com/mouadja02/skills/issues/new with the title
"Private security report: contact requested" and no vulnerability details.
Ask the maintainer to arrange a private reporting channel before sharing details.

Include the affected skill or script, source commit, impact, and reproduction
steps in the private report. If an imported skill is affected upstream, identify
its source from SKILL.md so the fix can be coordinated with its maintainers.

## Scope and review

Reports may cover installers, repository tooling, downloadable archives, or
bundled skill scripts. Skill instructions and examples are not a sandbox: review
commands and dependencies before running them, and provide only the credentials
needed for the task.

Security scanners can flag deliberate insecure examples, synthetic fixtures,
and detection patterns. Review each finding in context; do not suppress a rule
for the entire collection to hide a real issue.
