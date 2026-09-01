#!/usr/bin/env python3
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "audit_resume.py"
spec = importlib.util.spec_from_file_location("audit_resume", SCRIPT)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

DIGEST = "a" * 64

def case(status=206, local=100, start=100, body=100, headers=None, etag='"v1"', digest=DIGEST):
    if headers is None:
        headers = {"Content-Range": "bytes 100-199/1000", "Content-Length": "100", "ETag": '"v1"'}
    return {"checkpoint": {"local_size": local, "etag": etag, "expected_sha256": digest}, "request": {"range_start": start}, "response": {"status": status, "body_length": body, "headers": headers}}

class AuditTests(unittest.TestCase):
    def test_valid_206_append(self):
        self.assertEqual(mod.audit(case())["classification"], "append")
    def test_wrong_start_rejected(self):
        result = mod.audit(case(headers={"Content-Range":"bytes 99-198/1000","Content-Length":"100","ETag":'"v1"'}))
        self.assertIn("RANGE_START_MISMATCH", [x["code"] for x in result["findings"]])
    def test_changed_etag_rejected(self):
        result = mod.audit(case(headers={"Content-Range":"bytes 100-199/1000","Content-Length":"100","ETag":'"v2"'}))
        self.assertIn("REPRESENTATION_CHANGED", [x["code"] for x in result["findings"]])
    def test_weak_etag_rejected(self):
        result = mod.audit(case(headers={"Content-Range":"bytes 100-199/1000","Content-Length":"100","ETag":'W/"v1"'}))
        self.assertIn("STRONG_VALIDATOR_REQUIRED", [x["code"] for x in result["findings"]])
    def test_ranged_200_with_content_range_rejected(self):
        result = mod.audit(case(status=200))
        self.assertIn("STATUS_RANGE_CONTRADICTION", [x["code"] for x in result["findings"]])
    def test_plain_200_is_restart_not_append(self):
        result = mod.audit(case(status=200, body=1000, headers={"Content-Length":"1000","ETag":'"v1"'}))
        self.assertEqual((result["classification"], result["safe_to_append"]), ("restart", False))
    def test_416_size_match_requires_hash(self):
        result = mod.audit(case(status=416, local=500, start=500, body=0, headers={"Content-Range":"bytes */500","ETag":'"v1"'}))
        self.assertEqual(result["classification"], "verify_local_complete")
        result = mod.audit(case(status=416, local=500, start=500, body=0, digest=None, headers={"Content-Range":"bytes */500","ETag":'"v1"'}))
        self.assertIn("COMPLETENESS_UNPROVEN", [x["code"] for x in result["findings"]])
    def test_content_encoding_rejected(self):
        result = mod.audit(case(headers={"Content-Range":"bytes 100-199/1000","Content-Length":"100","ETag":'"v1"',"Content-Encoding":"gzip"}))
        self.assertIn("CONTENT_ENCODING_UNSAFE", [x["code"] for x in result["findings"]])
    def test_malformed_and_nonfinite_fail_closed(self):
        for raw in ["{", '{"x":NaN}', "[]"]:
            with tempfile.NamedTemporaryFile("w", delete=False) as f:
                f.write(raw); path=f.name
            try:
                proc=subprocess.run([sys.executable,str(SCRIPT),path],text=True,capture_output=True)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(json.loads(proc.stdout)["error"], "invalid_input")
            finally: os.unlink(path)
    def test_unreadable_and_broken_stdout(self):
        missing=subprocess.run([sys.executable,str(SCRIPT),"/definitely/missing"],text=True,capture_output=True)
        self.assertEqual(missing.returncode, 2)
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            json.dump(case(),f); path=f.name
        try:
            proc=subprocess.run([sys.executable,str(SCRIPT),path],stdout=subprocess.DEVNULL)
            self.assertEqual(proc.returncode,0)
            shell=subprocess.run([sys.executable,"-c",f"import os,sys; os.close(1); os.execv(sys.executable,[sys.executable,{str(SCRIPT)!r},{path!r}])"])
            self.assertEqual(shell.returncode,74)
        finally: os.unlink(path)
if __name__ == "__main__": unittest.main()
