# Evaluation prompts and assertions

Use the same synthetic packets for baseline and with-skill behavior.

## Normal

**Prompt:** Preflight this synthetic CRD storage-version upgrade packet before retiring `v1alpha1`; classify readiness and identify blockers.

**Assertions:** `status=pass`, no findings, and `mutation_permitted=false`.

## Difficult edge

**Prompt:** A CRD conversion webhook is unavailable, round-trip conversion loses a field, migration is incomplete, and the old version is marked unserved; find every evidenced blocker and recovery boundary.

**Assertions:** `status=fail`; findings include `WEBHOOK_ENDPOINTS_UNREADY`, `WEBHOOK_CA_INVALID`, `ROUND_TRIP_DATA_LOSS`, `REWRITE_INCOMPLETE`, `OLD_VERSION_STILL_STORED`, `OLD_VERSION_UNSERVED_TOO_EARLY`, `BACKUP_UNVERIFIED`, and `ROLLBACK_UNDOCUMENTED`; mutation remains forbidden.

## Should not activate

**Prompt:** Review this built-in Kubernetes API upgrade packet.

**Assertions:** `status=not_applicable`, no findings, and no mutation permission.
