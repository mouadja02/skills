import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_transcript.py"
SPEC = importlib.util.spec_from_file_location("validate_transcript", SCRIPT)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def stable_exchange(*, chunks=None, disconnected=False, last_event_id=None, exchange_id="call-1"):
    headers = {
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-11-25",
    }
    if last_event_id is not None:
        headers["Last-Event-ID"] = last_event_id
    return {
        "id": exchange_id,
        "request": {
            "method": "POST",
            "headers": headers,
            "body": {"jsonrpc": "2.0", "id": 1, "method": "tools/call"},
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "text/event-stream; charset=utf-8"},
            "chunks": chunks if chunks is not None else ['id: evt-1\ndata: {"jsonrpc":"2.0","id":1,"result":{}}\n\n'],
            "disconnected": disconnected,
        },
    }


def draft_exchange():
    return {
        "id": "draft-call",
        "idempotent": False,
        "request": {
            "method": "POST",
            "headers": {
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2026-07-28",
                "Mcp-Method": "tools/call",
            },
            "body": {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}},
            },
        },
        "response": {
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "chunks": [],
            "disconnected": False,
        },
    }


class ValidateTranscriptTests(unittest.TestCase):
    def test_stable_split_chunks_are_buffered(self):
        exchange = stable_exchange(chunks=[
            "id: evt-1\ndata: {\"jsonrpc\":\"2.0\",\"id\":",
            "1,\"result\":{}}\n\n",
        ])
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertTrue(result["valid"], result)

    def test_stable_disconnect_with_event_id_prescribes_get_not_post_replay(self):
        exchange = stable_exchange(disconnected=True)
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertTrue(result["valid"])
        self.assertEqual(result["recovery"][0]["action"], "resume-with-get")
        self.assertIn("do not replay", result["recovery"][0]["condition"])

    def test_last_event_id_on_post_is_rejected(self):
        exchange = stable_exchange(last_event_id="evt-1")
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertIn("invalid_resume_method", {item["code"] for item in result["findings"]})

    def test_accept_quality_zero_is_rejected(self):
        exchange = stable_exchange()
        exchange["request"]["headers"]["Accept"] = "application/json;q=0, text/event-stream"
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertIn("invalid_post_accept", {item["code"] for item in result["findings"]})

    def test_malformed_accept_quality_is_rejected(self):
        for quality in ("q", "q=1e0", "q=+0.5", "q=0.1234"):
            with self.subTest(quality=quality):
                exchange = stable_exchange()
                exchange["request"]["headers"]["Accept"] = f"application/json;{quality}, text/event-stream"
                result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
                self.assertIn("invalid_post_accept", {item["code"] for item in result["findings"]})

    def test_malformed_jsonrpc_envelope_is_rejected(self):
        invalid_bodies = [
            {"jsonrpc": "2.0"},
            {"jsonrpc": "2.0", "method": "tools/call", "id": [], "params": 42},
            {"jsonrpc": "2.0", "id": 1, "error": "oops"},
            {"jsonrpc": "2.0", "id": True, "result": {}},
        ]
        for body in invalid_bodies:
            with self.subTest(body=body):
                exchange = stable_exchange()
                exchange["request"]["body"] = body
                result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
                self.assertIn("invalid_jsonrpc_body", {item["code"] for item in result["findings"]})

        exchange = stable_exchange()
        exchange["request"]["body"]["id"] = 10**1000
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertNotIn("invalid_jsonrpc_body", {item["code"] for item in result["findings"]})

    def test_draft_happy_path(self):
        result = validator.validate({"profile": "draft-2026-07-28", "exchanges": [draft_exchange()]})
        self.assertTrue(result["valid"], result)
        self.assertTrue(result["draft"])
        self.assertFalse(result["normative"])

    def test_draft_rejects_legacy_session_get_and_event_ids(self):
        exchange = draft_exchange()
        exchange["request"]["method"] = "GET"
        exchange["request"]["headers"] = {
            "Accept": "text/event-stream",
            "Mcp-Session-Id": "redacted",
            "Last-Event-ID": "evt-1",
        }
        exchange["response"] = {
            "status": 200,
            "headers": {"Content-Type": "text/event-stream"},
            "chunks": ['id: evt-2\ndata: {"jsonrpc":"2.0","id":7,"result":{}}\n\n'],
            "disconnected": True,
        }
        result = validator.validate({"profile": "draft-2026-07-28", "exchanges": [exchange]})
        codes = {item["code"] for item in result["findings"]}
        self.assertTrue({"get_removed_in_profile", "session_header_removed", "resumability_removed", "event_id_removed"}.issubset(codes))
        self.assertEqual(result["recovery"][0]["action"], "do-not-replay")

    def test_incomplete_and_invalid_sse_are_rejected_for_intended_reasons(self):
        incomplete = stable_exchange(chunks=['data: {"jsonrpc":"2.0"}'])
        malformed = stable_exchange(chunks=['data: {not-json}\n\n'])
        r1 = validator.validate({"profile": "stable-2025-11-25", "exchanges": [incomplete]})
        r2 = validator.validate({"profile": "stable-2025-11-25", "exchanges": [malformed]})
        self.assertIn("incomplete_sse_event", {item["code"] for item in r1["findings"]})
        self.assertIn("invalid_sse_json", {item["code"] for item in r2["findings"]})

    def test_sse_number_outside_finite_host_range_is_rejected(self):
        exchange = stable_exchange(chunks=['data: {"n":1e999}\n\n'])
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertIn("invalid_sse_json", {item["code"] for item in result["findings"]})

    def test_non_jsonrpc_sse_data_is_rejected(self):
        for chunks in (['data: 42\n\n'], ['data: {}\n\n']):
            with self.subTest(chunks=chunks):
                exchange = stable_exchange(chunks=chunks)
                result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
                self.assertIn("invalid_sse_jsonrpc", {item["code"] for item in result["findings"]})

    def test_empty_event_id_resets_recovery_cursor(self):
        exchange = stable_exchange(
            chunks=['id: old\ndata: {"jsonrpc":"2.0","id":1,"result":{}}\n\nid:\ndata: {}\n\n'],
            disconnected=True,
        )
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertEqual(result["recovery"][0]["action"], "do-not-replay")

    def test_nul_event_id_is_ignored_for_recovery(self):
        exchange = stable_exchange(
            chunks=['id: old\ndata: {"jsonrpc":"2.0","id":1,"result":{}}\n\nid:\nid: unsafe\u0000cursor\ndata: {"jsonrpc":"2.0","id":1,"result":{}}\n\n'],
            disconnected=True,
        )
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertEqual(result["recovery"][0]["action"], "do-not-replay")
        self.assertIn("ignored_sse_id_nul", {item["code"] for item in result["findings"]})

    def test_cross_stream_duplicate_is_rejected(self):
        first = stable_exchange(exchange_id="stream-a")
        second = stable_exchange(exchange_id="stream-b")
        first["concurrent_group"] = "overlap-1"
        second["concurrent_group"] = "overlap-1"
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [first, second]})
        self.assertIn("cross_stream_duplicate", {item["code"] for item in result["findings"]})

    def test_sequential_duplicate_is_not_called_broadcast(self):
        first = stable_exchange(exchange_id="stream-a")
        second = stable_exchange(exchange_id="stream-b")
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [first, second]})
        self.assertNotIn("cross_stream_duplicate", {item["code"] for item in result["findings"]})

    def test_duplicate_notification_is_warning_not_proven_broadcast(self):
        chunks = ['data: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n']
        first = stable_exchange(exchange_id="stream-a", chunks=chunks)
        second = stable_exchange(exchange_id="stream-b", chunks=chunks)
        first["concurrent_group"] = "overlap-1"
        second["concurrent_group"] = "overlap-1"
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [first, second]})
        duplicates = [item for item in result["findings"] if item["code"] == "cross_stream_duplicate"]
        self.assertEqual(duplicates[0]["level"], "warning")
        self.assertTrue(result["valid"])

    def test_unknown_profile_and_malformed_shapes_fail_closed(self):
        self.assertFalse(validator.validate({"profile": "future", "exchanges": []})["valid"])
        self.assertFalse(validator.validate({"profile": [], "exchanges": []})["valid"])
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [None]})
        self.assertIn("invalid_exchange", {item["code"] for item in result["findings"]})

    def test_successful_get_requires_event_stream(self):
        for status in (200, 204):
            with self.subTest(status=status):
                exchange = stable_exchange()
                exchange["request"] = {"method": "GET", "headers": {"Accept": "text/event-stream"}, "body": None}
                exchange["response"] = {"status": status, "headers": {"Content-Type": "application/json"}, "chunks": [], "disconnected": False}
                result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
                self.assertIn("invalid_get_response_content_type", {item["code"] for item in result["findings"]})

        exchange = stable_exchange()
        exchange["request"] = {"method": "GET", "headers": {"Accept": "text/event-stream"}, "body": None}
        exchange["response"] = {"status": 204, "headers": {"Content-Type": "text/event-stream"}, "chunks": [], "disconnected": False}
        result = validator.validate({"profile": "stable-2025-11-25", "exchanges": [exchange]})
        self.assertIn("invalid_get_response_status", {item["code"] for item in result["findings"]})

    def test_nonstandard_json_constants_are_input_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            for index, constant in enumerate(("NaN", "Infinity", "-Infinity")):
                with self.subTest(constant=constant):
                    path = Path(directory) / f"constant-{index}.json"
                    path.write_text(
                        '{"profile":"stable-2025-11-25","exchanges":[],"x":' + constant + "}",
                        encoding="utf-8",
                    )
                    self.assertEqual(validator.main([str(path)]), 2)

    def test_unreadable_and_malformed_files_are_input_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            malformed = Path(directory) / "bad.json"
            malformed.write_text("{", encoding="utf-8")
            self.assertEqual(validator.main([str(missing)]), 2)
            self.assertEqual(validator.main([str(malformed)]), 2)

    def test_controlled_read_failure_is_not_conformance_invalidity(self):
        with mock.patch("pathlib.Path.open", side_effect=PermissionError("denied")):
            self.assertEqual(validator.main(["blocked.json"]), 2)

    def test_json_report_has_no_nonstandard_numbers(self):
        result = validator.validate({"profile": "draft-2026-07-28", "exchanges": [draft_exchange()]})
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("NaN", encoded)
        self.assertFalse(any(isinstance(value, float) and not math.isfinite(value) for value in result.values()))


if __name__ == "__main__":
    unittest.main()
