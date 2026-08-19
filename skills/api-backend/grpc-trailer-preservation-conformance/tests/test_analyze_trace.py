import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("analyzer", ROOT / "scripts" / "analyze_trace.py")
assert SPEC is not None and SPEC.loader is not None
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def observation(hop="origin", **updates):
    value = {
        "hop": hop,
        "http_version": "h2",
        "initial_headers": {"content-type": ["application/grpc"]},
        "messages": 1,
        "trailers_only": False,
        "trailers": {"grpc-status": ["0"], "x-test": ["redacted"]},
        "end_stream": True,
    }
    value.update(updates)
    return value


def document(observations=None, *, messages=1, trailers_only=False, status="0"):
    trailers = {"grpc-status": [status], "x-test": ["redacted"]}
    return {"version": 1, "cases": [{"id": "case", "expected": {
        "grpc_status": status, "messages": messages, "trailers_only": trailers_only, "trailers": trailers,
    }, "observations": observations or [observation()]}]}


class AnalyzeTests(unittest.TestCase):
    def test_preserves_across_hops(self):
        result = A.analyze(document([observation("origin"), observation("proxy"), observation("client")]))
        self.assertEqual("PASS", result["status"])
        self.assertIsNone(result["cases"][0]["first_divergent_hop"])

    def test_localizes_first_loss(self):
        result = A.analyze(document([observation("origin"), observation("proxy", trailers={}), observation("client", trailers={})]))
        self.assertEqual("proxy", result["cases"][0]["first_divergent_hop"])
        self.assertEqual("LOSS", result["cases"][0]["observations"][1]["classification"])

    def test_trailers_only_error(self):
        trailers = {"grpc-status": ["5"], "x-test": ["redacted"]}
        obs = observation(messages=0, trailers_only=True, trailers=trailers)
        self.assertEqual("PASS", A.analyze(document([obs], messages=0, trailers_only=True, status="5"))["status"])

    def test_zero_message_success(self):
        obs = observation(messages=0)
        self.assertEqual("PASS", A.analyze(document([obs], messages=0))["status"])

    def test_evidenced_limit_is_not_silent_loss(self):
        obs = observation(trailers={}, end_stream=False, declared_limit=True, limit_evidence=True,
                          configured_trailer_limit_bytes=4096, rejection_signature="response_headers_too_large")
        row = A.analyze(document([obs]))["cases"][0]["observations"][0]
        self.assertEqual("DECLARED_LIMIT", row["classification"])

    def test_claimed_limit_without_evidence_is_loss(self):
        obs = observation(trailers={}, declared_limit=True, limit_evidence=False,
                          configured_trailer_limit_bytes=4096, rejection_signature="reset")
        row = A.analyze(document([obs]))["cases"][0]["observations"][0]
        self.assertEqual("LOSS", row["classification"])

    def test_status_in_initial_headers_is_loss(self):
        obs = observation(initial_headers={"grpc-status": ["0"]})
        self.assertEqual("LOSS", A.analyze(document([obs]))["cases"][0]["observations"][0]["classification"])

    def test_translation_leg_is_not_silently_compared(self):
        obs = observation(http_version="http/1.1")
        self.assertEqual("OTHER_FAILURE", A.analyze(document([obs]))["cases"][0]["observations"][0]["classification"])

    def test_duplicate_json_member_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.txt"
            path.write_text('{"version":1,"version":1,"cases":[]}', encoding="utf-8")
            with self.assertRaises(A.InputError):
                A.load_json(path)

    def test_nan_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.txt"
            path.write_text('{"version":1,"cases":NaN}', encoding="utf-8")
            with self.assertRaises(A.InputError):
                A.load_json(path)

    def test_case_insensitive_duplicate_field_rejected(self):
        obs = observation(trailers={"grpc-status": ["0"], "Grpc-Status": ["0"]})
        with self.assertRaises(A.InputError):
            A.analyze(document([obs]))

    def test_repeated_hop_rejected(self):
        with self.assertRaises(A.InputError):
            A.analyze(document([observation("same"), observation("same")]))

    def test_output_failure_is_fail_closed(self):
        with mock.patch.object(Path, "write_text", side_effect=OSError("denied")):
            with self.assertRaises(A.InputError):
                A.write_result({"status": "PASS"}, "/not-written/result.json")


if __name__ == "__main__":
    unittest.main()
