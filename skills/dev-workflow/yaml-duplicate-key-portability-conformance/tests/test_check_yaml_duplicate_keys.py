#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_yaml_duplicate_keys.py"


class DuplicateKeyTests(unittest.TestCase):
    def run_case(self, text: str, *args: str, suffix: str = ".yaml"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"fixture{suffix}"
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), *args],
                text=True,
                capture_output=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            report = json.loads(result.stdout) if result.stdout else None
            return result, report

    def test_block_nested_and_flow_duplicates(self):
        result, report = self.run_case("a: 1\na: 2\nnested: {x: 1, x: 2}\n")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["finding_count"], 2)
        self.assertEqual({item["reason"] for item in report["findings"]}, {"duplicate_explicit_key"})
        self.assertEqual(report["findings"][0]["first"], {"line": 1, "column": 1})

    def test_resolved_equal_boolean_keys(self):
        result, report = self.run_case("true: first\nTRUE: second\n")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["findings"][0]["reason"], "duplicate_resolved_key")

    def test_cross_type_numeric_and_sexagesimal_keys(self):
        result, report = self.run_case("1: integer\n1.0: float\n1:20: first\n80: second\n")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["finding_count"], 2)
        self.assertEqual({item["reason"] for item in report["findings"]}, {"duplicate_resolved_key"})

    def test_quoted_and_plain_string_are_duplicates(self):
        result, report = self.run_case('name: one\n"name": two\n')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["findings"][0]["reason"], "duplicate_resolved_key")

    def test_multi_document_and_merge_allow(self):
        text = "defaults: &d\n  retries: 3\njob:\n  <<: *d\n  retries: 4\n---\ntrue: one\nTRUE: two\n"
        result, report = self.run_case(text, "--merge-policy", "allow")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["document_count"], 2)
        self.assertEqual(report["finding_count"], 1)
        self.assertEqual(report["findings"][0]["document"], 2)
        self.assertEqual(report["findings"][0]["reason"], "duplicate_resolved_key")

    def test_merge_forbid_is_distinct_finding(self):
        result, report = self.run_case("base: &b {x: 1}\nvalue: {<<: *b, x: 2}\n")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["finding_count"], 1)
        self.assertEqual(report["findings"][0]["reason"], "merge_key_forbidden")

    def test_unique_mapping_passes(self):
        result, report = self.run_case("a: 1\nb: [2, 3]\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["finding_count"], 0)

    def test_malformed_fails_without_report(self):
        result, report = self.run_case("a: [1, 2\n")
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertIn("malformed YAML", result.stderr)

    def test_unsupported_tag_fails_closed(self):
        result, report = self.run_case("a: !unsafe value\n")
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertIn("unsupported tag", result.stderr)

    def test_json_extension_is_not_applicable(self):
        result, report = self.run_case('{"a": 1}\n', suffix=".json")
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertIn(".yaml or .yml", result.stderr)

    def test_missing_input_fails_closed(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing/fixture.yaml"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    @unittest.skipUnless(Path("/dev/full").exists(), "requires /dev/full")
    def test_output_failure_uses_exit_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.yaml"
            path.write_text("a: 1\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--output", "/dev/full"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 3)
        self.assertIn("unable to write report", result.stderr)


if __name__ == "__main__":
    unittest.main()
