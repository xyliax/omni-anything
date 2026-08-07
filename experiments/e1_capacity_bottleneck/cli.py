"""Command-line interface for the unified E1 runner."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .config import DEFAULT_MODEL, MODES, RunConfig
from .runner import client_command, gateway_command, run, worker_command


ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Run one fresh-worker E1 point into a new immutable evidence directory.",
    )
    ap.add_argument("--mode", required=True, choices=sorted(MODES), help="implementation under test")
    ap.add_argument(
        "--trace",
        action="store_true",
        help="enable detailed tracing without changing the selected implementation",
    )
    ap.add_argument("--gpu", type=int, default=int(_env("GPUS", "3")))
    ap.add_argument("--n", dest="sessions", type=int, default=int(_env("N", "8")))
    ap.add_argument("--duration", dest="duration_s", type=float, default=float(_env("DUR", "600")))
    ap.add_argument("--model", default=_env("MODEL", DEFAULT_MODEL))
    ap.add_argument("--model-revision", default=os.environ.get("MODEL_REVISION"))
    ap.add_argument("--period-ms", type=int, default=int(_env("PERIOD_MS", "2000")))
    ap.add_argument("--chunk-ms", type=int, default=int(_env("CHUNK_MS", "20")))
    ap.add_argument("--mml", dest="max_model_len", type=int, default=int(_env("MML", "32768")))
    ap.add_argument("--max-num-seqs", type=int, default=int(_env("MAXSEQS", "16")))
    ap.add_argument("--gpu-mem", dest="gpu_memory_utilization", type=float, default=float(_env("GPU_MEM", "0.9")))
    ap.add_argument("--tpt", dest="tokens_per_tick", type=int, default=int(_env("TPT", "25")))
    ap.add_argument("--max-audio-chunks", type=int, default=int(_env("MAX_AUDIO_CHUNKS", "64")))
    ap.add_argument("--wait-budget-s", type=float, default=float(_env("WAIT_BUDGET_S", "1.6")))
    ap.add_argument("--seed-tokens", type=int, default=int(_env("SEED_TOKENS", "0")))
    ap.add_argument("--ingest-workers", type=int, default=int(_env("INGEST_WORKERS", "8")))
    ap.add_argument("--worker-port", type=int, default=int(_env("WPORT", "50054")))
    ap.add_argument("--gateway-port", type=int, default=int(_env("GPORT", "8907")))
    ap.add_argument("--client-shards", type=int, default=None)
    ap.add_argument("--startup-timeout", dest="startup_timeout_s", type=int, default=360)
    ap.add_argument("--quiet-seconds", type=int, default=60)
    ap.add_argument("--output-root", type=Path, default=None)
    ap.add_argument("--worker-python", type=Path, default=Path(_env("VLLM_PYTHON", ".venv-vllm023/bin/python")))
    ap.add_argument("--client-python", default=os.environ.get("CLIENT_PYTHON"))
    ap.add_argument("--label", help="optional human label embedded in the unique run ID")
    ap.add_argument("--allow-dirty", action="store_true", help="run from a dirty tree and record its status")
    ap.add_argument("--skip-gpu-quiet", action="store_true", help="skip the shared-GPU quiet window check")
    ap.add_argument("--skip-environment-check", action="store_true", help="skip exact vLLM/FIX 1 checks")
    ap.add_argument("--plan", action="store_true", help="print resolved config and commands without side effects")
    return ap


def config_from_args(args: argparse.Namespace) -> RunConfig:
    shards = args.client_shards if args.client_shards is not None else (4 if args.sessions >= 32 else 1)
    return RunConfig(
        root=ROOT,
        mode=args.mode,
        trace=args.trace,
        gpu=args.gpu,
        sessions=args.sessions,
        duration_s=args.duration_s,
        model=args.model,
        model_revision=args.model_revision,
        period_ms=args.period_ms,
        chunk_ms=args.chunk_ms,
        max_model_len=args.max_model_len,
        max_num_seqs=args.max_num_seqs,
        gpu_memory_utilization=args.gpu_memory_utilization,
        tokens_per_tick=args.tokens_per_tick,
        max_audio_chunks=args.max_audio_chunks,
        wait_budget_s=args.wait_budget_s,
        seed_tokens=args.seed_tokens,
        ingest_workers=args.ingest_workers,
        worker_port=args.worker_port,
        gateway_port=args.gateway_port,
        client_shards=shards,
        startup_timeout_s=args.startup_timeout_s,
        quiet_seconds=args.quiet_seconds,
        output_root=args.output_root,
        worker_python=args.worker_python,
        client_python=args.client_python,
        allow_dirty=args.allow_dirty,
        skip_gpu_quiet=args.skip_gpu_quiet,
        skip_environment_check=args.skip_environment_check,
        label=args.label,
    )


def print_plan(config: RunConfig) -> None:
    placeholder = Path("<run-dir>/.worker-ready")
    plan = {
        "config": config.manifest_config(),
        "output_root": str(config.output_root),
        "worker_python": str(config.worker_python),
        "commands": {
            "worker": worker_command(config, placeholder),
            "gateway": gateway_command(config),
            "client": client_command(config, "<unique-run-id>"),
        },
    }
    print(json.dumps(plan, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = config_from_args(args)
    except ValueError as exc:
        parser().error(str(exc))
    if args.plan:
        print_plan(config)
        return 0
    code, _ = run(
        config,
        [
            sys.executable,
            "-m",
            "experiments.e1_capacity_bottleneck.cli",
            *(argv or sys.argv[1:]),
        ],
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
