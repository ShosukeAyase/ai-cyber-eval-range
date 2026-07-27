from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import pytest

from cyber_eval.domain import WriteOperation
from cyber_eval.identity import (
    AuthenticationStrength,
    DevicePosture,
    EnvironmentClass,
    HumanRole,
    IdentityBoundary,
    InMemoryIdentityAuditSink,
    InMemoryReplayCache,
    InMemoryRevocationRegistry,
    TrustDomain,
)
from cyber_eval.identity.contracts import PrincipalKind, VerifiedPrincipal
from cyber_eval.identity.errors import (
    IdentityClaimError,
    IdentityReplayError,
    IdentityRevokedError,
)
from cyber_eval.identity.live_oidc import LiveOidcIntrospectionVerifier
from cyber_eval.identity.production_gateway import (
    ProductionIdentityGateway,
    production_state_change_bindings,
)
from cyber_eval.identity.synthetic import DeterministicSpiffeVerifier
from cyber_eval.identity_adapters import UrlLibOidcIntrospectionTransport


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


class FrozenClock:
    def now(self) -> datetime:
        return NOW


class StaticTransport:
    def __init__(self, response: Mapping[str, object]) -> None:
        self._response = response

    def introspect(self, token: str) -> Mapping[str, object]:
        assert token
        return self._response


def response(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "active": True,
        "iss": "https://idp.example.test",
        "aud": ["cyber-eval-control-plane"],
        "sub": "requester",
        "jti": "token-live-1",
        "nonce": "nonce-live-1",
        "iat": (NOW - timedelta(seconds=5)).timestamp(),
        "nbf": (NOW - timedelta(seconds=5)).timestamp(),
        "exp": (NOW + timedelta(minutes=5)).timestamp(),
        "roles": ["requester"],
        "trust_domain": "management",
        "engagement_ids": ["eng-phase08"],
        "device_posture": "compliant",
        "auth_strength": "phishing_resistant_mfa",
        "break_glass": False,
    }
    value.update(changes)
    return value


def live_verifier(document: Mapping[str, object]) -> LiveOidcIntrospectionVerifier:
    clock = FrozenClock()
    return LiveOidcIntrospectionVerifier(
        expected_issuer="https://idp.example.test",
        expected_audience="cyber-eval-control-plane",
        transport=StaticTransport(document),
        clock=clock,
        replay_cache=InMemoryReplayCache(clock),
    )


def test_live_oidc_introspection_maps_verified_principal() -> None:
    principal = live_verifier(response()).verify("opaque-live-token")
    assert principal.principal_id == "requester"
    assert principal.kind is PrincipalKind.HUMAN
    assert principal.authentication_strength is AuthenticationStrength.PHISHING_RESISTANT_MFA


def test_live_oidc_introspection_fails_closed_for_inactive_and_wrong_audience() -> None:
    with pytest.raises(IdentityRevokedError):
        live_verifier(response(active=False)).verify("inactive-token")
    with pytest.raises(IdentityClaimError, match="audience"):
        live_verifier(response(aud=["another-service"])).verify("wrong-audience-token")


def test_live_oidc_introspection_rejects_nonce_replay() -> None:
    selected = live_verifier(response())
    selected.verify("opaque-live-token")
    with pytest.raises(IdentityReplayError):
        selected.verify("opaque-live-token")


def test_oidc_transport_requires_https_or_loopback_http() -> None:
    with pytest.raises(ValueError, match="HTTPS or loopback"):
        UrlLibOidcIntrospectionTransport(
            endpoint="http://idp.example.test/introspect",
            client_id="collector",
            client_secret="secret",
        )
    transport = UrlLibOidcIntrospectionTransport(
        endpoint="http://127.0.0.1:8080/introspect",
        client_id="collector",
        client_secret="secret",
    )
    assert transport.endpoint == "http://127.0.0.1:8080/introspect"


def principal(
    *,
    principal_id: str,
    kind: PrincipalKind,
    roles: frozenset[HumanRole] = frozenset(),
    trust_domain: TrustDomain = TrustDomain.MANAGEMENT,
) -> VerifiedPrincipal:
    return VerifiedPrincipal(
        principal_id=principal_id,
        kind=kind,
        trust_domain=trust_domain,
        roles=roles,
        engagement_ids=frozenset({"eng-phase08"}),
        authenticated_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        authentication_strength=(
            AuthenticationStrength.PHISHING_RESISTANT_MFA
            if kind is PrincipalKind.HUMAN
            else AuthenticationStrength.WORKLOAD_MTLS
        ),
        credential_id=f"credential-{principal_id}",
        device_posture=DevicePosture.COMPLIANT,
    )


class RejectHumanVerifier:
    def verify(self, token: str) -> VerifiedPrincipal:
        raise AssertionError(token)


def gateway() -> ProductionIdentityGateway:
    clock = FrozenClock()
    boundary = IdentityBoundary(
        human_verifier=RejectHumanVerifier(),
        workload_verifier=DeterministicSpiffeVerifier(
            clock=clock,
            revocations=InMemoryRevocationRegistry(),
        ),
        audit_sink=InMemoryIdentityAuditSink(),
        clock=clock,
    )
    return ProductionIdentityGateway(boundary)


def test_production_gateway_covers_every_write_operation() -> None:
    assert {binding.operation for binding in production_state_change_bindings()} == set(
        WriteOperation
    )


def test_production_gateway_mediates_human_and_workload_operations() -> None:
    selected = gateway()
    human = principal(
        principal_id="platform-admin",
        kind=PrincipalKind.HUMAN,
        roles=frozenset({HumanRole.PLATFORM_ADMIN}),
    )
    assert (
        selected.authorize(
            operation=WriteOperation.CREATE_ENGAGEMENT,
            principal=human,
            engagement_id="eng-phase08",
            environment=EnvironmentClass.STAGING,
            device_posture=DevicePosture.COMPLIANT,
        )
        is human
    )
    workload = principal(
        principal_id="spiffe://phase8.internal/execution/runner",
        kind=PrincipalKind.WORKLOAD,
        trust_domain=TrustDomain.EXECUTION,
    )
    assert (
        selected.authorize(
            operation=WriteOperation.START_RUNNER_JOB,
            principal=workload,
            engagement_id="eng-phase08",
            environment=EnvironmentClass.STAGING,
            device_posture=DevicePosture.COMPLIANT,
        )
        is workload
    )
