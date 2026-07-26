"""Verified identity boundary for state-changing control-plane adapters."""

from __future__ import annotations

from collections.abc import Collection
from uuid import uuid4

from cyber_eval.identity.contracts import (
    AuthorizationContext,
    Clock,
    DevicePosture,
    EnvironmentClass,
    HumanIdentityVerifier,
    HumanRole,
    IdentityAuditEvent,
    IdentityAuditOutcome,
    IdentityAuditSink,
    PamElevationGrant,
    PrincipalKind,
    SyntheticSvid,
    TrustDomain,
    VerifiedPrincipal,
    WorkloadIdentityVerifier,
)
from cyber_eval.identity.errors import (
    ActorSpoofingError,
    IdentityAuthorizationError,
    SeparationOfDutiesError,
)


class IdentityBoundary:
    """Authenticate principals and enforce identity-level authorization invariants."""

    def __init__(
        self,
        *,
        human_verifier: HumanIdentityVerifier,
        workload_verifier: WorkloadIdentityVerifier,
        audit_sink: IdentityAuditSink,
        clock: Clock,
    ) -> None:
        self._human_verifier = human_verifier
        self._workload_verifier = workload_verifier
        self._audit_sink = audit_sink
        self._clock = clock

    def authenticate_human(
        self,
        token: str,
        *,
        request_body_actor_id: str | None = None,
    ) -> VerifiedPrincipal:
        principal = self._human_verifier.verify(token)
        if request_body_actor_id is not None and request_body_actor_id != principal.principal_id:
            self._audit(
                principal,
                "human.authenticate",
                IdentityAuditOutcome.DENIED,
                "actor spoofing",
            )
            raise ActorSpoofingError("request body actor_id cannot override verified identity")
        self._audit(principal, "human.authenticate", IdentityAuditOutcome.ALLOWED, "verified")
        return principal

    def authenticate_workload(
        self,
        svid: SyntheticSvid,
        *,
        expected_audience: str,
        expected_trust_domain: TrustDomain,
        expected_spiffe_id: str | None = None,
    ) -> VerifiedPrincipal:
        principal = self._workload_verifier.verify(
            svid,
            expected_audience=expected_audience,
            expected_trust_domain=expected_trust_domain,
            expected_spiffe_id=expected_spiffe_id,
        )
        self._audit(principal, "workload.authenticate", IdentityAuditOutcome.ALLOWED, "verified")
        return principal

    def authorize_state_change(
        self,
        context: AuthorizationContext,
        *,
        required_roles: Collection[HumanRole] = (),
        allowed_workload_domains: Collection[TrustDomain] = (),
    ) -> VerifiedPrincipal:
        principal = context.principal
        now = self._clock.now()
        if principal.expires_at <= now:
            self._deny(principal, context, "principal validity interval is invalid")
        if context.device_posture is not principal.device_posture:
            self._deny(principal, context, "device posture is not identity-bound")
        if context.environment is EnvironmentClass.PRODUCTION:
            if principal.device_posture is not DevicePosture.COMPLIANT:
                self._deny(principal, context, "production requires compliant device posture")
            if principal.break_glass:
                self._audit(
                    principal,
                    "break_glass.use",
                    IdentityAuditOutcome.ALLOWED,
                    "high-priority audit required",
                    engagement_id=context.engagement_id,
                )
        if principal.kind is PrincipalKind.HUMAN:
            if context.engagement_id not in principal.engagement_ids:
                self._deny(principal, context, "engagement attribute is missing")
            effective_roles = set(principal.roles)
            if context.elevation_grant is not None:
                self._validate_elevation(principal, context.elevation_grant, context.engagement_id)
                effective_roles.add(context.elevation_grant.role)
            if not set(required_roles).issubset(effective_roles):
                self._deny(principal, context, "required role is missing")
        else:
            if principal.trust_domain not in set(allowed_workload_domains):
                self._deny(principal, context, "workload trust domain is not permitted")
            if required_roles:
                self._deny(
                    principal,
                    context,
                    "human role cannot be satisfied by workload identity",
                )
        self._audit(
            principal,
            "state_change.authorize",
            IdentityAuditOutcome.ALLOWED,
            context.action,
            engagement_id=context.engagement_id,
        )
        return principal

    def require_independent_approval(
        self,
        *,
        requester: VerifiedPrincipal,
        approver: VerifiedPrincipal,
        engagement_id: str,
    ) -> None:
        if requester.kind is not PrincipalKind.HUMAN or approver.kind is not PrincipalKind.HUMAN:
            raise SeparationOfDutiesError("requester and approver must be verified humans")
        if requester.principal_id == approver.principal_id:
            raise SeparationOfDutiesError("self approval is prohibited")
        if HumanRole.REQUESTER not in requester.roles or HumanRole.APPROVER not in approver.roles:
            raise SeparationOfDutiesError("requester and approver roles are not separated")
        if (
            engagement_id not in requester.engagement_ids
            or engagement_id not in approver.engagement_ids
        ):
            raise SeparationOfDutiesError("both principals must be bound to the engagement")

    def _validate_elevation(
        self,
        principal: VerifiedPrincipal,
        grant: PamElevationGrant,
        engagement_id: str,
    ) -> None:
        if grant.revoked:
            raise IdentityAuthorizationError("elevation grant is revoked")
        if grant.principal_id != principal.principal_id:
            raise IdentityAuthorizationError("elevation grant is bound to another principal")
        if grant.engagement_id != engagement_id:
            raise IdentityAuthorizationError("elevation grant engagement mismatch")
        now = self._clock.now()
        if grant.expires_at <= now or grant.issued_at > now:
            raise IdentityAuthorizationError("elevation grant is not current")
        if len(set(grant.approved_by)) != 2 or principal.principal_id in grant.approved_by:
            raise IdentityAuthorizationError("elevation grant requires two independent approvers")
        if not grant.ticket_id:
            raise IdentityAuthorizationError("elevation grant requires a ticket")

    def _deny(
        self,
        principal: VerifiedPrincipal,
        context: AuthorizationContext,
        reason: str,
    ) -> None:
        self._audit(
            principal,
            "state_change.authorize",
            IdentityAuditOutcome.DENIED,
            reason,
            engagement_id=context.engagement_id,
        )
        raise IdentityAuthorizationError(reason)

    def _audit(
        self,
        principal: VerifiedPrincipal,
        event_type: str,
        outcome: IdentityAuditOutcome,
        reason: str,
        *,
        engagement_id: str | None = None,
    ) -> None:
        self._audit_sink.append(
            IdentityAuditEvent(
                event_id=f"idevt-{uuid4()}",
                event_type=event_type,
                principal_id=principal.principal_id,
                credential_id=principal.credential_id,
                outcome=outcome,
                occurred_at=self._clock.now(),
                engagement_id=engagement_id,
                reason=reason,
                attributes=(("trust_domain", principal.trust_domain.value),),
            )
        )
