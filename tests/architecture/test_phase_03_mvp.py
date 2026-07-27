from __future__ import annotations

import ast
import inspect
from dataclasses import fields
from pathlib import Path

from cyber_eval.approval_service import ApprovalService
from cyber_eval.audit import AuditService
from cyber_eval.credential_broker import CredentialBrokerMock
from cyber_eval.domain import CredentialReference, ModelRequest, ToolRequest
from cyber_eval.emergency_stop import EmergencyStopService
from cyber_eval.engagement_service import EngagementService
from cyber_eval.model_gateway import DeterministicModelGatewayMock
from cyber_eval.policy_adapter import LocalPolicyEngineAdapter
from cyber_eval.scope_roe_service import ScopeRoeService
from cyber_eval.tool_gateway import ToolGatewayMock

ROOT = Path(__file__).resolve().parents[2]

SERVICE_CLASSES = (
    EngagementService,
    ScopeRoeService,
    ApprovalService,
    LocalPolicyEngineAdapter,
    DeterministicModelGatewayMock,
    ToolGatewayMock,
    CredentialBrokerMock,
    EmergencyStopService,
    AuditService,
)

WRITE_METHODS = {
    EngagementService: ("create", "activate", "close"),
    ScopeRoeService: ("register",),
    ApprovalService: ("request", "approve"),
    CredentialBrokerMock: ("issue_reference", "revoke_reference"),
    EmergencyStopService: ("activate", "clear"),
}


def test_phase_03_required_files_exist() -> None:
    required = {
        ".github/workflows/phase-03-control-plane.yml",
        "docs/design/control-plane-mvp.md",
        "docs/exec-plans/completed/phase-03-control-plane-mvp.md",
        "src/cyber_eval/store.py",
        "src/cyber_eval/engagement_service.py",
        "src/cyber_eval/scope_roe_service.py",
        "src/cyber_eval/approval_service.py",
        "src/cyber_eval/policy_adapter.py",
        "src/cyber_eval/model_gateway.py",
        "src/cyber_eval/tool_gateway.py",
        "src/cyber_eval/credential_broker.py",
        "src/cyber_eval/emergency_stop.py",
        "src/cyber_eval/control_plane.py",
        "tests/integration/test_control_plane_mvp.py",
    }
    missing = sorted(path for path in required if not (ROOT / path).exists())
    assert not missing, missing


def test_all_public_service_operations_require_engagement_id() -> None:
    missing = []
    for service_class in SERVICE_CLASSES:
        for name, member in inspect.getmembers(service_class, inspect.isfunction):
            if name.startswith("_"):
                continue
            parameters = inspect.signature(member).parameters
            if "engagement_id" not in parameters:
                missing.append(f"{service_class.__name__}.{name}")
    assert not missing, missing


def test_all_state_writes_use_transactional_audit() -> None:
    missing = []
    for service_class, method_names in WRITE_METHODS.items():
        for method_name in method_names:
            source = inspect.getsource(getattr(service_class, method_name))
            if "audited_transaction" not in source:
                missing.append(f"{service_class.__name__}.{method_name}")
    assert not missing, missing


def test_model_and_tool_contracts_have_no_destination_or_command_fields() -> None:
    field_names = {field.name for field in fields(ModelRequest)} | {
        field.name for field in fields(ToolRequest)
    }
    forbidden = {"url", "ip", "hostname", "command", "shell", "endpoint"}
    assert field_names.isdisjoint(forbidden)


def test_credential_reference_has_no_secret_value_fields() -> None:
    field_names = {field.name for field in fields(CredentialReference)}
    forbidden = {"value", "password", "api_key", "access_token", "private_key"}
    assert field_names.isdisjoint(forbidden)


def test_emergency_stop_has_no_model_or_runner_dependency() -> None:
    parameters = set(inspect.signature(EmergencyStopService.__init__).parameters)
    forbidden = {"model", "model_gateway", "runner", "tool_gateway"}
    assert parameters.isdisjoint(forbidden)


def test_phase_03_source_has_no_http_server_or_network_runtime() -> None:
    forbidden_roots = {
        "socket",
        "http.server",
        "urllib",
        "requests",
        "httpx",
        "aiohttp",
        "fastapi",
        "flask",
        "uvicorn",
    }
    findings = []
    phase_specific_network_adapters = {
        "cyber_eval/agent",
        "cyber_eval/identity_adapters",
    }
    for path in (ROOT / "src").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        if any(component in relative for component in phase_specific_network_adapters):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if any(name == root or name.startswith(f"{root}.") for root in forbidden_roots):
                    findings.append((str(path.relative_to(ROOT)), name))
    assert not findings, findings


def test_phase_03_ci_is_read_only_and_local_validation_only() -> None:
    text = (ROOT / ".github/workflows/phase-03-control-plane.yml").read_text(encoding="utf-8")
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull_request_target" not in text
    assert "make validate" in text
    assert "python -m cyber_eval.demo" in text
    for term in ["terraform apply", "tofu apply", "kubectl", "docker run", "curl "]:
        assert term not in text
