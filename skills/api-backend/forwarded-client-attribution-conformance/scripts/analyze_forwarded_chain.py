#!/usr/bin/env python3
"""Offline forwarded-client attribution fixture analyzer."""
import argparse
import ipaddress
import json
import math
import sys
from pathlib import Path

MAX_BYTES = 1_000_000
MAX_RECORDS = 1000
MAX_FIELD_VALUES = 100
MAX_HOPS = 256
MODES = {"xff-cidr", "fixed-hop-count", "forwarded-cidr"}

class InputError(ValueError):
    pass

def split_quoted(value, delimiter):
    parts=[]; start=0; quoted=False; escaped=False
    for i,ch in enumerate(value):
        if escaped:
            escaped=False
        elif quoted and ch == "\\":
            escaped=True
        elif ch == '"':
            quoted=not quoted
        elif ch == delimiter and not quoted:
            parts.append(value[start:i].strip()); start=i+1
    if quoted or escaped:
        raise InputError("unterminated quoted string")
    parts.append(value[start:].strip())
    if any(not p for p in parts):
        raise InputError("empty list element")
    return parts

def unquote(value):
    if not value.startswith('"'):
        return value
    if len(value) < 2 or not value.endswith('"'):
        raise InputError("unterminated quoted value")
    out=[]; escaped=False
    for ch in value[1:-1]:
        if escaped:
            if ch not in ('"', "\\"):
                raise InputError("invalid quoted-pair")
            out.append(ch); escaped=False
        elif ch == "\\":
            escaped=True
        elif ord(ch) < 32 or ord(ch) == 127:
            raise InputError("control character in quoted value")
        else:
            out.append(ch)
    if escaped:
        raise InputError("dangling escape")
    return ''.join(out)

def parse_node(raw):
    text=unquote(raw.strip())
    if text.lower() == "unknown":
        return {"kind":"unknown","raw":text,"address":None,"port":None}
    if text.startswith("_"):
        if len(text) == 1 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in text):
            raise InputError("invalid obfuscated node")
        return {"kind":"obfuscated","raw":text,"address":None,"port":None}
    port=None; address=text
    if text.startswith("["):
        end=text.find("]")
        if end < 0:
            raise InputError("unclosed IPv6 bracket")
        address=text[1:end]
        suffix=text[end+1:]
        if suffix:
            if not suffix.startswith(":") or not suffix[1:].isdigit():
                raise InputError("invalid bracket suffix")
            port=int(suffix[1:])
    elif text.count(":") == 1:
        host, candidate=text.rsplit(":",1)
        if candidate.isdigit():
            address=host; port=int(candidate)
    if port is not None and not 1 <= port <= 65535:
        raise InputError("port out of range")
    try:
        ip=ipaddress.ip_address(address)
    except ValueError as exc:
        raise InputError("node is not an IP address") from exc
    return {"kind":"ip","raw":text,"address":str(ip),"port":port}

def field_values(record, key):
    vals=record.get(key, [])
    if not isinstance(vals, list) or any(not isinstance(x,str) for x in vals):
        raise InputError(f"{key} must be an array of strings")
    if len(vals) > MAX_FIELD_VALUES:
        raise InputError(f"too many {key} field instances")
    return vals

def parse_xff(record):
    nodes=[]
    for field in field_values(record, "x_forwarded_for"):
        for item in split_quoted(field, ','):
            nodes.append(parse_node(item))
    return nodes

def parse_forwarded(record):
    nodes=[]
    for field in field_values(record, "forwarded"):
        for element in split_quoted(field, ','):
            pairs={}
            for pair in split_quoted(element, ';'):
                if '=' not in pair:
                    raise InputError("Forwarded pair lacks equals")
                key,value=pair.split('=',1); key=key.strip().lower(); value=value.strip()
                if not key or key in pairs:
                    raise InputError("duplicate or empty Forwarded parameter")
                pairs[key]=value
            if "for" not in pairs:
                raise InputError("Forwarded element lacks for parameter")
            nodes.append(parse_node(pairs["for"]))
    return nodes

def parse_networks(record):
    vals=record.get("trusted_cidrs")
    if not isinstance(vals,list) or not vals or any(not isinstance(x,str) for x in vals):
        raise InputError("trusted_cidrs must be a non-empty array")
    try:
        return [ipaddress.ip_network(x, strict=False) for x in vals]
    except ValueError as exc:
        raise InputError("invalid trusted CIDR") from exc

def trusted(node, networks):
    if node["kind"] != "ip": return False
    ip=ipaddress.ip_address(node["address"])
    return any(ip.version == net.version and ip in net for net in networks)

def analyze(record):
    if not isinstance(record,dict): raise InputError("record must be an object")
    rid=record.get("id")
    if not isinstance(rid,str) or not rid: raise InputError("id must be a non-empty string")
    mode=record.get("mode")
    if mode not in MODES: raise InputError("unsupported mode")
    peer=parse_node(record.get("socket_peer", ""))
    if peer["kind"] != "ip": raise InputError("socket_peer must be an IP node")
    headers=parse_forwarded(record) if mode == "forwarded-cidr" else parse_xff(record)
    if len(headers) > MAX_HOPS: raise InputError("too many header hops")
    chain=[peer] + list(reversed(headers))
    result={"id":rid,"mode":mode,"status":"pass","selected_address":None,"selected_port":None,"selected_source":None,"chain_right_to_left":[n["raw"] for n in chain],"observations":[],"findings":[]}
    if mode == "fixed-hop-count":
        count=record.get("trusted_hops")
        if not isinstance(count,int) or isinstance(count,bool) or count < 0 or count > MAX_HOPS: raise InputError("trusted_hops must be an integer from 0 to 256")
        if len(headers) < count:
            result["status"]="error"; result["findings"].append({"code":"insufficient_hops","message":"fewer header nodes than declared trusted_hops"}); return result
        selected=chain[count]
        source="socket_peer" if count == 0 else f"x_forwarded_for[{len(headers)-count}]"
    else:
        networks=parse_networks(record)
        selected=None; source=None
        for index,node in enumerate(chain):
            if node["kind"] != "ip":
                result["status"]="error"; result["observations"].append({"code":f"{node['kind']}_boundary","chain_index":index}); result["findings"].append({"code":"unattributable_boundary","message":"nearest untrusted node is not an attributable IP"}); return result
            if trusted(node, networks): continue
            selected=node
            if index == 0: source="socket_peer"
            else:
                original=len(headers)-index
                source=("forwarded" if mode == "forwarded-cidr" else "x_forwarded_for")+f"[{original}]"
            break
        if selected is None:
            result["status"]="error"; result["findings"].append({"code":"all_hops_trusted","message":"no untrusted attributable client boundary"}); return result
    if selected["kind"] != "ip":
        result["status"]="error"; result["findings"].append({"code":"selected_node_not_ip","message":"selected hop is not an attributable IP"}); return result
    result["selected_address"]=selected["address"]; result["selected_port"]=selected["port"]; result["selected_source"]=source
    return result

def load(path):
    try: raw=Path(path).read_bytes()
    except OSError as exc: raise InputError(f"cannot read input: {exc}") from exc
    if len(raw)>MAX_BYTES: raise InputError("input exceeds byte limit")
    try: data=json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(InputError(f"non-finite JSON value: {x}")))
    except (json.JSONDecodeError,UnicodeDecodeError) as exc: raise InputError(f"malformed JSON: {exc}") from exc
    if not isinstance(data,dict) or set(data)-{"records"}: raise InputError("top level must contain only records")
    records=data.get("records")
    if not isinstance(records,list) or not records or len(records)>MAX_RECORDS: raise InputError("records must be a non-empty bounded array")
    return records

def write_report(report):
    try:
        sys.stdout.write(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n"); sys.stdout.flush()
    except (BrokenPipeError,OSError,UnicodeError) as exc:
        print(f"output failure: {exc}",file=sys.stderr); return 3
    return 1 if report["summary"]["error"] else 0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("fixture"); ns=ap.parse_args()
    try:
        records=load(ns.fixture); seen=set(); results=[]
        for record in records:
            rid=record.get("id") if isinstance(record,dict) else None
            if rid in seen: raise InputError("duplicate record id")
            seen.add(rid); results.append(analyze(record))
        report={"offline":True,"results":results,"summary":{"pass":sum(r["status"]=="pass" for r in results),"error":sum(r["status"]=="error" for r in results)}}
    except InputError as exc:
        print(f"input error: {exc}",file=sys.stderr); return 2
    return write_report(report)
if __name__ == "__main__": raise SystemExit(main())
