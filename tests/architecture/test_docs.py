from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def test_markdown_relative_links_exist():
    broken = []
    for path in ROOT.rglob("*.md"):
        text = path.read_text(errors="ignore")
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
        "docs/exec-plans/active/phase-03-implementation-plan.md",
    }
    bad = []
    for path in ROOT.rglob("*.md"):
        relative = str(path.relative_to(ROOT))
        if relative in allowed:
            continue
        if re.search(r"\b(TODO|TBD|FIXME)\b", path.read_text(errors="ignore")):
            bad.append(relative)
    assert not bad, bad


def test_document_index_points_to_current_plans():
    text = (ROOT / "docs/index.md").read_text()
    assert "exec-plans/completed/phase-01-design.md" in text
    assert "exec-plans/completed/phase-02-repository-skeleton.md" in text
    assert "exec-plans/active/phase-03-implementation-plan.md" in text
