import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'analyze_forwarded_chain.py'
FIXTURE=ROOT/'tests'/'fixtures'/'matrix.json'
spec=importlib.util.spec_from_file_location('analyzer',SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class AnalyzerTests(unittest.TestCase):
    def run_fixture(self, data):
        with tempfile.NamedTemporaryFile('w',delete=False) as f:
            json.dump(data,f); name=f.name
        try:
            p=subprocess.run([sys.executable,str(SCRIPT),name],text=True,capture_output=True)
            return p, json.loads(p.stdout) if p.stdout else None
        finally: os.unlink(name)

    def test_packaged_matrix(self):
        p=subprocess.run([sys.executable,str(SCRIPT),str(FIXTURE)],text=True,capture_output=True)
        self.assertEqual(p.returncode,1); report=json.loads(p.stdout)
        self.assertTrue(report['offline']); self.assertEqual(report['summary'],{'error':1,'pass':2})
        x=report['results'][0]
        self.assertEqual((x['selected_address'],x['selected_port'],x['selected_source']),('198.51.100.7',None,'x_forwarded_for[0]'))
        self.assertEqual(x['chain_right_to_left'],['10.0.0.9:43100','10.0.0.8','198.51.100.7'])
        edge=report['results'][1]
        self.assertEqual(edge['findings'][0]['code'],'unattributable_boundary'); self.assertIsNone(edge['selected_address'])

    def test_direct_untrusted_peer_wins_over_spoofed_header(self):
        p,r=self.run_fixture({'records':[{'id':'direct','mode':'xff-cidr','socket_peer':'203.0.113.9:1234','trusted_cidrs':['10.0.0.0/8'],'x_forwarded_for':['198.51.100.1']}]})
        self.assertEqual(p.returncode,0); x=r['results'][0]
        self.assertEqual(x['selected_source'],'socket_peer'); self.assertEqual(x['selected_port'],1234)

    def test_fixed_hop_short_path_fails_closed(self):
        p,r=self.run_fixture({'records':[{'id':'short','mode':'fixed-hop-count','trusted_hops':2,'socket_peer':'10.0.0.9','x_forwarded_for':['198.51.100.1']}]})
        self.assertEqual(p.returncode,1); self.assertEqual(r['results'][0]['findings'][0]['code'],'insufficient_hops')

    def test_forwarded_repeated_fields_and_quoted_ipv6(self):
        data={'records':[{'id':'v6','mode':'forwarded-cidr','socket_peer':'10.0.0.9','trusted_cidrs':['10.0.0.0/8','2001:db8::/64'],'forwarded':['for=198.51.100.7','for="[2001:db8::2]:8443"']}]}
        p,r=self.run_fixture(data); self.assertEqual(p.returncode,0)
        x=r['results'][0]; self.assertEqual(x['selected_address'],'198.51.100.7'); self.assertIsNone(x['selected_port']); self.assertEqual(x['selected_source'],'forwarded[0]')

    def test_unknown_and_duplicate_parameter(self):
        for value in ('for=unknown','for=198.51.100.1;for=198.51.100.2'):
            p,r=self.run_fixture({'records':[{'id':'bad','mode':'forwarded-cidr','socket_peer':'10.0.0.9','trusted_cidrs':['10.0.0.0/8'],'forwarded':[value]}]})
            if value == 'for=unknown':
                self.assertEqual(p.returncode,1); self.assertEqual(r['results'][0]['observations'][0]['code'],'unknown_boundary')
            else:
                self.assertEqual(p.returncode,2); self.assertIn('duplicate',p.stderr)

    def test_malformed_schema_nonfinite_and_duplicate_ids(self):
        cases=[b'{',b'{"records":[{"id":"x","mode":"xff-cidr","socket_peer":"1.1.1.1","trusted_cidrs":["10/8"]},{"id":"x","mode":"xff-cidr","socket_peer":"1.1.1.1","trusted_cidrs":["10/8"]}]}',b'{"records":[NaN]}',b'{"records":[{"id":"x","mode":"xff-cidr","socket_peer":"1.1.1.1","trusted_cidrs":[42]}]}']
        for raw in cases:
            with tempfile.NamedTemporaryFile(delete=False) as f: f.write(raw); name=f.name
            try:
                p=subprocess.run([sys.executable,str(SCRIPT),name],text=True,capture_output=True)
                self.assertEqual(p.returncode,2); self.assertFalse(p.stdout)
            finally: os.unlink(name)

    def test_unreadable_and_hop_cap(self):
        p=subprocess.run([sys.executable,str(SCRIPT),'/definitely/missing'],text=True,capture_output=True)
        self.assertEqual(p.returncode,2)
        many=', '.join(['10.0.0.1']*257)
        p,r=self.run_fixture({'records':[{'id':'many','mode':'xff-cidr','socket_peer':'10.0.0.9','trusted_cidrs':['10/8'],'x_forwarded_for':[many]}]})
        self.assertEqual(p.returncode,2); self.assertIsNone(r)

    def test_output_failure_returns_three(self):
        report={'summary':{'error':0}}
        broken=mock.Mock(); broken.write.side_effect=BrokenPipeError(); broken.flush=mock.Mock()
        with mock.patch.object(sys,'stdout',broken):
            self.assertEqual(mod.write_report(report),3)

if __name__=='__main__': unittest.main()
