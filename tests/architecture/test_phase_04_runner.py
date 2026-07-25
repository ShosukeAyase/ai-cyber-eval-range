from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

from cyber_eval.runner.contracts import RunnerJobRequest, RunnerLimits
from cyber_eval.runner.podman import PodmanCommandBuilder
from tests.harness.runner import runner_harness, runner_request

ROOT = Path(__file__).resolve().parents[2]


def test_phase_04_required_files_exist() -> None:
    required = {
        "docs/design/isolated-runner-mvp.md",
        ".github/workflows/phase-04-runner.yml",
        ".containerignore",
        "src/cyber_eval/runner/coordinator.py",
        "src/cyber_eval/runner/podman.py",
        "src/cyber_eval/runner/workload.py",
        "tests/integration/test_isolated_runner_mvp.py",
        "scripts/live_runner_smoke.py",
        "scripts/finalize_phase4.py",
        "scripts/complete_phase4_local.ps1",
    }
    assert not sorted(path for path in required if not (ROOT / path).exists())
    plan_candidates = {
        ROOT / "docs/exec-plans/active/phase-04-isolated-runner-mvp.md",
        ROOT / "docs/exec-plans/completed/phase-04-isolated-runner-mvp.md",
    }
    assert sum(path.exists() for path in plan_candidates) == 1


def test_runner_api_has_no_arbitrary_destination_or_command_fields() -> None:
    names = {field.name for field in fields(RunnerJobRequest)}
    assert names.isdisjoint({"url", "ip", "hostname", "command", "shell", "endpoint", "path"})


def test_podman_plan_enforces_isolation_and_resource_limits(tmp_path) -> None:
    app, coordinator, _, _ = runner_harness(tmp_path)
    spec = coordinator._authorize(
        "eng-control-mvp",
        "operator-local",
        _approved_id(app),
        runner_request("job-plan-check"),
    )
    arguments = PodmanCommandBuilder().create(
        spec,
        container_name="ce-job-plan-check",
        job_path=tmp_path / "job.json",
    )
    joined = " ".join(arguments)
    for required in [
        "--pull=never",
        "--network=none",
        "--pid=private",
        "--ipc=none",
        "--uts=private",
        "--cgroupns=private",
        "--no-hosts",
        "--no-hostname",
        "--http-proxy=false",
        "--image-volume=ignore",
        "--no-healthcheck",
        "--restart=no",
        "--log-driver=none",
        "--read-only",
        "--read-only-tmpfs=false",
        "--user=65532:65532",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--cpus=1.0",
        "--memory=256m",
        "--pids-limit=64",
        "--ulimit=fsize=",
        "--ulimit=nofile=",
        "--tmpfs=/workspace:",
        "dst=/input,ro=true",
        "dst=/job.json,ro=true",
    ]:
        assert required in joined
    for forbidden in [
        "--privileged",
        "--network=host",
        "--pid=host",
        "/var/run/docker.sock",
        "serviceaccount/token",
        "169.254.169.254",
        ".sqlite",
        "/audit",
    ]:
        assert forbidden not in joined
    assert joined.count("--tmpfs=") == 1
    app.close("eng-control-mvp")


def test_runner_limits_reject_unbounded_profiles() -> None:
    with pytest.raises(ValueError):
        RunnerLimits(memory_mib=2048)
    with pytest.raises(ValueError):
        RunnerLimits(timeout_seconds=0)
    with pytest.raises(ValueError):
        RunnerLimits(pids=1000)


def test_runner_source_does_not_use_shell_strings() -> None:
    text = (ROOT / "src/cyber_eval/runner/podman.py").read_text()
    assert "shell=False" in text
    assert "shell=True" not in text
    assert "--pull=never" in text
    assert "Sequence[str]" in text


def _approved_id(app) -> str:
    from tests.harness.runner import approve_runner_start

    return approve_runner_start(app, "apr-plan-start")


def test_offline_runner_image_has_no_package_or_network_build_step() -> None:
    text = (ROOT / "runner-image/Containerfile").read_text()
    assert "ARG BASE_IMAGE" in text
    assert "USER 65532:65532" in text
    assert "COPY src/cyber_eval" in text
    for forbidden in ["RUN ", "curl ", "wget ", "pip install", "apt ", "dnf ", "apk "]:
        assert forbidden not in text
    ignore = (ROOT / ".containerignore").read_text()
    assert ignore.startswith("*\n")
    assert "!src/cyber_eval/**" in ignore
    script = (ROOT / "scripts/build_phase4_runner_image.ps1").read_text()
    assert "--pull-never" in script
    assert "--network=none" in script
