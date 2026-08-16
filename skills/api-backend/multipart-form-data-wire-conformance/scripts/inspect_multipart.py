#!/usr/bin/env python3
"""Offline, fail-closed multipart/form-data wire inspector."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

TOKEN = re.compile(rb"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
BCHARS = set(b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'()+_,-./:=? ")
DEFAULT_LIMITS = {"max_body_bytes": 8_388_608, "max_parts": 100, "max_headers_per_part": 50, "max_header_bytes": 16_384}
LIMIT_KEYS = frozenset(DEFAULT_LIMITS)

class InputError(ValueError):
    pass

def split_semicolons(value: str) -> list[str]:
    pieces, current, quoted, escaped = [], [], False, False
    for ch in value:
        if escaped:
            current.append(ch); escaped = False
        elif ch == "\\" and quoted:
            current.append(ch); escaped = True
        elif ch == '"':
            current.append(ch); quoted = not quoted
        elif ch == ";" and not quoted:
            pieces.append("".join(current).strip()); current = []
        else:
            current.append(ch)
    if quoted or escaped:
        raise InputError("unterminated quoted parameter")
    pieces.append("".join(current).strip())
    return pieces

def unquote(value: str) -> str:
    if not value.startswith('"'):
        if '"' in value:
            raise InputError("malformed quoted parameter")
        return value
    if len(value) < 2 or not value.endswith('"'):
        raise InputError("unterminated quoted parameter")
    out, escaped = [], False
    for ch in value[1:-1]:
        if escaped:
            out.append(ch); escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            raise InputError("unescaped quote in parameter")
        else:
            out.append(ch)
    if escaped:
        raise InputError("dangling quoted-pair")
    return "".join(out)

def parse_parameterized(value: str) -> tuple[str, list[tuple[str, str]]]:
    pieces = split_semicolons(value)
    if not pieces or not pieces[0]:
        raise InputError("missing primary value")
    params = []
    for item in pieces[1:]:
        if not item or "=" not in item:
            raise InputError("malformed parameter")
        name, raw = item.split("=", 1)
        name = name.strip().lower(); raw = raw.strip()
        if not name or not TOKEN.fullmatch(name.encode("ascii", "strict")) or raw == "":
            raise InputError("malformed parameter")
        params.append((name, unquote(raw)))
    return pieces[0].strip().lower(), params

def finding(code: str, location: str, detail: str) -> dict[str, str]:
    return {"code": code, "location": location, "detail": detail}

def parse_limits(raw: Any) -> dict[str, int]:
    limits = dict(DEFAULT_LIMITS)
    if raw is None:
        return limits
    if not isinstance(raw, dict) or not set(raw).issubset(LIMIT_KEYS):
        raise InputError("limits must be an object containing only supported keys")
    for key, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 1_000_000_000:
            raise InputError(f"{key} must be an integer from 1 through 1000000000")
        limits[key] = value
    return limits

def parse_content_type(value: Any) -> tuple[bool, bytes | None, list[dict[str, str]]]:
    violations = []
    if not isinstance(value, str):
        raise InputError("content_type must be a string")
    try:
        media, params = parse_parameterized(value)
    except (InputError, UnicodeError) as exc:
        return True, None, [finding("content-type-malformed", "content-type", str(exc))]
    if media != "multipart/form-data":
        return False, None, []
    boundaries = [v for k, v in params if k == "boundary"]
    if len(boundaries) != 1:
        violations.append(finding("boundary-parameter-count", "content-type", "exactly one boundary parameter is required"))
        return True, None, violations
    try:
        boundary = boundaries[0].encode("ascii", "strict")
    except UnicodeError:
        violations.append(finding("boundary-invalid", "content-type", "boundary must be ASCII")); return True, None, violations
    if not 1 <= len(boundary) <= 70 or boundary[-1:] == b" " or any(ch not in BCHARS for ch in boundary):
        violations.append(finding("boundary-invalid", "content-type", "boundary must satisfy RFC 2046 length and character constraints")); return True, None, violations
    return True, boundary, violations

def delimiter_lines(body: bytes, boundary: bytes) -> tuple[list[tuple[int, int, bool]], list[int]]:
    marker = b"--" + boundary
    valid, malformed = [], []
    pos = 0
    while True:
        pos = body.find(marker, pos)
        if pos < 0:
            break
        if pos != 0 and body[pos-2:pos] != b"\r\n":
            pos += 1; continue
        line_end = body.find(b"\r\n", pos)
        eof = line_end < 0
        raw = body[pos:] if eof else body[pos:line_end]
        suffix = raw[len(marker):]
        closing = suffix.startswith(b"--")
        padding = suffix[2:] if closing else suffix
        if (not closing or not suffix.startswith(b"---")) and all(ch in (9, 32) for ch in padding):
            if not closing and eof:
                malformed.append(pos)
            else:
                valid.append((pos, len(body) if eof else line_end + 2, closing))
        else:
            malformed.append(pos)
        pos += len(marker)
    return valid, malformed

def parse_disposition(value: bytes, part_index: int, violations: list[dict[str, str]]) -> tuple[str | None, str | None]:
    loc = f"part[{part_index}].content-disposition"
    try:
        text = value.decode("latin-1")
        kind, params = parse_parameterized(text)
    except (InputError, UnicodeError) as exc:
        violations.append(finding("disposition-malformed", loc, str(exc))); return None, None
    if kind != "form-data":
        violations.append(finding("disposition-not-form-data", loc, "disposition must be form-data"))
    grouped: dict[str, list[str]] = {}
    for key, val in params:
        grouped.setdefault(key, []).append(val)
    for key, values in grouped.items():
        if len(values) > 1:
            violations.append(finding("disposition-parameter-duplicate", loc, f"parameter {key!r} occurs {len(values)} times"))
    if "name*" in grouped:
        violations.append(finding("disposition-extended-name", loc, "name* is not the RFC 7578 field-name parameter and is ambiguous across parsers"))
    if "filename*" in grouped:
        violations.append(finding("disposition-extended-filename", loc, "RFC 7578 forbids filename* in multipart/form-data"))
    name = grouped.get("name", [None])[0]
    filename = grouped.get("filename", [None])[0]
    if name is None or name == "":
        violations.append(finding("disposition-name-missing", loc, "a non-empty name parameter is required"))
    return name, filename

def parse_part(blob: bytes, index: int, limits: dict[str, int], violations: list[dict[str, str]]) -> dict[str, Any]:
    loc = f"part[{index}]"
    sep = blob.find(b"\r\n\r\n")
    if sep < 0:
        violations.append(finding("part-header-terminator-missing", loc, "part lacks CRLF CRLF header terminator")); headers_blob, payload = blob, b""
    else:
        headers_blob, payload = blob[:sep], blob[sep+4:]
    if len(headers_blob) > limits["max_header_bytes"]:
        violations.append(finding("part-headers-too-large", loc, "part header bytes exceed configured limit"))
    lines = headers_blob.split(b"\r\n") if headers_blob else []
    if len(lines) > limits["max_headers_per_part"]:
        violations.append(finding("part-header-count-exceeded", loc, "part header count exceeds configured limit"))
    headers: dict[bytes, list[bytes]] = {}
    for line_no, line in enumerate(lines):
        hloc = f"{loc}.header[{line_no}]"
        if line[:1] in (b" ", b"\t"):
            violations.append(finding("part-header-obs-fold", hloc, "folded headers are rejected")); continue
        if b":" not in line:
            violations.append(finding("part-header-malformed", hloc, "header line lacks colon")); continue
        name, value = line.split(b":", 1); lname = name.lower()
        if not TOKEN.fullmatch(name):
            violations.append(finding("part-header-name-invalid", hloc, "header name is not an HTTP token")); continue
        if any(ch == 127 or (ch < 32 and ch != 9) for ch in value):
            violations.append(finding("part-header-value-invalid", hloc, "header value contains a forbidden control")); continue
        headers.setdefault(lname, []).append(value.strip(b" \t"))
    cds = headers.get(b"content-disposition", [])
    if len(cds) != 1:
        violations.append(finding("content-disposition-count", loc, "exactly one Content-Disposition header is required")); name = filename = None
    else:
        name, filename = parse_disposition(cds[0], index, violations)
    cts = headers.get(b"content-type", [])
    if len(cts) > 1:
        violations.append(finding("part-content-type-duplicate", loc, "at most one Content-Type header is allowed"))
    content_type = cts[0].decode("latin-1") if len(cts) == 1 else None
    return {"index": index, "name": name, "filename": filename, "content_type": content_type, "body_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "header_names": sorted(k.decode("ascii") for k in headers)}

def inspect(content_type: Any, body: bytes, limits_raw: Any = None) -> dict[str, Any]:
    limits = parse_limits(limits_raw)
    applicable, boundary, violations = parse_content_type(content_type)
    result: dict[str, Any] = {"applicable": applicable, "valid": False, "violations": violations, "boundary": boundary.decode("ascii") if boundary else None, "body_bytes": len(body), "preamble_bytes": 0, "epilogue_bytes": 0, "closing_boundary": False, "parts": []}
    if not applicable or boundary is None:
        return result
    if len(body) > limits["max_body_bytes"]:
        violations.append(finding("body-too-large", "body", "body bytes exceed configured limit")); return result
    delimiters, malformed = delimiter_lines(body, boundary)
    for pos in malformed:
        violations.append(finding("boundary-line-malformed", f"body[{pos}]", "boundary marker has an invalid suffix or missing CRLF"))
    if not delimiters:
        violations.append(finding("opening-boundary-missing", "body", "no valid opening boundary line matches Content-Type")); return result
    if delimiters[0][2]:
        violations.append(finding("opening-boundary-missing", "body", "first delimiter is a closing boundary")); return result
    result["preamble_bytes"] = delimiters[0][0]
    for i, (start, content_start, closing) in enumerate(delimiters):
        if closing:
            if i == 0:
                continue
            result["closing_boundary"] = True
            result["epilogue_bytes"] = len(body) - content_start
            if i != len(delimiters) - 1:
                violations.append(finding("delimiter-after-close", f"body[{start}]", "a delimiter appears after the closing boundary"))
            break
        if i + 1 >= len(delimiters):
            violations.append(finding("closing-boundary-missing", "body", "multipart body has no closing boundary")); break
        next_start = delimiters[i+1][0]
        framed = body[content_start:next_start]
        if not framed.endswith(b"\r\n"):
            violations.append(finding("delimiter-prefix-crlf-missing", f"body[{next_start}]", "delimiter must be preceded by CRLF")); blob = framed
        else:
            blob = framed[:-2]
        if len(result["parts"]) >= limits["max_parts"]:
            violations.append(finding("part-count-exceeded", "body", "part count exceeds configured limit")); break
        result["parts"].append(parse_part(blob, len(result["parts"]), limits, violations))
    if not result["closing_boundary"] and not any(v["code"] == "closing-boundary-missing" for v in violations):
        violations.append(finding("closing-boundary-missing", "body", "multipart body has no closing boundary"))
    if not result["parts"]:
        violations.append(finding("part-count-zero", "body", "at least one part is required"))
    result["valid"] = not violations
    return result

def strict_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read case file: {exc}") from exc
    try:
        value = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(InputError(f"non-standard JSON constant {x}")))
    except (json.JSONDecodeError, InputError) as exc:
        raise InputError(f"invalid case JSON: {exc}") from exc
    if not isinstance(value, dict) or not set(value).issubset({"content_type", "body_base64", "limits"}) or not {"content_type", "body_base64"}.issubset(value):
        raise InputError("case must contain content_type and body_base64, plus optional limits only")
    if not isinstance(value["body_base64"], str):
        raise InputError("body_base64 must be a string")
    return value

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", type=Path, help="JSON object with content_type and body_base64")
    group.add_argument("--content-type", help="Content-Type for a raw body file")
    parser.add_argument("body", nargs="?", type=Path, help="raw body file with --content-type")
    args = parser.parse_args(argv)
    try:
        if args.case:
            case = strict_json(args.case)
            try:
                body = base64.b64decode(case["body_base64"], validate=True)
            except (binascii.Error, ValueError) as exc:
                raise InputError(f"body_base64 is invalid: {exc}") from exc
            report = inspect(case["content_type"], body, case.get("limits"))
        else:
            if args.body is None:
                raise InputError("a body file is required with --content-type")
            try:
                body = args.body.read_bytes()
            except OSError as exc:
                raise InputError(f"cannot read body file: {exc}") from exc
            report = inspect(args.content_type, body)
    except (InputError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True)); return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (not report["applicable"] or report["valid"]) else 1

if __name__ == "__main__":
    sys.exit(main())
