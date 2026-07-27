"""Collect live OIDC staging evidence without persisting bearer tokens or secrets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from cyber_eval.clock import SystemClock
from cyber_eval.identity.errors import (
    IdentityClaimError,
    IdentityProviderUnavailableError,
    IdentityReplayError,
    IdentityRevokedError,
)
from cyber_eval.identity.live_oidc import LiveOidcIntrospectionVerifier
from cyber_eval.identity.synthetic import InMemoryReplayCache
from cyber_eval.identity_adapters import UrlLibOidcIntrospectionTransport


@dataclass(frozen=True, slots=True)
class CaseResult:
    name: str
    status: str
    detail: str


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"required environment variable is missing: {name}")
    return value


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/phase-08/oidc"),
    )
    args = parser.parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    issuer = _required_env("PHASE8_OIDC_ISSUER")
    audience = _required_env("PHASE8_OIDC_AUDIENCE")
    endpoint = _required_env("PHASE8_OIDC_INTROSPECTION_ENDPOINT")
    client_id = _required_env("PHASE8_OIDC_INTROSPECTION_CLIENT_ID")
    client_secret = _required_env("PHASE8_OIDC_INTROSPECTION_CLIENT_SECRET")
    valid_token = _required_env("PHASE8_OIDC_VALID_TOKEN")
    rotated_key_token = _required_env("PHASE8_OIDC_ROTATED_KEY_TOKEN")
    expired_token = _required_env("PHASE8_OIDC_EXPIRED_TOKEN")
    revoked_token = _required_env("PHASE8_OIDC_REVOKED_TOKEN")
    outage_endpoint = _required_env("PHASE8_OIDC_OUTAGE_ENDPOINT")
    profile = os.environ.get("PHASE8_OIDC_PROFILE", "unspecified")

    clock = SystemClock()

    def verifier(
        selected_audience: str, selected_endpoint: str = endpoint
    ) -> LiveOidcIntrospectionVerifier:
        return LiveOidcIntrospectionVerifier(
            expected_issuer=issuer,
            expected_audience=selected_audience,
            transport=UrlLibOidcIntrospectionTransport(
                endpoint=selected_endpoint,
                client_id=client_id,
                client_secret=client_secret,
            ),
            clock=clock,
            replay_cache=InMemoryReplayCache(clock),
        )

    results: list[CaseResult] = []
    selected_verifier = verifier(audience)
    principal = selected_verifier.verify(valid_token)
    results.append(
        CaseResult(
            name="valid_token",
            status="pass",
            detail=f"verified principal {principal.principal_id}",
        )
    )

    try:
        selected_verifier.verify(valid_token)
    except IdentityReplayError:
        results.append(CaseResult("nonce_replay_denied", "pass", "replayed nonce rejected"))
    else:
        results.append(CaseResult("nonce_replay_denied", "fail", "replayed nonce accepted"))

    rotated_principal = verifier(audience).verify(rotated_key_token)
    results.append(
        CaseResult(
            name="signing_key_rotation_verified",
            status="pass",
            detail=f"rotated-key token verified for {rotated_principal.principal_id}",
        )
    )

    try:
        verifier("phase8-deliberately-wrong-audience").verify(valid_token)
    except IdentityClaimError:
        results.append(
            CaseResult("wrong_audience_denied", "pass", "audience mismatch rejected")
        )
    else:
        results.append(
            CaseResult("wrong_audience_denied", "fail", "audience mismatch accepted")
        )

    for name, token in (
        ("expired_token_denied", expired_token),
        ("revoked_token_denied", revoked_token),
    ):
        try:
            verifier(audience).verify(token)
        except (IdentityRevokedError, IdentityClaimError):
            results.append(CaseResult(name, "pass", "inactive or stale token rejected"))
        else:
            results.append(CaseResult(name, "fail", "inactive token accepted"))

    try:
        verifier(audience, outage_endpoint).verify(valid_token)
    except IdentityProviderUnavailableError:
        results.append(
            CaseResult("idp_outage_denied", "pass", "provider outage failed closed")
        )
    else:
        results.append(
            CaseResult("idp_outage_denied", "fail", "provider outage failed open")
        )

    status = "pass" if all(result.status == "pass" for result in results) else "fail"
    gate_eligible = profile == "enterprise-staging"
    evidence = {
        "schema_version": "1.0",
        "evidence_type": "live_oidc_staging",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": status,
        "gate_eligible": gate_eligible,
        "profile": profile,
        "issuer": issuer,
        "audience": audience,
        "introspection_endpoint": endpoint,
        "verified_principal_id": principal.principal_id,
        "verified_credential_id": principal.credential_id,
        "token_fingerprints": {
            "valid": _fingerprint(valid_token),
            "rotated_key": _fingerprint(rotated_key_token),
            "expired": _fingerprint(expired_token),
            "revoked": _fingerprint(revoked_token),
        },
        "tests": [asdict(result) for result in results],
        "secrets_persisted": False,
    }
    (output_dir / "oidc-staging-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
