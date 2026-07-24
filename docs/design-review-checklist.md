# Design Review Checklist

## Authorization and governance

- [ ] Target ownership and authorization evidence are defined.
- [ ] Engagement and ROE schemas are approved.
- [ ] Approval separation of duties and expiry are acceptable.
- [ ] Prohibited actions cannot be enabled by configuration.

## Boundaries and networking

- [ ] Four planes use separate IAM, credentials, networks, and hosts.
- [ ] No range route exists to internet/corporate/production.
- [ ] Metadata, Docker/runtime sockets, and Kubernetes API are blocked.
- [ ] Observability path is write-only or one-way.

## Execution safety

- [ ] Tool APIs use object IDs and closed schemas.
- [ ] No arbitrary shell, URL, IP, hostname, or plugin loading path exists.
- [ ] Quotas and repeated-failure thresholds are defined.
- [ ] Emergency stop is independent and tested.

## Credentials and data

- [ ] Model context cannot contain credentials.
- [ ] Credentials are target/action/audience bound and short-lived.
- [ ] Only synthetic data and dummy secrets are used.
- [ ] Evidence redaction and retention are approved.

## Range lifecycle

- [ ] Scenario initialization is reproducible.
- [ ] Reset/destruction is idempotent and attested.
- [ ] Package/image mirrors are isolated and pre-populated.
- [ ] High-risk jobs use appropriate dedicated hardware.

## Assurance

- [ ] Threat model covers required actors.
- [ ] Risk register has owners and human decisions.
- [ ] ADRs contain alternatives and revisit conditions.
- [ ] Traceability and negative tests are complete.
- [ ] Required validation tools and CI gates are selected.
## Phase 02 automated skeleton evidence

- [x] Every schema has a validating synthetic example.
- [x] Scope-outside and approval-missing requests are denied.
- [x] Policy unavailability and exceptions fail closed.
- [x] Invalid state transitions are rejected.
- [x] Dispatch remains non-executable.
- [x] Architecture tests prohibit shell, network, cloud, IaC, runtime images, and secret material.
- [x] CI is read-only and validation-only.
- [x] Requirements have design and test traceability.
