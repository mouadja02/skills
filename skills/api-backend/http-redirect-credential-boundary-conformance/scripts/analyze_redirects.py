#!/usr/bin/env python3
"""Offline analyzer for redacted HTTP redirect hop transcripts."""
import argparse
import json
import re
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit

TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
REDIRECTS = {301, 302, 303, 307, 308}

class InputError(ValueError):
    pass

def require_dict(value, label):
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    return value

def header_names(value, label):
    if not isinstance(value, list):
        raise InputError(f"{label} must be an array of header-name strings")
    out = []
    for item in value:
        if not isinstance(item, str) or not TOKEN.fullmatch(item):
            raise InputError(f"{label} contains an invalid header name")
        name = item.lower()
        if name in out:
            raise InputError(f"{label} contains a duplicate header name")
        out.append(name)
    return out

def normalized_url(value, label):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise InputError(f"{label} must be a non-empty URL without controls")
    try:
        p = urlsplit(value)
        port = p.port
    except ValueError as exc:
        raise InputError(f"{label} is malformed: {exc}") from exc
    scheme = p.scheme.lower()
    if scheme not in ("http", "https") or not p.hostname:
        raise InputError(f"{label} must be an absolute HTTP(S) URL")
    if p.username is not None or p.password is not None:
        raise InputError(f"{label} must not contain userinfo")
    if p.fragment:
        raise InputError(f"{label} must not contain a fragment")
    try:
        host = p.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise InputError(f"{label} has an invalid hostname") from exc
    effective = port if port is not None else (443 if scheme == "https" else 80)
    if not 1 <= effective <= 65535:
        raise InputError(f"{label} has an invalid port")
    display_host = f"[{host}]" if ":" in host else host
    default_port = 443 if scheme == "https" else 80
    netloc = display_host if port is None or port == default_port else f"{display_host}:{port}"
    path = p.path or "/"
    return urlunsplit((scheme, netloc, path, p.query, "")), (scheme, host, effective)

def expected_method(status, method):
    if status == 303 and method != "HEAD":
        return "GET"
    if status in (301, 302) and method == "POST":
        return "GET"
    return method

def analyze(document):
    root = require_dict(document, "document")
    allowed = {"credential_headers", "hops"}
    if set(root) - allowed:
        raise InputError("document contains unknown fields")
    credentials = header_names(root.get("credential_headers"), "credential_headers")
    for standard in ("authorization", "cookie", "proxy-authorization"):
        if standard not in credentials:
            credentials.append(standard)
    hops = root.get("hops")
    if not isinstance(hops, list) or not hops:
        raise InputError("hops must be a non-empty array")
    parsed = []
    for index, raw in enumerate(hops):
        hop = require_dict(raw, f"hops[{index}]")
        if set(hop) - {"request", "response"}:
            raise InputError(f"hops[{index}] contains unknown fields")
        req = require_dict(hop.get("request"), f"hops[{index}].request")
        if set(req) != {"url", "method", "headers"}:
            raise InputError(f"hops[{index}].request fields must be url, method, headers")
        url, origin = normalized_url(req["url"], f"hops[{index}].request.url")
        method = req["method"]
        if not isinstance(method, str) or not TOKEN.fullmatch(method) or method != method.upper():
            raise InputError(f"hops[{index}].request.method must be an uppercase token")
        headers = header_names(req["headers"], f"hops[{index}].request.headers")
        res = require_dict(hop.get("response"), f"hops[{index}].response")
        if set(res) - {"status", "location"} or "status" not in res:
            raise InputError(f"hops[{index}].response has invalid fields")
        status = res["status"]
        if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
            raise InputError(f"hops[{index}].response.status must be an HTTP status integer")
        location = res.get("location")
        if status in REDIRECTS and index < len(hops) - 1:
            if not isinstance(location, str) or not location:
                raise InputError(f"hops[{index}] redirect requires Location")
        elif location is not None and not isinstance(location, str):
            raise InputError(f"hops[{index}].response.location must be a string")
        parsed.append((url, origin, method, headers, status, location))
    findings, observations, transitions = [], [], []
    for i in range(len(parsed) - 1):
        url, origin, method, headers, status, location = parsed[i]
        nurl, norigin, nmethod, nheaders, _, _ = parsed[i + 1]
        if status not in REDIRECTS:
            findings.append({"code":"UNEXPECTED_FOLLOWUP_AFTER_NON_REDIRECT","transition":i})
            continue
        try:
            joined = urlsplit(urljoin(url, location))
            request_target = urlunsplit((joined.scheme, joined.netloc, joined.path, joined.query, ""))
            target, target_origin = normalized_url(request_target, f"hops[{i}].response.location")
        except InputError as exc:
            raise InputError(str(exc)) from exc
        same = origin == target_origin
        downgrade = origin[0] == "https" and target_origin[0] == "http"
        expected = expected_method(status, method)
        present_before = sorted(set(headers) & set(credentials))
        present_after = sorted(set(nheaders) & set(credentials))
        action = "forward" if same and not downgrade else "strip"
        transitions.append({"index":i,"from":url,"to":target,"same_origin":same,"downgrade":downgrade,"expected_method":expected,"observed_method":nmethod,"credential_action":action,"credential_headers_before":present_before,"credential_headers_after":present_after})
        if nurl != target:
            findings.append({"code":"NEXT_URL_MISMATCH","transition":i})
        if nmethod != expected:
            findings.append({"code":"REDIRECT_METHOD_MISMATCH","transition":i})
        leaked = sorted(set(present_after) & set(present_before))
        if leaked and (not same or downgrade):
            code = "CREDENTIAL_FORWARDED_ON_DOWNGRADE" if downgrade else "CREDENTIAL_FORWARDED_CROSS_ORIGIN"
            findings.append({"code":code,"transition":i,"headers":leaked})
        introduced = sorted(set(present_after) - set(present_before))
        if introduced:
            findings.append({"code":"CREDENTIAL_INTRODUCED_ON_REDIRECT","transition":i,"headers":introduced})
        stripped = sorted(set(present_before) - set(present_after))
        if stripped and same and not downgrade:
            observations.append({"code":"CREDENTIAL_STRIPPED_SAME_ORIGIN","transition":i,"headers":stripped})
    return {"schema_version":1,"credential_inventory":sorted(credentials),"transition_count":len(transitions),"finding_count":len(findings),"findings":findings,"observations":observations,"transitions":transitions}

def emit(payload):
    try:
        sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        return 3
    return None

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args(argv)
    try:
        with open(args.input, "r", encoding="utf-8") as handle:
            doc = json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"non-finite JSON value: {value}")))
        report = analyze(doc)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        status = emit({"schema_version":1,"error":{"code":"INVALID_INPUT","message":str(exc)}})
        return 3 if status == 3 else 2
    status = emit(report)
    if status == 3:
        return 3
    return 1 if report["finding_count"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
