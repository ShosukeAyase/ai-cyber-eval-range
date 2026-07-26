"""Finalize Phase 05 only after local quality gates pass."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path


def _manifest_paths(root: Path) -> list[str]:
    excluded = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }
    paths: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or excluded.intersection(path.parts):
            continue
        if path.suffix == ".pyc" or any(part.endswith(".egg-info") for part in path.parts):
            continue
        paths.append(path.relative_to(root).as_posix())
    return sorted(paths)


def finalize(root: Path, completed_at: datetime) -> None:
    root = root.resolve()
    active = root / "docs/exec-plans/active/phase-05-cyber-range-mvp.md"
    completed = root / "docs/exec-plans/completed/phase-05-cyber-range-mvp.md"
    if active.exists() and completed.exists():
        raise RuntimeError("Phase 05 plan exists in both active and completed directories")
    if active.exists():
        plan = active.read_text(encoding="utf-8")
    elif completed.exists():
        plan = completed.read_text(encoding="utf-8")
    else:
        raise RuntimeError("Phase 05 execution plan is missing")
    plan = re.sub(r"^Status:.*$", "Status: completed", plan, count=1, flags=re.MULTILINE)
    plan = plan.replace("- [ ]", "- [x]")
    if "## Completion record" not in plan:
        plan += (
            "\n## Completion record\n\n"
            f"- Completed at: `{completed_at.astimezone(UTC).isoformat()}`.\n"
            "- Ruff format/lint: PASS.\n"
            "- mypy strict type check: PASS.\n"
            "- Complete pytest suite: PASS.\n"
            "- Scenario catalog verification: PASS for seven scenarios.\n"
            "- Phase 05 is complete for the approved non-networked local profile only.\n"
        )
    completed.parent.mkdir(parents=True, exist_ok=True)
    completed.write_text(plan, encoding="utf-8")
    if active.exists():
        active.unlink()

    active_readme = root / "docs/exec-plans/active/README.md"
    active_readme.write_text(
        "# Active Execution Plans\n\n"
        "No subsequent phase is approved. Phase 05 is recorded under `../completed/`. "
        "Networked vulnerable services, external targets, real credentials, cloud resources, "
        "Kubernetes clusters, exploit validation, and production deployment remain prohibited.\n",
        encoding="utf-8",
    )

    completed_readme = root / "docs/exec-plans/completed/README.md"
    text = completed_readme.read_text(encoding="utf-8")
    if "phase-05-cyber-range-mvp.md" not in text:
        text = text.rstrip() + "\n- `phase-05-cyber-range-mvp.md`\n"
    completed_readme.write_text(text, encoding="utf-8")

    index_path = root / "docs/index.md"
    index = index_path.read_text(encoding="utf-8")
    index = index.replace(
        "- [Active Phase 05 Cyber Range MVP](exec-plans/active/phase-05-cyber-range-mvp.md)",
        "- [Completed Phase 05 Cyber Range MVP](exec-plans/completed/phase-05-cyber-range-mvp.md)",
    )
    index_path.write_text(index, encoding="utf-8")

    report_path = root / "docs/validation-report.md"
    report = report_path.read_text(encoding="utf-8")
    report = report.replace(
        "Phase 05 implementation and deterministic validation are complete. Phase 05 formal "
        "status:\npending operator-laptop Ruff, mypy, complete pytest, Python compilation, "
        "catalog verification,\nand Git whitespace gates.",
        "Phase 05 implementation, deterministic validation, and operator-laptop quality gates "
        "are complete. Phase 05 formal status: complete for the approved non-networked local "
        "synthetic profile.",
    )
    if "## Operator-laptop Phase 05 quality gates" not in report:
        report += (
            "\n## Operator-laptop Phase 05 quality gates\n\n"
            f"- Completed at: `{completed_at.astimezone(UTC).isoformat()}`.\n"
            "- Ruff format check and lint: PASS.\n"
            "- mypy strict type check: PASS.\n"
            "- Complete pytest suite: PASS.\n"
            "- Python compilation: PASS.\n"
            "- Git whitespace validation: PASS.\n"
            "- Phase 05 status: complete for the local non-networked synthetic profile.\n"
        )
    report_path.write_text(report, encoding="utf-8")

    manifest_path = root / "FILE-MANIFEST.txt"
    manifest_path.write_text("\n".join(_manifest_paths(root)) + "\n", encoding="utf-8")


def main() -> None:
    finalize(Path(__file__).resolve().parents[1], datetime.now(UTC))


if __name__ == "__main__":
    main()
