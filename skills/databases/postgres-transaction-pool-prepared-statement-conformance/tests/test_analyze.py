#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze.py"
spec = importlib.util.spec_from_file_location("analyze", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load analyzer")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = {
    "pool_mode": "transaction",
    "preparation_kind": "protocol_named",
    "max_prepared_statements": 0,
    "client_statement_cache": True,
    "operation": "query",
    "concurrent_clients": 8,
}

class AnalyzeTests(unittest.TestCase):
    def test_tracking_disabled_is_incompatible(self):
        result = mod.analyze(mod.validate(dict(BASE)))
        self.assertEqual(result["classification"], "incompatible")
        self.assertIn("PROTOCOL_TRACKING_DISABLED", {x["code"] for x in result["findings"]})

    def test_tracking_enabled_is_conditional(self):
        case = dict(BASE, max_prepared_statements=100)
        self.assertEqual(mod.analyze(mod.validate(case))["classification"], "conditionally_compatible")

    def test_sql_prepare_not_transaction_safe(self):
        case = dict(BASE, preparation_kind="sql_prepare")
        self.assertIn("SQL_PREPARE_REQUIRES_SESSION_AFFINITY", {x["code"] for x in mod.analyze(mod.validate(case))["findings"]})

    def test_session_mode_does_not_get_transaction_rule(self):
        case = dict(BASE, pool_mode="session", preparation_kind="sql_prepare")
        self.assertEqual(mod.analyze(mod.validate(case))["classification"], "compatible_by_declared_invariants")

    def test_statement_copy_rejected(self):
        case = dict(BASE, pool_mode="statement", operation="copy", max_prepared_statements=100)
        self.assertIn("STATEMENT_POOL_OPERATION_BOUNDARY", {x["code"] for x in mod.analyze(mod.validate(case))["findings"]})

    def test_direct_session_not_applicable(self):
        case = dict(BASE, pool_mode="none", preparation_kind="none")
        self.assertFalse(mod.analyze(mod.validate(case))["applicable"])

    def test_cache_off_is_observation_not_violation(self):
        case = dict(BASE, client_statement_cache=False, max_prepared_statements=100)
        result = mod.analyze(mod.validate(case))
        self.assertIn("NAMED_PREPARATION_DESPITE_CACHE_OFF", {x["code"] for x in result["observations"]})
        self.assertEqual(result["findings"], [])

    def test_missing_field_fails_closed(self):
        case = dict(BASE); del case["pool_mode"]
        with self.assertRaises(ValueError): mod.validate(case)

    def test_unknown_field_fails_closed(self):
        with self.assertRaises(ValueError): mod.validate(dict(BASE, surprise=True))

    def test_boolean_integer_rejected(self):
        with self.assertRaises(ValueError): mod.validate(dict(BASE, concurrent_clients=True))

    def test_out_of_range_integer_rejected(self):
        with self.assertRaises(ValueError): mod.validate(dict(BASE, concurrent_clients=10**9))

    def test_giant_integer_rejected_without_overflow(self):
        with self.assertRaises(ValueError):
            mod.validate(dict(BASE, max_prepared_statements=10**10000))

    def test_nan_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.txt"
            path.write_text(json.dumps(BASE).replace('"max_prepared_statements": 0', '"max_prepared_statements": NaN'))
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("non-standard JSON number", run.stderr)

    def test_non_object_json_fails_closed(self):
        with self.assertRaises(ValueError):
            mod.validate([])

    def test_missing_input_fails_closed(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing/input.json"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn("error:", run.stderr)

    def test_controlled_output_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.json"
            source.write_text(json.dumps(BASE))
            run = subprocess.run([sys.executable, str(SCRIPT), str(source), "--output", tmp], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("error:", run.stderr)

if __name__ == "__main__":
    unittest.main()
