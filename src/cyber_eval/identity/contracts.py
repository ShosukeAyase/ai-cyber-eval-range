"""Typed identity contracts for Phase 08 production IAM boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class PrincipalKind(StrEnum):
    HUMAN = "human"
    WORKLOAD = "workload"


class TrustDomain(StrEnum):
    CONTROL = "control"
    EXECUTION = "execution"
    RANGE = "range"
    EVIDENCE = "evidence"
    MANAGEMENT = "management"


class HumanRole(StrEnum):
    REQUESTER = "requester"
    APPROVER = "approver"
    AUDITOR = "auditor"
    PLATFORM_ADMIN = "platform_admin"
    SECURITY_OPERATOR = "security_operator"


class AuthenticationStrength(StrEnum):
    PHISHING_RESISTANT_MFA = "phishing_resistant_mfa"
    WORKLOAD_MTLS = "workload_mtls"
    BREAK_GLASS_MFA = "break_glass_mfa"


class DevicePosture(StrEnum):
    COMPLIANT = "compliant"
    NONCOMPLIANT = "noncompliant"
    UNKNOWN = "unknown"


class EnvironmentClass(StrEnum):
    LOCAL_DEMO = "local_demo"
    STAGING = "staging"
    PRODUCTION = "production"


class IdentityAuditOutcome(StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class HumanTokenClaims:
    issuer: str
    audience: str
    subject: str
    token_id: str
    nonce: str
    issued_at: datetime
    not_before: datetime
    expires_at: datetime
    roles: frozenset[HumanRole]
    trust_domain: TrustDomain
    engagement_ids: frozenset[str]
    device_posture: DevicePosture
    authentication_strength: AuthenticationStrength
    break_glass: bool = False


@dataclass(frozen=True, slots=True)
class SyntheticSvid:
    spiffe_id: str
    serial_number: str
    audience: str
    trust_domain: TrustDomain
    issued_at: datetime
    not_before: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class VerifiedPrincipal:
    principal_id: str
    kind: PrincipalKind
    trust_domain: TrustDomain
    roles: frozenset[HumanRole]
    engagement_ids: frozenset[str]
    authenticated_at: datetime
    expires_at: datetime
    authentication_strength: AuthenticationStrength
    credential_id: str
    device_posture: DevicePosture
    break_glass: bool = False
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class PamElevationGrant:
    grant_id: str
    principal_id: str
    role: HumanRole
    engagement_id: str
    ticket_id: str
    approved_by: tuple[str, str]
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False


@dataclass(frozen=True, slots=True)
class AuthorizationContext:
    principal: VerifiedPrincipal
    engagement_id: str
    action: str
    environment: EnvironmentClass
    device_posture: DevicePosture
    elevation_grant: PamElevationGrant | None = None


@dataclass(frozen=True, slots=True)
class IdentityAuditEvent:
    event_id: str
    event_type: str
    principal_id: str
    credential_id: str
    outcome: IdentityAuditOutcome
    occurred_at: datetime
    engagement_id: str | None = None
    reason: str = ""
    attributes: tuple[tuple[str, str], ...] = ()


class Clock(Protocol):
    def now(self) -> datetime:
        """Return a timezone-aware time."""


class IdentityAuditSink(Protocol):
    def append(self, event: IdentityAuditEvent) -> None:
        """Append an identity event to an independently controlled sink."""


class HumanIdentityVerifier(Protocol):
    def verify(self, token: str) -> VerifiedPrincipal:
        """Verify a human identity token or fail closed."""


class WorkloadIdentityVerifier(Protocol):
    def verify(
        self,
        svid: SyntheticSvid,
        *,
        expected_audience: str,
        expected_trust_domain: TrustDomain,
        expected_spiffe_id: str | None = None,
    ) -> VerifiedPrincipal:
        """Verify a workload identity and its intended service boundary."""
