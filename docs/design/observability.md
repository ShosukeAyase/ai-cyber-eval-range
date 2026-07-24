# Observability Design

## Telemetry

- Centralized application and security logs.
- Packet capture or flow records at range boundaries.
- Process tree and syscall/security events.
- File-system deltas and image/snapshot hashes.
- OpenTelemetry traces, metrics, and logs.
- Policy decisions, approvals, model metadata, and scheduler state.
- Health heartbeats from independent sensors.

## Independence

The observability plane uses separate identities, hosts/accounts, keys, and administrators. Execution and range components can write through a narrow gateway but cannot query, update, or delete evidence.

## Integrity

- Signed event envelopes and source identity.
- Sequence numbers and clock-quality metadata.
- Hash chains for job event streams.
- WORM retention for material evidence.
- Integrity-verification jobs run under evidence-custodian identity.

## Stop-on-blindness

Loss of mandatory packet, process, policy-decision, or lifecycle telemetry beyond a defined grace threshold causes job quarantine and termination.

## SRE indicators

- Policy decision latency/error rate.
- Approval wait/expiry rate.
- Runner provision and destruction success rate.
- Telemetry completeness.
- Scope-deny and stop-condition counts.
- Evidence sealing latency.
- Range reset consistency.
