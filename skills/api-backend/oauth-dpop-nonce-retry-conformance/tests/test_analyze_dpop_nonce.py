import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_dpop_nonce.py"
FIXTURES = ROOT / "tests" / "fixtures"
spec = importlib.util.spec_from_file_location("analyze_dpop_nonce", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DpopNonceTests(unittest.TestCase):
    def load(self, name):
        return module.load_input(FIXTURES / name)

    def test_normal_challenge_and_retry_is_ready(self):
        report = module.analyze(self.load("normal.json"))
        self.assertEqual("ready", report["classification"])
        self.assertEqual(1, report["max_automatic_retries"])
        self.assertIn("bounded_retry_verified", {f["code"] for f in report["findings"]})

    def test_stale_response_does_not_clobber_newer_nonce(self):
        report = module.analyze(self.load("stale-safe.json"))
        key = "resource_server|https://api.example|/orders"
        self.assertEqual("rs-n2", report["active_nonces"][key])
        self.assertIn("stale_nonce_ignored", {f["code"] for f in report["findings"]})
        self.assertEqual("as-n7", report["active_nonces"]["authorization_server|https://as.example|/token"])

    def test_duplicate_nonce_is_parsed_then_blocked(self):
        document = self.load("duplicate-blocked.json")
        report = module.analyze(document)
        self.assertEqual("blocked", report["classification"])
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("ambiguous_nonce_header", codes)
        self.assertIn("challenge_nonce_unusable", codes)

    def test_edge_fixture_preserves_safe_state_while_blocking_ambiguity(self):
        report = module.analyze(self.load("edge.json"))
        self.assertEqual("blocked", report["classification"])
        self.assertEqual("rs-n2", report["active_nonces"]["resource_server|https://api.example|/orders"])
        self.assertEqual("as-n7", report["active_nonces"]["authorization_server|https://as.example|/token"])
        self.assertNotIn("resource_server|https://other.example|/data", report["active_nonces"])
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("stale_nonce_ignored", codes)
        self.assertIn("ambiguous_nonce_header", codes)

    def test_non_dpop_flow_is_not_applicable(self):
        report = module.analyze(self.load("not-applicable.json"))
        self.assertEqual("not_applicable", report["classification"])

    def test_malformed_fixture_is_input_error_not_protocol_failure(self):
        with self.assertRaisesRegex(module.InputError, "malformed JSON"):
            self.load("malformed.txt")

    def test_nonstandard_nan_fails_closed(self):
        self.assertLoadFails('{"profile":"oauth-dpop-nonce-v1","events":NaN}', "non-standard JSON")

    def test_duplicate_json_member_fails_closed(self):
        self.assertLoadFails('{"profile":"oauth-dpop-nonce-v1","profile":"x","events":[]}', "duplicate JSON member")

    def test_forbidden_secret_key_fails_closed(self):
        doc = {"profile": module.PROFILE, "events": [{"access_token": "sentinel"}]}
        with self.assertRaisesRegex(module.InputError, "forbidden credential-bearing key"):
            module.analyze(doc)

    def test_unknown_member_and_wrong_event_shape_fail_closed(self):
        with self.assertRaisesRegex(module.InputError, "unsupported members"):
            module.analyze({"profile": module.PROFILE, "events": [], "mode": "loose"})
        with self.assertRaisesRegex(module.InputError, "expected object"):
            module.analyze({"profile": module.PROFILE, "events": ["event"]})

    def test_second_retry_mode_is_rejected_before_iteration(self):
        doc = self.load("normal.json")
        doc["events"][1]["retry_index"] = 2
        with self.assertRaisesRegex(module.InputError, "only 0 or 1"):
            module.analyze(doc)

    def test_browser_nonce_requires_cors_exposure(self):
        doc = self.load("stale-safe.json")
        doc["events"][0]["browser_context"] = True
        report = module.analyze(doc)
        self.assertEqual("blocked", report["classification"])
        self.assertIn("nonce_not_cors_exposed", {f["code"] for f in report["findings"]})
        doc["events"][0]["cors_exposed_headers"] = ["DPoP-Nonce"]
        report = module.analyze(doc)
        self.assertEqual("ready", report["classification"])

    def test_repeated_challenge_stops(self):
        doc = self.load("normal.json")
        retry = doc["events"][1]
        retry.update({"status": 400, "oauth_error": "use_dpop_nonce", "dpop_nonce_headers": ["as-n2"]})
        report = module.analyze(doc)
        self.assertEqual("blocked", report["classification"])
        self.assertIn("repeated_nonce_challenge", {f["code"] for f in report["findings"]})

    def test_cli_exit_codes(self):
        for name, expected in (("normal.json", 0), ("duplicate-blocked.json", 1), ("malformed.txt", 2)):
            result = subprocess.run([sys.executable, str(SCRIPT), str(FIXTURES / name)], capture_output=True, text=True)
            self.assertEqual(expected, result.returncode, result.stderr)

    def test_controlled_output_failure_fails_closed(self):
        class Broken(io.StringIO):
            def write(self, value):
                raise OSError("controlled failure")
        with self.assertRaisesRegex(module.InputError, "cannot serialize report"):
            module.emit_report({"classification": "ready"}, Broken())

    def assertLoadFails(self, payload, message):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.txt"
            path.write_text(payload, encoding="utf-8")
            with self.assertRaisesRegex(module.InputError, message):
                module.load_input(path)


if __name__ == "__main__":
    unittest.main()
