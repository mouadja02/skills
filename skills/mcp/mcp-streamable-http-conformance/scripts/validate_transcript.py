#!/usr/bin/env python3
"""Offline validator for normalized MCP Streamable HTTP transcripts."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

PROFILES = {
    "stable-2025-11-25": {
        "version": "2025-11-25",
        "get": True,
        "sessions": True,
        "resumability": True,
        "draft": False,
    },
    "draft-2026-07-28": {
        "version": "2026-07-28",
        "get": False,
        "sessions": False,
        "resumability": False,
        "draft": True,
    },
}


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    path: str
    message: str


def reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value}")


def finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"number is outside the finite host range: {value}")
    return parsed


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=reject_constant, parse_float=finite_float)


def header_map(value: Any, path: str, findings: list[Finding]) -> dict[str, str]:
    if not isinstance(value, dict):
        findings.append(Finding("error", "invalid_headers", path, "headers must be an object of string values"))
        return {}
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            findings.append(Finding("error", "invalid_headers", path, "header names and values must be strings"))
            continue
        lowered = key.lower()
        if lowered in result:
            findings.append(Finding("error", "duplicate_header", path, f"duplicate case-insensitive header: {key}"))
        result[lowered] = item
    return result


def media_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def has_accept(headers: dict[str, str], required: set[str]) -> bool:
    offered: set[str] = set()
    for item in headers.get("accept", "").split(","):
        parts = [part.strip() for part in item.split(";")]
        if not parts or not parts[0]:
            continue
        quality = 1.0
        valid = True
        for parameter in parts[1:]:
            name, separator, value = parameter.partition("=")
            if name.strip().lower() == "q":
                if not separator:
                    valid = False
                    continue
                raw_quality = value.strip()
                if not re.fullmatch(r"(?:0(?:\.\d{0,3})?|1(?:\.0{0,3})?)", raw_quality):
                    valid = False
                    continue
                quality = float(raw_quality)
        if valid and quality > 0:
            offered.add(parts[0].lower())
    return required.issubset(offered)


def parse_sse(chunks: Any, path: str, findings: list[Finding]) -> list[dict[str, Any]]:
    if not isinstance(chunks, list) or not all(isinstance(chunk, str) for chunk in chunks):
        findings.append(Finding("error", "invalid_chunks", path, "chunks must be an array of strings"))
        return []
    text = "".join(chunks).replace("\r\n", "\n").replace("\r", "\n")
    if text and not text.endswith("\n\n"):
        findings.append(Finding("error", "incomplete_sse_event", path, "stream ended with an unterminated SSE event"))
    events: list[dict[str, Any]] = []
    for index, block in enumerate(text.split("\n\n")):
        if not block:
            continue
        fields: dict[str, list[str]] = {}
        for line in block.split("\n"):
            if not line or line.startswith(":"):
                continue
            name, separator, value = line.partition(":")
            if not separator:
                value = ""
            elif value.startswith(" "):
                value = value[1:]
            if name not in {"event", "data", "id", "retry"}:
                continue
            fields.setdefault(name, []).append(value)
        event: dict[str, Any] = {"index": index}
        if "id" in fields:
            for candidate_id in fields["id"]:
                if "\x00" in candidate_id:
                    findings.append(Finding("warning", "ignored_sse_id_nul", f"{path}/{index}", "SSE id containing NUL was ignored"))
                else:
                    event["id"] = candidate_id
        if "retry" in fields:
            retry = fields["retry"][-1]
            if not retry.isdigit():
                findings.append(Finding("error", "invalid_sse_retry", f"{path}/{index}", "retry must be an integer number of milliseconds"))
            else:
                event["retry"] = int(retry)
        if "data" in fields:
            raw = "\n".join(fields["data"])
            event["data"] = raw
            if raw:
                try:
                    event["json"] = json.loads(raw, parse_constant=reject_constant, parse_float=finite_float)
                except (json.JSONDecodeError, ValueError) as exc:
                    findings.append(Finding("error", "invalid_sse_json", f"{path}/{index}", f"data is not strict JSON: {exc}"))
        events.append(event)
    return events


def body_method(body: Any) -> str | None:
    return body.get("method") if isinstance(body, dict) and isinstance(body.get("method"), str) else None


def is_jsonrpc_message(body: Any) -> bool:
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return False
    rpc_id = body.get("id")
    if "id" in body and not (
        rpc_id is None
        or isinstance(rpc_id, str)
        or (isinstance(rpc_id, int) and not isinstance(rpc_id, bool))
        or (isinstance(rpc_id, float) and math.isfinite(rpc_id))
    ):
        return False
    if isinstance(body.get("method"), str):
        params = body.get("params")
        return (
            "result" not in body
            and "error" not in body
            and ("params" not in body or isinstance(params, (dict, list)))
        )
    if "id" not in body or (("result" in body) == ("error" in body)):
        return False
    if "error" in body:
        error = body["error"]
        return (
            isinstance(error, dict)
            and isinstance(error.get("code"), int)
            and not isinstance(error.get("code"), bool)
            and isinstance(error.get("message"), str)
        )
    return True


def validate(document: Any) -> dict[str, Any]:
    findings: list[Finding] = []
    recovery: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return {"valid": False, "profile": None, "draft": False, "normative": False, "findings": [asdict(Finding("error", "invalid_document", "/", "top level must be an object"))], "recovery": []}
    profile_name = document.get("profile")
    if not isinstance(profile_name, str) or profile_name not in PROFILES:
        return {"valid": False, "profile": profile_name, "draft": False, "normative": False, "findings": [asdict(Finding("error", "unknown_profile", "/profile", "use an exact bundled profile name"))], "recovery": []}
    profile = PROFILES[profile_name]
    exchanges = document.get("exchanges")
    if not isinstance(exchanges, list) or not exchanges:
        findings.append(Finding("error", "invalid_exchanges", "/exchanges", "exchanges must be a non-empty array"))
        exchanges = []

    seen_ids: set[str] = set()
    stream_payloads: dict[tuple[str, str], str] = {}
    for index, exchange in enumerate(exchanges):
        base = f"/exchanges/{index}"
        if not isinstance(exchange, dict):
            findings.append(Finding("error", "invalid_exchange", base, "exchange must be an object"))
            continue
        exchange_id = exchange.get("id")
        if not isinstance(exchange_id, str) or not exchange_id:
            findings.append(Finding("error", "invalid_exchange_id", f"{base}/id", "id must be a non-empty string"))
            exchange_id = f"index-{index}"
        elif exchange_id in seen_ids:
            findings.append(Finding("error", "duplicate_exchange_id", f"{base}/id", "exchange id must be unique"))
        seen_ids.add(exchange_id)

        concurrent_group = exchange.get("concurrent_group")
        if concurrent_group is not None and (not isinstance(concurrent_group, str) or not concurrent_group):
            findings.append(Finding("error", "invalid_concurrent_group", f"{base}/concurrent_group", "concurrent_group must be a non-empty string when present"))
            concurrent_group = None

        request = exchange.get("request")
        response = exchange.get("response")
        if not isinstance(request, dict) or not isinstance(response, dict):
            findings.append(Finding("error", "invalid_exchange_shape", base, "request and response must be objects"))
            continue
        method = request.get("method")
        if not isinstance(method, str):
            findings.append(Finding("error", "invalid_http_method", f"{base}/request/method", "HTTP method must be a string"))
            continue
        method = method.upper()
        req_headers = header_map(request.get("headers", {}), f"{base}/request/headers", findings)
        res_headers = header_map(response.get("headers", {}), f"{base}/response/headers", findings)
        body = request.get("body")

        if method == "POST":
            if not has_accept(req_headers, {"application/json", "text/event-stream"}):
                findings.append(Finding("error", "invalid_post_accept", f"{base}/request/headers", "POST Accept must list application/json and text/event-stream"))
            if not is_jsonrpc_message(body):
                findings.append(Finding("error", "invalid_jsonrpc_body", f"{base}/request/body", "POST body must be one JSON-RPC 2.0 object"))
        elif method == "GET":
            if not profile["get"]:
                findings.append(Finding("error", "get_removed_in_profile", f"{base}/request/method", "this draft profile has no standalone GET stream"))
            if not has_accept(req_headers, {"text/event-stream"}):
                findings.append(Finding("error", "invalid_get_accept", f"{base}/request/headers", "GET Accept must include text/event-stream"))
        elif method == "DELETE":
            if not profile["sessions"]:
                findings.append(Finding("error", "delete_removed_in_profile", f"{base}/request/method", "this draft profile has no protocol session deletion"))
        else:
            findings.append(Finding("error", "unsupported_http_method", f"{base}/request/method", "normalized MCP transcript supports POST, GET, or DELETE"))

        version = req_headers.get("mcp-protocol-version")
        if method == "POST" and version != profile["version"]:
            findings.append(Finding("error", "protocol_version_mismatch", f"{base}/request/headers", f"expected MCP-Protocol-Version {profile['version']}"))
        if not profile["sessions"] and "mcp-session-id" in req_headers:
            findings.append(Finding("error", "session_header_removed", f"{base}/request/headers", "Mcp-Session-Id is removed in this draft profile"))
        if "last-event-id" in req_headers:
            if not profile["resumability"]:
                findings.append(Finding("error", "resumability_removed", f"{base}/request/headers", "Last-Event-ID is removed in this draft profile"))
            elif method != "GET":
                findings.append(Finding("error", "invalid_resume_method", f"{base}/request/method", "2025-11-25 resumption uses GET"))

        if profile["draft"] and method == "POST":
            rpc_method = body_method(body)
            if rpc_method is None:
                findings.append(Finding("error", "draft_response_post_removed", f"{base}/request/body", "draft profile POST body must be a JSON-RPC request or notification"))
            if req_headers.get("mcp-method") != rpc_method:
                findings.append(Finding("error", "method_header_mismatch", f"{base}/request/headers", "Mcp-Method must equal the JSON-RPC method"))
            meta_version = None
            if isinstance(body, dict):
                params = body.get("params")
                if isinstance(params, dict) and isinstance(params.get("_meta"), dict):
                    meta_version = params["_meta"].get("io.modelcontextprotocol/protocolVersion")
            if meta_version != profile["version"]:
                findings.append(Finding("error", "body_version_mismatch", f"{base}/request/body", "draft profile requires matching protocolVersion in params._meta"))

        status = response.get("status")
        if not isinstance(status, int) or isinstance(status, bool) or not 100 <= status <= 599:
            findings.append(Finding("error", "invalid_status", f"{base}/response/status", "status must be an HTTP integer from 100 through 599"))
        content_type = media_type(res_headers.get("content-type", ""))
        events: list[dict[str, Any]] = []
        if method == "GET" and isinstance(status, int) and not isinstance(status, bool) and 200 <= status < 300 and status != 200:
            findings.append(Finding("error", "invalid_get_response_status", f"{base}/response/status", "successful GET stream must use status 200"))
        if content_type == "text/event-stream":
            events = parse_sse(response.get("chunks"), f"{base}/response/chunks", findings)
            for event in events:
                if profile["draft"] and "id" in event:
                    findings.append(Finding("error", "event_id_removed", f"{base}/response/chunks/{event['index']}", "draft profile does not support resumable SSE event IDs"))
                payload = event.get("json")
                if "data" in event and event.get("data") and not is_jsonrpc_message(payload):
                    findings.append(Finding("error", "invalid_sse_jsonrpc", f"{base}/response/chunks/{event['index']}", "non-empty SSE data must contain one JSON-RPC 2.0 message"))
                if isinstance(payload, dict):
                    signature = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    if concurrent_group is not None:
                        key = (concurrent_group, signature)
                        previous = stream_payloads.get(key)
                        if previous is not None and previous != exchange_id:
                            level = "error" if "id" in payload else "warning"
                            findings.append(Finding(level, "cross_stream_duplicate", f"{base}/response/chunks/{event['index']}", f"same JSON-RPC payload already appeared on concurrent stream {previous}; notifications without IDs require manual correlation"))
                        stream_payloads[key] = exchange_id
        elif status == 200 and method == "POST" and content_type != "application/json":
            findings.append(Finding("error", "invalid_response_content_type", f"{base}/response/headers", "request response must be application/json or text/event-stream"))
        elif isinstance(status, int) and not isinstance(status, bool) and 200 <= status < 300 and method == "GET":
            findings.append(Finding("error", "invalid_get_response_content_type", f"{base}/response/headers", "successful GET must return text/event-stream"))

        disconnected = response.get("disconnected", False)
        if not isinstance(disconnected, bool):
            findings.append(Finding("error", "invalid_disconnected", f"{base}/response/disconnected", "disconnected must be boolean"))
        elif disconnected and content_type == "text/event-stream":
            last_event_id = None
            for event in events:
                if "id" in event:
                    last_event_id = event["id"]
            idempotent = exchange.get("idempotent")
            if profile["resumability"] and last_event_id:
                recovery.append({"exchange": exchange_id, "action": "resume-with-get", "condition": "send only Last-Event-ID and any required session header; do not replay the POST"})
            elif idempotent is True:
                recovery.append({"exchange": exchange_id, "action": "manual-reissue-with-fresh-jsonrpc-id", "condition": "operator confirms no result was committed and retry policy permits reissue"})
            else:
                recovery.append({"exchange": exchange_id, "action": "do-not-replay", "condition": "idempotency was not explicitly proven"})

    valid = not any(item.level == "error" for item in findings)
    return {
        "valid": valid,
        "profile": profile_name,
        "draft": profile["draft"],
        "normative": not profile["draft"],
        "findings": [asdict(item) for item in findings],
        "recovery": recovery,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--report", choices=("human", "json"), default="human")
    args = parser.parse_args(argv)
    try:
        document = load_json(args.transcript)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    result = validate(document)
    if args.report == "json":
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    else:
        print(f"profile: {result['profile']}" + (" (NON-NORMATIVE DRAFT)" if result["draft"] else ""))
        print(f"result: {'PASS' if result['valid'] else 'FAIL'}")
        for item in result["findings"]:
            print(f"{item['level'].upper()} {item['code']} {item['path']}: {item['message']}")
        for item in result["recovery"]:
            print(f"RECOVERY {item['exchange']}: {item['action']} — {item['condition']}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
