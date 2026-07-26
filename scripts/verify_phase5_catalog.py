"""Verify the seven Phase 05 scenario packages and print baseline digests."""

from __future__ import annotations

from pathlib import Path

from cyber_eval.range.catalog import LocalScenarioCatalog

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    catalog = LocalScenarioCatalog(ROOT / "range-scenarios")
    for scenario_id in catalog.scenario_ids():
        scenario = catalog.scenario(scenario_id)
        print(f"{scenario_id} {scenario.baseline_digest}")


if __name__ == "__main__":
    main()
