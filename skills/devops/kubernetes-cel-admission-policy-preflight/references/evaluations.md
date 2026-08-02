# Evaluation prompts and assertions

Use redacted synthetic packets only. These prompts exercise classification behavior; they do not authorize cluster mutation.

## Normal

> Preflight this native ValidatingAdmissionPolicy evidence packet before canary rollout; classify readiness and explain any blockers.

Input: a pinned Kubernetes/CEL environment, CREATE and UPDATE fixtures including user and missing-parameter behavior, static/runtime cost evidence, a bounded resource observation, acyclic bootstrap dependencies, and an observed Warn canary.

**Assertions:** exit `0`; `status=pass`; no finding codes; `mutation_permitted=false`.

## Difficult edge

> A fail-closed Deny binding is planned for DELETE and depends on its own controller startup path; find every evidenced safety and coverage gap.

Input: unpinned CEL environment, no DELETE/oldObject/userInfo/missing-param/error fixtures, no cost evidence, excess memory per pair, a policy-node cycle, and Deny without canary or rollback.

**Assertions:** exit `1`; `status=fail`; findings include `CEL_ENVIRONMENT_UNPINNED`, `OPERATION_UNTESTED`, `DELETE_OLD_OBJECT_UNTESTED`, `USER_INFO_UNTESTED`, `PARAMS_ABSENCE_UNTESTED`, `FAILURE_POLICY_UNTESTED`, `STATIC_COST_UNCHECKED`, `RUNTIME_COST_UNOBSERVED`, `RESOURCE_BUDGET_EXCEEDED`, `BOOTSTRAP_DEPENDENCY_CYCLE`, `DENY_WITHOUT_CANARY`, and `ROLLBACK_UNDOCUMENTED`.

## Should not activate

> Analyze this Kyverno-native policy packet.

Input: `target_type=kyverno_policy` with inventory metadata only.

**Assertions:** exit `0`; `status=not_applicable`; no findings; reason says this checker is limited to native Kubernetes `ValidatingAdmissionPolicy` packets.
