# Design checklist

## Claim and scope

- Cite the primary incident source and preserve its exact claim.
- Separate observed harm, proposed cause, assumptions, and unknowns.
- Exclude secrets, personal data, production identifiers, and exploit details.
- State which deployment decision the experiment can change.

## Matched worlds

- Build both worlds from one frozen fixture.
- Remove only the suspected hazard in the control.
- Keep names, task, permissions, data volume, timing, and tool interfaces fixed.
- Review every leaf-level difference, including generated IDs and timestamps.
- Hash fixtures and reset images.

## Reachability and oracle

- Prove the incident path reaches harm with a deterministic policy.
- Prove the same policy remains safe in the no-hazard control.
- Derive harm from final state, not transcript wording.
- Test the oracle against known-harm and known-safe states.
- Fail closed on unreadable or ambiguous state.

## Intervention isolation

| Condition | Changes text | Changes authority/world | Purpose |
| --- | --- | --- | --- |
| Baseline | no | no | Original behavior |
| Equal-length neutral | yes | no | Placement/attention control |
| Fact-only | yes | no | Fact without consequence |
| Hazard plus consequence | yes | no | Informative warning |
| Structural remediation | optional | yes | Eliminate or block hazard |

Do not compare a warning against a control that also changes permissions, resource names, or tool visibility.

## Trial protocol

- Freeze agent/model/tool versions and decoding.
- Randomize order; isolate sessions; reset and verify before each run.
- Predeclare repetitions, exclusions, stopping rules, and analysis.
- Account for completed, failed, timed-out, contaminated, and censored runs.
- Record token, tool, latency, and infrastructure costs.

## Decision

- Report paired effects and uncertainty, not only aggregate percentages.
- Check whether reduced harm is blanket refusal.
- Prefer effective structural remediation over warning-only deployment.
- State generalization limits and rollback triggers.
