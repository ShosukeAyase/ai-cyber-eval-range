from __future__ import annotations

import ast
import json
from dataclasses import fields
from pathlib import Path

from cyber_eval.identity import AuthorizationContext, HumanTokenClaims, VerifiedPrincipal

ROOT = Path(__file__).resolve().parents[2]
IDENTITY_ROOT = ROOT / "src/cyber_eval/identity"


def test_phase_08_required_files_exist() -> None:
    required = {
        ".github/workflows/phase-08-identity.yml",
        "docs/adr/0016-production-identity.md",
        "docs/design/production-identity.md",
        "docs/exec-plans/active/phase-08-production-iam.md",
        "schemas/human-identity-claims.schema.json",
        "schemas/workload-identity.schema.json",
        "schemas/authorization-context.schema.json",
        "src/cyber_eval/identity/contracts.py",
        "src/cyber_eval/identity/synthetic.py",
        "src/cyber_eval/identity/boundary.py",
        "tests/unit/test_phase_08_identity.py",
        "tests/integration/test_phase_08_identity_boundary.py",
        "scripts/complete_phase8.ps1",
    }
    assert not sorted(path for path in required if not (ROOT / path).exists())
    assert not (ROOT / "docs/exec-plans/completed/phase-08-production-iam.md").exists()


def test_identity_contracts_do_not_accept_secrets_or_caller_roles() -> None:
    names = {field.name for field in fields(HumanTokenClaims)}
    names |= {field.name for field in fields(VerifiedPrincipal)}
    names |= {field.name for field in fields(AuthorizationContext)}
    forbidden = {
        "password",
        "api_key",
        "access_token",
        "private_key",
        "secret",
        "request_body_role",
        "caller_role",
    }
    assert names.isdisjoint(forbidden)


def test_identity_package_has_no_network_or_process_execution_imports() -> None:
    forbidden_roots = {
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
    }
    findings: list[tuple[str, str]] = []
    for path in IDENTITY_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                root = name.split(".", 1)[0]
                if root in forbidden_roots:
                    findings.append((path.relative_to(ROOT).as_posix(), name))
    assert findings == []


def test_identity_schemas_are_closed_and_contain_no_secret_material() -> None:
    for name in ["human-identity-claims", "workload-identity", "authorization-context"]:
        schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
        properties = set(schema["properties"])
        assert properties.isdisjoint(
            {"password", "api_key", "access_token", "private_key", "secret"}
        )


def test_phase_08_ci_is_read_only_and_requires_full_validation() -> None:
    text = (ROOT / ".github/workflows/phase-08-identity.yml").read_text(encoding="utf-8")
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull_request_target" not in text
    assert "python -m pytest" in text
    assert "python -m mypy src" in text
    assert "OIDC_CLIENT_SECRET" not in text
    assert "SPIFFE" not in text
