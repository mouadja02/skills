#!/usr/bin/env python3
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

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "validate_genai.py"
SPEC = importlib.util.spec_from_file_location("validator", SCRIPT)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(validator)
PROFILES = validator.load_json(HERE.parent / "references" / "profiles.json")
PROFILE = "otel-genai-main-434c91d"


def doc(records, capture=None):
    return {"schema_version": 1, "profile": PROFILE, "content_capture": capture or {"opt_in": False, "redaction_verified": False, "truncation_limit": None}, "records": records}


def record(name="chat model", attrs=None, kind="span"):
    return {"kind": kind, "name": name, "attributes": attrs or {"gen_ai.operation.name": "chat", "gen_ai.request.model": "model"}}


class ValidatorTests(unittest.TestCase):
    def codes(self, result):
        return {item["code"] for item in result["findings"]}

    def test_valid_span_passes(self):
        result = validator.validate(doc([record(attrs={"gen_ai.operation.name": "chat", "gen_ai.request.model": "model", "gen_ai.usage.input_tokens": 5, "gen_ai.usage.cache_read.input_tokens": 2})]), PROFILES)
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["mutation_permitted"])

    def test_non_genai_is_not_applicable(self):
        result = validator.validate(doc([record("SELECT", {"db.system.name": "postgresql"})]), PROFILES)
        self.assertEqual(result["status"], "not_applicable")

    def test_legacy_content_and_token_edge_fails(self):
        attrs = {"gen_ai.system": "openai", "gen_ai.usage.input_tokens": 1, "gen_ai.usage.cache_read.input_tokens": 2, "gen_ai.input.messages": []}
        result = validator.validate(doc([record(attrs=attrs), record("gen_ai.client.inference.operation.details", {"gen_ai.operation.name": "chat"}, "event")]), PROFILES)
        self.assertTrue({"legacy_attribute", "legacy_event", "content_without_opt_in", "input_token_total_too_small"}.issubset(self.codes(result)))
        self.assertEqual(result["status"], "fail")

    def test_unknown_profile_fails_closed(self):
        value = doc([]); value["profile"] = "future"
        with self.assertRaisesRegex(ValueError, "pinned profile"):
            validator.validate(value, PROFILES)

    def test_wrong_root_shape_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "root"):
            validator.validate([], PROFILES)

    def test_unknown_root_key_fails_closed(self):
        value = doc([]); value["extra"] = True
        with self.assertRaisesRegex(ValueError, "unknown root keys"):
            validator.validate(value, PROFILES)

    def test_strict_boolean(self):
        value = doc([]); value["content_capture"]["opt_in"] = 1
        with self.assertRaisesRegex(ValueError, "booleans"):
            validator.validate(value, PROFILES)

    def test_nan_json_rejected(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write('{"x": NaN}'); path = Path(f.name)
        try:
            with self.assertRaisesRegex(ValueError, "non-standard"):
                validator.load_json(path)
        finally:
            path.unlink()

    def test_malformed_json_cli_is_error(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("{"); path = f.name
        try:
            run = subprocess.run([sys.executable, str(SCRIPT), "--input", path], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("validation error", run.stderr)
        finally:
            os.unlink(path)

    def test_missing_file_cli_is_error(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "--input", "/definitely/missing"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)

    def test_negative_and_boolean_tokens_rejected(self):
        result = validator.validate(doc([record(attrs={"gen_ai.operation.name": "chat", "gen_ai.usage.input_tokens": -1, "gen_ai.usage.output_tokens": True})]), PROFILES)
        self.assertEqual([x["code"] for x in result["findings"]].count("invalid_token_count"), 2)

    def test_execute_tool_name_and_tool_required(self):
        result = validator.validate(doc([record("wrong", {"gen_ai.operation.name": "execute_tool"})]), PROFILES)
        self.assertTrue({"missing_tool_name"}.issubset(self.codes(result)))

    def test_content_with_controls_is_allowed(self):
        capture = {"opt_in": True, "redaction_verified": True, "truncation_limit": 256}
        result = validator.validate(doc([record(attrs={"gen_ai.operation.name": "chat", "gen_ai.request.model": "model", "gen_ai.input.messages": []})], capture), PROFILES)
        self.assertEqual(result["status"], "pass")

    def test_output_write_failure_returns_error(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            json.dump(doc([]), f); path = f.name
        try:
            with mock.patch.object(validator.sys.stdout, "write", side_effect=OSError("closed")):
                self.assertEqual(validator.main(["--input", path]), 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
