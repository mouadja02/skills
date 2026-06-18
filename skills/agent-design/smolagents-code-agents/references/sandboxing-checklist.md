# Smolagents Sandboxing Checklist

Use this before running a code-executing agent.

## Required Controls

- Run untrusted code in Docker, E2B, Modal, Blaxel, or equivalent isolation.
- Mount a disposable workspace, not the whole repository or home directory.
- Pass secrets through scoped runtime configuration only when the tool requires them.
- Disable outbound network unless the task needs it.
- Whitelist imports.
- Set max steps, wall-clock timeout, and output-size limit.
- Log every code action before execution.
- Capture final artifacts outside the sandbox only after review.

## Tool Contract

Each tool should document:

- Input schema.
- Output shape.
- Side effects.
- Network behavior.
- Filesystem behavior.
- Expected failure modes.

## Reject

- Direct local execution for unknown web content.
- Broad imports such as `os`, `subprocess`, or `shutil` unless the task explicitly requires them and the sandbox is disposable.
- Write access to credentials, shell profiles, SSH directories, browser profiles, or package-manager auth files.
