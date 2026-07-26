"""Generate deterministic Phase 07 assurance evidence without changing system state."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class Check:
    check_id: str
    area: str
    status: str
    severity_if_failed: str
    evidence: str
    remediation: str


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _workflow_actions() -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if "uses:" not in stripped:
                continue
            value = stripped.split("uses:", maxsplit=1)[1].strip()
            if value.startswith("./") or "@" not in value:
                continue
            findings.append((path.relative_to(ROOT).as_posix(), value))
    return findings


def _has_executable_supply_chain_gate() -> bool:
    patterns = ("cosign verify", "in-toto", "slsa provenance", "sbom")
    for root_name in ("scripts", ".github/workflows"):
        root = ROOT / root_name
        for path in root.rglob("*"):
            if not path.is_file() or path.name == "run_phase7_assurance.py":
                continue
            try:
                text = path.read_text(encoding="utf-8").lower()
            except (UnicodeDecodeError, OSError):
                continue
            if any(pattern in text for pattern in patterns):
                return True
    return False


def _check(
    check_id: str,
    area: str,
    status: str,
    severity: str,
    evidence: str,
    remediation: str,
) -> Check:
    return Check(check_id, area, status, severity, evidence, remediation)


def build_checks() -> list[Check]:
    actions = _workflow_actions()
    unpinned = [
        f"{path}:{action}"
        for path, action in actions
        if not FULL_SHA.fullmatch(action.rsplit("@", 1)[1])
    ]
    lockfiles = ("requirements.lock", "requirements.txt", "uv.lock", "poetry.lock")
    pyproject = _text("pyproject.toml")
    policy = _text("src/cyber_eval/policy_adapter.py")
    store = _text("src/cyber_eval/store.py")
    runner = _text("src/cyber_eval/runner/podman.py")
    model = _text("src/cyber_eval/agent/model_client.py")
    approval = _text("src/cyber_eval/approval_service.py")
    emergency = _text("src/cyber_eval/emergency_stop.py")
    hardcoded_facts = all(
        token in policy
        for token in (
            "manifest_valid=True",
            "policy_version_current=True",
            "within_limits=True",
            "destination_matches=True",
        )
    )
    return [
        _check(
            "AUTH-001",
            "IAM",
            "FAIL",
            "high",
            "Public services accept caller-supplied actor_id strings; no external identity "
            "verification implementation exists.",
            "Add phishing-resistant authentication, workload identity, signed tokens, role "
            "binding, and authorization independent of caller input.",
        ),
        _check(
            "AUD-001",
            "Audit trail",
            "FAIL",
            "high",
            "Audit events share the local SQLite database and have no external signature, "
            "monotonic counter, or WORM retention.",
            "Send events to an independently administered append-only service and WORM store; "
            "sign batches and use trusted time.",
        ),
        _check(
            "POL-001",
            "Policy Engine",
            "FAIL" if hardcoded_facts else "PASS",
            "high",
            "The adapter supplies authorization facts as constants and executes the Python stub "
            "instead of the Rego policy bundle.",
            "Use an independent policy decision point, signed bundles, and authoritative fact "
            "providers; test stale and malformed bundles.",
        ),
        _check(
            "TOOL-001",
            "Tool Gateway",
            "FAIL",
            "high",
            "The gateway is a mock returning accepted_no_execution; no production adapter "
            "identity, destination resolver, or authenticated result channel exists.",
            "Implement narrow adapters with workload identity, semantic parameters, trusted "
            "destination resolution, signed receipts, and output validation.",
        ),
        _check(
            "APR-001",
            "Human Approval",
            "FAIL"
            if "requested_by == actor_id" in approval and "role" not in approval.lower()
            else "PASS",
            "high",
            "Self-approval is blocked, but role, organization identity, signed evidence, and "
            "anti-replay nonce are not enforced by external IAM.",
            "Bind approvals to authenticated roles, signed requests, nonce/audience/expiry, and "
            "dual control for high-risk actions.",
        ),
        _check(
            "KILL-001",
            "Kill Switch",
            "FAIL" if "LocalControlPlaneStore" in emergency else "PASS",
            "high",
            "The Kill Switch shares the Control Plane process and SQLite trust domain; Runner "
            "enforcement requires an in-process monitor.",
            "Deploy an independent stop controller and network isolation path with separate "
            "identity, administration, heartbeat, and runtime authority.",
        ),
        _check(
            "RUN-001",
            "Runner isolation",
            "FAIL" if "--network=none" in runner and "seccomp" not in runner.lower() else "PASS",
            "high",
            "Rootless Podman uses the same laptop and a host bind mount; no explicit seccomp, "
            "MAC profile, microVM boundary, or independent escape test is configured.",
            "Use dedicated VM/microVM hosts, explicit seccomp/MAC profiles, immutable hosts, and "
            "independent escape and host-compromise testing.",
        ),
        _check(
            "NET-001",
            "Network isolation",
            "FAIL",
            "high",
            "Runner network=none is tested, but no independent firewall/sensor or continuous "
            "route/DNS monitor exists. Model egress is restricted by code constant only.",
            "Enforce egress at a separate layer, remove default routes, use a controlled proxy, "
            "continuously verify policy, and stop on monitoring loss.",
        ),
        _check(
            "SEC-001",
            "Secret management",
            "FAIL" if "OPENAI_API_KEY" in model and "os.environ" in model else "PASS",
            "high",
            "Provider authentication uses a process environment variable; the Credential Broker "
            "is metadata-only and no KMS/HSM-backed issuance exists.",
            "Use a KMS/HSM-backed broker, workload identity, short-lived credentials, direct "
            "adapter delivery, rotation, revocation, and output redaction.",
        ),
        _check(
            "SCM-001",
            "Supply chain",
            "FAIL" if unpinned else "PASS",
            "high",
            "GitHub Actions use mutable tags: " + "; ".join(unpinned[:8]),
            "Pin actions to full commit SHAs and enforce repository SHA-pinning policy.",
        ),
        _check(
            "SCM-002",
            "Supply chain",
            "FAIL" if not any((ROOT / name).exists() for name in lockfiles) else "PASS",
            "high",
            "No hash-bearing dependency lockfile exists; build requirements are ranges and CI "
            "installs from the public package index.",
            "Use an internal mirror, hash-locked dependencies, offline build inputs, and "
            "reproducible build records.",
        ),
        _check(
            "SCM-003",
            "Supply chain",
            "PASS" if _has_executable_supply_chain_gate() else "FAIL",
            "high",
            "No executable verification gate for image/scenario signatures, provenance, or SBOM "
            "is present.",
            "Generate SBOM/provenance, sign images and scenario bundles, and verify approved "
            "identities before use.",
        ),
        _check(
            "AI-001",
            "Model governance",
            "FAIL" if 'DEFAULT_PINNED_MODEL = "gpt-5.6-sol"' in model else "PASS",
            "high",
            "The code labels gpt-5.6-sol as pinned, but it is a durable model identifier rather "
            "than a dated immutable snapshot.",
            "Use an immutable provider snapshot when available, or gate provider changes through "
            "signed configuration, regression evaluation, and rollback criteria.",
        ),
        _check(
            "AI-002",
            "Prompt injection",
            "PASS",
            "medium",
            "Closed schemas, no provider tools, object-ID proposals, secret redaction, evidence "
            "binding, and adversarial tests are present.",
            "Add continuous live-model red-team evaluations in private CI and maintain "
            "model-version-specific baselines.",
        ),
        _check(
            "RNG-001",
            "Scenario safety",
            "FAIL" if any((ROOT / "range-scenarios").glob("*/answer-key.json")) else "PASS",
            "high",
            "Answer keys are public and scenario bundles are unsigned, weakening scoring and "
            "release integrity.",
            "Move keys to a private grader and require signed reviewed scenario artifacts with "
            "provenance and secret/PII scanning.",
        ),
        _check(
            "ROE-001",
            "Legal authorization and ROE",
            "FAIL",
            "high",
            "Scope/ROE are local database objects; target ownership, jurisdiction, counsel "
            "approval, signed authorization, and consent evidence are not implemented.",
            "Require signed authorization packages, ownership verification, legal/data review, "
            "expiry, revocation, and independent approval.",
        ),
        _check(
            "RES-001",
            "Recovery and resilience",
            "FAIL",
            "high",
            "The Control Plane is one process and SQLite database with no HA, protected backup, "
            "restore drill, disaster recovery, or rollback protection.",
            "Define RTO/RPO, deploy redundant services, protect backups, perform restore drills, "
            "and detect rollback or cloned databases.",
        ),
        _check(
            "DOS-001",
            "Resource exhaustion",
            "PARTIAL",
            "medium",
            "Runner and Agent have local limits, but no global API budget, rate limiter, host "
            "quota, audit-growth bound, or provider cost circuit breaker exists.",
            "Add global quotas, concurrency controls, storage limits, cost budgets, backpressure, "
            "and emergency budget shutdown.",
        ),
        _check(
            "RST-001",
            "Reset and destruction",
            "PARTIAL",
            "medium",
            "Local roots are removed and reset digests are tested, but snapshots, backups, crash "
            "remnants, and cryptographic erasure are not covered.",
            "Add inventory-backed destruction, backup exclusions, key destruction, crash cleanup, "
            "and independent post-destruction verification.",
        ),
        _check(
            "CFG-001",
            "Build configuration",
            "PARTIAL" if "setuptools>=68,<80" in pyproject else "PASS",
            "medium",
            "Runtime dependencies are empty and dev versions exact, but build requirements remain "
            "ranged and unhashed.",
            "Pin and hash build backend artifacts through the internal supply-chain process.",
        ),
        _check(
            "AUD-002",
            "Audit trail",
            "FAIL" if "hash" not in store.lower() and "signature" not in store.lower() else "PASS",
            "high",
            "Audit records have no cryptographic integrity chain and rely on local wall-clock "
            "timestamps.",
            "Add chained digests, external signatures, trusted timestamps, sequence numbers, and "
            "verification tooling.",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/assurance/phase7-assurance-evidence.json",
    )
    args = parser.parse_args()
    checks = build_checks()
    summary = {
        "pass": sum(item.status == "PASS" for item in checks),
        "partial": sum(item.status == "PARTIAL" for item in checks),
        "fail": sum(item.status == "FAIL" for item in checks),
        "high_or_critical_unresolved": sum(
            item.status != "PASS" and item.severity_if_failed in {"high", "critical"}
            for item in checks
        ),
    }
    document = {
        "schema_version": "1.0",
        "reviewed_commit": "a6ebab812c0047395fb1c54af4d2d244f7e0ac3f",
        "decision": "NO-GO" if summary["high_or_critical_unresolved"] else "GO",
        "summary": summary,
        "checks": [asdict(item) for item in checks],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": document["decision"], **summary}, sort_keys=True))


if __name__ == "__main__":
    main()
