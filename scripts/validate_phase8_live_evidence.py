"""Validate Phase 08 live-gate evidence content, not merely path existence."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class EvidenceValidationError(RuntimeError):
    pass


def _object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EvidenceValidationError(f"required evidence file is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceValidationError(f"evidence is not valid JSON: {path}") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise EvidenceValidationError(f"evidence must be a JSON object: {path}")
    return {str(key): item for key, item in value.items()}


def _require(value: bool, message: str) -> None:
    if not value:
        raise EvidenceValidationError(message)


def _tests_pass(document: Mapping[str, Any], evidence_name: str) -> None:
    tests = document.get("tests")
    _require(isinstance(tests, list) and bool(tests), f"{evidence_name} tests are missing")
    for item in tests:
        _require(isinstance(item, dict), f"{evidence_name} test entry is invalid")
        _require(item.get("status") == "pass", f"{evidence_name} contains a failed test")


def validate(oidc_dir: Path, spire_dir: Path, api_dir: Path) -> None:
    oidc = _object(oidc_dir / "oidc-staging-evidence.json")
    _require(oidc.get("evidence_type") == "live_oidc_staging", "OIDC evidence type is invalid")
    _require(oidc.get("status") == "pass", "OIDC staging evidence did not pass")
    _require(oidc.get("gate_eligible") is True, "OIDC evidence is not enterprise-staging eligible")
    _require(oidc.get("secrets_persisted") is False, "OIDC evidence reports persisted secrets")
    _tests_pass(oidc, "OIDC")
    required_oidc_tests = {
        "valid_token",
        "nonce_replay_denied",
        "signing_key_rotation_verified",
        "wrong_audience_denied",
        "expired_token_denied",
        "revoked_token_denied",
        "idp_outage_denied",
    }
    observed_oidc_tests = {
        str(item.get("name")) for item in oidc["tests"] if isinstance(item, dict)
    }
    _require(required_oidc_tests <= observed_oidc_tests, "OIDC evidence lacks required cases")

    spire = _object(spire_dir / "spire-mtls-staging-evidence.json")
    _require(
        spire.get("evidence_type") == "live_spire_mtls_staging",
        "SPIRE evidence type is invalid",
    )
    _require(spire.get("status") == "pass", "SPIRE/mTLS staging evidence did not pass")
    _require(spire.get("gate_eligible") is True, "SPIRE evidence is not staging eligible")
    _require(spire.get("private_keys_persisted") is False, "SPIRE evidence reports persisted keys")
    _tests_pass(spire, "SPIRE")
    required_spire_tests = {
        "server_ready",
        "agents_ready",
        "workload_svid_issued",
        "mtls_success",
        "foreign_identity_denied",
        "svid_rotation_observed",
        "revoked_svid_denied",
        "workload_api_outage_denied",
    }
    observed_spire_tests = {
        str(item.get("name")) for item in spire["tests"] if isinstance(item, dict)
    }
    _require(required_spire_tests <= observed_spire_tests, "SPIRE evidence lacks required cases")
    required_domains = {"control", "execution", "range", "evidence", "management"}
    domains = spire.get("logical_trust_domains")
    _require(isinstance(domains, list), "SPIRE logical trust domains are missing")
    _require(
        required_domains <= {str(item) for item in domains},
        "SPIRE trust-domain coverage is incomplete",
    )

    coverage = _object(api_dir / "coverage-report.json")
    _require(
        coverage.get("evidence_type") == "static_complete_mediation_coverage",
        "API coverage evidence type is invalid",
    )
    _require(coverage.get("status") == "pass", "API coverage evidence did not pass")
    _require(coverage.get("coverage_percent") == 100, "state-changing API coverage is not 100%")
    _require(
        coverage.get("caller_asserted_actor_id_count") == 0,
        "caller-asserted actor_id remains at the production boundary",
    )
    _require(
        coverage.get("missing_operations") == [],
        "state-changing operations are missing from the production gateway",
    )
    _require(
        coverage.get("unexpected_operations") == [],
        "unexpected operations exist in API coverage",
    )
    _require(
        coverage.get("deployment_review_required") is True,
        "API coverage must retain the independent deployment review requirement",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oidc-dir", type=Path, required=True)
    parser.add_argument("--spire-dir", type=Path, required=True)
    parser.add_argument("--api-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate(args.oidc_dir, args.spire_dir, args.api_dir)
    except EvidenceValidationError as exc:
        print(f"Phase 08 evidence validation failed: {exc}")
        return 1
    print("Phase 08 live evidence content validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
