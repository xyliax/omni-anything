"""Build the E3 lead/group tradeoff table and figure from successful runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.e2_kv_conveyor.artifacts import sha256
from experiments.e2_kv_conveyor.runner import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="20260806_main")
    args = parser.parse_args()
    runs_root = ROOT / "results" / "e3_phase_scheduling" / "runs"
    rows = []
    trace_hashes = set()
    for run in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        status = json.loads((run / "status.json").read_text(encoding="utf-8"))
        if status.get("state") != "success":
            continue
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        trace_hashes.add(manifest["compute_trace_sha256"])
        tdma = next(arm for arm in summary["arms"] if arm["arm"] == "conveyor_tdma")
        random = summary["policy_aggregates"]["random"]
        rows.append({
            "run_id": run.name,
            "lead_ms": manifest["config"]["lead_ms"],
            "tdma_group_size": manifest["config"]["tdma_group_size"],
            "link_median_gbps": summary["link_median_gbps"],
            "tdma_valid": tdma["mechanism_valid"],
            "tdma_transfer_miss_rate": tdma["transfer_deadline_miss_rate"],
            "tdma_output_miss_rate": tdma["output_deadline_miss_rate"],
            "tdma_compute_busy_fraction": tdma["compute_busy_fraction"],
            "tdma_staging_peak_sessions": tdma["staging_peak_sessions"],
            "tdma_validated_capacity_wall_ms": tdma["validated_capacity_wall_ms"],
            "random_transfer_miss_rate_median": random["transfer_deadline_miss_rate"]["median"],
            "random_output_miss_rate_median": random["output_deadline_miss_rate"]["median"],
        })
    if not rows:
        raise ValueError(f"no successful E3 runs in {runs_root}")
    if len(trace_hashes) != 1:
        raise ValueError("E3 aggregate cannot mix compute traces")

    output = runs_root.parent / "aggregates" / args.name
    output.mkdir(parents=True, exist_ok=False)
    aggregate = {
        "schema_version": 1,
        "experiment": "e3_phase_scheduling",
        "evidence_level": "trace-driven CUDA mechanism prototype",
        "source_compute_trace_sha256": next(iter(trace_hashes)),
        "source_runs": [row["run_id"] for row in rows],
        "points": rows,
    }
    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lead_rows = sorted(
        (row for row in rows if row["tdma_group_size"] == 7 and row["lead_ms"] != 20),
        key=lambda row: row["lead_ms"],
    )
    group_rows = sorted(
        (row for row in rows if row["lead_ms"] == 20),
        key=lambda row: row["tdma_group_size"],
    )
    figure, axes = plt.subplots(1, 2, figsize=(9.5, 3.8))
    axes[0].plot(
        [row["lead_ms"] for row in lead_rows],
        [row["tdma_staging_peak_sessions"] for row in lead_rows],
        "o-", color="#24796c",
    )
    axes[0].set(xlabel="prefetch lead (ms)", ylabel="peak staged tails (sessions)", ylim=(6.5, 8.3))
    colors = ["#d45b35" if not row["tdma_valid"] else "#24796c" for row in group_rows]
    axes[1].bar(
        [str(row["tdma_group_size"]) for row in group_rows],
        [100 * row["tdma_output_miss_rate"] for row in group_rows],
        color=colors,
    )
    axes[1].set(xlabel="TDMA first-group size", ylabel="output deadline misses (%)")
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="#dddddd", linewidth=0.6)
        axis.set_axisbelow(True)
    figure.suptitle("E3 phase control: late prefetch saves staging; group shape is compute-constrained")
    figure.tight_layout()
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"phase_tradeoffs.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(figure)

    artifacts = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in sorted(output.iterdir())
    }
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_runs": aggregate["source_runs"],
                "artifacts": artifacts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
