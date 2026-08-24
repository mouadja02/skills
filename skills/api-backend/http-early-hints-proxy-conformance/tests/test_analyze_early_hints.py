import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_early_hints.py"
spec = importlib.util.spec_from_file_location("analyzer", SCRIPT)
analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyzer)

BODY = "a" * 64


def event(status, headers=None, body=None):
    row = {"status": status, "headers": headers or []}
    if body is not None:
        row["body_sha256"] = body
    return row


def hop(name, protocol="http/1.1", hints=1, final_headers=None, body=BODY):
    events = [event(103, [["Link", f"</{i}.css>; rel=preload"]]) for i in range(hints)]
    events.append(event(200, final_headers, body))
    return {"name": name, "protocol": protocol, "events": events}


def doc(*hops):
    return {"schema_version": 1, "hops": list(hops)}


class AnalyzerTests(unittest.TestCase):
    def test_preserved_multiple_hints_across_protocols_is_ready(self):
        r = analyzer.analyze(doc(hop("origin", hints=2), hop("proxy", "h2", hints=2), hop("client", "h3", hints=2)))
        self.assertEqual(r["control"], "ready")
        self.assertTrue(all(x["outcome"] == "pass" for x in r["comparisons"]))

    def test_first_drop_is_localized(self):
        r = analyzer.analyze(doc(hop("origin"), hop("p1"), hop("p2", hints=0)))
        self.assertEqual(r["control"], "blocked")
        self.assertEqual(r["findings"][0], {"type": "dropped", "between": ["p1", "p2"]})

    def test_merge_into_final_is_not_a_pass(self):
        link = [["Link", "</0.css>; rel=preload"]]
        r = analyzer.analyze(doc(hop("origin"), hop("proxy", hints=0, final_headers=link)))
        self.assertEqual(r["comparisons"][0]["outcome"], "merged_into_final")
        self.assertEqual(r["control"], "blocked")

    def test_reordering_is_blocked(self):
        a = hop("a", hints=2)
        b = hop("b", hints=2)
        b["events"][0], b["events"][1] = b["events"][1], b["events"][0]
        self.assertEqual(analyzer.analyze(doc(a, b))["comparisons"][0]["outcome"], "mutated_or_reordered")

    def test_final_status_or_body_change_is_blocked(self):
        b = hop("b")
        b["events"][-1]["body_sha256"] = "b" * 64
        types = [x["type"] for x in analyzer.analyze(doc(hop("a"), b))["findings"]]
        self.assertIn("final_response_changed", types)

    def test_no_103_is_not_applicable(self):
        r = analyzer.analyze(doc(hop("origin", hints=0), hop("client", hints=0)))
        self.assertEqual(r["control"], "not_applicable")
        self.assertFalse(r["applicable"])

    def test_101_is_terminal_not_continuation(self):
        valid = {"name": "upgrade", "protocol": "http/1.1", "events": [event(101)]}
        self.assertEqual(analyzer.analyze(doc(valid))["control"], "not_applicable")
        invalid = {"name": "bad", "protocol": "http/1.1", "events": [event(101), event(200)]}
        with self.assertRaises(analyzer.InputError):
            analyzer.analyze(doc(invalid))

    def test_informational_only_is_rejected(self):
        bad = {"name": "bad", "protocol": "h2", "events": [event(103)]}
        with self.assertRaises(analyzer.InputError):
            analyzer.analyze(doc(bad))

    def test_informational_body_is_rejected(self):
        bad = {"name": "bad", "protocol": "h2", "events": [event(103, body=BODY), event(200)]}
        with self.assertRaises(analyzer.InputError):
            analyzer.analyze(doc(bad))

    def test_header_injection_is_rejected(self):
        bad = hop("bad")
        bad["events"][0]["headers"] = [["Link", "ok\r\nInjected: yes"]]
        with self.assertRaises(analyzer.InputError):
            analyzer.analyze(doc(bad))

    def test_invalid_field_name_is_rejected(self):
        bad = hop("bad")
        bad["events"][0]["headers"] = [["bad name", "value"]]
        with self.assertRaises(analyzer.InputError):
            analyzer.analyze(doc(bad))

    def test_bool_status_duplicate_names_and_unknown_protocol_fail_closed(self):
        for value in [
            doc({"name": "x", "protocol": "h2", "events": [event(True)]}),
            doc(hop("x"), hop("x")),
            doc(hop("x", protocol="spdy")),
            {"schema_version": 1, "hops": [hop("x")], "hopz": []},
            {"schema_version": 1, "hops": [{**hop("x"), "complete": True}]},
        ]:
            with self.subTest(value=value), self.assertRaises(analyzer.InputError):
                analyzer.analyze(value)

    def test_nonfinite_malformed_and_oversize_cli_inputs_are_blocked(self):
        for raw, extra in [
            (b'{"x":NaN}', []),
            (b'{', []),
            (b'{"schema_version":1,"schema_version":1,"hops":[]}', []),
            (b'{}', ["--max-bytes", "1"]),
        ]:
            cp = subprocess.run([sys.executable, str(SCRIPT), "-", *extra], input=raw, capture_output=True)
            self.assertEqual(cp.returncode, 2)
            self.assertEqual(json.loads(cp.stdout)["control"], "blocked")

    def test_missing_input_is_io_failure(self):
        cp = subprocess.run([sys.executable, str(SCRIPT), "/definitely/missing"], capture_output=True)
        self.assertEqual(cp.returncode, 3)
        self.assertEqual(json.loads(cp.stdout)["control"], "blocked")

    def test_unwritable_output_is_exit_three(self):
        payload = json.dumps(doc(hop("origin"))).encode()
        cp = subprocess.run(f"{sys.executable} {SCRIPT} - > /dev/full", input=payload, shell=True)
        self.assertEqual(cp.returncode, 3)


if __name__ == "__main__":
    unittest.main()
