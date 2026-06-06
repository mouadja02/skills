#!/usr/bin/env python3
"""Audit an MCP tool inventory and print a graph-routing report."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


WRITE_HINTS = ("write", "delete", "create", "update", "send", "post", "commit", "merge", "deploy")


def read_inventory(path: str) -> list[dict]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict):
        return data.get("servers", data.get("tools", []))
    return data


def stable_hash(item: dict) -> str:
    payload = json.dumps(item, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def iter_tools(records: list[dict]):
    for record in records:
        if "tools" in record:
            server = record.get("name", record.get("server", "unknown-server"))
            for tool in record.get("tools", []):
                yield server, tool
        else:
            yield record.get("server", "unknown-server"), record


def side_effect_class(tool: dict) -> str:
    text = " ".join(str(tool.get(key, "")) for key in ("name", "description")).lower()
    if any(hint in text for hint in WRITE_HINTS):
        return "write-capable"
    return tool.get("side_effects", "read-only-or-unknown")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", help="JSON inventory path, or '-' for stdin")
    args = parser.parse_args()

    records = read_inventory(args.inventory)
    by_server: dict[str, list[dict]] = defaultdict(list)
    effects = Counter()

    for server, tool in iter_tools(records):
        by_server[server].append(tool)
        effects[side_effect_class(tool)] += 1

    print("# MCP Tool Routing Report\n")
    print(f"Servers: {len(by_server)}")
    print(f"Tools: {sum(len(tools) for tools in by_server.values())}\n")

    print("## Side-Effect Classes")
    for key, count in effects.most_common():
        print(f"- {key}: {count}")

    print("\n## Server Nodes")
    for server, tools in sorted(by_server.items()):
        print(f"- {server}: {len(tools)} tools")

    print("\n## Tool Nodes")
    for server, tools in sorted(by_server.items()):
        for tool in tools:
            name = tool.get("name", "unnamed-tool")
            print(f"- {server} -> {name} [{side_effect_class(tool)}] hash={stable_hash(tool)}")

    print("\n## Routing Gates")
    print("- Refresh the inventory when any hash changes.")
    print("- Keep write-capable tools out of default candidate sets unless the user goal requires them.")
    print("- Validate arguments against live schemas immediately before invocation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

