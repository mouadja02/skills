#!/usr/bin/env python3
"""Estimate the context a coding agent loads before you type anything.

Counts memory files (CLAUDE.md, CLAUDE.local.md, AGENTS.md, .claude/CLAUDE.md, user-level
~/.claude/CLAUDE.md) and the name + description of every installed skill, which clients keep
in context on every request. Skill bodies load only when a skill is used and are reported
separately. Token counts are estimates (characters / 4); run /context in Claude Code for the
exact figure, which also covers the system prompt, tools, and MCP servers.

Usage:
    python3 context_budget.py [PROJECT_DIR] [--client claude|cursor|agents] [--json] [--top N]

--client picks which skill folder to count: .claude/skills (default), .cursor/skills, or
.agents/skills, each in the project and in the home directory.

Standard library only. Read-only.
"""

import json
import os
import re
import sys

MEMORY_FILES = ["CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", os.path.join(".claude", "CLAUDE.md")]
# Each client discovers skills under its own folder, in the project and in the home directory.
SKILL_ROOTS = {
    "claude": os.path.join(".claude", "skills"),
    "cursor": os.path.join(".cursor", "skills"),
    "agents": os.path.join(".agents", "skills"),
}
CLAUDE_MD_LINE_TARGET = 200  # Claude Code's cost guide: keep CLAUDE.md under 200 lines.


def estimate_tokens(text):
    return (len(text) + 3) // 4


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def skill_metadata(text):
    """Returns (name, description, body) using a small frontmatter reader."""
    text = text.lstrip("﻿").replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---[ \t]*(?:\n|$)", text, re.S)
    if not match:
        return "", "", text
    block, body = match.group(1), text[match.end():]
    fields, key, parts = {}, None, []
    for line in block.split("\n"):
        top = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if top:
            if key:
                fields[key] = " ".join(parts).strip()
            key, parts = top.group(1), [top.group(2).strip()]
        elif key and line.strip():
            parts.append(line.strip())
    if key:
        fields[key] = " ".join(parts).strip()
    description = fields.get("description", "")
    description = re.sub(r"^[>|][+-]?\s*", "", description).strip("\"'")
    return fields.get("name", "").strip("\"'"), description, body


def scan(project, client):
    home = os.path.expanduser("~")
    candidates = [(os.path.join(project, rel), "project") for rel in MEMORY_FILES]
    candidates.append((os.path.join(home, ".claude", "CLAUDE.md"), "user"))
    memory = []
    for path, scope in candidates:
        text = read(path)
        if text is not None:
            memory.append({
                "file": path, "scope": scope, "lines": text.count("\n") + 1,
                "tokens": estimate_tokens(text),
            })
    skills, seen = [], set()
    for base, scope in ((project, "project"), (home, "user")):
        for rel in [SKILL_ROOTS[client]]:
            root = os.path.join(base, rel)
            if not os.path.isdir(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", "__pycache__"}]
                if "SKILL.md" not in filenames:
                    continue
                path = os.path.realpath(os.path.join(dirpath, "SKILL.md"))
                if path in seen:
                    continue
                seen.add(path)
                text = read(path) or ""
                name, description, body = skill_metadata(text)
                skills.append({
                    "skill": name or os.path.basename(dirpath), "scope": scope, "path": path,
                    "always_tokens": estimate_tokens(name + description) + 8,
                    "body_tokens": estimate_tokens(body), "body_lines": body.count("\n") + 1,
                })
    return memory, skills


def main(argv):
    as_json = "--json" in argv
    options = {"--top": "10", "--client": "claude"}
    for flag in options:
        if flag in argv:
            options[flag] = argv[argv.index(flag) + 1]
    top, client = int(options["--top"]), options["--client"]
    if client not in SKILL_ROOTS:
        print(f"--client must be one of: {', '.join(SKILL_ROOTS)}", file=sys.stderr)
        return 2
    positional = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in options)]
    project = os.path.abspath(positional[0] if positional else os.getcwd())
    memory, skills = scan(project, client)
    memory_total = sum(m["tokens"] for m in memory)
    skills_total = sum(s["always_tokens"] for s in skills)
    advice = []
    for m in memory:
        if m["lines"] > CLAUDE_MD_LINE_TARGET:
            advice.append(f"{m['file']} is {m['lines']} lines; move workflow-specific sections into skills (target under {CLAUDE_MD_LINE_TARGET}).")
    if len(skills) > 50:
        advice.append(f"{len(skills)} skills installed; every description is in context on every request. Uninstall what you do not use, or discover skills on demand (for example through a skills MCP server).")
    heavy = [s for s in skills if s["body_lines"] > 500]
    for s in heavy[:5]:
        advice.append(f"skill '{s['skill']}' body is {s['body_lines']} lines; each use loads all of it.")
    result = {
        "project": project,
        "client": client,
        "always_loaded_estimate": memory_total + skills_total,
        "memory_files": memory, "memory_tokens": memory_total,
        "skills_installed": len(skills), "skill_description_tokens": skills_total,
        "largest_skill_descriptions": sorted(skills, key=lambda s: -s["always_tokens"])[:top],
        "largest_skill_bodies": sorted(skills, key=lambda s: -s["body_tokens"])[:top],
        "advice": advice,
    }
    if as_json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Always-loaded estimate: ~{result['always_loaded_estimate']:,} tokens (memory files + skill descriptions)")
    print(f"\nMemory files: ~{memory_total:,} tokens")
    for m in memory:
        print(f"  {m['tokens']:>7,}  {m['lines']:>5} lines  {m['file']}")
    print(f"\nSkills under {SKILL_ROOTS[client]} (project and home): {len(skills)} installed, ~{skills_total:,} tokens of descriptions")
    for s in result["largest_skill_descriptions"]:
        print(f"  {s['always_tokens']:>7,}  {s['skill']}")
    if skills:
        print(f"\nLargest skill bodies (loaded only when the skill runs):")
        for s in result["largest_skill_bodies"]:
            print(f"  {s['body_tokens']:>7,}  {s['skill']}")
    if advice:
        print("\nAdvice:")
        for line in advice:
            print(f"  - {line}")
    print("\nEstimates only (chars/4). Use /context for exact numbers, including tools and MCP servers.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
