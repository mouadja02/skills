---
name: geofeed-tuner
description: >
  Use this skill whenever the user mentions IP geolocation feeds, RFC 8805, geofeeds, or wants help creating, tuning, validating, or publishing a
  self-published IP geolocation feed in CSV format. Intended user audience is a network
  operator, ISP, mobile carrier, cloud provider, hosting company, IXP, or satellite provider
  asking about IP geolocation accuracy, or geofeed authoring best practices.
  Helps create, refine, and improve CSV-format IP geolocation feeds with opinionated
  recommendations beyond RFC 8805 compliance. Do NOT use for private or internal IP address
  management — applies only to publicly routable IP addresses.
license: Apache-2.0
metadata:
  author: Sid Mathur <support@getfastah.com>
  version: "0.0.10"
compatibility: Requires Python 3
source: "https://github.com/github/awesome-copilot"
attribution: "github/awesome-copilot by GitHub Community"
---

> **Attribution:** Sourced from [github/awesome-copilot](https://github.com/github/awesome-copilot) by [GitHub Community](https://github.com/github), licensed Apache-2.0. Modified for this collection: Phases 3 to 5 were moved unchanged into `references/`, and an unclosed code fence in the Phase 4 example was closed.

# Geofeed Tuner – Create Better IP Geolocation Feeds

This skill helps you create and improve IP geolocation feeds in CSV format by:
- Ensuring your CSV is well-formed and consistent
- Checking alignment with [RFC 8805](references/rfc8805.txt) (the industry standard)
- Applying **opinionated best practices** learned from real-world deployments
- Suggesting improvements for accuracy, completeness, and privacy

## When to Use This Skill

- Use this skill when a user asks for help **creating, improving, or publishing** an IP geolocation feed file in CSV format.
- Use it to **tune and troubleshoot CSV geolocation feeds** — catching errors, suggesting improvements, and ensuring real-world usability beyond RFC compliance.
- **Intended audience:**
  - Network operators, administrators, and engineers responsible for publicly routable IP address space
  - Organizations such as ISPs, mobile carriers, cloud providers, hosting and colocation companies, Internet Exchange operators, and satellite internet providers
- **Do not use** this skill for private or internal IP address management; it applies **only to publicly routable IP addresses**.

## Prerequisites

- **Python 3** is required.

## Directory Structure and File Management

This skill uses a clear separation between **distribution files** (read-only) and **working files** (generated at runtime).

### Read-Only Directories (Do Not Modify)

The following directories contain static distribution assets. **Do not create, modify, or delete files in these directories:**

| Directory      | Purpose                                                    |
|----------------|------------------------------------------------------------|
| `assets/`      | Static data files (ISO codes, examples)                    |
| `references/`  | RFC specifications and code snippets for reference         |
| `scripts/`     | Executable code and HTML template files for reports        |

### Working Directories (Generated Content)

All generated, temporary, and output files go in these directories:

| Directory       | Purpose                                              |
|-----------------|------------------------------------------------------|
| `run/`          | Working directory for all agent-generated content    |
| `run/data/`     | Downloaded CSV files from remote URLs                |
| `run/report/`   | Generated HTML tuning reports                        |

### File Management Rules

1. **Never write to `assets/`, `references/`, or `scripts/`** — these are part of the skill distribution and must remain unchanged.
2. **All downloaded input files** (from remote URLs) must be saved to `./run/data/`.
3. **All generated HTML reports** must be saved to `./run/report/`.
4. **All generated Python scripts** must be saved to `./run/`.
5. The `run/` directory may be cleared between sessions; do not store permanent data there.
6. **Working directory for execution:** All generated scripts in `./run/` must be executed with the **skill root directory** (the directory containing `SKILL.md`) as the current working directory, so that relative paths like `assets/iso3166-1.json` and `./run/data/report-data.json` resolve correctly. Do not `cd` into `./run/` before running scripts.

## Processing Pipeline: Sequential Phase Execution

All phases must be executed **in order**, from Phase 1 through Phase 6. Each phase depends on the successful completion of the previous phase. For example, **structure checks** must complete before **quality analysis** can run.

The phases are summarized below. The agent must follow the detailed steps outlined further in each phase section.

| Phase | Name                       | Description                                                                       |
|-------|----------------------------|-----------------------------------------------------------------------------------|
| 1     | Understand the Standard    | Review the key requirements of RFC 8805 for self-published IP geolocation feeds   |
| 2     | Gather Input               | Collect IP subnet data from local files or remote URLs                            |
| 3     | Checks & Suggestions       | Validate CSV structure, analyze IP prefixes, and check data quality               |
| 4     | Tuning Data Lookup         | Use Fastah's MCP tool to retrieve tuning data for improving geolocation accuracy  |
| 5     | Generate Tuning Report     | Create an HTML report summarizing the analysis and suggestions                    |
| 6     | Final Review               | Verify consistency and completeness of the report data                            |

**Do not skip phases.** Each phase provides critical checks or data transformations required by subsequent stages.

### Execution Plan Rules

Before executing each phase, the agent MUST generate a visible TODO checklist.

The plan MUST:
- Appear at the very start of the phase
- List every step in order
- Use a checkbox format
- Be updated live as steps complete

### Phase 1: Understand the Standard

The key requirements from RFC 8805 that this skill enforces are summarized below. **Use this summary as your working reference.** Only consult the full [RFC 8805 text](references/rfc8805.txt) for edge cases, ambiguous situations, or when the user asks a standards question not covered here.

#### RFC 8805 Key Facts

**Purpose:** A self-published IP geolocation feed lets network operators publish authoritative location data for their IP address space in a simple CSV format, allowing geolocation providers to incorporate operator-supplied corrections.

**CSV Column Order (Sections 2.1.1.1–2.1.1.5):**

| Column | Field         | Required | Notes                                                      |
|--------|---------------|----------|------------------------------------------------------------|
| 1      | `ip_prefix`   | Yes      | CIDR notation; IPv4 or IPv6; must be a network address     |
| 2      | `alpha2code`  | No       | ISO 3166-1 alpha-2 country code; empty or "ZZ" = do-not-geolocate |
| 3      | `region`      | No       | ISO 3166-2 subdivision code (e.g., `US-CA`)               |
| 4      | `city`        | No       | Free-text city name; no authoritative validation set       |
| 5      | `postal_code` | No       | **Deprecated** — must be left empty or absent             |

**Structural rules:**
- Files may contain comment lines beginning with `#` (including the header, if present).
- A header row is optional; if present, it is treated as a comment if it starts with `#`.
- Files must be encoded in UTF-8.
- Subnet host bits must not be set (i.e., `192.168.1.1/24` is invalid; use `192.168.1.0/24`).
- Applies only to **globally routable** unicast addresses — not private, loopback, link-local, or multicast space.

**Do-not-geolocate:** An entry with an empty `alpha2code` or case-insensitive `ZZ` (irrespective of values of region/city) is an explicit signal that the operator does not want geolocation applied to that prefix.

**Postal codes deprecated (Section 2.1.1.5):** The fifth column must not contain postal or ZIP codes. They are too fine-grained for IP-range mapping and raise privacy concerns.

### Phase 2: Gather Input

- If the user has not already provided a list of IP subnets or ranges (sometimes referred to as `inetnum` or `inet6num`), prompt them to supply it. Accepted input formats:
  - Text pasted into the chat
  - A local CSV file
  - A remote URL pointing to a CSV file

- If the input is a **remote URL**:
  - Attempt to download the CSV file to `./run/data/` before processing.
  - On HTTP error (4xx, 5xx, timeout, or redirect loop), **stop immediately** and report to the user:
    `Feed URL is not reachable: HTTP {status_code}. Please verify the URL is publicly accessible.`
  - Do not proceed to Phase 3 with an incomplete or empty download.

- If the input is a **local file**, process it directly without downloading.

- **Encoding detection and normalization:**
  1. Attempt to read the file as UTF-8 first.
  2. If a `UnicodeDecodeError` is raised, try `utf-8-sig` (UTF-8 with BOM), then `latin-1`.
  3. Once successfully decoded, re-encode and write the working copy as UTF-8.
  4. If no encoding succeeds, stop and report: `Unable to decode input file. Please save it as UTF-8 and try again.`

### Phase 3: Checks & Suggestions

Write a script that validates the CSV structure, analyzes IP prefixes, and checks country, region, city, and postal-code quality, then stores the result in `./run/data/report-data.json` using a fixed schema. Read [`references/phase3-checks.md`](references/phase3-checks.md) at the start of this phase. It holds the immutable JSON schema, the validation rules, message wording, accuracy-level counting, and the tuning recommendations.

### Phase 4: Tuning Data Lookup

Look up every entry with Fastah's `rfc8805-row-place-search` MCP tool (deduplicated, at most 1000 entries per request), then attach the best match to each entry as `TunedEntry`. If the MCP server fails, warn, set `TunedEntry: {}`, and continue to Phase 5. Suggestions are advisory only. Read [`references/phase4-tuning-lookup.md`](references/phase4-tuning-lookup.md) for the payload, invocation, and attachment steps.

### Phase 5: Generate Tuning Report

Render `./scripts/templates/index.html` (Go `html/template` syntax) with a Python script, using `./run/data/report-data.json` and `./run/data/comments.json`, into the self-contained `./run/report/geofeed-report.html`. Read [`references/phase5-report.md`](references/phase5-report.md) for the placeholder-by-placeholder rendering steps and output guarantees.

### Phase 6: Final Review

Perform a final verification pass using concrete, checkable assertions before presenting results to the user.

**Check 1 — Entry count integrity**
- Count non-comment, non-blank data rows in the original input CSV.
- Assert: `len(entries) in report-data.json == data_row_count`
- On failure: `Row count mismatch: input has {N} data rows but report contains {M} entries.`

**Check 2 — Summary counter integrity**
- These counters use **mutual exclusion** based on the boolean flags, which mirrors the highest-severity `Status` field. An entry with both `HasError: true` and `HasWarning: true` is counted only in `Errors`, never in `Warnings`. This is equivalent to counting by the entry's `Status` field.
- Assert all of the following; correct any that fail before generating the report:
  - `Errors == sum(1 for e in Entries if e['HasError'])`
  - `Warnings == sum(1 for e in Entries if e['HasWarning'] and not e['HasError'])`
  - `Suggestions == sum(1 for e in Entries if e['HasSuggestion'] and not e['HasError'] and not e['HasWarning'])`
  - `OK == sum(1 for e in Entries if not e['HasError'] and not e['HasWarning'] and not e['HasSuggestion'])`
  - `Errors + Warnings + Suggestions + OK == TotalEntries - InvalidEntries`

**Check 3 — Accuracy bucket integrity**
- Assert: `CityLevelAccuracy + RegionLevelAccuracy + CountryLevelAccuracy + DoNotGeolocate == TotalEntries - InvalidEntries`
- **Note:** The accuracy buckets defined in Phase 3 say "Do not count entries with `HasError: true`", but the Check 3 formula above uses `TotalEntries - InvalidEntries` (which still includes ERROR entries). This means ERROR entries (those that parsed as valid IPs but failed validation) **are** counted in accuracy buckets by their geo-field presence. Only `InvalidEntries` (unparsable IP prefixes) are excluded. Follow the Check 3 formula as the authoritative rule.
- On failure, trace and fix the bucketing logic before proceeding.

**Check 4 — No duplicate line numbers**
- Assert: all `Line` values in `Entries` are unique.
- On failure, report the duplicated line numbers to the user.

**Check 5 — TunedEntry completeness**
- Assert: every object in `Entries` has a `TunedEntry` key (even if its value is `{}`).
- On failure, add `"TunedEntry": {}` to any entry missing the key, then re-save `report-data.json`.

**Check 6 — Report file is present and non-empty**
- Confirm `./run/report/geofeed-report.html` was written and has a file size greater than zero bytes.
- On failure, regenerate the report before presenting to the user.
