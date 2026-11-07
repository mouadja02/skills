#!/usr/bin/env python3
"""Offline tests for scaffold_contracts.py.

Run from anywhere:  python3 scripts/test_scaffold_contracts.py
Fixtures are generated in temporary directories, so the suite needs no network,
no dbt installation, and no warehouse connection.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "scaffold_contracts.py"

_spec = importlib.util.spec_from_file_location("scaffold_contracts", MODULE_PATH)
scaffold = importlib.util.module_from_spec(_spec)
sys.modules["scaffold_contracts"] = scaffold
_spec.loader.exec_module(scaffold)


def manifest_nodes(specs):
    nodes = {}
    for spec in specs:
        uid = f"model.{spec.get('package', 'jaffle')}.{spec['name']}"
        nodes[uid] = {
            "resource_type": "model",
            "name": spec["name"],
            "package_name": spec.get("package", "jaffle"),
            "config": {"materialized": spec.get("materialized", "table")},
        }
    return {"metadata": {"dbt_schema_version": "v11"}, "nodes": nodes}


def catalog_nodes(specs):
    nodes = {}
    for spec in specs:
        if "columns" not in spec:
            continue
        uid = f"model.{spec.get('package', 'jaffle')}.{spec['name']}"
        nodes[uid] = {
            "metadata": {"type": spec.get("materialized", "table")},
            "columns": {name: {"type": ctype, "name": name} for name, ctype in spec["columns"].items()},
        }
    return {"metadata": {"dbt_schema_version": "v1"}, "nodes": nodes, "sources": {}}


PROPERTIES = """\
version: 2
models:
  - name: dim_customers
    description: One row per customer.
    columns:
      - name: customer_id
        description: Primary key of the customer.
        tests:
          - unique
          - not_null
      - name: lifetime_value
        description: Lifetime value in EUR.
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
"""

BASE_MODELS = [
    {
        "name": "dim_customers",
        "materialized": "table",
        "columns": {
            "customer_id": "NUMBER(38,0)",
            "email": "VARCHAR(16777216)",
            "lifetime_value": "NUMBER(38,9)",
        },
    }
]


class CuratorTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        for path in self.tmp.rglob("*"):
            try:
                if path.is_dir():
                    os.chmod(path, 0o700)
            except OSError:
                pass
        self._tmp.cleanup()

    def write(self, name, content):
        path = self.tmp / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return path

    def run_cli(self, extra_args, properties_text=PROPERTIES, manifest_models=None, catalog_models=None, adapter="snowflake"):
        manifest = self.write("target/manifest.json", manifest_nodes(manifest_models if manifest_models is not None else BASE_MODELS))
        catalog = self.write("target/catalog.json", catalog_nodes(catalog_models if catalog_models is not None else BASE_MODELS))
        props = self.write("models/schema.yml", properties_text)
        out = self.tmp / "out/proposed-schema.yml"
        args = [
            "--manifest", str(manifest),
            "--catalog", str(catalog),
            "--properties", str(props),
            "--out", str(out),
            "--adapter", adapter,
        ] + list(extra_args)
        code = scaffold.main(args)
        return code, out, props

    def load_report(self, out: Path) -> dict:
        return json.loads(Path(str(out) + ".report.json").read_text(encoding="utf-8"))


class NormalPathTests(CuratorTestCase):
    def test_scaffold_adds_contract_and_types_while_preserving_semantics(self):
        code, out, _ = self.run_cli([])
        self.assertEqual(code, 0)
        doc = yaml.safe_load(out.read_text(encoding="utf-8"))
        entry = next(m for m in doc["models"] if m["name"] == "dim_customers")
        self.assertEqual(entry["config"]["contract"], {"enforced": True})
        self.assertEqual(entry["description"], "One row per customer.")
        columns = {c["name"]: c for c in entry["columns"]}
        self.assertEqual(columns["customer_id"]["data_type"], "number(38,0)")
        self.assertEqual(columns["customer_id"]["description"], "Primary key of the customer.")
        self.assertEqual(columns["customer_id"]["tests"], ["unique", "not_null"])
        self.assertEqual(columns["lifetime_value"]["data_type"], "number(38,9)")
        self.assertEqual(columns["lifetime_value"]["description"], "Lifetime value in EUR.")
        self.assertIn("data_type", columns["email"])
        report = self.load_report(out)
        self.assertEqual(report["summary"]["ready"], 1)
        self.assertEqual(report["summary"]["columns"], 3)

    def test_numeric_precision_and_scale_are_preserved(self):
        code, out, _ = self.run_cli([])
        self.assertEqual(code, 0)
        doc = yaml.safe_load(out.read_text(encoding="utf-8"))
        entry = next(m for m in doc["models"] if m["name"] == "dim_customers")
        types = {c["name"]: c["data_type"] for c in entry["columns"]}
        self.assertEqual(types["lifetime_value"], "number(38,9)")

    def test_snowflake_varchar_length_is_dropped_with_warning(self):
        code, out, _ = self.run_cli([])
        self.assertEqual(code, 0)
        doc = yaml.safe_load(out.read_text(encoding="utf-8"))
        entry = next(m for m in doc["models"] if m["name"] == "dim_customers")
        types = {c["name"]: c["data_type"] for c in entry["columns"]}
        self.assertEqual(types["email"], "varchar")
        report = self.load_report(out)
        warnings = " ".join(report["models"][0]["warnings"])
        self.assertIn("does not enforce length", warnings)

    def test_postgres_keeps_declared_varchar_length(self):
        code, out, _ = self.run_cli([], adapter="postgres")
        self.assertEqual(code, 0)
        doc = yaml.safe_load(out.read_text(encoding="utf-8"))
        entry = next(m for m in doc["models"] if m["name"] == "dim_customers")
        types = {c["name"]: c["data_type"] for c in entry["columns"]}
        self.assertEqual(types["email"], "varchar(16777216)")

    def test_model_filter_limits_scope(self):
        models = BASE_MODELS + [{"name": "other", "materialized": "view", "columns": {"id": "int8"}}]
        code, out, _ = self.run_cli(["--model", "other"], manifest_models=models, catalog_models=models)
        self.assertEqual(code, 0)
        doc = yaml.safe_load(out.read_text(encoding="utf-8"))
        entries = {m["name"]: m for m in doc["models"]}
        # Filtered-in model gains a contract; untouched models keep their original shape.
        self.assertEqual(entries["other"]["config"]["contract"], {"enforced": True})
        self.assertNotIn("config", entries["dim_customers"])
        self.assertEqual(entries["dim_customers"]["description"], "One row per customer.")


class BlockingTests(CuratorTestCase):
    def test_malformed_manifest_is_refused_without_writing_proposal(self):
        manifest = self.write("target/manifest.json", "{not json")
        catalog = self.write("target/catalog.json", catalog_nodes(BASE_MODELS))
        props = self.write("models/schema.yml", PROPERTIES)
        out = self.tmp / "out/proposed.yml"
        code = scaffold.main([
            "--manifest", str(manifest), "--catalog", str(catalog), "--properties", str(props),
            "--out", str(out), "--adapter", "snowflake",
        ])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_non_standard_json_constants_are_refused(self):
        manifest = self.write("target/manifest.json", '{"nodes": {"model.a.b": {"name": "b", "value": NaN}}}')
        catalog = self.write("target/catalog.json", catalog_nodes(BASE_MODELS))
        props = self.write("models/schema.yml", PROPERTIES)
        out = self.tmp / "out/proposed.yml"
        code = scaffold.main([
            "--manifest", str(manifest), "--catalog", str(catalog), "--properties", str(props),
            "--out", str(out), "--adapter", "snowflake",
        ])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_duplicate_yaml_keys_are_refused(self):
        duplicate_key_doc = "version: 2\nversion: 3\nmodels: []\n"
        code, out, _ = self.run_cli([], properties_text=duplicate_key_doc)
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_duplicate_model_entries_are_refused(self):
        duplicate_doc = "version: 2\nmodels:\n  - name: dim_customers\n  - name: dim_customers\n"
        code, out, _ = self.run_cli([], properties_text=duplicate_doc)
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_duplicate_model_names_across_packages_are_blocked(self):
        models = [
            {"name": "dim_customers", "package": "a", "materialized": "table", "columns": {"id": "int8"}},
            {"name": "dim_customers", "package": "b", "materialized": "table", "columns": {"id": "int8"}},
        ]
        code, out, _ = self.run_cli([], manifest_models=models, catalog_models=models, properties_text="version: 2\nmodels: []\n")
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())
        report = self.load_report(out)
        statuses = {m["package"]: m["status"] for m in report["models"]}
        self.assertEqual(statuses, {"a": "BLOCKED_DUPLICATE_NAME", "b": "BLOCKED_DUPLICATE_NAME"})

    def test_missing_catalog_entry_is_skipped_not_contracted(self):
        code, out, _ = self.run_cli([], catalog_models=[])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())
        report = self.load_report(out)
        self.assertEqual(report["models"][0]["status"], "SKIPPED_NOT_IN_CATALOG")

    def test_catalog_column_without_type_is_blocked_not_invented(self):
        models = [{"name": "dim_customers", "materialized": "table", "columns": {"customer_id": "NUMBER(38,0)", "mystery": ""}}]
        code, out, _ = self.run_cli([], manifest_models=models, catalog_models=models)
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())
        report = self.load_report(out)
        self.assertEqual(report["models"][0]["status"], "BLOCKED_COLUMN_TYPE")
        self.assertEqual(report["models"][0]["blocked_columns"][0]["name"], "mystery")

    def test_complex_type_is_blocked(self):
        models = [{"name": "dim_customers", "materialized": "table", "columns": {"payload": "VARIANT"}}]
        code, out, _ = self.run_cli([], manifest_models=models, catalog_models=models)
        self.assertEqual(code, 2)
        report = self.load_report(out)
        self.assertEqual(report["models"][0]["status"], "BLOCKED_COLUMN_TYPE")

    def test_incremental_model_is_skipped_with_on_schema_change_hazard(self):
        models = [{"name": "fct_orders", "materialized": "incremental", "columns": {"order_id": "NUMBER(38,0)"}}]
        code, out, _ = self.run_cli([], manifest_models=models, catalog_models=models)
        self.assertEqual(code, 2)
        report = self.load_report(out)
        record = report["models"][0]
        self.assertEqual(record["status"], "SKIPPED_MATERIALIZATION")
        self.assertIn("on_schema_change", " ".join(record["reasons"]))

    def test_ephemeral_model_is_not_contracted(self):
        models = [{"name": "stg_x", "materialized": "ephemeral", "columns": {"id": "int8"}}]
        code, out, _ = self.run_cli([], manifest_models=models, catalog_models=models)
        self.assertEqual(code, 2)
        report = self.load_report(out)
        self.assertEqual(report["models"][0]["status"], "SKIPPED_MATERIALIZATION")

    def test_unknown_model_filter_is_refused(self):
        code, out, _ = self.run_cli(["--model", "does_not_exist"])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())


class WriteSafetyTests(CuratorTestCase):
    def test_apply_without_snapshot_dir_is_refused(self):
        code, _out, props = self.run_cli(["--apply"])
        self.assertEqual(code, 2)
        self.assertNotIn("contract", props.read_text(encoding="utf-8"))

    def test_apply_snapshots_original_before_overwrite(self):
        props_before = PROPERTIES
        code, _out, props = self.run_cli(["--apply", "--snapshot-dir", str(self.tmp / "snap")])
        self.assertEqual(code, 0)
        snapshot_dir = self.tmp / "snap"
        snapshots = list(snapshot_dir.iterdir())
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].read_text(encoding="utf-8"), props_before)
        self.assertIn("enforced: true", props.read_text(encoding="utf-8"))
        self.assertEqual(stat.S_IMODE(snapshot_dir.stat().st_mode), 0o700)

    def test_unwritable_output_returns_write_failure(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("root ignores directory permissions")
        locked = self.tmp / "locked"
        locked.mkdir()
        os.chmod(locked, 0o500)
        manifest = self.write("target/manifest.json", manifest_nodes(BASE_MODELS))
        catalog = self.write("target/catalog.json", catalog_nodes(BASE_MODELS))
        props = self.write("models/schema.yml", PROPERTIES)
        code = scaffold.main([
            "--manifest", str(manifest), "--catalog", str(catalog), "--properties", str(props),
            "--out", str(locked / "proposed.yml"), "--adapter", "snowflake",
        ])
        os.chmod(locked, 0o700)
        self.assertEqual(code, 3)
        self.assertEqual(props.read_text(encoding="utf-8"), PROPERTIES)


class TypeNormalizationTests(unittest.TestCase):
    def test_quoted_and_spaced_types_are_cleaned(self):
        data_type, warnings, reason = scaffold.normalize_type('"NUMBER(38, 9)"', "snowflake")
        self.assertEqual(data_type, "number(38,9)")
        self.assertIsNone(reason)
        self.assertEqual(warnings, [])

    def test_nested_shape_is_blocked(self):
        _data_type, _warnings, reason = scaffold.normalize_type("STRUCT<a INT64, b STRING>", "bigquery")
        self.assertIn("nested", reason)

    def test_numeric_without_precision_warns(self):
        data_type, warnings, reason = scaffold.normalize_type("NUMERIC", "bigquery")
        self.assertEqual(data_type, "numeric")
        self.assertIsNone(reason)
        self.assertTrue(warnings)

    def test_empty_type_is_blocked(self):
        _data_type, _warnings, reason = scaffold.normalize_type("   ", "snowflake")
        self.assertIn("empty", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
