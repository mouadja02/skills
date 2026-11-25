"""Tests for the agentic-benchmark-task-authoring skill's package validator.

Runs under pytest or plain stdlib execution:

    python3 tests/skills/test_agentic_benchmark_task_authoring_skill.py
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(
    REPO_ROOT, "skills", "agent-eval", "agentic-benchmark-task-authoring", "scripts",
    "verify_task_package.py",
)

VALID_TASK_TOML = textwrap.dedent(
    """\
    schema_version = "1.4"

    artifacts = ["/app/out/report.json"]

    [metadata]
    category = "data-engineering"

    [verifier]
    environment_mode = "separate"
    timeout_sec = 300.0
    network_mode = "no-network"

    [agent]
    timeout_sec = 900.0

    [environment]
    network_mode = "no-network"
    """
)

VALID_TEST_SH = textwrap.dedent(
    """\
    #!/bin/bash
    set -uo pipefail
    mkdir -p /logs/verifier
    printf '0' > /logs/verifier/reward.txt
    [ -s /app/out/report.json ] || exit 0
    printf '1' > /logs/verifier/reward.txt
    """
)

VALID_INSTRUCTION = "# Report\n\nWrite /app/out/report.json with the unmatched rows.\n"

VALID_ROLLOUTS = {
    "task": "report",
    "rollouts": [
        {"class": "oracle", "trials": [1, 1, 1]},
        {"class": "no-op", "trials": [0, 0, 0]},
        {"class": "near-miss", "trials": [0, 0, 0]},
        {"class": "shortcut", "trials": [0, 0, 0]},
        {"class": "alternative-valid", "trials": [1, 1, 1]},
    ],
}


def _make_task(root, *, toml=VALID_TASK_TOML, test_sh=VALID_TEST_SH,
               instruction=VALID_INSTRUCTION, solve=True, extra_files=None):
    os.makedirs(os.path.join(root, "environment"), exist_ok=True)
    with open(os.path.join(root, "task.toml"), "w", encoding="utf-8") as fh:
        fh.write(toml)
    with open(os.path.join(root, "instruction.md"), "w", encoding="utf-8") as fh:
        fh.write(instruction)
    with open(os.path.join(root, "environment", "Dockerfile"), "w", encoding="utf-8") as fh:
        fh.write("FROM ubuntu:24.04\n")
    os.makedirs(os.path.join(root, "tests"), exist_ok=True)
    test_path = os.path.join(root, "tests", "test.sh")
    with open(test_path, "w", encoding="utf-8") as fh:
        fh.write(test_sh)
    os.chmod(test_path, 0o755)
    os.makedirs(os.path.join(root, "solution"), exist_ok=True)
    solve_path = os.path.join(root, "solution", "solve.sh")
    with open(solve_path, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/bash\ntrue\n")
    os.chmod(solve_path, 0o755 if solve else 0o644)
    for rel, content in (extra_files or {}).items():
        target = os.path.join(root, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)
    return root


def _run(task_dir, rollouts=None):
    cmd = [sys.executable, SCRIPT, task_dir, "--json"]
    if rollouts:
        cmd.extend(["--rollouts", rollouts])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    report = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, report, proc.stderr


def _codes(report):
    return {item["code"] for item in report.get("findings", [])}


def test_valid_package_is_publishable():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"))
        code, report, err = _run(task)
        assert code == 0, err
        assert report["publishable"] is True
        assert report["blocking_findings"] == 0
        assert set(report["checks_run"]) >= {"layout", "task.toml", "tests/test.sh", "leakage"}


def test_missing_reward_channel_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"),
                          test_sh="#!/bin/bash\necho done\n")
        code, report, _ = _run(task)
        assert code == 1
        assert "missing-reward-channel" in _codes(report)


def test_shared_verifier_blocks():
    toml = VALID_TASK_TOML.replace('environment_mode = "separate"\n', "")
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), toml=toml)
        code, report, _ = _run(task)
        assert code == 1
        assert "verifier-not-separated" in _codes(report)


def test_shared_verifier_with_environment_section_is_a_conflict():
    toml = textwrap.dedent(
        """\
        schema_version = "1.4"

        artifacts = ["/app/out/report.json"]

        [verifier]
        environment_mode = "shared"
        timeout_sec = 300.0

        [verifier.environment]
        network_mode = "no-network"

        [agent]
        timeout_sec = 900.0

        [environment]
        network_mode = "no-network"
        """
    )
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), toml=toml)
        code, report, _ = _run(task)
        assert code == 1
        assert "verifier-mode-conflict" in _codes(report)


def test_public_verifier_network_blocks():
    # No verifier network override and no [verifier.environment]: the verifier inherits
    # the agent environment, whose network_mode default is "public".
    toml = textwrap.dedent(
        """\
        schema_version = "1.4"

        artifacts = ["/app/out/report.json"]

        [verifier]
        environment_mode = "separate"
        timeout_sec = 300.0

        [agent]
        timeout_sec = 900.0
        """
    )
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), toml=toml)
        code, report, _ = _run(task)
        assert code == 1
        assert "verifier-public-network" in _codes(report)


def test_allowlist_without_hosts_blocks_and_with_hosts_passes():
    no_hosts = VALID_TASK_TOML.replace(
        'network_mode = "no-network"\n\n[agent]', 'network_mode = "allowlist"\n\n[agent]'
    )
    with_hosts = no_hosts.replace(
        'network_mode = "allowlist"', 'network_mode = "allowlist"\nallowed_hosts = ["pypi.org"]'
    )
    with tempfile.TemporaryDirectory() as tmp:
        bad = _make_task(os.path.join(tmp, "bad"), toml=no_hosts)
        code, report, _ = _run(bad)
        assert code == 1
        assert "verifier-allowlist-empty" in _codes(report)
        good = _make_task(os.path.join(tmp, "good"), toml=with_hosts)
        code, report, _ = _run(good)
        assert code == 0, report
        assert report["publishable"] is True


def test_undeclared_artifact_blocks():
    toml = VALID_TASK_TOML.replace('artifacts = ["/app/out/report.json"]', "artifacts = []")
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), toml=toml)
        code, report, _ = _run(task)
        assert code == 1
        assert "undeclared-artifact" in _codes(report)


def test_system_paths_are_not_treated_as_artifacts():
    test_sh = VALID_TEST_SH.replace(
        "[ -s /app/out/report.json ] || exit 0",
        "/usr/bin/env true\n/usr/bin/find /usr/share -maxdepth 0 2>/dev/null\n"
        "[ -s /app/out/report.json ] || exit 0",
    )
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), test_sh=test_sh)
        code, report, _ = _run(task)
        assert code == 0, report
        assert report["publishable"] is True


def test_input_shipped_in_environment_is_not_an_artifact():
    test_sh = VALID_TEST_SH.replace(
        "[ -s /app/out/report.json ] || exit 0",
        "[ -s /app/in/partner.csv ] || exit 0\n[ -s /app/out/report.json ] || exit 0",
    )
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), test_sh=test_sh,
                          extra_files={"environment/in/partner.csv": "id,amount\n1,10\n"})
        code, report, _ = _run(task)
        assert code == 0, report
        assert report["publishable"] is True
        # Same path is flagged once the input no longer ships in the image.
        os.remove(os.path.join(task, "environment", "in", "partner.csv"))
        code, report, _ = _run(task)
        assert code == 1, report
        assert "undeclared-artifact" in _codes(report)


def test_instruction_leak_blocks():
    for leak in ("Graded by tests/test_outputs.py.", "Run solution/solve.sh for the answer.",
                 "Write the reward to /logs/verifier/reward.txt."):
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_task(os.path.join(tmp, "task"),
                              instruction=VALID_INSTRUCTION + "\n" + leak + "\n")
            code, report, _ = _run(task)
            assert code == 1, leak
            assert "instruction-leak" in _codes(report), leak


def test_non_executable_solve_and_test_scripts_block():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), solve=False)
        code, report, _ = _run(task)
        assert code == 1
        assert "solution-not-executable" in _codes(report)


def test_expected_fixture_in_agent_environment_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(
            os.path.join(tmp, "task"),
            extra_files={"tests/expected.json": "[]\n", "environment/expected.json": "[]\n"},
        )
        code, report, _ = _run(task)
        assert code == 1
        assert "fixture-in-agent-env" in _codes(report)


def test_malformed_rollout_json_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"))
        rollouts = os.path.join(tmp, "rollouts.txt")
        with open(rollouts, "w", encoding="utf-8") as fh:
            fh.write('{"rollouts": [ {"class": "oracle", "trials": [1, 1,\n')
        code, report, _ = _run(task, rollouts)
        assert code == 1
        assert "rollouts-unreadable" in _codes(report)


def test_rollout_expectations_are_enforced():
    cases = {}
    missing = json.loads(json.dumps(VALID_ROLLOUTS))
    missing["rollouts"] = [r for r in missing["rollouts"] if r["class"] != "shortcut"]
    cases["missing"] = missing

    wrong = json.loads(json.dumps(VALID_ROLLOUTS))
    for entry in wrong["rollouts"]:
        if entry["class"] == "shortcut":
            entry["trials"] = [0, 1, 0]
    cases["wrong"] = wrong

    few = json.loads(json.dumps(VALID_ROLLOUTS))
    for entry in few["rollouts"]:
        entry["trials"] = entry["trials"][:2]
    cases["few"] = few

    flaky = json.loads(json.dumps(VALID_ROLLOUTS))
    for entry in flaky["rollouts"]:
        if entry["class"] == "oracle":
            entry["trials"] = [1, 1, 0]
    cases["flaky"] = flaky

    expected_codes = {
        "missing": "control-missing",
        "wrong": "control-wrong-reward",
        "few": "control-too-few-trials",
        "flaky": "flaky-control",
    }
    for name, manifest in cases.items():
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_task(os.path.join(tmp, "task"))
            path = os.path.join(tmp, "rollouts.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(manifest, fh)
            code, report, _ = _run(task, path)
            assert code == 1, name
            assert expected_codes[name] in _codes(report), (name, _codes(report))


def test_complete_rollouts_pass():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"))
        path = os.path.join(tmp, "rollouts.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(VALID_ROLLOUTS, fh)
        code, report, err = _run(task, path)
        assert code == 0, err
        assert report["publishable"] is True
        assert "rollouts" in report["checks_run"]


def test_unparseable_toml_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), toml="schema_version = \n[verifier\n")
        code, report, _ = _run(task)
        assert code == 1
        assert "task-toml-unparseable" in _codes(report)


def test_missing_task_directory_exits_two():
    code, _report, err = _run(os.path.join(tempfile.gettempdir(), "does-not-exist-task-package"))
    assert code == 2
    assert "not found" in err


def test_missing_instruction_blocks_and_empty_instruction_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), instruction="   \n")
        code, report, _ = _run(task)
        assert code == 1
        assert "instruction-empty" in _codes(report)


def test_secret_material_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(
            os.path.join(tmp, "task"),
            extra_files={"tests/grader.py": 'KEY = "sk-' + "a" * 24 + '"\n'},
        )
        code, report, _ = _run(task)
        assert code == 1
        assert "secret-material" in _codes(report)


def test_missing_metadata_category_is_a_warning_only():
    toml = VALID_TASK_TOML.replace('category = "data-engineering"\n', "")
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), toml=toml)
        code, report, _ = _run(task)
        assert code == 0, report
        assert report["publishable"] is True
        assert "missing-metadata-category" in _codes(report)
        assert report["warning_findings"] >= 1


def test_report_is_deterministic():
    with tempfile.TemporaryDirectory() as tmp:
        task = _make_task(os.path.join(tmp, "task"), solve=False)
        first = _run(task)[1]
        second = _run(task)[1]
        assert first == second


def _main():
    failures = []
    tests = [obj for name, obj in sorted(globals().items())
             if name.startswith("test_") and callable(obj)]
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failures.append((test.__name__, exc))
            print(f"FAIL {test.__name__}: {exc}")
    print(f"{len(tests) - len(failures)}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_main())
