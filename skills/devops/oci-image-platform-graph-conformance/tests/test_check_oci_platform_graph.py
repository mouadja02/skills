import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts/check_oci_platform_graph.py"
spec = importlib.util.spec_from_file_location("checker", SCRIPT)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
D = lambda c: "sha256:" + c * 64

def desc(c="a", arch="amd64", variant=None, media=checker.IMAGE_MT):
    p = {"os": "linux", "architecture": arch}
    if variant: p["variant"] = variant
    return {"mediaType": media, "digest": D(c), "size": 10, "platform": p}

def child(arch="amd64", variant=None):
    p = {"os": "linux", "architecture": arch}
    if variant: p["variant"] = variant
    return {"schemaVersion": 2, "config": p}

def audit(manifests=None, children=None, request=None):
    return {"schema_version": 1, "kind": "oci_image_platform_graph_audit", "profile": "oci-image-spec-1.1.1", "matcher": "exact", "request": request or {"os": "linux", "architecture": "amd64"}, "before": {"index": {"schemaVersion": 2, "mediaType": checker.INDEX_MT, "manifests": manifests or [desc()]}, "children": children or {D("a"): child()}}}

class Tests(unittest.TestCase):
    def codes(self, report): return {x["code"] for x in report["findings"]}
    def test_pass(self):
        report, code = checker.analyze(audit()); self.assertEqual(code, 0); self.assertEqual(report["status"], "pass")
    def test_platform_mismatch(self):
        report, code = checker.analyze(audit(children={D("a"): child("arm64", "v8")})); self.assertEqual(code, 1); self.assertIn("PLATFORM_CONFIG_MISMATCH", self.codes(report))
    def test_ambiguous_uses_first(self):
        data = audit([desc("a"), desc("b")], {D("a"): child(), D("b"): child()}); report, _ = checker.analyze(data); self.assertEqual(report["selected_digest"], D("a")); self.assertIn("AMBIGUOUS_PLATFORM_MATCH", self.codes(report))
    def test_graph_removal(self):
        data = audit([desc("a"), desc("b", "arm64", "v8")], {D("a"): child(), D("b"): child("arm64", "v8")}); data["after"] = {"index": {"schemaVersion": 2, "manifests": [desc("a")]}, "children": {D("a"): child()}}; report, _ = checker.analyze(data); self.assertIn("GRAPH_DESCRIPTOR_REMOVED", self.codes(report))
    def test_graph_metadata_drift(self):
        data = audit(); changed = desc(); changed["size"] = 11; data["after"] = {"index": {"schemaVersion": 2, "manifests": [changed]}, "children": {D("a"): child()}}; report, _ = checker.analyze(data); self.assertIn("GRAPH_DESCRIPTOR_DRIFT", self.codes(report))
    def test_graph_child_drift(self):
        data = audit(); data["after"] = {"index": data["before"]["index"], "children": {D("a"): child("arm64", "v8")}}; report, _ = checker.analyze(data); self.assertIn("GRAPH_CHILD_DRIFT", self.codes(report))
    def test_graph_order_change(self):
        a, b = desc("a"), desc("b", "arm64", "v8"); data = audit([a,b], {D("a"): child(), D("b"): child("arm64","v8")}); data["after"] = {"index": {"schemaVersion": 2, "manifests": [b,a]}, "children": data["before"]["children"]}; report, _ = checker.analyze(data); self.assertIn("GRAPH_ORDER_CHANGED", self.codes(report))
    def test_unknown_media_type_not_rejected(self):
        x = desc(media="application/vnd.example.future"); report, code = checker.analyze(audit([x], {})); self.assertEqual(code, 1); self.assertIn("NON_IMAGE_DESCRIPTOR_PLATFORM", {o["code"] for o in report["observations"]})
    def test_single_manifest_not_applicable(self):
        report, code = checker.analyze({"schemaVersion":2,"mediaType":checker.IMAGE_MT}); self.assertEqual(code,0); self.assertEqual(report["status"],"not_applicable")
    def test_missing_child_fails(self):
        data=audit(); data["before"]["children"]={}; report,_=checker.analyze(data); self.assertIn("MISSING_CHILD_CONTENT",self.codes(report))
    def test_bool_size_rejected(self):
        x=desc(); x["size"]=True
        with self.assertRaises(checker.InputError): checker.analyze(audit([x],{D("a"):child()}))
    def test_bad_digest_rejected(self):
        x=desc(); x["digest"]="sha256:no"
        with self.assertRaises(checker.InputError): checker.analyze(audit([x],{}))
    def test_wrong_matcher_rejected(self):
        data=audit(); data["matcher"]="runtime"
        with self.assertRaises(checker.InputError): checker.analyze(data)
    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x"; p.write_text('{"x":NaN}')
            with self.assertRaises(checker.InputError): checker.load_json(p)
    def test_malformed_json_cli_exit_2(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"bad.txt"; p.write_text("{"); run=subprocess.run([sys.executable,str(SCRIPT),"--input",str(p)],capture_output=True,text=True); self.assertEqual(run.returncode,2)
    def test_unwritable_output_exit_2(self):
        if sys.platform == "win32": self.skipTest("POSIX output sink")
        with tempfile.TemporaryDirectory() as td:
            inp=Path(td)/"in.json"; inp.write_text(json.dumps(audit())); out=Path(td)/"missing"/"out.json"; run=subprocess.run([sys.executable,str(SCRIPT),"--input",str(inp),"--output",str(out)],capture_output=True,text=True); self.assertEqual(run.returncode,2)

if __name__ == "__main__": unittest.main()
