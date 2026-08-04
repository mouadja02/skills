#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_state_upgrade_evidence.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CheckerTests(unittest.TestCase):
    def run_case(self, name: str, *extra: str):
        return subprocess.run([sys.executable, str(CHECKER), str(FIXTURES / name), *extra], text=True, capture_output=True, check=False)

    def test_normal_passes(self):
        result = self.run_case("normal.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")

    def test_edge_fails_with_boundaries(self):
        result = self.run_case("edge.json")
        self.assertEqual(result.returncode, 1)
        codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
        self.assertTrue({"NON_SEQUENTIAL_TRANSITION", "TRANSITION_COVERAGE_GAP", "HISTORICAL_SCHEMA_UNPROVEN", "PLAN_CHECK_UNSUPPORTED", "RELEASED_MIGRATION_FAILED", "RESTORE_NOT_REHEARSED"} <= codes)

    def test_other_task_is_not_applicable(self):
        result = self.run_case("should-not-activate.json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "not_applicable")

    def test_malformed_json_is_invalid(self):
        result = self.run_case("malformed.txt")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)["status"], "invalid")

    def test_nan_is_rejected(self):
        result = self.run_case("nan.json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("non-standard JSON constant", result.stderr)

    def test_top_level_array_is_invalid(self):
        result = self.run_case("array.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["findings"][0]["code"], "PACKET_NOT_OBJECT")

    def test_duplicate_transition_fails(self):
        packet = json.loads((FIXTURES / "normal.json").read_text())
        packet["transitions"].append(dict(packet["transitions"][1]))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "packet.json"
            path.write_text(json.dumps(packet))
            result = subprocess.run([sys.executable, str(CHECKER), str(path)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        codes = {item["code"] for item in json.loads(result.stdout)["findings"]}
        self.assertIn("DUPLICATE_TRANSITION", codes)

    def test_direct_to_current_strategy_passes(self):
        packet = json.loads((FIXTURES / "normal.json").read_text())
        packet["upgrade_strategy"] = "direct_to_current"
        packet["transitions"][0]["to"] = 2
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "packet.json"
            path.write_text(json.dumps(packet))
            result = subprocess.run([sys.executable, str(CHECKER), str(path)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")

    def test_boolean_integer_is_rejected_as_version(self):
        packet = json.loads((FIXTURES / "normal.json").read_text())
        packet["current_schema_version"] = True
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "packet.json"
            path.write_text(json.dumps(packet))
            result = subprocess.run([sys.executable, str(CHECKER), str(path)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CURRENT_VERSION_INVALID", result.stdout)

    def test_atomic_output(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "result.json"
            result = self.run_case("normal.json", "--output", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(target.read_text())["status"], "pass")

    def test_controlled_output_failure_is_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_case("normal.json", "--output", folder)
            self.assertEqual(result.returncode, 2)
            self.assertIn("INPUT_OR_OUTPUT_ERROR", result.stderr)


if __name__ == "__main__":
    unittest.main()
