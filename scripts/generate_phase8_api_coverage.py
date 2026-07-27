"""Generate deterministic complete-mediation evidence for Phase 08 write operations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
from datetime import UTC, datetime
from pathlib import Path

from cyber_eval.domain import WriteOperation
from cyber_eval.identity.production_gateway import (
    ProductionIdentityGateway,
    production_state_change_bindings,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/phase-08/api-coverage"),
    )
    args = parser.parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    bindings = production_state_change_bindings()
    expected = {operation.value for operation in WriteOperation}
    covered = {binding.operation.value for binding in bindings}
    missing = sorted(expected - covered)
    extra = sorted(covered - expected)
    signature = inspect.signature(ProductionIdentityGateway.authorize)
    caller_asserted_actor_id_count = int("actor_id" in signature.parameters)
    coverage_percent = (
        0 if not expected else round(100 * len(covered & expected) / len(expected), 2)
    )

    source_path = Path("src/cyber_eval/identity/production_gateway.py")
    source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    operations: list[dict[str, object]] = [
        {
            "operation": binding.operation.value,
            "action": binding.action,
            "principal_class": "human" if binding.required_roles else "workload",
            "required_roles": sorted(role.value for role in binding.required_roles),
            "allowed_workload_domains": sorted(
                domain.value for domain in binding.allowed_workload_domains
            ),
            "independent_approval_required": binding.independent_approval_required,
        }
        for binding in bindings
    ]
    status = (
        "pass"
        if coverage_percent == 100
        and not missing
        and not extra
        and caller_asserted_actor_id_count == 0
        else "fail"
    )
    report: dict[str, object] = {
        "schema_version": "1.0",
        "evidence_type": "static_complete_mediation_coverage",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "status": status,
        "production_boundary": "cyber_eval.identity.ProductionIdentityGateway.authorize",
        "state_changing_api_count": len(expected),
        "verified_principal_mediated_count": len(covered & expected),
        "coverage_percent": coverage_percent,
        "caller_asserted_actor_id_count": caller_asserted_actor_id_count,
        "missing_operations": missing,
        "unexpected_operations": extra,
        "source_sha256": f"sha256:{source_digest}",
        "deployment_review_required": True,
        "operations": operations,
    }
    (output_dir / "coverage-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "state-changing-api-inventory.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "operation",
                "action",
                "principal_class",
                "required_roles",
                "allowed_workload_domains",
                "independent_approval_required",
            ]
        )
        for binding in bindings:
            writer.writerow(
                [
                    binding.operation.value,
                    binding.action,
                    "human" if binding.required_roles else "workload",
                    ";".join(sorted(role.value for role in binding.required_roles)),
                    ";".join(sorted(domain.value for domain in binding.allowed_workload_domains)),
                    str(binding.independent_approval_required).lower(),
                ]
            )
    print(json.dumps(report, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
