from __future__ import annotations

import ast
import json
from dataclasses import fields
from pathlib import Path

from cyber_eval.agent import AGENT_TURN_SCHEMA, AgentModelInput, AgentRunRequest
from cyber_eval.agent.contracts import AgentTurn

ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = ROOT / "src/cyber_eval/agent"


def test_phase_06_required_files_exist() -> None:
    required = {
        ".github/workflows/phase-06-agent.yml",
        "docs/design/agent-integration.md",
        "schemas/agent-run.schema.json",
        "schemas/agent-turn.schema.json",
        "src/cyber_eval/agent/context.py",
        "src/cyber_eval/agent/model_client.py",
        "src/cyber_eval/agent/orchestrator.py",
        "tests/integration/test_agent_workflow.py",
    }
    assert not sorted(path for path in required if not (ROOT / path).exists())
    plans = {
        ROOT / "docs/exec-plans/active/phase-06-agent-integration.md",
        ROOT / "docs/exec-plans/completed/phase-06-agent-integration.md",
    }
    assert sum(path.exists() for path in plans) == 1


def test_model_contracts_have_no_raw_destination_command_or_credential_fields() -> None:
    names = {field.name for field in fields(AgentRunRequest)}
    names |= {field.name for field in fields(AgentModelInput)}
    names |= {field.name for field in fields(AgentTurn)}
    forbidden = {
        "url",
        "ip",
        "hostname",
        "endpoint",
        "port",
        "command",
        "shell",
        "password",
        "api_key",
        "access_token",
        "private_key",
    }
    assert names.isdisjoint(forbidden)


def test_only_model_client_may_import_network_transport() -> None:
    network_roots = {"urllib", "socket", "requests", "httpx", "aiohttp"}
    findings: list[tuple[str, str]] = []
    for path in AGENT_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if any(name == root or name.startswith(f"{root}.") for root in network_roots):
                    findings.append((path.relative_to(ROOT).as_posix(), name))
    assert findings == [
        ("src/cyber_eval/agent/model_client.py", "urllib.error"),
        ("src/cyber_eval/agent/model_client.py", "urllib.request"),
    ]


def test_openai_transport_is_fixed_and_builtin_tools_are_disabled() -> None:
    text = (AGENT_ROOT / "model_client.py").read_text(encoding="utf-8")
    assert 'OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"' in text
    assert '"tool_choice": "none"' in text
    assert '"parallel_tool_calls": False' in text
    assert '"store": False' in text
    assert '"tools"' not in text


def test_agent_output_schema_is_closed_and_contains_no_execution_fields() -> None:
    assert AGENT_TURN_SCHEMA["additionalProperties"] is False
    properties = set(AGENT_TURN_SCHEMA["properties"])
    forbidden = {
        "command",
        "shell",
        "url",
        "ip",
        "hostname",
        "approval",
        "credential",
        "kill_switch",
        "audit_mutation",
        "tool_gateway_receipts",
    }
    assert properties.isdisjoint(forbidden)


def test_agent_source_cannot_directly_change_scope_approval_audit_or_credentials() -> None:
    orchestrator = (AGENT_ROOT / "orchestrator.py").read_text(encoding="utf-8")
    forbidden_calls = {
        ".scope_roe.register(",
        ".approvals.approve(",
        ".credential_broker.",
        ".emergency_stop.activate(",
        "DELETE FROM audit_events",
        "UPDATE audit_events",
    }
    assert not [term for term in forbidden_calls if term in orchestrator]
    assert "self._tool_gateway.invoke(" in orchestrator


def test_agent_schema_serializes_as_json_schema() -> None:
    document = json.loads(json.dumps(AGENT_TURN_SCHEMA))
    assert document["type"] == "object"
    assert document["properties"]["findings"]["items"]["additionalProperties"] is False


def test_phase_06_ci_is_read_only_and_runs_full_validation() -> None:
    text = (ROOT / ".github/workflows/phase-06-agent.yml").read_text(encoding="utf-8")
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull_request_target" not in text
    assert "python -m pytest" in text
    assert "OPENAI_API_KEY" not in text
