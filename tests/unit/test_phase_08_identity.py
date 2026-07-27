from __future__ import annotations

import base64
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from cyber_eval.identity import (
    AuthenticationStrength,
    DeterministicOidcVerifier,
    DeterministicSpiffeVerifier,
    DevicePosture,
    HumanRole,
    HumanTokenClaims,
    InMemoryReplayCache,
    InMemoryRevocationRegistry,
    SyntheticOidcIssuer,
    SyntheticSvid,
    TrustDomain,
)
from cyber_eval.identity.errors import (
    IdentityClaimError,
    IdentityProviderUnavailableError,
    IdentityReplayError,
    IdentityRevokedError,
    InvalidIdentityTokenError,
    WorkloadIdentityUnavailableError,
)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def set(self, now: datetime) -> None:
        self._now = now


NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
KEY = b"phase-08-synthetic-key-material-32-bytes-minimum"
ISSUER = "https://idp.synthetic.invalid"
AUDIENCE = "cyber-eval-control-plane"


def claims(**changes: object) -> HumanTokenClaims:
    base = HumanTokenClaims(
        issuer=ISSUER,
        audience=AUDIENCE,
        subject="user-requester",
        token_id="token-001",
        nonce="nonce-001",
        issued_at=NOW - timedelta(seconds=5),
        not_before=NOW - timedelta(seconds=5),
        expires_at=NOW + timedelta(minutes=5),
        roles=frozenset({HumanRole.REQUESTER}),
        trust_domain=TrustDomain.MANAGEMENT,
        engagement_ids=frozenset({"eng-phase08"}),
        device_posture=DevicePosture.COMPLIANT,
        authentication_strength=AuthenticationStrength.PHISHING_RESISTANT_MFA,
    )
    return replace(base, **changes)


def verifier(
    clock: FrozenClock,
    *,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    available: bool = True,
    revocations: InMemoryRevocationRegistry | None = None,
) -> DeterministicOidcVerifier:
    registry = revocations or InMemoryRevocationRegistry()
    return DeterministicOidcVerifier(
        expected_issuer=issuer,
        expected_audience=audience,
        verification_keys={"synthetic-kid": KEY},
        clock=clock,
        replay_cache=InMemoryReplayCache(clock),
        revocations=registry,
        available=available,
    )


def issue(value: HumanTokenClaims) -> str:
    return SyntheticOidcIssuer(
        issuer=value.issuer,
        key_id="synthetic-kid",
        signing_key=KEY,
    ).issue(value)


def test_valid_human_token_returns_verified_principal() -> None:
    clock = FrozenClock(NOW)
    principal = verifier(clock).verify(issue(claims()))
    assert principal.principal_id == "user-requester"
    assert principal.roles == frozenset({HumanRole.REQUESTER})
    assert principal.authentication_strength is AuthenticationStrength.PHISHING_RESISTANT_MFA


@pytest.mark.parametrize(
    ("claim_changes", "message"),
    [
        ({"issuer": "https://wrong.invalid"}, "issuer"),
        ({"audience": "wrong-audience"}, "audience"),
        ({"expires_at": NOW}, "expired"),
        ({"not_before": NOW + timedelta(minutes=2)}, "not active"),
        ({"issued_at": NOW + timedelta(minutes=2)}, "future"),
    ],
)
def test_invalid_temporal_and_binding_claims_fail_closed(
    claim_changes: dict[str, object],
    message: str,
) -> None:
    clock = FrozenClock(NOW)
    token = issue(claims(**claim_changes))
    with pytest.raises(IdentityClaimError, match=message):
        verifier(clock).verify(token)


def test_wrong_verifier_issuer_and_audience_fail_closed() -> None:
    clock = FrozenClock(NOW)
    token = issue(claims())
    with pytest.raises(IdentityClaimError, match="issuer"):
        verifier(clock, issuer="https://another.invalid").verify(token)
    with pytest.raises(IdentityClaimError, match="audience"):
        verifier(clock, audience="another-service").verify(token)


def test_unsigned_or_tampered_token_is_rejected() -> None:
    clock = FrozenClock(NOW)
    token = issue(claims())
    header_segment, payload_segment, signature_segment = token.split(".")
    header = json.loads(base64.urlsafe_b64decode(header_segment + "=="))
    header["alg"] = "none"
    unsigned_header = (
        base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode())
        .rstrip(b"=")
        .decode()
    )
    with pytest.raises(InvalidIdentityTokenError, match="unsupported or unsigned"):
        verifier(clock).verify(f"{unsigned_header}.{payload_segment}.{signature_segment}")

    tampered_payload = payload_segment[:-1] + ("A" if payload_segment[-1] != "A" else "B")
    with pytest.raises(InvalidIdentityTokenError):
        verifier(clock).verify(f"{header_segment}.{tampered_payload}.{signature_segment}")


def test_nonce_replay_is_rejected() -> None:
    clock = FrozenClock(NOW)
    selected = verifier(clock)
    token = issue(claims())
    selected.verify(token)
    with pytest.raises(IdentityReplayError):
        selected.verify(token)


def test_revoked_user_and_token_are_rejected() -> None:
    clock = FrozenClock(NOW)
    registry = InMemoryRevocationRegistry()
    registry.revoke_principal("user-requester")
    with pytest.raises(IdentityRevokedError):
        verifier(clock, revocations=registry).verify(issue(claims()))

    second = InMemoryRevocationRegistry()
    second.revoke_credential("token-001")
    with pytest.raises(IdentityRevokedError):
        verifier(clock, revocations=second).verify(issue(claims(nonce="nonce-002")))


def test_idp_outage_fails_closed() -> None:
    clock = FrozenClock(NOW)
    with pytest.raises(IdentityProviderUnavailableError):
        verifier(clock, available=False).verify(issue(claims()))


def test_non_phishing_resistant_human_authentication_is_rejected() -> None:
    clock = FrozenClock(NOW)
    token = issue(claims(authentication_strength=AuthenticationStrength.WORKLOAD_MTLS))
    with pytest.raises(IdentityClaimError, match="phishing resistant"):
        verifier(clock).verify(token)


def test_workload_verifier_binds_identity_audience_and_trust_domain() -> None:
    clock = FrozenClock(NOW)
    selected = DeterministicSpiffeVerifier(
        clock=clock,
        revocations=InMemoryRevocationRegistry(),
    )
    svid = SyntheticSvid(
        spiffe_id="spiffe://control/service/tool-gateway",
        serial_number="serial-001",
        audience="policy-service",
        trust_domain=TrustDomain.CONTROL,
        issued_at=NOW - timedelta(minutes=1),
        not_before=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
    )
    principal = selected.verify(
        svid,
        expected_audience="policy-service",
        expected_trust_domain=TrustDomain.CONTROL,
        expected_spiffe_id="spiffe://control/service/tool-gateway",
    )
    assert principal.principal_id == svid.spiffe_id
    assert principal.trust_domain is TrustDomain.CONTROL

    with pytest.raises(IdentityClaimError, match="another workload"):
        selected.verify(
            svid,
            expected_audience="policy-service",
            expected_trust_domain=TrustDomain.CONTROL,
            expected_spiffe_id="spiffe://control/service/scheduler",
        )
    with pytest.raises(IdentityClaimError, match="crossing"):
        selected.verify(
            svid,
            expected_audience="policy-service",
            expected_trust_domain=TrustDomain.EXECUTION,
        )
    with pytest.raises(IdentityClaimError, match="audience"):
        selected.verify(
            svid,
            expected_audience="evidence-service",
            expected_trust_domain=TrustDomain.CONTROL,
        )


def test_workload_api_outage_and_revocation_fail_closed() -> None:
    clock = FrozenClock(NOW)
    svid = SyntheticSvid(
        spiffe_id="spiffe://execution/service/runner",
        serial_number="serial-002",
        audience="control-plane",
        trust_domain=TrustDomain.EXECUTION,
        issued_at=NOW - timedelta(minutes=1),
        not_before=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
    )
    unavailable = DeterministicSpiffeVerifier(
        clock=clock,
        revocations=InMemoryRevocationRegistry(),
        available=False,
    )
    with pytest.raises(WorkloadIdentityUnavailableError):
        unavailable.verify(
            svid,
            expected_audience="control-plane",
            expected_trust_domain=TrustDomain.EXECUTION,
        )

    revocations = InMemoryRevocationRegistry()
    revocations.revoke_credential("serial-002")
    revoked = DeterministicSpiffeVerifier(clock=clock, revocations=revocations)
    with pytest.raises(IdentityRevokedError):
        revoked.verify(
            svid,
            expected_audience="control-plane",
            expected_trust_domain=TrustDomain.EXECUTION,
        )
