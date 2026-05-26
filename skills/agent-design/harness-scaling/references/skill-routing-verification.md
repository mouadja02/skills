# Skill Routing & Verification

From arXiv:2605.26112v1 — Shangding Gu, UC Berkeley, May 2026.

The failure mode is **confident-but-unchecked**: specialized subagents return plausible, fluent outputs without downstream validation, and the orchestrator accepts them as correct. Scaling skill breadth without scaling verification produces faster but less reliable agents.

---

## The Core Problem: Confident but Unchecked

```
Agent pipeline:
  Orchestrator → calls SpecialistAgent("refactor this function")
  SpecialistAgent → returns refactored code (looks correct, compiles)
  Orchestrator → writes code to file, marks task done

What was NOT checked:
  - Does the refactored code have the same behavior?
  - Do existing tests still pass?
  - Were all call sites updated?
  - Was the original backed up?

The agent completed the task with HIGH CONFIDENCE.
The code is SILENTLY WRONG.
```

**Key insight from the paper:** Fluent output ≠ correct output. Post-condition verification must be a first-class component of every skill specification, not an afterthought.

---

## Skill Specification Standard

Every skill must be specified with:
1. **Capability scope** — exactly what it can do
2. **Input contract** — what it expects
3. **Output contract** — what it produces
4. **Post-conditions** — mandatory checks after execution
5. **Confidence threshold** — minimum routing confidence
6. **Escalation target** — what to use when confidence is too low

```python
from dataclasses import dataclass, field
from typing import Callable, Optional, Any

@dataclass
class SkillSpec:
    # Identity
    name: str
    description: str
    version: str

    # Capability scope — precise and bounded
    # State what the skill CAN do, and equally important, what it CANNOT
    can_do: list[str]
    cannot_do: list[str]

    # Contracts
    input_schema: dict   # JSON Schema
    output_schema: dict  # JSON Schema

    # Post-condition checkers
    # Each function takes (original_task, result) and returns bool
    postconditions: list[Callable[[Any, Any], bool]] = field(default_factory=list)

    # Routing
    min_confidence: float = 0.75
    escalation_skill: Optional[str] = None  # Used when confidence < min_confidence

    # Composition metadata
    output_format: str = "json"  # What downstream consumers expect
    expected_latency_ms: int = 5000


# Example: Code refactoring skill with verification
refactor_skill = SkillSpec(
    name="code_refactor",
    description="Refactors a Python function while preserving behavior",
    version="1.0.0",
    can_do=["rename variables", "extract helper functions", "simplify logic"],
    cannot_do=["change function signature", "add new features", "modify tests"],
    input_schema={
        "source_code": {"type": "string"},
        "refactor_instructions": {"type": "string"},
        "test_suite_path": {"type": "string"}
    },
    output_schema={
        "refactored_code": {"type": "string"},
        "changes_summary": {"type": "string"},
        "tests_passed": {"type": "boolean"}
    },
    postconditions=[
        # Post-condition 1: Output is syntactically valid Python
        lambda task, result: is_valid_python(result["refactored_code"]),
        # Post-condition 2: Tests still pass after refactor
        lambda task, result: result.get("tests_passed", False),
        # Post-condition 3: Function signature unchanged
        lambda task, result: same_signature(task["source_code"], result["refactored_code"]),
    ],
    min_confidence=0.80,
    escalation_skill="human_review",
)
```

---

## Adaptive Routing Policy

Route to the most appropriate skill based on real-time task classification. When confidence is insufficient, escalate rather than guess.

```python
from enum import Enum
import logging

class EscalationLevel(Enum):
    SKILL_FALLBACK = 1  # Use a more general skill
    MORE_CAPABLE_MODEL = 2  # Same skill, stronger ℛ model
    HUMAN_REVIEW = 3  # Surface to human before proceeding

class SkillRouter:
    def __init__(self, registry: dict[str, SkillSpec]):
        self.registry = registry
        self.routing_log: list[dict] = []

    async def route(
        self,
        task: SubTask,
        escalation_budget: int = 2  # Max escalation attempts
    ) -> tuple[Any, SkillSpec]:
        """
        Route task to skill with confidence-aware escalation.
        Returns (result, skill_used).
        """
        task_type, confidence = self.classify_task(task)
        skill = self.registry.get(task_type)

        if skill is None:
            skill = self.registry["general_purpose"]
            confidence = 0.5  # Low confidence for fallback

        attempt = 0
        while attempt <= escalation_budget:
            if confidence < skill.min_confidence:
                skill, confidence = self._escalate(skill, confidence, task)

            result = await self._execute_with_postconditions(task, skill)

            if result.postconditions_passed:
                self._log_routing(task, skill, confidence, success=True)
                return result.value, skill

            # Post-conditions failed — escalate
            logging.warning(
                f"Skill {skill.name} failed post-conditions for task {task.id}. "
                f"Escalating (attempt {attempt+1}/{escalation_budget})."
            )
            skill, confidence = self._escalate(skill, 0.0, task)
            attempt += 1

        raise SkillRoutingError(
            f"Failed to route task {task.id} after {escalation_budget} escalations"
        )

    def _escalate(
        self, skill: SkillSpec, confidence: float, task: SubTask
    ) -> tuple[SkillSpec, float]:
        """Escalate to more capable skill/model."""
        if skill.escalation_skill and skill.escalation_skill in self.registry:
            return self.registry[skill.escalation_skill], 0.9
        elif confidence < 0.5:
            # Very low confidence — route to most capable general skill
            return self.registry["general_purpose_strong"], 0.9
        else:
            return skill, confidence  # No escalation available

    async def _execute_with_postconditions(
        self, task: SubTask, skill: SkillSpec
    ) -> ExecutionResult:
        result_value = await skill.execute(task)

        # Run all post-conditions
        passed = []
        failed = []
        for i, postcond in enumerate(skill.postconditions):
            try:
                ok = postcond(task, result_value)
                (passed if ok else failed).append(i)
            except Exception as e:
                failed.append(i)
                logging.error(f"Post-condition {i} raised exception: {e}")

        return ExecutionResult(
            value=result_value,
            postconditions_passed=len(failed) == 0,
            failed_postconditions=failed,
        )
```

---

## Post-Condition Design Patterns

### Pattern 1: State-Change Verification

For skills that modify external state (file system, database, API):

```python
async def verified_file_write(file_path: str, content: str) -> bool:
    """Write a file and verify the write succeeded."""
    # Execute
    with open(file_path, "w") as f:
        f.write(content)

    # Post-condition: verify the file now contains the expected content
    with open(file_path, "r") as f:
        actual = f.read()

    if actual != content:
        raise PostConditionError(
            f"File write verification failed: expected {len(content)} chars, "
            f"got {len(actual)} chars"
        )
    return True
```

### Pattern 2: Semantic Equivalence Check

For code transformation skills:

```python
def semantic_equivalence_postcondition(original: str, transformed: str) -> bool:
    """
    Verify transformed code is semantically equivalent to original.
    Uses test suite execution as proxy for semantic equivalence.
    """
    import subprocess
    import tempfile

    # Write transformed code to temp file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as f:
        f.write(transformed)
        temp_path = f.name

    # Run tests against transformed code
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", temp_path],
        capture_output=True, timeout=60
    )
    return result.returncode == 0
```

### Pattern 3: Consistency Check for Multi-Step Pipelines

For chained skill invocations:

```python
class PipelineVerifier:
    """
    Verifies that outputs from upstream skills are consistent
    with inputs expected by downstream skills.
    """

    def verify_handoff(
        self,
        upstream_output: Any,
        upstream_skill: SkillSpec,
        downstream_skill: SkillSpec
    ) -> bool:
        """Verify upstream output matches downstream input schema."""
        from jsonschema import validate, ValidationError

        try:
            validate(instance=upstream_output, schema=downstream_skill.input_schema)
            return True
        except ValidationError as e:
            logging.error(
                f"Handoff verification failed between {upstream_skill.name} → "
                f"{downstream_skill.name}: {e.message}"
            )
            return False
```

---

## Mixture-Style Skill Composition

For complex tasks requiring multiple skills, use composition with intermediate verification:

```python
class SkillCompositionPipeline:
    """
    Execute a sequence of skills with verification at each step.
    Stops on verification failure rather than propagating errors.
    """

    def __init__(self, skills: list[SkillSpec], router: SkillRouter):
        self.skills = skills
        self.router = router
        self.verifier = PipelineVerifier()

    async def execute(self, initial_task: SubTask) -> CompositionResult:
        results = []
        current_input = initial_task.input
        pipeline_verifier = PipelineVerifier()

        for i, skill in enumerate(self.skills):
            # Wrap input as subtask for this skill
            subtask = SubTask(
                id=f"{initial_task.id}_step_{i}",
                input=current_input,
                skill_hint=skill.name
            )

            result, used_skill = await self.router.route(subtask)

            # Verify handoff to next skill (if there is a next)
            if i < len(self.skills) - 1:
                next_skill = self.skills[i + 1]
                if not pipeline_verifier.verify_handoff(result, used_skill, next_skill):
                    return CompositionResult(
                        success=False,
                        failed_at_step=i,
                        results=results,
                        error=f"Handoff verification failed at step {i} → {i+1}"
                    )

            results.append(StepResult(step=i, skill=used_skill.name, output=result))
            current_input = result  # Output becomes next input

        return CompositionResult(success=True, results=results, final_output=results[-1].output)
```

---

## Routing Decision Audit Log

Every routing decision should be logged for auditability:

```python
@dataclass
class RoutingDecision:
    timestamp: datetime
    task_id: str
    task_description: str
    task_type_estimate: str
    routing_confidence: float
    skill_chosen: str
    escalation_count: int
    postconditions_passed: bool
    failed_postconditions: list[int]
    execution_duration_ms: int
    result_size_tokens: int

class RoutingAuditLog:
    def log(self, decision: RoutingDecision):
        """Persist routing decision for analysis and debugging."""
        ...

    def get_failure_patterns(self, time_window: timedelta) -> dict:
        """Identify which skills fail post-conditions most often."""
        decisions = self.query(time_window=time_window)
        return {
            skill: {
                "failure_rate": sum(1 for d in decisions
                                    if d.skill_chosen == skill and not d.postconditions_passed)
                              / max(1, sum(1 for d in decisions if d.skill_chosen == skill)),
                "avg_confidence": sum(d.routing_confidence for d in decisions
                                      if d.skill_chosen == skill)
                                / max(1, sum(1 for d in decisions if d.skill_chosen == skill)),
            }
            for skill in {d.skill_chosen for d in decisions}
        }
```

---

## Routing Failure Modes

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| **Confident-but-unchecked** | Skill returns plausible output, no post-condition check | Mandatory post-conditions for every skill |
| **Scope creep** | Skill does more than its documented scope | Enforce `cannot_do` list in post-conditions |
| **Silent degradation** | Skill output quality drops but format is correct | Add semantic quality checks as post-conditions |
| **Composition drift** | Upstream output format changes silently break downstream | Schema validation at every handoff |
| **Over-escalation** | Every task escalates to general agent; specialization wasted | Calibrate min_confidence thresholds empirically |
| **Under-escalation** | Wrong skill used confidently without triggering escalation | Lower min_confidence threshold; add task-type training data |
| **Postcondition gaming** | Skill is optimized to pass checks, not to be actually correct | Design postconditions that check real outcomes, not output format |
