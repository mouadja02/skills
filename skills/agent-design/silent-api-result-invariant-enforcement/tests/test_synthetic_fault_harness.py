import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "synthetic_fault_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fault_harness", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load harness")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SyntheticFaultHarnessTests(unittest.TestCase):
    def test_correct_api_is_verified_with_cost(self):
        report = load_module().run_scenario("correct")
        self.assertEqual(report["decision"], "verified")
        self.assertEqual(report["released_value"], 3)
        self.assertEqual(report["extra_calls"], 4)
        self.assertEqual(report["failed_checks"], [])

    def test_lasting_exact_faults_are_withheld(self):
        harness = load_module()
        for mode in ("drop-last", "cap-total", "or-semantics", "drop-field", "off-by-one"):
            with self.subTest(mode=mode):
                report = harness.run_scenario(mode)
                self.assertEqual(report["decision"], "withheld")
                self.assertIsNone(report["released_value"])
                self.assertTrue(report["failed_checks"])
                self.assertEqual(report["check_class"], "exact")

    def test_transient_fault_is_rechecked_before_release(self):
        report = load_module().run_scenario("transient")
        self.assertEqual(report["decision"], "verified_on_recheck")
        self.assertEqual(report["released_value"], 3)
        self.assertEqual(report["rechecks"], 1)

    def test_unsupported_capability_never_claims_verification(self):
        report = load_module().run_scenario("unsupported")
        self.assertEqual(report["decision"], "unsupported")
        self.assertFalse(report["verified"])
        self.assertEqual(report["extra_calls"], 0)
        self.assertIn("complement", report["limitations"][0])

    def test_cli_writes_complete_json_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--all", "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(len(payload["scenarios"]), 8)
            self.assertIn("consistently lying API", payload["global_limitations"])

    def test_cli_rejects_unknown_mode_without_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode", "unknown", "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 2)
            self.assertFalse(output.exists())

    def test_cli_output_failure_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing-directory"
            output.mkdir()
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "--mode", "correct", "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 2)
            self.assertTrue(output.is_dir())
            self.assertIn("error:", run.stderr)


if __name__ == "__main__":
    unittest.main()
