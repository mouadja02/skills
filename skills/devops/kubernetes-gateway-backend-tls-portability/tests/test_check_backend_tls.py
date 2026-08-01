import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_backend_tls.py"
spec = importlib.util.spec_from_file_location("checker", SCRIPT)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

def valid():
    return {
        "schema_version": 1, "kind": "gateway_backend_tls_audit", "profile": "gateway-api-v1.6.1",
        "inventory": {"controller": "fixture", "controller_version": "1", "gateway_api_version": "v1.6.1", "supported_features": ["BackendTLSPolicy"]},
        "policy": {"namespace": "n", "target_namespace": "n", "target_kind": "Service", "target_name": "echo", "target_exists": True, "target_refs_distinct": True, "ca_source": "ConfigMap", "hostname": "echo.n.svc", "subject_alt_name_types": [], "competing_policy": False, "conditions": {"Accepted": True, "ResolvedRefs": True}},
        "probes": {"valid_ca_hostname": "success", "untrusted_ca": "http_5xx", "mismatched_hostname": "http_5xx", "configmap_rotation": "reconciled"}
    }

class Tests(unittest.TestCase):
    def test_pass(self): self.assertEqual(checker.evaluate(valid())["status"], "pass")
    def test_not_applicable(self): self.assertEqual(checker.evaluate({"kind": "frontend_tls"})["status"], "not_applicable")
    def test_wrong_profile_fails_closed(self):
        d=valid(); d["profile"]="latest"
        with self.assertRaises(checker.InputError): checker.evaluate(d)
    def test_mismatched_inventory_version_fails_closed(self):
        d=valid(); d["inventory"]["gateway_api_version"]="v1.5.0"
        with self.assertRaises(checker.InputError): checker.evaluate(d)
    def test_unknown_key_fails_closed(self):
        d=valid(); d["surprise"]=1
        with self.assertRaises(checker.InputError): checker.evaluate(d)
    def test_strict_boolean(self):
        d=valid(); d["policy"]["target_exists"]=1
        with self.assertRaises(checker.InputError): checker.evaluate(d)
    def test_duplicate_features(self):
        d=valid(); d["inventory"]["supported_features"] *= 2
        with self.assertRaises(checker.InputError): checker.evaluate(d)
    def test_untrusted_and_hostname_failures(self):
        d=valid(); d["probes"]["untrusted_ca"]="success"; d["probes"]["mismatched_hostname"]="success"
        self.assertEqual({x["code"] for x in checker.evaluate(d)["findings"]}, {"UNTRUSTED_CA_ACCEPTED","HOSTNAME_MISMATCH_ACCEPTED"})
    def test_uri_san_requires_feature_and_probes(self):
        d=valid(); d["policy"]["subject_alt_name_types"]=["URI"]; d["probes"].update(uri_san_match="http_5xx",uri_san_mismatch="success")
        codes={x["code"] for x in checker.evaluate(d)["findings"]}
        self.assertTrue({"SAN_FEATURE_UNADVERTISED","URI_SAN_MATCH_FAILED","URI_SAN_MISMATCH_ACCEPTED"} <= codes)
    def test_hostname_san_requires_feature_and_probes(self):
        d=valid(); d["policy"]["subject_alt_name_types"]=["Hostname"]
        codes={x["code"] for x in checker.evaluate(d)["findings"]}
        self.assertTrue({"SAN_FEATURE_UNADVERTISED","HOSTNAME_SAN_MATCH_FAILED","HOSTNAME_SAN_MISMATCH_ACCEPTED"} <= codes)
    def test_attachment_and_precedence(self):
        d=valid(); d["policy"]["target_namespace"]="other"; d["policy"]["competing_policy"]=True
        codes={x["code"] for x in checker.evaluate(d)["findings"]}
        self.assertTrue({"TARGET_ATTACHMENT_INVALID","POLICY_PRECEDENCE_UNRESOLVED"} <= codes)
    def test_nan_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.json"; p.write_text('{"kind":NaN}')
            with self.assertRaises(checker.InputError): checker.load(p)
    def test_malformed_json_exit_two(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.json"; p.write_text('{')
            r=subprocess.run([sys.executable,str(SCRIPT),"--input",str(p)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
    def test_controlled_output_failure(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.json"; p.write_text(json.dumps(valid()))
            r=subprocess.run([sys.executable,str(SCRIPT),"--input",str(p),"--output",td],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)

if __name__ == "__main__": unittest.main()
