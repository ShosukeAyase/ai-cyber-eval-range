"""Finalize Phase 04 documentation only after the operator-laptop live gate passes."""

from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path

_IMAGE_REF = re.compile(r"^(?:[a-z0-9][a-z0-9._/-]*@)?sha256:[0-9a-f]{64}$")


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise RuntimeError(f"could not update {label}")
    return text.replace(old, new, 1)


def _manifest_paths(root: Path) -> list[str]:
    excluded_parts = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    paths: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or excluded_parts.intersection(path.parts):
            continue
        if path.suffix == ".pyc":
            continue
        paths.append(path.relative_to(root).as_posix())
    return sorted(paths)


def finalize(root: Path, runner_image_ref: str, completed_at: datetime) -> None:
    root = root.resolve()
    if not _IMAGE_REF.fullmatch(runner_image_ref):
        raise ValueError("runner image reference must be digest-pinned")

    active = root / "docs/exec-plans/active/phase-04-isolated-runner-mvp.md"
    completed = root / "docs/exec-plans/completed/phase-04-isolated-runner-mvp.md"
    if active.exists() and completed.exists():
        raise RuntimeError("Phase 04 plan exists in both active and completed directories")
    if active.exists():
        plan = active.read_text(encoding="utf-8")
    elif completed.exists():
        plan = completed.read_text(encoding="utf-8")
    else:
        raise RuntimeError("Phase 04 execution plan is missing")

    plan = re.sub(r"^Status:.*$", "Status: completed", plan, count=1, flags=re.MULTILINE)
    plan = plan.replace(
        "- [ ] Execute the live rootless-Podman smoke test on the operator laptop.",
        "- [x] Execute the live rootless-Podman smoke test on the operator laptop.",
    )
    if "## Live completion record" not in plan:
        plan += (
            "\n## Live completion record\n\n"
            f"- Completed at: `{completed_at.astimezone(UTC).isoformat()}`\n"
            f"- Runner image: `{runner_image_ref}`\n"
            "- Rootless Podman preflight: PASS.\n"
            "- Ruff format/lint, mypy, complete pytest suite, and live isolated Runner "
            "smoke: PASS.\n"
            "- Phase 04 is complete for the approved single-laptop local profile only.\n"
        )
    completed.parent.mkdir(parents=True, exist_ok=True)
    completed.write_text(plan, encoding="utf-8")
    if active.exists():
        active.unlink()

    active_readme = root / "docs/exec-plans/active/README.md"
    active_readme.write_text(
        "# Active Execution Plans\n\n"
        "No subsequent phase is approved. Phase 04 is recorded under `../completed/`. "
        "External targets, internet access, real credentials, arbitrary commands, cloud "
        "resources, Kubernetes workloads, exploit validation, and production deployment "
        "remain prohibited.\n",
        encoding="utf-8",
    )

    index_path = root / "docs/index.md"
    index = index_path.read_text(encoding="utf-8")
    index = _replace_once(
        index,
        "- [Active Phase 04 Runner MVP](exec-plans/active/phase-04-isolated-runner-mvp.md)",
        "- [Completed Phase 04 Runner MVP](exec-plans/completed/phase-04-isolated-runner-mvp.md)",
        label="documentation index",
    )
    index_path.write_text(index, encoding="utf-8")

    report_path = root / "docs/validation-report.md"
    report = report_path.read_text(encoding="utf-8")
    conditional = (
        "Phase 04 implementation, deterministic tests, documentation, offline image definition, "
        "and local completion scripts are complete. Formal Phase 04 completion remains conditional "
        "on the operator laptop successfully running Ruff, mypy, the complete pytest suite, "
        "rootless Podman preflight, and the live isolated Runner smoke test using a reviewed "
        "digest-pinned local image."
    )
    completed_status = (
        "Phase 04 is complete for the approved single-laptop local profile. Deterministic "
        "validation and the operator-laptop Ruff, mypy, complete pytest, rootless Podman, and "
        "live isolated Runner gates passed."
    )
    report = _replace_once(report, conditional, completed_status, label="validation status")
    if "## Operator-laptop live validation" not in report:
        report += (
            "\n## Operator-laptop live validation\n\n"
            f"- Completed at: `{completed_at.astimezone(UTC).isoformat()}`\n"
            f"- Digest-pinned Runner image: `{runner_image_ref}`\n"
            "- Rootless Podman preflight: PASS.\n"
            "- Ruff format/lint: PASS.\n"
            "- mypy strict type check: PASS.\n"
            "- Complete pytest suite: PASS.\n"
            "- Live isolated Runner smoke test: PASS.\n"
        )
    report_path.write_text(report, encoding="utf-8")

    manifest_path = root / "FILE-MANIFEST.txt"
    manifest_path.write_text("\n".join(_manifest_paths(root)) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner-image-ref", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args()
    finalize(arguments.root, arguments.runner_image_ref, datetime.now(UTC))


if __name__ == "__main__":
    main()
