#!/usr/bin/env python3
"""Bounded offline analyzer for synthetic permessage-deflate message traces."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import sys
import tempfile
import time
import zlib
from pathlib import Path
from typing import Any

MAX_MESSAGES = 64
MAX_FRAGMENTS = 256
MAX_LIMIT = 64 * 1024 * 1024
TAIL = b"\x00\x00\xff\xff"


class InputError(ValueError):
    pass


def reject_constant(value: str) -> None:
    raise InputError(f"non-standard JSON number is forbidden: {value}")


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError("top-level value must be an object")
    return value


def integer(obj: dict[str, Any], key: str, *, minimum: int, maximum: int) -> int:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputError(f"{key} must be an integer")
    if not minimum <= value <= maximum:
        raise InputError(f"{key} must be between {minimum} and {maximum}")
    return value


def decode_fragment(value: Any) -> bytes:
    if not isinstance(value, str):
        raise InputError("every fragment must be a base64 string")
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InputError("fragment is not canonical base64 data") from exc


def validate(document: dict[str, Any]) -> tuple[bool, str, dict[str, int], list[dict[str, Any]]]:
    if not isinstance(document, dict):
        raise InputError("top-level value must be an object")
    if document.get("version") != 1:
        raise InputError("version must equal 1")
    negotiated = document.get("permessage_deflate_negotiated")
    if not isinstance(negotiated, bool):
        raise InputError("permessage_deflate_negotiated must be boolean")
    mode = document.get("context_takeover")
    if mode not in ("takeover", "no_context_takeover"):
        raise InputError("context_takeover must be takeover or no_context_takeover")
    limits = document.get("limits")
    if not isinstance(limits, dict):
        raise InputError("limits must be an object")
    parsed_limits = {
        "compressed_bytes": integer(limits, "compressed_bytes", minimum=1, maximum=MAX_LIMIT),
        "output_bytes": integer(limits, "output_bytes", minimum=1, maximum=MAX_LIMIT),
        "ratio": integer(limits, "ratio", minimum=1, maximum=1_000_000),
        "milliseconds": integer(limits, "milliseconds", minimum=1, maximum=600_000),
        "fragments": integer(limits, "fragments", minimum=1, maximum=MAX_FRAGMENTS),
    }
    messages = document.get("messages")
    if not isinstance(messages, list) or len(messages) > MAX_MESSAGES:
        raise InputError(f"messages must be an array with at most {MAX_MESSAGES} entries")
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise InputError(f"message {index} must be an object")
        if not isinstance(message.get("id"), str) or not message["id"]:
            raise InputError(f"message {index} requires a non-empty string id")
        if message.get("compressed") is not True:
            raise InputError(f"message {index} must declare compressed=true")
        fragments = message.get("fragments")
        if not isinstance(fragments, list) or not fragments:
            raise InputError(f"message {index} requires a non-empty fragments array")
        if len(fragments) > parsed_limits["fragments"]:
            raise InputError(f"message {index} exceeds the fragment-count policy")
    return negotiated, mode, parsed_limits, messages


def finding(kind: str, message_id: str, compressed: int, output: int, close_code: int) -> dict[str, Any]:
    return {
        "status": "rejected",
        "reason": kind,
        "message_id": message_id,
        "compressed_bytes": compressed,
        "output_bytes": output,
        "application_delivered": False,
        "close_connection": True,
        "close_code": close_code,
    }


def analyze(document: dict[str, Any]) -> dict[str, Any]:
    negotiated, mode, limits, messages = validate(document)
    if not negotiated:
        return {
            "version": 1,
            "status": "not_applicable",
            "reason": "permessage-deflate was not negotiated; no compressed trace was processed",
            "messages": [],
        }

    inflater: Any = None
    results: list[dict[str, Any]] = []
    for message in messages:
        if inflater is None or mode == "no_context_takeover":
            inflater = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        assert inflater is not None
        started = time.monotonic()
        compressed = 0
        output = 0
        rejected: dict[str, Any] | None = None
        fragments = message["fragments"]
        for fragment_index, encoded in enumerate(fragments):
            chunk = decode_fragment(encoded)
            compressed += len(chunk)
            if compressed > limits["compressed_bytes"]:
                rejected = finding("compressed_byte_limit", message["id"], compressed, output, 1009)
                break
            if (time.monotonic() - started) * 1000 > limits["milliseconds"]:
                rejected = finding("time_limit", message["id"], compressed, output, 1009)
                break
            if fragment_index == len(fragments) - 1:
                chunk += TAIL
            remaining = limits["output_bytes"] - output
            try:
                produced = inflater.decompress(chunk, remaining + 1)
            except zlib.error:
                rejected = finding("invalid_deflate", message["id"], compressed, output, 1002)
                break
            output += len(produced)
            if output > limits["output_bytes"]:
                rejected = finding("output_byte_limit", message["id"], compressed, output, 1009)
                break
            if output > compressed * limits["ratio"]:
                rejected = finding("expansion_ratio_limit", message["id"], compressed, output, 1009)
                break
            if inflater.unconsumed_tail:
                rejected = finding("output_byte_limit", message["id"], compressed, output, 1009)
                break
        if rejected is None and (time.monotonic() - started) * 1000 > limits["milliseconds"]:
            rejected = finding("time_limit", message["id"], compressed, output, 1009)
        if rejected is not None:
            results.append(rejected)
            return {
                "version": 1,
                "status": "rejected",
                "context_takeover": mode,
                "messages": results,
                "connection_state": "closed",
            }
        results.append({
            "status": "accepted",
            "message_id": message["id"],
            "compressed_bytes": compressed,
            "output_bytes": output,
            "application_delivered": True,
        })
        if mode == "no_context_takeover":
            inflater = None

    return {
        "version": 1,
        "status": "accepted",
        "context_takeover": mode,
        "messages": results,
        "connection_state": "open",
    }


def write_output(result: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(text)
        return
    output = output.resolve()
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, output)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(load_json(args.trace))
        write_output(result, args.output)
    except (InputError, OSError) as exc:
        print(json.dumps({"version": 1, "status": "invalid_input", "error": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
