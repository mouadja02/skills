#!/usr/bin/env python3
"""Scaffold reviewable dbt model contracts from dbt artifacts.

Reads a dbt ``manifest.json`` and ``catalog.json`` plus an existing properties
YAML file, then emits (a) a proposed properties YAML document with
``config.contract.enforced: true`` and per-column ``data_type`` and (b) a
machine-readable report explaining every decision.

Design rules that make the output safe to review:

* metadata is evidence, never authority -- types come from the compiled
  catalog, nothing is inferred from data samples or from the rendered SQL;
* existing ``description``, ``data``, ``tests``, ``meta``, ``tags`` and
  ``constraints`` are preserved by column name;
* anything ambiguous is blocked with a reason instead of guessed;
* the properties file is never edited in place unless ``--apply`` is paired
  with ``--snapshot-dir``, which stores a verified copy first.

Exit codes: 0 proposal written, 2 refused (bad input / ambiguous state /
unsafe apply), 3 write failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on bare interpreters
    sys.stderr.write("scaffold_contracts: PyYAML is required (pip install pyyaml)\n")
    raise SystemExit(2)

SCHEMA_VERSION = 1

# Materializations that dbt can enforce a contract on without extra caveats.
CONTRACT_SAFE_MATERIALIZATIONS = {"table", "view"}

# Materializations that may support contracts but need a human decision first.
CONTRACT_CAVEAT_MATERIALIZATIONS = {
    "incremental": (
        "incremental models accept contracts, but on_schema_change must be set to "
        "'fail' or 'append_new_columns'; a contract cannot retro-fit type changes. "
        "Choose the strategy before enabling enforcement."
    ),
    "materialized_view": (
        "materialized views support contracts only on adapters that expose column "
        "types at creation time; verify the target adapter before enforcing."
    ),
}

NON_CONTRACTABLE_MATERIALIZATIONS = {
    "ephemeral": "ephemeral models are inlined as CTEs and have no physical columns to contract.",
    "snapshot": "snapshots are managed by dbt; contracts are not supported on snapshot resources.",
}

# Types whose column shape is nested/opaque: dbt contracts cannot express them.
UNSUPPORTED_TYPE_KEYWORDS = {
    "variant",
    "object",
    "array",
    "map",
    "struct",
    "json",
    "jsonb",
    "super",
    "geometry",
    "geography",
    "xml",
    "hllsketch",
}

# Adapters that do not enforce a length/byte-size parameter on character types.
LENGTH_NOT_ENFORCED_ADAPTERS = {
    "snowflake",
    "bigquery",
    "databricks",
    "spark",
    "athena",
    "trino",
    "duckdb",
}

CHARACTER_TYPE_RE = re.compile(
    r"^(varchar|nvarchar|char|nchar|character\s+varying|character|string|text)\s*"
    r"(?:\(\s*(\d+)\s*(?:(max|byte|char|bytes|chars))?\s*\))?$",
    re.IGNORECASE,
)

NUMERIC_TYPE_RE = re.compile(
    r"^(numeric|decimal|number|dec)\s*(?:\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?\))?$",
    re.IGNORECASE,
)

NESTED_SHAPE_RE = re.compile(r"[<>\[\]{}|]")


class Refused(Exception):
    """Raised for input states that must stop the run (exit code 2)."""


class WriteFailure(Exception):
    """Raised when the proposal or snapshot cannot be written (exit code 3)."""


class StrictLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys rather than keeping the last."""


def _construct_mapping(loader: StrictLoader, node, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise Refused(f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _reject_json_constant(name: str):
    raise Refused(f"non-standard JSON constant {name!r} is not valid dbt artifact output")


def load_json(path: Path, label: str) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Refused(f"cannot read {label} at {path}: {exc.strerror or exc}") from exc
    try:
        doc = json.loads(raw, parse_constant=_reject_json_constant)
    except Refused:
        raise
    except json.JSONDecodeError as exc:
        raise Refused(f"{label} at {path} is not valid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise Refused(f"{label} at {path} must be a JSON object, got {type(doc).__name__}")
    return doc


def load_properties(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Refused(f"cannot read properties YAML at {path}: {exc.strerror or exc}") from exc
    try:
        doc = yaml.load(raw, Loader=StrictLoader)  # noqa: S506 - StrictLoader subclasses SafeLoader
    except Refused:
        raise
    except yaml.YAMLError as exc:
        raise Refused(f"properties YAML at {path} does not parse: {exc}") from exc
    if doc is None:
        return {"version": 2}
    if not isinstance(doc, dict):
        raise Refused(f"properties YAML at {path} must map keys at the top level")
    return doc


def clean_type(raw_type: str) -> str:
    """Collapse whitespace and strip identifier quotes; keep parameter lists intact."""
    cleaned = " ".join(str(raw_type).strip().split())
    cleaned = cleaned.strip('"`')
    return cleaned


def normalize_type(raw_type: str, adapter: str) -> tuple[str, list[str], str | None]:
    """Return (data_type, warnings, block_reason)."""
    cleaned = clean_type(raw_type)
    if not cleaned:
        return "", [], "catalog reported an empty type"
    if NESTED_SHAPE_RE.search(cleaned):
        return cleaned, [], f"nested or parameterised shape {cleaned!r} cannot be expressed as a dbt contract type"
    lowered = cleaned.lower()
    base = re.split(r"[\s(]", lowered, maxsplit=1)[0]
    if base in UNSUPPORTED_TYPE_KEYWORDS:
        return cleaned, [], f"type {cleaned!r} is nested/opaque; dbt contracts cannot express it"

    warnings: list[str] = []
    numeric = NUMERIC_TYPE_RE.match(cleaned)
    if numeric:
        base_name = numeric.group(1).lower()
        precision, scale = numeric.group(2), numeric.group(3)
        if precision is None:
            warnings.append(f"numeric type {cleaned!r} has no declared precision; confirm the warehouse default")
            return base_name, warnings, None
        if scale is None:
            return f"{base_name}({precision})", warnings, None
        return f"{base_name}({precision},{scale})", warnings, None

    character = CHARACTER_TYPE_RE.match(cleaned)
    if character:
        base_name = " ".join(character.group(1).lower().split())
        length = character.group(2)
        if length and adapter in LENGTH_NOT_ENFORCED_ADAPTERS:
            warnings.append(
                f"{adapter} does not enforce length {length} on {cleaned!r}; "
                "emitted the bare type so the contract is not falsely precise"
            )
            return base_name, warnings, None
        if length:
            return f"{base_name}({length})", warnings, None
        return base_name, warnings, None

    if lowered.endswith("[]") or "(" in cleaned and lowered.startswith(("array", "map", "struct")):
        return cleaned, [], f"collection type {cleaned!r} is not contractable"

    return cleaned.upper() if lowered != cleaned.lower() else cleaned, warnings, None


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def catalog_columns(catalog: dict) -> dict[str, dict]:
    """Map model unique_id -> {column_name: catalog node}."""
    nodes = catalog.get("nodes")
    if not isinstance(nodes, dict):
        raise Refused("catalog.json has no 'nodes' object -- run `dbt docs generate` first")
    result = {}
    for uid, node in nodes.items():
        if not isinstance(node, dict):
            continue
        columns = node.get("columns")
        if isinstance(columns, dict):
            result[uid] = columns
    return result


def select_models(manifest: dict, only: set[str] | None, exclude_packages: set[str]):
    nodes = manifest.get("nodes")
    if not isinstance(nodes, dict):
        raise Refused("manifest.json has no 'nodes' object -- is this a dbt manifest?")
    selected = []
    for uid, node in nodes.items():
        if not isinstance(node, dict) or node.get("resource_type") != "model":
            continue
        name = node.get("name") or uid.split(".")[-1]
        package = node.get("package_name") or ""
        node_config = node.get("config")
        config = node_config if isinstance(node_config, dict) else {}
        materialized = config.get("materialized") or "view"
        if only and name not in only:
            continue
        if package in exclude_packages:
            continue
        selected.append(
            {
                "unique_id": uid,
                "name": name,
                "package": package,
                "materialized": str(materialized).lower(),
            }
        )
    if only:
        missing = {n for n in only if n not in {m["name"] for m in selected}}
        for name in sorted(missing):
            raise Refused(f"requested model {name!r} is not a model in this manifest")
    selected.sort(key=lambda m: (m["package"], m["name"]))
    return selected


def existing_model_entry(doc: dict, model_name: str) -> dict | None:
    models = doc.get("models")
    if not isinstance(models, list):
        return None
    matches = [e for e in models if isinstance(e, dict) and e.get("name") == model_name]
    if len(matches) > 1:
        raise Refused(
            f"properties YAML declares model {model_name!r} {len(matches)} times; "
            "resolve the duplicate before scaffolding so the target entry is unambiguous"
        )
    return matches[0] if matches else None


def index_existing_columns(entry: dict | None) -> dict[str, dict]:
    columns = {}
    if not entry or not isinstance(entry.get("columns"), list):
        return columns
    for column in entry["columns"]:
        if isinstance(column, dict) and column.get("name"):
            columns[str(column["name"]).lower()] = column
    return columns


def merge_column(existing: dict | None, name: str, data_type: str) -> tuple[dict, int]:
    """Preserve existing column semantics, set the catalog type."""
    merged: dict = {"name": name}
    preserved = 0
    if existing:
        for key, value in existing.items():
            if key == "name":
                continue
            merged[key] = value
            if key in {"description", "tests", "data_tests", "meta", "tags", "constraints", "quote"}:
                preserved += 1
    merged["data_type"] = data_type
    return merged, preserved


def build_proposal(manifest, catalog, doc, adapter, only, exclude_packages):
    columns_by_uid = catalog_columns(catalog)
    models = select_models(manifest, only, exclude_packages)

    seen_names: dict[str, list[str]] = {}
    for model in models:
        seen_names.setdefault(model["name"], []).append(model["unique_id"])

    report_models = []
    ready_entries = []
    total_columns = 0

    for model in models:
        record = {
            "unique_id": model["unique_id"],
            "name": model["name"],
            "package": model["package"],
            "materialized": model["materialized"],
            "status": "READY",
            "reasons": [],
            "warnings": [],
            "column_count": 0,
            "columns_preserved": 0,
            "blocked_columns": [],
        }

        duplicates = seen_names.get(model["name"], [])
        if len(duplicates) > 1:
            record["status"] = "BLOCKED_DUPLICATE_NAME"
            record["reasons"].append(
                "model name collides across packages: " + ", ".join(sorted(duplicates))
            )

        if record["status"] == "READY" and model["materialized"] in NON_CONTRACTABLE_MATERIALIZATIONS:
            record["status"] = "SKIPPED_MATERIALIZATION"
            record["reasons"].append(NON_CONTRACTABLE_MATERIALIZATIONS[model["materialized"]])
        elif record["status"] == "READY" and model["materialized"] in CONTRACT_CAVEAT_MATERIALIZATIONS:
            record["status"] = "SKIPPED_MATERIALIZATION"
            record["reasons"].append(CONTRACT_CAVEAT_MATERIALIZATIONS[model["materialized"]])
        elif record["status"] == "READY" and model["materialized"] not in CONTRACT_SAFE_MATERIALIZATIONS:
            record["status"] = "SKIPPED_MATERIALIZATION"
            record["reasons"].append(f"materialization {model['materialized']!r} is not contract-safe by default")

        columns = columns_by_uid.get(model["unique_id"])
        if record["status"] == "READY" and not columns:
            record["status"] = "SKIPPED_NOT_IN_CATALOG"
            record["reasons"].append(
                "model has no catalog columns (model not built, or `dbt docs generate` is stale); "
                "build the model and regenerate catalog.json before scaffolding"
            )

        if record["status"] != "READY":
            report_models.append(record)
            continue

        entry = existing_model_entry(doc, model["name"])
        existing_columns = index_existing_columns(entry)
        proposed_columns = []
        warnings: list[str] = []
        for column_name, column_node in sorted(columns.items()):
            raw_type = ""
            if isinstance(column_node, dict):
                raw_type = column_node.get("type") or ""
            data_type, type_warnings, block_reason = normalize_type(str(raw_type), adapter)
            warnings.extend(f"{column_name}: {w}" for w in type_warnings)
            if block_reason:
                record["blocked_columns"].append({"name": str(column_name), "reason": block_reason})
                continue
            merged, preserved = merge_column(existing_columns.get(str(column_name).lower()), str(column_name), data_type)
            record["columns_preserved"] += preserved
            proposed_columns.append(merged)

        if record["blocked_columns"]:
            record["status"] = "BLOCKED_COLUMN_TYPE"
            record["reasons"].append(
                f"{len(record['blocked_columns'])} column(s) cannot be expressed as a dbt contract; "
                "hand-author or exclude them before enabling enforcement"
            )
            record["warnings"] = warnings
            report_models.append(record)
            continue

        if not proposed_columns:
            record["status"] = "BLOCKED_EMPTY_COLUMNS"
            record["reasons"].append("catalog reported zero columns for this model")
            report_models.append(record)
            continue

        record["column_count"] = len(proposed_columns)
        record["warnings"] = warnings
        report_models.append(record)

        merged_entry = dict(entry) if entry else {"name": model["name"]}
        entry_config = merged_entry.get("config")
        model_config = entry_config if isinstance(entry_config, dict) else {}
        config = dict(model_config)
        config["contract"] = {"enforced": True}
        merged_entry["config"] = config
        merged_entry["columns"] = proposed_columns
        ready_entries.append(merged_entry)
        total_columns += len(proposed_columns)

    return report_models, ready_entries, total_columns


def apply_proposal(doc, ready_entries, report_models):
    """Merge proposed model entries into a copy of the properties document."""
    out = dict(doc)
    models = out.get("models")
    models = list(models) if isinstance(models, list) else []
    ready_by_name = {str(e["name"]): e for e in ready_entries}
    replaced = set()
    for index, entry in enumerate(models):
        if isinstance(entry, dict) and entry.get("name") in ready_by_name:
            name = str(entry["name"])
            models[index] = ready_by_name[name]
            replaced.add(name)
    for name, entry in ready_by_name.items():
        if name not in replaced:
            models.append(entry)
    models.sort(key=lambda e: str(e.get("name", "")))
    out["models"] = models
    if "version" not in out:
        out = {"version": 2, **out}
    return out


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    except OSError as exc:
        raise WriteFailure(f"cannot write {path}: {exc.strerror or exc}") from exc


def snapshot(path: Path, snapshot_dir: Path) -> dict:
    try:
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(snapshot_dir, 0o700)
    except OSError as exc:
        raise WriteFailure(f"cannot prepare snapshot directory {snapshot_dir}: {exc}") from exc
    digest = fingerprint(path)
    target = snapshot_dir / f"{path.name}.{digest[:12]}.orig"
    try:
        shutil.copy2(path, target)
    except OSError as exc:
        raise WriteFailure(f"cannot snapshot {path} to {target}: {exc}") from exc
    if fingerprint(target) != digest:
        raise WriteFailure(f"snapshot {target} does not match source checksum {digest}")
    return {"path": str(target), "sha256": digest}


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Scaffold dbt model contracts from dbt artifacts.")
    parser.add_argument("--manifest", required=True, type=Path, help="path to target/manifest.json")
    parser.add_argument("--catalog", required=True, type=Path, help="path to target/catalog.json")
    parser.add_argument("--properties", required=True, type=Path, help="existing properties YAML file")
    parser.add_argument("--out", required=True, type=Path, help="where to write the proposed properties YAML")
    parser.add_argument("--report", type=Path, help="where to write the JSON report (default: <out>.report.json)")
    parser.add_argument("--adapter", default="postgres", help="target adapter name, e.g. snowflake")
    parser.add_argument("--model", action="append", default=[], help="limit to these model names (repeatable)")
    parser.add_argument("--exclude-package", action="append", default=[], help="skip models from this package (repeatable)")
    parser.add_argument("--apply", action="store_true", help="overwrite --properties after snapshotting it")
    parser.add_argument("--snapshot-dir", type=Path, help="directory that must hold the pre-write snapshot")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.apply and not args.snapshot_dir:
        sys.stderr.write("scaffold_contracts: --apply requires --snapshot-dir so the original stays recoverable\n")
        return 2

    try:
        manifest = load_json(args.manifest, "manifest.json")
        catalog = load_json(args.catalog, "catalog.json")
        doc = load_properties(args.properties)
        report_models, ready_entries, total_columns = build_proposal(
            manifest,
            catalog,
            doc,
            args.adapter.lower(),
            set(args.model) or None,
            set(args.exclude_package),
        )
        if not ready_entries:
            summary = {"ready": 0, "skipped": 0, "blocked": len(report_models), "columns": 0}
            payload = {
                "schema_version": SCHEMA_VERSION,
                "adapter": args.adapter,
                "inputs": {
                    "manifest": str(args.manifest),
                    "catalog": str(args.catalog),
                    "properties": str(args.properties),
                },
                "models": report_models,
                "summary": summary,
                "proposal": None,
            }
            report_path = args.report or args.out.with_suffix(args.out.suffix + ".report.json")
            write_text(report_path, json.dumps(payload, indent=2, sort_keys=False) + "\n")
            text = (
                f"scaffold_contracts: no model was contract-ready ({len(report_models)} inspected); "
                f"report written to {report_path}\n"
            )
            try:
                sys.stdout.write(text)
                sys.stdout.flush()
            except OSError as exc:
                raise WriteFailure(f"cannot write summary to stdout: {exc}") from exc
            return 2

        proposal_doc = apply_proposal(doc, ready_entries, report_models)
        yaml_text = yaml.safe_dump(proposal_doc, sort_keys=False, allow_unicode=True, default_flow_style=False)

        snapshot_info = None
        if args.apply:
            snapshot_info = snapshot(args.properties, args.snapshot_dir)
            write_text(args.properties, yaml_text)
            written = args.properties
        else:
            write_text(args.out, yaml_text)
            written = args.out

        skipped = sum(1 for m in report_models if str(m["status"]).startswith("SKIPPED"))
        blocked = sum(1 for m in report_models if str(m["status"]).startswith("BLOCKED"))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "adapter": args.adapter,
            "inputs": {
                "manifest": str(args.manifest),
                "catalog": str(args.catalog),
                "properties": str(args.properties),
            },
            "models": report_models,
            "summary": {
                "ready": len(ready_entries),
                "skipped": skipped,
                "blocked": blocked,
                "columns": total_columns,
            },
            "proposal": {"path": str(written), "applied": bool(args.apply), "snapshot": snapshot_info},
        }
        report_path = args.report or Path(str(args.out) + ".report.json")
        write_text(report_path, json.dumps(payload, indent=2, sort_keys=False) + "\n")
    except Refused as exc:
        sys.stderr.write(f"scaffold_contracts: refused: {exc}\n")
        return 2
    except WriteFailure as exc:
        sys.stderr.write(f"scaffold_contracts: write failure: {exc}\n")
        return 3

    text = (
        f"scaffold_contracts: {len(ready_entries)} model(s) contract-ready, "
        f"{skipped} skipped, {blocked} blocked, {total_columns} column(s) typed. "
        f"Proposal: {written}. Report: {report_path}\n"
    )
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except OSError as exc:
        sys.stderr.write(f"scaffold_contracts: write failure: cannot write summary to stdout: {exc}\n")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
