"""Assemble SPIRE and mTLS staging evidence from independently captured test logs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


_REQUIRED_CASES = {
    "server_ready": "PHASE8_PASS:server_ready",
    "agents_ready": "PHASE8_PASS:agents_ready",
    "workload_svid_issued": "PHASE8_PASS:workload_svid_issued",
    "mtls_success": "PHASE8_PASS:mtls_success",
    "foreign_identity_denied": "PHASE8_PASS:foreign_identity_denied",
    "svid_rotation_observed": "PHASE8_PASS:svid_rotation_observed",
    "revoked_svid_denied": "PHASE8_PASS:revoked_svid_denied",
    "workload_api_outage_denied": "PHASE8_PASS:workload_api_outage_denied",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/phase-08/spire"),
    )
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--trust-domain", required=True)
    parser.add_argument(
        "--profile",
        choices=("isolated-staging", "local-development"),
        required=True,
    )
    args = parser.parse_args()
    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    tests: list[dict[str, str]] = []
    log_digests: dict[str, str] = {}
    for name, marker in sorted(_REQUIRED_CASES.items()):
        path = input_dir / f"{name}.txt"
        if not path.is_file():
            tests.append({"name": name, "status": "fail", "detail": "log missing"})
            continue
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        log_digests[name] = "sha256:" + hashlib.sha256(data).hexdigest()
        tests.append(
            {
                "name": name,
                "status": "pass" if marker in text else "fail",
                "detail": "required marker present" if marker in text else "marker missing",
            }
        )

    status = "pass" if all(test["status"] == "pass" for test in tests) else "fail"
    evidence = {
        "schema_version": "1.0",
        "evidence_type": "live_spire_mtls_staging",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": status,
        "gate_eligible": args.profile == "isolated-staging",
        "profile": args.profile,
        "cluster": args.cluster,
        "spiffe_trust_domain": args.trust_domain,
        "logical_trust_domains": [
            "control",
            "execution",
            "range",
            "evidence",
            "management",
        ],
        "tests": tests,
        "log_sha256": log_digests,
        "private_keys_persisted": False,
    }
    (output_dir / "spire-mtls-staging-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
