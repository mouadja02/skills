#!/usr/bin/env python3
"""Offline tests for inspect_zip_metadata.py."""
from __future__ import annotations

import binascii
import json
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "inspect_zip_metadata.py"
EFS = 1 << 11

def field(kind: int, data: bytes) -> bytes:
    return struct.pack("<HH", kind, len(data)) + data

def unicode_field(kind: int, legacy: bytes, text: str, crc: int | None = None) -> bytes:
    checksum = (binascii.crc32(legacy) & 0xFFFFFFFF) if crc is None else crc
    return field(kind, bytes([1]) + struct.pack("<I", checksum) + text.encode())

def archive(entries: list[dict], archive_comment: bytes = b"") -> bytes:
    locals_blob = bytearray()
    central_blob = bytearray()
    for item in entries:
        local_name = item["local_name"]
        central_name = item.get("central_name", local_name)
        local_extra = item.get("local_extra", b"")
        central_extra = item.get("central_extra", b"")
        comment = item.get("comment", b"")
        local_flags = item.get("local_flags", 0)
        central_flags = item.get("central_flags", local_flags)
        content = item.get("content", b"x")
        crc = binascii.crc32(content) & 0xFFFFFFFF
        offset = len(locals_blob)
        locals_blob += struct.pack("<4s5H3I2H", b"PK\x03\x04", 20, local_flags, 0, 0, 0, crc, len(content), len(content), len(local_name), len(local_extra))
        locals_blob += local_name + local_extra + content
        central_blob += struct.pack("<4s6H3I5H2I", b"PK\x01\x02", 20, 20, central_flags, 0, 0, 0, crc, len(content), len(content), len(central_name), len(central_extra), len(comment), 0, 0, 0, offset)
        central_blob += central_name + central_extra + comment
    eocd = struct.pack("<4s4H2IH", b"PK\x05\x06", 0, 0, len(entries), len(entries), len(central_blob), len(locals_blob), len(archive_comment))
    return bytes(locals_blob + central_blob + eocd + archive_comment)

class InspectorTests(unittest.TestCase):
    def run_archive(self, data: bytes) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.zip"
            path.write_bytes(data)
            result = subprocess.run([str(SCRIPT), str(path)], capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            return result.returncode, json.loads(result.stdout)

    def test_efs_utf8_safe_control(self) -> None:
        name = "café.txt".encode()
        code, report = self.run_archive(archive([{"local_name": name, "local_flags": EFS}]))
        self.assertEqual(code, 0)
        self.assertEqual(report["entries"][0]["decoded_name"], "café.txt")
        self.assertEqual(report["findings"], [])
        self.assertTrue(report["safe_to_extract"])

    def test_independent_difficult_findings(self) -> None:
        local = b"caf\x82.txt"
        central = b"bad\xff.txt"
        stale = unicode_field(0x7075, central, "safe.txt", crc=0)
        code, report = self.run_archive(archive([{"local_name": local, "central_name": central, "local_flags": 0, "central_flags": EFS, "central_extra": stale, "comment": b"\xff"}]))
        self.assertEqual(code, 1)
        codes = {item["code"] for item in report["findings"]}
        self.assertTrue({"local-central-name-mismatch", "efs-flag-mismatch", "invalid-utf8-central-name", "invalid-utf8-central-comment", "unicode-path-crc-mismatch"}.issubset(codes))
        self.assertFalse(report["safe_to_extract"])

    def test_valid_unicode_extras_and_cp437_baseline(self) -> None:
        name = b"caf\x82.txt"
        comment = b"gr\x81n"
        extras = unicode_field(0x7075, name, "café.txt") + unicode_field(0x6375, comment, "grün")
        code, report = self.run_archive(archive([{"local_name": name, "central_extra": extras, "comment": comment}]))
        self.assertEqual(code, 0)
        self.assertEqual(report["entries"][0]["decoded_name"], "café.txt")
        self.assertEqual(report["entries"][0]["decoded_comment"], "grün")

    def test_disagreeing_local_and_central_unicode_paths_fail(self) -> None:
        name = b"legacy.txt"
        code, report = self.run_archive(archive([{
            "local_name": name,
            "local_extra": unicode_field(0x7075, name, "one.txt"),
            "central_extra": unicode_field(0x7075, name, "two.txt"),
        }]))
        self.assertEqual(code, 1)
        self.assertIn("local-central-unicode-path-mismatch", {item["code"] for item in report["findings"]})

    def test_eocd_signature_inside_archive_comment_is_not_misidentified(self) -> None:
        code, report = self.run_archive(archive([{"local_name": b"x"}], archive_comment=b"note PK\x05\x06 tail"))
        self.assertEqual(code, 0)
        self.assertEqual(len(report["entries"]), 1)

    def test_duplicate_extra_and_unsafe_path_fail_closed(self) -> None:
        name = b"../x"
        duplicate = unicode_field(0x7075, name, "../x") * 2
        code, report = self.run_archive(archive([{"local_name": name, "central_extra": duplicate}]))
        self.assertEqual(code, 1)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("duplicate-unicode-path-field", codes)
        self.assertIn("unsafe-decoded-path", codes)

    def test_malformed_extra_is_not_an_expected_invalid_parse_failure(self) -> None:
        bad = struct.pack("<HH", 0x7075, 100) + b"x"
        code, report = self.run_archive(archive([{"local_name": b"x", "central_extra": bad}]))
        self.assertEqual(code, 1)
        self.assertIn("malformed-extra-field", {item["code"] for item in report["findings"]})

    def test_non_zip_and_missing_input_are_input_failures(self) -> None:
        code, report = self.run_archive(b"not a zip")
        self.assertEqual(code, 2)
        self.assertFalse(report["applicable"])
        result = subprocess.run([str(SCRIPT), "/definitely/missing/archive.zip"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["applicable"])

    @unittest.skipUnless(Path("/dev/full").exists(), "requires POSIX /dev/full")
    def test_report_write_failure_uses_exit_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.zip"
            path.write_bytes(archive([{"local_name": b"x"}]))
            result = subprocess.run([str(SCRIPT), str(path), "--output", "/dev/full"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            self.assertIn("cannot write report", result.stderr)

if __name__ == "__main__":
    unittest.main(verbosity=2)
