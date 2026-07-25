import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ssa_ownership.py"
SPEC = importlib.util.spec_from_file_location("ssa_ownership", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class OwnershipTests(unittest.TestCase):
    def write(self, value=None, raw=None):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        with handle:
            handle.write(raw if raw is not None else json.dumps(value))
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return handle.name

    def resource(self, fields=None):
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "api",
                "namespace": "prod",
                "resourceVersion": "12",
                "managedFields": [{
                    "manager": "gitops",
                    "operation": "Apply",
                    "apiVersion": "apps/v1",
                    "fieldsType": "FieldsV1",
                    "fieldsV1": fields or {
                        "f:spec": {
                            "f:replicas": {},
                            "f:template": {
                                "f:spec": {
                                    "f:containers": {
                                        "k:{\"name\":\"api\"}": {".": {}, "f:image": {}}
                                    }
                                }
                            },
                        }
                    },
                }],
            },
        }

    def test_inventory_flattens_fields_and_keyed_lists(self):
        result = MOD.inventory(self.write(self.resource()))
        paths = result["managers"][0]["paths"]
        self.assertEqual(result["resource"]["name"], "api")
        self.assertIn(".spec.replicas", paths)
        self.assertIn('.spec.template.spec.containers[name="api"]', paths)
        self.assertIn('.spec.template.spec.containers[name="api"].image', paths)

    def test_conflicts_extract_manager_api_and_multiple_paths(self):
        path = self.write(raw='Apply failed: conflict with "hpa" using autoscaling/v1: .spec.replicas, .metadata.labels.team\n')
        result = MOD.conflicts(path)
        self.assertEqual(result["conflicts"][0]["manager"], "hpa")
        self.assertEqual(result["conflicts"][0]["paths"], [".spec.replicas", ".metadata.labels.team"])

    def test_rejects_non_object_root(self):
        with self.assertRaisesRegex(ValueError, "root must be an object"):
            MOD.inventory(self.write([]))

    def test_rejects_malformed_json(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "inventory", self.write(raw="{")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error:", proc.stderr)

    def test_rejects_nan(self):
        data = '{"metadata":{"managedFields":[]},"x":NaN}'
        proc = subprocess.run([sys.executable, str(SCRIPT), "inventory", self.write(raw=data)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("non-standard JSON constant", proc.stderr)

    def test_rejects_bad_fields_shape_and_unknown_prefix(self):
        bad = self.resource({"x:spec": {}})
        with self.assertRaisesRegex(ValueError, "unknown fieldsV1 key prefix"):
            MOD.inventory(self.write(bad))
        bad = self.resource()
        bad["metadata"]["managedFields"][0]["fieldsV1"] = []
        with self.assertRaisesRegex(ValueError, "fieldsV1 must be an object"):
            MOD.inventory(self.write(bad))

    def test_rejects_malformed_selector(self):
        with self.assertRaisesRegex(ValueError, "invalid managedFields selector"):
            MOD.inventory(self.write(self.resource({"f:items": {"k:not-json": {}}})))

    def test_rejects_unrecognized_conflict_and_missing_file(self):
        with self.assertRaisesRegex(ValueError, "no recognized"):
            MOD.conflicts(self.write(raw="ordinary validation error"))
        proc = subprocess.run([sys.executable, str(SCRIPT), "inventory", "/not/present"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
