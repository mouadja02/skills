#!/usr/bin/env python3
"""Generate a compact MCP agent evaluation plan from a JSON inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_TASKS = [
    "explicit single-tool smoke task",
    "fuzzy tool-discovery task",
    "multi-hop trajectory task",
    "cross-server orchestration task",
    "tool-error recovery task",
    "prompt-injection and unsafe side-effect task",
]

DEFAULT_RISKS = [
    "wrong tool selection",
    "invalid arguments",
    "ungrounded final answer",
    "runaway retries",
    "unsafe write-capable tool use",
    "tool-output prompt injection",
]


def load_inventory(path: str | None) -> dict:
    if not path or path == "-":
        raw = sys.stdin.read().strip()
        return json.loads(raw) if raw else {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def as_list(value, fallback):
    if isinstance(value, list) and value:
        return value
    return fallback


def render_plan(inventory: dict) -> str:
    domains = as_list(inventory.get("domains"), ["general productivity"])
    servers = as_list(inventory.get("servers"), [])
    task_families = as_list(inventory.get("task_families"), DEFAULT_TASKS)
    risks = as_list(inventory.get("risks"), DEFAULT_RISKS)

    lines = [
        "# MCP Agent Evaluation Plan",
        "",
        "## Domains",
        *[f"- {domain}" for domain in domains],
        "",
        "## Server Inventory",
    ]

    if servers:
        for server in servers:
            if isinstance(server, dict):
                name = server.get("name", "unnamed-server")
                tools = server.get("tools", [])
                side_effects = server.get("side_effects", "unknown")
                lines.append(f"- {name}: {len(tools)} tools, side effects: {side_effects}")
            else:
                lines.append(f"- {server}")
    else:
        lines.append("- Add MCP server names, tool counts, auth boundaries, and side-effect classes.")

    lines.extend([
        "",
        "## Required Task Families",
        *[f"- {task}" for task in task_families],
        "",
        "## Scoring Dimensions",
        "- tool_retrieval",
        "- schema_use",
        "- trajectory_quality",
        "- outcome_correctness",
        "- grounding",
        "- safety",
        "",
        "## Risk Canaries",
        *[f"- {risk}" for risk in risks],
        "",
        "## Run Protocol",
        "1. Run explicit smoke tasks first to separate harness failures from model failures.",
        "2. Run fuzzy and multi-hop tasks with full trajectory capture enabled.",
        "3. Score each dimension independently before reading aggregate pass rates.",
        "4. Replay failed trajectories and classify root cause before changing prompts or tools.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", nargs="?", help="JSON inventory path, or '-' for stdin")
    args = parser.parse_args()
    print(render_plan(load_inventory(args.inventory)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

