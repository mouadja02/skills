"""Regression tests for autoresearch rollback; uses temporary local Git repos only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "skills/agent-eval/autoresearch-agent/scripts/run_experiment.py"
sys.path.insert(0, str(RUNNER.parent))
spec = importlib.util.spec_from_file_location("autoresearch_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RollbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.test")
        (self.repo / "target.txt").write_text("base", encoding="utf-8")
        (self.repo / "other.txt").write_text("base", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.parent = self.git("rev-parse", "HEAD")
        self.git("checkout", "-qb", "autoresearch/custom/demo")
        (self.repo / "target.txt").write_text("experiment", encoding="utf-8")
        self.git("add", "target.txt")
        self.git("commit", "-qm", "experiment")
        self.commit = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.STDOUT, text=True).strip()

    def rollback(self, target="target.txt"):
        return runner.rollback_experiment(self.repo, "custom/demo", target, self.commit, self.parent)

    def test_revert_preserves_history(self):
        self.assertTrue(self.rollback()[0])
        self.assertEqual((self.repo / "target.txt").read_text(), "base")
        self.assertEqual(self.git("rev-parse", "HEAD^"), self.commit)
        self.assertEqual(self.git("rev-parse", "HEAD^^"), self.parent)

    def test_dirty_and_mismatched_target_leave_state_unchanged(self):
        self.assertFalse(self.rollback("other.txt")[0])
        (self.repo / "other.txt").write_text("unsaved", encoding="utf-8")
        self.assertFalse(self.rollback()[0])
        self.assertEqual(self.git("rev-parse", "HEAD"), self.commit)
        self.assertEqual((self.repo / "target.txt").read_text(), "experiment")
        self.assertEqual((self.repo / "other.txt").read_text(), "unsaved")

    def test_failed_rollback_stops_cli(self):
        experiment = self.repo / ".autoresearch/custom/demo"
        experiment.mkdir(parents=True)
        cmd = json.dumps([sys.executable, "-c", "raise SystemExit(2)"])
        (experiment / "config.cfg").write_text(f"target: target.txt\nevaluate_cmd: {cmd}\nmetric: score\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(RUNNER), "--experiment", "custom/demo", "--single"], cwd=self.repo, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ROLLBACK PENDING", result.stdout)
        self.assertIn("\trollback_pending\texit_2", (experiment / "results.tsv").read_text())
        self.assertEqual(self.git("rev-parse", "HEAD"), self.commit)


if __name__ == "__main__":
    unittest.main()
