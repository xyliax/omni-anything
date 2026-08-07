"""Aggregate successful E2 repetitions into one provenance-bearing result."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from .artifacts import sha256
from .runner import ROOT


def load_runs(runs_root: Path) -> list[tuple[Path, dict, dict]]:
    rows = []
    for run in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        status = json.loads((run / "status.json").read_text(encoding="utf-8"))
        if status.get("state") != "success":
            continue
        summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        rows.append((run, summary, manifest))
    if not rows:
        raise ValueError(f"no successful E2 runs in {runs_root}")
    trace_hashes = {manifest["compute_trace_sha256"] for _, _, manifest in rows}
    if len(trace_hashes) != 1:
        raise ValueError("E2 aggregate cannot mix compute traces")
    return rows


def distribution(values: list[float]) -> dict:
    return {
        "count": len(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="20260806_main")
    args = parser.parse_args()
    runs_root = ROOT / "results" / "e2_kv_conveyor" / "runs"
    rows = load_runs(runs_root)
    output = runs_root.parent / "aggregates" / args.name
    output.mkdir(parents=True, exist_ok=False)

    extensions = [float(summary["capacity_extension_tdma_vs_resident"]) for _, summary, _ in rows]
    bandwidth = [float(summary["link_median_gbps"]) for _, summary, _ in rows]
    conveyor = [
        next(arm for arm in summary["arms"] if arm["arm"] == "conveyor_tdma")
        for _, summary, _ in rows
    ]
    aggregate = {
        "schema_version": 1,
        "experiment": "e2_kv_conveyor",
        "evidence_level": "trace-driven CUDA mechanism prototype",
        "claim_boundary": rows[0][2]["claim_boundary"],
        "source_runs": [run.name for run, _, _ in rows],
        "source_compute_trace_sha256": rows[0][2]["compute_trace_sha256"],
        "link_median_gbps": distribution(bandwidth),
        "capacity_extension": distribution(extensions),
        "all_mechanism_valid": all(arm["mechanism_valid"] for arm in conveyor),
        "transfer_deadline_misses": sum(arm["transfer_deadline_misses"] for arm in conveyor),
        "output_deadline_misses": sum(arm["output_deadline_misses"] for arm in conveyor),
        "staging_peak_sessions": distribution(
            [float(arm["staging_peak_sessions"]) for arm in conveyor]
        ),
    }
    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
    repeats = list(range(1, len(rows) + 1))
    axes[0].plot(repeats, bandwidth, "o-", color="#24796c", linewidth=1.5)
    axes[0].axhline(statistics.median(bandwidth), color="#555555", linestyle="--", linewidth=1)
    axes[0].set(xlabel="independent calibration", ylabel="pinned H2D (GB/s)", xticks=repeats)
    baseline_wall = rows[0][1]["arms"][0]["validated_capacity_wall_ms"] / 1000
    conveyor_wall = conveyor[0]["validated_capacity_wall_ms"] / 1000
    axes[1].bar(["resident", "conveyor 7+1"], [baseline_wall, conveyor_wall], color=["#777777", "#d45b35"])
    axes[1].set(ylabel="validated capacity wall (s)", ylim=(0, conveyor_wall * 1.18))
    axes[1].bar_label(axes[1].containers[0], fmt="%.0f s", padding=3)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="#dddddd", linewidth=0.6)
        axis.set_axisbelow(True)
    figure.suptitle("E2 mechanism result: stable link calibration, modest capacity extension")
    figure.tight_layout()
    for suffix in ("png", "pdf"):
        figure.savefig(output / f"capacity_summary.{suffix}", dpi=180, bbox_inches="tight")
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
