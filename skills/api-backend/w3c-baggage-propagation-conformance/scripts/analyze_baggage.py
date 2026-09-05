#!/usr/bin/env python3
"""Offline W3C Baggage parser and propagation-transition analyzer."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

TOKEN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
HEX = set("0123456789abcdefABCDEF")
ALLOWED_VALUE = {chr(i) for i in list(range(0x21, 0x22)) + list(range(0x23, 0x2C)) + list(range(0x2D, 0x3B)) + list(range(0x3C, 0x5C)) + list(range(0x5D, 0x7F))}


class InputError(Exception):
    pass


def decode_value(raw):
    data = bytearray()
    i = 0
    while i < len(raw):
        char = raw[i]
        if char == "%":
            if i + 2 >= len(raw) or raw[i + 1] not in HEX or raw[i + 2] not in HEX:
                raise ValueError("percent_sign_not_encoded")
            data.append(int(raw[i + 1:i + 3], 16))
            i += 3
            continue
        if char not in ALLOWED_VALUE or ord(char) > 0x7f:
            raise ValueError("character_outside_baggage_octet")
        data.append(ord(char))
        i += 1
    return data.decode("utf-8", errors="replace")


def encode_value(value):
    # W3C baggage-octet excluding '%' because literal percent MUST be encoded.
    return quote(value, safe="!#$&'()*+-./:<>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~0123456789")


def parse_member(raw, index):
    pieces = raw.split(";")
    pair = pieces[0].strip(" \t")
    if "=" not in pair:
        raise ValueError("missing_key_value_separator")
    key, value = pair.split("=", 1)
    key, value = key.strip(" \t"), value.strip(" \t")
    if not key or not TOKEN.fullmatch(key):
        raise ValueError("invalid_key")
    decoded = decode_value(value)
    properties = []
    for raw_property in pieces[1:]:
        prop = raw_property.strip(" \t")
        if not prop:
            raise ValueError("empty_property")
        if "=" in prop:
            prop_key, prop_value = prop.split("=", 1)
            prop_key, prop_value = prop_key.strip(" \t"), prop_value.strip(" \t")
            if not TOKEN.fullmatch(prop_key):
                raise ValueError("invalid_property_key")
            # Property values use value grammar but remain opaque: validate, do not decode/rewrite.
            decode_value(prop_value)
            properties.append({"key": prop_key, "raw_value": prop_value})
        else:
            if not TOKEN.fullmatch(prop):
                raise ValueError("invalid_property_key")
            properties.append({"key": prop, "raw_value": None})
    canonical = key + "=" + encode_value(decoded)
    for prop in properties:
        canonical += ";" + prop["key"]
        if prop["raw_value"] is not None:
            canonical += "=" + prop["raw_value"]
    return {"index": index, "key": key, "raw_value": value, "decoded_value": decoded,
            "properties": properties, "canonical": canonical}


def parse_fields(fields):
    if not isinstance(fields, list) or not fields or not all(isinstance(v, str) for v in fields):
        raise InputError("received_fields must be a non-empty array of strings")
    combined = ",".join(fields)
    members, findings = [], []
    for index, raw in enumerate(combined.split(",")):
        try:
            members.append(parse_member(raw, index))
        except ValueError as exc:
            findings.append({"code": "invalid_list_member", "index": index, "reason": str(exc)})
    return combined, members, findings


def identity(member):
    return (member["key"], member["decoded_value"],
            tuple((p["key"], p["raw_value"]) for p in member["properties"]))


def analyze(document):
    if not isinstance(document, dict):
        raise InputError("top-level JSON value must be an object")
    if document.get("kind") != "w3c_baggage_trace":
        return {"classification": "not_applicable", "findings": [], "observations": []}
    unknown = set(document) - {"kind", "received_fields", "forwarded_fields", "declared_mutated_indexes"}
    if unknown:
        raise InputError("unknown top-level fields: " + ", ".join(sorted(unknown)))
    combined, members, findings = parse_fields(document.get("received_fields"))
    observations = [{"code": "combined_limits", "member_count": len(combined.split(",")),
                     "combined_bytes": len(combined.encode("utf-8")),
                     "within_64_members": len(combined.split(",")) <= 64,
                     "within_8192_bytes": len(combined.encode("utf-8")) <= 8192}]
    declared = document.get("declared_mutated_indexes", [])
    if not isinstance(declared, list) or not all(type(v) is int and v >= 0 for v in declared):
        raise InputError("declared_mutated_indexes must be an array of non-negative integers")
    if any(index >= len(combined.split(",")) for index in declared):
        raise InputError("declared_mutated_indexes contains an out-of-range index")
    if "forwarded_fields" in document:
        _, forwarded, forwarded_findings = parse_fields(document["forwarded_fields"])
        findings.extend({**item, "stage": "forwarded"} for item in forwarded_findings)
        available = [identity(member) for member in forwarded]
        if observations[0]["within_64_members"] and observations[0]["within_8192_bytes"]:
            for member in members:
                if member["index"] in declared:
                    continue
                ident = identity(member)
                if ident in available:
                    available.remove(ident)
                else:
                    findings.append({"code": "undeclared_member_loss_under_limits", "index": member["index"]})
        observations.append({"code": "forwarded_member_count", "count": len(forwarded)})
    return {"classification": "blocked" if findings else "ready", "findings": findings,
            "observations": observations, "members": members}


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise InputError(f"cannot parse input: {exc}") from exc


def emit(result):
    try:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
        sys.stdout.flush()
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot write output: {exc}") from exc


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: analyze_baggage.py TRACE.json", file=sys.stderr)
        return 2
    try:
        result = analyze(load(args[0]))
        emit(result)
    except InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    return 1 if result["classification"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())