#!/bin/bash
# Verifier entrypoint template. Replace the assertions; keep the reward discipline.
#
# Contract:
#   - reward defaults to 0 and is promoted to 1 only after every assertion passed;
#   - the reward is written to exactly one channel under /logs/verifier/;
#   - transfer failures, parse failures, and missing output are non-passing;
#   - no network, no writes outside /logs/verifier.
set -uo pipefail

REWARD_DIR="/logs/verifier"
REWARD_FILE="${REWARD_DIR}/reward.txt"
OUTPUT="/app/out/report.json"

mkdir -p "${REWARD_DIR}"
printf '0' > "${REWARD_FILE}"

fail() {
  printf 'verifier: %s\n' "$1" >&2
  printf '0' > "${REWARD_FILE}"
  exit 0
}

# 1. The artifact must exist; an undeclared or missing artifact is a hard zero.
[ -s "${OUTPUT}" ] || fail "missing or empty output at ${OUTPUT}"

# 2. Parse strictly. Malformed output is a zero, not a crash.
python3 - "${OUTPUT}" <<'PY' || fail "output failed schema validation"
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
except (OSError, json.JSONDecodeError) as exc:
    print(f"unreadable: {exc}", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(data, dict):
    print("expected a JSON object", file=sys.stderr)
    raise SystemExit(1)
for key, kind in (("field_a", str), ("field_b", int)):
    if key not in data or not isinstance(data[key], kind):
        print(f"missing or mistyped field {key}", file=sys.stderr)
        raise SystemExit(1)
PY

# 3. Semantic assertions against the trusted expectation. Replace with real checks.
python3 - "${OUTPUT}" <<'PY' || fail "semantic assertions failed"
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
expected = {"field_a": "example", "field_b": 0}
problems = [k for k, v in expected.items() if data.get(k) != v]
if problems:
    print(f"mismatched fields: {problems}", file=sys.stderr)
    raise SystemExit(1)
PY

printf '1' > "${REWARD_FILE}"
exit 0
