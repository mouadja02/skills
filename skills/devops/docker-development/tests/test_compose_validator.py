#!/usr/bin/env python3
"""Offline regressions for the Compose validator CLI."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "compose_validator.py"


class ComposeValidatorTests(unittest.TestCase):
    def run_validator(self, content):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = Path(tmpdir) / "compose.txt"
            fixture.write_text(content, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(fixture), "--output", "json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_normal_block_yaml_remains_clean(self):
        result = self.run_validator(
            "services:\n"
            "  api:\n"
            "    image: example/api:1.0\n"
            "    healthcheck:\n"
            "      test: [\"CMD\", \"true\"]\n"
            "    restart: unless-stopped\n"
            "    mem_limit: 256m\n"
            "networks:\n"
            "  app:\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["service_count"], 1)
        self.assertEqual(report["finding_counts"]["critical"], 0)

    def test_json_compose_detects_inline_secret(self):
        result = self.run_validator(
            json.dumps(
                {
                    "services": {
                        "api": {
                            "image": "example/api:1.0",
                            "environment": {"API_TOKEN": "not-a-real-secret"},
                        }
                    }
                }
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["service_count"], 1)
        self.assertEqual(report["finding_counts"]["critical"], 1)

    def test_malformed_json_fails_closed(self):
        result = self.run_validator('{"services":\n')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("malformed JSON", result.stderr)

    def test_nonstandard_json_constant_fails_closed(self):
        result = self.run_validator('{"services":{"api":{"mem_limit":NaN}}}')
        self.assertEqual(result.returncode, 2)
        self.assertIn("non-standard JSON constant", result.stderr)

    def test_non_mapping_service_fails_closed(self):
        result = self.run_validator('{"services":{"api":"image"}}')
        self.assertEqual(result.returncode, 2)
        self.assertIn("service 'api' must be a mapping", result.stderr)


if __name__ == "__main__":
    unittest.main()
