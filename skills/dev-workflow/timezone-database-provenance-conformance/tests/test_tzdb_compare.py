#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys, tempfile
SCRIPT=pathlib.Path(__file__).parents[1]/"scripts"/"tzdb_compare.py"
PROBES=[
 {"id":"gap","kind":"gap","wall":"2026-03-08T02:30:00","fold":None,"valid":False,"offset_seconds":None,"utc":None},
 {"id":"fold-0","kind":"fold","wall":"2026-11-01T01:30:00","fold":0,"valid":True,"offset_seconds":-25200,"utc":"2026-11-01T08:30:00Z"},
 {"id":"fold-1","kind":"fold","wall":"2026-11-01T01:30:00","fold":1,"valid":True,"offset_seconds":-28800,"utc":"2026-11-01T09:30:00Z"},
 {"id":"recent","kind":"recent-rule","wall":"2026-12-01T12:00:00","fold":None,"valid":True,"offset_seconds":-28800,"utc":"2026-12-01T20:00:00Z"}]
def doc(version="2026a",require=True):
 return {"schema_version":1,"mode":"named-zone","policy":{"require_declared_version":require},"observations":[{"runtime_id":"browser","provider":"Intl","version":version,"zone":"America/Vancouver","probes":PROBES},{"runtime_id":"server","provider":"zoneinfo","version":"2026a","zone":"America/Vancouver","probes":json.loads(json.dumps(PROBES))}]}
def run(value,raw=False,stdout=None):
 with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False) as fh:
  fh.write(value if raw else json.dumps(value)); name=fh.name
 try:
  cp=subprocess.run([sys.executable,str(SCRIPT),name],text=True,stdout=subprocess.PIPE if stdout is None else stdout,stderr=subprocess.PIPE)
  payload=json.loads(cp.stdout) if stdout is None and cp.stdout else None
  return cp,payload
 finally: os.unlink(name)
def assert_case(name,fn):
 fn(); print("ok",name)
def main():
 def allow():
  cp,p=run(doc()); assert cp.returncode==0 and p["status"]=="allow" and p["findings"]==[]
 def divergent():
  d=doc(); d["observations"][1]["probes"][-1]["offset_seconds"]=-25200; d["observations"][1]["probes"][-1]["utc"]="2026-12-01T19:00:00Z"; cp,p=run(d); assert cp.returncode==1 and any(f["code"]=="PROBE_DIVERGENCE" for f in p["findings"])
 def unknown_required():
  cp,p=run(doc(None)); assert cp.returncode==1 and p["findings"][0]["severity"]=="violation"
 def unknown_observed():
  cp,p=run(doc(None,False)); assert cp.returncode==0 and p["findings"][0]["severity"]=="observation"
 def missing_kind():
  d=doc(); [o.update(probes=[p for p in o["probes"] if p["kind"]!="gap"]) for o in d["observations"]]; cp,p=run(d); assert cp.returncode==1 and sum(f["code"]=="MISSING_TRANSITION_COVERAGE" for f in p["findings"])==2
 def fixed():
  cp,p=run({"schema_version":1,"mode":"fixed-offset"}); assert cp.returncode==0 and p["status"]=="not_applicable"
 def malformed():
  cp,p=run("{",True); assert cp.returncode==2 and p["status"]=="input_error"
 def nonfinite():
  cp,p=run('{"schema_version":1,"mode":"named-zone","policy":{"require_declared_version":true},"observations":NaN}',True); assert cp.returncode==2 and "non-finite" in p["error"]
 def wrong_shape():
  cp,p=run([]); assert cp.returncode==2 and p["status"]=="input_error"
 def aware_wall():
  d=doc(); d["observations"][0]["probes"][0]["wall"]="2026-03-08T02:30:00-08:00"; cp,p=run(d); assert cp.returncode==2 and "offset-free" in p["error"]
 def stdout_failure():
  d=doc()
  with tempfile.NamedTemporaryFile("w",delete=False) as fh: json.dump(d,fh); name=fh.name
  try:
   with open("/dev/full","wb") as sink:
    cp=subprocess.run([sys.executable,str(SCRIPT),name],stdout=sink,stderr=subprocess.PIPE)
   assert cp.returncode==74,(cp.returncode,cp.stderr)
  finally: os.unlink(name)
 for name,fn in [("allow",allow),("divergent",divergent),("unknown-required",unknown_required),("unknown-observed",unknown_observed),("missing-kind",missing_kind),("fixed-offset",fixed),("malformed",malformed),("nonfinite",nonfinite),("wrong-shape",wrong_shape),("aware-wall",aware_wall),("stdout-failure",stdout_failure)]: assert_case(name,fn)
 print("11 tests passed")
if __name__=="__main__": main()
