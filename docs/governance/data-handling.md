# Data Handling

## Allowed data

- synthetic application data;
- dummy identities and credentials;
- non-sensitive open-source code copied into the range under license;
- intentionally vulnerable training applications;
- harmless markers and canary values;
- redacted findings and evidence.

## Prohibited data

- production data;
- real PII, PHI, financial, customer, employee, or confidential information;
- real credentials, tokens, private keys, or leaked secrets;
- unrestricted malware samples or weaponized payloads;
- third-party data without explicit authorization and license.

## Handling rules

- Classify data at ingestion.
- Scan scenario packages for secrets and PII.
- Keep raw evidence in the observability plane; give the model redacted excerpts.
- Encrypt data in transit and at rest with plane-specific keys.
- Record provenance and license for imported artifacts.
- Apply size and content limits to prevent exfiltration through evidence channels.
