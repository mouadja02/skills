#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("analyze_slots.py")

def base_slot(**overrides):
    slot = {"slot_name":"cdc","slot_type":"logical","active":True,"failover":True,"synced":False,"temporary":False,"invalidation_reason":None,"wal_status":"reserved","safe_wal_size":2_000_000_000,"retained_wal_bytes":10,"consumer_owner_confirmed":True}
    slot.update(overrides)
    return slot

def snapshot(slot=None, role="primary"):
    return {"schema_version":1,"server_role":role,"slots":[slot or base_slot()]}

class AnalyzeSlotsTests(unittest.TestCase):
    def run_case(self, value, raw=False):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"input.json"
            p.write_text(value if raw else json.dumps(value), encoding="utf-8")
            return subprocess.run([sys.executable,str(SCRIPT),"--input",str(p)],text=True,capture_output=True)

    def assert_overall(self, value, expected):
        p=self.run_case(value); self.assertEqual(p.returncode,0,p.stderr); self.assertEqual(json.loads(p.stdout)["overall"],expected)

    def test_orphan_candidate(self):
        v=snapshot(base_slot(active=False,consumer_owner_confirmed=False,retained_wal_bytes=99),"demoted_primary")
        p=self.run_case(v); self.assertEqual(p.returncode,0); out=json.loads(p.stdout); self.assertEqual(out["overall"],"review"); self.assertEqual(out["slots"][0]["classification"],"orphan_candidate"); self.assertFalse(out["mutation_permitted"])
    def test_standby_ready(self): self.assert_overall(snapshot(base_slot(synced=True),"standby"),"ready")
    def test_standby_not_ready(self): self.assert_overall(snapshot(base_slot(synced=False),"standby"),"blocked")
    def test_invalidated_is_critical(self): self.assert_overall(snapshot(base_slot(invalidation_reason="wal_removed",wal_status="lost"),"standby"),"critical")
    def test_safe_wal_zero_is_critical(self): self.assert_overall(snapshot(base_slot(safe_wal_size=0)),"critical")
    def test_physical_is_not_applicable(self): self.assert_overall(snapshot(base_slot(slot_type="physical",failover=False)),"not_applicable")
    def test_unknown_key_fails_closed(self):
        v=snapshot(); v["password"]="secret"; self.assertEqual(self.run_case(v).returncode,2)
    def test_missing_slot_key_fails_closed(self):
        slot=base_slot(); del slot["wal_status"]; self.assertEqual(self.run_case(snapshot(slot)).returncode,2)
    def test_boolean_integer_fails_closed(self):
        v=snapshot(base_slot(active=1)); self.assertEqual(self.run_case(v).returncode,2)
    def test_duplicate_names_fail_closed(self):
        v=snapshot(); v["slots"].append(base_slot()); self.assertEqual(self.run_case(v).returncode,2)
    def test_nan_fails_closed(self): self.assertEqual(self.run_case('{"schema_version":1,"server_role":"primary","warning_threshold_bytes":NaN,"slots":[]}',True).returncode,2)
    def test_non_object_fails_closed(self): self.assertEqual(self.run_case([],False).returncode,2)
    def test_missing_file_fails_closed(self):
        p=subprocess.run([sys.executable,str(SCRIPT),"--input","/definitely/missing"],text=True,capture_output=True); self.assertEqual(p.returncode,2)

if __name__ == "__main__": unittest.main()
