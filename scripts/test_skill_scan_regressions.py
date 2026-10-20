"""Keep detection coverage and response data intact during catalog cleanup."""

import ast
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def patterns(source, assignment):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == assignment for target in targets):
                return ast.literal_eval(node.value)
    raise AssertionError(f"Missing pattern table: {assignment}")


class ScanRegressions(unittest.TestCase):
    def test_dynamic_execution_payloads_remain_high_findings(self):
        cases = [
            ('skills/skills-management/skill-scanner/scripts/scan_skill.py', 'DANGEROUS_SCRIPT_PATTERNS'),
            ('skills/devops/senior-secops/scripts/security_scanner.py', 'COMMAND_INJECTION_PATTERNS'),
        ]
        for filename, table in cases:
            with self.subTest(filename=filename):
                current = patterns((ROOT / filename).read_text(encoding='utf-8'), table)
                for operation in ('eval', 'exec'):
                    payload = operation + '(user_input)'
                    matched = [entry for entry in current if re.search(entry[0], payload)]
                    self.assertTrue(matched, f'Detector missed {operation}')
                    if table == 'DANGEROUS_SCRIPT_PATTERNS':
                        self.assertTrue(all(entry[2] == 'high' for entry in matched))


    def test_private_key_markers_are_still_detected(self):
        module = load_module('catalog_secret_patterns',
            'skills/devops/senior-security/scripts/secret_scanner.py')
        rules = {rule.pattern_id: rule for rule in module.SECRET_PATTERNS}
        for rule_id, kind in [('CRYPTO001', 'RSA'), ('CRYPTO002', 'EC'), ('CRYPTO003', 'OPENSSH')]:
            rule = rules[rule_id]
            marker = ' '.join(['-----BEGIN', kind, 'PRIVATE', 'KEY-----'])
            with self.subTest(kind=kind):
                self.assertIsNotNone(re.search(rule.regex, marker))
                self.assertEqual(rule.severity, module.Severity.CRITICAL)
                self.assertIsNone(re.search(rule.regex, 'ordinary public text'))

    def test_pagination_tokens_round_trip_through_json(self):
        directory = ROOT / 'skills/cloud-aws/core/aws-observability/scripts'
        sys.path.insert(0, str(directory))
        try:
            from di_crud_rendering import render_list_instrumentations_output
            from di_status_rendering import render_get_instrumentation_configuration_status_output
            for token in ['opaque-pagination-value', 'quoted"value\\suffix']:
                outputs = [
                    render_list_instrumentations_output(
                        {'LatestConfigurations': [{}], 'NextToken': token},
                        'code', 'service', 'environment'),
                    render_get_instrumentation_configuration_status_output(
                        {'NextToken': token}, 'code', 'service', 'environment', 'ACTIVE'),
                ]
                for output in outputs:
                    encoded = output.split('Use next_token=', 1)[1].split(' to retrieve', 1)[0]
                    self.assertEqual(json.loads(encoded), token)
        finally:
            sys.path.remove(str(directory))


if __name__ == '__main__':
    unittest.main()
