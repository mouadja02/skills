# Trace Schema

The helper accepts one JSON object:

- `kind`: use `w3c_baggage_trace`; another value returns `not_applicable`.
- `received_fields`: non-empty array containing raw field values, without `baggage:`.
- `forwarded_fields`: optional non-empty array captured after extract/inject.
- `declared_mutated_indexes`: optional source-member indexes intentionally changed or deleted by application policy.

Repeated field values are joined with one comma for parsing and combined-limit accounting. Unknown fields, malformed JSON, non-finite JSON constants, and wrong types fail with exit 2. The helper never reads headers from the network and values should be synthetic or redacted.