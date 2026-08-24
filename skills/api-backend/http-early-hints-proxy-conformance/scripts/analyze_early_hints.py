#!/usr/bin/env python3
"""Fail-closed analyzer for normalized HTTP informational-response captures."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

MAX_BYTES_DEFAULT = 1_048_576
MAX_HOPS_DEFAULT = 32
MAX_EVENTS_DEFAULT = 256
HEX = set("0123456789abcdef")
FIELD_NAME = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


class InputError(ValueError):
    pass


def _keys(value: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InputError(f"{where} has unknown members: {', '.join(unknown)}")


def _obj(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{where} must be an object")
    return value


def _list(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list):
        raise InputError(f"{where} must be an array")
    return value


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise InputError(f"{where} must be non-empty text without controls")
    return value


def _status(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 100 <= value <= 599:
        raise InputError(f"{where} must be an integer from 100 through 599")
    return value


def _headers(value: Any, where: str) -> list[tuple[str, str]]:
    rows = _list(value, where)
    out: list[tuple[str, str]] = []
    for i, row in enumerate(rows):
        pair = _list(row, f"{where}[{i}]")
        if len(pair) != 2:
            raise InputError(f"{where}[{i}] must contain name and value")
        name = _text(pair[0], f"{where}[{i}][0]").lower()
        if not FIELD_NAME.fullmatch(name):
            raise InputError(f"{where}[{i}][0] must be an HTTP field name")
        val = pair[1]
        if not isinstance(val, str) or "\r" in val or "\n" in val or "\0" in val:
            raise InputError(f"{where}[{i}][1] must be a header value without CR, LF, or NUL")
        out.append((name, val.strip()))
    return out


def _digest(value: Any, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 64 or any(c not in HEX for c in value):
        raise InputError(f"{where} must be a lowercase SHA-256 hex digest")
    return value


def _parse_hop(raw: Any, index: int, max_events: int) -> dict[str, Any]:
    hop = _obj(raw, f"hops[{index}]")
    _keys(hop, {"name", "protocol", "events"}, f"hops[{index}]")
    name = _text(hop.get("name"), f"hops[{index}].name")
    protocol = _text(hop.get("protocol"), f"hops[{index}].protocol")
    if protocol not in {"http/1.1", "h2", "h3"}:
        raise InputError(f"hops[{index}].protocol must be http/1.1, h2, or h3")
    events = _list(hop.get("events"), f"hops[{index}].events")
    if not events or len(events) > max_events:
        raise InputError(f"hops[{index}].events must contain 1..{max_events} events")
    parsed = []
    terminal_seen = False
    for j, raw_event in enumerate(events):
        event = _obj(raw_event, f"hops[{index}].events[{j}]")
        _keys(event, {"status", "headers", "body_sha256"}, f"hops[{index}].events[{j}]")
        status = _status(event.get("status"), f"hops[{index}].events[{j}].status")
        headers = _headers(event.get("headers", []), f"hops[{index}].events[{j}].headers")
        body = _digest(event.get("body_sha256"), f"hops[{index}].events[{j}].body_sha256")
        if terminal_seen:
            raise InputError(f"hops[{index}] has an event after its terminal response")
        if 100 <= status < 200:
            if body is not None:
                raise InputError(f"hops[{index}] informational event {j} must not have a body digest")
            if status == 101:
                terminal_seen = True
        else:
            terminal_seen = True
        parsed.append({"status": status, "headers": headers, "body_sha256": body})
    if not terminal_seen:
        raise InputError(f"hops[{index}] has no final response or terminal 101")
    return {"name": name, "protocol": protocol, "events": parsed}


def _hint_signature(hop: dict[str, Any]) -> list[list[tuple[str, str]]]:
    return [[h for h in e["headers"] if h[0] == "link"] for e in hop["events"] if e["status"] == 103]


def _final(hop: dict[str, Any]) -> dict[str, Any]:
    return next(e for e in hop["events"] if e["status"] == 101 or e["status"] >= 200)


def analyze(document: Any, max_hops: int = MAX_HOPS_DEFAULT, max_events: int = MAX_EVENTS_DEFAULT) -> dict[str, Any]:
    root = _obj(document, "document")
    _keys(root, {"schema_version", "hops"}, "document")
    if root.get("schema_version") != 1:
        raise InputError("schema_version must equal 1")
    raw_hops = _list(root.get("hops"), "hops")
    if not 1 <= len(raw_hops) <= max_hops:
        raise InputError(f"hops must contain 1..{max_hops} observations")
    hops = [_parse_hop(h, i, max_events) for i, h in enumerate(raw_hops)]
    names = [h["name"] for h in hops]
    if len(set(names)) != len(names):
        raise InputError("hop names must be unique")

    reference_hints = _hint_signature(hops[0])
    reference_final = _final(hops[0])
    applicable = bool(reference_hints)
    comparisons = []
    findings = []
    for left, right in zip(hops, hops[1:]):
        before, after = _hint_signature(left), _hint_signature(right)
        left_final, right_final = _final(left), _final(right)
        final_preserved = left_final["status"] == right_final["status"]
        if left_final["body_sha256"] is not None:
            final_preserved = final_preserved and left_final["body_sha256"] == right_final["body_sha256"]
        if before == after:
            outcome = "pass"
        elif before and not after:
            final_links = [h for h in right_final["headers"] if h[0] == "link"]
            flattened = [item for block in before for item in block]
            outcome = "merged_into_final" if flattened and all(x in final_links for x in flattened) else "dropped"
        else:
            outcome = "mutated_or_reordered"
        if outcome != "pass":
            findings.append({"type": outcome, "between": [left["name"], right["name"]]})
        if not final_preserved:
            findings.append({"type": "final_response_changed", "between": [left["name"], right["name"]]})
        comparisons.append({
            "from": left["name"], "to": right["name"], "outcome": outcome,
            "final_preserved": final_preserved,
            "protocol_translation": left["protocol"] != right["protocol"],
        })

    if not applicable:
        control = "not_applicable"
    elif findings:
        control = "blocked"
    else:
        control = "ready"
    return {
        "schema_version": 1,
        "control": control,
        "applicable": applicable,
        "reference_early_hints": len(reference_hints),
        "hop_count": len(hops),
        "comparisons": comparisons,
        "findings": findings,
        "recommendation": "deploy" if control == "ready" else ("use ordinary final-response checks" if control == "not_applicable" else "stop at the first divergent hop and repair before replay"),
    }


def _load(path: str, max_bytes: int) -> Any:
    if path == "-":
        raw = sys.stdin.buffer.read(max_bytes + 1)
    else:
        with open(path, "rb") as handle:
            raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise InputError(f"input exceeds max-bytes={max_bytes}")
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise InputError(f"duplicate JSON member {key!r}")
            result[key] = value
        return result
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=lambda x: (_ for _ in ()).throw(InputError(f"non-standard number {x}")),
        )
    except UnicodeDecodeError as exc:
        raise InputError(f"input is not UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"malformed JSON: {exc.msg}") from exc


def _emit(report: dict[str, Any]) -> None:
    json.dump(report, sys.stdout, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _silence_broken_stdout() -> None:
    try:
        fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(fd, sys.stdout.fileno())
        os.close(fd)
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", help="normalized JSON capture, or - for stdin")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT)
    parser.add_argument("--max-hops", type=int, default=MAX_HOPS_DEFAULT)
    parser.add_argument("--max-events", type=int, default=MAX_EVENTS_DEFAULT)
    args = parser.parse_args()
    if min(args.max_bytes, args.max_hops, args.max_events) < 1:
        parser.error("limits must be positive")
    try:
        report = analyze(_load(args.capture, args.max_bytes), args.max_hops, args.max_events)
        _emit(report)
        return 0 if report["control"] in {"ready", "not_applicable"} else 2
    except (InputError, OSError) as exc:
        report = {"schema_version": 1, "control": "blocked", "applicable": None, "error": str(exc)}
        try:
            _emit(report)
        except OSError:
            _silence_broken_stdout()
            return 3
        return 2 if isinstance(exc, InputError) else 3


if __name__ == "__main__":
    raise SystemExit(main())
