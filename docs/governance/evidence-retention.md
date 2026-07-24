# Evidence Retention

## Evidence classes

| Class | Content | Default retention | Storage |
|---|---|---|---|
| E0 | Transient debug telemetry with no finding value | 7 days | Restricted hot storage |
| E1 | Routine job logs and test results | 90 days | Immutable object storage |
| E2 | Findings, approvals, policy decisions, packet/process/file evidence | 1 year | WORM/retention lock |
| E3 | Incident or formal-assurance evidence | Legal/compliance hold | WORM plus offline copy |

## Integrity controls

- Content hashes and signed evidence manifests.
- Trusted timestamps and monotonic sequence numbers.
- Separate custody from execution administrators.
- Retention lock cannot be shortened retroactively.
- Access is read-only and logged.
- Exports include chain-of-custody metadata.

## Destruction

After retention expiry, evidence is deleted according to policy. Ephemeral runner/range data is destroyed immediately after the engagement, except evidence explicitly transferred to the observability plane.
