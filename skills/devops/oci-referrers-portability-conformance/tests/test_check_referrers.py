#!/usr/bin/env python3
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_referrers.py"
spec = importlib.util.spec_from_file_location("check_referrers", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
D1 = "sha256:" + "a" * 64
D2 = "sha256:" + "b" * 64
D3 = "sha256:" + "c" * 64


def descriptor(digest=D2):
    return {"mediaType": "application/vnd.oci.image.manifest.v1+json", "digest": digest, "size": 12, "artifactType": "application/vnd.test.signature", "annotations": {"test": "true"}}


def endpoint(items=None):
    return {"api_status": 200, "content_type": module.INDEX_MEDIA_TYPE, "referrers": [descriptor()] if items is None else items, "platform_coverage": []}


def fixture():
    return {"schema_version": 1, "kind": "oci_referrers_audit", "profile": module.PROFILE, "subject": D1, "platform_subjects": [], "source": endpoint(), "destination": endpoint()}


class AnalyzeTests(unittest.TestCase):
    def test_matching_graph_passes(self):
        report = module.analyze(fixture())
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["fallback_tag"], "sha256-" + "a" * 64)
        self.assertFalse(report["mutation_permitted"])

    def test_unrelated_document_is_not_applicable(self):
        report = module.analyze({"kind": "generic_sbom_inventory", "data": []})
        self.assertEqual(report["status"], "not_applicable")

    def test_fallback_mode_is_classified(self):
        value = fixture()
        for side in ("source", "destination"):
            value[side]["api_status"] = 404
            value[side]["fallback_status"] = 200
        report = module.analyze(value)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["modes"]["source"], "fallback_tag")

    def test_missing_fallback_fails(self):
        value = fixture()
        value["destination"].update(api_status=404, fallback_status=404)
        self.assertIn("FALLBACK_UNAVAILABLE", {x["code"] for x in module.analyze(value)["findings"]})

    def test_duplicate_and_metadata_drift_fail(self):
        value = fixture()
        changed = descriptor()
        changed["artifactType"] = "application/vnd.changed"
        changed["annotations"] = {}
        value["destination"]["referrers"] = [changed, changed.copy()]
        codes = {x["code"] for x in module.analyze(value)["findings"]}
        self.assertTrue({"DUPLICATE_DESCRIPTOR", "ARTIFACT_TYPE_DRIFT", "ANNOTATION_DRIFT"} <= codes)

    def test_missing_and_extra_are_distinguished(self):
        value = fixture()
        value["destination"]["referrers"] = [descriptor(D3)]
        report = module.analyze(value)
        by_code = {x["code"]: x["severity"] for x in report["findings"]}
        self.assertEqual(by_code["DESTINATION_MISSING_REFERRER"], "error")
        self.assertEqual(by_code["DESTINATION_EXTRA_REFERRER"], "warning")

    def test_platform_coverage_is_differential(self):
        value = fixture()
        value["platform_subjects"] = [D3]
        value["source"]["platform_coverage"] = [D3]
        codes = {x["code"] for x in module.analyze(value)["findings"]}
        self.assertIn("DESTINATION_PLATFORM_COVERAGE_MISSING", codes)

    def test_invalid_shapes_fail_closed(self):
        cases = []
        wrong = fixture(); wrong["destination"]["referrers"] = {}; cases.append(wrong)
        wrong = fixture(); wrong["destination"]["referrers"][0]["size"] = True; cases.append(wrong)
        wrong = fixture(); wrong["platform_subjects"] = "bad"; cases.append(wrong)
        wrong = fixture(); wrong["profile"] = "moving-main"; cases.append(wrong)
        wrong = fixture(); wrong["destination"]["referrers"][0]["annotations"] = []; cases.append(wrong)
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(module.InputError):
                    module.analyze(case)

    def test_nonfinite_fails_closed(self):
        value = fixture(); value["noise"] = math.inf
        with self.assertRaises(module.InputError):
            module.analyze(value)


class CliTests(unittest.TestCase):
    def run_cli(self, payload, output=None):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
            command = [sys.executable, str(SCRIPT), "--input", str(source)]
            if output is not None:
                command += ["--output", str(output)]
            return subprocess.run(command, text=True, capture_output=True, check=False)

    def test_malformed_json_returns_two(self):
        result = self.run_cli("{")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "input_error")

    def test_nan_returns_two(self):
        result = self.run_cli('{"kind":"oci_referrers_audit","x":NaN}')
        self.assertEqual(result.returncode, 2)

    def test_behavioral_failure_returns_one(self):
        value = fixture(); value["destination"]["referrers"] = []
        result = self.run_cli(value)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "fail")

    def test_controlled_output_failure_returns_two(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(fixture(), Path(directory))
            self.assertEqual(result.returncode, 2)
            self.assertIn("cannot write report", result.stderr)


if __name__ == "__main__":
    unittest.main()
