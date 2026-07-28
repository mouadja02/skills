import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_oauth_flow.py"
SPEC = importlib.util.spec_from_file_location("analyze_oauth_flow", SCRIPT)
assert SPEC and SPEC.loader
analyzer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analyzer
SPEC.loader.exec_module(analyzer)


def valid_flow():
    resource = "https://mcp.example.test/mcp"
    issuer = "https://login.example.test"
    redirect = "http://127.0.0.1:8765/callback"
    return {
        "schema_version": 1,
        "profile": "mcp-2025-11-25",
        "context": "initial",
        "target_resource": resource,
        "challenge": {
            "status": 401,
            "error": "invalid_token",
            "resource_metadata": "https://mcp.example.test/.well-known/oauth-protected-resource/mcp",
            "scope": "tools.read",
        },
        "resource_metadata": {
            "url": "https://mcp.example.test/.well-known/oauth-protected-resource/mcp",
            "resource": resource,
            "authorization_servers": [issuer],
            "scopes_supported": ["tools.read"],
        },
        "authorization_server_metadata": {
            "issuer": issuer,
            "authorization_endpoint": issuer + "/authorize",
            "token_endpoint": issuer + "/token",
            "code_challenge_methods_supported": ["S256"],
        },
        "authorization_request": {
            "endpoint": issuer + "/authorize",
            "resource": resource,
            "scope": ["tools.read"],
            "redirect_uri": redirect,
            "pkce_method": "S256",
        },
        "token_request": {
            "endpoint": issuer + "/token",
            "resource": resource,
            "scope": ["tools.read"],
            "redirect_uri": redirect,
            "pkce_verifier_present": True,
        },
        "token_response": {"status": 200, "granted_scope": ["tools.read"]},
        "retry": {"status": 200},
    }


class AnalyzeOAuthFlowTests(unittest.TestCase):
    def test_ready_flow(self):
        result = analyzer.analyze(valid_flow())
        self.assertEqual(result["classification"], "ready")
        self.assertTrue(result["valid"])
        self.assertEqual(result["findings"], [])

    def test_partial_oauth_evidence_is_never_ready(self):
        flow = {
            "schema_version": 1,
            "profile": "mcp-2025-11-25",
            "context": "initial",
            "target_resource": "https://mcp.example.test/mcp",
            "challenge": {
                "status": 401,
                "resource_metadata": "https://mcp.example.test/.well-known/oauth-protected-resource/mcp",
            },
        }
        result = analyzer.analyze(flow)
        self.assertEqual(result["classification"], "blocked")
        incomplete = [x for x in result["findings"] if x["code"] == "evidence_incomplete"]
        self.assertEqual(incomplete[0]["phase"], "resource_metadata")

    def test_resource_is_compared_without_trailing_slash_normalization(self):
        flow = valid_flow()
        flow["authorization_request"]["resource"] += "/"
        flow["token_request"]["resource"] += "/"
        result = analyzer.analyze(flow)
        self.assertIn("resource_indicator_mismatch", {x["code"] for x in result["findings"]})
        self.assertEqual(result["classification"], "blocked")

    def test_mid_session_redirect_without_exchange_is_blocked(self):
        flow = valid_flow()
        flow["context"] = "mid_session"
        del flow["token_request"]
        del flow["token_response"]
        del flow["retry"]
        result = analyzer.analyze(flow)
        self.assertIn("mid_session_reauth_incomplete", {x["code"] for x in result["findings"]})

    def test_insufficient_scope_challenge_requires_scope(self):
        flow = valid_flow()
        flow["challenge"]["status"] = 403
        flow["challenge"]["error"] = "insufficient_scope"
        del flow["challenge"]["scope"]
        result = analyzer.analyze(flow)
        self.assertIn("scope_missing_on_insufficient_scope", {x["code"] for x in result["findings"]})

    def test_token_scope_omission_is_provider_compatibility_warning(self):
        flow = valid_flow()
        flow["token_request"]["scope"] = []
        result = analyzer.analyze(flow)
        warning = [x for x in result["findings"] if x["code"] == "token_scope_omitted"]
        self.assertEqual(warning[0]["level"], "warning")
        self.assertTrue(result["valid"])

    def test_discovery_endpoint_redirect_and_granted_scope_mismatches(self):
        cases = []
        a = valid_flow(); a["resource_metadata"]["authorization_servers"] = ["https://other.example.test"]; cases.append((a, "issuer_not_authorized"))
        b = valid_flow(); b["token_request"]["endpoint"] = "https://login.example.test/other"; cases.append((b, "token_endpoint_mismatch"))
        c = valid_flow(); c["token_request"]["redirect_uri"] = "http://localhost:9999/callback"; cases.append((c, "redirect_uri_mismatch"))
        d = valid_flow(); d["token_response"]["granted_scope"] = ["profile"]; cases.append((d, "granted_scope_insufficient"))
        for flow, code in cases:
            with self.subTest(code=code):
                self.assertIn(code, {x["code"] for x in analyzer.analyze(flow)["findings"]})

    def test_successful_token_rejected_on_retry(self):
        flow = valid_flow(); flow["retry"] = {"status": 401, "error": "invalid_token"}
        result = analyzer.analyze(flow)
        self.assertIn("token_rejected_on_retry", {x["code"] for x in result["findings"]})

    def test_should_not_activate_without_oauth_evidence(self):
        flow = {
            "schema_version": 1,
            "profile": "mcp-2025-11-25",
            "context": "initial",
            "target_resource": "https://mcp.example.test/mcp",
            "retry": {"status": 502, "error": "upstream_reset"},
        }
        result = analyzer.analyze(flow)
        self.assertEqual(result["classification"], "not_applicable")
        self.assertTrue(result["valid"])

    def test_unknown_fields_shapes_urls_and_status_fail_closed(self):
        bad = []
        a = valid_flow(); a["extra"] = 1; bad.append(a)
        b = valid_flow(); b["challenge"] = []; bad.append(b)
        c = valid_flow(); c["target_resource"] = "http://public.example.test"; bad.append(c)
        d = valid_flow(); d["retry"]["status"] = True; bad.append(d)
        e = valid_flow(); e["authorization_request"]["scope"] = ["x", "x"]; bad.append(e)
        f = valid_flow(); f["profile"] = "future"; bad.append(f)
        for flow in bad:
            with self.subTest(flow=flow):
                with self.assertRaises(analyzer.InputError):
                    analyzer.analyze(flow)

    def test_secret_fields_bearer_values_and_sensitive_urls_fail_closed(self):
        cases = []
        a = valid_flow(); a["token_response"]["access_token"] = "secret"; cases.append(a)
        b = valid_flow(); b["challenge"]["error"] = "Bearer abcdefghijklmnop"; cases.append(b)
        c = valid_flow(); c["target_resource"] = "https://mcp.example.test/mcp?access_token=x"; cases.append(c)
        for flow in cases:
            with self.subTest(flow=flow):
                with self.assertRaises(analyzer.InputError):
                    analyzer.analyze(flow)

    def test_error_text_invalid_scope_and_missing_target_fail_closed(self):
        cases = []
        a = valid_flow(); a["retry"] = {"status": 401, "error": "invalid token for user alice"}; cases.append(a)
        b = valid_flow(); b["authorization_request"]["scope"] = ["tools read"]; cases.append(b)
        c = valid_flow(); del c["target_resource"]; cases.append(c)
        for flow in cases:
            with self.subTest(flow=flow):
                with self.assertRaises(analyzer.InputError):
                    analyzer.analyze(flow)

    def test_non_standard_json_duplicate_keys_and_unreadable_input_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name, text in (("nan.json", '{"x": NaN}'), ("dupe.json", '{"x":1,"x":2}'), ("bad.json", "{")):
                path = base / name; path.write_text(text)
                with self.subTest(name=name), self.assertRaises(analyzer.InputError):
                    analyzer.load_json(path)
            with self.assertRaises(analyzer.InputError):
                analyzer.load_json(base / "missing.json")

    def test_serialization_failure_is_input_error(self):
        with mock.patch.object(analyzer.json, "dump", side_effect=OSError("controlled")):
            with self.assertRaises(analyzer.InputError):
                analyzer.emit_json({"valid": True}, io.StringIO())

    def test_cli_exit_codes_distinguish_blocked_and_input_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "flow.json"
            path.write_text(json.dumps(valid_flow()))
            with mock.patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(analyzer.main([str(path)]), 0)
            flow = valid_flow(); flow["authorization_request"]["resource"] += "/"
            path.write_text(json.dumps(flow))
            with mock.patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(analyzer.main([str(path)]), 1)
            path.write_text('{"x": NaN}')
            with mock.patch.object(sys, "stderr", io.StringIO()):
                self.assertEqual(analyzer.main([str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
