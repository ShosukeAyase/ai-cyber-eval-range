"""Bounded HTTPS transport for OAuth 2.0 token introspection."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from cyber_eval.identity.errors import (
    IdentityProviderUnavailableError,
    InvalidIdentityTokenError,
)


class UrlLibOidcIntrospectionTransport:
    """Minimal HTTPS client for an OAuth 2.0 token introspection endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        if not client_id or not client_secret:
            raise ValueError("OIDC introspection requires a client id and secret")
        if timeout_seconds <= 0:
            raise ValueError("OIDC introspection timeout must be positive")
        _require_secure_endpoint(endpoint)
        self._endpoint = endpoint
        self._client_id = client_id
        self._client_secret = client_secret
        self._timeout_seconds = timeout_seconds

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def introspect(self, token: str) -> Mapping[str, object]:
        if not token:
            raise InvalidIdentityTokenError("identity token must not be empty")
        authorization = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode("utf-8")
        ).decode("ascii")
        request = Request(
            self._endpoint,
            data=urlencode({"token": token, "token_type_hint": "access_token"}).encode(
                "ascii"
            ),
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {authorization}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                payload = response.read(1024 * 1024 + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise IdentityProviderUnavailableError(
                "OIDC introspection endpoint is unavailable"
            ) from exc
        if len(payload) > 1024 * 1024:
            raise InvalidIdentityTokenError(
                "OIDC introspection response exceeds size limit"
            )
        try:
            document = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise InvalidIdentityTokenError(
                "OIDC introspection response is not valid JSON"
            ) from exc
        if not isinstance(document, dict) or not all(
            isinstance(key, str) for key in document
        ):
            raise InvalidIdentityTokenError(
                "OIDC introspection response must be an object"
            )
        return {str(key): value for key, value in document.items()}


def _require_secure_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("OIDC endpoint URL must not contain credentials")
    if parsed.scheme == "https" and parsed.hostname:
        return
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return
    raise ValueError("OIDC introspection requires HTTPS or loopback HTTP")
