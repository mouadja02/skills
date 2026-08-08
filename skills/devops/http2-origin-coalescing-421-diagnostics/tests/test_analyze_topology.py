import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]; SCRIPT=ROOT/'scripts'/'analyze_topology.py'; VALID=ROOT/'tests'/'fixtures'/'misdirected.json.txt'

def run_bytes(data, output=None):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'in.txt'; p.write_bytes(data)
        cmd=[sys.executable,str(SCRIPT),str(p)]
        if output: cmd += ['--output',str(output)]
        return subprocess.run(cmd,text=True,capture_output=True)
def base(): return json.loads(VALID.read_text())
class TestAnalyzer(unittest.TestCase):
    def test_detects_coalesced_wrong_origin(self):
        r=run_bytes(VALID.read_bytes()); self.assertEqual(r.returncode,1); out=json.loads(r.stdout); self.assertIn('WRONG_ORIGIN_CONTENT',{x['code'] for x in out['findings']}); self.assertTrue(out['observations'][0]['coalesced_candidate'])
    def test_safe_421_origin(self):
        d=base(); d['observations'][0]['status']=421; d['observations'][0]['served_backend']='app-b'; r=run_bytes(json.dumps(d).encode()); self.assertEqual(r.returncode,0); self.assertTrue(json.loads(r.stdout)['safe'])
    def test_safe_authority_aware_coalescing(self):
        d=base(); d['observations'][0]['served_backend']='app-b'; r=run_bytes(json.dumps(d).encode()); self.assertEqual(r.returncode,0); self.assertTrue(json.loads(r.stdout)['observations'][0]['coalesced_candidate'])
    def test_proxy_must_not_generate_421(self):
        d=base(); d['role']='proxy'; d['observations'][0]['status']=421; d['observations'][0]['served_backend']='app-b'; r=run_bytes(json.dumps(d).encode()); self.assertEqual(r.returncode,1); self.assertIn('PROXY_MUST_NOT_GENERATE_421',r.stdout)
    def test_fresh_wrong_backend_is_not_blindly_coalescing(self):
        d=base(); d['observations'][0]['fresh_connection']=True; r=run_bytes(json.dumps(d).encode()); self.assertIn('FRESH_CONNECTION_MISROUTED',r.stdout)
    def test_rejects_nan(self): self.assertEqual(run_bytes(VALID.read_bytes().replace(b'200',b'NaN',1)).returncode,2)
    def test_rejects_non_object(self): self.assertEqual(run_bytes(b'[]').returncode,2)
    def test_rejects_unknown_key(self):
        d=base(); d['surprise']=1; self.assertEqual(run_bytes(json.dumps(d).encode()).returncode,2)
    def test_rejects_boolean_status(self):
        d=base(); d['observations'][0]['status']=True; self.assertEqual(run_bytes(json.dumps(d).encode()).returncode,2)
    def test_rejects_empty_dns_label(self):
        d=base(); d['observations'][0]['authority']='bad..example.test'; self.assertEqual(run_bytes(json.dumps(d).encode()).returncode,2)
    def test_wildcard_is_one_label_only(self):
        d=base(); d['observations'][0]['authority']='deep.b.example.test'; d['owned_hosts']['deep.b.example.test']='app-b'; r=run_bytes(json.dumps(d).encode()); self.assertFalse(json.loads(r.stdout)['observations'][0]['certificate_covers_both'])
    def test_output_failure_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'directory'; target.mkdir(); r=run_bytes(VALID.read_bytes(),target); self.assertEqual(r.returncode,2)
if __name__=='__main__': unittest.main()
