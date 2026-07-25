"""Fixed read-only Runner workload; it never executes repository-supplied code."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cyber_eval.errors import ResourceLimitError, RunnerEvidenceError
from cyber_eval.runner.contracts import RunnerOperation

_FORBIDDEN_IMPORTS = {
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "aiohttp",
    "paramiko",
    "docker",
    "kubernetes",
    "boto3",
}
_FORBIDDEN_CALLS = {"eval", "exec", "compile", "system", "popen", "Popen"}


def execute_fixed_workload(
    *,
    job: dict[str, Any],
    input_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    """Read, analyze, test, and collect evidence without executing target code."""
    limits = job["limits"]
    operations = tuple(RunnerOperation(value) for value in job["operations"])
    files = _inventory(
        input_root,
        max_files=int(limits["max_source_files"]),
        max_file_bytes=int(limits["max_file_bytes"]),
    )
    findings: list[dict[str, str]] = []
    tests: list[dict[str, str]] = []

    if RunnerOperation.STATIC_ANALYSIS in operations:
        findings = _static_analysis(input_root, files)
    if RunnerOperation.RUN_DEFINED_TESTS in operations:
        tests = _predefined_tests(input_root, files)

    isolation = _isolation_observations()
    evidence = {
        "schema_version": "1.0",
        "job_id": job["job_id"],
        "engagement_id": job["engagement_id"],
        "target_id": job["target_id"],
        "repository_id": job["repository_id"],
        "profile_id": job["profile_id"],
        "repository_sha256": _content_digest(input_root, files),
        "operations": [item.value for item in operations],
        "files": files,
        "findings": findings,
        "tests": tests,
        "isolation": isolation,
    }
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > int(limits["evidence_bytes"]):
        raise RunnerEvidenceError("evidence exceeds the approved byte limit")
    workspace_root.mkdir(parents=True, exist_ok=True)
    output = workspace_root / "evidence.json"
    output.write_bytes(encoded)
    return evidence


def _inventory(root: Path, *, max_files: int, max_file_bytes: int) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.is_symlink():
            raise RunnerEvidenceError("symbolic links are not accepted by the fixed workload")
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            raise ResourceLimitError("source file exceeds the approved size limit")
        files.append({"path": relative.as_posix(), "size_bytes": size})
        if len(files) > max_files:
            raise ResourceLimitError("repository exceeds the approved file-count limit")
    return files


def _static_analysis(root: Path, files: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for item in files:
        relative = str(item["path"])
        if not relative.endswith(".py"):
            continue
        path = root / relative
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (SyntaxError, UnicodeDecodeError) as exc:
            findings.append({"path": relative, "rule": "python_parse_error", "detail": str(exc)})
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for name in names:
                root_name = name.split(".", maxsplit=1)[0]
                if root_name in _FORBIDDEN_IMPORTS:
                    findings.append({"path": relative, "rule": "sensitive_import", "detail": name})
            if isinstance(node, ast.Call):
                call_name = _call_name(node)
                if call_name in _FORBIDDEN_CALLS:
                    findings.append(
                        {"path": relative, "rule": "dynamic_execution", "detail": call_name}
                    )
    return findings


def _predefined_tests(root: Path, files: list[dict[str, Any]]) -> list[dict[str, str]]:
    parse_failures = [
        item["path"]
        for item in files
        if str(item["path"]).endswith(".py") and not _parses(root / str(item["path"]))
    ]
    return [
        {
            "test_id": "defined-python-parse",
            "status": "passed" if not parse_failures else "failed",
            "detail": ",".join(str(item) for item in parse_failures),
        },
        {
            "test_id": "defined-no-symlinks",
            "status": "passed",
            "detail": "inventory rejected symbolic links",
        },
        {
            "test_id": "defined-size-bounds",
            "status": "passed",
            "detail": f"checked {len(files)} files",
        },
    ]


def _parses(path: Path) -> bool:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return False
    return True


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _content_digest(root: Path, files: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for item in files:
        relative = str(item["path"])
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / relative).read_bytes())
    return digest.hexdigest()


def _isolation_observations() -> dict[str, bool]:
    route_file = Path("/proc/net/route")
    has_non_loopback_default = False
    if route_file.exists():
        lines = route_file.read_text(errors="ignore").splitlines()[1:]
        has_non_loopback_default = any(
            fields[1] == "00000000" and fields[0] != "lo"
            for line in lines
            if len(fields := line.split()) >= 2
        )
    return {
        "non_root": not hasattr(os, "geteuid") or os.geteuid() != 0,
        "no_default_route": not has_non_loopback_default,
        "docker_socket_absent": not Path("/var/run/docker.sock").exists(),
        "kubernetes_token_absent": not Path(
            "/var/run/secrets/kubernetes.io/serviceaccount/token"
        ).exists(),
        "audit_store_absent": not Path("/audit").exists(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    arguments = parser.parse_args()
    job = json.loads(arguments.job.read_text(encoding="utf-8"))
    execute_fixed_workload(job=job, input_root=arguments.input, workspace_root=arguments.workspace)


if __name__ == "__main__":
    main()
