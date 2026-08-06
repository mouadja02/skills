from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_tool_stream.py"
FIXTURES = ROOT / "tests" / "fixtures"
spec = importlib.util.spec_from_file_location("validator", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load validator module")
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def schema(name: str = "weather") -> dict:
    return {
        name: {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        }
    }


def openai(arguments: list[str], *, finish: str | None = "tool_calls", call_id: str = "call_1") -> dict[str, Any]:
    chunks = []
    for index, part in enumerate(arguments):
        item = {"index": 0, "function": {"arguments": part}}
        if index == 0:
            item.update({"id": call_id, "type": "function"})
            item["function"]["name"] = "weather"
        choice = {"delta": {"tool_calls": [item]}}
        if index == len(arguments) - 1 and finish is not None:
            choice["finish_reason"] = finish
        chunks.append({"choices": [choice]})
    return {"profile": "openai", "tool_schemas": schema(), "chunks": chunks}


def codes(report: dict) -> set[str]:
    return {item["code"] for item in report["findings"]}


class ValidatorTests(unittest.TestCase):
    def test_packaged_normal_fixture(self) -> None:
        report = validator.validate(json.loads((FIXTURES / "normal.json").read_text()))
        self.assertEqual("pass", report["status"])
        self.assertTrue(report["executable"])
        self.assertEqual({"city": "Paris"}, report["calls"][0]["arguments"])

    def test_identity_collision_blocks_turn(self) -> None:
        report = validator.validate(json.loads((FIXTURES / "difficult.json").read_text()))
        self.assertEqual("fail", report["status"])
        self.assertFalse(report["executable"])
        self.assertIn("identity_collision", codes(report))

    def test_text_only_is_not_applicable(self) -> None:
        report = validator.validate(json.loads((FIXTURES / "should-not-activate.json").read_text()))
        self.assertEqual("not_applicable", report["status"])
        self.assertFalse(report["applicable"])

    def test_anthropic_fragmented_input(self) -> None:
        document = {
            "profile": "anthropic", "tool_schemas": schema(), "events": [
                {"type": "content_block_start", "index": 1, "content_block": {"type": "tool_use", "id": "toolu_1", "name": "weather", "input": {}}},
                {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": "{\"city\":\"Par"}},
                {"type": "content_block_delta", "index": 1, "delta": {"type": "input_json_delta", "partial_json": "is\"}"}},
                {"type": "content_block_stop", "index": 1},
            ]}
        report = validator.validate(document)
        self.assertEqual("pass", report["status"])
        self.assertEqual("toolu_1", report["calls"][0]["id"])

    def test_mistral_openai_shape(self) -> None:
        document = openai(["{\"city\":", "\"Paris\"}"])
        document["profile"] = "mistral"
        self.assertEqual("pass", validator.validate(document)["status"])

    def test_choice_indices_have_separate_slot_scope(self) -> None:
        document = openai(["{\"city\":\"Paris\"}"])
        document["chunks"] = [{"choices": [
            {"index": 0, "delta": {"tool_calls": [{"index": 0, "id": "a", "function": {"name": "weather", "arguments": "{\"city\":\"Paris\"}"}}]}, "finish_reason": "tool_calls"},
            {"index": 1, "delta": {"tool_calls": [{"index": 0, "id": "b", "function": {"name": "weather", "arguments": "{\"city\":\"Lyon\"}"}}]}, "finish_reason": "tool_calls"},
            {"index": 2, "delta": {"content": "ordinary alternative"}, "finish_reason": "stop"},
        ]}]
        report = validator.validate(document)
        self.assertEqual("pass", report["status"])
        self.assertEqual(["choice:0", "choice:1"], [call["scope"] for call in report["calls"]])

    def test_missing_terminal_fails(self) -> None:
        report = validator.validate(openai(["{\"city\":\"Paris\"}"], finish=None))
        self.assertIn("missing_terminal", codes(report))
        self.assertFalse(report["executable"])

    def test_parseable_prefix_does_not_execute_early(self) -> None:
        report = validator.validate(openai(["{\"city\":\"Paris\"}", "{\"city\":\"Lyon\"}"]))
        self.assertIn("invalid_arguments_json", codes(report))
        self.assertFalse(report["executable"])

    def test_duplicate_terminal_fails(self) -> None:
        document = openai(["{\"city\":\"Paris\"}"])
        document["chunks"].append({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]})
        report = validator.validate(document)
        self.assertIn("duplicate_terminal", codes(report))

    def test_schema_required_and_additional_properties(self) -> None:
        report = validator.validate(openai(["{\"country\":\"FR\"}"]))
        self.assertIn("schema_required", codes(report))
        self.assertIn("schema_additional_property", codes(report))

    def test_unsupported_schema_keyword_fails_closed(self) -> None:
        document = openai(["{\"city\":\"Paris\"}"])
        document["tool_schemas"]["weather"]["oneOf"] = []
        report = validator.validate(document)
        self.assertIn("unsupported_schema_keyword", codes(report))
        self.assertFalse(report["executable"])

    def test_unknown_tool_fails_closed(self) -> None:
        document = openai(["{\"city\":\"Paris\"}"])
        document["tool_schemas"] = {}
        report = validator.validate(document)
        self.assertIn("unknown_tool", codes(report))

    def test_nonfinite_argument_rejected(self) -> None:
        report = validator.validate(openai(["{\"city\":NaN}"]))
        self.assertIn("invalid_arguments_json", codes(report))

    def test_nonfinite_fixture_rejected_by_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.txt"
            path.write_text('{"profile":"openai","chunks":[],"x":Infinity}', encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path), "--report", "json"], capture_output=True, text=True)
        self.assertEqual(2, run.returncode)
        self.assertIn("non-standard JSON constant", run.stderr)

    def test_malformed_fixture_rejected_by_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.txt"
            path.write_text('{"profile":', encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
        self.assertEqual(2, run.returncode)
        self.assertIn("input error", run.stderr)

    def test_wrong_container_shapes_fail(self) -> None:
        report = validator.validate({"profile": "openai", "tool_schemas": [], "chunks": {}})
        self.assertIn("invalid_tool_schemas", codes(report))
        self.assertIn("invalid_chunks", codes(report))

    def test_delta_after_anthropic_terminal_fails(self) -> None:
        document = {
            "profile": "anthropic", "tool_schemas": schema(), "events": [
                {"type": "content_block_start", "index": 0, "content_block": {"type": "tool_use", "id": "x", "name": "weather", "input": {}}},
                {"type": "content_block_delta", "index": 0, "delta": {"type": "input_json_delta", "partial_json": "{\"city\":\"Paris\"}"}},
                {"type": "content_block_stop", "index": 0},
                {"type": "content_block_delta", "index": 0, "delta": {"type": "input_json_delta", "partial_json": " "}},
            ]}
        report = validator.validate(document)
        self.assertIn("delta_after_terminal", codes(report))


if __name__ == "__main__":
    unittest.main()
