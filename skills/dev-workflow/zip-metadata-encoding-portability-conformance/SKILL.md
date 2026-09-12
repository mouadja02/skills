---
name: zip-metadata-encoding-portability-conformance
description: Use when ZIP member names or comments become mojibake, differ across Python/.NET/Go/archive tools, lose UTF-8 flags after rewrites, or need pre-extraction EFS and Unicode extra-field verification.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
---

# ZIP Metadata Encoding Portability Conformance

Inspect ZIP header bytes before extraction. Keep format validity, runtime decoding policy, and a guessed legacy code page separate.

## When to Use

- A ZIP filename or per-entry comment is mojibake, replaced, or decoded differently across runtimes.
- A rewrite or append operation may have changed EFS (general-purpose bit 11).
- Local and central headers, or Info-ZIP Unicode Path/Comment fields, may disagree.
- A migration needs an evidence report before choosing a legacy decoding policy.

Do **not** activate for ordinary UTF-8 files that are not ZIP members, archive content corruption, compression-ratio analysis, or TAR metadata.

## Prerequisites

- Python 3.9+ for the offline inspector.
- Read access to a bounded, non-multipart ZIP. The helper refuses ZIP64 and archives larger than 64 MiB; use a reviewed ZIP64-aware parser for those cases.
- A separately documented consumer profile if unflagged bytes are known to use a legacy encoding other than CP437. Do not infer one from locale or visual plausibility.

## Quick Reference

```bash
python3 scripts/inspect_zip_metadata.py archive.zip
python3 scripts/inspect_zip_metadata.py archive.zip --output report.json
python3 tests/test_inspect_zip_metadata.py
```

Exit codes: `0` conforming, `1` inspected with violations, `2` input/format failure or unsupported archive, `3` report write failure. The helper never extracts members or reads compressed payloads.

## Procedure

### 1. Preserve and bound the evidence

Work on a copy when a production system may rewrite the archive. Record its digest, size, producer, consumer, runtime versions, and whether append/update mode was used. Do not “repair” bytes before capturing the failing artifact.

### 2. Inspect metadata without extraction

Run the helper and retain the JSON. It:

1. locates and bounds the end-of-central-directory and central directory;
2. parses every central entry and its referenced local header;
3. compares raw name bytes and EFS independently;
4. decodes EFS names/comments as strict UTF-8 and unflagged names as CP437 for the format baseline;
5. validates `0x7075` Unicode Path and `0x6375` Unicode Comment version, UTF-8 payload, uniqueness, and CRC-32 binding to the legacy bytes;
6. reports unsafe path forms without extracting.

A successful parser run is not permission to extract. `safe_to_extract` is only this skill's metadata gate; still apply traversal, size, link, encryption, and decompression-resource policy in the actual extractor.

### 3. Classify the failure

- `efs-flag-mismatch`: local and central headers declare different encodings. Treat rewriting or append behavior as suspect.
- `local-central-name-mismatch`: the two headers identify different raw member names. Do not select one silently.
- `invalid-utf8-*`: EFS is set but the governed bytes are not valid UTF-8.
- `unicode-*-crc-mismatch`: an Info-ZIP Unicode field is stale and must not override its bound legacy bytes.
- `unicode-*-conflict`: a valid Unicode field disagrees with an EFS-governed UTF-8 value.
- `ambiguous-unflagged-utf8`: an observation, not a violation. Valid UTF-8 bytes without EFS do not prove producer intent; CP437 remains the format baseline while real tools may apply another policy.

### 4. Compare consumers explicitly

Test the same immutable bytes with each real consumer. Record raw-name access, EFS exposure, configured fallback encoding, decoded name/comment, Unicode-extra behavior, and rewrite stability. Label these as **observed runtime policy**, not format validity.

Never silently choose Windows-1252, CP850, Shift-JIS, or another code page because one filename “looks right.” Require producer documentation, a controlled corpus, or user-approved policy. Keep archive comments separate from per-entry comments.

### 5. Recover without destroying evidence

Prefer regenerating from the source filenames with EFS and UTF-8 for both member names and per-entry comments. If a legacy archive must be migrated:

1. approve one explicit source encoding;
2. decode raw names in an isolated workspace;
3. reject NUL, controls, absolute paths, traversal, separators introduced by decoding, and collisions after normalization;
4. write a new archive rather than editing headers in place;
5. inspect the new archive and test every target consumer;
6. compare member counts and content digests using a separate safe extraction pipeline.

Rollback is the original immutable archive plus the recorded decoding policy. Never overwrite the only copy.

## Objective Verification

Completion requires all of the following:

- every central entry references a valid local header;
- local/central raw names and EFS agree;
- all EFS-governed names and comments decode as strict UTF-8;
- each Unicode extra field is structurally valid and CRC-bound to the exact legacy bytes;
- no unsafe decoded path or duplicate decoded name is present;
- the selected producer/consumer matrix reproduces the expected names without metadata mutation;
- safe and intentionally invalid synthetic fixtures produce the expected exit codes and finding codes.

## Pitfalls and Safety

- EFS governs both the filename and per-entry comment, not the archive-level EOCD comment.
- Same-origin or same-runtime success does not establish cross-runtime portability.
- A valid `0x7075` value with a bad CRC is stale evidence, not an authoritative name.
- Local and central extra fields must be parsed separately; matching decoded text cannot excuse byte or flag disagreement.
- Never extract researched, emailed, or production archives during diagnosis. This helper intentionally does not support repair.

## Evaluation Prompts

1. **Normal:** Inspect a synthetic ZIP whose local and central names are identical UTF-8, both EFS flags are set, and no Unicode extra exists; return a machine-readable conformance report.
2. **Difficult:** Inspect a synthetic ZIP with different local/central raw names, mismatched EFS, invalid UTF-8 name/comment, and a stale `0x7075` CRC; identify each independent failure without extraction.
3. **Should not activate:** A standalone UTF-8 text file named `café.txt` displays correctly and is not archived; decide whether ZIP metadata inspection applies.

## Sources and Fact/Policy Boundary

**Sourced facts:** PKWARE APPNOTE 6.3.10 defines EFS bit 11 for UTF-8 filename and comment fields and documents Info-ZIP Unicode Path/Comment fields. Python, .NET, Go, and libarchive records demonstrate divergent or changing behavior around flags and unflagged bytes.

**Recommendations:** size caps, fail-closed handling, immutable evidence, explicit code-page approval, and the recovery sequence are conservative operational policy authored for this skill.

- [PKWARE APPNOTE 6.3.10](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT)
- [CPython issue 152845: EFS loss with UTF-8 comments and append rewrites](https://github.com/python/cpython/issues/152845)
- [.NET runtime issue 92283: EFS decoding regression](https://github.com/dotnet/runtime/issues/92283)
- [.NET runtime issue 43231: exposing EFS for entry decoding](https://github.com/dotnet/runtime/issues/43231)
- [libarchive issue 1281: UTF-8 bytes without EFS](https://github.com/libarchive/libarchive/issues/1281)
- [Go issue 67878: non-ASCII filename investigation](https://github.com/golang/go/issues/67878)
- [Python `zipfile` documentation](https://docs.python.org/3/library/zipfile.html)
- [Go `archive/zip` documentation](https://pkg.go.dev/archive/zip)
