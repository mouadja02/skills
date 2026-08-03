#!/usr/bin/env python3
"""Classify a redacted CRD storage-version upgrade evidence packet offline."""
import argparse
import json
import os
import sys
from pathlib import Path

class InputError(ValueError):
    pass

def reject_constant(value):
    raise InputError(f"non-standard JSON number: {value}")

def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise InputError(f"duplicate key: {key}")
        out[key] = value
    return out

def load_packet(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot read input: {exc}") from exc
    try:
        data = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (json.JSONDecodeError, InputError) as exc:
        raise InputError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise InputError("root must be an object")
    return data

def exact_keys(obj, required, optional=(), where="object"):
    if not isinstance(obj, dict):
        raise InputError(f"{where} must be an object")
    required, allowed = set(required), set(required) | set(optional)
    missing, unknown = sorted(required - set(obj)), sorted(set(obj) - allowed)
    if missing:
        raise InputError(f"{where} missing fields: {', '.join(missing)}")
    if unknown:
        raise InputError(f"{where} unknown fields: {', '.join(unknown)}")

def string(value, where, nonempty=True):
    if not isinstance(value, str):
        raise InputError(f"{where} must be a string")
    if nonempty and not value.strip():
        raise InputError(f"{where} must not be empty")
    return value.strip()

def boolean(value, where):
    if type(value) is not bool:
        raise InputError(f"{where} must be a boolean")
    return value

def integer(value, where):
    if type(value) is not int or value < 0:
        raise InputError(f"{where} must be a non-negative integer")
    return value

def string_list(value, where):
    if not isinstance(value, list) or not value:
        raise InputError(f"{where} must be a non-empty array")
    values = [string(v, f"{where}[]") for v in value]
    if len(values) != len(set(values)):
        raise InputError(f"{where} must contain unique values")
    return values

def finding(code, message):
    return {"code": code, "message": message}

def classify(packet):
    exact_keys(packet, ("schema_version", "kind", "target_type"),
               ("cluster", "crd", "migration", "round_trip_fixtures", "retirement", "rollback"), "root")
    if type(packet["schema_version"]) is not int or packet["schema_version"] != 1:
        raise InputError("schema_version must equal integer 1")
    if packet["kind"] != "kubernetes_crd_storage_upgrade_preflight":
        raise InputError("unsupported kind")
    target = string(packet["target_type"], "target_type")
    if target != "kubernetes_crd_upgrade":
        return {"schema_version": 1, "status": "not_applicable", "target_type": target,
                "findings": [], "mutation_permitted": False}

    exact_keys(packet, ("schema_version", "kind", "target_type", "cluster", "crd", "migration",
                        "round_trip_fixtures", "retirement", "rollback"), where="root")
    findings = []
    cluster = packet["cluster"]
    exact_keys(cluster, ("kubernetes_version", "disposable", "backup_verified"), where="cluster")
    version = string(cluster["kubernetes_version"], "cluster.kubernetes_version", nonempty=False)
    if not version:
        findings.append(finding("CLUSTER_VERSION_UNPINNED", "Pin the target Kubernetes version."))
    if not boolean(cluster["disposable"], "cluster.disposable"):
        findings.append(finding("NON_DISPOSABLE_TEST_BOUNDARY", "Run conversion and outage probes on a disposable cluster."))
    if not boolean(cluster["backup_verified"], "cluster.backup_verified"):
        findings.append(finding("BACKUP_UNVERIFIED", "Verify an API/etcd backup and restore boundary before migration."))

    crd = packet["crd"]
    exact_keys(crd, ("name", "current_storage_version", "desired_storage_version", "served_versions",
                     "stored_versions", "conversion_strategy", "webhook"), where="crd")
    string(crd["name"], "crd.name")
    current = string(crd["current_storage_version"], "crd.current_storage_version")
    desired = string(crd["desired_storage_version"], "crd.desired_storage_version")
    served = string_list(crd["served_versions"], "crd.served_versions")
    stored = string_list(crd["stored_versions"], "crd.stored_versions")
    if current not in served:
        findings.append(finding("CURRENT_STORAGE_NOT_SERVED", "The current storage version must remain served during migration."))
    if desired not in served:
        findings.append(finding("DESIRED_STORAGE_NOT_SERVED", "The desired storage version is not served."))
    strategy = string(crd["conversion_strategy"], "crd.conversion_strategy")
    if strategy not in ("None", "Webhook"):
        raise InputError("crd.conversion_strategy must be None or Webhook")
    webhook = crd["webhook"]
    exact_keys(webhook, ("service_exists", "endpoints_ready", "ca_valid", "ownership_known", "outage_probe_completed"), where="crd.webhook")
    checks = {k: boolean(webhook[k], f"crd.webhook.{k}") for k in webhook}
    if strategy == "Webhook":
        codes = {
            "service_exists": "WEBHOOK_SERVICE_MISSING", "endpoints_ready": "WEBHOOK_ENDPOINTS_UNREADY",
            "ca_valid": "WEBHOOK_CA_INVALID", "ownership_known": "WEBHOOK_OWNERSHIP_UNKNOWN",
            "outage_probe_completed": "WEBHOOK_OUTAGE_UNTESTED"}
        for key, code in codes.items():
            if not checks[key]:
                findings.append(finding(code, f"Conversion webhook check failed: {key}."))

    migration = packet["migration"]
    exact_keys(migration, ("method", "feature_enabled", "objects_before", "objects_after", "rewrite_completed"), where="migration")
    method = string(migration["method"], "migration.method")
    feature_enabled = boolean(migration["feature_enabled"], "migration.feature_enabled")
    before = integer(migration["objects_before"], "migration.objects_before")
    after = integer(migration["objects_after"], "migration.objects_after")
    rewrite = boolean(migration["rewrite_completed"], "migration.rewrite_completed")
    if method not in ("storage_version_migration", "controlled_rewrite"):
        raise InputError("migration.method must be storage_version_migration or controlled_rewrite")
    if method == "storage_version_migration" and not feature_enabled:
        findings.append(finding("STORAGE_MIGRATION_API_DISABLED", "StorageVersionMigration was selected but its API is not enabled."))
    if before != after:
        findings.append(finding("OBJECT_COUNT_CHANGED", "Object counts differ across the migration boundary."))
    if not rewrite:
        findings.append(finding("REWRITE_INCOMPLETE", "Stored objects have not all been rewritten."))
    if rewrite and desired not in stored:
        findings.append(finding("DESIRED_VERSION_NOT_RECORDED", "The desired version is absent from status.storedVersions after rewrite."))

    fixtures = packet["round_trip_fixtures"]
    if not isinstance(fixtures, list) or not fixtures:
        raise InputError("round_trip_fixtures must be a non-empty array")
    ids = set()
    covered = set()
    for i, fixture in enumerate(fixtures):
        where = f"round_trip_fixtures[{i}]"
        exact_keys(fixture, ("id", "from_version", "to_version", "back_to_version", "equal", "unknown_field_checked"), where=where)
        fid = string(fixture["id"], f"{where}.id")
        if fid in ids:
            raise InputError("round_trip_fixtures ids must be unique")
        ids.add(fid)
        source = string(fixture["from_version"], f"{where}.from_version")
        destination = string(fixture["to_version"], f"{where}.to_version")
        back = string(fixture["back_to_version"], f"{where}.back_to_version")
        if source not in served or destination not in served or back != source:
            findings.append(finding("ROUND_TRIP_VERSION_INVALID", f"Fixture {fid} does not form a served-version round trip."))
        covered.update((source, destination))
        if not boolean(fixture["equal"], f"{where}.equal"):
            findings.append(finding("ROUND_TRIP_DATA_LOSS", f"Fixture {fid} did not round-trip losslessly."))
        if not boolean(fixture["unknown_field_checked"], f"{where}.unknown_field_checked"):
            findings.append(finding("UNKNOWN_FIELD_UNTESTED", f"Fixture {fid} omits an unknown/pruned-field probe."))
    if not set(served).issubset(covered):
        findings.append(finding("SERVED_VERSION_COVERAGE_INCOMPLETE", "Round-trip fixtures do not cover every served version."))

    retirement = packet["retirement"]
    exact_keys(retirement, ("old_version", "served_false", "stored_absent", "clients_checked", "conversion_support_retained"), where="retirement")
    old = string(retirement["old_version"], "retirement.old_version")
    if old != current:
        findings.append(finding("RETIREMENT_VERSION_MISMATCH", "Retirement target differs from the recorded current storage version."))
    retirement_checks = {k: boolean(retirement[k], f"retirement.{k}") for k in ("served_false", "stored_absent", "clients_checked", "conversion_support_retained")}
    for key, code in (("stored_absent", "OLD_VERSION_STILL_STORED"), ("clients_checked", "OLD_VERSION_CLIENTS_UNCHECKED"), ("conversion_support_retained", "CONVERSION_ROLLBACK_REMOVED")):
        if not retirement_checks[key]:
            findings.append(finding(code, f"Old-version retirement check failed: {key}."))
    if retirement_checks["served_false"] and (not retirement_checks["stored_absent"] or not rewrite):
        findings.append(finding("OLD_VERSION_UNSERVED_TOO_EARLY", "The old version is unserved before storage migration is proven complete."))

    rollback = packet["rollback"]
    exact_keys(rollback, ("documented", "backup_restore_rehearsed"), where="rollback")
    if not boolean(rollback["documented"], "rollback.documented"):
        findings.append(finding("ROLLBACK_UNDOCUMENTED", "Document a bounded rollback sequence."))
    if not boolean(rollback["backup_restore_rehearsed"], "rollback.backup_restore_rehearsed"):
        findings.append(finding("RESTORE_UNREHEARSED", "Rehearse restore on the disposable boundary."))

    return {"schema_version": 1, "status": "fail" if findings else "pass", "target_type": target,
            "findings": findings, "mutation_permitted": False}

def write_report(report, path):
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if path == "-":
        sys.stdout.write(text)
        return
    target = Path(path)
    try:
        with target.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except (OSError, UnicodeError, ValueError) as exc:
        raise InputError(f"cannot write report: {exc}") from exc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="-")
    args = parser.parse_args()
    try:
        report = classify(load_packet(args.input))
        write_report(report, args.output)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1 if report["status"] == "fail" else 0
if __name__ == "__main__":
    raise SystemExit(main())
