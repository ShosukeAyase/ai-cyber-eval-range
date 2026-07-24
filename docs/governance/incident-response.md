# Incident Response

## Incident triggers

- Scope deviation or forbidden destination.
- Unexpected privilege escalation, persistence, listener, or credential search.
- Metadata, Docker socket, or unauthorized Kubernetes API access.
- Log/monitoring modification or telemetry loss.
- Policy/scope file modification.
- Repeated unsafe failures or quota breach.
- Evidence integrity failure.

## Response sequence

1. Emergency Stop isolates the runner and freezes new scheduling.
2. Credential Broker revokes all related credentials.
3. Range network blocks affected scenario segments.
4. Observability plane seals current evidence and marks an incident boundary.
5. Runner and scenario snapshots are captured only when safe and authorized.
6. Incident Commander decides destruction, forensic retention, and notification.
7. No resume occurs; a new engagement/version is required.

## Severity

- SEV-1: potential external/corporate/production reachability or cross-plane compromise.
- SEV-2: scope violation contained inside range or evidence/credential integrity concern.
- SEV-3: quota, repeated failure, or control degradation without boundary crossing.

Post-incident review updates the threat model, risk register, policy tests, and relevant ADRs.
