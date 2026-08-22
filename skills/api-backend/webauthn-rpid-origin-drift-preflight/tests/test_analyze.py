import importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/'scripts'/'analyze_webauthn_boundary.py'; FIX=ROOT/'tests'/'fixtures'
spec=importlib.util.spec_from_file_location('analyzer',SCRIPT)
assert spec is not None and spec.loader is not None
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_ready(self): self.assertEqual(m.analyze(json.loads((FIX/'normal.json').read_text()))['classification'],'ready')
 def test_edge_findings(self):
  r=m.analyze(json.loads((FIX/'edge.json').read_text())); codes={x['code'] for x in r['findings']}
  self.assertTrue({'authentication_origin_mismatch','ambiguous_proxy_trust','credential_reenrollment_required'} <= codes)
 def test_not_applicable(self): self.assertEqual(m.analyze({'kind':'oauth'})['classification'],'not_applicable')
 def test_port_is_origin_boundary_not_rpid(self):
  d=json.loads((FIX/'normal.json').read_text()); d['public_origin']='https://login.example.test:8443'; r=m.analyze(d)
  self.assertIn('registration_origin_mismatch',{x['code'] for x in r['findings']}); self.assertNotIn('rp_id_origin_scope_mismatch',{x['code'] for x in r['findings']})
 def test_public_suffix_rejected(self):
  d=json.loads((FIX/'normal.json').read_text()); d['rp_id']='test';
  with self.assertRaises(m.InputError): m.analyze(d)
 def test_escaped_and_malformed_origins_fail(self):
  for origin in ['https://user@example.test','https://example.test/path','https://example.test%00.evil','android:apk-key-hash:U3ludGhldGljVGVzdEhhc2g']:
   d=json.loads((FIX/'normal.json').read_text()); d['public_origin']=origin
   with self.assertRaises(m.InputError): m.analyze(d)
 def test_missing_or_boolean_hop_counts_block(self):
  for trusted,observed in [(None,None),(True,True),(2,1)]:
   d=json.loads((FIX/'normal.json').read_text()); d['proxy']={'derive_from_forwarded':True,'direct_peer_trusted':True,'edge_strips_client_forwarded':True,'headers_agree':True,'trusted_hop_count':trusted,'observed_hop_count':observed,'forwarded_origin':d['public_origin']}
   self.assertIn('ambiguous_proxy_trust',{x['code'] for x in m.analyze(d)['findings']})
 def test_bad_shapes_and_secret_keys_fail(self):
  for d in [{'kind':'webauthn','cookie':'x'},{'kind':'webauthn','allowed_origins':{}},[]]:
   with self.assertRaises((m.InputError,AttributeError)): m.analyze(d)
 def test_nonfinite_and_malformed_cli_fail_closed(self):
  for name in ['nan.txt','malformed.txt']:
   p=subprocess.run([sys.executable,str(SCRIPT),str(FIX/name)],capture_output=True,text=True)
   self.assertEqual(p.returncode,2); self.assertIn('input_error',p.stderr)
 def test_expected_invalid_parses_then_blocks(self):
  p=subprocess.run([sys.executable,str(SCRIPT),str(FIX/'edge.json')],capture_output=True,text=True)
  self.assertEqual(p.returncode,1); self.assertEqual(json.loads(p.stdout)['classification'],'blocked')
 def test_controlled_output_failure(self):
  with tempfile.TemporaryDirectory() as td:
   target=Path(td)/'as-directory'; target.mkdir()
   p=subprocess.run([sys.executable,str(SCRIPT),str(FIX/'normal.json'),'--output',str(target)],capture_output=True,text=True)
   self.assertEqual(p.returncode,2); self.assertIn('input_error',p.stderr)
if __name__=='__main__': unittest.main()
