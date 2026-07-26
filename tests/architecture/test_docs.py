import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_markdown_relative_links_exist():
    broken = []
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            destination = (path.parent / target.split("#", 1)[0]).resolve()
            if not destination.exists():
                broken.append((str(path.relative_to(ROOT)), target))
    assert not broken, broken


def test_no_unresolved_todo_markers():
    allowed = {
        "docs/assumptions.md",
        "docs/security/risk-register.md",
        "docs/exec-plans/active/README.md",
    }
    bad = []
    for path in ROOT.rglob("*.md"):
        relative = str(path.relative_to(ROOT))
        if relative in allowed:
            continue
        if re.search(r"\b(TODO|TBD|FIXME)\b", path.read_text(encoding="utf-8", errors="ignore")):
            bad.append(relative)
    assert not bad, bad


def test_document_index_points_to_current_plans():
    text = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    assert "exec-plans/completed/phase-01-design.md" in text
    assert "exec-plans/completed/phase-02-repository-skeleton.md" in text
    assert "exec-plans/completed/phase-03-control-plane-mvp.md" in text
    assert "exec-plans/completed/phase-04-isolated-runner-mvp.md" in text
    phase_05_links = {
        "exec-plans/active/phase-05-cyber-range-mvp.md",
        "exec-plans/completed/phase-05-cyber-range-mvp.md",
    }
    assert sum(link in text for link in phase_05_links) == 1
    phase_06_links = {
        "exec-plans/active/phase-06-agent-integration.md",
        "exec-plans/completed/phase-06-agent-integration.md",
    }
    assert sum(link in text for link in phase_06_links) == 1
    assert "exec-plans/active/README.md" in text
