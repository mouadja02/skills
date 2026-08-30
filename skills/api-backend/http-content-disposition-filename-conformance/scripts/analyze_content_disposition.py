#!/usr/bin/env python3
"""Offline Content-Disposition filename parser and safety-policy analyzer."""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import unquote_to_bytes

TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
ATTR_CHAR = re.compile(r"^[!#$&+\-.^_`|~0-9A-Za-z]*$")
HEX = frozenset("0123456789abcdefABCDEF")
BIDI = frozenset(chr(x) for x in (0x061C, 0x200E, 0x200F, *range(0x202A, 0x202F), *range(0x2066, 0x206A)))
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
ALLOWED_INPUT_KEYS = {"content_disposition", "content_type", "media_type_extensions"}


class InputError(ValueError):
    pass


def split_parameters(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif char == ";" and not quoted:
            parts.append(value[start:index].strip())
            start = index + 1
    if quoted or escaped:
        raise InputError("unterminated quoted-string")
    parts.append(value[start:].strip())
    return parts


def parse_parameter_value(raw: str) -> str:
    if raw.startswith('"'):
        if len(raw) < 2 or not raw.endswith('"'):
            raise InputError("malformed quoted-string")
        output: list[str] = []
        escaped = False
        for char in raw[1:-1]:
            if escaped:
                output.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                raise InputError("unescaped quote in quoted-string")
            else:
                output.append(char)
        if escaped:
            raise InputError("trailing quoted-pair escape")
        value = "".join(output)
    else:
        if not TOKEN.fullmatch(raw):
            raise InputError("parameter value is neither token nor quoted-string")
        value = raw
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise InputError("control character in parameter value")
    return value


def decode_extended(raw: str) -> tuple[str, str]:
    pieces = raw.split("'", 2)
    if len(pieces) != 3:
        raise InputError("extended value must use charset'language'value")
    charset, language, encoded = pieces
    normalized_charset = charset.lower()
    if normalized_charset not in {"utf-8", "iso-8859-1"}:
        raise InputError("unsupported extended-value charset")
    if language and not re.fullmatch(r"[A-Za-z0-9-]+", language):
        raise InputError("invalid extended-value language tag")
    index = 0
    while index < len(encoded):
        if encoded[index] == "%":
            if index + 2 >= len(encoded) or encoded[index + 1] not in HEX or encoded[index + 2] not in HEX:
                raise InputError("malformed percent encoding")
            index += 3
        else:
            index += 1
    plain_chunks = re.split(r"%[0-9A-Fa-f]{2}", encoded)
    if any(not ATTR_CHAR.fullmatch(chunk) for chunk in plain_chunks):
        raise InputError("invalid attr-char in extended value")
    try:
        decoded = unquote_to_bytes(encoded).decode(normalized_charset, "strict")
    except UnicodeDecodeError as exc:
        raise InputError("extended value is invalid for declared charset") from exc
    return decoded, language


def parse_content_disposition(header: str) -> dict[str, Any]:
    if not header or "\r" in header or "\n" in header:
        raise InputError("empty, folded, or multi-line Content-Disposition")
    parts = split_parameters(header)
    disposition = parts[0].lower()
    if not TOKEN.fullmatch(disposition):
        raise InputError("invalid disposition type")
    parameters: dict[str, str] = {}
    duplicates: list[str] = []
    errors: list[dict[str, str]] = []
    for part in parts[1:]:
        if not part or "=" not in part:
            raise InputError("malformed disposition parameter")
        name, raw = part.split("=", 1)
        name = name.strip().lower()
        raw = raw.strip()
        if not TOKEN.fullmatch(name) or not raw:
            raise InputError("invalid parameter name or empty value")
        try:
            value = parse_parameter_value(raw)
        except InputError as exc:
            errors.append({"parameter": name, "error": str(exc)})
            continue
        if name in parameters:
            duplicates.append(name)
        else:
            parameters[name] = value
    return {"disposition": disposition, "parameters": parameters, "duplicates": duplicates, "parameter_errors": errors}


def validate_policy_map(value: Any) -> dict[str, set[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InputError("media_type_extensions must be an object")
    result: dict[str, set[str]] = {}
    for media_type, extensions in value.items():
        if not isinstance(media_type, str) or not re.fullmatch(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+", media_type.lower()):
            raise InputError("invalid media type in policy map")
        if not isinstance(extensions, list) or not extensions or any(not isinstance(ext, str) or not re.fullmatch(r"\.[A-Za-z0-9]{1,16}", ext) for ext in extensions):
            raise InputError("extension policies must be non-empty arrays of dot-prefixed extensions")
        result[media_type.lower()] = {ext.lower() for ext in extensions}
    return result


def filename_findings(filename: str, content_type: str | None, policies: dict[str, set[str]]) -> list[str]:
    findings: list[str] = []
    normalized = unicodedata.normalize("NFC", filename)
    if normalized != filename:
        findings.append("filename-non-nfc")
    if not filename:
        findings.append("filename-empty")
    if "/" in filename or "\\" in filename:
        findings.append("filename-path-separator")
    if filename in {".", ".."} or ".." in re.split(r"[/\\]", filename):
        findings.append("filename-dot-segment")
    if any(char in BIDI for char in filename):
        findings.append("filename-bidi-control")
    if any(unicodedata.category(char) in {"Cc", "Cf"} for char in filename):
        findings.append("filename-control")
    if filename.endswith((" ", ".")) or filename != filename.strip():
        findings.append("filename-unsafe-whitespace-or-dot")
    stem = filename.rsplit(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED:
        findings.append("filename-reserved-device-name")
    if content_type and policies:
        media_type = content_type.split(";", 1)[0].strip().lower()
        allowed = policies.get(media_type)
        if allowed is not None:
            suffix = Path(filename).suffix.lower()
            if suffix not in allowed:
                findings.append("filename-extension-media-policy-mismatch")
    return findings


def analyze(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise InputError("top-level JSON must be an object")
    unknown = sorted(set(document) - ALLOWED_INPUT_KEYS)
    if unknown:
        raise InputError(f"unknown input keys: {', '.join(unknown)}")
    header = document.get("content_disposition")
    content_type = document.get("content_type")
    if not isinstance(header, str):
        raise InputError("content_disposition must be a string")
    if content_type is not None and not isinstance(content_type, str):
        raise InputError("content_type must be a string or null")
    if content_type is not None:
        media_type = content_type.split(";", 1)[0].strip().lower()
        if not re.fullmatch(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+", media_type):
            raise InputError("content_type has an invalid media type")
    policies = validate_policy_map(document.get("media_type_extensions"))
    parsed = parse_content_disposition(header)
    codes: list[str] = []
    for name in parsed["duplicates"]:
        codes.append(f"duplicate-{name}-parameter")
    for error in parsed["parameter_errors"]:
        message = error["error"]
        if error["parameter"] == "filename*" and message == "malformed percent encoding":
            codes.append("filename-star-malformed-percent-encoding")
        else:
            codes.append(f"invalid-{error['parameter']}-parameter")
    selected_parameter: str | None = None
    decoded_filename: str | None = None
    language: str | None = None
    parameters = parsed["parameters"]
    if "filename*" in parameters and not any(item["parameter"] == "filename*" for item in parsed["parameter_errors"]):
        try:
            decoded_filename, language = decode_extended(parameters["filename*"])
            selected_parameter = "filename*"
        except InputError as exc:
            code = "filename-star-malformed-percent-encoding" if str(exc) == "malformed percent encoding" else "filename-star-invalid-extended-value"
            codes.append(code)
    elif "filename" in parameters:
        decoded_filename = parameters["filename"]
        selected_parameter = "filename"
    if decoded_filename is not None:
        codes.extend(filename_findings(decoded_filename, content_type, policies))
    if parsed["disposition"] not in {"attachment", "inline"}:
        codes.append("unknown-disposition-type")
    codes = list(dict.fromkeys(codes))
    decision = "accept" if decoded_filename is not None and not codes else "reject"
    reasons = [
        {"kind": "standard", "detail": "filename* precedes filename when its extended value is valid"}
        if selected_parameter == "filename*"
        else {"kind": "standard", "detail": "selected the filename parameter because no valid filename* was present"},
        {"kind": "consumer-policy", "detail": "basename and optional media-type extension policy checks were applied"},
    ]
    recovery = None
    if decision == "reject":
        recovery = "require-new-unambiguous-server-header" if any(code.startswith("duplicate-") or code.startswith("filename-star-") for code in codes) else "reject-unsafe-name-and-apply-reviewed-local-fallback"
    return {
        "activate": True,
        "parsed": True,
        "disposition": parsed["disposition"],
        "selected_parameter": selected_parameter,
        "decoded_filename": decoded_filename,
        "safe_basename": unicodedata.normalize("NFC", decoded_filename) if decision == "accept" and decoded_filename is not None else None,
        "language": language,
        "decision": decision,
        "finding_codes": codes,
        "policy_applied": bool(policies),
        "reasons": reasons,
        "recovery": recovery,
    }


def load_document(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot read UTF-8 input: {exc}") from exc
    try:
        return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"non-standard JSON number: {value}")))
    except json.JSONDecodeError as exc:
        raise InputError(f"malformed JSON: {exc.msg}") from exc


def emit(payload: dict[str, Any]) -> None:
    try:
        json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        sys.stdout.write("\n")
        sys.stdout.flush()
    except (OSError, UnicodeError) as exc:
        raise BrokenPipeError(str(exc)) from exc


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: analyze_content_disposition.py INPUT.json", file=sys.stderr)
        return 2
    try:
        report = analyze(load_document(Path(argv[1])))
    except InputError as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2
    try:
        emit(report)
    except BrokenPipeError as exc:
        # Prevent a second buffered flush during interpreter shutdown from
        # replacing the documented output-failure status.
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
        print(f"output failure: {exc}", file=sys.stderr)
        return 3
    return 0 if report["decision"] == "accept" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
