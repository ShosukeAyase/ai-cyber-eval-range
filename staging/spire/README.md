# Phase 08 SPIRE and mTLS staging

This profile installs the official hardened SPIRE Helm charts into an isolated `kind` cluster. It creates one SPIFFE trust domain, `phase8.internal`, and five separately selected logical trust zones: Control, Execution, Range, Evidence, and Management.

Run:

```powershell
pwsh -File scripts/setup_phase8_spire_staging.ps1
```

The setup script pins the SPIRE chart to `0.29.0` and the CRD chart to `0.5.0`. Before treating evidence as release-gate eligible, replace the default kind node tag with an internally approved digest-pinned image and record the digest in the evidence package.

## Workload contract

A workload must be deployed in the matching namespace and carry one of these labels:

```text
phase8.cyber-eval/trust-domain=control
phase8.cyber-eval/trust-domain=execution
phase8.cyber-eval/trust-domain=range
phase8.cyber-eval/trust-domain=evidence
phase8.cyber-eval/trust-domain=management
```

Mount the SPIFFE CSI Workload API socket as documented by the installed chart. Do not copy SVID private keys into the repository or long-lived evidence storage.

## Required live cases

Execute the following cases with real workload SVIDs and application-level peer SPIFFE-ID authorization. Each test log must contain exactly the corresponding success marker:

| Log file | Required marker |
|---|---|
| `server_ready.txt` | `PHASE8_PASS:server_ready` |
| `agents_ready.txt` | `PHASE8_PASS:agents_ready` |
| `workload_svid_issued.txt` | `PHASE8_PASS:workload_svid_issued` |
| `mtls_success.txt` | `PHASE8_PASS:mtls_success` |
| `foreign_identity_denied.txt` | `PHASE8_PASS:foreign_identity_denied` |
| `svid_rotation_observed.txt` | `PHASE8_PASS:svid_rotation_observed` |
| `revoked_svid_denied.txt` | `PHASE8_PASS:revoked_svid_denied` |
| `workload_api_outage_denied.txt` | `PHASE8_PASS:workload_api_outage_denied` |

The positive mTLS case must authenticate both peers and record both SPIFFE IDs. The foreign-identity case must use a valid SVID from a disallowed logical zone. The rotation case must show different certificate serial numbers without persisting private keys. The revocation and outage cases must demonstrate rejection of a new state-changing connection.

Assemble the evidence only after all raw logs exist:

```powershell
python scripts/collect_phase8_spire_evidence.py `
  --input-dir artifacts/phase-08/spire/raw `
  --output-dir artifacts/phase-08/spire `
  --cluster phase8-spire `
  --trust-domain phase8.internal `
  --profile isolated-staging
```

The collector hashes the logs and refuses success when any required marker is absent. It does not manufacture or infer a passing mTLS result.
