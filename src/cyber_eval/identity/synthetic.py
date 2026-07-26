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
            self._entries = {key: expiry for key, expiry in self._entries.items() if expiry > now}
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
            raise IdentityProviderUnavailableErroŠšY[]H›ÝšY\ˆ\È[˜]˜Z[X›HŠBˆÙYÛY[ÈHÚÙ[‹œÜ]
‹ˆŠBˆYˆ[ŠÙYÛY[ÊHOHÎ‚ˆ˜Z\ÙH[˜[YY[]UÚÙ[‘\œ›ÜŠÚÙ[ˆ]\ÝÛÛZ[ˆ™YHÙYÛY[ÈŠBˆXY\ˆHÚœÛÛ—ÛØš™XÝ
ÙYÛY[ÖÌJBˆ^[ØYHÚœÛÛ—ÛØš™XÝ
ÙYÛY[ÖÌWJBˆYˆXY\‹™Ù]
˜[ÈŠHOH’ÌMˆˆÜˆXY\‹™Ù]
\ŠHOH’•ÕŽ‚ˆ˜Z\ÙH[˜[YY[]UÚÙ[‘\œ›ÜŠ[œÝ\ÜYÜˆ[œÚYÛ™YÚÙ[ˆŠBˆÙ^WÚYHÜÝš[™ÊXY\‹™Ù]
šÚYŠKšÚYŠBˆÙ^HHÙ[‹—Ý™\šYšXØ][Û—ÚÙ^\Ë™Ù]
Ù^WÚY
BˆYˆÙ^H\È›Û™N‚ˆ˜Z\ÙH[˜[YY[]UÚÙ[‘\œ›ÜŠ[šÛ›ÝÛˆÚÙ[ˆÚYÛš[™ÈÙ^HŠBˆÚYÛš[™×Ú[œ]HˆžÜÙYÛY[ÖÌ_KžÜÙYÛY[ÖÌW_H‹™[˜ÛÙJ˜\ØÚZHŠBˆ^XÝYÜÚYÛ˜]\™HHXXË›™]ÊÙ^KÚYÛš[™×Ú[œ]\ÚX‹œÚLMŠK™YÙ\Ý

BˆXÝX[ÜÚYÛ˜]\™HHØ\›ÙXÛÙJÙYÛY[ÖÌ—JBˆYˆ›ÝXXË˜ÛÛ\\™WÙYÙ\Ý
^XÝYÜÚYÛ˜]\™KXÝX[ÜÚYÛ˜]\™JN‚ˆ˜Z\ÙH[˜[YY[]UÚÙ[‘\œ›ÜŠÚÙ[ˆÚYÛ˜]\™H\È[˜[YŠB‚ˆ\ÜÝY\ˆHÜÝš[™Ê^[ØY™Ù]
š\ÜÈŠKš\ÜÈŠBˆ]YY[˜ÙHHÜÝš[™Ê^[ØY™Ù]
˜]YŠK˜]YŠBˆÝXš™XÝHÜÝš[™Ê^[ØY™Ù]
œÝXˆŠKœÝXˆŠBˆÚÙ[—ÚYHÜÝš[™Ê^[ØY™Ù]
šHŠKšHŠBˆ›Û˜ÙHHÜÝš[™Ê^[ØY™Ù]
››Û˜ÙHŠK››Û˜ÙHŠBˆ\ÜÝYYØ]HÝ[Y\Ý[\
^[ØY™Ù]
šX]ŠKšX]ŠBˆ›ÝØ™Y›Ü™HHÝ[Y\Ý[\
^[ØY™Ù]
›˜™ˆŠK›˜™ˆŠBˆ^\™\×Ø]HÝ[Y\Ý[\
^[ØY™Ù]
™^ŠK™^ŠBˆ›ÝÈHÙ[‹—ØÛØÚË››ÝÊ
B‚ˆYˆ\ÜÝY\ˆOHÙ[‹—Ù^XÝYÚ\ÜÝY\Ž‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ[™^XÝYÚÙ[ˆ\ÜÝY\ˆŠBˆYˆ]YY[˜ÙHOHÙ[‹—Ù^XÝYØ]YY[˜ÙN‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ[™^XÝYÚÙ[ˆ]YY[˜ÙHŠBˆYˆ^[ØY™Ù]
œš[˜Ú\[ÚÚ[™ŠHOHš[˜Ú\[Ú[™’SPS‹˜[YN‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ“ÒQÈ]XØÙ\È[X[ˆš[˜Ú\[ÈÛ›HŠBˆYˆ\ÜÝYYØ]ˆ›ÝÈ
ÈÙ[‹—ÛX^[][WØÛØÚ×ÜÚÙ]Î‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÚÙ[ˆ\ÜÝYYX][YH\È[ˆH]\™HŠBˆYˆ›ÝØ™Y›Ü™Hˆ›ÝÈ
ÈÙ[‹—ÛX^[][WØÛØÚ×ÜÚÙ]Î‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÚÙ[ˆ\È›ÝXÝ]™HY]ŠBˆYˆ^\™\×Ø]H›ÝÎ‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÚÙ[ˆ\È^\™YŠBˆYˆ^\™\×Ø]H›ÝØ™Y›Ü™N‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÚÙ[ˆ˜[Y]H[\˜[\È[˜[YŠB‚ˆžN‚ˆ›Û\ÈHœ›Þ™[œÙ]
ˆ[X[”›ÛJ][JH›Üˆ][H[ˆÜÝš[™×ÜÙ]
^[ØY™Ù]
œ›Û\ÈŠKœ›Û\ÈŠBˆ
Bˆ\ÝÙÛXZ[ˆH\ÝÛXZ[ŠÜÝš[™Ê^[ØY™Ù]
\ÝÙÛXZ[ˆŠK\ÝÙÛXZ[ˆŠJBˆ[™ØYÙ[Y[ÚYÈHÜÝš[™×ÜÙ]
^[ØY™Ù]
™[™ØYÙ[Y[ÚYÈŠK™[™ØYÙ[Y[ÚYÈŠBˆ]šXÙWÜÜÝ\™HH]šXÙTÜÝ\™JÜÝš[™Ê^[ØY™Ù]
™]šXÙWÜÜÝ\™HŠK™]šXÙWÜÜÝ\™HŠJBˆ]]ÜÝ™[™ÝH]][XØ][Û”Ý™[™Ý
ˆÜÝš[™Ê^[ØY™Ù]
˜]]ÜÝ™[™ÝŠK˜]]ÜÝ™[™ÝŠBˆ
Bˆ^Ù\˜[YQ\œ›Üˆ\È^Î‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÚÙ[ˆÛÛZ[œÈ[ˆ[œÝ\ÜYY[]HÛZ[HŠHœ›ÛH^Âˆœ™XZ×ÙÛ\ÜÈH^[ØY™Ù]
˜œ™XZ×ÙÛ\ÜÈ‹˜[ÙJBˆYˆ›Ý\Ú[œÝ[˜ÙJœ™XZ×ÙÛ\ÜË›ÛÛ
N‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ˜œ™XZ×ÙÛ\ÜÈ]\Ý™H›ÛÛX[ˆŠBˆ\›Z]YÜÝ™[™ÝÈHÂˆ]][XØ][Û”Ý™[™Ý”TÒS‘×Ô‘TÒTÕS•ÓQKˆ]][XØ][Û”Ý™[™Ý”‘PR×ÑÓTÔ×ÓQKˆBˆYˆ]]ÜÝ™[™Ý›Ý[ˆ\›Z]YÜÝ™[™ÝÎ‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠš[X[ˆ]][XØ][Ûˆ\È›Ý\Ú[™È™\Ú\Ý[ŠBˆYˆœ™XZ×ÙÛ\ÜÈ[™]]ÜÝ™[™Ý\È›Ý]][XØ][Û”Ý™[™Ý”‘PR×ÑÓTÔ×ÓQN‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ˜œ™XZËYÛ\ÜÈY[]H™\]Z\™\Èœ™XZËYÛ\ÜÈQHŠB‚ˆÙ[‹—Ü™]›ØØ][ÛœËœ™\]Z\™WØXÝ]™JÝXš™XÝÚÙ[—ÚY
BˆÙ[‹—Ü™\^WØØXÚK˜ÛÛœÝ[YJ›Û˜ÙK^\™\×Ø]
Bˆ™]\›ˆ™\šYšYYš[˜Ú\[
ˆš[˜Ú\[ÚY\ÝXš™XÝˆÚ[™Tš[˜Ú\[Ú[™’SPS‹ˆ\ÝÙÛXZ[]\ÝÙÛXZ[‹ˆ›Û\Ï\›Û\Ëˆ[™ØYÙ[Y[ÚYÏY[™ØYÙ[Y[ÚYËˆ]][XØ]YØ][›ÝËˆ^\™\×Ø]Y^\™\×Ø]ˆ]][XØ][Û—ÜÝ™[™ÝX]]ÜÝ™[™ÝˆÜ™Y[X[ÚY]ÚÙ[—ÚYˆ]šXÙWÜÜÝ\™OY]šXÙWÜÜÝ\™Kˆœ™XZ×ÙÛ\ÜÏXœ™XZ×ÙÛ\ÜËˆ]šX]\ÏJ
š\ÜÝY\ˆ‹\ÜÝY\ŠK
˜]YY[˜ÙH‹]YY[˜ÙJJKˆ
B‚‚˜Û\ÜÈ]\›Z[š\ÝXÔÜY™™U™\šYšY\Ž‚ˆˆˆ”Þ[]XÈÔQ‘‘KÔÕ’Q™\šYšY\ˆ›ÜˆÒH[™ÛÛ˜XÝ\ÝÈÛ›Kˆˆˆ‚‚ˆYˆ×Ú[š]×ÊˆÙ[‹ˆ
‹ˆÛØÚÎˆÛØÚËˆ™]›ØØ][ÛœÎˆ[“Y[[ÜžT™]›ØØ][Û”™YÚ\ÝžKˆ]˜Z[X›Nˆ›ÛÛHYKˆ
HOˆ›Û™N‚ˆÙ[‹—ØÛØÚÈHÛØÚÂˆÙ[‹—Ü™]›ØØ][ÛœÈH™]›ØØ][ÛœÂˆÙ[‹—Ø]˜Z[X›HH]˜Z[X›B‚ˆYˆ™\šYžJˆÙ[‹ˆÝšYˆÞ[]XÔÝšYˆ
‹ˆ^XÝYØ]YY[˜ÙNˆÝ‹ˆ^XÝYÝ\ÝÙÛXZ[Žˆ\ÝÛXZ[‹ˆ^XÝYÜÜY™™WÚYˆÝˆ›Û™HH›Û™Kˆ
HOˆ™\šYšYYš[˜Ú\[‚ˆYˆ›ÝÙ[‹—Ø]˜Z[X›N‚ˆ˜Z\ÙHÛÜšÛØYY[]U[˜]˜Z[X›Q\œ›ÜŠÛÜšÛØYY[]HTH\È[˜]˜Z[X›HŠBˆ›ÝÈHÙ[‹—ØÛØÚË››ÝÊ
BˆYˆ›ÝÝšYœÜY™™WÚYœÝ\ÝÚ]
œÜY™™N‹ËÈŠN‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠš[˜[YÔQ‘‘HQŠBˆ^XÝYÜ™Yš^HˆœÜY™™N‹ËÞÜÝšY\ÝÙÛXZ[‹˜[Y_KÈ‚ˆYˆ›ÝÝšYœÜY™™WÚYœÝ\ÝÚ]
^XÝYÜ™Yš^
N‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ”ÔQ‘‘HQÙ\È›ÝX]Ú\ÜÙ\Y\ÝÛXZ[ˆŠBˆYˆÝšY\ÝÙÛXZ[ˆ\È›Ý^XÝYÝ\ÝÙÛXZ[Ž‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÛÜšÛØY\ÝYÛXZ[ˆÜ›ÜÜÚ[™È\È[šYYŠBˆYˆÝšY˜]YY[˜ÙHOH^XÝYØ]YY[˜ÙN‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÛÜšÛØY]YY[˜ÙHZ\ÛX]ÚŠBˆYˆ^XÝYÜÜY™™WÚY\È›Ý›Û™H[™ÝšYœÜY™™WÚYOH^XÝYÜÜY™™WÚY‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠÛÜšÛØYÜ™Y[X[\È›Ý[™È[›Ý\ˆÛÜšÛØYŠBˆYˆÝšYš\ÜÝYYØ]ˆ›ÝÈ
È[YY[JÙXÛÛ™ÏLÌ
N‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ”Õ’Q\ÜÝYYX][YH\È[ˆH]\™HŠBˆYˆÝšY››ÝØ™Y›Ü™Hˆ›ÝÎ‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ”Õ’Q\È›ÝXÝ]™HY]ŠBˆYˆÝšY™^\™\×Ø]H›ÝÎ‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ”Õ’Q\È^\™YŠBˆYˆÝšY™^\™\×Ø]HÝšYš\ÜÝYYØ]ˆ[YY[JÝ\œÏLJN‚ˆ˜Z\ÙHY[]PÛZ[Q\œ›ÜŠ”Õ’QY™][YH^ÙYYÈHÚÜ[]™Y›Ùš[HŠBˆÙ[‹—Ü™]›ØØ][ÛœËœ™\]Z\™WØXÝ]™JÝšYœÜY™™WÚYÝšYœÙ\šX[Û[X™\ŠBˆ™]\›ˆ™\šYšYYš[˜Ú\[
ˆš[˜Ú\[ÚY\ÝšYœÜY™™WÚYˆÚ[™Tš[˜Ú\[Ú[™•ÓÔ’ÓÐQˆ\ÝÙÛXZ[\ÝšY\ÝÙÛXZ[‹ˆ›Û\ÏYœ›Þ™[œÙ]

Kˆ[™ØYÙ[Y[ÚYÏYœ›Þ™[œÙ]

Kˆ]][XØ]YØ][›ÝËˆ^\™\×Ø]\ÝšY™^\™\×Ø]ˆ]][XØ][Û—ÜÝ™[™ÝP]][XØ][Û”Ý™[™Ý•ÓÔ’ÓÐQÓUËˆÜ™Y[X[ÚY\ÝšYœÙ\šX[Û[X™\‹ˆ]šXÙWÜÜÝ\™OQ]šXÙTÜÝ\™KÓÓTPS•ˆ]šX]\ÏJ
˜]YY[˜ÙH‹ÝšY˜]YY[˜ÙJK
Kˆ
B