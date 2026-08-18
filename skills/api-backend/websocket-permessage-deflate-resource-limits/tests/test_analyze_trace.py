#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_trace.py"
spec = importlib.util.spec_from_file_location("analyze_trace", SCRIPT)
assert spec is not None
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def b64(parts: list[bytes]) -> list[str]:
    return [base64.b64encode(part).decode("ascii") for part in parts]


def compress_messages(payloads: list[bytes], takeover: bool) -> list[bytes]:
    compressor = None
    output = []
    for payload in payloads:
        if compressor is None or not takeover:
            compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        encoded = compressor.compress(payload) + compressor.flush(zlib.Z_SYNC_FLUSH)
        assert encoded.endswith(module.TAIL)
        output.append(encoded[:-4])
        if not takeover:
            compressor = None
    return output


def trace(encoded: list[bytes], *, takeover: bool = False, output_limit: int = 8192, ratio: int = 1000):
    messages = []
    for index, data in enumerate(encoded):
        cuts = [data[: max(1, len(data) // 3)], data[max(1, len(data) // 3): max(2, 2 * len(data) // 3)], data[max(2, 2 * len(data) // 3):]]
        cuts = [part for part in cuts if part]
        messages.append({"id": f"m{index + 1}", "compressed": True, "fragments": b64(cuts)})
    return {
        "version": 1,
        "permessage_deflate_negotiated": True,
        "context_takeover": "takeover" if takeover else "no_context_takeover",
        "limits": {"compressed_bytes": 4096, "output_bytes": output_limit, "ratio": ratio, "milliseconds": 1000, "fragments": 8},
        "messages": messages,
    }


class AnalyzerTests(unittest.TestCase):
    def test_fragmented_message_is_counted_once_and_accepted(self):
        payload = b"fragmented-safe-payload" * 20
        result = module.analyze(trace(compress_messages([payload], False)))
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["messages"][0]["output_bytes"], len(payload))

    def test_output_limit_aborts_without_delivery(self):
        payload = b"A" * 4096
        result = module.analyze(trace(compress_messages([payload], False), output_limit=2048, ratio=1000))
        finding = result["messages"][0]
        self.assertEqual(finding["reason"], "output_byte_limit")
        self.assertFalse(finding["application_delivered"])
        self.assertEqual(result["connection_state"], "closed")
        self.assertLessEqual(finding["output_bytes"], 2049)

    def test_ratio_limit_is_independent(self):
        payload = b"B" * 2048
        result = module.analyze(trace(compress_messages([payload], False), output_limit=4096, ratio=2))
        self.assertEqual(result["messages"][0]["reason"], "expansion_ratio_limit")

    def test_context_takeover_and_no_takeover_both_work(self):
        payloads = [b"shared-dictionary-value:" * 80, b"shared-dictionary-value:" * 20]
        with_takeover = module.analyze(trace(compress_messages(payloads, True), takeover=True))
        without_takeover = module.analyze(trace(compress_messages(payloads, False), takeover=False))
        self.assertEqual([x["status"] for x in with_takeover["messages"]], ["accepted", "accepted"])
        self.assertEqual([x["status"] for x in without_takeover["messages"]], ["accepted", "accepted"])

    def test_wrong_reset_rejects_context_dependent_second_message(self):
        payloads = [bytes(range(256)) * 8, bytes(range(256)) * 2]
        encoded = compress_messages(payloads, True)
        result = module.analyze(trace(encoded, takeover=False))
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["messages"][-1]["reason"], "invalid_deflate")

    def test_not_negotiated_is_not_applicable(self):
        document = trace(compress_messages([b"small"], False))
        document["permessage_deflate_negotiated"] = False
        result = module.analyze(document)
        self.assertEqual(result["status"], "not_applicable")
        self.assertEqual(result["messages"], [])

    def test_malformed_shapes_and_nonstandard_numbers_fail_closed(self):
        with self.assertRaises(module.InputError):
            module.validate([])
        document = trace(compress_messages([b"small"], False))
        document["limits"]["output_bytes"] = True
        with self.assertRaises(module.InputError):
            module.validate(document)
        with self.assertRaises(module.InputError):
            json.loads('{"x":NaN}', parse_constant=module.reject_constant)

    def test_invalid_base64_and_deflate_are_distinct_failures(self):
        document = trace(compress_messages([b"small"], False))
        document["messages"][0]["fragments"] = ["***"]
        with self.assertRaises(module.InputError):
            module.analyze(document)
        document["messages"][0]["fragments"] = b64([b"not deflate"])
        result = module.analyze(document)
        self.assertEqual(result["messages"][0]["reason"], "invalid_deflate")

    def test_expected_invalid_must_parse_before_protocol_rejection(self):
        document = trace(compress_messages([b"small"], False))
        document["messages"][0]["fragments"] = b64([b"invalid"])
        result = module.analyze(document)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["messages"][0]["reason"], "invalid_deflate")

    def test_cli_write_failure_is_nonzero(self):
        document = trace(compress_messages([b"small"], False))
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "trace.json"
            source.write_text(json.dumps(document), encoding="utf-8")
            cp = subprocess.run([sys.executable, str(SCRIPT), str(source), "--output", directory], capture_output=True, text=True)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("invalid_input", cp.stderr)


if __name__ == "__main__":
    unittest.main()
