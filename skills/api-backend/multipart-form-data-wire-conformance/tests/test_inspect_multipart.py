import base64
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "inspect_multipart.py"
spec = importlib.util.spec_from_file_location("inspect_multipart", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inspector module")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

B = b"Boundary42"
def body(disposition=b'form-data; name="field"', payload=b"value", close=True, epilogue=b""):
    data = b"--"+B+b"\r\nContent-Disposition: "+disposition+b"\r\n\r\n"+payload+b"\r\n"
    return data + (b"--"+B+b"--" + (b"\r\n"+epilogue if epilogue else b"") if close else b"")

def inspect(data, ct="multipart/form-data; boundary=Boundary42", limits=None):
    return mod.inspect(ct, data, limits)

class InspectorTests(unittest.TestCase):
    def assertCode(self, report, code):
        self.assertIn(code, [v["code"] for v in report["violations"]])

    def test_normal_binary_and_eof_close(self):
        data = (b"preamble\r\n--Boundary42\r\nContent-Disposition: form-data; name=\"note\"\r\n\r\nhello\r\n"
                b"--Boundary42\r\nContent-Disposition: form-data; name=\"blob\"; filename=\"x.bin\"\r\nContent-Type: application/octet-stream\r\n\r\n\x00tail\xff\r\n--Boundary42--")
        r = inspect(data)
        self.assertTrue(r["valid"]); self.assertEqual(2, len(r["parts"])); self.assertEqual(6, r["parts"][1]["body_bytes"])
        self.assertEqual("c159720c5b7d5e85a3b79f67b16d9333cd3846a06caa533674d2fcb8910bd054", r["parts"][1]["sha256"])
        self.assertEqual(10, r["preamble_bytes"]); self.assertEqual(0, r["epilogue_bytes"])

    def test_epilogue_and_extended_name_fail_closed(self):
        r = inspect(body(b'form-data; name="safe"; name*=utf-8\'\'other', epilogue=b"epilogue"))
        self.assertFalse(r["valid"]); self.assertTrue(r["closing_boundary"]); self.assertEqual(8, r["epilogue_bytes"])
        self.assertCode(r, "disposition-extended-name")

    def test_duplicate_parameter(self):
        r = inspect(body(b'form-data; name="a"; name="b"'))
        self.assertCode(r, "disposition-parameter-duplicate")

    def test_filename_star_forbidden(self):
        self.assertCode(inspect(body(b'form-data; name="a"; filename*=utf-8\'\'x')), "disposition-extended-filename")

    def test_missing_close(self):
        self.assertCode(inspect(body(close=False)), "closing-boundary-missing")

    def test_boundary_case_mismatch(self):
        self.assertCode(inspect(body().replace(B, b"boundary42")), "opening-boundary-missing")

    def test_malformed_boundary_suffix(self):
        self.assertCode(inspect(body().replace(b"--Boundary42--", b"--Boundary42-X")), "boundary-line-malformed")

    def test_non_multipart_not_applicable(self):
        r = inspect(b'{}', "application/json")
        self.assertFalse(r["applicable"]); self.assertFalse(r["valid"]); self.assertEqual([], r["violations"])

    def test_boundary_parameter_constraints(self):
        self.assertCode(inspect(body(), "multipart/form-data"), "boundary-parameter-count")
        self.assertCode(inspect(body(), "multipart/form-data; boundary=x; boundary=y"), "boundary-parameter-count")
        self.assertCode(inspect(body(), "multipart/form-data; boundary=bad@value"), "boundary-invalid")

    def test_headers_fail_closed(self):
        data = body().replace(b"Content-Disposition", b" Folded\r\nContent-Disposition")
        self.assertCode(inspect(data), "part-header-obs-fold")
        data = body().replace(b"Content-Disposition:", b"Content-Disposition:\r\nContent-Disposition:")
        self.assertCode(inspect(data), "content-disposition-count")
        data = body().replace(b'name="field"', b'name="field"\x01')
        self.assertCode(inspect(data), "part-header-value-invalid")

    def test_limits(self):
        self.assertCode(inspect(body(), limits={"max_body_bytes": 1}), "body-too-large")
        two = body().replace(b"--Boundary42--", b"--Boundary42\r\nContent-Disposition: form-data; name=\"b\"\r\n\r\ny\r\n--Boundary42--")
        self.assertCode(inspect(two, limits={"max_parts": 1}), "part-count-exceeded")

    def test_payload_boundary_like_bytes_are_preserved(self):
        payload = b"abc--Boundary42not-a-line\n--Boundary42-X"
        r = inspect(body(payload=payload))
        self.assertTrue(r["valid"]); self.assertEqual(len(payload), r["parts"][0]["body_bytes"])

    def test_case_cli_valid_invalid_and_not_applicable(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"case.json"
            p.write_text(json.dumps({"content_type":"multipart/form-data; boundary=Boundary42","body_base64":base64.b64encode(body()).decode()}))
            ok = subprocess.run([sys.executable, str(SCRIPT), "--case", str(p)], capture_output=True, text=True)
            self.assertEqual(0, ok.returncode); self.assertTrue(json.loads(ok.stdout)["valid"])
            p.write_text(json.dumps({"content_type":"multipart/form-data; boundary=Boundary42","body_base64":base64.b64encode(body(b'form-data; name*=x')).decode()}))
            bad = subprocess.run([sys.executable, str(SCRIPT), "--case", str(p)], capture_output=True, text=True)
            self.assertEqual(1, bad.returncode); self.assertFalse(json.loads(bad.stdout)["valid"])
            p.write_text(json.dumps({"content_type":"application/json","body_base64":"e30="}))
            skip = subprocess.run([sys.executable, str(SCRIPT), "--case", str(p)], capture_output=True, text=True)
            self.assertEqual(0, skip.returncode); self.assertFalse(json.loads(skip.stdout)["applicable"])

    def test_case_cli_rejects_malformed_schema_json_base64_and_unreadable(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"case.txt"
            for text in ["{", '{"content_type":"x","body_base64":"e30=","extra":1}', '{"content_type":"x","body_base64":"%%%"}', '{"content_type":"x","body_base64":"e30=","limits":{"max_parts":NaN}}']:
                p.write_text(text)
                cp = subprocess.run([sys.executable, str(SCRIPT), "--case", str(p)], capture_output=True, text=True)
                self.assertEqual(2, cp.returncode); self.assertIn("error", json.loads(cp.stdout))
            cp = subprocess.run([sys.executable, str(SCRIPT), "--case", str(Path(td)/"missing")], capture_output=True, text=True)
            self.assertEqual(2, cp.returncode)

if __name__ == "__main__":
    unittest.main()
