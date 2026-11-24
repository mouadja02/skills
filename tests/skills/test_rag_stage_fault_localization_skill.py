import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/agent-eval/rag-stage-fault-localization"


def test_skill_package_contract():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    required_sections = [
        "## When to Use",
        "## Prerequisites",
        "## How to Run",
        "## Quick Reference",
        "## Procedure",
        "## Pitfalls",
        "## Verification Checklist",
    ]
    positions = [text.index(section) for section in required_sections]
    assert positions == sorted(positions)
    assert "provisional retrieval-output fault" in text.lower()
    assert "Never inject faults into production." in text
    assert "certificate trust" in text
    assert (SKILL / "references/evidence-schema.md").is_file()
    assert (SKILL / "templates/incident-report.json").is_file()


def test_incident_template_preserves_unknowns_and_gates():
    report = json.loads((SKILL / "templates/incident-report.json").read_text(encoding="utf-8"))
    assert report["activation"]["status"] == "insufficient_evidence"
    assert report["earliest_supported_fault"] is None
    assert report["mapping_validation"]["status"] == "insufficient"
    assert report["replay"]["status"] == "not_executed"
    assert report["outcome"]["status"] == "inconclusive"
    assert report["safety"]["recorded_file_analysis_default"] is True
    assert report["safety"]["live_traffic_interception_authorized"] is False
    assert report["safety"]["certificate_trust_change_authorized"] is False
    assert report["safety"]["live_fault_injection_authorized"] is False
    assert report["cost"]["observed"] == "unknown"
