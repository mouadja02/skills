#!/usr/bin/env python3
"""Inspect ZIP filename/comment encoding metadata without extraction."""
from __future__ import annotations

import argparse
import binascii
import json
import os
import struct
import sys
from pathlib import Path
from typing import Any

MAX_ARCHIVE = 64 * 1024 * 1024
EOCD = b"PK\x05\x06"
CENTRAL = b"PK\x01\x02"
LOCAL = b"PK\x03\x04"
EFS = 1 << 11

class InspectionError(Exception):
    pass

def finding(code: str, entry: int | None, detail: str, severity: str = "error") -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "severity": severity, "detail": detail}
    if entry is not None:
        item["entry"] = entry
    return item

def extras(raw: bytes, entry: int, where: str, findings: list[dict[str, Any]]) -> dict[int, list[bytes]]:
    result: dict[int, list[bytes]] = {}
    pos = 0
    while pos < len(raw):
        if len(raw) - pos < 4:
            findings.append(finding("malformed-extra-field", entry, f"{where}: truncated extra-field header"))
            return result
        kind, size = struct.unpack_from("<HH", raw, pos)
        pos += 4
        if size > len(raw) - pos:
            findings.append(finding("malformed-extra-field", entry, f"{where}: field 0x{kind:04x} exceeds its container"))
            return result
        result.setdefault(kind, []).append(raw[pos:pos + size])
        pos += size
    return result

def strict_utf8(raw: bytes, code: str, entry: int, findings: list[dict[str, Any]]) -> str | None:
    try:
        return raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        findings.append(finding(code, entry, "bytes governed by EFS are not strict UTF-8"))
        return None

def unicode_extra(kind: int, values: list[bytes], legacy: bytes, entry: int, where: str, findings: list[dict[str, Any]]) -> str | None:
    label = "path" if kind == 0x7075 else "comment"
    if not values:
        return None
    if len(values) != 1:
        findings.append(finding(f"duplicate-unicode-{label}-field", entry, f"{where}: found {len(values)} fields"))
        return None
    value = values[0]
    if len(value) < 5:
        findings.append(finding(f"malformed-unicode-{label}-field", entry, f"{where}: payload shorter than version plus CRC"))
        return None
    version = value[0]
    expected_crc = struct.unpack_from("<I", value, 1)[0]
    if version != 1:
        findings.append(finding(f"unsupported-unicode-{label}-version", entry, f"{where}: version {version}"))
        return None
    actual_crc = binascii.crc32(legacy) & 0xFFFFFFFF
    if expected_crc != actual_crc:
        findings.append(finding(f"unicode-{label}-crc-mismatch", entry, f"{where}: expected {expected_crc:08x}, actual {actual_crc:08x}"))
        return None
    try:
        return value[5:].decode("utf-8", "strict")
    except UnicodeDecodeError:
        findings.append(finding(f"invalid-unicode-{label}-utf8", entry, f"{where}: payload is not strict UTF-8"))
        return None

def unsafe_path(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name or name.startswith(("/", "\\")):
        return True
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        return True
    parts = name.replace("\\", "/").split("/")
    return any(part == ".." for part in parts) or (len(name) > 1 and name[1] == ":")

def inspect(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise InspectionError(f"cannot stat input: {exc}") from exc
    if size > MAX_ARCHIVE:
        raise InspectionError(f"archive exceeds {MAX_ARCHIVE} byte inspection cap")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise InspectionError(f"cannot read input: {exc}") from exc
    start = max(0, len(data) - (65535 + 22))
    eocd_pos = -1
    search_at = start
    while True:
        candidate = data.find(EOCD, search_at)
        if candidate < 0:
            break
        if candidate + 22 <= len(data):
            candidate_comment_len = struct.unpack_from("<H", data, candidate + 20)[0]
            if candidate + 22 + candidate_comment_len == len(data):
                eocd_pos = candidate
        search_at = candidate + 1
    if eocd_pos < 0:
        raise InspectionError("valid bounded EOCD not found")
    eocd = struct.unpack_from("<4s4H2IH", data, eocd_pos)
    disk, cd_disk, disk_entries, total_entries, cd_size, cd_offset, comment_len = eocd[1:]
    if eocd_pos + 22 + comment_len != len(data):
        raise InspectionError("EOCD comment length does not terminate at end of file")
    if disk or cd_disk or disk_entries != total_entries:
        raise InspectionError("multipart ZIP is unsupported")
    if total_entries == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
        raise InspectionError("ZIP64 is unsupported")
    if cd_offset + cd_size != eocd_pos or cd_offset > len(data):
        raise InspectionError("central-directory bounds are inconsistent")

    findings: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    seen_names: dict[str, int] = {}
    pos = cd_offset
    for index in range(total_entries):
        if pos + 46 > eocd_pos or data[pos:pos + 4] != CENTRAL:
            raise InspectionError(f"central entry {index} is truncated or has a bad signature")
        c = struct.unpack_from("<4s6H3I5H2I", data, pos)
        flags, name_len, extra_len, entry_comment_len, disk_start, local_offset = c[3], c[10], c[11], c[12], c[13], c[16]
        end = pos + 46 + name_len + extra_len + entry_comment_len
        if end > eocd_pos:
            raise InspectionError(f"central entry {index} exceeds directory bounds")
        c_name = data[pos + 46:pos + 46 + name_len]
        c_extra_raw = data[pos + 46 + name_len:pos + 46 + name_len + extra_len]
        c_comment = data[pos + 46 + name_len + extra_len:end]
        if disk_start:
            raise InspectionError("multipart member is unsupported")
        if local_offset + 30 > cd_offset or data[local_offset:local_offset + 4] != LOCAL:
            raise InspectionError(f"entry {index} references an invalid local header")
        local = struct.unpack_from("<4s5H3I2H", data, local_offset)
        l_flags, l_name_len, l_extra_len = local[2], local[9], local[10]
        l_end = local_offset + 30 + l_name_len + l_extra_len
        if l_end > cd_offset:
            raise InspectionError(f"entry {index} local metadata exceeds central directory")
        l_name = data[local_offset + 30:local_offset + 30 + l_name_len]
        l_extra_raw = data[local_offset + 30 + l_name_len:l_end]
        if l_name != c_name:
            findings.append(finding("local-central-name-mismatch", index, "raw filename bytes differ"))
        if bool(l_flags & EFS) != bool(flags & EFS):
            findings.append(finding("efs-flag-mismatch", index, "local and central EFS bits differ"))

        l_extra = extras(l_extra_raw, index, "local", findings)
        c_extra = extras(c_extra_raw, index, "central", findings)
        l_text = strict_utf8(l_name, "invalid-utf8-local-name", index, findings) if l_flags & EFS else l_name.decode("cp437")
        c_text = strict_utf8(c_name, "invalid-utf8-central-name", index, findings) if flags & EFS else c_name.decode("cp437")
        comment_text = strict_utf8(c_comment, "invalid-utf8-central-comment", index, findings) if flags & EFS else c_comment.decode("cp437")
        l_upath = unicode_extra(0x7075, l_extra.get(0x7075, []), l_name, index, "local", findings)
        c_upath = unicode_extra(0x7075, c_extra.get(0x7075, []), c_name, index, "central", findings)
        ucomment = unicode_extra(0x6375, c_extra.get(0x6375, []), c_comment, index, "central", findings)
        if l_upath is not None and c_upath is not None and l_upath != c_upath:
            findings.append(finding("local-central-unicode-path-mismatch", index, "valid local and central Unicode Path fields disagree"))
        if l_text is not None and l_upath is not None and l_flags & EFS and l_text != l_upath:
            findings.append(finding("unicode-path-conflict", index, "local EFS name disagrees with valid Unicode Path field"))
        if c_text is not None and c_upath is not None and flags & EFS and c_text != c_upath:
            findings.append(finding("unicode-path-conflict", index, "central EFS name disagrees with valid Unicode Path field"))
        if comment_text is not None and ucomment is not None and flags & EFS and comment_text != ucomment:
            findings.append(finding("unicode-comment-conflict", index, "EFS comment disagrees with valid Unicode Comment field"))
        if not flags & EFS and any(b >= 128 for b in c_name):
            try:
                c_name.decode("utf-8", "strict")
                observations.append({"code": "ambiguous-unflagged-utf8", "entry": index, "detail": "non-ASCII name is valid UTF-8 but EFS is clear; producer intent is not proven"})
            except UnicodeDecodeError:
                pass
        effective = c_upath if c_upath is not None else c_text
        if effective is not None:
            if unsafe_path(effective):
                findings.append(finding("unsafe-decoded-path", index, "decoded member name is empty, absolute, traversal-capable, or contains unsafe characters"))
            if effective in seen_names:
                findings.append(finding("duplicate-decoded-name", index, f"same decoded name as entry {seen_names[effective]}"))
            else:
                seen_names[effective] = index
        entries.append({
            "index": index,
            "raw_central_name_hex": c_name.hex(),
            "raw_local_name_hex": l_name.hex(),
            "efs": {"local": bool(l_flags & EFS), "central": bool(flags & EFS)},
            "decoded_name": effective,
            "decoded_comment": ucomment if ucomment is not None else comment_text,
            "unicode_path": {"local": l_upath, "central": c_upath},
            "unicode_comment": ucomment,
        })
        pos = end
    if pos != eocd_pos:
        raise InspectionError("central-directory entry count does not consume its declared bytes")
    return {"schema_version": 1, "applicable": True, "archive": str(path), "entries": entries, "findings": findings, "observations": observations, "safe_to_extract": not findings}

def emit(report: dict[str, Any], output: str | None) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    try:
        if output:
            with open(output, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
        else:
            sys.stdout.write(text)
            sys.stdout.flush()
    except (OSError, UnicodeError) as exc:
        raise InspectionError(f"cannot write report: {exc}") from exc

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        report = inspect(args.archive)
    except InspectionError as exc:
        error = {"schema_version": 1, "applicable": False, "error": str(exc)}
        try:
            emit(error, args.output)
        except InspectionError as write_exc:
            print(str(write_exc), file=sys.stderr)
            return 3
        return 2
    try:
        emit(report, args.output)
    except InspectionError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    return 1 if report["findings"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
