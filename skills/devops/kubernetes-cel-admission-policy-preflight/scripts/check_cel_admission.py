#!/usr/bin/env python3
"""Fail-closed offline checker for Kubernetes native CEL admission preflight evidence."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


class InputError(ValueError):
    pass


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in items:
        if key in out:
            raise InputError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _constant(value: str) -> None:
    raise InputError(f"non-standard JSON number: {value}")


def _object(value: Any, where: str, required: set[str], optional: set[str] = set()) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{where} must be an object")
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing:
        raise InputError(f"{where} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise InputError(f"{where} unknown fields: {', '.join(sorted(unknown))}")
    return value


def _string(value: Any, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise InputError(f"{where} must be a{' possibly empty' if allow_empty else ' non-empty'} string")
    return value


def _bool(value: Any, where: str) -> bool:
    if type(value) is not bool:
        raise InputError(f"{where} must be a boolean")
    return value


def _number(value: Any, where: str, *, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise InputError(f"{where} must be a finite number >= {minimum}")
    return float(value)


def _strings(value: Any, where: str, allowed: set[str] | None = None) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise InputError(f"{where} must be an array of non-empty strings")
    if len(set(value)) != len(value):
        raise InputError(f"{where} must not contain duplicates")
    if allowed is not None and any(v not in allowed for v in value):
        raise InputError(f"{where} contains an unsupported value")
    return value


def _enum(value: Any, where: str, allowed: set[str]) -> str:
    value = _string(value, where)
    if value not in allowed:
        raise InputError(f"{where} must be one of: {', '.join(sorted(allowed))}")
    return value


def _cycle_through(node: str, nodes: list[str], edges: list[list[str]]) -> bool:
    graph = {name: [] for name in nodes}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or any(not isinstance(v, str) for v in edge):
            raise InputError("bootstrap.edges entries must be two-string arrays")
        source, target = edge
        if source not in graph or target not in graph:
            raise InputError("bootstrap.edges must reference declared nodes")
        graph[source].append(target)
    stack = list(graph[node])
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current == node:
            return True
        if current not in seen:
            seen.add(current)
            stack.extend(graph[current])
    return False


def analyze(data: Any) -> dict[str, Any]:
    top = _object(data, "root", {"schema_version", "kind", "target_type", "inventory"},
                  {"policy", "bindings", "fixtures", "cost", "resources", "bootstrap", "rollout"})
    if type(top["schema_version"]) is not int or top["schema_version"] != 1:
        raise InputError("schema_version must be integer 1")
    if top["kind"] != "kubernetes_cel_admission_preflight":
        raise InputError("kind must be kubernetes_cel_admission_preflight")
    target_type = _string(top["target_type"], "target_type")
    inventory = _object(top["inventory"], "inventory", {"kubernetes_version", "cel_environment"})
    _string(inventory["kubernetes_version"], "inventory.kubernetes_version")
    _string(inventory["cel_environment"], "inventory.cel_environment", allow_empty=True)

    if target_type != "native_vap":
        return {
            "schema_version": 1,
            "status": "not_applicable",
            "target_type": target_type,
            "finding_codes": [],
            "findings": [],
            "mutation_permitted": False,
            "reason": "This checker only classifies native Kubernetes ValidatingAdmissionPolicy evidence packets."
        }

    for name in ("policy", "bindings", "fixtures", "cost", "resources", "bootstrap", "rollout"):
        if name not in top:
            raise InputError(f"root missing fields for native_vap: {name}")

    policy = _object(top["policy"], "policy", {"failure_policy", "match_operations", "required_context"})
    failure_policy = _enum(policy["failure_policy"], "policy.failure_policy", {"Fail", "Ignore"})
    operations = _strings(policy["match_operations"], "policy.match_operations", {"CREATE", "UPDATE", "DELETE", "CONNECT"})
    contexts = _strings(policy["required_context"], "policy.required_context",
                        {"object", "oldObject", "request.userInfo", "params"})
    if not operations:
        raise InputError("policy.match_operations must not be empty")

    bindings = top["bindings"]
    if not isinstance(bindings, list) or not bindings:
        raise InputError("bindings must be a non-empty array")
    all_actions: set[str] = set()
    binding_names: set[str] = set()
    for index, raw in enumerate(bindings):
        binding = _object(raw, f"bindings[{index}]", {"name", "validation_actions"})
        name = _string(binding["name"], f"bindings[{index}].name")
        if name in binding_names:
            raise InputError("binding names must be unique")
        binding_names.add(name)
        actions = _strings(binding["validation_actions"], f"bindings[{index}].validation_actions", {"Audit", "Warn", "Deny"})
        if not actions:
            raise InputError("validation_actions must not be empty")
        all_actions.update(actions)

    fixtures = top["fixtures"]
    if not isinstance(fixtures, list) or not fixtures:
        raise InputError("fixtures must be a non-empty array")
    fixture_rows = []
    ids: set[str] = set()
    for index, raw in enumerate(fixtures):
        fixture = _object(raw, f"fixtures[{index}]", {"id", "operation", "user_info", "old_object", "params", "outcome"})
        fixture_id = _string(fixture["id"], f"fixtures[{index}].id")
        if fixture_id in ids:
            raise InputError("fixture ids must be unique")
        ids.add(fixture_id)
        fixture_rows.append({
            "id": fixture_id,
            "operation": _enum(fixture["operation"], f"fixtures[{index}].operation", {"CREATE", "UPDATE", "DELETE", "CONNECT"}),
            "user_info": _bool(fixture["user_info"], f"fixtures[{index}].user_info"),
            "old_object": _enum(fixture["old_object"], f"fixtures[{index}].old_object", {"present", "null", "omitted"}),
            "params": _enum(fixture["params"], f"fixtures[{index}].params", {"present", "absent", "not_applicable"}),
            "outcome": _enum(fixture["outcome"], f"fixtures[{index}].outcome", {"allow", "deny", "error"}),
        })

    cost = _object(top["cost"], "cost", {"static_estimate_checked", "runtime_budget_observed"})
    static_checked = _bool(cost["static_estimate_checked"], "cost.static_estimate_checked")
    runtime_observed = _bool(cost["runtime_budget_observed"], "cost.runtime_budget_observed")

    resources = _object(top["resources"], "resources", {"baseline_mib", "observed_mib", "policy_binding_pairs", "max_extra_mib_per_pair"})
    baseline = _number(resources["baseline_mib"], "resources.baseline_mib")
    observed = _number(resources["observed_mib"], "resources.observed_mib")
    pairs = _number(resources["policy_binding_pairs"], "resources.policy_binding_pairs", minimum=1)
    if not pairs.is_integer():
        raise InputError("resources.policy_binding_pairs must be an integer")
    budget = _number(resources["max_extra_mib_per_pair"], "resources.max_extra_mib_per_pair")
    extra_per_pair = (observed - baseline) / pairs

    bootstrap = _object(top["bootstrap"], "bootstrap", {"policy_node", "nodes", "edges"})
    nodes = _strings(bootstrap["nodes"], "bootstrap.nodes")
    policy_node = _string(bootstrap["policy_node"], "bootstrap.policy_node")
    if policy_node not in nodes:
        raise InputError("bootstrap.policy_node must be a declared node")
    if not isinstance(bootstrap["edges"], list):
        raise InputError("bootstrap.edges must be an array")
    bootstrap_cycle = _cycle_through(policy_node, nodes, bootstrap["edges"])

    rollout = _object(top["rollout"], "rollout", {"stage", "canary_observed", "emergency_rollback_documented"})
    stage = _enum(rollout["stage"], "rollout.stage", {"Audit", "Warn", "Deny"})
    canary = _bool(rollout["canary_observed"], "rollout.canary_observed")
    rollback = _bool(rollout["emergency_rollback_documented"], "rollout.emergency_rollback_documented")

    findings: list[dict[str, str]] = []
    def add(code: str, message: str) -> None:
        findings.append({"code": code, "message": message})

    if not inventory["cel_environment"].strip():
        add("CEL_ENVIRONMENT_UNPINNED", "Record the exact Kubernetes CEL environment/version used by policy evaluation.")
    covered = {f["operation"] for f in fixture_rows}
    for operation in operations:
        if operation not in covered:
            add("OPERATION_UNTESTED", f"No fixture covers matched operation {operation}.")
    if "DELETE" in operations and not any(f["operation"] == "DELETE" and f["old_object"] == "present" for f in fixture_rows):
        add("DELETE_OLD_OBJECT_UNTESTED", "DELETE is matched but no DELETE fixture carries oldObject.")
    if "request.userInfo" in contexts and not any(f["user_info"] for f in fixture_rows):
        add("USER_INFO_UNTESTED", "The policy uses request.userInfo but no fixture includes it.")
    if "params" in contexts and not any(f["params"] == "absent" for f in fixture_rows):
        add("PARAMS_ABSENCE_UNTESTED", "The policy uses params but missing-parameter behavior is not covered.")
    if failure_policy == "Fail" and not any(f["outcome"] == "error" for f in fixture_rows):
        add("FAILURE_POLICY_UNTESTED", "Fail behavior is selected but no expression/error fixture observes it.")
    if not static_checked:
        add("STATIC_COST_UNCHECKED", "Static CEL cost estimation was not checked.")
    if not runtime_observed:
        add("RUNTIME_COST_UNOBSERVED", "Runtime cost-budget behavior was not observed on the pinned environment.")
    if extra_per_pair > budget:
        add("RESOURCE_BUDGET_EXCEEDED", f"Observed {extra_per_pair:.3f} MiB per policy-binding pair exceeds {budget:.3f} MiB.")
    if bootstrap_cycle:
        add("BOOTSTRAP_DEPENDENCY_CYCLE", "The policy node participates in a declared startup dependency cycle.")
    if stage not in all_actions:
        add("ROLLOUT_ACTION_MISMATCH", "The rollout stage is not present in any binding validation action.")
    if (stage == "Deny" or "Deny" in all_actions) and not canary:
        add("DENY_WITHOUT_CANARY", "Deny is selected without an observed Audit/Warn canary.")
    if not rollback:
        add("ROLLBACK_UNDOCUMENTED", "Emergency rollback is not documented.")

    return {
        "schema_version": 1,
        "status": "fail" if findings else "pass",
        "target_type": target_type,
        "finding_codes": [item["code"] for item in findings],
        "findings": findings,
        "metrics": {"fixture_count": len(fixture_rows), "extra_mib_per_pair": round(extra_per_pair, 6)},
        "mutation_permitted": False,
    }


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read valid UTF-8 JSON from {path}: {exc}") from exc


def emit(report: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        try:
            sys.stdout.write(payload)
        except OSError as exc:
            raise InputError(f"cannot write report: {exc}") from exc
        return
    output = output.resolve()
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, output)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as exc:
        raise InputError(f"cannot write report to {output}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = analyze(load(args.input))
        emit(report, args.output)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
