"""Deterministic identity fakes used only for Phase 08 local validation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

from cyber_eval.identity.contracts import (
    AuthenticationStrength,
    Clock,
    DevicePosture,
    HumanRole,
    HumanTokenClaims,
    PrincipalKind,
    SyntheticSvid,
    TrustDomain,
    VerifiedPrincipal,
)
from cyber_eval.identity.errors import (
    IdentityClaimError,
    IdentityProviderUnavailableError,
    IdentityReplayError,
    IdentityRevokedError,
    InvalidIdentityTokenError,
    WorkloadIdentityUnavailableError,
)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, TypeError) as exc:
        raise InvalidIdentityTokenError("invalid base64url token segment") from exc


def _json_object(segment: str) -> dict[str, Any]:
    try:
        value = json.loads(_b64url_decode(segment))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidIdentityTokenError("invalid token JSON") from exc
    if not isinstance(value, dict):
        raise InvalidIdentityTokenError("token segment must be a JSON object")
    return {str(key): item for key, item in value.items()}


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, int | float):
        raise IdentityClaimError(f"{field} must be a numeric date")
    return datetime.fromtimestamp(float(value), tz=UTC)


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise IdentityClaimError(f"{field} must be a non-empty string")
    return value


def _string_set(value: Any, field: str) -> frozenset[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise IdentityClaimError(f"{field} must be a list of non-empty strings")
    return frozenset(value)


class InMemoryReplayCache:
    """Single-use nonce cache with deterministic expiration."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._entries: dict[str, datetime] = {}
        self._lock = Lock()

    def consume(self, nonce: str, expires_at: datetime) -> None:
        now = self._clock.now()
        with self._lock:
            self._entries = {
                key: expiry for key, expiry in self._entries.items() if expiry > now
            }
            if nonce in self._entries:
                raise IdentityReplayError("identity nonce has already been consumed")
            self._entries[nonce] = expires_at


class InMemoryRevocationRegistry:
    """Deterministic principal and credential revocation registry."""

    def __init__(self) -> None:
        self._principals: set[str] = set()
        self._credentials: set[str] = set()
        self._lock = Lock()

    def revoke_principal(self, principal_id: str) -> None:
        with self._lock:
            self._principals.add(principal_id)

    def revoke_credential(self, credential_id: str) -> None:
        with self._lock:
            self._credentials.add(credential_id)

    def require_active(self, principal_id: str, credential_id: str) -> None:
        with self._lock:
            if principal_id in self._principals or credential_id in self._credentials:
                raise IdentityRevokedError("principal or credential is revoked")


class SyntheticOidcIssuer:
    """HS256 token issuer for tests; not a production IdP adapter."""

    def __init__(self, *, issuer: str, key_id: str, signing_key: bytes) -> None:
        if not issuer or not key_id or len(signing_key) < 32:
            raise ValueError("synthetic issuer requires issuer, key id, and a 32-byte key")
        self._issuer = issuer
        self._key_id = key_id
        self._signing_key = signing_key

    def issue(self, claims: HumanTokenClaims) -> str:
        if claims.issuer != self._issuer:
            raise ValueError("claims issuer does not match synthetic issuer")
        header = {"alg": "HS256", "kid": self._key_id, "typ": "JWT"}
        payload = {
            "iss": claims.issuer,
            "aud": claims.audience,
            "sub": claims.subject,
            "jti": claims.token_id,
            "nonce": claims.nonce,
            "iat": claims.issued_at.timestamp(),
            "nbf": claims.not_before.timestamp(),
            "exp": claims.expires_at.timestamp(),
            "principal_kind": PrincipalKind.HUMAN.value,
            "roles": sorted(role.value for role in claims.roles),
            "trust_domain": claims.trust_domain.value,
            "engagement_ids": sorted(claims.engagement_ids),
            "device_posture": claims.device_posture.value,
            "auth_strength": claims.authentication_strength.value,
            "break_glass": claims.break_glass,
        }
        header_segment = _b64url_encode(
            json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        payload_segment = _b64url_encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        signature = hmac.new(self._signing_key, signing_input, hashlib.sha256).digest()
        return f"{header_segment}.{payload_segment}.{_b64url_encode(signature)}"


class DeterministicOidcVerifier:
    """Fail-closed OIDC-shaped verifier for synthetic signed tokens."""

    def __init__(
        self,
        *,
        expected_issuer: str,
        expected_audience: str,
        verification_keys: Mapping[str, bytes],
        clock: Clock,
        replay_cache: InMemoryReplayCache,
        revocations: InMemoryRevocationRegistry,
        available: bool = True,
        maximum_clock_skew: timedelta = timedelta(seconds=30),
    ) -> None:
        self._expected_issuer = expected_issuer
        self._expected_audience = expected_audience
        self._verification_keys = dict(verification_keys)
        self._clock = clock
        self._replay_cache = replay_cache
        self._revocations = revocations
        self._available = available
        self._maximum_clock_skew = maximum_clock_skew

    def verify(self, token: str) -> VerifiedPrincipal:
        if not self._available:
            raise IdentityProviderUnavailableError("identity provider is unavailable")
        segments = token.split(".")
        if len(segments) != 3:
            raise InvalidIdentityTokenError("token must contain three segments")
        header = _json_object(segments[0])
        payload = _json_object(segments[1])
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise InvalidIdentityTokenError("unsupported or unsigned token")
        key_id = _string(header.get("kid"), "kid")
        key = self._verification_keys.get(key_id)
        if key is None:
            raise InvalidIdentityTokenError("unknown token signing key")
        signing_input = f"{segments[0]}.{segments[1]}".encode("ascii")
        expected_signature = hmac.new(key, signing_input, hashlib.sha256).digest()
        actual_signature = _b64url_decode(segments[2])
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise InvalidIdentityTokenError("token signature is invalid")

        issuer = _string(payload.get("iss"), "iss")
        audience = _string(payload.get("aud"), "aud")
        subject = _string(payload.get("sub"), "sub")
        token_id = _string(payload.get("jti"), "jti")
        nonce = _string(payload.get("nonce"), "nonce")
        issued_at = _timestamp(payload.get("iat"), "iat")
        not_before = _timestamp(payload.get("nbf"), "nbf")
        expires_at = _timestamp(payload.get("exp"), "exp")
        now = self._clock.now()

        if issuer != self._expected_issuer:
            raise IdentityClaimError("unexpected token issuer")
        if audience != self._expected_audience:
            raise IdentityClaimError("unexpected token audience")
        if payload.get("principal_kind") != PrincipalKind.HUMAN.value:
            raise IdentityClaimError("OIDC path accepts human principals only")
        if issued_at > now + self._maximum_clock_skew:
            raise IdentityClaimError("token issued-at time is in the future")
        if not_before > now + self._maximum_clock_skew:
            raise IdentityClaimError("token is not active yet")
        if expires_at <= now:
            raise IdentityClaimError("token is expired")
        if expires_at <= not_before:
            raise IdentityClaimError("token validity interval is invalid")

        try:
            roles = frozenset(
                HumanRole(item) for item in _string_set(payload.get("roles"), "roles")
            )
            trust_domain = TrustDomain(_string(payload.get("trust_domain"), "trust_domain"))
            engagement_ids = _string_set(payload.get("engagement_ids"), "engagement_ids")
            device_posture = DevicePosture(
                _string(payload.get("device_posture"), "device_posture")
            )
            auth_strength = AuthenticationStrength(
                _string(payload.get("auth_strength"), "auth_strength")
            )
        except ValueError as exc:
            raise IdentityClaimError("token contains an unsupported identity claim") from exc
        break_glass = payload.get("break_glass", False)
        if not isinstance(break_glass, bool):
            raise IdentityClaimError("break_glass must be boolean")
        permitted_strengths = {
            AuthenticationStrength.PHISHING_RESISTANT_MFA,
            AuthenticationStrength.BREAK_GLASS_MFA,
        }
        if auth_strength not in permitted_strengths:
            raise IdentityClaimError("human authentication is not phishing resistant")
        if break_glass and auth_strength is not AuthenticationStrength.BREAK_GLASS_MFA:
            raise IdentityClaimError("break-glass identity requires break-glass MFA")

        self._revocations.require_active(subject, token_id)
        self._replay_cache.consume(nonce, expires_at)
        return VerifiedPrincipal(
            principal_id=subject,
            kind=PrincipalKind.HUMAN,
            trust_domain=trust_domain,
            roles=roles,
            engagement_ids=engagement_ids,
            authenticated_at=now,
            expires_at=expires_at,
            authentication_strength=auth_strength,
            credential_id=token_id,
            device_posture=device_posture,
            break_glass=break_glass,
            attributes=(("issuer", issuer), ("audience", audience)),
        )


class DeterministicSpiffeVerifier:
    """Synthetic SPIFFE/SVID verifier for CI and contract tests only."""

    def __init__(
        self,
        *,
        clock: Clock,
        revocations: InMemoryRevocationRegistry,
        available: bool = True,
    ) -> None:
        self._clock = clock
        self._revocations = revocations
        self._available = available

    def verify(
        self,
        svid: SyntheticSvid,
        *,
        expected_audience: str,
        expected_trust_domain: TrustDomain,
        expected_spiffe_id: str | None = None,
    ) -> VerifiedPrincipal:
        if not self._available:
            raise WorkloadIdentityUnavailableError("workload identity API is unavailable")
        now = self._clock.now()
        if not svid.spiffe_id.startswith("spiffe://"):
            raise IdentityClaimError("invalid SPIFFE ID")
        expected_prefix = f"spiffe://{svid.trust_domain.value}/"
        if not svid.spiffe_id.startswith(expected_prefix):
            raise IdentityClaimError("SPIFFE ID does not match asserted trust domain")
        if svid.trust_domain is not expected_trust_domain:
            raise IdentityClaimError("workload trust-domain crossing is denied")
        if svid.audience != expected_audience:
            raise IdentityClaimError("workload audience mismatch")
        if expected_spiffe_id is not None and svid.spiffe_id != expected_spiffe_id:
            raise IdentityClaimError("workload credential is bound to another workload")
        if svid.issued_at > now + timedelta(seconds=30):
            raise IdentityClaimError("SVID issued-at time is in the future")
        if svid.not_before > now:
            raise IdentityClaimError("SVID is not active yet")
        if svid.expires_at <= now:
            raise IdentityClaimError("SVID is expired")
        if svid.expires_at - svid.issued_at > timedelta(hours=1):
            raise IdentityClaimError("SVID lifetime exceeds the short-lived profile")
        self._revocations.require_active(svid.spiffe_id, svid.serial_number)
        return VerifiedPrincipal(
            principal_id=svid.spiffe_id,
            kind=PrincipalKind.WORKLOAD,
            trust_domain=svid.trust_domain,
            roles=frozenset(),
            engagement_ids=frozenset(),
            authenticated_at=now,
            expires_at=svid.expires_at,
            authentication_strength=AuthenticationStrength.WORKLOAD_MTLS,
            credential_id=svid.serial_number,
            device_posture=DevicePosture.COMPLIANT,
            attributes=(("audience", svid.audience),),
        )
