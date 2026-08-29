#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_redirects.py"

def run(doc):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "input.json"
        if isinstance(doc, bytes): p.write_bytes(doc)
        else: p.write_text(json.dumps(doc), encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), str(p)], text=True, capture_output=True)
        return r.returncode, json.loads(r.stdout)

def chain(dst="https://api.example.test/b", status=307, before=("Authorization",), after=("Authorization",), method="GET", next_method=None):
    return {"credential_headers":["authorization","x-api-key"],"hops":[
      {"request":{"url":"https://api.example.test:443/a","method":method,"headers":list(before)},"response":{"status":status,"location":dst}},
      {"request":{"url":dst,"method":next_method or method,"headers":list(after)},"response":{"status":200}}]}

def check(name, condition):
    if not condition: raise AssertionError(name)
    print("ok", name)

def main():
    rc, out = run(chain(status=301))
    check("default-port same origin", rc == 0 and out["finding_count"] == 0 and out["transitions"][0]["same_origin"])
    rc, out = run(chain(dst="https://cdn.example.test/b", before=("X-API-Key",), after=("X-API-Key",)))
    check("custom credential cross-origin", rc == 1 and out["findings"][0]["code"] == "CREDENTIAL_FORWARDED_CROSS_ORIGIN")
    rc, out = run(chain(dst="http://api.example.test/b"))
    check("downgrade", rc == 1 and any(x["code"] == "CREDENTIAL_FORWARDED_ON_DOWNGRADE" for x in out["findings"]))
    rc, out = run(chain(dst="https://cdn.example.test/b", after=()))
    check("safe stripped positive control", rc == 0 and out["transitions"][0]["credential_action"] == "strip")
    rc, out = run(chain(status=303, method="POST", next_method="GET"))
    check("303 method rewrite", rc == 0 and out["transitions"][0]["expected_method"] == "GET")
    rc, out = run(chain(status=307, method="POST", next_method="GET"))
    check("307 method preserve", rc == 1 and any(x["code"] == "REDIRECT_METHOD_MISMATCH" for x in out["findings"]))
    rc, out = run(b'{"credential_headers":[],"hops":[NaN]}')
    check("non-finite malformed input", rc == 2 and out["error"]["code"] == "INVALID_INPUT")
    bad = chain(); bad["hops"][0]["request"]["url"] = "https://user:secret@api.example.test/a"
    rc, out = run(bad)
    check("userinfo rejected", rc == 2 and out["error"]["code"] == "INVALID_INPUT")
    bad = chain(); bad["hops"][0]["request"]["headers"] = {"Authorization":"secret"}
    rc, out = run(bad)
    check("header values rejected", rc == 2 and "array of header-name" in out["error"]["message"])
    spec = importlib.util.spec_from_file_location("analyzer", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load analyzer")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    class Broken:
        def write(self, value): raise OSError("controlled")
        def flush(self): raise OSError("controlled")
    old = sys.stdout
    try:
        sys.stdout = Broken(); result = mod.emit({"ok":True})
    finally: sys.stdout = old
    check("controlled output failure", result == 3)
    return 0

if __name__ == "__main__": raise SystemExit(main())
