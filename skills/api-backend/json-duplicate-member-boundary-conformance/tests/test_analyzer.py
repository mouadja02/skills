#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_json_duplicates.py"
spec = importlib.util.spec_from_file_location("analyzer", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

class AnalyzerTests(unittest.TestCase):
    def check(self, text, control, count=0):
        out = mod.analyze_bytes(text if isinstance(text, bytes) else text.encode())
        self.assertEqual(control, out["control"])
        self.assertEqual(count, out["duplicate_count"])
        return out

    def test_unique_ready(self): self.check('{"a":1,"b":[true,null]}', "ready")
    def test_direct_duplicate(self): self.check('{"a":1,"a":2}', "blocked", 1)
    def test_escaped_equivalent(self):
        out = self.check('{"a":1,"\\u0061":2}', "blocked", 1)
        self.assertEqual("/a", out["duplicates"][0]["member_path"])
        self.assertEqual([1, 2], out["duplicates"][0]["parser_policy_projection"]["preserve_all"])
    def test_scopes_and_arrays(self): self.check('[{"a":1},{"a":2},1,1]', "ready")
    def test_nested_pointer_and_offsets(self):
        out = self.check('{"x":{"a":1,"a":2}}', "blocked", 1)
        self.assertEqual("/x", out["duplicates"][0]["object_path"])
        self.assertEqual(2, len(out["duplicates"][0]["occurrence_byte_offsets"]))
    def test_pointer_escaping(self):
        out = self.check('{"x":{"a/b~":1,"a\\u002fb~":2}}', "blocked", 1)
        self.assertEqual("/x/a~1b~0", out["duplicates"][0]["member_path"])
    def test_three_occurrences(self):
        out = self.check('{"a":1,"a":2,"a":3}', "blocked", 1)
        self.assertEqual(3, out["duplicates"][0]["parser_policy_projection"]["last_wins"])
    def test_interleaved_duplicates_and_utf8_byte_offsets(self):
        out = self.check('{"é":0,"a":1,"b":1,"a":2,"b":2,"a":3}', "blocked", 2)
        by_name = {finding["decoded_name"]: finding for finding in out["duplicates"]}
        self.assertEqual(3, by_name["a"]["parser_policy_projection"]["last_wins"])
        self.assertGreater(by_name["a"]["occurrence_byte_offsets"][0], by_name["a"]["occurrence_char_offsets"][0])
    def test_malformed_not_expected_duplicate(self):
        out = self.check('{"a":1,', "blocked")
        self.assertFalse(out["valid_json"])
        self.assertEqual("invalid_or_unprovable_json", out["violation"])
    def test_nan_infinity_and_overflow_rejected(self):
        for value in ("NaN", "Infinity", "1e9999"):
            with self.subTest(value=value): self.assertFalse(self.check('{"a":'+value+'}', "blocked")["valid_json"])
    def test_invalid_utf8_and_bom_rejected(self):
        for raw in (b'{"a":"\xff"}', b'\xef\xbb\xbf{}'):
            with self.subTest(raw=raw): self.assertFalse(self.check(raw, "blocked")["valid_json"])
    def test_unpaired_surrogate_rejected(self): self.assertFalse(self.check(b'{"\\ud800":1}', "blocked")["valid_json"])
    def test_limits_fail_closed(self):
        out = mod.analyze_bytes(b'{"a":1}', mod.Limits(max_bytes=2, max_depth=1, max_members=1))
        self.assertEqual("blocked", out["control"])
    def test_cli_exit_codes_and_stdin(self):
        good = subprocess.run([sys.executable, str(SCRIPT), "-"], input=b'{"a":1}', capture_output=True, check=False)
        bad = subprocess.run([sys.executable, str(SCRIPT), "-"], input=b'{"a":1,"a":2}', capture_output=True, check=False)
        self.assertEqual(0, good.returncode); self.assertEqual(2, bad.returncode)
        self.assertEqual("blocked", json.loads(bad.stdout)["control"])
    def test_unreadable_file_fails_closed(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing.json"], capture_output=True, check=False)
        self.assertEqual(3, run.returncode)
    def test_controlled_output_failure(self):
        class Broken:
            def write(self, _): raise OSError("controlled")
        with self.assertRaises(OSError): mod.write_report({"control":"ready"}, Broken())

if __name__ == "__main__": unittest.main(verbosity=2)
