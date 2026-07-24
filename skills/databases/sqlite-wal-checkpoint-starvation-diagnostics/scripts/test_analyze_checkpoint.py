#!/usr/bin/env python3
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("analyze_checkpoint.py")
spec = importlib.util.spec_from_file_location("analyze_checkpoint", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AnalyzeCheckpointTests(unittest.TestCase):
    def base(self):
        return {"mode":"PASSIVE","busy":0,"log_frames":100,"checkpointed_frames":25,"wal_bytes":1000,"free_bytes":1500}

    def test_partial_passive_and_disk_gate(self):
        out = module.analyze(self.base())
        self.assertEqual(out["classification"], "partial_passive_progress")
        self.assertEqual(out["remaining_frames"], 75)
        self.assertEqual(out["disk_headroom"], "critical_by_recommended_ratio")

    def test_complete(self):
        item = self.base(); item["checkpointed_frames"] = 100
        self.assertEqual(module.analyze(item)["classification"], "all_reported_frames_checkpointed")

    def test_blocking_busy(self):
        item = self.base(); item.update(mode="TRUNCATE", busy=1)
        self.assertEqual(module.analyze(item)["classification"], "blocking_checkpoint_incomplete")

    def test_fail_closed_shapes_and_values(self):
        bad = [None, [], {"mode":"PASSIVE"}]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(ValueError): module.analyze(item)
        for field, value in [("busy", True), ("log_frames", -1), ("wal_bytes", 1.5)]:
            item = self.base(); item[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): module.analyze(item)
        item = self.base(); item["extra"] = 1
        with self.assertRaises(ValueError): module.analyze(item)
        item = self.base(); item["checkpointed_frames"] = 101
        with self.assertRaises(ValueError): module.analyze(item)
        item = self.base(); item["busy"] = 1
        with self.assertRaises(ValueError): module.analyze(item)

    def test_cli_rejects_malformed_unreadable_and_nan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name, text in [("malformed.json", "{"), ("nan.json", '{"mode":"PASSIVE","busy":0,"log_frames":NaN,"checkpointed_frames":0,"wal_bytes":0,"free_bytes":0}')]:
                path = root / name; path.write_text(text)
                run = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)], capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(run.stdout, "")
            missing = subprocess.run([sys.executable, str(SCRIPT), "--input", str(root / "missing.json")], capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)

    def test_real_reader_boundary_then_release(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "fixture.db"
            writer = sqlite3.connect(db)
            self.assertEqual(writer.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
            writer.execute("CREATE TABLE items(value TEXT)")
            writer.execute("INSERT INTO items VALUES ('before')")
            writer.commit()

            reader = sqlite3.connect(db)
            reader.execute("BEGIN")
            self.assertEqual(reader.execute("SELECT count(*) FROM items").fetchone()[0], 1)
            writer.executemany("INSERT INTO items VALUES (?)", [(str(i),) for i in range(200)])
            writer.commit()

            busy, log, done = writer.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            self.assertEqual(busy, 0)
            self.assertLess(done, log)

            reader.rollback()
            reader.close()
            busy, log, done = writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            self.assertEqual((busy, log, done), (0, 0, 0))
            writer.close()


if __name__ == "__main__":
    unittest.main()
