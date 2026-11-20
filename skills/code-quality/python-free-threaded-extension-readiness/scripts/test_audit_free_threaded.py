#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("audit_free_threaded.py")


def ready() -> dict:
    return {
        "schema_version": 1,
        "project": "fixture",
        "claim": "ready",
        "native_extensions": [
            {"name": "fixture._core", "gil_declaration": "not-used", "stress": {"runs": 50, "threads": 4, "completed": True, "failures": 0}, "tsan": "clean"}
        ],
        "builds": [
            {"mode": "gil", "passed": True, "py_gil_disabled": False},
            {"mode": "free-threaded", "passed": True, "py_gil_disabled": True},
        ],
        "dependencies": [{"name": "native-lib", "version": "1.0", "free_threaded_support": "yes"}],
    }


class AuditTests(unittest.TestCase):
    def run_data(self, data, *args):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            if isinstance(data, str):
                path.write_text(data, encoding="utf-8")
            else:
                path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), *args, str(path)], text=True, capture_output=True, check=False)
            return result.returncode, json.loads(result.stdout)

    def test_ready(self):
        code, output = self.run_data(ready(), "--require-tsan")
        self.assertEqual(code, 0)
        self.assertEqual(output["status"], "ready")

    def test_difficult_edge_blocks_for_all_boundaries(self):
        data = ready()
        extension = data["native_extensions"][0]
        extension["gil_declaration"] = "unknown"
        extension["stress"] = {"runs": 1, "threads": 2, "completed": True, "failures": 0}
        extension["tsan"] = "findings"
        data["dependencies"][0]["free_threaded_support"] = "unknown"
        code, output = self.run_data(data)
        self.assertEqual(code, 1)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(len(output["blocking"]), 4)

    def test_no_native_extensions_is_not_applicable(self):
        data = ready()
        data.update(claim="not-applicable", native_extensions=[], builds=[], dependencies=[])
        code, output = self.run_data(data)
        self.assertEqual((code, output["status"]), (0, "not_applicable"))

    def test_not_applicable_with_build_evidence_is_invalid(self):
        data = ready()
        data.update(claim="not-applicable", native_extensions=[], dependencies=[])
        code, output = self.run_data(data)
        self.assertEqual((code, output["status"]), (2, "invalid"))

    def test_missing_matrix_leg_blocks(self):
        data = ready()
        data["builds"].pop()
        code, output = self.run_data(data)
        self.assertEqual(code, 1)
        self.assertIn("missing free-threaded build leg", output["blocking"])

    def test_non_ready_claim_blocks_when_extensions_exist(self):
        data = ready()
        data["claim"] = "experimental"
        code, output = self.run_data(data)
        self.assertEqual(code, 1)
        self.assertIn("declared release claim is experimental, not ready", output["blocking"])

    def test_duplicate_mode_is_invalid(self):
        data = ready()
        data["builds"].append(data["builds"][0])
        code, output = self.run_data(data)
        self.assertEqual((code, output["status"]), (2, "invalid"))

    def test_unknown_key_is_invalid(self):
        data = ready()
        data["unexpected"] = True
        code, output = self.run_data(data)
        self.assertEqual((code, output["status"]), (2, "invalid"))

    def test_boolean_is_not_an_integer(self):
        data = ready()
        data["native_extensions"][0]["stress"]["runs"] = True
        code, output = self.run_data(data)
        self.assertEqual((code, output["status"]), (2, "invalid"))

    def test_non_finite_json_is_invalid(self):
        code, output = self.run_data('{"schema_version": NaN}')
        self.assertEqual((code, output["status"]), (2, "invalid"))

    def test_malformed_json_is_invalid(self):
        code, output = self.run_data("{")
        self.assertEqual((code, output["status"]), (2, "invalid"))

    def test_missing_file_is_invalid(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing/evidence.json"], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid")

    def test_require_tsan_changes_warning_to_block(self):
        data = ready()
        data["native_extensions"][0]["tsan"] = "not-run"
        code, output = self.run_data(data)
        self.assertEqual(code, 0)
        self.assertEqual(len(output["warnings"]), 1)
        code, output = self.run_data(data, "--require-tsan")
        self.assertEqual(code, 1)
        self.assertEqual(len(output["blocking"]), 1)


if __name__ == "__main__":
    unittest.main()
