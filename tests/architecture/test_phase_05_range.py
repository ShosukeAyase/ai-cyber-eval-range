from __future__ import annotations

import ast
import json
import re
from dataclasses import fields
from pathlib import Path

from cyber_eval.range.catalog import LocalScenarioCatalog
from cyber_eval.range.contracts import RangeActionRequest
from tests.harness.range import CATALOG_ROOT

ROOT = Path(__file__).resolve().parents[2]


def test_phase_05_required_files_exist() -> None:
    required = {
        "docs/design/cyber-range-mvp.md",
        ".github/workflows/phase-05-range.yml",
        "src/cyber_eval/range/catalog.py",
        "src/cyber_eval/range/runtime.py",
        "src/cyber_eval/range/scoring.py",
        "src/cyber_eval/range/service.py",
        "tests/integration/test_cyber_range_mvp.py",
        "schemas/range-scenario.schema.json",
    }
    assert not sorted(path for path in required if not (ROOT / path).exists())
    plan_candidates = {
        ROOT / "docs/exec-plans/active/phase-05-cyber-range-mvp.md",
        ROOT / "docs/exec-plans/completed/phase-05-cyber-range-mvp.md",
    }
    assert sum(path.exists() for path in plan_candidates) == 1


def test_range_action_has_object_ids_only() -> None:
    names = {field.name for field in fields(RangeActionRequest)}
    forbidden = {"url", "ip", "hostname", "endpoint", "port", "command", "shell", "path"}
    assert names.isdisjoint(forbidden)


def test_range_source_has_no_network_or_process_execution_imports() -> None:
    forbidden = {"socket", "subprocess", "requests", "httpx", "aiohttp", "urllib", "ftplib"}
    bad: list[tuple[str, str]] = []
    for path in (ROOT / "src/cyber_eval/range").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if any(name == root or name.startswith(f"{root}.") for root in forbidden):
                    bad.append((str(path.relative_to(ROOT)), name))
    assert not bad, bad


def test_catalog_contains_seven_non_networked_synthetic_scenarios() -> None:
    catalog = LocalScenarioCatalog(CATALOG_ROOT)
    assert len(catalog.scenario_ids()) == 7
    for scenario_id in catalog.scenario_ids():
        root = CATALOG_ROOT / scenario_id
        document = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
        assert document["network"] == {"mode": "none", "external_access": False}
        assert document["synthetic_data"]["contains_real_data"] is False
        assert document["synthetic_data"]["contains_credentials"] is False
        assert document["lateral_movement"]["outside_assets_denied"] is True
        assert (root / "answer-key.json").is_file()
        assert not (root / "synthetic" / "answer-key.json").exists()


def test_scenario_packages_have_all_requested_sections() -> None:
    required = {
        "initial_state",
        "allowed_operations",
        "forbidden_operations",
        "synthetic_data",
        "expected_findings",
        "expected_detections",
        "stop_conditions",
        "scoring",
        "reset",
        "destruction",
    }
    for path in CATALOG_ROOT.glob("*/scenario.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        assert required <= set(document), path
        assert sum(item["points"] for item in document["scoring"]) == 100
        assert document["reset"]["deterministic"] is True
        assert all(document["destruction"].values())


def test_synthetic_scenarios_contain_no_active_payload_or_external_destination() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in CATALOG_ROOT.rglob("*")
        if path.is_file()
    )
    forbidden_patterns = (
        r"https?://",
        r"\b(?:curl|wget)\b",
        r"\brm\s+-rf\b",
        r"/bin/(?:sh|bash)",
        r"powershell(?:\.exe)?\s+-",
        r"169\.254\.169\.254",
        r"/var/run/docker\.sock",
        r"serviceaccount/token",
    )
    assert not [pattern for pattern in forbidden_patterns if re.search(pattern, text, re.I)]
    markers = re.findall(r"RANGE-MARKER-[A-Z0-9-]+", text)
    assert markers


def test_phase_05_ci_is_read_only_and_validation_only() -> None:
    text = (ROOT / ".github/workflows/phase-05-range.yml").read_text(encoding="utf-8")
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "pull_request_target" not in text
    assert "python -m pytest" in text
    assert "podman run" not in text
    assert "docker run" not in text
