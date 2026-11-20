#!/usr/bin/env python3
"""Offline HTTP/2 origin-coalescing topology analyzer."""
import argparse, json, os, re, sys, tempfile
from pathlib import Path

LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
ROLES = {"origin", "gateway", "proxy"}
ROOT_KEYS = {"version", "local_only", "role", "owned_hosts", "certificate_sans", "observations"}
OBS_KEYS = {"name", "connection_id", "fresh_connection", "sni", "authority", "listener", "served_backend", "status"}

class InputError(Exception): pass

def reject_constant(value): raise InputError(f"non-standard JSON constant: {value}")
def host(value, field, wildcard=False):
    candidate = value[2:] if isinstance(value, str) and value.startswith("*.") else value
    labels = candidate.split(".") if isinstance(candidate, str) else []
    if (not isinstance(value, str) or not value or value != value.lower() or len(value) > 253
            or len(labels) < 2 or any(not LABEL.fullmatch(label) for label in labels)):
        raise InputError(f"{field} must be a lowercase DNS name" + (" or wildcard" if wildcard else ""))
    if not wildcard and value.startswith("*."): raise InputError(f"{field} cannot be a wildcard")
    return value

def san_matches(san, name):
    if san.startswith("*."):
        suffix = san[1:]
        return name.endswith(suffix) and name.count(".") == san.count(".")
    return san == name

def load(path):
    try:
        raw = Path(path).read_text(encoding="utf-8")
        data = json.loads(raw, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as e: raise InputError(f"cannot read topology: {e}")
    if not isinstance(data, dict): raise InputError("topology root must be an object")
    unknown = set(data) - ROOT_KEYS
    if unknown: raise InputError(f"unknown root keys: {sorted(unknown)}")
    if data.get("version") != 1 or data.get("local_only") is not True: raise InputError("version must be 1 and local_only must be true")
    role = data.get("role")
    if role not in ROLES: raise InputError("role must be origin, gateway, or proxy")
    owned = data.get("owned_hosts")
    if not isinstance(owned, dict) or not owned: raise InputError("owned_hosts must be a non-empty object")
    clean_owned = {}
    for k,v in owned.items():
        k=host(k,"owned_hosts key")
        if not isinstance(v,str) or not v or len(v)>128: raise InputError("backend IDs must be non-empty strings of at most 128 characters")
        clean_owned[k]=v
    sans=data.get("certificate_sans")
    if not isinstance(sans,list) or not sans: raise InputError("certificate_sans must be a non-empty array")
    clean_sans=[]
    for i,s in enumerate(sans): clean_sans.append(host(s,f"certificate_sans[{i}]",True))
    obs=data.get("observations")
    if not isinstance(obs,list) or not obs: raise InputError("observations must be a non-empty array")
    names=set(); clean=[]
    for i,o in enumerate(obs):
        if not isinstance(o,dict): raise InputError(f"observations[{i}] must be an object")
        unknown=set(o)-OBS_KEYS
        if unknown: raise InputError(f"observations[{i}] has unknown keys: {sorted(unknown)}")
        if set(o)!=OBS_KEYS: raise InputError(f"observations[{i}] must declare every observation field")
        name=o["name"]
        if not isinstance(name,str) or not name or name in names: raise InputError("observation names must be non-empty and unique")
        names.add(name)
        for key in ("connection_id","listener","served_backend"):
            if not isinstance(o[key],str) or not o[key] or len(o[key])>128: raise InputError(f"{name}.{key} must be a bounded non-empty string")
        if type(o["fresh_connection"]) is not bool: raise InputError(f"{name}.fresh_connection must be boolean")
        if type(o["status"]) is not int or not 100 <= o["status"] <= 599: raise InputError(f"{name}.status must be an integer HTTP status")
        c=dict(o); c["sni"]=host(o["sni"],f"{name}.sni"); c["authority"]=host(o["authority"],f"{name}.authority")
        clean.append(c)
    return {"role":role,"owned":clean_owned,"sans":clean_sans,"observations":clean}

def analyze(d):
    findings=[]; rows=[]
    def finding(code,severity,o,detail): findings.append({"code":code,"severity":severity,"observation":o["name"],"detail":detail})
    for o in d["observations"]:
        expected=d["owned"].get(o["authority"]); cert_covers=all(any(san_matches(s,x) for s in d["sans"]) for x in (o["sni"],o["authority"]))
        coalesced=(not o["fresh_connection"] and o["sni"] != o["authority"] and cert_covers)
        if expected is None: finding("UNOWNED_AUTHORITY","critical",o,"authority has no declared backend owner")
        elif o["served_backend"] != expected and 200 <= o["status"] < 300: finding("WRONG_ORIGIN_CONTENT","critical",o,"successful response came from another origin's backend")
        # SNI/:authority divergence is evidence of connection reuse, not a
        # violation by itself: an authority-aware server can safely serve both.
        misdirected = expected is None or o["served_backend"] != expected
        if d["role"] == "proxy" and o["status"] == 421: finding("PROXY_MUST_NOT_GENERATE_421","critical",o,"RFC 9110 forbids a proxy from generating 421")
        if d["role"] in {"origin","gateway"} and misdirected and o["status"] != 421:
            finding("MISDIRECTED_NOT_REJECTED","high",o,"origin/gateway observation should reject this connection context instead of serving content")
        if o["fresh_connection"] and expected is not None and o["served_backend"] != expected: finding("FRESH_CONNECTION_MISROUTED","high",o,"a fresh connection still reached the wrong backend; coalescing alone is not the cause")
        rows.append({"name":o["name"],"expected_backend":expected,"certificate_covers_both":cert_covers,"coalesced_candidate":coalesced})
    return {"schema_version":1,"local_only":True,"role":d["role"],"safe":not findings,"findings":findings,"observations":rows,
      "recommendation":("Do not generate 421 at the proxy; repair listener/backend routing or preserve an upstream origin/gateway rejection." if d["role"]=="proxy" else "For mismatched origin or connection context, reject at the origin/gateway with 421 and verify the client retries on a fresh origin-specific connection. Do not weaken hostname validation.")}

def write_atomic(path,obj):
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=target.name+".",dir=target.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(obj,f,indent=2,allow_nan=False); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,target)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("topology"); ap.add_argument("--output"); a=ap.parse_args()
    try:
        report=analyze(load(a.topology))
        if a.output: write_atomic(a.output,report)
        else: print(json.dumps(report,indent=2,allow_nan=False))
        return 0 if report["safe"] else 1
    except (InputError,OSError,TypeError,ValueError) as e:
        print(f"error: {e}",file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
