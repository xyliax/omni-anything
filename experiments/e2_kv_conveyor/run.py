"""CLI for E2: paired resident versus conveyor capacity experiment."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from .core import SimulationConfig
from .runner import DEFAULT_E1_RUN, run_matrix


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the paired E2 KV-conveyor mechanism experiment.")
    ap.add_argument("--gpu", type=int, default=3)
    ap.add_argument("--sessions", type=int, default=8)
    ap.add_argument("--ticks", type=int, default=300)
    ap.add_argument("--period-ms", type=float, default=2000)
    ap.add_argument("--growth-tokens", type=int, default=78)
    ap.add_argument("--initial-context", type=int, default=0)
    ap.add_argument("--tail-tokens", type=int, default=4096)
    ap.add_argument("--pool-tokens", type=int, default=73728)
    ap.add_argument("--lead-ms", type=float, default=20)
    ap.add_argument("--tdma-group-size", type=int, default=7)
    ap.add_argument("--tdma-guard-ms", type=float, default=30)
    ap.add_argument("--h2d-samples", type=int, default=15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--e1-run", default=DEFAULT_E1_RUN)
    ap.add_argument("--worker-python", type=Path, default=Path(".venv-vllm023/bin/python"))
    ap.add_argument("--output-root", type=Path)
    ap.add_argument("--keep-failed", action="store_true")
    ap.add_argument("--plan", action="store_true")
    return ap


def main() -> int:
    args = parser().parse_args()
    config = SimulationConfig(
        sessions=args.sessions,
        ticks=args.ticks,
        period_ms=args.period_ms,
        growth_tokens_per_tick=args.growth_tokens,
        initial_context_tokens=args.initial_context,
        tail_tokens=args.tail_tokens,
        pool_tokens=args.pool_tokens,
        lead_ms=args.lead_ms,
        tdma_group_size=args.tdma_group_size,
        tdma_guard_ms=args.tdma_guard_ms,
    )
    arms = [
        ("resident_sync", False, "synchronized", args.seed),
        ("conveyor_tdma", True, "tdma", args.seed),
    ]
    if args.plan:
        print(json.dumps({"config": asdict(config), "arms": arms}, indent=2))
        return 0
    path = run_matrix(
        experiment="e2_kv_conveyor",
        label=f"n{args.sessions}_tail{args.tail_tokens}_r{args.seed}",
        config=config,
        arms=arms,
        gpu=args.gpu,
        h2d_samples=args.h2d_samples,
        e1_run=args.e1_run,
        worker_python=Path(os.path.abspath(args.worker_python.expanduser())),
        output_root=args.output_root.resolve() if args.output_root else None,
        keep_failed=args.keep_failed,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
