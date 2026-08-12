import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "preflight.py"
FIXTURES = ROOT / "tests" / "fixtures"
spec = importlib.util.spec_from_file_location("preflight", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load preflight module")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PreflightTests(unittest.TestCase):
    def cli(self, response, expected=FIXTURES / "expected.json", profile="current-id-v1"):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--profile",
                profile,
                str(response),
                str(expected),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )

    def raw(self):
        return (FIXTURES / "response.http").read_bytes()

    def write_raw(self, directory, raw):
        path = Path(directory) / "response.http"
        path.write_bytes(raw)
        return path

    def test_current_id_profile_hydrates_nested_stream_list(self):
        proc = self.cli(FIXTURES / "response.http")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        expected = json.loads((FIXTURES / "expected.json").read_text())
        self.assertEqual(report["merged_data"], expected)
        self.assertEqual(report["profile"], "current-id-v1")
        self.assertEqual(report["parts"], 3)
        self.assertEqual(report["patches"], 3)
        self.assertEqual(report["pending_ids"], ["profile", "team-members"])
        self.assertEqual(report["completed_ids"], ["team-members", "profile"])
        self.assertTrue(report["expected_match"])

    def test_unknown_envelope_key_blocks(self):
        raw = self.raw().replace(
            b'"hasNext":false}',
            b'"hydrationHint":{"mode":"append"},"hasNext":false}',
        )
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("unknown envelope keys", proc.stderr)
        self.assertIn("hydrationHint", proc.stderr)

    def test_profile_is_mandatory(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURES / "response.http"), str(FIXTURES / "expected.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--profile", proc.stderr)

    def test_expected_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            expected = Path(td) / "expected.json"
            expected.write_text('{"viewer":{}}')
            proc = self.cli(FIXTURES / "response.http", expected)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not equal expected", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_graphql_errors_block(self):
        raw = self.raw().replace(
            b'"hasNext":false}',
            b'"errors":[{"message":"upstream failed"}],"hasNext":false}',
        )
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("GraphQL errors", proc.stderr)

    def test_missing_terminal_has_next_false_blocks(self):
        raw = self.raw().replace(b'"hasNext":false}', b'"hasNext":true}')
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("final part", proc.stderr)

    def test_malformed_closing_boundary_blocks(self):
        raw = self.raw().replace(b"--graphql-boundary--\r\n", b"--graphql-boundary\r\n")
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("truncated", proc.stderr)

    def test_wrong_content_length_blocks(self):
        raw = self.raw().replace(
            b'Content-Type: multipart/mixed; boundary="graphql-boundary"; deferSpec=20220824\r\n',
            b'Content-Type: multipart/mixed; boundary="graphql-boundary"; deferSpec=20220824\r\nContent-Length: 1\r\n',
        )
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Content-Length", proc.stderr)

    def test_chunked_http_capture_is_supported(self):
        raw = self.raw()
        split = raw.index(b"\r\n\r\n")
        headers, body = raw[:split], raw[split + 4:]
        middle = len(body) // 2
        chunked = (
            f"{middle:x}\r\n".encode() + body[:middle] + b"\r\n"
            + f"{len(body) - middle:x}\r\n".encode() + body[middle:] + b"\r\n0\r\n\r\n"
        )
        capture = headers + b"\r\nTransfer-Encoding: chunked\r\n\r\n" + chunked
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, capture))
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_duplicate_json_key_and_nonfinite_number_block(self):
        cases = [
            (b'"hasNext":true}', b'"hasNext":true,"hasNext":true}'),
            (b'"id":"u-1"', b'"id":NaN'),
        ]
        for old, new in cases:
            with self.subTest(new=new):
                with tempfile.TemporaryDirectory() as td:
                    proc = self.cli(self.write_raw(td, self.raw().replace(old, new, 1)))
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(proc.stdout, "")

    def test_stream_patch_blocks_as_out_of_scope(self):
        raw = self.raw()
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw), profile="legacy-path-2022")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid choice", proc.stderr)

    def test_legacy_folded_initial_payload_is_merged(self):
        body = (
            b"--b\r\nContent-Type: application/json\r\n\r\n"
            b'{"data":{"book":{}},"incremental":[{"data":{"title":"Dune"},"path":["book"]}],"hasNext":false}'
            b"\r\n--b--\r\n"
        )
        raw = b'HTTP/1.1 200 OK\r\nContent-Type: multipart/mixed; boundary="b"\r\n\r\n' + body
        with tempfile.TemporaryDirectory() as td:
            response = self.write_raw(td, raw)
            expected = Path(td) / "expected.json"
            expected.write_text('{"book":{"title":"Dune"}}')
            proc = self.cli(response, expected, profile="legacy-path-v0.1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["merged_data"], {"book": {"title": "Dune"}})

    def test_patch_conflict_blocks(self):
        raw = self.raw().replace(
            b'{"data":{"bio":"compiler pioneer"},"id":"profile"}',
            b'{"data":{"location":"Paris"},"id":"profile"}',
        )
        with tempfile.TemporaryDirectory() as td:
            proc = self.cli(self.write_raw(td, raw))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("conflicts", proc.stderr)


if __name__ == "__main__":
    unittest.main()
