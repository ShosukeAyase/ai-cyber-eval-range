# Cyber Range Design

## Scenario families

- Web/API: intentionally vulnerable applications, WAF, IdP, API gateway, database, synthetic data.
- Linux network: segmented hosts, DNS, PKI, SSH, service misconfiguration, IDS/IPS.
- Windows domain: disposable directory, member servers/workstations, synthetic users, EDR/SIEM connectors.
- Containers/Kubernetes: disposable cluster, vulnerable workloads, admission policies, runtime telemetry.
- Cloud simulation: local IAM/object-storage/control-plane simulators; no real cloud credentials.

## Shared internal services

- Dummy DNS and NTP.
- Scenario-local PKI.
- Dummy IdP and federation endpoints.
- Package/image mirrors populated before the engagement.
- Mail, webhook, and callback sinks that never relay externally.

## Isolation

The range has no general internet, corporate, or production route. Management is on a separate out-of-band network unavailable to runners and targets. Scenario VLAN/VRF or virtual-switch rules prevent cross-scenario traffic.

## Scenario lifecycle

1. Verify signed scenario manifest and artifact provenance.
2. Allocate isolated address space and internal services.
3. Instantiate from signed images/templates.
4. Seed synthetic data and dummy credentials.
5. Run health and isolation tests.
6. Publish target-object mappings to Scope Service.
7. Execute authorized jobs.
8. Collect final state/evidence.
9. Revoke credentials and destroy compute/storage/network state.
10. Produce destruction attestation.

## Scenario authoring controls

Scenario content is untrusted and scanned for secrets, PII, public endpoints, unsafe payloads, and prompt injection markers. Intentional injection markers are harmless and documented in hidden ground truth for scoring.

## Phase 05 local MVP

The implemented local profile is intentionally narrower than the future service-emulation design.
It uses deterministic synthetic files and safe markers, has no network primitive, and does not run
vulnerable software. See [Cyber Range MVP](cyber-range-mvp.md).
