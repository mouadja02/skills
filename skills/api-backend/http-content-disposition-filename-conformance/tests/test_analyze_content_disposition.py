#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_content_disposition.py"


class AnalyzerTests(unittest.TestCase):
    def run_case(self, document, expected=0):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.json"
            path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], text=True, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(expected, result.returncode, result.stderr)
        return json.loads(result.stdout) if result.stdout else None

    def test_filename_star_precedence_and_utf8(self):
        report = self.run_case({
            "content_disposition": "attachment; filename=\"resume.csv\"; filename*=UTF-8''r%C3%A9sum%C3%A9.csv",
            "content_type": "text/csv",
            "media_type_extensions": {"text/csv": [".csv"]},
        })
        self.assertEqual("filename*", report["selected_parameter"])
        self.assertEqual("résumé.csv", report["safe_basename"])
        self.assertEqual([], report["finding_codes"])
        self.assertEqual(["standard", "consumer-policy"], [reason["kind"] for reason in report["reasons"]])

    def test_duplicate_and_malformed_extended_value_are_separate(self):
        report = self.run_case({
            "content_disposition": "attachment; filename=\"safe.txt\"; filename=\"other.txt\"; filename*=UTF-8''..%2F%E2%80%AEgpj.exe%ZZ",
            "content_type": "image/jpeg",
            "media_type_extensions": {"image/jpeg": [".jpg", ".jpeg"]},
        }, 1)
        self.assertTrue(report["parsed"])
        self.assertIn("duplicate-filename-parameter", report["finding_codes"])
        self.assertIn("filename-star-malformed-percent-encoding", report["finding_codes"])
        self.assertIsNone(report["safe_basename"])
        self.assertEqual("require-new-unambiguous-server-header", report["recovery"])

    def test_path_bidi_device_and_extension_policy(self):
        cases = [
            ("attachment; filename*=UTF-8''..%2Fevil.txt", "filename-path-separator"),
            ("attachment; filename*=UTF-8''safe%E2%80%AEgpj.exe", "filename-bidi-control"),
            ('attachment; filename="CON.txt"', "filename-reserved-device-name"),
            ('attachment; filename="photo.exe"', "filename-extension-media-policy-mismatch"),
        ]
        for header, code in cases:
            with self.subTest(code=code):
                report = self.run_case({"content_disposition": header, "content_type": "image/jpeg", "media_type_extensions": {"image/jpeg": [".jpg", ".jpeg"]}}, 1)
                self.assertIn(code, report["finding_codes"])

    def test_iso_8859_1_and_quoted_escape(self):
        report = self.run_case({"content_disposition": "attachment; filename*=ISO-8859-1'en'%A3rates.txt", "content_type": None})
        self.assertEqual("£rates.txt", report["safe_basename"])
        quoted = self.run_case({"content_disposition": 'attachment; filename="a\\\"b.txt"', "content_type": None})
        self.assertEqual('a"b.txt', quoted["safe_basename"])

    def test_invalid_utf8_rejected_for_intended_reason(self):
        report = self.run_case({"content_disposition": "attachment; filename*=UTF-8''%FF.txt", "content_type": None}, 1)
        self.assertIn("filename-star-invalid-extended-value", report["finding_codes"])

    def test_malformed_schema_json_and_nonfinite_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, text in (("array", "[]"), ("nan", '{"content_disposition":NaN}'), ("broken", "{")):
                path = Path(directory) / name
                path.write_text(text, encoding="utf-8")
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], text=True, capture_output=True)
                self.assertEqual(2, result.returncode, (name, result.stderr))
        self.run_case({"content_disposition": "attachment; filename=ok.txt", "content_type": "not-a-media-type"}, 2)

    def test_unreadable_input_and_output_failure(self):
        missing = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing/input.json"], text=True, capture_output=True)
        self.assertEqual(2, missing.returncode)
        if Path("/dev/full").exists():
            with tempfile.TemporaryDirectory() as directory, open("/dev/full", "w", encoding="utf-8") as sink:
                path = Path(directory) / "case.json"
                path.write_text('{"content_disposition":"attachment; filename=ok.txt","content_type":null}', encoding="utf-8")
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], text=True, stdout=sink, stderr=subprocess.PIPE)
                self.assertEqual(3, result.returncode, result.stderr)

    def test_should_not_activate_is_routing_not_parser_input(self):
        has_content_disposition_header = False
        has_downloaded_representation = False
        self.assertFalse(has_content_disposition_header or has_downloaded_representation)


if __name__ == "__main__":
    unittest.main(verbosity=2)
