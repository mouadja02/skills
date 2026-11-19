#!/usr/bin/env python3
"""Offline tests for the packaged senior-data-scientist JSON workflows."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class WorkflowTests(unittest.TestCase):
    def run_workflow(self, script: str, payload: object, output_exists: bool = False) -> tuple[subprocess.CompletedProcess[str], Path, tempfile.TemporaryDirectory[str]]:
        temporary = tempfile.TemporaryDirectory()
        directory = Path(temporary.name)
        source = directory / "input.json"
        output = directory / "output.json"
        source.write_text(json.dumps(payload), encoding="utf-8")
        if output_exists:
            output.write_text('{"preserved": true}\n', encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--input", str(source), "--output", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        return result, output, temporary

    def test_experiment_design(self) -> None:
        result, output, temporary = self.run_workflow(
            "experiment_designer.py",
            {"baseline_rate": 0.1, "relative_mde": 0.1, "alpha": 0.05, "power": 0.8},
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(report["status"], "designed")
        self.assertGreater(report["sample_size_per_variant"], 0)
        self.assertEqual(report["total_sample_size"], 2 * report["sample_size_per_variant"])

    def test_feature_parameters_are_fit_on_training_only(self) -> None:
        payload = {
            "records": [
                {"age": 20, "country": "FR", "at": "2026-01-05T00:00:00Z"},
                {"age": 30, "country": "US", "at": "2026-01-06T00:00:00Z"},
                {"age": 1000, "country": "DE", "at": "2026-01-07T00:00:00Z"},
            ],
            "split_index": 2,
            "numeric": ["age"],
            "categorical": ["country"],
            "datetime": ["at"],
        }
        result, output, temporary = self.run_workflow("feature_engineering_pipeline.py", payload)
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(report["parameters"]["numeric"]["age"]["mean"], 25)
        self.assertNotIn("DE", report["parameters"]["categorical"]["country"]["vocabulary"])
        self.assertEqual(report["holdout"][0]["country__unknown"], 1)

    def test_model_metrics(self) -> None:
        result, output, temporary = self.run_workflow(
            "model_evaluation_suite.py",
            {"y_true": [0, 0, 1, 1], "y_score": [0.1, 0.4, 0.35, 0.8], "threshold": 0.5},
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(report["confusion_matrix"], {"tn": 2, "fp": 0, "fn": 1, "tp": 1})
        self.assertAlmostEqual(report["metrics"]["roc_auc"], 0.75)
        self.assertAlmostEqual(report["metrics"]["average_precision"], 5 / 6)

    def test_model_metrics_ties_are_order_independent(self) -> None:
        first, first_output, first_temporary = self.run_workflow(
            "model_evaluation_suite.py",
            {"y_true": [1, 0, 1, 0], "y_score": [0.8, 0.8, 0.2, 0.2]},
        )
        second, second_output, second_temporary = self.run_workflow(
            "model_evaluation_suite.py",
            {"y_true": [0, 1, 0, 1], "y_score": [0.8, 0.8, 0.2, 0.2]},
        )
        self.addCleanup(first_temporary.cleanup)
        self.addCleanup(second_temporary.cleanup)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        first_metrics = json.loads(first_output.read_text())["metrics"]
        second_metrics = json.loads(second_output.read_text())["metrics"]
        self.assertEqual(first_metrics["average_precision"], second_metrics["average_precision"])
        self.assertEqual(first_metrics["roc_auc"], second_metrics["roc_auc"])

    def test_invalid_input_fails_without_output(self) -> None:
        result, output, temporary = self.run_workflow(
            "experiment_designer.py",
            {"baseline_rate": 1.0, "relative_mde": 0.1, "alpha": 0.05, "power": 0.8},
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_existing_output_is_preserved(self) -> None:
        result, output, temporary = self.run_workflow(
            "model_evaluation_suite.py",
            {"y_true": [0, 1], "y_score": [0.1, 0.9]},
            output_exists=True,
        )
        self.addCleanup(temporary.cleanup)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(output.read_text()), {"preserved": True})


if __name__ == "__main__":
    unittest.main()
