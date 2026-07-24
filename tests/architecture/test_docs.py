from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

def test_markdown_relative_links_exist():
    broken=[]
    for p in ROOT.rglob("*.md"):
        text=p.read_text(errors="ignore")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            dest=(p.parent/target.split("#",1)[0]).resolve()
            if not dest.exists(): broken.append((str(p.relative_to(ROOT)),target))
    assert not broken, broken

def test_no_unresolved_todo_markers():
    allowed={"docs/assumptions.md","docs/security/risk-register.md","docs/exec-plans/active/phase-01-design.md","docs/exec-plans/active/phase-02-implementation-plan.md"}
    bad=[]
    for p in ROOT.rglob("*.md"):
        rel=str(p.relative_to(ROOT))
        if rel in allowed: continue
        if re.search(r"\b(TODO|TBD|FIXME)\b", p.read_text(errors="ignore")):
            bad.append(rel)
    assert not bad, bad
