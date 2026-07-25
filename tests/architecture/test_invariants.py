import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "README.md",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "pyproject.toml",
    ".github/workflows/phase-02-skeleton.yml",
    "docs/index.md",
    "docs/assumptions.md",
    "docs/security/security-principles.md",
    "docs/security/threat-model.md",
    "docs/security/trust-boundaries.md",
    "docs/security/data-flow-diagrams.md",
    "docs/security/network-matrix.md",
    "docs/security/iam-model.md",
    "docs/security/credential-model.md",
    "docs/security/prompt-injection-model.md",
    "docs/security/abuse-cases.md",
    "docs/security/risk-register.md",
    "docs/governance/authorization-model.md",
    "docs/governance/rules-of-engagement.md",
    "docs/governance/data-handling.md",
    "docs/governance/evidence-retention.md",
    "docs/governance/incident-response.md",
    "docs/design/control-plane.md",
    "docs/design/execution-plane.md",
    "docs/design/cyber-range.md",
    "docs/design/observability.md",
    "docs/design/scoring.md",
    "docs/design/reset-and-destruction.md",
    "docs/design/api-boundaries.md",
    "docs/design/state-machines.md",
    "docs/design/repository-skeleton.md",
    "docs/traceability.md",
    "docs/design-review-checklist.md",
    "docs/exec-plans/completed/phase-01-design.md",
    "docs/exec-plans/completed/phase-02-repository-skeleton.md",
    "docs/exec-plans/completed/phase-03-control-plane-mvp.md",
    "docs/exec-plans/active/README.md",
    "src/cyber_eval/domain.py",
    "src/cyber_eval/interfaces.py",
    "src/cyber_eval/policy.py",
    "src/cyber_eval/gateway.py",
    "src/cyber_eval/state_machine.py",
]

FORBIDDEN_IMPORT_ROOTS = {
    "socket",
    "requests",
    "httpx",
    "aiohttp",
    "paramiko",
    "fabric",
    "boto3",
    "botocore",
    "azure",
    "google.cloud",
    "kubernetes",
    "docker",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_files_exist():
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    assert not missing, missing


def test_required_architecture_terms():
    text = read("ARCHITECTURE.md").lower()
    for term in [
        "control plane",
        "execution plane",
        "cyber range",
        "observability plane",
        "fail-closed",
        "default-deny",
    ]:
        assert term in text


def test_network_matrix_has_mandatory_denies():
    text = read("docs/security/network-matrix.md").lower()
    for term in [
        "general internet",
        "corporate/production",
        "cloud metadata",
        "docker",
        "kubernetes management api",
        "deny",
    ]:
        assert term in text


def test_threat_actors_present():
    text = read("docs/security/threat-model.md").lower()
    for term in [
        "external attacker",
        "malicious scenario content",
        "compromised or misaligned model",
        "malicious insider",
        "supply-chain attacker",
    ]:
        assert term in text


def test_stop_conditions_present():
    text = read("policies/stop_conditions.rego")
    for term in [
        "scope_deviation",
        "general_internet_access",
        "unexpected_privilege_escalation",
        "persistence",
        "log_tampering",
        "monitoring_loss",
    ]:
        assert term in text


def test_required_diagrams():
    expected = {
        "context.mmd",
        "trust-boundary-dfd.mmd",
        "network-zones.mmd",
        "evaluation-job-sequence.mmd",
        "approval-state.mmd",
        "emergency-stop-sequence.mmd",
        "runner-lifecycle.mmd",
        "credential-sequence.mmd",
        "closed-loop.mmd",
        "audit-one-way.mmd",
    }
    actual = {path.name for path in (ROOT / "diagrams").glob("*.mmd")}
    assert expected <= actual


def test_required_adrs():
    adrs = list((ROOT / "docs/adr").glob("[0-9][0-9][0-9][0-9]-*.md"))
    assert len(adrs) >= 14
    for path in adrs:
        text = path.read_text()
        for heading in [
            "## Context",
            "## Decision",
            "## Alternatives",
            "## Security consequences",
            "## Operational consequences",
            "## Rejected options",
            "## Revisit conditions",
        ]:
            assert heading in text, (path, heading)


def test_no_arbitrary_model_api_examples():
    text = "\n".join(path.read_text(errors="ignore") for path in ROOT.rglob("*.md"))
    for pattern in [r"run_command\(", r"execute_shell\(", r"scan_url\(", r"scan_ip\("]:
        assert not re.search(pattern, text, re.IGNORECASE), pattern


def test_source_has_no_network_or_cloud_imports():
    bad = []
    for path in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                prohibited = any(
                    name == root or name.startswith(f"{root}.") for root in FORBIDDEN_IMPORT_ROOTS
                )
                if prohibited:
                    bad.append((str(path.relative_to(ROOT)), name))
    assert not bad, bad


def test_only_podman_adapter_uses_fixed_subprocess_boundary():
    bad = []
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text()
        if "import subprocess" in text and path.name != "podman.py":
            bad.append(str(path.relative_to(ROOT)))
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "compile"}:
                bad.append((str(path.relative_to(ROOT)), node.func.id))
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "system",
                "popen",
                "Popen",
                "call",
                "check_call",
                "check_output",
            }:
                bad.append((str(path.relative_to(ROOT)), node.func.attr))
    podman = read("src/cyber_eval/runner/podman.py")
    assert "shell=False" in podman
    assert "Sequence[str]" in podman
    assert not bad, bad


def test_phase_02_has_no_iac_or_runtime_image_artifacts():
    forbidden_names = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
    forbidden_suffixes = {".tf", ".tfvars", ".hcl"}
    bad = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file() and (path.name in forbidden_names or path.suffix in forbidden_suffixes)
    ]
    assert not bad, bad


def test_phase_02_runtime_contract_has_no_credential_fields():
    text = "\n".join(path.read_text().lower() for path in (ROOT / "src").rglob("*.py"))
    forbidden = ["api_key", "private_key", "access_token", "refresh_token", "password"]
    assert not [term for term in forbidden if term in text]


def test_traceability_exists():
    text = read("docs/traceability.md")
    for requirement in [
        "Phase 02 out-of-scope rejection",
        "Phase 02 approval rejection",
        "Phase 02 policy fail-closed",
        "Phase 02 negative state transitions",
        "Phase 02 non-executable skeleton",
    ]:
        assert requirement in text


def test_risk_register_has_high_risks():
    text = read("docs/security/risk-register.md")
    assert "R-001" in text and "R-018" in text


def test_ci_is_read_only_and_validation_only():
    text = read(".github/workflows/phase-02-skeleton.yml")
    assert "contents: read" in text
    assert "pull_request_target" not in text
    assert "contents: write" not in text
    assert "make validate" in text
    assert "terraform apply" not in text
    assert "tofu apply" not in text


def test_validation_dependencies_are_pinned():
    import tomllib

    configuration = tomllib.loads(read("pyproject.toml"))
    assert configuration["project"]["dependencies"] == []
    dependencies = configuration["project"]["optional-dependencies"]["dev"]
    assert dependencies
    assert all("==" in dependency for dependency in dependencies)
