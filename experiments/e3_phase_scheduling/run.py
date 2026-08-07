"""CLI for E3: random phase versus TDMA and prefetch-lead sweep."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, replace
from pathlib import Path

from experiments.e2_kv_conveyor.core import SimulationConfig
from experiments.e2_kv_conveyor.runner import DEFAULT_E1_RUN, run_matrix


def csv_numbers(raw: str, cast):
    return [cast(value.strip()) for value in raw.split(",") if value.strip()]


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the E3 random-phase/TDMA scheduling matrix.")
    ap.add_argument("--gpu", type=int, default=3)
    ap.add_argument("--sessions", type=int, default=8)
    ap.add_argument("--ticks", type=int, default=300)
    ap.add_argument("--period-ms", type=float, default=2000)
    ap.add_argument("--growth-tokens", type=int, default=78)
    ap.add_argument("--tail-tokens", type=int, default=4096)
    ap.add_argument("--pool-tokens", type=int, default=73728)
    ap.add_argument("--tdma-group-size", type=int, default=7)
    ap.add_argument(
        "--group-sizes",
        help="comma-separated TDMA group sizes; overrides --tdma-group-size",
    )
    ap.add_argument("--tdma-guard-ms", type=float, default=30)
    ap.add_argument("--leads-ms", default="10,25,50,80,120")
    ap.add_argument("--seeds", default="0,1,2,3,4")
    ap.add_argument("--h2d-samples", type=int, default=25)
    ap.add_argument("--e1-run", default=DEFAULT_E1_RUN)
    ap.add_argument("--worker-python", type=Path, default=Path(".venv-vllm023/bin/python"))
    ap.add_argument("--output-root", type=Path)
    ap.add_argument("--keep-failed", action="store_true")
    ap.add_argument("--plan", action="store_true")
    return ap


def main() -> int:
    args = parser().parse_args()
    leads = csv_numbers(args.leads_ms, float)
    seeds = csv_numbers(args.seeds, int)
    group_sizes = (
        csv_numbers(args.group_sizes, int)
        if args.group_sizes is not None
        else [args.tdma_group_size]
    )
    if not leads or not seeds or not group_sizes:
        parser().error("lead, seed, and group-size lists must be non-empty")
    base = SimulationConfig(
        sessions=args.sessions,
        ticks=args.ticks,
        period_ms=args.period_ms,
        growth_tokens_per_tick=args.growth_tokens,
        tail_tokens=args.tail_tokens,
        pool_tokens=args.pool_tokens,
        lead_ms=max(leads),
        tdma_group_size=group_sizes[0],
        tdma_guard_ms=args.tdma_guard_ms,
    )
    # run_matrix currently has one config-wide lead. Run one immutable directory per lead so
    # each manifest describes exactly one scheduling point; seeds remain repeated arms.
    plans = []
    for lead in leads:
        for group_size in group_sizes:
            config = replace(base, lead_ms=lead, tdma_group_size=group_size)
            arms = [("resident_sync", False, "synchronized", 0)]
            arms += [(f"conveyor_random_seed{seed}", True, "random", seed) for seed in seeds]
            # TDMA is deterministic; repeating it under different random seeds
            # would duplicate evidence without adding a replicate.
            arms.append(("conveyor_tdma", True, "tdma", 0))
            plans.append((config, arms))
    if args.plan:
        print(json.dumps([
            {"config": asdict(config), "arms": arms} for config, arms in plans
        ], indent=2))
        return 0
    for config, arms in plans:
        path = run_matrix(
            experiment="e3_phase_scheduling",
            label=(
                f"lead{int(config.lead_ms)}_group{config.tdma_group_size}"
                f"_n{args.sessions}"
            ),
            config=config,
            arms=arms,
            gpu=args.gpu,
            h2d_samples=args.h2d_samples,
            e1_run=args.e1_run,
            worker_python=Path(os.path.abspath(args.worker_python.expanduser())),
            output_root=args.output_root.resolve() if args.output_root else None,
            keep_failed=args.keep_failed,
            record_transfers=False,
        )
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
