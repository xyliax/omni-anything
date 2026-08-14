"""Baseline run assembly: what is launched and what counts as an issue.

Everything experiment-specific lives here — commands, environments, and the
issue scanners. The chronological workflow (readiness, watchdog, teardown,
terminal verdict) is ``lab/workflow.py`` and is shared by every experiment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

from lab.artifacts import RunStore, make_run_id, scan_worker_fatal
from lab.probes import resolve_model_snapshot
from lab.workflow import Launch, RunPlan, execute
from tracekit.collect import apply_scheduler_trace, gpu_monitor_command

from .config import BaselineConfig, model, platform, workload


# The client self-terminates after --duration; the slack covers connection
# ramp and shutdown. Beyond this the watchdog kills the run and records an
# issue instead of hanging an unattended sweep forever.
CLIENT_WATCHDOG_SLACK_S = 120


def worker_command(config: BaselineConfig, ready_file: Path) -> list[str]:
    snapshot = resolve_model_snapshot(model.ID, model.REVISION)
    command = [
        str(config.worker_python),
        "-u",
        str(config.worker_path),
        "--model",
        str(snapshot),
        "--port",
        str(platform.WORKER_PORT),
        "--gpu-mem",
        str(config.gpu_memory_utilization),
        "--max-model-len",
        str(config.max_model_len),
        "--max-num-seqs",
        str(config.max_num_seqs),
        "--tpt",
        str(workload.TOKENS_PER_TICK),
        "--max-audio-chunks",
        str(workload.MAX_AUDIO_CHUNKS),
        "--wait-budget-s",
        str(config.wait_budget_s),
        "--ready-file",
        str(ready_file),
    ]
    if config.mode_spec.parallel_ingest:
        command.extend(["--seed-tokens", str(config.seed_tokens)])
    return command


def worker_environment(config: BaselineConfig, run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": str(config.gpu),
        "HF_HUB_OFFLINE": "1",
        "VLLM_NO_USAGE_STATS": "1",
        "METRONOME_ROOT": str(config.metronome_root),
        "METRONOME_STATLOG": str(run_dir / "kv.log"),
        "INGEST_WORKERS": str(config.ingest_workers),
    })
    if config.per_request_logs:
        env["PERREQ_LOG"] = str(run_dir / "per_request.log")
        env["PERITER_LOG"] = str(run_dir / "per_iteration.log")
    if config.trace:
        apply_scheduler_trace(
            env, run_dir / "scheduler.log", run_dir / "scheduler_errors.log"
        )
    return env


def gateway_command(config: BaselineConfig) -> list[str]:
    return [
        str(config.gateway_path),
        "--port",
        str(platform.GATEWAY_PORT),
        "--worker",
        f"127.0.0.1:{platform.WORKER_PORT}",
        "--period-ms",
        str(workload.PERIOD_MS),
        "--tpt",
        str(workload.TOKENS_PER_TICK),
    ]


def client_command(config: BaselineConfig, run_id: str) -> list[str]:
    return [
        str(config.worker_python),
        "-u",
        "experiments/sustained_fd.py",
        "--uri",
        f"ws://127.0.0.1:{platform.GATEWAY_PORT}",
        "--shards",
        str(config.client_shards),
        "--m",
        str(config.sessions // config.client_shards),
        "--duration",
        str(config.duration_s),
        "--chunk-ms",
        str(workload.CHUNK_MS),
        "--budget-ms",
        str(workload.PERIOD_MS),
        "--tag",
        run_id,
    ]


def collect_issues(store: RunStore) -> list[str]:
    """Baseline-specific validation on top of the generic artifact checks."""
    issues: list[str] = []
    scheduler_errors = store.file("scheduler_errors.log")
    if scheduler_errors.is_file() and scheduler_errors.stat().st_size:
        issues.append("scheduler trace reported serialization errors")
    issues.extend(scan_worker_fatal(store.file("worker.log")))
    client_json = store.file("client.json")
    if client_json.is_file():
        client_errors = int(json.loads(client_json.read_text(encoding="utf-8")).get("err", 0))
        if client_errors:
            issues.append(f"client reported {client_errors} session error(s)")
    return issues


def plan(config: BaselineConfig, run_id: str) -> RunPlan:
    run_dir = config.output_root / run_id
    ready_file = run_dir / ".worker-ready"
    client_env = os.environ.copy()
    client_env["FD_PHASE_STAGGER"] = "1"
    return RunPlan(
        experiment=config.experiment_name,
        run_id=run_id,
        root=config.root,
        worker_python=config.worker_python,
        gpu=config.gpu,
        output_root=config.output_root,
        config=config.manifest_config(),
        manifest_extra={"mode": config.mode},
        worker=Launch(
            "worker",
            tuple(worker_command(config, ready_file)),
            "worker.log",
            cwd=config.root,
            env=worker_environment(config, run_dir),
        ),
        ready_file=ready_file,
        startup_timeout_s=config.startup_timeout_s,
        services=(
            Launch(
                "gateway",
                tuple(gateway_command(config)),
                "gateway.log",
                cwd=config.metronome_root,
            ),
            Launch(
                "gpu_monitor",
                tuple(gpu_monitor_command(config.gpu, platform.GPU_SAMPLE_PERIOD_S)),
                "gpu.csv",
                cwd=config.root,
            ),
        ),
        client=Launch(
            "client",
            tuple(client_command(config, run_id)),
            "client.txt",
            cwd=config.metronome_root,
            env=client_env,
        ),
        client_timeout_s=config.duration_s + CLIENT_WATCHDOG_SLACK_S,
        client_result=config.metronome_root / "results" / "sustained_fd" / f"{run_id}.json",
        required_artifacts=config.required_artifact_names(),
        collect_issues=collect_issues,
    )


def run(argv: Sequence[str], **knobs: Any) -> tuple[int, Path]:
    """Execute one run and always leave a terminal ``status.json`` behind.

    ``knobs`` are the per-run ``BaselineConfig`` fields; ``None`` values mean
    "use the default" and are dropped before construction.
    """
    config = BaselineConfig(**{k: v for k, v in knobs.items() if v is not None})
    return execute(plan(config, make_run_id(config.label)), argv)
