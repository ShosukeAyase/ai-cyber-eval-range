# Phase 08 live OIDC staging

The production adapter uses OAuth 2.0 token introspection and fails closed when introspection is unavailable, inactive, malformed, or contains claims outside the configured issuer and audience.

## Required token claims

The introspection response must expose:

```text
active
iss
aud
sub
jti
nonce
iat
nbf
exp
roles
trust_domain
engagement_ids
device_posture
auth_strength
break_glass
```

`auth_strength` must be `phishing_resistant_mfa` or `break_glass_mfa`. Configure the enterprise staging IdP to emit these server-controlled claims. Do not allow callers to supply them in request bodies.

## Evidence inputs

Set the following environment variables in the current PowerShell process. Tokens and the introspection client secret are read only from the process environment and are never written to evidence files.

```powershell
$env:PHASE8_OIDC_PROFILE = "enterprise-staging"
$env:PHASE8_OIDC_ISSUER = "https://idp-staging.example/realms/phase8"
$env:PHASE8_OIDC_AUDIENCE = "cyber-eval-control-plane"
$env:PHASE8_OIDC_INTROSPECTION_ENDPOINT = "https://idp-staging.example/realms/phase8/protocol/openid-connect/token/introspect"
$env:PHASE8_OIDC_INTROSPECTION_CLIENT_ID = "phase8-evidence-collector"
$env:PHASE8_OIDC_INTROSPECTION_CLIENT_SECRET = "<set-in-shell-only>"
$env:PHASE8_OIDC_VALID_TOKEN = "<fresh-phishing-resistant-token>"
$env:PHASE8_OIDC_ROTATED_KEY_TOKEN = "<fresh-token-issued-after-signing-key-rotation>"
$env:PHASE8_OIDC_EXPIRED_TOKEN = "<expired-token>"
$env:PHASE8_OIDC_REVOKED_TOKEN = "<revoked-session-token>"
$env:PHASE8_OIDC_OUTAGE_ENDPOINT = "https://stopped-idp-staging.example/token/introspect"
```

Then run:

```powershell
python scripts/collect_phase8_oidc_evidence.py `
  --output-dir artifacts/phase-08/oidc
```

The collector verifies a valid token, nonce replay denial, a fresh token issued after signing-key rotation, wrong-audience denial, expired-token denial, revoked-session denial, and fail-closed behavior against the designated stopped endpoint. It stores only token SHA-256 fingerprints and verified identifiers. The rotated-key token must use a new token ID and nonce.

## Local Keycloak reference profile

`docker compose -f staging/oidc/keycloak-compose.yml up -d` starts Keycloak 26.7.0 on loopback only. This is useful for adapter development, but `PHASE8_OIDC_PROFILE=local-keycloak` is deliberately not accepted by the Phase 08 completion gate. Development mode and locally configured password flows do not prove enterprise phishing-resistant authentication, administrative separation, key rotation, or session governance.
