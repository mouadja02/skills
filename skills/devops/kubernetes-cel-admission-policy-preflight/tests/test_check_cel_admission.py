#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_cel_admission.py"
SPEC = importlib.util.spec_from_file_location("checker", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def valid() -> dict:
    return {
        "schema_version": 1,
        "kind": "kubernetes_cel_admission_preflight",
        "target_type": "native_vap",
        "inventory": {"kubernetes_version": "1.34.1", "cel_environment": "kubernetes-1.34"},
        "policy": {"failure_policy": "Fail", "match_operations": ["CREATE", "UPDATE"], "required_context": ["object", "request.userInfo", "params"]},
        "bindings": [{"name": "canary", "validation_actions": ["Audit", "Warn"]}],
        "fixtures": [
            {"id": "create", "operation": "CREATE", "user_info": True, "old_object": "null", "params": "present", "outcome": "allow"},
            {"id": "update", "operation": "UPDATE", "user_info": True, "old_object": "present", "params": "present", "outcome": "deny"},
            {"id": "no-params", "operation": "CREATE", "user_info": True, "old_object": "null", "params": "absent", "outcome": "error"},
        ],
        "cost": {"static_estimate_checked": True, "runtime_budget_observed": True},
        "resources": {"baseline_mib": 100, "observed_mib": 102, "policy_binding_pairs": 10, "max_extra_mib_per_pair": 0.3},
        "bootstrap": {"policy_node": "vap", "nodes": ["vap", "api", "controller"], "edges": [["api", "controller"], ["controller", "vap"]]},
        "rollout": {"stage": "Warn", "canary_observed": True, "emergency_rollback_documented": True},
    }


class CheckerTests(unittest.TestCase):
    def test_pass(self):
        report = checker.analyze(valid())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["finding_codes"], [])
        self.assertFalse(report["mutation_permitted"])

    def test_not_applicable_short_circuits_native_sections(self):
        data = {"schema_version": 1, "kind": "kubernetes_cel_admission_preflight", "target_type": "kyverno_policy", "inventory": {"kubernetes_version": "1.34", "cel_environment": "kubernetes-1.34"}}
        self.assertEqual(checker.analyze(data)["status"], "not_applicable")

    def test_difficult_edge_codes(self):
        data = valid()
        data["inventory"]["cel_environment"] = ""
        data["policy"]["match_operations"] = ["CREATE", "DELETE"]
        data["fixtures"] = [{"id": "create", "operation": "CREATE", "user_info": False, "old_object": "omitted", "params": "present", "outcome": "allow"}]
        data["cost"] = {"static_estimate_checked": False, "runtime_budget_observed": False}
        data["resources"]["observed_mib"] = 108
        data["bootstrap"]["edges"] = [["vap", "controller"], ["controller", "api"], ["api", "vap"]]
        data["bindings"] = [{"name": "production", "validation_actions": ["Deny"]}]
        data["rollout"] = {"stage": "Deny", "canary_observed": False, "emergency_rollback_documented": False}
        codes = set(checker.analyze(data)["finding_codes"])
        self.assertTrue({"CEL_ENVIRONMENT_UNPINNED", "OPERATION_UNTESTED", "DELETE_OLD_OBJECT_UNTESTED", "USER_INFO_UNTESTED", "PARAMS_ABSENCE_UNTESTED", "FAILURE_POLICY_UNTESTED", "STATIC_COST_UNCHECKED", "RUNTIME_COST_UNOBSERVED", "RESOURCE_BUDGET_EXCEEDED", "BOOTSTRAP_DEPENDENCY_CYCLE", "DENY_WITHOUT_CANARY", "ROLLBACK_UNDOCUMENTED"} <= codes)

    def test_unknown_field_rejected(self):
        data = valid(); data["secret"] = "x"
        with self.assertRaises(checker.InputError): checker.analyze(data)

    def test_strict_boolean_rejected(self):
        data = valid(); data["cost"]["static_estimate_checked"] = 1
        with self.assertRaises(checker.InputError): checker.analyze(data)

    def test_duplicate_fixture_id_rejected(self):
        data = valid(); data["fixtures"][1]["id"] = "create"
        with self.assertRaises(checker.InputError): checker.analyze(data)

    def test_edge_unknown_node_rejected(self):
        data = valid(); data["bootstrap"]["edges"] = [["vap", "missing"]]
        with self.assertRaises(checker.InputError): checker.analyze(data)

    def test_non_integer_pair_count_rejected(self):
        data = valid(); data["resources"]["policy_binding_pairs"] = 1.5
        with self.assertRaises(checker.InputError): checker.analyze(data)

    def test_nonfinite_number_rejected(self):
        data = valid(); data["resources"]["observed_mib"] = math.inf
        with self.assertRaises(checker.InputError): checker.analyze(data)

    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"; path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            with self.assertRaises(checker.InputError): checker.load(path)

    def test_nan_json_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"; path.write_text('{"x":NaN}', encoding="utf-8")
            with self.assertRaises(checker.InputError): checker.load(path)

    def test_malformed_json_cli_exit_two(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"; path.write_text("{", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)

    def test_fail_cli_exit_one(self):
        data = valid(); data["cost"]["static_estimate_checked"] = False
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fail.json"; path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "fail")

    def test_controlled_output_failure(self):
        data = valid()
        with mock.patch.object(checker.os, "replace", side_effect=OSError("controlled")):
            with tempfile.TemporaryDirectory() as td:
                with self.assertRaises(checker.InputError): checker.emit(checker.analyze(data), Path(td) / "out.json")


if __name__ == "__main__":
    unittest.main()
