"""Fail-closed live OIDC token verification through RFC 7662 introspection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol, TypeVar

from cyber_eval.identity.contracts import (
    AuthenticationStrength,
    Clock,
    DevicePosture,
    HumanRole,
    PrincipalKind,
    TrustDomain,
    VerifiedPrincipal,
)
from cyber_eval.identity.errors import IdentityClaimError, IdentityRevokedError


_EnumT = TypeVar("_EnumT", bound=StrEnum)


class ReplayCache(Protocol):
    def consume(self, nonce: str, expires_at: datetime) -> None:
        """Record a nonce or raise when it has already been used."""


class OidcIntrospectionTransport(Protocol):
    def introspect(self, token: str) -> Mapping[str, object]:
        """Return one introspection response for the supplied bearer token."""


@dataclass(frozen=True, slots=True)
class OidcClaimNames:
    roles: str = "roles"
    trust_domain: str = "trust_domain"
    engagement_ids: str = "engagement_ids"
    device_posture: str = "device_posture"
    authentication_strength: str = "auth_strength"
    break_glass: str = "break_glass"


class LiveOidcIntrospectionVerifier:
    """Map a live introspection response to a verified human principal."""

    def __init__(
        self,
        *,
        expected_issuer: str,
        expected_audience: str,
        transport: OidcIntrospectionTransport,
        clock: Clock,
        replay_cache: ReplayCache,
        claim_names: OidcClaimNames = OidcClaimNames(),
        maximum_clock_skew: timedelta = timedelta(seconds=30),
    ) -> None:
        if not expected_issuer or not expected_audience:
            raise ValueError("expected OIDC issuer and audience are required")
        if maximum_clock_skew < timedelta(0):
            raise ValueError("maximum clock skew cannot be negative")
        self._expected_issuer = expected_issuer.rstrip("/")
        self._expected_audience = expected_audience
        self._transport = transport
        self._clock = clock
        self._replay_cache = replay_cache
        self._claim_names = claim_names
        self._maximum_clock_skew = maximum_clock_skew

    def verify(self, token: str) -> VerifiedPrincipal:
        document = self._transport.introspect(token)
        if document.get("active") is not True:
            raise IdentityRevokedError("identity provider reports token inactive")

        issuer = _required_string(document, "iss").rstrip("/")
        if issuer != self._expected_issuer:
            raise IdentityClaimError("OIDC issuer does not match the configured provider")
        audience = _audience(document.get("aud"))
        if self._expected_audience not in audience:
            raise IdentityClaimError("OIDC audience does not include the control plane")

        subject = _required_string(document, "sub")
        token_id = _required_string(document, "jti")
        nonce = _required_string(document, "nonce")
        issued_at = _timestamp(document.get("iat"), "iat")
        not_before = _timestamp(document.get("nbf"), "nbf")
        expires_at = _timestamp(document.get("exp"), "exp")
        now = self._clock.now()
        if issued_at > now + self._maximum_clock_skew:
            raise IdentityClaimError("OIDC token was issued in the future")
        if not_before > now + self._maximum_clock_skew:
            raise IdentityClaimError("OIDC token is not active yet")
        if expires_at <= now - self._maximum_clock_skew:
            raise IdentityClaimError("OIDC token is expired")
        if issued_at >= expires_at or not_before >= expires_at:
            raise IdentityClaimError("OIDC token validity interval is invalid")

        roles = frozenset(
            _enum_values(
                document.get(self._claim_names.roles),
                self._claim_names.roles,
                HumanRole,
            )
        )
        if not roles:
            raise IdentityClaimError("OIDC identity must contain at least one role")
        trust_domain = _enum_value(
            document.get(self._claim_names.trust_domain),
            self._claim_names.trust_domain,
            TrustDomain,
        )
        engagement_ids = _string_set(
            document.get(self._claim_names.engagement_ids),
            self._claim_names.engagement_ids,
        )
        device_posture = _enum_value(
            document.get(self._claim_names.device_posture),
            self._claim_names.device_posture,
            DevicePosture,
        )
        authentication_strength = _enum_value(
            document.get(self._claim_names.authentication_strength),
            self._claim_names.authentication_strength,
            AuthenticationStrength,
        )
        if authentication_strength not in {
            AuthenticationStrength.PHISHING_RESISTANT_MFA,
            AuthenticationStrength.BREAK_GLASS_MFA,
        }:
            raise IdentityClaimError("human authentication is not phishing resistant")
        break_glass = _required_bool(
            document.get(self._claim_names.break_glass),
            self._claim_names.break_glass,
        )
        if break_glass != (
            authentication_strength is AuthenticationStrength.BREAK_GLASS_MFA
        ):
            raise IdentityClaimError(
                "break-glass claim and authentication strength disagree"
            )

        self._replay_cache.consume(nonce, expires_at)
        return VerifiedPrincipal(
            principal_id=subject,
            kind=PrincipalKind.HUMAN,
            trust_domain=trust_domain,
            roles=roles,
            engagement_ids=engagement_ids,
            authenticated_at=issued_at,
            expires_at=expires_at,
            authentication_strength=authentication_strength,
            credential_id=token_id,
            device_posture=device_posture,
            break_glass=break_glass,
            attributes=(("issuer", issuer), ("audience", self._expected_audience)),
        )


def _required_string(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value:
        raise IdentityClaimError(f"{field} must be a non-empty string")
    return value


def _required_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise IdentityClaimError(f"{field} must be a boolean")
    return value


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise IdentityClaimError(f"{field} must be a numeric date")
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise IdentityClaimError(f"{field} is outside the supported range") from exc


def _audience(value: object) -> frozenset[str]:
    if isinstance(value, str) and value:
        return frozenset({value})
    return _string_set(value, "aud")


def _string_set(value: object, field: str) -> frozenset[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise IdentityClaimError(f"{field} must be a list of non-empty strings")
    return frozenset(value)


def _enum_value(value: object, field: str, enum_type: type[_EnumT]) -> _EnumT:
    if not isinstance(value, str) or not value:
        raise IdentityClaimError(f"{field} must be a non-empty string")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise IdentityClaimError(f"{field} contains an unsupported value") from exc


def _enum_values(value: object, field: str, enum_type: type[_EnumT]) -> list[_EnumT]:
    return [_enum_value(item, field, enum_type) for item in _string_set(value, field)]
