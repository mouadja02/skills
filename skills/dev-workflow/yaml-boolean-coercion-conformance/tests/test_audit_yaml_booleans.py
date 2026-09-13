#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_yaml_booleans.py"
spec = importlib.util.spec_from_file_location("audit_yaml_booleans", SCRIPT)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class AuditTests(unittest.TestCase):
    def test_block_flow_roles_and_coordinates(self):
        text = "enabled: yes\nfeature: \"on\"\noff: deploy\nitems:\n  - no\nflow: {mode: ON, safe: 'no'}\n"
        report = module.audit(text)
        observed = [(f["line"], f["column"], f["spelling"], f["role"], f["kind"]) for f in report["findings"]]
        self.assertEqual(observed, [
            (1, 10, "yes", "value", "legacy_only_boolean"),
            (3, 1, "off", "key", "legacy_only_boolean"),
            (5, 5, "no", "value", "legacy_only_boolean"),
            (6, 14, "ON", "value", "legacy_only_boolean"),
        ])

    def test_comments_block_scalars_substrings_and_multidoc(self):
        text = "# yes\nmessage: |\n  yes no on off\nlist: [y, N, true, false, off]\nmap: {Yes: value, quoted: \"NO\", path: /on/off}\n---\nnested:\n  choice: Off\n"
        report = module.audit(text)
        observed = [(f["line"], f["column"], f["spelling"], f["kind"]) for f in report["findings"]]
        self.assertEqual(observed, [
            (4, 8, "y", "legacy_only_boolean"),
            (4, 11, "N", "legacy_only_boolean"),
            (4, 14, "true", "stable_boolean"),
            (4, 20, "false", "stable_boolean"),
            (4, 27, "off", "legacy_only_boolean"),
            (5, 7, "Yes", "legacy_only_boolean"),
            (8, 11, "Off", "legacy_only_boolean"),
        ])

    def test_all_yaml_11_spellings_case_insensitive(self):
        tokens = "y Y yes Yes YES n N no No NO true True TRUE false False FALSE on On ON off Off OFF"
        report = module.audit("values: [" + tokens.replace(" ", ", ") + "]\n")
        self.assertEqual(report["finding_count"], 22)
        self.assertEqual(report["legacy_only_count"], 16)

    def test_larger_plain_scalars_are_not_findings(self):
        report = module.audit("a: yes please\nb: /on/off\nc: foo-no\nd: https://example.test/on\n")
        self.assertEqual(report["findings"], [])

    def test_malformed_inputs_fail_closed(self):
        for text in ["x: [yes}\n", "x: [yes\n", "x: \"yes\n", "x:\n\t- yes\n", "x: no\x00\n"]:
            with self.subTest(text=text):
                with self.assertRaises(module.AuditError):
                    module.audit(text)

    def test_cli_exit_codes_and_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "bad.yml"
            bad.write_bytes(b"x: \xff\n")
            proc = subprocess.run([sys.executable, str(SCRIPT), str(bad)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            flagged = root / "flagged.yml"
            flagged.write_text("mode: no\n", encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), str(flagged)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(json.loads(proc.stdout)["legacy_only_count"], 1)
            clean = root / "clean.yml"
            clean.write_text('mode: "no"\nenabled: true\n', encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), str(clean)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)

    def test_stdout_failure_uses_exit_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clean.yml"
            path.write_text("enabled: true\n", encoding="utf-8")
            with mock.patch.object(sys, "argv", [str(SCRIPT), str(path)]), mock.patch.object(sys, "stdout", io.StringIO()) as stdout:
                stdout.flush = mock.Mock(side_effect=OSError("closed sink"))
                with mock.patch.object(sys, "stderr", io.StringIO()):
                    self.assertEqual(module.main(), 3)


if __name__ == "__main__":
    unittest.main()
