# Evidence and scope

Accessed 2026-09-01.

## Canonical behavior

- RFC 9110 defines byte range requests, 206 Partial Content, Content-Range, 416, strong validators, and If-Range. The helper operationalizes a conservative append boundary; it does not reproduce specification text.

## Demonstrated problems

- Hugging Face Hub issues 4060, 4196, and 3007 report corruption recovery, restart, and unsafe cached-partial concerns.
- rclone issue 6980 reports missing Content-Range validation.
- uv issue 16934 and GitHub CLI issue 13919 request resumable downloads after expensive restarts.
- ModelScope Hub issue 50 reports a ranged 200 response carrying a partial Content-Range, which can corrupt restart/append decisions.

## Licensing

The workflow, helper, tests, and fixtures are original MIT-licensed work synthesized from factual evidence. Hugging Face Hub, uv, and ModelScope Hub are Apache-2.0; rclone and GitHub CLI are MIT. No source code or issue prose is copied.

## Limits

The helper validates one redacted response transcript. It does not perform HTTP requests, persist checkpoint data, hash files, follow redirects, or prove a server implementation correct. Final integrity still requires an independently obtained digest.
