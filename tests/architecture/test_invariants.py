from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
 "README.md","AGENTS.md","ARCHITECTURE.md","docs/index.md","docs/assumptions.md",
 "docs/security/security-principles.md","docs/security/threat-model.md","docs/security/trust-boundaries.md",
 "docs/security/data-flow-diagrams.md","docs/security/network-matrix.md","docs/security/iam-model.md",
 "docs/security/credential-model.md","docs/security/prompt-injection-model.md","docs/security/abuse-cases.md",
 "docs/security/risk-register.md","docs/governance/authorization-model.md","docs/governance/rules-of-engagement.md",
 "docs/governance/data-handling.md","docs/governance/evidence-retention.md","docs/governance/incident-response.md",
 "docs/design/control-plane.md","docs/design/execution-plane.md","docs/design/cyber-range.md",
 "docs/design/observability.md","docs/design/scoring.md","docs/design/reset-and-destruction.md",
 "docs/design/api-boundaries.md","docs/design/state-machines.md","docs/traceability.md",
 "docs/design-review-checklist.md","docs/exec-plans/active/phase-01-design.md",
 "docs/exec-plans/active/phase-02-implementation-plan.md",
]

def read(path): return (ROOT / path).read_text(encoding="utf-8")

def test_required_files_exist():
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    assert not missing, missing

def test_required_architecture_terms():
    text = read("ARCHITECTURE.md").lower()
    for term in ["control plane", "execution plane", "cyber range", "observability plane", "fail-closed", "default-deny"]:
        assert term in text

def test_network_matrix_has_mandatory_denies():
    text = read("docs/security/network-matrix.md").lower()
    for term in ["general internet", "corporate/production", "cloud metadata", "docker", "kubernetes management api", "deny"]:
        assert term in text

def test_threat_actors_present():
    text = read("docs/security/threat-model.md").lower()
    for term in ["external attacker", "malicious scenario content", "compromised or misaligned model", "malicious insider", "supply-chain attacker"]:
        assert term in text

def test_stop_conditions_present():
    text = read("policies/stop_conditions.rego")
    for term in ["scope_deviation", "general_internet_access", "unexpected_privilege_escalation", "persistence", "log_tampering", "monitoring_loss"]:
        assert term in text

def test_required_diagrams():
    expected = {"context.mmd","trust-boundary-dfd.mmd","network-zones.mmd","evaluation-job-sequence.mmd","approval-state.mmd","emergency-stop-sequence.mmd","runner-lifecycle.mmd","credential-sequence.mmd","closed-loop.mmd","audit-one-way.mmd"}
    actual = {p.name for p in (ROOT/"diagrams").glob("*.mmd")}
    assert expected <= actual

def test_required_adrs():
    adrs = list((ROOT/"docs/adr").glob("[0-9][0-9][0-9][0-9]-*.md"))
    assert len(adrs) >= 14
    for p in adrs:
        t = p.read_text()
        for heading in ["## Context","## Decision","## Alternatives","## Security consequences","## Operational consequences","## Rejected options","## Revisit conditions"]:
            assert heading in t, (p, heading)

def test_no_arbitrary_model_api_examples():
    text = "\n".join(p.read_text(errors="ignore") for p in ROOT.rglob("*.md"))
    forbidden = [r"run_command\(", r"execute_shell\(", r"scan_url\(", r"scan_ip\("]
    for pattern in forbidden:
        assert not re.search(pattern, text, re.IGNORECASE), pattern

def test_risk_register_has_high_risks():
    text = read("docs/security/risk-register.md")
    scores = [int(x) for x in re.findall(r"\|\s*(\d{1,2})\s*\|\s*(?:Treatment|[A-Za-z])", text)]
    assert "R-001" in text and "R-018" in text
