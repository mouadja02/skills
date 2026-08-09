#!/usr/bin/env python3
"""Offline PgBouncer prepared-statement compatibility classifier."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MODES = {"none", "session", "transaction", "statement"}
PREPARATION = {"none", "sql_prepare", "protocol_unnamed", "protocol_named"}
OPERATIONS = {"query", "migration", "copy"}


def load_strict(path: Path) -> object:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard JSON number: {value}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=reject_constant)


def validate(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("input must be a JSON object")
    required = {
        "pool_mode", "preparation_kind", "max_prepared_statements",
        "client_statement_cache", "operation", "concurrent_clients",
    }
    missing = sorted(required - data.keys())
    unknown = sorted(data.keys() - required)
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))
    if unknown:
        raise ValueError("unknown fields: " + ", ".join(unknown))
    if data["pool_mode"] not in MODES:
        raise ValueError("invalid pool_mode")
    if data["preparation_kind"] not in PREPARATION:
        raise ValueError("invalid preparation_kind")
    if data["operation"] not in OPERATIONS:
        raise ValueError("invalid operation")
    if type(data["client_statement_cache"]) is not bool:
        raise ValueError("client_statement_cache must be boolean")
    for field in ("max_prepared_statements", "concurrent_clients"):
        value = data[field]
        if type(value) is not int:
            raise ValueError(f"{field} must be an integer")
    if not 0 <= data["max_prepared_statements"] <= 1_000_000:
        raise ValueError("max_prepared_statements must be between 0 and 1000000")
    if not 1 <= data["concurrent_clients"] <= 1_000_000:
        raise ValueError("concurrent_clients must be between 1 and 1000000")
    return data


def analyze(data: dict) -> dict:
    mode = data["pool_mode"]
    prep = data["preparation_kind"]
    observations: list[dict] = []
    findings: list[dict] = []

    if mode == "none":
        return {
            "applicable": False,
            "classification": "not_applicable",
            "observations": [{"code": "NO_POOLER", "detail": "No pooler boundary was declared."}],
            "findings": [],
            "recommended_mode": None,
            "verification": ["Use query-performance or direct-session diagnostics instead."],
        }

    if mode == "session":
        observations.append({"code": "SESSION_AFFINITY", "detail": "A backend session remains assigned for the client session."})
    else:
        observations.append({"code": "BACKEND_REASSIGNMENT", "detail": "Backend session identity can change before the next client statement."})

    if prep == "protocol_named" and not data["client_statement_cache"]:
        observations.append({
            "code": "NAMED_PREPARATION_DESPITE_CACHE_OFF",
            "detail": "Observed protocol-level naming is stronger evidence than a disabled client cache; special paths can still prepare.",
        })

    if mode in {"transaction", "statement"} and prep == "sql_prepare":
        findings.append({
            "code": "SQL_PREPARE_REQUIRES_SESSION_AFFINITY",
            "severity": "error",
            "detail": "SQL PREPARE creates session state and cannot safely follow backend reassignment.",
        })

    if mode in {"transaction", "statement"} and prep == "protocol_named":
        if data["max_prepared_statements"] == 0:
            findings.append({
                "code": "PROTOCOL_TRACKING_DISABLED",
                "severity": "error",
                "detail": "Named protocol statements cross a reassignment boundary while PgBouncer tracking is disabled.",
            })
        else:
            observations.append({
                "code": "PROTOCOL_TRACKING_CONFIGURED",
                "detail": "PgBouncer protocol-level tracking is configured; compatibility still needs a reassignment fixture.",
            })

    if mode == "statement" and data["operation"] in {"migration", "copy"}:
        findings.append({
            "code": "STATEMENT_POOL_OPERATION_BOUNDARY",
            "severity": "error",
            "detail": "The operation needs a broader lifecycle check than statement pooling can safely assume.",
        })
    elif mode == "transaction" and data["operation"] == "migration":
        findings.append({
            "code": "MIGRATION_SESSION_STATE_RISK",
            "severity": "error",
            "detail": "Route migrations through a direct or session-affine endpoint unless the migration is proven transaction-local.",
        })

    if findings:
        classification = "incompatible"
        recommended = "session"
    elif mode in {"transaction", "statement"} and prep == "protocol_named":
        classification = "conditionally_compatible"
        recommended = mode
    else:
        classification = "compatible_by_declared_invariants"
        recommended = mode

    return {
        "applicable": True,
        "classification": classification,
        "observations": observations,
        "findings": findings,
        "recommended_mode": recommended,
        "verification": [
            "Run fresh-connection and reused-connection controls.",
            "Force more concurrent clients than backend connections and prove backend reassignment.",
            "Exercise the exact query, COPY, or migration path and compare result bytes/errors.",
            "Verify pool reuse and server-side prepared-statement counts after the run.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(validate(load_strict(args.input)))
        encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(encoded, encoding="utf-8")
        else:
            sys.stdout.write(encoded)
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
