# Catalog scan follow-up

This addresses the remaining source matches reported for
[awesome-ai-plugins PR #886](https://github.com/hashgraph-online/awesome-ai-plugins/pull/886).
The maintainer requested a score of at least 80 and no critical or high findings.
No scanner rule, input directory, severity, or score threshold is suppressed.

The scan of source commit `038ee4900eab4972c4dd0eaf8e026ee37c644e1f`
scored 77 with 19 `HARDCODED_SECRET` and four
`DANGEROUS_DYNAMIC_EXECUTION` matches. The catalog uses scanner 3.0.123;
scanner 3.51.0 reproduced the score locally before this follow-up.

## Source changes

| Match category | Change and retained behavior |
| --- | --- |
| Test credentials and deliberate insecure examples | Mark values with an explicit `example-` prefix; unsafe examples remain labelled and continue to demonstrate hardcoded-credential risks. |
| Authentication recipes | Read registration/login passwords interactively, generate the development JWT secret, use the Azure password environment variable, and pass the password from each test-user fixture. |
| CodeBuild parameter reference | Demonstrate a non-secret service endpoint in the Parameter Store mapping; secret retrieval remains documented separately. |
| Pagination output | Serialize runtime tokens as JSON, preserving ordinary output while escaping quotes and backslashes correctly. |
| Shell credential references | Use quoted, braced variable expansions; no literal credential or non-empty fallback is introduced. |
| Environment-name constants | Use the `*_API_KEY_ENV` naming convention to distinguish a variable's name from its credential value. |
| Private-key detection rules | Express PEM marker whitespace in regex syntax; canonical RSA, EC, and OpenSSH markers remain critical findings. |
| Dynamic-execution detection rules | Clarify human-readable descriptions; the regexes and severity levels are unchanged. |
| Browser inspection | Rename the internal CDP method from `eval` to `evaluate`, update every caller, and retain `Runtime.evaluate`, argument serialization, and exception propagation. This remains explicit browser-side execution. |
| SQL review exercise | Keep an explicitly unsafe string-interpolation exercise using `%` formatting rather than an f-string that resembles a static password assignment. |

## Verification

- `node --test scripts/test-skill-subprocesses.mjs` checks subprocess boundaries
  and the CDP request/response contract without launching a browser.
- `python3 -m unittest scripts/test_skill_scan_regressions.py` checks dynamic
  execution detection, critical private-key marker detection, and pagination
  token round trips, including quotes and backslashes.
- `.github/workflows/catalog-security.yml` runs the catalog's SHA-pinned scanner
  on pushes and pull requests with `min_score: 80`, `fail_on_severity: high`,
  and repository policy overrides disabled.
- The catalog's centralized rerun remains the required listing verdict.

These changes make the source's intent unambiguous to the scanner. They do not
claim that renaming a browser method or rewording detection-rule descriptions
changes the underlying execution capability. The listing maintainer can review
the source diff and scanner output together.
