import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "schema_preflight.py"
SPEC = importlib.util.spec_from_file_location("schema_preflight", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 8},
                "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
            },
            "required": ["name"],
        }

    def test_openai_reports_all_required_and_closed_object(self):
        findings = MODULE.profile_checks(self.schema, "openai")
        codes = {item["code"] for item in findings}
        self.assertIn("openai-all-required", codes)
        self.assertIn("openai-closed-object", codes)

    def test_bedrock_reports_max_length_and_open_object(self):
        findings = MODULE.profile_checks(self.schema, "bedrock")
        codes = {item["code"] for item in findings}
        self.assertIn("bedrock-unsupported", codes)
        self.assertIn("bedrock-open-object", codes)

    def test_tighten_is_copyable_and_reports_pointers(self):
        candidate, changes = MODULE.tighten_objects(json.loads(json.dumps(self.schema)))
        self.assertNotIn("additionalProperties", self.schema)
        self.assertFalse(candidate["additionalProperties"])
        self.assertIn("#/additionalProperties", changes)

    def test_tighten_does_not_treat_property_map_as_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "properties": {"type": "string"},
            },
        }
        candidate, changes = MODULE.tighten_objects(schema)
        self.assertEqual(False, candidate["additionalProperties"])
        self.assertNotIn("additionalProperties", candidate["properties"])
        self.assertEqual(["#/additionalProperties"], changes)

    def test_fixture_validation_preserves_original_constraints(self):
        valid = {"name": "short", "tags": ["a"]}
        invalid = {"name": "too-long-name", "tags": ["a", "b", "c"]}
        self.assertEqual([], MODULE.validate_instance(valid, self.schema, self.schema))
        errors = MODULE.validate_instance(invalid, self.schema, self.schema)
        self.assertTrue(any("maxLength" in item for item in errors))
        self.assertTrue(any("maxItems" in item for item in errors))

    def test_ref_sibling_constraint_is_enforced(self):
        schema = {
            "$defs": {"name": {"type": "string"}},
            "$ref": "#/$defs/name",
            "maxLength": 3,
        }
        errors = MODULE.validate_instance("long", schema, schema)
        self.assertTrue(any("maxLength" in item for item in errors))

    def test_malformed_required_reports_instead_of_crashing(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": None}
        findings = MODULE.structural_checks(schema) + MODULE.profile_checks(schema, "openai")
        self.assertIn("invalid-required", {item["code"] for item in findings})
        self.assertIn("openai-all-required", {item["code"] for item in findings})

    def test_effective_depth_ignores_unused_defs_and_combines_ref_siblings(self):
        schema = {
            "$defs": {
                "unused": {"type": "object", "properties": {"deep": {"type": "object"}}},
                "used": {"type": "object", "properties": {"child": {"type": "object"}}},
            },
            "$ref": "#/$defs/used",
            "properties": {"sibling": {"type": "object", "properties": {"leaf": {"type": "object"}}}},
        }
        self.assertEqual(3, MODULE.effective_object_depth(schema, schema))
        shallow = {"type": "object", "$defs": schema["$defs"]}
        self.assertEqual(1, MODULE.effective_object_depth(shallow, shallow))

    def test_cli_json_and_exit_code(self):
        with tempfile.TemporaryDirectory() as directory:
            schema_path = Path(directory) / "schema.json"
            fixture_path = Path(directory) / "valid.json"
            schema_path.write_text(json.dumps(self.schema), encoding="utf-8")
            fixture_path.write_text(json.dumps({"name": "ok"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(schema_path), "--profile", "generic", "--fixture", str(fixture_path), "--report", "json"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual("pass", report["result"])
            self.assertTrue(report["fixtures"][0]["expectation_met"])
            self.assertTrue(report["fixtures"][0]["observed_valid"])

    def test_cli_expected_invalid_fixture_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            schema_path = Path(directory) / "schema.json"
            fixture_path = Path(directory) / "invalid.json"
            schema_path.write_text(json.dumps(self.schema), encoding="utf-8")
            fixture_path.write_text(json.dumps({"name": "too-long-name"}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(schema_path), "--invalid-fixture", str(fixture_path), "--report", "json"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["fixtures"][0]["expectation_met"])
            self.assertFalse(report["fixtures"][0]["observed_valid"])

    def test_nonstandard_json_constant_invalid_fixture_fails_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            schema_path = Path(directory) / "schema.json"
            fixture_path = Path(directory) / "invalid.json"
            schema_path.write_text(json.dumps(self.schema), encoding="utf-8")
            fixture_path.write_text("NaN", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(schema_path), "--invalid-fixture", str(fixture_path), "--report", "json"],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(1, result.returncode, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["fixtures"][0]["expectation_met"])
            self.assertIsNone(report["fixtures"][0]["observed_valid"])
            self.assertTrue(report["fixtures"][0]["load_error"])


if __name__ == "__main__":
    unittest.main()
