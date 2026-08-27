#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inspect_scoped_ipv6.py"
spec = importlib.util.spec_from_file_location("inspect_scoped_ipv6", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class InspectorTests(unittest.TestCase):
    def inspect(self, mode, value, known=None):
        record = {"id": "case", "mode": mode, "input": value}
        if known is not None:
            record["known_zones"] = known
        return mod.inspect_record(record, 64)

    def test_current_ui_form_and_known_zone(self):
        result = self.inspect("ui", "fe80::1%eth0", ["eth0"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["address"], "fe80::1")
        self.assertEqual(result["zone"], "eth0")
        self.assertIn("local_only_zone", [x["code"] for x in result["findings"]])

    def test_obsolete_uri_extension_is_observation_not_portability_claim(self):
        result = self.inspect("uri", "http://[fe80::1%25eth0]:8080/status")
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["port"], 8080)
        self.assertIn("obsolete_uri_extension", [x["code"] for x in result["findings"]])

    def test_double_encoding_is_not_recursively_decoded(self):
        result = self.inspect("uri", "http://[fe80::1%2525eth0]/")
        self.assertEqual(result["zone"], "25eth0")
        self.assertIn("possible_double_encoding", [x["code"] for x in result["findings"]])

    def test_injected_suffix_fails(self):
        result = self.inspect("uri", "http://[fe80::1%25]evil.example]/")
        self.assertEqual(result["status"], "error")
        self.assertIn("unexpected text", result["findings"][0]["detail"])

    def test_empty_and_control_zones_fail(self):
        self.assertEqual(self.inspect("ui", "fe80::1%")["status"], "error")
        control = self.inspect("ui", "fe80::1%eth0\x00x")
        self.assertEqual(control["status"], "error")
        self.assertIn("control", control["findings"][0]["detail"])

    def test_bracket_port_and_numeric_multicast_zone(self):
        result = self.inspect("socket", "[ff02::1%3]:5353", ["3"])
        self.assertEqual((result["status"], result["port"], result["zone"]), ("ok", 5353, "3"))

    def test_global_no_zone_should_not_activate(self):
        result = self.inspect("uri", "https://[2001:db8::42]/api")
        self.assertEqual(result["status"], "not_applicable")
        self.assertIn("no_scoped_zone", [x["code"] for x in result["findings"]])

    def test_zone_on_unscoped_address_fails(self):
        result = self.inspect("ui", "2001:db8::1%eth0")
        self.assertEqual(result["status"], "error")
        self.assertIn("zone_on_unscoped_address", [x["code"] for x in result["findings"]])

    def run_cli(self, raw: bytes):
        with tempfile.NamedTemporaryFile(suffix=".txt") as fixture:
            fixture.write(raw); fixture.flush()
            return subprocess.run([sys.executable, str(SCRIPT), fixture.name], capture_output=True, text=True, check=False)

    def test_cli_malformed_and_nonstandard_json_fail_closed(self):
        malformed = self.run_cli(b'{"records":')
        self.assertEqual(malformed.returncode, 2)
        nan = self.run_cli(b'{"records": [], "max_zone_length": NaN}')
        self.assertEqual(nan.returncode, 2)

    def test_cli_schema_and_duplicate_ids_fail_closed(self):
        wrong = self.run_cli(json.dumps({"records": {}}).encode())
        self.assertEqual(wrong.returncode, 2)
        duplicate = self.run_cli(json.dumps({"records": [
            {"id": "x", "mode": "ui", "input": "fe80::1%1"},
            {"id": "x", "mode": "ui", "input": "fe80::2%1"}
        ]}).encode())
        self.assertEqual(duplicate.returncode, 2)

    def test_cli_expected_invalid_is_parsed_then_rejected(self):
        run = self.run_cli(json.dumps({"records": [{"id": "bad", "mode": "ui", "input": "fe80::1%"}]}).encode())
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)["records"][0]["findings"][0]["code"], "invalid_input")

    @unittest.skipUnless(Path("/dev/full").exists(), "requires /dev/full")
    def test_broken_stdout_exit_code(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as fixture:
            json.dump({"records": []}, fixture); fixture.flush()
            with open("/dev/full", "wb") as sink:
                run = subprocess.run([sys.executable, str(SCRIPT), fixture.name], stdout=sink, stderr=subprocess.PIPE, check=False)
        self.assertEqual(run.returncode, 3)


if __name__ == "__main__":
    unittest.main()
