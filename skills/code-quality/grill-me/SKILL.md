---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
license: MIT
source: "https://github.com/mattpocock/skills"
attribution: "mattpocock/skills by Matt Pocock"
---

> **Attribution:** Sourced from [mattpocock/skills](https://github.com/mattpocock/skills) by [Matt Pocock](https://github.com/mattpocock), licensed MIT (original text of `skills/grill-me`, also redistributed in alirezarezvani/claude-skills). Modified for this collection.

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

**Related skill:** `grilling` is the current upstream version of this interview. It asks in numbered rounds and dispatches sub-agents to look up facts instead of asking the user.
