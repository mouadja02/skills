#!/usr/bin/env python3
"""Verify an agent benchmark task package against the authoring contract.

Fail-closed validator: exit 0 only when no blocking finding is produced.

    python3 verify_task_package.py <task-dir> [--rollouts rollouts.json] [--json]

Exit codes
    0  no blocking findings
    1  at least one blocking finding (do not publish)
    2  usage, I/O, or parse error (treated as failure)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None

CONTROL_EXPECTATIONS = {
    "oracle": 1,
    "no-op": 0,
    "near-miss": 0,
    "shortcut": 0,
    "alternative-valid": 1,
}
MIN_TRIALS = 3
REWARD_CHANNELS = ("/logs/verifier/reward.txt", "/logs/verifier/reward.json")
# Paths a verifier may legitimately reference without artifact declaration.
SYSTEM_PREFIXES = ("/bin", "/sbin", "/usr", "/etc", "/dev", "/proc", "/sys", "/lib",
                   "/lib64", "/var", "/root", "/home", "/tmp", "/opt", "/tests",
                   "/logs/verifier")
LEAK_TOKENS = ("tests/", "solution/", "solve.sh", "test_outputs.py", "/tests", "/logs/verifier")
SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("api-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),
)
ABSOLUTE_PATH = re.compile(r"(?<![\w.-])/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+")


class Findings:
    def __init__(self) -> None:
        self.items: list[dict] = []
        self.checks: list[str] = []

    def check(self, name: str) -> None:
        self.checks.append(name)

    def add(self, code: str, path: str, message: str, blocking: bool = True) -> None:
        self.items.append({
            "code": code,
            "severity": "blocking" if blocking else "warning",
            "path": path,
            "message": message,
        })

    def blocking(self) -> list[dict]:
        return [i for i in self.items if i["severity"] == "blocking"]


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_toml(path: str) -> dict:
    if tomllib is None:
        raise RuntimeError("python3.11+ is required (tomllib)")
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def is_executable(path: str) -> bool:
    return os.path.isfile(path) and os.stat(path).st_mode & 0o111 != 0


def sandbox_paths(text: str) -> list[str]:
    """Absolute paths a verifier script touches, excluding system and fixed roots."""
    found = []
    for match in ABSOLUTE_PATH.finditer(text):
        candidate = match.group(0).rstrip(".")
        if any(candidate == p or candidate.startswith(p + "/") for p in SYSTEM_PREFIXES):
            continue
        if candidate not in found:
            found.append(candidate)
    return found


def declared_artifacts(config: dict) -> list[str]:
    raw = config.get("artifacts") or []
    paths = []
    for item in raw:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict) and isinstance(item.get("source"), str):
            paths.append(item["source"])
    return paths


def environment_basenames(root: str) -> set[str]:
    """Basenames shipped in the agent image: read-only inputs the verifier may read."""
    names: set[str] = set()
    env_dir = os.path.join(root, "environment")
    for base, dirs, files in os.walk(env_dir):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git"}]
        names.update(files)
    return names


def effective_verifier_mode(config: dict) -> str:
    verifier = config.get("verifier") or {}
    mode = verifier.get("environment_mode")
    if mode:
        return str(mode)
    return "separate" if verifier.get("environment") else "shared"


def effective_verifier_network(config: dict) -> str:
    verifier = config.get("verifier") or {}
    venv = verifier.get("environment") or {}
    if verifier.get("network_mode"):
        return str(verifier["network_mode"])
    if venv.get("network_mode"):
        return str(venv["network_mode"])
    environment = config.get("environment") or {}
    return str(environment.get("network_mode") or "public")


def check_layout(root: str, f: Findings) -> dict:
    f.check("layout")
    for rel in ("instruction.md", "task.toml", "solution/solve.sh", "tests/test.sh"):
        if not os.path.isfile(os.path.join(root, rel)):
            f.add("missing-file", rel, f"required file {rel} is missing")
    env_dir = os.path.join(root, "environment")
    env_specs = ("Dockerfile", "docker-compose.yaml", "docker-compose.yml", "Apptainer.def")
    has_env_spec = any(os.path.isfile(os.path.join(env_dir, name)) for name in env_specs)
    return {"has_env_spec": has_env_spec, "env_dir": env_dir}


def check_config(root: str, f: Findings, layout: dict) -> dict:
    f.check("task.toml")
    path = os.path.join(root, "task.toml")
    if not os.path.isfile(path):
        return {}
    try:
        config = load_toml(path)
    except (OSError, ValueError) as exc:
        f.add("task-toml-unparseable", "task.toml", f"task.toml could not be parsed: {exc}")
        return {}
    if "schema_version" not in config:
        f.add("missing-schema-version", "task.toml", "schema_version is required")
    verifier = config.get("verifier") or {}
    agent = config.get("agent") or {}
    if verifier.get("environment_mode") == "shared" and verifier.get("environment"):
        f.add("verifier-mode-conflict", "task.toml",
              "environment_mode = 'shared' cannot be combined with [verifier.environment]")
    if not layout.get("has_env_spec") and not (config.get("environment") or {}).get("docker_image"):
        f.add("missing-environment", "environment/",
              "no environment spec (Dockerfile/docker-compose/Apptainer) and no environment.docker_image")
    if not verifier.get("timeout_sec"):
        f.add("missing-verifier-timeout", "task.toml", "[verifier].timeout_sec is required")
    if not agent.get("timeout_sec"):
        f.add("missing-agent-timeout", "task.toml", "[agent].timeout_sec is required")
    if effective_verifier_mode(config) != "separate":
        f.add("verifier-not-separated", "task.toml",
              "verifier runs in the agent container; set verifier.environment_mode = 'separate'")
    network = effective_verifier_network(config)
    if network == "public":
        f.add("verifier-public-network", "task.toml",
              "verifier egress resolves to the 'public' default; use no-network or allowlist")
    elif network == "allowlist":
        venv = (verifier.get("environment") or {})
        hosts = verifier.get("allowed_hosts") or venv.get("allowed_hosts")
        if not hosts:
            f.add("verifier-allowlist-empty", "task.toml",
                  "verifier network_mode is allowlist but no allowed_hosts are declared")
    if not (config.get("metadata") or {}).get("category"):
        f.add("missing-metadata-category", "task.toml",
              "[metadata].category is not set", blocking=False)
    return config


def check_solution(root: str, f: Findings) -> None:
    f.check("solution")
    solve = os.path.join(root, "solution", "solve.sh")
    if os.path.isfile(solve) and not is_executable(solve):
        f.add("solution-not-executable", "solution/solve.sh",
              "solve.sh must be executable for the oracle agent")


def check_verifier_script(root: str, f: Findings, config: dict) -> None:
    f.check("tests/test.sh")
    tests_dir = os.path.join(root, "tests")
    script = os.path.join(tests_dir, "test.sh")
    if not os.path.isfile(script):
        return
    if not is_executable(script):
        f.add("verifier-not-executable", "tests/test.sh", "tests/test.sh must be executable")
    try:
        text = read_text(script)
    except OSError as exc:
        f.add("verifier-unreadable", "tests/test.sh", f"tests/test.sh could not be read: {exc}")
        return
    if not any(channel in text for channel in REWARD_CHANNELS):
        f.add("missing-reward-channel", "tests/test.sh",
              "tests/test.sh writes no reward under /logs/verifier/reward.txt or reward.json")
    if "/logs/verifier/" in text and "mkdir" not in text:
        f.add("reward-dir-not-created", "tests/test.sh",
              "the reward directory is written without creating it first", blocking=False)

    # Artifact contract: every agent-produced path the grader reads must be declared.
    artifacts = declared_artifacts(config)
    inputs = environment_basenames(root)
    if effective_verifier_mode(config) == "separate":
        extra = []
        for sub in ("test.sh",):
            extra.extend(sandbox_paths(text))
        for name in sorted(os.listdir(tests_dir)):
            if name.endswith((".py", ".sh")) and name != "test.sh":
                try:
                    extra.extend(sandbox_paths(read_text(os.path.join(tests_dir, name))))
                except OSError:
                    continue
        for path in sorted(set(extra)):
            if any(a == path or path.startswith(a.rstrip("/") + "/") for a in artifacts):
                continue
            if os.path.basename(path) in inputs:
                continue  # read-only input shipped in the agent image
            f.add("undeclared-artifact", "tests/test.sh",
                  f"{path} is read by the verifier but not declared in top-level artifacts")


def check_leakage(root: str, f: Findings) -> None:
    f.check("leakage")
    instruction = os.path.join(root, "instruction.md")
    if not os.path.isfile(instruction):
        return
    try:
        text = read_text(instruction)
    except OSError as exc:
        f.add("instruction-unreadable", "instruction.md", f"instruction.md could not be read: {exc}")
        return
    if not text.strip():
        f.add("instruction-empty", "instruction.md", "instruction.md is empty")
        return
    lowered = text.lower()
    for token in LEAK_TOKENS:
        if token in lowered:
            f.add("instruction-leak", "instruction.md",
                  f"instruction.md references '{token}'; describe the observable contract instead")
    # Reference fixtures must not ship inside the agent environment.
    tests_dir = os.path.join(root, "tests")
    env_dir = os.path.join(root, "environment")
    if os.path.isdir(tests_dir) and os.path.isdir(env_dir):
        env_names = set()
        for base, _dirs, files in os.walk(env_dir):
            env_names.update(files)
        for base, _dirs, files in os.walk(tests_dir):
            for name in files:
                if name in env_names and name not in {"Dockerfile", ".dockerignore"}:
                    f.add("fixture-in-agent-env", f"environment/{name}",
                          f"{name} exists in both environment/ and tests/; the agent can read the expected fixture")


def check_secrets(root: str, f: Findings) -> None:
    f.check("secret-scan")
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
        for name in files:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root)
            try:
                text = read_text(path)
            except (OSError, UnicodeDecodeError):
                continue
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    f.add("secret-material", rel, f"possible {label} material in {rel}")


def check_rollouts(path: str, f: Findings) -> None:
    f.check("rollouts")
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        f.add("rollouts-unreadable", os.path.basename(path), f"rollout manifest unreadable: {exc}")
        return
    rollouts = manifest.get("rollouts") if isinstance(manifest, dict) else manifest
    if not isinstance(rollouts, list) or not rollouts:
        f.add("rollouts-empty", os.path.basename(path), "rollout manifest has no rollouts")
        return
    seen: dict[str, list[int]] = {}
    for entry in rollouts:
        if not isinstance(entry, dict):
            f.add("rollouts-malformed", os.path.basename(path), "rollout entry is not an object")
            continue
        cls = str(entry.get("class", "")).strip().lower()
        trials = entry.get("trials")
        if cls not in CONTROL_EXPECTATIONS:
            f.add("rollouts-unknown-class", os.path.basename(path),
                  f"unknown control class '{cls}'")
            continue
        if not isinstance(trials, list) or not trials:
            f.add("rollouts-missing-trials", os.path.basename(path),
                  f"control '{cls}' has no trials")
            continue
        cleaned = []
        for value in trials:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                f.add("rollouts-bad-trial", os.path.basename(path),
                      f"control '{cls}' has a non-numeric trial value")
                cleaned = []
                break
            cleaned.append(int(value))
        if not cleaned:
            continue
        seen[cls] = cleaned
        expected = CONTROL_EXPECTATIONS[cls]
        if any(v != expected for v in cleaned):
            f.add("control-wrong-reward", os.path.basename(path),
                  f"control '{cls}' expected every trial = {expected}, observed {cleaned}")
        if len(cleaned) < MIN_TRIALS:
            f.add("control-too-few-trials", os.path.basename(path),
                  f"control '{cls}' has {len(cleaned)} trials; at least {MIN_TRIALS} are required")
        if len(set(cleaned)) > 1:
            f.add("flaky-control", os.path.basename(path),
                  f"control '{cls}' produced mixed outcomes {cleaned}; fix nondeterminism")
    for cls in CONTROL_EXPECTATIONS:
        if cls not in seen:
            f.add("control-missing", os.path.basename(path),
                  f"control class '{cls}' has no rollout evidence")


def verify(root: str, rollouts: str | None = None) -> dict:
    findings = Findings()
    if not os.path.isdir(root):
        raise ValueError(f"task directory not found: {root}")
    layout = check_layout(root, findings)
    config = check_config(root, findings, layout)
    check_solution(root, findings)
    check_verifier_script(root, findings, config)
    check_leakage(root, findings)
    check_secrets(root, findings)
    if rollouts:
        check_rollouts(rollouts, findings)
    blocking = findings.blocking()
    return {
        "task_path": os.path.abspath(root),
        "checks_run": findings.checks,
        "findings": findings.items,
        "blocking_findings": len(blocking),
        "warning_findings": len(findings.items) - len(blocking),
        "publishable": not blocking,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify an agent benchmark task package.")
    parser.add_argument("task_dir")
    parser.add_argument("--rollouts", default=None, help="rollout manifest JSON")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args(argv)

    try:
        report = verify(args.task_dir, args.rollouts)
    except (ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc), "publishable": False}), file=sys.stderr)
        sys.stdout.flush()
        return 2

    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        print(f"task: {report['task_path']}")
        print(f"checks: {', '.join(report['checks_run'])}")
        for item in report["findings"]:
            print(f"[{item['severity']}] {item['code']} ({item['path']}): {item['message']}")
        print(f"blocking: {report['blocking_findings']}  warnings: {report['warning_findings']}")
        print("publishable" if report["publishable"] else "not publishable")
    sys.stdout.flush()
    return 0 if report["publishable"] else 1


if __name__ == "__main__":
    sys.exit(main())
