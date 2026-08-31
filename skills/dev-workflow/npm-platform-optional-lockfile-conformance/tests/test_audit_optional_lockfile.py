#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_optional_lockfile.py"
spec = importlib.util.spec_from_file_location("auditor", SCRIPT)
assert spec is not None and spec.loader is not None
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)


def member(package: str, os_name: str, cpu: str, libc: str | None = None) -> dict:
    result = {"package": package, "os": [os_name], "cpu": [cpu]}
    if libc:
        result["libc"] = [libc]
    return result


def base() -> dict:
    names = {
        "@acme/native-linux-x64-gnu": ("linux", "x64", "glibc"),
        "@acme/native-linux-arm64-musl": ("linux", "arm64", "musl"),
        "@acme/native-darwin-arm64": ("darwin", "arm64", None),
        "@acme/native-win32-x64-msvc": ("win32", "x64", None),
    }
    packages = {"": {}}
    optionals = {}
    members = []
    for name, (os_name, cpu, libc) in names.items():
        optionals[name] = "2.0.0"
        entry = {"version": "2.0.0", "optional": True, "os": [os_name], "cpu": [cpu]}
        if libc:
            entry["libc"] = [libc]
        packages[f"node_modules/{name}"] = entry
        members.append(member(name, os_name, cpu, libc))
    return {
        "package_json": {"optionalDependencies": optionals},
        "lockfile": {"lockfileVersion": 3, "packages": packages},
        "families": [{"name": "acme-native", "members": members}],
        "targets": [
            {"os": "linux", "cpu": "x64", "libc": "glibc"},
            {"os": "linux", "cpu": "arm64", "libc": "musl"},
            {"os": "darwin", "cpu": "arm64"},
            {"os": "win32", "cpu": "x64"},
        ],
    }


class AuditTests(unittest.TestCase):
    def test_conformant_all_modes(self):
        result, findings = auditor.audit(base())
        self.assertFalse(findings)
        self.assertEqual(result["classification"], "conformant")
        self.assertEqual(result["summary"], {"families": 1, "targets": 4, "findings": 0})

    def test_missing_stale_selector_and_target_findings(self):
        data = base()
        packages = data["lockfile"]["packages"]
        del packages["node_modules/@acme/native-win32-x64-msvc"]
        packages["node_modules/@acme/native-linux-arm64-musl"]["version"] = "1.9.0"
        packages["node_modules/@acme/native-darwin-arm64"]["cpu"] = ["x64"]
        result, findings = auditor.audit(data)
        self.assertTrue(findings)
        codes = [item["code"] for item in result["findings"]]
        self.assertEqual(codes.count("MISSING_LOCK_ENTRY"), 1)
        self.assertEqual(codes.count("VERSION_MISMATCH"), 1)
        self.assertEqual(codes.count("SELECTOR_MISMATCH"), 1)
        self.assertEqual(codes.count("TARGET_UNCOVERED"), 3)

    def test_unrelated_workspace_optional_is_ignored(self):
        data = base()
        data["lockfile"]["packages"]["packages/tool"] = {"optionalDependencies": {"fsevents": "2.3.3"}}
        result, findings = auditor.audit(data)
        self.assertFalse(findings)
        self.assertNotIn("fsevents", json.dumps(result))

    def test_no_family_is_not_applicable_with_empty_findings(self):
        data = {"package_json": {"dependencies": {"left-pad": "1.3.0"}}, "lockfile": {"lockfileVersion": 3, "packages": {"": {}, "node_modules/left-pad": {"version": "1.3.0"}}}, "families": [], "targets": []}
        result, findings = auditor.audit(data)
        self.assertFalse(findings)
        self.assertFalse(result["applicable"])
        self.assertEqual(result["findings"], [])

    def test_mode_specific_libc_is_not_applied_to_darwin(self):
        data = base()
        result, findings = auditor.audit(data)
        self.assertFalse(findings)
        darwin = data["lockfile"]["packages"]["node_modules/@acme/native-darwin-arm64"]
        self.assertNotIn("libc", darwin)
        self.assertEqual(result["classification"], "conformant")

    def test_malformed_schema_and_duplicate_members_fail_closed(self):
        bad = base()
        bad["targets"] = "linux"
        with self.assertRaises(auditor.InputError):
            auditor.audit(bad)
        duplicate = base()
        duplicate["families"][0]["members"].append(duplicate["families"][0]["members"][0].copy())
        with self.assertRaises(auditor.InputError):
            auditor.audit(duplicate)

    def run_cli_bytes(self, payload: bytes) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
            handle.write(payload)
            path = handle.name
        try:
            return subprocess.run([sys.executable, str(SCRIPT), path], text=True, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        finally:
            os.unlink(path)

    def test_malformed_and_nonfinite_json_fail_closed(self):
        malformed = self.run_cli_bytes(b'{"package_json":')
        self.assertEqual(malformed.returncode, auditor.EXIT_INPUT)
        nonfinite = self.run_cli_bytes(b'{"package_json":{},"lockfile":{"lockfileVersion":NaN,"packages":{}},"families":[],"targets":[]}')
        self.assertEqual(nonfinite.returncode, auditor.EXIT_INPUT)

    @unittest.skipUnless(Path("/dev/full").exists(), "requires /dev/full")
    def test_controlled_stdout_failure_returns_74(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            json.dump(base(), handle)
            path = handle.name
        try:
            with open("/dev/full", "w") as sink:
                completed = subprocess.run([sys.executable, str(SCRIPT), path], stdout=sink, stderr=subprocess.PIPE, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(completed.returncode, auditor.EXIT_IO)
            self.assertIn("output error", completed.stderr)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
