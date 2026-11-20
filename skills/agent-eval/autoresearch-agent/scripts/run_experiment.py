#!/usr/bin/env python3
"""
autoresearch-agent: Experiment Runner

Executes a single experiment iteration. The AI agent is the loop —
it calls this script repeatedly. The script handles evaluation,
metric parsing, keep/discard decisions, and git rollback on failure.

Usage:
    python scripts/run_experiment.py --experiment engineering/api-speed --single
    python scripts/run_experiment.py --experiment engineering/api-speed --dry-run
    python scripts/run_experiment.py --experiment engineering/api-speed --single --description "added caching"
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from eval_command import parse_eval_command


def find_autoresearch_root():
    """Find .autoresearch/ in project or user home."""
    project_root = Path(".").resolve() / ".autoresearch"
    if project_root.exists():
        return project_root
    user_root = Path.home() / ".autoresearch"
    if user_root.exists():
        return user_root
    return None


def load_config(experiment_dir):
    """Load config.cfg from experiment directory."""
    cfg_file = experiment_dir / "config.cfg"
    if not cfg_file.exists():
        print(f"  Error: no config.cfg in {experiment_dir}")
        sys.exit(1)
    config = {}
    for line in cfg_file.read_text().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            config[k.strip()] = v.strip()
    return config


def run_git(args, cwd=None, timeout=30):
    """Run a git command safely (no shell injection). Returns (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True,
        cwd=cwd, timeout=timeout
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_current_commit(path):
    """Get short hash of current HEAD."""
    _, commit, _ = run_git(["rev-parse", "--short", "HEAD"], cwd=path)
    return commit


def get_best_metric(experiment_dir, direction):
    """Read the best metric from results.tsv."""
    tsv = experiment_dir / "results.tsv"
    if not tsv.exists():
        return None
    lines = [l for l in tsv.read_text().splitlines()[1:] if "\tkeep\t" in l]
    if not lines:
        return None
    metrics = []
    for line in lines:
        parts = line.split("\t")
        try:
            if parts[1] != "N/A":
                metrics.append(float(parts[1]))
        except (ValueError, IndexError):
            continue
    if not metrics:
        return None
    return min(metrics) if direction == "lower" else max(metrics)


def run_evaluation(project_root, eval_cmd, time_budget_minutes, log_file):
    """Run the evaluator directly and save output to the log."""
    hard_limit = time_budget_minutes * 60 * 2.5
    t0 = time.time()
    try:
        with open(log_file, "w") as lf:
            try:
                result = subprocess.run(
                    parse_eval_command(eval_cmd),
                    stdout=lf, stderr=subprocess.STDOUT,
                    cwd=str(project_root),
                    timeout=hard_limit,
                )
            except (OSError, ValueError) as exc:
                print(f"Evaluation command could not start: {exc}", file=lf)
                return 127, time.time() - t0
        elapsed = time.time() - t0
        return result.returncode, elapsed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        return -1, elapsed


def extract_metric(log_file, metric_grep):
    """Extract metric value from log file."""
    log_path = Path(log_file)
    if not log_path.exists():
        return None
    for line in reversed(log_path.read_text().splitlines()):
        stripped = line.strip()
        if stripped.startswith(metric_grep.lstrip("^")):
            try:
                return float(stripped.split(":")[-1].strip())
            except ValueError:
                continue
    return None


def is_improvement(new_val, old_val, direction):
    """Check if new result is better than old."""
    if old_val is None:
        return True
    if direction == "lower":
        return new_val < old_val
    return new_val > old_val


def log_result(experiment_dir, commit, metric_val, status, description):
    """Append result to results.tsv."""
    tsv = experiment_dir / "results.tsv"
    metric_str = f"{metric_val:.6f}" if metric_val is not None else "N/A"
    with open(tsv, "a") as f:
        f.write(f"{commit}\t{metric_str}\t{status}\t{description}\n")


def get_experiment_count(experiment_dir):
    """Count experiments run so far."""
    tsv = experiment_dir / "results.tsv"
    if not tsv.exists():
        return 0
    return max(0, len(tsv.read_text().splitlines()) - 1)


def get_description_from_diff(project_root):
    """Auto-generate a description from git diff --stat HEAD~1."""
    code, diff_stat, _ = run_git(["diff", "--stat", "HEAD~1"], cwd=str(project_root))
    if code == 0 and diff_stat:
        return diff_stat.split("\n")[0][:50]
    return "experiment"


def read_last_lines(filepath, n=5):
    """Read last n lines of a file (replaces tail shell command)."""
    path = Path(filepath)
    if not path.exists():
        return ""
    lines = path.read_text().splitlines()
    return "\n".join(lines[-n:])


def rollback_experiment(project_root, experiment, target, expected_commit, expected_parent):
    """Revert only a verified, single-target experiment commit; never rewrite history."""
    if not expected_commit or not expected_parent:
        return False, "Supply --expected-commit and --expected-parent to authorize rollback"
    root = str(project_root)
    def git(*args):
        return run_git(list(args), cwd=root)
    code, head, _ = git("rev-parse", "--verify", "HEAD")
    if code or head != expected_commit:
        return False, "HEAD does not match the expected full commit SHA"
    code, branch, _ = git("symbolic-ref", "--quiet", "--short", "HEAD")
    if code or branch != f"autoresearch/{experiment}":
        return False, "Current branch is not the experiment branch"
    code, parents, _ = git("rev-list", "--parents", "-n", "1", head)
    if code or parents.split() != [head, expected_parent]:
        return False, "Commit does not have the expected single parent"
    code, status, _ = git("status", "--porcelain", "--untracked-files=no")
    if code or status:
        return False, "Tracked worktree or index is not clean"
    target_path = (project_root / target).resolve()
    try:
        relative = target_path.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return False, "Target is outside the project"
    code, changed, _ = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--no-renames", head)
    if code or changed.splitlines() != [relative]:
        return False, "Commit does not change exactly the configured target"
    code, _, error = git("revert", "--no-edit", head)
    if code:
        return False, f"Git revert failed; inspect repository state: {error}"
    return True, "Created a revert commit"


def run_single(project_root, experiment_dir, config, exp_num, dry_run=False, description=None, experiment=None, expected_commit=None, expected_parent=None):
    """Run one experiment iteration."""
    direction = config.get("metric_direction", "lower")
    metric_grep = config.get("metric_grep", "^metric:")
    eval_cmd = config.get("evaluate_cmd", "python evaluate.py")
    time_budget = int(config.get("time_budget_minutes", 5))
    metric_name = config.get("metric", "metric")
    log_file = str(experiment_dir / "run.log")

    best = get_best_metric(experiment_dir, direction)
    ts = datetime.now().strftime("%H:%M:%S")

    print(f"\n[{ts}] Experiment #{exp_num}")
    print(f"  Best {metric_name}: {best}")

    if dry_run:
        print("  [DRY RUN] Would run evaluation and check metric")
        return "dry_run"

    # Auto-generate description if not provided
    if not description:
        description = get_description_from_diff(str(project_root))

    # Run evaluation
    print(f"  Running: {eval_cmd} (budget: {time_budget}m)")
    ret_code, elapsed = run_evaluation(project_root, eval_cmd, time_budget, log_file)

    commit = get_current_commit(str(project_root))

    def rollback():
        ok, message = rollback_experiment(project_root, experiment, config.get("target", ""), expected_commit, expected_parent)
        print(f"  Rollback: {message}")
        return ok

    # Timeout
    if ret_code == -1:
        print(f"  TIMEOUT after {elapsed:.0f}s — discarding")
        rolled_back = rollback()
        status = "crash" if rolled_back else "rollback_pending"
        log_result(experiment_dir, commit, None, status, f"timeout_{elapsed:.0f}s")
        return status

    # Crash
    if ret_code != 0:
        tail = read_last_lines(log_file, 5)
        print(f"  CRASH (exit {ret_code}) after {elapsed:.0f}s")
        print(f"  Last output: {tail[:200]}")
        rolled_back = rollback()
        status = "crash" if rolled_back else "rollback_pending"
        log_result(experiment_dir, commit, None, status, f"exit_{ret_code}")
        return status

    # Extract metric
    metric_val = extract_metric(log_file, metric_grep)
    if metric_val is None:
        print(f"  Could not parse {metric_name} from run.log")
        rolled_back = rollback()
        status = "crash" if rolled_back else "rollback_pending"
        log_result(experiment_dir, commit, None, status, "metric_parse_failed")
        return status

    delta = ""
    if best is not None:
        diff = metric_val - best
        delta = f" (delta {diff:+.4f})"

    print(f"  {metric_name}: {metric_val:.6f}{delta} in {elapsed:.0f}s")

    # Keep or discard
    if is_improvement(metric_val, best, direction):
        print(f"  KEEP — improvement")
        log_result(experiment_dir, commit, metric_val, "keep", description)
        return "keep"
    else:
        print(f"  DISCARD — no improvement")
        rolled_back = rollback()
        best_str = f"{best:.4f}" if best is not None else "?"
        log_result(experiment_dir, commit, metric_val, "discard" if rolled_back else "rollback_pending",
                   f"no_improvement_{metric_val:.4f}_vs_{best_str}")
        return "discard" if rolled_back else "rollback_pending"


def main():
    parser = argparse.ArgumentParser(description="autoresearch-agent runner")
    parser.add_argument("--experiment", help="Experiment path: domain/name (e.g. engineering/api-speed)")
    parser.add_argument("--single", action="store_true", help="Run one experiment iteration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--description", help="Description of the change (auto-generated from git diff if omitted)")
    parser.add_argument("--path", default=".", help="Project root")
    parser.add_argument("--expected-commit", help="Full SHA of the experiment commit authorized for rollback")
    parser.add_argument("--expected-parent", help="Full SHA of its expected parent")
    args = parser.parse_args()

    project_root = Path(args.path).resolve()
    root = find_autoresearch_root()

    if root is None:
        print("No .autoresearch/ found. Run setup_experiment.py first.")
        sys.exit(1)

    if not args.experiment:
        print("Specify --experiment domain/name")
        sys.exit(1)

    experiment_dir = root / args.experiment
    if not experiment_dir.exists():
        print(f"Experiment not found: {experiment_dir}")
        print("Run: python scripts/setup_experiment.py --list")
        sys.exit(1)

    config = load_config(experiment_dir)

    print(f"\n  autoresearch-agent")
    print(f"  Experiment: {args.experiment}")
    print(f"  Target: {config.get('target', '?')}")
    print(f"  Metric: {config.get('metric', '?')} ({config.get('metric_direction', '?')} is better)")
    print(f"  Budget: {config.get('time_budget_minutes', '?')} min/experiment")
    print(f"  Mode: {'dry-run' if args.dry_run else 'single'}")

    exp_num = get_experiment_count(experiment_dir) + 1
    result = run_single(project_root, experiment_dir, config, exp_num, args.dry_run, args.description,
                        args.experiment, args.expected_commit, args.expected_parent)
    if result == "rollback_pending":
        print("  ROLLBACK PENDING ? stop the loop and review the repository.")
        sys.exit(1)


if __name__ == "__main__":
    main()
