#!/usr/bin/env python3
"""Validate a captured GraphQL @defer HTTP response and merge its patches offline."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

MAX_INPUT = 16 * 1024 * 1024
MAX_PARTS = 10_000
PROFILES = {"current-id-v1", "legacy-path-v0.1"}
TOKEN = re.compile(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
STATUS = re.compile(rb"HTTP/1\.[01] ([0-9]{3})(?: [^\r\n]*)?\Z")


class PreflightError(ValueError):
    """A fail-closed wire or GraphQL contract violation."""


def _read(path: Path) -> bytes:
    try:
        size = path.stat().st_size
        if size > MAX_INPUT:
            raise PreflightError(f"input exceeds {MAX_INPUT} bytes: {path}")
        return path.read_bytes()
    except OSError as exc:
        raise PreflightError(f"cannot read {path}: {exc}") from exc


def _headers(block: bytes, where: str) -> tuple[bytes | None, dict[str, bytes]]:
    lines = block.split(b"\r\n")
    first = lines.pop(0) if where == "HTTP" else None
    out: dict[str, bytes] = {}
    for line in lines:
        if not line or line[:1] in b" \t" or b":" not in line:
            raise PreflightError(f"malformed {where} header line")
        name, value = line.split(b":", 1)
        if not TOKEN.fullmatch(name):
            raise PreflightError(f"invalid {where} header name")
        key = name.decode("ascii").lower()
        if key in out:
            raise PreflightError(f"duplicate {where} header: {key}")
        value = value.strip(b" \t")
        if any(byte < 32 and byte != 9 for byte in value) or b"\x7f" in value:
            raise PreflightError(f"invalid {where} header value: {key}")
        out[key] = value
    return first, out


def _content_type(value: bytes, where: str) -> tuple[str, dict[str, str]]:
    try:
        text = value.decode("ascii")
    except UnicodeDecodeError as exc:
        raise PreflightError(f"non-ASCII {where} Content-Type") from exc
    pieces: list[str] = []
    current: list[str] = []
    quoted = False
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == '"':
            quoted = not quoted
            current.append(char)
        elif char == ";" and not quoted:
            pieces.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if quoted or escaped:
        raise PreflightError(f"malformed {where} Content-Type quoting")
    pieces.append("".join(current).strip())
    media = pieces.pop(0).lower()
    params: dict[str, str] = {}
    for piece in pieces:
        if "=" not in piece:
            raise PreflightError(f"malformed {where} Content-Type parameter")
        name, raw = piece.split("=", 1)
        name = name.strip().lower()
        raw = raw.strip()
        if not name or name in params:
            raise PreflightError(f"duplicate/empty {where} Content-Type parameter")
        if raw.startswith('"'):
            if not raw.endswith('"') or len(raw) < 2:
                raise PreflightError(f"malformed {where} Content-Type parameter")
            raw = raw[1:-1]
        params[name] = raw
    return media, params


def _decode_chunked(body: bytes) -> bytes:
    pos = 0
    chunks: list[bytes] = []
    total = 0
    while True:
        end = body.find(b"\r\n", pos)
        if end < 0:
            raise PreflightError("truncated chunk-size line")
        line = body[pos:end]
        size_text = line.split(b";", 1)[0]
        if not size_text or not re.fullmatch(rb"[0-9A-Fa-f]+", size_text):
            raise PreflightError("invalid HTTP chunk size")
        size = int(size_text, 16)
        pos = end + 2
        if size == 0:
            trailer_end = body.find(b"\r\n\r\n", pos)
            if body[pos:pos + 2] == b"\r\n":
                trailer_end = pos
            if trailer_end < 0 or trailer_end + 4 != len(body) and trailer_end + 2 != len(body):
                raise PreflightError("malformed chunked trailers or trailing bytes")
            if trailer_end > pos:
                _headers(body[pos:trailer_end], "chunk trailer")
            return b"".join(chunks)
        if size > MAX_INPUT or total + size > MAX_INPUT:
            raise PreflightError("decoded chunked body exceeds limit")
        end = pos + size
        if end + 2 > len(body) or body[end:end + 2] != b"\r\n":
            raise PreflightError("truncated HTTP chunk")
        chunks.append(body[pos:end])
        total += size
        pos = end + 2


def parse_http(raw: bytes) -> tuple[bytes, str, dict[str, str]]:
    split = raw.find(b"\r\n\r\n")
    if split < 0:
        raise PreflightError("HTTP headers must end with CRLF CRLF")
    first, headers = _headers(raw[:split], "HTTP")
    match = STATUS.fullmatch(first or b"")
    if not match:
        raise PreflightError("expected an HTTP/1.x status line")
    if int(match.group(1)) != 200:
        raise PreflightError(f"expected HTTP 200, got {match.group(1).decode()}")
    if "content-type" not in headers:
        raise PreflightError("missing HTTP Content-Type")
    media, params = _content_type(headers["content-type"], "HTTP")
    if media != "multipart/mixed":
        raise PreflightError(f"expected multipart/mixed, got {media!r}")
    boundary = params.get("boundary", "")
    try:
        boundary_bytes = boundary.encode("ascii")
    except UnicodeEncodeError as exc:
        raise PreflightError("non-ASCII multipart boundary") from exc
    if not 1 <= len(boundary_bytes) <= 70 or not re.fullmatch(rb"[0-9A-Za-z'()+_,./:=?-]+", boundary_bytes):
        raise PreflightError("invalid or missing multipart boundary")

    body = raw[split + 4:]
    transfer = headers.get("transfer-encoding")
    length = headers.get("content-length")
    if transfer is not None and length is not None:
        raise PreflightError("both Transfer-Encoding and Content-Length are present")
    if transfer is not None:
        if transfer.strip().lower() != b"chunked":
            raise PreflightError("only chunked Transfer-Encoding is supported")
        body = _decode_chunked(body)
    elif length is not None:
        if not re.fullmatch(rb"[0-9]+", length):
            raise PreflightError("invalid Content-Length")
        if int(length) != len(body):
            raise PreflightError("Content-Length does not match captured body")
    return body, boundary, params


def parse_multipart(body: bytes, boundary: str) -> list[bytes]:
    delimiter = b"--" + boundary.encode("ascii")
    pos = 0
    parts: list[bytes] = []
    while True:
        if body[pos:pos + len(delimiter)] != delimiter:
            raise PreflightError("multipart body has preamble, bad boundary, or missing delimiter")
        pos += len(delimiter)
        if body[pos:pos + 2] == b"--":
            tail = body[pos + 2:]
            if tail not in (b"", b"\r\n"):
                raise PreflightError("bytes found after closing multipart boundary")
            if not parts:
                raise PreflightError("multipart response has no parts")
            return parts
        if body[pos:pos + 2] != b"\r\n":
            raise PreflightError("multipart boundary line is malformed")
        pos += 2
        header_end = body.find(b"\r\n\r\n", pos)
        if header_end < 0:
            raise PreflightError("multipart part headers are truncated")
        _, headers = _headers(body[pos:header_end], "part")
        if "content-type" not in headers:
            raise PreflightError("multipart part is missing Content-Type")
        media, _ = _content_type(headers["content-type"], "part")
        if media not in {"application/json", "application/graphql-response+json"}:
            raise PreflightError(f"unexpected part Content-Type: {media!r}")
        start = header_end + 4
        marker = body.find(b"\r\n" + delimiter, start)
        if marker < 0:
            raise PreflightError("multipart part has no following boundary")
        parts.append(body[start:marker])
        if len(parts) > MAX_PARTS:
            raise PreflightError(f"multipart response exceeds {MAX_PARTS} parts")
        pos = marker + 2


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise PreflightError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _constant(value: str) -> None:
    raise PreflightError(f"non-standard JSON number: {value}")


def parse_json(raw: bytes, where: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError(f"{where} is not UTF-8") from exc
    if text.startswith("\ufeff"):
        raise PreflightError(f"{where} starts with a UTF-8 BOM")
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except json.JSONDecodeError as exc:
        raise PreflightError(f"invalid JSON in {where}: {exc}") from exc


def _path(path: Any, where: str) -> list[str | int]:
    if not isinstance(path, list):
        raise PreflightError(f"{where}.path must be an array")
    result: list[str | int] = []
    for item in path:
        if isinstance(item, str) or type(item) is int and item >= 0:
            result.append(item)
        else:
            raise PreflightError(f"{where}.path contains an invalid segment")
    return result


def _exact_keys(value: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(value.keys() - allowed)
    if unknown:
        raise PreflightError(f"{where} has unknown envelope keys: {', '.join(unknown)}")


def _id(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise PreflightError(f"{where}.id must be a non-empty string")
    return value


def _resolve(root: Any, path: list[str | int], where: str) -> Any:
    target = root
    for segment in path:
        if isinstance(segment, str):
            if not isinstance(target, dict) or segment not in target:
                raise PreflightError(f"{where}.path does not resolve at {segment!r}")
            target = target[segment]
        else:
            if not isinstance(target, list) or segment >= len(target):
                raise PreflightError(f"{where}.path index does not resolve: {segment}")
            target = target[segment]
    return target


def apply_patch(root: dict[str, Any], path: list[str | int], patch: Any, where: str) -> None:
    if not isinstance(patch, dict):
        raise PreflightError(f"{where}.data must be an object for @defer")
    target = _resolve(root, path, where)
    if not isinstance(target, dict):
        raise PreflightError(f"{where}.path target is not an object")
    for key, value in patch.items():
        if key in target and target[key] != value:
            raise PreflightError(f"{where} conflicts with existing field {key!r}")
        target[key] = value


def merge_current(parts: list[bytes]) -> tuple[dict[str, Any], int, list[str], list[str]]:
    merged: dict[str, Any] | None = None
    patch_count = 0
    pending: dict[str, list[str | int]] = {}
    pending_order: list[str] = []
    completed_order: list[str] = []
    for index, raw in enumerate(parts):
        where = f"part[{index}]"
        payload = parse_json(raw, where)
        if not isinstance(payload, dict):
            raise PreflightError(f"{where} must be a JSON object")
        allowed = {"hasNext", "errors", "extensions"}
        allowed |= {"data", "pending"} if index == 0 else {"pending", "incremental", "completed"}
        _exact_keys(payload, allowed, where)
        if payload.get("errors"):
            raise PreflightError(f"{where} contains GraphQL errors")
        if type(payload.get("hasNext")) is not bool:
            raise PreflightError(f"{where}.hasNext must be boolean")
        if index < len(parts) - 1 and payload["hasNext"] is not True:
            raise PreflightError(f"{where}.hasNext must be true before the final part")
        if index == len(parts) - 1 and payload["hasNext"] is not False:
            raise PreflightError("final part must contain hasNext=false")
        if index == 0:
            if not isinstance(payload.get("data"), dict):
                raise PreflightError("first part must contain object-valued data")
            merged = payload["data"]
        elif "data" in payload:
            raise PreflightError(f"{where} unexpectedly contains top-level data")

        new_pending = payload.get("pending", [])
        if not isinstance(new_pending, list):
            raise PreflightError(f"{where}.pending must be an array")
        for pending_index, entry in enumerate(new_pending):
            pending_where = f"{where}.pending[{pending_index}]"
            if not isinstance(entry, dict):
                raise PreflightError(f"{pending_where} must be an object")
            _exact_keys(entry, {"id", "path", "label"}, pending_where)
            task_id = _id(entry.get("id"), pending_where)
            if task_id in pending or task_id in completed_order:
                raise PreflightError(f"{pending_where} repeats id {task_id!r}")
            path = _path(entry.get("path"), pending_where)
            assert merged is not None
            _resolve(merged, path, pending_where)
            if "label" in entry and not isinstance(entry["label"], str):
                raise PreflightError(f"{pending_where}.label must be a string")
            pending[task_id] = path
            pending_order.append(task_id)

        incremental = payload.get("incremental", [])
        if not isinstance(incremental, list):
            raise PreflightError(f"{where}.incremental must be an array")
        for patch_index, entry in enumerate(incremental):
            patch_where = f"{where}.incremental[{patch_index}]"
            if not isinstance(entry, dict):
                raise PreflightError(f"{patch_where} must be an object")
            is_stream = "items" in entry
            allowed_patch = {"id", "subPath", "errors", "extensions", "items" if is_stream else "data"}
            _exact_keys(entry, allowed_patch, patch_where)
            if entry.get("errors"):
                raise PreflightError(f"{patch_where} contains GraphQL errors")
            if ("data" in entry) == ("items" in entry):
                raise PreflightError(f"{patch_where} must contain exactly one of data or items")
            task_id = _id(entry.get("id"), patch_where)
            if task_id not in pending:
                raise PreflightError(f"{patch_where} references non-pending id {task_id!r}")
            sub_path = _path(entry.get("subPath", []), patch_where)
            path = pending[task_id] + sub_path
            assert merged is not None
            if is_stream:
                items = entry["items"]
                if not isinstance(items, list):
                    raise PreflightError(f"{patch_where}.items must be an array")
                target = _resolve(merged, path, patch_where)
                if not isinstance(target, list):
                    raise PreflightError(f"{patch_where} stream target is not a list")
                target.extend(items)
            else:
                apply_patch(merged, path, entry["data"], patch_where)
            patch_count += 1

        completed = payload.get("completed", [])
        if not isinstance(completed, list):
            raise PreflightError(f"{where}.completed must be an array")
        for completed_index, entry in enumerate(completed):
            completed_where = f"{where}.completed[{completed_index}]"
            if not isinstance(entry, dict):
                raise PreflightError(f"{completed_where} must be an object")
            _exact_keys(entry, {"id", "errors"}, completed_where)
            if entry.get("errors"):
                raise PreflightError(f"{completed_where} contains GraphQL errors")
            task_id = _id(entry.get("id"), completed_where)
            if task_id not in pending:
                raise PreflightError(f"{completed_where} references non-pending id {task_id!r}")
            del pending[task_id]
            completed_order.append(task_id)
        if payload["hasNext"] is False and pending:
            raise PreflightError(f"final part leaves pending ids: {', '.join(pending)}")
    if patch_count == 0:
        raise PreflightError("response contains no incremental patches")
    assert merged is not None
    return merged, patch_count, pending_order, completed_order


def merge_legacy(parts: list[bytes]) -> tuple[dict[str, Any], int, list[str], list[str]]:
    """Replay the path-based V0.1 shape, including folded initial patches."""
    merged: dict[str, Any] | None = None
    patch_count = 0
    for index, raw in enumerate(parts):
        where = f"part[{index}]"
        payload = parse_json(raw, where)
        if not isinstance(payload, dict):
            raise PreflightError(f"{where} must be a JSON object")
        _exact_keys(payload, {"data", "incremental", "hasNext", "errors", "extensions"}, where)
        if payload.get("errors"):
            raise PreflightError(f"{where} contains GraphQL errors")
        if type(payload.get("hasNext")) is not bool:
            raise PreflightError(f"{where}.hasNext must be boolean")
        if index < len(parts) - 1 and payload["hasNext"] is not True:
            raise PreflightError(f"{where}.hasNext must be true before the final part")
        if index == len(parts) - 1 and payload["hasNext"] is not False:
            raise PreflightError("final part must contain hasNext=false")
        if index == 0:
            if not isinstance(payload.get("data"), dict):
                raise PreflightError("first part must contain object-valued data")
            merged = payload["data"]
        elif "data" in payload:
            raise PreflightError(f"{where} unexpectedly contains top-level data")
        entries = payload.get("incremental", [])
        if not isinstance(entries, list):
            raise PreflightError(f"{where}.incremental must be an array")
        for patch_index, entry in enumerate(entries):
            patch_where = f"{where}.incremental[{patch_index}]"
            if not isinstance(entry, dict):
                raise PreflightError(f"{patch_where} must be an object")
            is_stream = "items" in entry
            allowed = {"path", "label", "errors", "extensions", "items" if is_stream else "data"}
            _exact_keys(entry, allowed, patch_where)
            if entry.get("errors"):
                raise PreflightError(f"{patch_where} contains GraphQL errors")
            if ("data" in entry) == ("items" in entry):
                raise PreflightError(f"{patch_where} must contain exactly one of data or items")
            path = _path(entry.get("path"), patch_where)
            assert merged is not None
            if is_stream:
                items = entry["items"]
                if not isinstance(items, list):
                    raise PreflightError(f"{patch_where}.items must be an array")
                target = _resolve(merged, path, patch_where)
                if not isinstance(target, list):
                    raise PreflightError(f"{patch_where} stream target is not a list")
                target.extend(items)
            else:
                apply_patch(merged, path, entry["data"], patch_where)
            patch_count += 1
    if patch_count == 0:
        raise PreflightError("response contains no incremental patches")
    assert merged is not None
    return merged, patch_count, [], []


def merge_parts(parts: list[bytes], profile: str) -> tuple[dict[str, Any], int, list[str], list[str]]:
    if profile not in PROFILES:
        raise PreflightError(f"unsupported replay profile {profile!r}; expected one of {sorted(PROFILES)!r}")
    return merge_current(parts) if profile == "current-id-v1" else merge_legacy(parts)


def run(raw_path: Path, expected_path: Path, profile: str) -> dict[str, Any]:
    raw = _read(raw_path)
    body, boundary, params = parse_http(raw)
    parts = parse_multipart(body, boundary)
    merged, patch_count, pending_ids, completed_ids = merge_parts(parts, profile)
    expected = parse_json(_read(expected_path), "expected document")
    if merged != expected:
        raise PreflightError(
            "final merged data does not equal expected document; "
            f"merged={json.dumps(merged, sort_keys=True, separators=(',', ':'))}"
        )
    canonical = json.dumps(merged, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "status": "pass",
        "profile": profile,
        "http_status": 200,
        "media_type": "multipart/mixed",
        "boundary": boundary,
        "defer_spec": params.get("deferspec"),
        "parts": len(parts),
        "patches": patch_count,
        "pending_ids": pending_ids,
        "completed_ids": completed_ids,
        "terminal_has_next": False,
        "expected_match": True,
        "merged_sha256": hashlib.sha256(canonical).hexdigest(),
        "merged_data": merged,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=sorted(PROFILES), help="pinned replay contract")
    parser.add_argument("raw_response", type=Path, help="captured HTTP status line, headers, and body")
    parser.add_argument("expected_json", type=Path, help="expected final GraphQL data object")
    args = parser.parse_args()
    try:
        report = run(args.raw_response, args.expected_json, args.profile)
    except PreflightError as exc:
        sys.stderr.write(f"BLOCK: {exc}\n")
        return 1
    sys.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
