#!/usr/bin/env python3
"""Offline WebAuthn RP-ID/origin boundary preflight (standard library only)."""
from __future__ import annotations
import argparse, ipaddress, json, math, os, re, sys, tempfile
from pathlib import Path
from urllib.parse import urlsplit

APP_ORIGIN = re.compile(r"^android:apk-key-hash:[A-Za-z0-9_-]{16,}$")
DNS = re.compile(r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)
FORBIDDEN_KEYS = {"password", "cookie", "authorization", "private_key", "session_cookie", "assertion", "attestation_object"}

class InputError(ValueError): pass

def load(path: Path):
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(InputError(f"non-finite JSON number: {x}")))
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as e:
        raise InputError(str(e)) from e
    if not isinstance(data, dict): raise InputError("top level must be an object")
    return data

def scan_secrets(value, path="$" ):
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str): raise InputError(f"{path}: non-string key")
            if key.lower() in FORBIDDEN_KEYS: raise InputError(f"{path}.{key}: credential-bearing key forbidden")
            scan_secrets(item, f"{path}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value): scan_secrets(item, f"{path}[{i}]")
    elif isinstance(value, float) and not math.isfinite(value): raise InputError(f"{path}: non-finite number")

def text(data, key, required=True):
    value=data.get(key)
    if value is None and not required: return None
    if not isinstance(value,str) or not value.strip(): raise InputError(f"{key} must be a non-empty string")
    return value.strip()

def canonical_web_origin(value, allow_native=False):
    if not isinstance(value,str): raise InputError("origin must be a string")
    if allow_native and APP_ORIGIN.fullmatch(value): return value
    try: p=urlsplit(value)
    except ValueError as e: raise InputError(f"invalid origin: {e}") from e
    if p.scheme != "https" or not p.hostname or p.username is not None or p.password is not None or p.path not in ("",) or p.query or p.fragment:
        raise InputError("web origin must be an HTTPS origin without userinfo, path, query, or fragment")
    try: port=p.port
    except ValueError as e: raise InputError(f"invalid origin port: {e}") from e
    host=p.hostname.rstrip(".").lower()
    try: ipaddress.ip_address(host); raise InputError("IP-literal WebAuthn origins require an explicit environment-specific policy")
    except ValueError: pass
    if not DNS.fullmatch(host): raise InputError("invalid DNS host")
    return f"https://{host}" + (f":{port}" if port not in (None,443) else "")

def valid_dns(name, label):
    if not isinstance(name,str): raise InputError(f"{label} must be a string")
    name=name.rstrip(".").lower()
    if not DNS.fullmatch(name) or "." not in name: raise InputError(f"{label} must be a DNS name, not a URL or single label")
    return name

def suffix(host, parent): return host == parent or host.endswith("."+parent)

def analyze(data):
    scan_secrets(data)
    if data.get("kind") != "webauthn":
        return {"schema_version":1,"classification":"not_applicable","findings":[],"observations":["kind is not webauthn"]}
    public=canonical_web_origin(text(data,"public_origin")); host=urlsplit(public).hostname
    rp=valid_dns(text(data,"rp_id"),"rp_id")
    public_suffix=text(data,"public_suffix").rstrip(".").lower()
    if not DNS.fullmatch(public_suffix): raise InputError("public_suffix must be an audited DNS suffix")
    findings=[]; observations=[]
    def finding(code, detail): findings.append({"code":code,"detail":detail})
    if rp == public_suffix or not suffix(rp, public_suffix): finding("rp_id_public_suffix_boundary","RP ID must be above the audited public suffix boundary")
    if not suffix(host,rp): finding("rp_id_origin_scope_mismatch","public origin host is neither RP ID nor its subdomain")
    ceremony=data.get("ceremony")
    if not isinstance(ceremony,dict): raise InputError("ceremony must be an object")
    for phase in ("registration","authentication"):
        item=ceremony.get(phase)
        if not isinstance(item,dict): raise InputError(f"ceremony.{phase} must be an object")
        origin=canonical_web_origin(item.get("origin")); phase_rp=valid_dns(item.get("rp_id"),f"ceremony.{phase}.rp_id")
        if origin != public: finding(f"{phase}_origin_mismatch",f"{origin} != {public}")
        if phase_rp != rp: finding(f"{phase}_rp_id_mismatch",f"{phase_rp} != {rp}")
    reg=ceremony["registration"]; auth=ceremony["authentication"]
    if canonical_web_origin(reg["origin"]) != canonical_web_origin(auth["origin"]) or reg["rp_id"].rstrip(".").lower()!=auth["rp_id"].rstrip(".").lower():
        finding("ceremony_parity_mismatch","registration and authentication boundaries differ")
    allowed=data.get("allowed_origins",[])
    if not isinstance(allowed,list): raise InputError("allowed_origins must be an array")
    canonical=[]
    for value in allowed:
        origin=canonical_web_origin(value, allow_native=True)
        if origin in canonical: finding("duplicate_allowed_origin",origin)
        canonical.append(origin)
    if public not in canonical: finding("public_origin_not_allowed",public)
    native=[x for x in canonical if x.startswith("android:")]
    if native: observations.append("explicit_native_app_origin_present")
    proxy=data.get("proxy",{})
    if not isinstance(proxy,dict): raise InputError("proxy must be an object")
    if proxy.get("derive_from_forwarded") is True:
        observations.append("forwarded_origin_derivation_enabled")
        trusted_hops=proxy.get("trusted_hop_count"); observed_hops=proxy.get("observed_hop_count")
        counts_valid=(isinstance(trusted_hops,int) and not isinstance(trusted_hops,bool) and trusted_hops>0 and
                      isinstance(observed_hops,int) and not isinstance(observed_hops,bool) and observed_hops>0 and
                      trusted_hops == observed_hops)
        required={"direct_peer_trusted":True,"edge_strips_client_forwarded":True,"headers_agree":True}
        for key,want in required.items():
            if proxy.get(key) != want: finding("ambiguous_proxy_trust",f"proxy.{key} does not satisfy fail-closed trust invariant")
        if not counts_valid: finding("ambiguous_proxy_trust","trusted and observed hop counts must be matching positive integers")
        forwarded=proxy.get("forwarded_origin")
        if forwarded is None: finding("forwarded_origin_missing","derived mode requires a canonical forwarded origin")
        elif canonical_web_origin(forwarded) != public: finding("forwarded_origin_mismatch","trusted proxy origin differs from configured public origin")
    credential_ids=data.get("credential_rp_ids",[])
    if not isinstance(credential_ids,list): raise InputError("credential_rp_ids must be an array")
    for old in credential_ids:
        old=valid_dns(old,"credential_rp_ids[]")
        if old != rp: finding("credential_reenrollment_required",f"credential bound to {old} cannot authenticate under {rp}")
    return {"schema_version":1,"classification":"blocked" if findings else "ready","canonical":{"public_origin":public,"rp_id":rp,"public_suffix":public_suffix,"allowed_origins":canonical},"findings":findings,"observations":observations}

def write_atomic(path, result):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(result,f,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("input",type=Path); ap.add_argument("--output",type=Path); args=ap.parse_args(argv)
    try:
        result=analyze(load(args.input))
        payload=json.dumps(result,indent=2,sort_keys=True)+"\n"
        if args.output: write_atomic(args.output,result)
        else: sys.stdout.write(payload)
        return 1 if result["classification"]=="blocked" else 0
    except (InputError,OSError,TypeError,KeyError) as e:
        sys.stderr.write(json.dumps({"classification":"input_error","error":str(e)})+"\n"); return 2
if __name__=="__main__": raise SystemExit(main())
