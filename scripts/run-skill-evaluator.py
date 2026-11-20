#!/usr/bin/env python3
"""Run strict, keyless SkillEvaluator checks on every tracked skill."""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent.parent
MPL_EXCEPTION_PATHS = {
    "skills/devops/terraform-style-guide",
    "skills/devops/terraform-test",
}
MPL_LICENSE_SHA256 = "3f3d9e0024b1921b067d6f7f88deb4a60cbe7a78e76c64e3f1d7fc3b779b9d04"
LAUNCH_WITH_AWS = Path("skills/cloud-aws/core/launch-with-aws")
ARCHIVE_EXCLUSIONS_SHA256 = "42d12856fdbf8c6c038beedeacccd2a3296485af843e3c097f7ea6eb3913f8dd"


def archive_exclusion_baseline(skill: Path) -> Path | None:
    if skill != LAUNCH_WITH_AWS:
        return None
    baseline = ROOT / "scripts/qa-policies/launch-with-aws.json"
    archive_source = ROOT / skill / "scripts/archive.py"
    if not baseline.is_file() or not archive_source.is_file() or archive_source.is_symlink():
        return None
    if hashlib.sha256(archive_source.read_bytes()).hexdigest() != ARCHIVE_EXCLUSIONS_SHA256:
        return None
    return baseline


def verified_mpl_exception(skill: Path, report: dict, exit_code: int) -> bool:
    """Recognize only the known MPL text misclassified by evaluator 1.0.1."""
    if skill.as_posix() not in MPL_EXCEPTION_PATHS or exit_code != 1:
        return False
    try:
        license_bytes = (ROOT / skill / "LICENSE").read_bytes()
        skill_text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill_text.split("---", 2)
        results = report["results"]
        if (hashlib.sha256(license_bytes).hexdigest() != MPL_LICENSE_SHA256
                or len(frontmatter) != 3 or frontmatter[0].strip()
                or re.findall(r"(?m)^license:\s*(\S+)\s*$", frontmatter[1]) != ["MPL-2.0"]
                or report["version"] != "1.0.1" or report["overall_status"] != "failed"
                or report["overall_passed"] is not False or report["incomplete_scans"] != []
                or report["total_errors"] != 1 or not isinstance(results, list)
                or len(results) != report["total_validators"] or not results):
            return False
        failed = []
        for result in results:
            if (not isinstance(result, dict) or result["incomplete_scans"] != []
                    or result["skipped"] is not False
                    or result["gating"]["blocking"] is not True):
                return False
            if result["status"] == "failed" and result["passed"] is False:
                failed.append(result)
            elif result["status"] != "passed" or result["passed"] is not True:
                return False
        if len(failed) != 1 or failed[0]["validator"] != "License Compliance":
            return False
        finding_list = failed[0]["findings"]
        if failed[0]["summary"]["errors"] != 1 or len(finding_list) != 1:
            return False
        finding = finding_list[0]
        expected = {
            "category": "LICENSE", "severity": "critical", "check_name": "blocked_license",
            "message": "License 'GPL-3.0' is not allowed (restrictive/copyleft)",
            "file_path": "LICENSE", "line_number": None,
        }
        if not all(finding.get(key) == value for key, value in expected.items()):
            return False
        groups = [group for group in report["finding_groups"]
                  if group["severity"] in ("critical", "high")]
        return (len(groups) == 1 and groups[0]["finding_id"] == finding["finding_id"]
                and groups[0]["category"] == "LICENSE"
                and groups[0]["check_name"] == "blocked_license"
                and groups[0]["occurrence_count"] == 1
                and len(groups[0]["occurrences"]) == 1
                and groups[0]["occurrences"][0]["file_path"] == "LICENSE")
    except (OSError, UnicodeError, KeyError, TypeError, ValueError, AttributeError):
        return False


def validate(skill: Path, reports: Path, source: list[str]) -> dict:
    output = reports / "skills" / skill.relative_to("skills")
    output.mkdir(parents=True, exist_ok=True)
    command = [
        "skillevaluator", "validate", str(skill), "--profile", "default",
        "--tiers", "1", "--no-llm", "--min-score", "70", "--continue-on-failure",
        "--report", "json,markdown", "--output-dir", str(output), *source,
    ]
    pii_waivers = ROOT / "pii-waivers.json"
    if pii_waivers.is_file():
        command.extend(["--pii-waivers", str(pii_waivers)])
    security_baseline = archive_exclusion_baseline(skill)
    if security_baseline is not None:
        command.extend(["--skillspector-baseline", str(security_baseline)])
    with (output / "cli.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False)

    json_reports = list(output.glob("skillevaluator-output-*.json"))
    status = "error"
    if len(json_reports) == 1 and json_reports[0].with_suffix(".md").is_file():
        try:
            report = json.loads(json_reports[0].read_text(encoding="utf-8"))
        except (OSError, ValueError):
            report = None
        verdict = report.get("overall_status") if isinstance(report, dict) else None
        success = verdict == "passed" and completed.returncode == 0
        blocked = verdict in ("failed", "incomplete") and completed.returncode == 1
        if success or blocked:
            status = verdict
    exception = None
    if status == "failed" and verified_mpl_exception(skill, report, completed.returncode):
        exception = "verified MPL-2.0 license text misclassified as GPL-3.0"
    return {"skill": skill.as_posix(), "status": status, "exit_code": completed.returncode,
            "disposition": "accepted_exception" if exception else status,
            "security_baseline": security_baseline.relative_to(ROOT).as_posix() if security_baseline else None,
            "exception": exception}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if shutil.which("skillevaluator") is None:
        parser.error("install SkillEvaluator so skillevaluator is available on PATH")
    reports = args.output_dir.resolve()
    if reports.exists() and any(reports.iterdir()):
        parser.error("--output-dir must be empty")

    manifests = subprocess.check_output(["git", "ls-files", "--deduplicate", "-z", "--", "skills"], cwd=ROOT)
    skills = [Path(name).parent for name in manifests.decode("utf-8").split("\0") if name.endswith("/SKILL.md")]
    if not skills:
        parser.error("no tracked skills found")

    source = []
    if os.environ.get("GITHUB_REPOSITORY") and os.environ.get("GITHUB_SHA"):
        source = [
            "--evaluated-source-repository", os.environ["GITHUB_REPOSITORY"],
            "--evaluated-source-revision", os.environ["GITHUB_SHA"],
        ]

    # A standalone scan can verify evidence for references to files a skill creates
    # in the user's project. It also evaluates every published nested skill.
    print(f"Evaluating {len(skills)} tracked skills with {args.workers} workers", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda skill: validate(skill, reports, source), skills))
    counts = Counter(result["status"] for result in results)
    dispositions = Counter(result["disposition"] for result in results)
    (reports / "summary.json").write_text(
        json.dumps({"total": len(results), "counts": dict(counts),
                    "dispositions": dict(dispositions), "results": results}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(", ".join(f"{count} {status}" for status, count in sorted(counts.items())))
    if dispositions["accepted_exception"]:
        print(f"Accepted verified MPL-2.0 misclassifications: {dispositions['accepted_exception']}")
    return int(dispositions["passed"] + dispositions["accepted_exception"] != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
