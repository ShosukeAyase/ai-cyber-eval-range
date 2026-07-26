from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSURANCE = ROOT / "docs/assurance"


def test_required_assurance_outputs_exist() -> None:
    required = {
        "assurance-report.md",
        "residual-risk-register.md",
        "go-no-go-checklist.md",
        "production-readiness-gaps.md",
        "phase7-assurance-evidence.json",
    }
    assert not sorted(name for name in required if not (ASSURANCE / name).is_file())


def test_assurance_decision_is_no_go_when_high_risks_are_open() -> None:
    evidence_path = ASSURANCE / "phase7-assurance-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["summary"]["high_or_critical_unresolved"] > 0
    assert evidence["decision"] == "NO-GO"


def test_reports_do_not_claim_production_readiness() -> None:
    report = (ASSURANCE / "assurance-report.md").read_text(encoding="utf-8")
    checklist = (ASSURANCE / "go-no-go-checklist.md").read_text(encoding="utf-8")
    assert "Production decision: NO-GO" in report
    assert "**NO-GO**" in checklist
    assert "production-ready" not in report.lower().split("not production-ready", 1)[0]


def test_high_risks_have_required_treatment() -> None:
    evidence_path = ASSURANCE / "phase7-assurance-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    high = [
        item
        for item in evidence["checks"]
        if item["status"] != "PASS" and item["severity_if_failed"] in {"high", "critical"}
    ]
    assert high
    assert all(item["remediation"].strip() for item in high)
