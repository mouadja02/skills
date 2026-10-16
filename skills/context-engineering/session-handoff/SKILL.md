---
name: session-handoff
description: >-
  Use when a long session should continue in a fresh agent — context is nearly full, compaction would
  lose detail, or the work is moving to another tool or teammate. Compacts the conversation into a
  handoff document in the OS temp directory, pointing at existing specs, plans, and diffs instead of
  repeating them.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
license: MIT
source: "https://github.com/mattpocock/skills"
attribution: "mattpocock/skills by Matt Pocock"
version: "1.0.0"
---

> **Attribution:** Sourced from [mattpocock/skills](https://github.com/mattpocock/skills) by [Matt Pocock](https://github.com/mattpocock), licensed MIT. Modified for this collection (upstream name: `handoff`).

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS (`$TMPDIR`, else `/tmp`; `%TEMP%` on Windows) - not the current workspace.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
