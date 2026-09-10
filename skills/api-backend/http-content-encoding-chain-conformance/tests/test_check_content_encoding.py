import base64
import contextlib
import gzip
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_content_encoding.py"
SPEC = importlib.util.spec_from_file_location("checker", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load checker module")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def encoded(data: bytes, chain: list[str]) -> bytes:
    current = data
    for coding in chain:
        current = gzip.compress(current, mtime=0) if coding == "gzip" else zlib.compress(current)
    return current


class AnalyzeTests(unittest.TestCase):
    def fixture(self, chain, body=b"payload", lines=None, policy=None):
        wire = encoded(body, chain)
        return {
            "field_lines": lines if lines is not None else [", ".join(chain)],
            "body_base64": base64.b64encode(wire).decode(),
            "policy": policy or {"max_chain": 4, "max_encoded_bytes": 1000, "max_output_bytes": 1000, "max_expansion_ratio": 1000},
        }

    def test_repeated_lines_and_inverse_order(self):
        report, code = checker.analyze(self.fixture(["gzip", "deflate"], lines=["gzip", " deflate "]))
        self.assertEqual((code, report["status"]), (0, "decoded"))
        self.assertEqual([x["coding"] for x in report["transitions"]], ["deflate", "gzip"])

    def test_repeated_gzip(self):
        report, code = checker.analyze(self.fixture(["gzip", "gzip"]))
        self.assertEqual(code, 0)
        self.assertEqual(report["decoded_bytes"], 7)

    def test_exact_chain_cap_passes(self):
        report, code = checker.analyze(self.fixture(["gzip", "gzip"], policy={"max_chain": 2, "max_encoded_bytes": 1000, "max_output_bytes": 1000, "max_expansion_ratio": 1000}))
        self.assertEqual(code, 0)

    def test_chain_cap_plus_one_rejects_before_decode(self):
        doc = self.fixture(["gzip", "gzip", "gzip"], policy={"max_chain": 2})
        report, code = checker.analyze(doc)
        self.assertEqual((code, report["reason"], report["transitions"]), (2, "chain_limit_exceeded", []))

    def test_unknown_rejects_before_partial_decode(self):
        report, code = checker.analyze({"field_lines": ["gzip, x-unknown", "deflate"], "policy": {"max_chain": 3}})
        self.assertEqual((code, report["reason"], report["transitions"]), (2, "unsupported_coding", []))

    def test_empty_member_rejected(self):
        report, code = checker.analyze({"field_lines": ["gzip,,deflate"]})
        self.assertEqual((code, report["reason"]), (2, "empty_coding"))

    def test_identity_rejected(self):
        report, code = checker.analyze({"field_lines": ["identity"]})
        self.assertEqual((code, report["reason"]), (2, "identity_not_allowed"))

    def test_wrong_field_shape_rejected(self):
        report, code = checker.analyze({"field_lines": "gzip"})
        self.assertEqual((code, report["reason"]), (2, "invalid_field_lines"))

    def test_output_cap_exact_passes(self):
        report, code = checker.analyze(self.fixture(["gzip"], body=b"1234567", policy={"max_output_bytes": 7, "max_encoded_bytes": 1000, "max_chain": 1, "max_expansion_ratio": 1000}))
        self.assertEqual(code, 0)

    def test_output_cap_plus_one_fails(self):
        report, code = checker.analyze(self.fixture(["gzip"], body=b"12345678", policy={"max_output_bytes": 7, "max_encoded_bytes": 1000, "max_chain": 1, "max_expansion_ratio": 1000}))
        self.assertEqual((code, report["reason"]), (2, "output_limit_exceeded"))

    def test_truncated_stream_fails(self):
        doc = self.fixture(["gzip"])
        raw = base64.b64decode(doc["body_base64"])
        doc["body_base64"] = base64.b64encode(raw[:-4]).decode()
        report, code = checker.analyze(doc)
        self.assertEqual((code, report["reason"]), (2, "truncated_stream"))

    def test_trailing_member_fails(self):
        doc = self.fixture(["gzip"])
        doc["body_base64"] = base64.b64encode(base64.b64decode(doc["body_base64"]) + b"junk").decode()
        report, code = checker.analyze(doc)
        self.assertEqual((code, report["reason"]), (2, "trailing_data"))

    def test_ratio_cap_fails(self):
        report, code = checker.analyze(self.fixture(["gzip"], body=b"0" * 1000, policy={"max_output_bytes": 2000, "max_encoded_bytes": 1000, "max_chain": 1, "max_expansion_ratio": 2}))
        self.assertEqual((code, report["reason"]), (2, "expansion_ratio_exceeded"))

    def test_transfer_encoding_is_not_applicable(self):
        report, code = checker.analyze({"field_lines": [], "transfer_encoding": "chunked"})
        self.assertEqual((code, report["status"], report["conceptual_layer"]), (0, "not_applicable", "transfer-coding/message-framing"))

    def test_nonfinite_policy_rejected(self):
        report, code = checker.analyze({"field_lines": [], "policy": {"max_expansion_ratio": float("nan")}})
        self.assertEqual((code, report["reason"]), (2, "invalid_policy"))

    def test_cli_malformed_json_and_nan_fail_closed(self):
        for raw in ("{bad", '{"field_lines":[],"policy":{"max_expansion_ratio":NaN}}'):
            with self.subTest(raw=raw):
                with tempfile.NamedTemporaryFile("w", delete=False) as handle:
                    handle.write(raw)
                    path = handle.name
                try:
                    proc = subprocess.run([sys.executable, str(SCRIPT), path], capture_output=True, text=True)
                    self.assertEqual(proc.returncode, 2)
                    self.assertEqual(json.loads(proc.stdout)["reason"], "input_error")
                finally:
                    os.unlink(path)

    def test_cli_broken_stdout_returns_three(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            json.dump({"field_lines": []}, handle)
            path = handle.name
        class Broken:
            def write(self, _value):
                raise OSError("closed")
            def flush(self):
                raise OSError("closed")
        try:
            with contextlib.redirect_stdout(Broken()):
                self.assertEqual(checker.main([path]), 3)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
