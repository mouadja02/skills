"""Tests for the offline JOSE "crit" header validator.

Standard library only (unittest). Run from the skill directory with:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(SKILL_DIR, "scripts", "validate_jose_crit.py")


def run_cli(payload):
    """Run the validator CLI with a JSON payload written to a temp file."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(payload, fh)
        path = fh.name
    try:
        proc = subprocess.run(
            [sys.executable, SCRIPT, path],
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr
    finally:
        os.unlink(path)


class TestStructuralRules(unittest.TestCase):
    def test_ready_for_supported_extension(self):
        code, out, _ = run_cli({
            "header": {"alg": "ES256", "kid": "k1", "crit": ["exp-verified"], "exp-verified": True},
            "supported_extensions": ["exp-verified"],
        })
        self.assertEqual(code, 0)
        doc = json.loads(out)
        self.assertEqual(doc["classification"], "ready")
        self.assertEqual(doc["violations"], [])

    def test_standard_name_rejected(self):
        code, out, _ = run_cli({"header": {"alg": "RS256", "crit": ["alg"]}})
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertEqual(doc["classification"], "blocked")
        self.assertIn("crit_standard_name", [v["id"] for v in doc["violations"]])

    def test_duplicate_rejected(self):
        code, out, _ = run_cli({"header": {"alg": "RS256", "crit": ["foo", "foo"], "foo": True}})
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertIn("crit_duplicate", [v["id"] for v in doc["violations"]])

    def test_dangling_rejected(self):
        code, out, _ = run_cli({"header": {"alg": "RS256", "crit": ["foo"]}})
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertIn("crit_dangling", [v["id"] for v in doc["violations"]])

    def test_non_array_rejected_after_parse(self):
        # Expected-invalid: parses successfully, then rejected for the right reason.
        code, out, _ = run_cli({"header": {"alg": "RS256", "crit": "not-an-array"}})
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertIn("crit_not_array", [v["id"] for v in doc["violations"]])

    def test_non_string_entry_rejected(self):
        code, out, _ = run_cli({"header": {"alg": "RS256", "crit": [1], "1": True}})
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertIn("crit_non_string_entry", [v["id"] for v in doc["violations"]])


class TestFailClosedExtensions(unittest.TestCase):
    def test_unknown_extension_blocked(self):
        code, out, _ = run_cli({
            "header": {"alg": "HS256", "crit": ["x-custom-policy"], "x-custom-policy": "require-mfa"},
        })
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertEqual(doc["classification"], "blocked")
        self.assertIn("crit_unsupported", [v["id"] for v in doc["violations"]])

    def test_understood_extension_ready(self):
        code, out, _ = run_cli({
            "header": {"alg": "HS256", "crit": ["x-custom-policy"], "x-custom-policy": "require-mfa"},
            "supported_extensions": ["x-custom-policy"],
        })
        self.assertEqual(code, 0)
        doc = json.loads(out)
        self.assertEqual(doc["classification"], "ready")


class TestB64Interaction(unittest.TestCase):
    def test_b64_false_requires_b64_in_crit(self):
        code, out, _ = run_cli({"header": {"alg": "RS256", "b64": False, "crit": []}})
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertIn("b64_false_missing_crit", [v["id"] for v in doc["violations"]])

    def test_b64_false_with_crit_and_support_is_ready(self):
        code, out, _ = run_cli({
            "header": {"alg": "RS256", "b64": False, "crit": ["b64"]},
            "supported_extensions": ["b64"],
        })
        self.assertEqual(code, 0)
        doc = json.loads(out)
        self.assertEqual(doc["classification"], "ready")

    def test_b64_false_without_support_is_blocked(self):
        # "b64" is an extension; an implementation not supporting it must reject.
        code, out, _ = run_cli({
            "header": {"alg": "RS256", "b64": False, "crit": ["b64"]},
        })
        self.assertEqual(code, 1)
        doc = json.loads(out)
        self.assertIn("crit_unsupported", [v["id"] for v in doc["violations"]])


class TestNotApplicable(unittest.TestCase):
    def test_no_crit(self):
        code, out, _ = run_cli({"header": {"alg": "HS256", "typ": "JWT", "kid": "abc"}})
        self.assertEqual(code, 0)
        doc = json.loads(out)
        self.assertEqual(doc["classification"], "not_applicable")


class TestInputErrors(unittest.TestCase):
    def test_missing_header_and_token_is_input_error(self):
        code, _, err = run_cli({"alg": "HS256"})
        self.assertEqual(code, 2)

    def test_malformed_json_is_input_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            fh.write("{not json")
            path = fh.name
        try:
            proc = subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)
        finally:
            os.unlink(path)
        self.assertEqual(proc.returncode, 2)

    def test_compact_token_roundtrip(self):
        import base64
        header = {"alg": "HS256", "crit": ["foo"], "foo": True}
        seg = base64.urlsafe_b64encode(
            json.dumps(header, separators=(",", ":")).encode()
        ).rstrip(b"=").decode()
        code, out, _ = run_cli({"token": seg + ".cGF5bG9hZA.sig"})
        self.assertEqual(code, 1)  # unknown extension "foo"
        doc = json.loads(out)
        self.assertIn("crit_unsupported", [v["id"] for v in doc["violations"]])


if __name__ == "__main__":
    unittest.main()
