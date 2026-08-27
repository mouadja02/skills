#!/usr/bin/env python3
"""Offline scoped-IPv6 boundary preflight. No DNS, interface, or network access."""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes

MAX_INPUT = 4096
ZONE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
PORT_RE = re.compile(r"^[0-9]{1,5}$")
HEX_ESCAPE_RE = re.compile(r"%[0-9A-Fa-f]{2}")
MODES = {"ui", "uri", "socket"}


class InputError(ValueError):
    pass


def finding(code: str, severity: str, detail: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "detail": detail}


def has_control(text: str) -> bool:
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in text)


def decode_zone_once(raw: str) -> str:
    try:
        decoded = unquote_to_bytes(raw).decode("utf-8", "strict")
    except (UnicodeDecodeError, ValueError) as exc:
        raise InputError("zone has malformed percent encoding or invalid UTF-8") from exc
    return decoded


def split_ui(value: str) -> tuple[str, str | None, int | None]:
    if "://" in value:
        raise InputError("UI mode does not accept a URI")
    port = None
    host = value
    if value.startswith("["):
        close = value.find("]")
        if close < 0:
            raise InputError("missing closing bracket")
        host = value[1:close]
        suffix = value[close + 1 :]
        if suffix:
            if not suffix.startswith(":") or not PORT_RE.fullmatch(suffix[1:]):
                raise InputError("unexpected text after closing bracket")
            port = int(suffix[1:])
    elif "]" in value or "[" in value:
        raise InputError("unbalanced bracket")
    if "%" not in host:
        return host, None, port
    address, zone = host.split("%", 1)
    return address, zone, port


def split_uri(value: str) -> tuple[str, str | None, int | None, list[dict[str, str]]]:
    notes: list[dict[str, str]] = []
    scheme_sep = value.find("://")
    if scheme_sep <= 0:
        raise InputError("URI requires an explicit scheme and authority")
    authority_rest = value[scheme_sep + 3 :]
    authority = re.split(r"[/#?]", authority_rest, maxsplit=1)[0]
    if "@" in authority:
        raise InputError("userinfo is not accepted")
    if not authority.startswith("["):
        raise InputError("IPv6 URI host must be bracketed")
    close = authority.find("]")
    if close < 0:
        raise InputError("missing closing bracket")
    inside = authority[1:close]
    suffix = authority[close + 1 :]
    port = None
    if suffix:
        if not suffix.startswith(":") or not PORT_RE.fullmatch(suffix[1:]):
            raise InputError("unexpected text after closing bracket")
        port = int(suffix[1:])
    if "%" not in inside:
        return inside, None, port, notes
    match = re.search(r"%25", inside, re.IGNORECASE)
    if not match:
        raise InputError("raw or malformed percent delimiter in URI host")
    address = inside[: match.start()]
    raw_zone = inside[match.end() :]
    if "%" in address:
        raise InputError("ambiguous percent delimiter before zone")
    if re.search(r"%(?![0-9A-Fa-f]{2})", raw_zone):
        raise InputError("malformed percent encoding in zone")
    zone = decode_zone_once(raw_zone)
    notes.append(finding("obsolete_uri_extension", "warning", "RFC 9844 obsoletes RFC 6874; treat %25 zone syntax as an observed parser extension, not portable generic URI syntax"))
    if inside.lower().find("%2525") >= 0:
        notes.append(finding("possible_double_encoding", "warning", "decoded exactly once; the remaining '25' prefix was not recursively decoded"))
    return address, zone, port, notes


def address_supports_zone(addr: ipaddress.IPv6Address) -> bool:
    return addr.is_link_local or addr.is_multicast


def inspect_record(record: Any, max_zone_length: int) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise InputError("each record must be an object")
    allowed = {"id", "mode", "input", "known_zones"}
    extra = sorted(set(record) - allowed)
    if extra:
        raise InputError(f"unknown record fields: {', '.join(extra)}")
    rid, mode, value = record.get("id"), record.get("mode"), record.get("input")
    if not isinstance(rid, str) or not rid or has_control(rid):
        raise InputError("id must be a non-empty control-free string")
    if mode not in MODES:
        raise InputError("mode must be ui, uri, or socket")
    if not isinstance(value, str) or not value or len(value) > MAX_INPUT:
        raise InputError(f"input must be a non-empty string of at most {MAX_INPUT} characters")
    known = record.get("known_zones")
    if known is not None and (not isinstance(known, list) or any(not isinstance(x, str) for x in known)):
        raise InputError("known_zones must be an array of strings")

    notes: list[dict[str, str]] = []
    try:
        if mode == "uri":
            address_text, zone, port, uri_notes = split_uri(value)
            notes.extend(uri_notes)
        else:
            address_text, zone, port = split_ui(value)
        if port is not None and not 1 <= port <= 65535:
            raise InputError("port is outside 1..65535")
        try:
            addr = ipaddress.IPv6Address(address_text)
        except ValueError as exc:
            raise InputError("address is not a valid IPv6 literal") from exc
        result: dict[str, Any] = {
            "id": rid,
            "mode": mode,
            "status": "ok",
            "address": addr.compressed,
            "zone": zone,
            "port": port,
            "findings": notes,
        }
        if zone is None:
            if address_supports_zone(addr):
                result["findings"].append(finding("zone_absent", "observation", "scoped address has no zone; routing may be ambiguous, but no lookup was attempted"))
            else:
                result["status"] = "not_applicable"
                result["findings"].append(finding("no_scoped_zone", "observation", "ordinary IPv6 input; scoped-zone workflow should not activate"))
            return result
        if not zone:
            raise InputError("zone identifier is empty")
        if len(zone) > max_zone_length:
            raise InputError("zone identifier exceeds configured length limit")
        if has_control(zone):
            raise InputError("zone identifier contains a control character")
        if not ZONE_RE.fullmatch(zone):
            raise InputError("zone identifier contains characters outside the conservative portable policy")
        if not address_supports_zone(addr):
            result["status"] = "error"
            result["findings"].append(finding("zone_on_unscoped_address", "error", "zone is accepted only for link-local or multicast addresses by this conservative policy"))
            return result
        if known is None:
            result["status"] = "warning"
            result["findings"].append(finding("interface_lookup_not_run", "warning", "supply a redacted known_zones inventory or perform an explicit local lookup before connecting"))
        elif zone not in known:
            result["status"] = "error"
            result["findings"].append(finding("unknown_local_zone", "error", "zone was not found in the supplied local inventory"))
        else:
            result["findings"].append(finding("known_local_zone", "observation", "zone matched the supplied local inventory; no network call was made"))
        result["findings"].append(finding("local_only_zone", "observation", "keep the zone as local socket metadata; it is not part of the 128-bit IPv6 wire address"))
        return result
    except InputError as exc:
        return {"id": rid, "mode": mode, "status": "error", "address": None, "zone": None, "port": None, "findings": [finding("invalid_input", "error", str(exc))]}


def load_payload(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read input: {exc}") from exc
    try:
        payload = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"non-standard JSON constant: {value}")))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InputError(f"malformed JSON: {exc}") from exc
    if not isinstance(payload, dict) or set(payload) - {"records", "max_zone_length"}:
        raise InputError("top level must contain only records and optional max_zone_length")
    records = payload.get("records")
    if not isinstance(records, list):
        raise InputError("records must be an array")
    limit = payload.get("max_zone_length", 64)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 255:
        raise InputError("max_zone_length must be an integer from 1 to 255")
    return {"records": records, "max_zone_length": limit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON fixture or redacted inventory")
    args = parser.parse_args()
    try:
        payload = load_payload(args.input)
        seen: set[str] = set()
        results = []
        for record in payload["records"]:
            result = inspect_record(record, payload["max_zone_length"])
            if result["id"] in seen:
                raise InputError(f"duplicate id: {result['id']}")
            seen.add(result["id"])
            results.append(result)
        document = {"schema_version": 1, "offline": True, "records": results}
        try:
            json.dump(document, sys.stdout, indent=2, sort_keys=True, allow_nan=False)
            sys.stdout.write("\n")
            sys.stdout.flush()
        except (BrokenPipeError, OSError, ValueError):
            # Prevent a second buffered flush during interpreter shutdown from
            # replacing the documented output-failure exit status.
            try:
                sink = os.open(os.devnull, os.O_WRONLY)
                os.dup2(sink, sys.stdout.fileno())
                os.close(sink)
            except OSError:
                pass
            return 3
        return 1 if any(r["status"] == "error" for r in results) else 0
    except InputError as exc:
        try:
            json.dump({"schema_version": 1, "offline": True, "error": str(exc)}, sys.stderr, sort_keys=True)
            sys.stderr.write("\n")
            sys.stderr.flush()
        except (BrokenPipeError, OSError):
            return 3
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
