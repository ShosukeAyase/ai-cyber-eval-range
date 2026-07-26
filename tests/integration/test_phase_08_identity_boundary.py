from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from cyber_eval.identity import (
    AuthenticationStrength,
    AuthorizationContext,
    DeterministicOidcVerifier,
    DeterministicSpiffeVerifier,
    DevicePosture,
    EnvironmentClass,
    HumanRole,
    HumanTokenClaims,
    IdentityAuditOutcome,
    IdentityBoundary,
    InMemoryIdentityAuditSink,
    InMemoryReplayCache,
    InMemoryRevocationRegistry,
    PamElevationGrant,
    SyntheticOidcIssuer,
    TrustDomain,
)
from cyber_eval.identity.errors import (
    ActorSpoofingError,
    IdentityAuthorizationError,
    SeparationOfDutiesError,
)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)
KEY = b"phase-08-synthetic-key-material-32-bytes-minimum"
ISSUER = "https://idp.synthetic.invalid"
AUDIENCE = "cyber-eval-control-plane"


def build_boundary() -> tuple[IdentityBoundary, InMemoryIdentityAuditSink, FrozenClock]:
    clock = FrozenClock(NOW)
    revocations = InMemoryRevocationRegistry()
    audit = InMemoryIdentityAuditSink()
    boundary = IdentityBoundary(
        human_verifier=DeterministicOidcVerifier(
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            verification_keys={"synthetic-kid": KEY},
            clock=clock,
            replay_cache=InMemoryReplayCache(clock),
            revocations=revocations,
        ),
        workload_verifier=DeterministicSpiffeVerifier(
            clock=clock,
            revocations=revocations,
        ),
        audit_sink=audit,
        clock=clock,
    )
    return boundary, audit, clock


def token(
    *,
    subject: str,
    token_id: str,
    nonce: str,
    roles: frozenset[HumanRole],
    break_glass: bool = False,
) -> str:
    claims = HumanTokenClaims(
        issuer=ISSUER,
        audience=AUDIENCE,
        subject=subject,
        token_id=token_id,
        nonce=nonce,
        issued_at=NOW - timedelta(seconds=5),
        not_before=NOW - timedelta(seconds=5),
        expires_at=NOW + timedelta(minutes=5),
        roles=roles,
        trust_domain=TrustDomain.MANAGEMENT,
        engagement_ids=frozenset({"eng-phase08"}),
        device_posture=DevicePosture.COMPLIANT,
        authentication_strength=(
            AuthenticationStrength.BREAK_GLASS_MFA
            if break_glass
            else AuthenticationStrength.PHISHING_RESISTANT_MFA
        ),
        break_glass=break_glass,
    )
    return SyntheticOidcIssuer(
        issuer=ISSUER,
        key_id="synthetic-kid",
        signing_key=KEY,
    ).issue(claims)


def test_request_body_actor_id_cannot_spoof_verified_identity() -> None:
    boundary, audit, _ = build_boundary()
    with pytest.raises(ActorSpoofingError):
        boundary.authenticate_human(
            token(
                subject="verified-user",
                token_id="token-1",
                nonce="nonce-1",
                roles=frozenset({HumanRole.REQUESTER}),
            ),
            request_body_actor_id="admin-from-request-body",
        )
    assert audit.events()[-1].outcome is IdentityAuditOutcome.DENIED


def test_state_change_uses_verified_principal_and_abac_context() -> None:
    boundary, audit, _ = build_boundary()
    principal = boundary.authenticate_human(
        token(
            subject="requester",
            token_id="token-2",
            nonce="nonce-2",
            roles=frozenset({HumanRole.REQUESTER}),
        )
    )
    context = AuthorizationContext(
        principal=principal,
        engagement_id="eng-phase08",
        action="engagement.create",
        environment=EnvironmentClass.STAGING,
        device_posture=DevicePosture.COMPLIANT,
    )
    assert (
        boundary.authorize_state_change(
            context,
            required_roles={HumanRole.REQUESTER},
        )
        is principal
    )
    assert audit.events()[-1].event_type == "state_change.authorize"


def test_role_escalation_and_engagement_crossing_are_denied() -> None:
    boundary, _, _ = build_boundary()
    principal = boundary.authenticate_human(
        token(
            subject="requester",
            token_id="token-3",
            nonce="nonce-3",
            roles=frozenset({HumanRole.REQUESTER}),
        )
    )
    base = AuthorizationContext(
        principal=principal,
        engagement_id="eng-phase08",
        action="approval.decide",
        environment=EnvironmentClass.STAGING,
        device_posture=DevicePosture.COMPLIANT,
    )
    with pytest.raises(IdentityAuthorizationError, match="required role"):
        boundary.authorize_state_change(base, required_roles={HumanRole.APPROVER})
    with pytest.raises(IdentityAuthorizationError, match="engagement"):
        boundary.authorize_state_change(
            replace(base, engagement_id="eng-other"),
            required_roles={HumanRole.REQUESTER},
        )


def test_self_approval_is_denied_at_identity_level() -> None:
    boundary, _, _ = build_boundary()
    principal = boundary.authenticate_human(
        token(
            subject="dual-role-user",
            token_id="token-4",
            nonce="nonce-4",
            roles=frozenset({HumanRole.REQUESTER, HumanRole.APPROVER}),
        )
    )
    with pytest.raises(SeparationOfDutiesError, match="self approval"):
        boundary.require_independent_approval(
            requester=principal,
            approver=principal,
            engagement_id="eng-phase08",
        )


def test_independent_requester_and_approver_are_accepted() -> None:
    boundary, _, _ = build_boundary()
    requester = boundary.authenticate_human(
        token(
            subject="requester",
            token_id="token-5",
            nonce="nonce-5",
            roles=frozenset({HumanRole.REQUESTER}),
        )
    )
    approver = boundary.authenticate_human(
        token(
            subject="approver",
            token_id="token-6",
            nonce="nonce-6",
            roles=frozenset({HumanRole.APPROVER}),
        )
    )
    boundary.require_independent_approval(
        requester=requester,
        approver=approver,
        engagement_id="eng-phase08",
    )


def test_pam_elevation_requires_ticket_two_approvers_and_binding() -> None:
    boundary, _, _ = build_boundary()
    principal = boundary.authenticate_human(
        token(
            subject="operator",
            token_id="token-7",
            nonce="nonce-7",
            roles=frozenset({HumanRole.REQUESTER}),
        )
    )
    grant = PamElevationGrant(
        grant_id="elev-1",
        principal_id="operator",
        role=HumanRole.SECURITY_OPERATOR,
        engagement_id="eng-phase08",
        ticket_id="SEC-42",
        approved_by=("approver-a", "approver-b"),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=10),
    )
    context = AuthorizationContext(
        principal=principal,
        engagement_id="eng-phase08",
        action="emergency-stop.clear",
        environment=EnvironmentClass.STAGING,
        device_posture=DevicePosture.COMPLIANT,
        elevation_grant=grant,
    )
    boundary.authorize_state_change(
        context,
        required_roles={HumanRole.SECURITY_OPERATOR},
    )
    with pytest.raises(IdentityAuthorizationError, match="two independent"):
        boundary.authorize_state_change(
            replace(context, elevation_grant=replace(grant, approved_by=("same", "same"))),
            required_roles={HumanRole.SECURITY_OPERATOR},
        )


def test_break_glass_use_creates_high_priority_audit_event() -> None:
    boundary, audit, _ = build_boundary()
    principal = boundary.authenticate_human(
        token(
            subject="break-glass-user",
            token_id="token-8",
            nonce="nonce-8",
            roles=frozenset({HumanRole.SECURITY_OPERATOR}),
            break_glass=True,
        )
    )
    boundary.authorize_state_change(
        AuthorizationContext(
            principal=principal,
            engagement_id="eng-phase08",
            action="emergency-stop.activate",
            environment=EnvironmentClass.PRODUCTION,
            device_posture=DevicePosture.COMPLIANT,
        ),
        required_roles={HumanRole.SECURITY_OPERATOR},
    )
    assert any(event.event_type == "break_glass.use" for event in audit.events())
