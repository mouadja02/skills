#!/usr/bin/env python3
"""Create a minimal smolagents scaffold with visible safety defaults."""

from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATE = '''"""Smolagents starter with explicit safety placeholders."""

from smolagents import CodeAgent, InferenceClientModel


def build_agent():
    model = InferenceClientModel()

    # Add only tools with narrow, documented side effects.
    tools = []

    return CodeAgent(
        tools=tools,
        model=model,
        stream_outputs=True,
        additional_authorized_imports=[],
        max_steps=12,
    )


if __name__ == "__main__":
    agent = build_agent()
    print(agent.run("Inspect the configured tools and report readiness."))
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="smolagent_app", help="output directory")
    args = parser.parse_args()

    root = Path(args.name)
    root.mkdir(parents=True, exist_ok=True)
    (root / "agent.py").write_text(TEMPLATE, encoding="utf-8")
    (root / "README.md").write_text(
        "# Smolagents App\n\nRun model-written code only in a sandbox for untrusted tasks.\n",
        encoding="utf-8",
    )
    print(f"Created {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
