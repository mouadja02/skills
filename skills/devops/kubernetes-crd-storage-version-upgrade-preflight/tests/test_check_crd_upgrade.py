#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_crd_upgrade.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

def run(path: Path, output: str | Path = "-"):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(CHECKER), "--input", str(path), "--output", str(output)], text=True, capture_output=True, env=env)

class CheckerTests(unittest.TestCase):
    def test_normal_passes(self):
        result = run(FIXTURES / "normal.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "pass")

    def test_edge_fails_with_required_boundaries(self):
        result = run(FIXTURES / "edge.json")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        codes = {f["code"] for f in report["findings"]}
        required = {"WEBHOOK_ENDPOINTS_UNREADY", "WEBHOOK_CA_INVALID", "ROUND_TRIP_DATA_LOSS",
                    "REWRITE_INCOMPLETE", "OLD_VERSION_STILL_STORED", "OLD_VERSION_UNSERVED_TOO_EARLY",
                    "BACKUP_UNVERIFIED", "ROLLBACK_UNDOCUMENTED"}
        self.assertTrue(required.issubset(codes), required - codes)
        self.assertFalse(report["mutation_permitted"])

    def test_non_crd_target_is_not_applicable(self):
        result = run(FIXTURES / "not-applicable.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "not_applicable")

    def malformed(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(text)
            return run(path)

    def test_duplicate_key_fails_closed(self):
        result = self.malformed('{"schema_version":1,"schema_version":1,"kind":"kubernetes_crd_storage_upgrade_preflight","target_type":"x"}')
        self.assertEqual(result.returncode, 2)

    def test_nan_fails_closed(self):
        result = self.malformed('{"schema_version":NaN,"kind":"kubernetes_crd_storage_upgrade_preflight","target_type":"x"}')
        self.assertEqual(result.returncode, 2)

    def test_non_object_root_fails_closed(self):
        self.assertEqual(self.malformed('[]').returncode, 2)

    def test_unknown_root_field_fails_closed(self):
        self.assertEqual(self.malformed('{"schema_version":1,"kind":"kubernetes_crd_storage_upgrade_preflight","target_type":"x","extra":true}').returncode, 2)

    def test_loose_boolean_fails_closed(self):
        packet = json.loads((FIXTURES / "normal.json").read_text())
        packet["cluster"]["disposable"] = 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"; path.write_text(json.dumps(packet))
            self.assertEqual(run(path).returncode, 2)

    def test_duplicate_fixture_id_fails_closed(self):
        packet = json.loads((FIXTURES / "normal.json").read_text())
        packet["round_trip_fixtures"].append(dict(packet["round_trip_fixtures"][0]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"; path.write_text(json.dumps(packet))
            self.assertEqual(run(path).returncode, 2)

    def test_unwritable_output_fails_closed(self):
        result = run(FIXTURES / "normal.json", ROOT)
        self.assertEqual(result.returncode, 2)

if __name__ == "__main__":
    unittest.main()
