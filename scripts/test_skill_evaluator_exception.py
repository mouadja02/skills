import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('evaluator', ROOT / 'scripts/run-skill-evaluator.py')
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


class MplExceptionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.skill = Path('skills/devops/terraform-test')
        dest = self.root / self.skill
        dest.mkdir(parents=True)
        (dest / 'LICENSE').write_bytes((ROOT / self.skill / 'LICENSE').read_bytes())
        (dest / 'SKILL.md').write_text('---\nlicense: MPL-2.0\n---\n', encoding='utf-8')
        finding = {'finding_id': 'known', 'category': 'LICENSE', 'severity': 'critical',
                   'check_name': 'blocked_license', 'message': "License 'GPL-3.0' is not allowed (restrictive/copyleft)",
                   'file_path': 'LICENSE', 'line_number': None}
        failed = {'validator': 'License Compliance', 'status': 'failed', 'passed': False,
                  'incomplete_scans': [], 'skipped': False, 'gating': {'blocking': True},
                  'summary': {'errors': 1}, 'findings': [finding]}
        group = {'finding_id': 'known', 'category': 'LICENSE', 'severity': 'critical',
                 'check_name': 'blocked_license', 'occurrence_count': 1,
                 'occurrences': [{'file_path': 'LICENSE'}]}
        self.report = {'version': '1.0.1', 'overall_status': 'failed', 'overall_passed': False,
                       'incomplete_scans': [], 'total_errors': 1, 'total_validators': 1,
                       'results': [failed], 'finding_groups': [group]}
        self.root_patch = patch.object(evaluator, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def check(self, report=None, skill=None, exit_code=1):
        return evaluator.verified_mpl_exception(skill or self.skill, self.report if report is None else report, exit_code)

    def test_known_mpl_only(self):
        self.assertTrue(self.check())
        self.assertFalse(self.check(skill=Path('skills/other/terraform-test')))
        self.assertFalse(self.check(exit_code=0))

    def test_changed_license_and_gpl(self):
        license_file = self.root / self.skill / 'LICENSE'
        for text in (b'GNU General Public License Version 3', license_file.read_bytes() + b'changed'):
            license_file.write_bytes(text)
            self.assertFalse(self.check())

    def test_extra_findings_and_failed_validators(self):
        report = copy.deepcopy(self.report)
        report['results'][0]['findings'].append(copy.deepcopy(report['results'][0]['findings'][0]))
        self.assertFalse(self.check(report))
        report = copy.deepcopy(self.report)
        report['finding_groups'].append({'severity': 'critical', 'category': 'LICENSE'})
        self.assertFalse(self.check(report))
        report = copy.deepcopy(self.report)
        report['results'].append(copy.deepcopy(report['results'][0]))
        report['total_validators'] += 1
        self.assertFalse(self.check(report))

    def test_missing_or_mismatched_evidence(self):
        self.assertFalse(self.check({}))
        report = copy.deepcopy(self.report)
        report['results'][0]['findings'][0]['file_path'] = 'other/LICENSE'
        self.assertFalse(self.check(report))
        (self.root / self.skill / 'SKILL.md').write_text('---\nlicense: GPL-3.0\n---\n', encoding='utf-8')
        self.assertFalse(self.check())


class ArchiveBaselineTest(unittest.TestCase):
    def test_applies_only_to_the_reviewed_archive_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = evaluator.LAUNCH_WITH_AWS
            archive = root / skill / 'scripts/archive.py'
            archive.parent.mkdir(parents=True)
            reviewed_source = b'# Reviewed archive fixture\n'
            archive.write_bytes(reviewed_source)
            baseline = root / 'scripts/qa-policies/launch-with-aws.json'
            baseline.parent.mkdir(parents=True)
            baseline.write_text('{}', encoding='utf-8')
            digest = hashlib.sha256(reviewed_source).hexdigest()
            with patch.multiple(evaluator, ROOT=root, ARCHIVE_EXCLUSIONS_SHA256=digest):
                self.assertEqual(evaluator.archive_exclusion_baseline(skill), baseline)
                self.assertIsNone(evaluator.archive_exclusion_baseline(Path('skills/other/launch-with-aws')))
                archive.write_bytes(archive.read_bytes() + b'\n# Different source\n')
                self.assertIsNone(evaluator.archive_exclusion_baseline(skill))


if __name__ == '__main__':
    unittest.main()
