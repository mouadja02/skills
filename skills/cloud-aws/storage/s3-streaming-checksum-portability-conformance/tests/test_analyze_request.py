import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_request.py"
FIXTURES = ROOT / "tests" / "fixtures"
spec = importlib.util.spec_from_file_location("analyze_request", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load analyzer module")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AnalyzerTests(unittest.TestCase):
    def run_cli(self, fixture, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(fixture), *map(str, args)],
            text=True,
            capture_output=True,
            timeout=10,
            cwd=ROOT,
        )

    def test_signed_trailer_normal(self):
        proc = self.run_cli(FIXTURES / "signed-trailer.json.txt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report["mode"], "signed-payload-trailer")
        self.assertEqual(report["status"], "pass")
        self.assertIn("aws-chunked", report["observations"])
        self.assertIn("checksum-trailer", report["observations"])
        self.assertEqual(report["violations"], [])

    def test_contradictory_upload_part_fails_closed(self):
        proc = self.run_cli(FIXTURES / "contradictory-upload-part.json.txt")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report["mode"], "ambiguous")
        self.assertIn("multipart-operation", report["observations"])
        self.assertIn("contradictory-streaming-evidence", report["violations"])
        self.assertIn("Block rollout", report["next_action"])

    def test_get_object_not_applicable(self):
        proc = self.run_cli(FIXTURES / "get-object.json.txt")
        self.assertEqual(proc.returncode, 2)
        report = json.loads(proc.stdout)
        self.assertFalse(report["applicable"])
        self.assertEqual(report["mode"], "not-applicable")

    def test_all_supported_modes(self):
        base = json.loads((FIXTURES / "signed-trailer.json.txt").read_text())
        cases = [
            ("STREAMING-UNSIGNED-PAYLOAD-TRAILER", "aws-chunked", "x-amz-checksum-sha256", "unsigned-payload-trailer"),
            ("STREAMING-AWS4-HMAC-SHA256-PAYLOAD", "aws-chunked", None, "signed-streaming-payload"),
            ("UNSIGNED-PAYLOAD", None, None, "unsigned-payload"),
            ("a" * 64, None, None, "fixed-payload-hash"),
        ]
        for token, encoding, trailer, expected in cases:
            with self.subTest(expected=expected):
                data = dict(base, x_amz_content_sha256=token, content_encoding=encoding, x_amz_trailer=trailer)
                report, code = mod.analyze(data)
                self.assertEqual(code, 0)
                self.assertEqual(report["mode"], expected)

    def test_integrity_unknown_blocks(self):
        data = json.loads((FIXTURES / "signed-trailer.json.txt").read_text())
        data["download_sha256_matches"] = None
        report, code = mod.analyze(data)
        self.assertEqual(code, 1)
        self.assertIn("download-integrity-unverified", report["violations"])

    def test_schema_and_non_finite_fail_closed(self):
        bad = [
            "[]",
            '{"operation":"PutObject"}',
            (FIXTURES / "signed-trailer.json.txt").read_text().replace('"operation"', '"extra":1,"operation"', 1),
            (FIXTURES / "signed-trailer.json.txt").read_text().replace('true', 'NaN', 1),
            (FIXTURES / "signed-trailer.json.txt").read_text().replace('true', 'Infinity', 1),
            (FIXTURES / "signed-trailer.json.txt").read_text().replace('"operation"', '"operation":"PutObject","operation"', 1),
        ]
        with tempfile.TemporaryDirectory() as td:
            for index, raw in enumerate(bad):
                path = Path(td) / f"bad-{index}.txt"
                path.write_text(raw)
                proc = self.run_cli(path)
                self.assertEqual(proc.returncode, 2, (index, proc.stdout, proc.stderr))
                self.assertEqual(proc.stdout, "")

    def test_wrong_boolean_type_rejected(self):
        data = json.loads((FIXTURES / "signed-trailer.json.txt").read_text())
        data["content_length_known"] = 1
        with self.assertRaises(mod.InputError):
            mod.analyze(data)

    def test_unknown_trailer_name_blocks(self):
        data = json.loads((FIXTURES / "signed-trailer.json.txt").read_text())
        data["x_amz_trailer"] = "x-amz-meta-not-a-checksum"
        report, code = mod.analyze(data)
        self.assertEqual(code, 1)
        self.assertEqual(report["mode"], "ambiguous")
        self.assertIn("unknown-checksum-trailer", report["violations"])

    def test_atomic_output_and_write_failure(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.json"
            proc = self.run_cli(FIXTURES / "signed-trailer.json.txt", "--output", out)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(out.read_text())["status"], "pass")
            old = out.read_text()
            with mock.patch.object(mod.os, "replace", side_effect=OSError("controlled")):
                with self.assertRaises(OSError):
                    mod.write_atomic(out, "replacement")
            self.assertEqual(out.read_text(), old)

    def test_missing_input_and_bad_output_parent(self):
        proc = self.run_cli(ROOT / "missing.json")
        self.assertEqual(proc.returncode, 2)
        proc = self.run_cli(FIXTURES / "signed-trailer.json.txt", "--output", ROOT / "missing" / "x.json")
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
