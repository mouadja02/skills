import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_grpc_deadline.py"
FIXTURES = ROOT / "tests" / "fixtures"
spec = importlib.util.spec_from_file_location("deadline", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("unable to load analyzer")
deadline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deadline)

class DeadlineTests(unittest.TestCase):
    def load(self, name):
        return json.loads((FIXTURES / name).read_text())

    def test_normal_transition(self):
        result = deadline.analyze(self.load("normal.json"))
        self.assertEqual("ready", result["classification"])
        self.assertEqual([], result["findings"])
        self.assertEqual(2_000_000_000, result["initial_timeout_ns"])
        self.assertEqual({"hop":"proxy","received_ns":2_000_000_000,"elapsed_ns":250_000_000,
                          "available_ns":1_750_000_000,"sent_ns":1_750_000_000}, result["transitions"][0])

    def test_edge_separates_expansion_and_cancellation(self):
        result = deadline.analyze(self.load("edge.json"))
        self.assertEqual("blocked", result["classification"])
        self.assertEqual(["deadline_budget_expanded", "work_continued_after_expiry"],
                         [f["code"] for f in result["findings"]])
        self.assertEqual(700_000_000, result["transitions"][1]["available_ns"])

    def test_timeout_grammar_all_units_and_boundaries(self):
        for suffix, multiplier in deadline.UNITS.items():
            self.assertEqual(multiplier, deadline.timeout_ns("1" + suffix))
            self.assertEqual(99_999_999 * multiplier, deadline.timeout_ns("99999999" + suffix))
        for bad in ["0S", "000000001S", "100000000S", "+1S", "1.0S", "1s", " 1S", "1S ", "1", 1]:
            with self.subTest(bad=bad):
                with self.assertRaises(deadline.InputError):
                    deadline.timeout_ns(bad)

    def test_invalid_timeout_is_parsed_protocol_finding(self):
        doc = self.load("normal.json")
        doc["initial_timeout"] = "000000001S"
        result = deadline.analyze(doc)
        self.assertEqual("blocked", result["classification"])
        self.assertEqual("invalid_timeout", result["findings"][0]["code"])

    def test_safe_clamp_is_observation_not_violation(self):
        result = deadline.analyze(self.load("clamp-safe.json"))
        self.assertEqual("ready", result["classification"])
        self.assertEqual("server_max_clamp", result["observations"][0]["code"])
        self.assertEqual(1_000_000_000, result["effective_initial_ns"])

    def test_omission_policy_and_not_applicable(self):
        for rpc_type in deadline.RPC_TYPES:
            base = {"schema_version":1,"kind":"grpc_deadline_trace","rpc_type":rpc_type,
                    "missing_deadline_policy":"allow"}
            self.assertEqual("ready", deadline.analyze(base)["classification"])
            base["missing_deadline_policy"] = "block"
            self.assertEqual("blocked", deadline.analyze(base)["classification"])
        result = deadline.analyze(self.load("not-applicable.json"))
        self.assertEqual("not_applicable", result["classification"])

    def test_expired_before_dispatch(self):
        doc = self.load("normal.json")
        doc["hops"] = [{"name":"slow","elapsed_ns":2_000_000_000,"forwarded_timeout":"1n"}]
        codes = [f["code"] for f in deadline.analyze(doc)["findings"]]
        self.assertEqual(["expired_before_dispatch", "deadline_budget_expanded"], codes)

    def test_server_expiry_boundary_is_exact(self):
        doc = self.load("normal.json")
        doc["initial_timeout"] = "1S"
        doc["hops"] = []
        doc["server"] = {"elapsed_since_initial_ns":999_999_999,"work_active":True,"cancellation_observed":False}
        self.assertEqual("ready", deadline.analyze(doc)["classification"])
        doc["server"]["elapsed_since_initial_ns"] = 1_000_000_000
        self.assertEqual("work_continued_after_expiry", deadline.analyze(doc)["findings"][0]["code"])

    def test_schema_rejects_bool_float_nonfinite_and_wrong_shapes(self):
        docs = [[], {"schema_version":1,"kind":"grpc_deadline_trace","rpc_type":"bad","missing_deadline_policy":"allow"},
                {"schema_version":1,"kind":"grpc_deadline_trace","rpc_type":"unary","missing_deadline_policy":"allow","initial_timeout":"1S","hops":{}},
                {"schema_version":1,"kind":"grpc_deadline_trace","rpc_type":"unary","missing_deadline_policy":"allow","initial_timeout":"1S","hops":[{"name":"x","elapsed_ns":True,"forwarded_timeout":"1S"}]}]
        for doc in docs:
            with self.subTest(doc=doc):
                with self.assertRaises(deadline.InputError): deadline.analyze(doc)
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
            tmp.write('{"schema_version": NaN}')
            name = tmp.name
        try:
            proc = subprocess.run([sys.executable, str(SCRIPT), name], text=True, capture_output=True)
            self.assertEqual(2, proc.returncode)
            self.assertEqual("input_error", json.loads(proc.stdout)["classification"])
        finally:
            Path(name).unlink()

    def test_malformed_cli_is_input_error(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), str(FIXTURES/"malformed.txt")], text=True, capture_output=True)
        self.assertEqual(2, proc.returncode)
        self.assertEqual("input_error", json.loads(proc.stdout)["classification"])

    def test_blocked_cli_exit_one(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), str(FIXTURES/"edge.json")], text=True, capture_output=True)
        self.assertEqual(1, proc.returncode)
        self.assertEqual("blocked", json.loads(proc.stdout)["classification"])

    @unittest.skipUnless(Path("/dev/full").exists(), "requires /dev/full")
    def test_broken_stdout_returns_documented_exit_two(self):
        with open("/dev/full", "w") as sink:
            proc = subprocess.run([sys.executable, str(SCRIPT), str(FIXTURES/"normal.json")],
                                  stdout=sink, stderr=subprocess.DEVNULL)
        self.assertEqual(2, proc.returncode)

if __name__ == "__main__":
    unittest.main()
