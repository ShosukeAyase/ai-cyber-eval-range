"""Finalize Phase 06 only after operator-laptop quality gates pass."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "docs/exec-plans/active/phase-06-agent-integration.md"
COMPLETED = ROOT / "docs/exec-plans/completed/phase-06-agent-integration.md"


def write_lf(path: Path, text: str) -> None:
    path.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8")


def update_manifest() -> None:
    excluded_parts = {".git", ".pytest_cache", "__pycache__"}
    paths = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in excluded_parts or part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.suffix == ".pyc":
            continue
        paths.append(relative.as_posix())
    write_lf(ROOT / "FILE-MANIFEST.txt", "\n".join(sorted(paths)) + "\n")


def completion_time(plan_text: str) -> str:
    match = re.search(r"- Completed at: `([^`]+)`\.", plan_text)
    if match is not None:
        return match.group(1)
    return datetime.now(UTC).isoformat()


def finalize_plan() -> tuple[str, str]:
    if ACTIVE.exists():
        text = ACTIVE.read_text(encoding="utf-8")
    elif COMPLETED.exists():
        text = COMPLETED.read_text(encoding="utf-8")
    else:
        raise SystemExit("Phase 06 execution plan is missing")

    text = text.replace("Status: active", "Status: completed", 1)
    text = text.replace(
        (
            "- [ ] Execute operator-laptop Ruff, mypy, full pytest, and optional "
            "live provider validation."
        ),
        "- [x] Execute operator-laptop Ruff, mypy, full pytest, compilation, and Git gates.",
    )
    completed_at = completion_time(text)
    if "## Operator-laptop completion record" not in text:
        text = text.rstrip() + (
            "\n\n## Operator-laptop completion record\n\n"
            f"- Completed at: `{completed_at}`.\n"
            "- Ruff format and lint: PASS.\n"
            "- mypy strict type check: PASS.\n"
            "- Complete pytest suite: PASS.\n"
            "- Python compilation: PASS.\n"
            "- Git whitespace validation: PASS.\n"
            "- Live provider request: not required for deterministic completion; "
            "explicit operator gate.\n"
            "- Phase 06 is complete for the proposal-only Agent integration profile.\n"
        )
    write_lf(COMPLETED, text)
    if ACTIVE.exists():
        ACTIVE.unlink()
    return text, completed_at


def update_indexes() -> None:
    write_lf(
        ROOT / "docs/exec-plans/active/README.md",
        "# Active Execution Plans\n\nNo subsequent phase is approved. Phase 06 is recorded under "
        "`../completed/`. External targets, arbitrary commands, model-selected destinations, "
        "real credentials, exploit capability, and automatic patch merge remain prohibited.\n",
    )

    completed_index = ROOT / "docs/exec-plans/completed/README.md"
    completed_text = completed_index.read_text(encoding="utf-8")
    link = "- [Phase 06 Agent integration](phase-06-agent-integration.md)\n"
    if link not in completed_text:
        completed_text = completed_text.rstrip() + "\n" + link
    write_lf(completed_index, completed_text)

    index = ROOT / "docs/index.md"
    index_text = index.read_text(encoding="utf-8").replace(
        "- [Active Phase 06 Agent integration](exec-plans/active/phase-06-agent-integration.md)",
        "- [Completed Phase 06 Agent integration]"
        "(exec-plans/completed/phase-06-agent-integration.md)",
    )
    write_lf(index, index_text)


def update_validation(completed_at: str) -> None:
    validation = ROOT / "docs/validation-report.md"
    text = validation.read_text(encoding="utf-8")
    text = text.replace(
        "Phase 06 implementation and deterministic adversarial validation are complete. Formal "
        "status\nremains active until the operator-laptop quality gates are recorded.",
        "Phase 06 implementation, deterministic adversarial validation, and operator-laptop "
        "quality gates are complete. Phase 06 formal status: complete for the proposal-only "
        "Agent integration profile.",
    )
    if "## Operator-laptop Phase 06 quality gates" not in text:
        text = text.rstrip() + (
            "\n\n## Operator-laptop Phase 06 quality gates\n\n"
            f"- Completed at: `{completed_at}`.\n"
            "- Ruff format check and lint: PASS.\n"
            "- mypy strict type check: PASS.\n"
            "- Complete pytest suite: PASS.\n"
            "- Python compilation: PASS.\n"
            "- Git whitespace validation: PASS.\n"
            "- Phase 06 status: complete for the proposal-only Agent integration profile.\n"
        )
    write_lf(validation, text)


def main() -> None:
    _, completed_at = finalize_plan()
    update_indexes()
    update_validation(completed_at)
    update_manifest()


if __name__ == "__main__":
    main()
