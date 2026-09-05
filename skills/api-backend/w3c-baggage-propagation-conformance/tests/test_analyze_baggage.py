import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_baggage.py"
SPEC = importlib.util.spec_from_file_location("analyze_baggage", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class BaggageTests(unittest.TestCase):
    def analyze(self, fields, **extra):
        return MOD.analyze({"kind": "w3c_baggage_trace", "received_fields": fields, **extra})

    def test_combines_repeated_fields_and_decodes(self):
        result = self.analyze(["userId=alice", "serverNode=DF%2028,isProduction=false"],
                              forwarded_fields=["userId=alice,serverNode=DF%2028,isProduction=false"])
        self.assertEqual("ready", result["classification"])
        self.assertEqual(["alice", "DF 28", "false"], [m["decoded_value"] for m in result["members"]])

    def test_equal_sign_is_value_after_decoding(self):
        result = self.analyze(["route=version%3Dv2"])
        self.assertEqual("version=v2", result["members"][0]["decoded_value"])

    def test_literal_percent_is_invalid(self):
        result = self.analyze(["bad=%ZZ"])
        self.assertEqual("blocked", result["classification"])
        self.assertEqual("percent_sign_not_encoded", result["findings"][0]["reason"])

    def test_invalid_utf8_is_replaced(self):
        result = self.analyze(["name=%FF"])
        self.assertEqual("�", result["members"][0]["decoded_value"])

    def test_properties_validated_but_preserved_opaque(self):
        result = self.analyze(["route=v;vendor = raw%20value;flag"])
        props = result["members"][0]["properties"]
        self.assertEqual([{"key": "vendor", "raw_value": "raw%20value"}, {"key": "flag", "raw_value": None}], props)

    def test_limits_are_combined_and_independent(self):
        at_members = self.analyze([",".join(f"k{i}=v" for i in range(64))])["observations"][0]
        over_members = self.analyze([",".join(f"k{i}=v" for i in range(65))])["observations"][0]
        at_bytes = self.analyze(["a=" + "x" * 8190])["observations"][0]
        over_bytes = self.analyze(["a=" + "x" * 8191])["observations"][0]
        self.assertTrue(at_members["within_64_members"])
        self.assertFalse(over_members["within_64_members"])
        self.assertTrue(over_members["within_8192_bytes"])
        self.assertTrue(at_bytes["within_8192_bytes"])
        self.assertFalse(over_bytes["within_8192_bytes"])

    def test_loss_under_limits_requires_declared_mutation(self):
        blocked = self.analyze(["a=1,b=2"], forwarded_fields=["a=1"])
        ready = self.analyze(["a=1,b=2"], forwarded_fields=["a=1"], declared_mutated_indexes=[1])
        self.assertEqual("blocked", blocked["classification"])
        self.assertEqual("ready", ready["classification"])

    def test_duplicate_order_is_preserved(self):
        result = self.analyze(["a=1,a=2"])
        self.assertEqual(["1", "2"], [m["decoded_value"] for m in result["members"]])

    def test_not_applicable(self):
        self.assertEqual("not_applicable", MOD.analyze({"kind": "traceparent"})["classification"])

    def test_schema_and_nonfinite_json_fail_closed(self):
        with self.assertRaises(MOD.InputError):
            MOD.analyze({"kind": "w3c_baggage_trace", "received_fields": "a=1"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"kind":"w3c_baggage_trace","received_fields":NaN}')
            proc = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(2, proc.returncode)

    def test_missing_file_fails_closed(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing.json"], capture_output=True, text=True)
        self.assertEqual(2, proc.returncode)

    def test_broken_stdout_has_input_failure_code(self):
        with mock.patch.object(sys, "stdout", io.StringIO()) as stream:
            stream.flush = mock.Mock(side_effect=OSError("closed"))
            self.assertEqual(2, MOD.main([str(ROOT / "tests" / "fixtures" / "valid.json")]))


if __name__ == "__main__":
    unittest.main()