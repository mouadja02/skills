#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "no_proxy_probe.py"
FIXTURES = pathlib.Path(__file__).parent / "fixtures"

class ProbeTests(unittest.TestCase):
    def run_probe(self, fixture, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), str(FIXTURES/fixture), *map(str,extra)], text=True, capture_output=True, env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    def test_valid_matrix_observes_both_routes(self):
        r=self.run_probe("valid-matrix.json.txt"); self.assertEqual(r.returncode,0,r.stderr)
        d=json.loads(r.stdout); self.assertTrue(d["passed"]); self.assertEqual(len(d["rows"]),4)
        self.assertEqual({x["observed"] for x in d["rows"]},{"direct","proxy"})
    def test_expectation_mismatch_is_exit_one(self):
        r=self.run_probe("mismatch.json.txt"); self.assertEqual(r.returncode,1); self.assertFalse(json.loads(r.stdout)["passed"])
    def test_malformed_json_is_exit_two(self):
        r=self.run_probe("malformed.json.txt"); self.assertEqual(r.returncode,2); self.assertIn("error:",r.stderr)
    def test_nan_is_rejected(self):
        r=self.run_probe("nan.json.txt"); self.assertEqual(r.returncode,2); self.assertIn("non-finite",r.stderr)
    def test_unknown_client_is_rejected(self):
        r=self.run_probe("unknown-client.json.txt"); self.assertEqual(r.returncode,2)
    def test_non_loopback_host_is_rejected(self):
        r=self.run_probe("non-loopback.json.txt"); self.assertEqual(r.returncode,2); self.assertIn("localhost or 127.0.0.1",r.stderr)
    def test_environment_key_is_restricted(self):
        r=self.run_probe("unsafe-env.json.txt"); self.assertEqual(r.returncode,2)
    def test_output_failure_is_exit_two(self):
        with tempfile.TemporaryDirectory() as td:
            r=self.run_probe("valid-matrix.json.txt","--output",td)
            self.assertEqual(r.returncode,2); self.assertIn("cannot write report",r.stderr)
    def test_atomic_output(self):
        with tempfile.TemporaryDirectory() as td:
            out=pathlib.Path(td)/"report.json"; r=self.run_probe("valid-matrix.json.txt","--output",out)
            self.assertEqual(r.returncode,0,r.stderr); self.assertTrue(json.loads(out.read_text())["passed"])

if __name__ == "__main__": unittest.main()
