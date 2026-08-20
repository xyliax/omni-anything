"""Baseline run assembly: what is launched and what counts as an issue.

Everything experiment-specific lives here — commands, environments, and the
issue scanners. The chronological workflow (readiness, watchdog, teardown,
terminal verdict) is ``infra/run/workflow.py`` and is shared by every experiment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

from infra.run.artifacts import RunStore, make_run_id, scan_client_health, scan_worker_fatal
from infra.run.probes import resolve_model_snapshot
from infra.run.workflow import Launch, RunPlan, execute
from infra.trace.collect import apply_scheduler_trace, gpu_monitor_command

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
        # warm-start barrier: all seed prefills complete before ready (state
        # construction precedes the tick cadence, same semantics as conveyor)
        command.extend(["--pre-seed-sessions", str(config.sessions if config.seed_tokens else 0)])
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
        # honored by the instrumented worker (shared stat logger); the vanilla
        # pin worker keeps its own hardcoded 1 Hz and simply ignores this.
        "OMNI_STATLOG_PERIOD_S": str(config.kv_log_period_s),
    })
    if config.per_request_logs:
        env["PERREQ_LOG"] = str(run_dir / "per_request.log")
        env["PERITER_LOG"] = str(run_dir / "per_iteration.log")
    if config.trace:
        apply_scheduler_trace(
            env,
            run_dir / "scheduler.log",
            run_dir / "scheduler_errors.log",
            run_dir / "residency.log",
        )
    if config.seed_tokens:
        # Seed runs need the frozen-max_tokens fix in the EngineCore process
        # (worker/engine_fix/sitecustomize.py) — without it the seed's
        # max_tokens=1 caps every segment at 1 token while cadence stays
        # green. Prepend AHEAD of the trace collector dir: only the first
        # sitecustomize on sys.path is imported, and engine_fix chain-loads
        # the collector when tracing is also on.
        env["OMNI_SESSION_MAXTOKENS_FIX"] = "1"
        fix_dir = config.root / "engines" / "baseline" / "worker" / "engine_fix"
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(fix_dir), env.get("PYTHONPATH", "")])
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
    manifest_config: dict[str, Any] = {}
    manifest = store.file("manifest.json")
    if manifest.is_file():
        try:
            loaded_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            config_value = loaded_manifest.get("config", {})
            if isinstance(config_value, dict):
                manifest_config = config_value
        except (json.JSONDecodeError, OSError, TypeError, AttributeError):
            # Generic artifact validation owns malformed manifests. Continue
            # scanning independent first-party health signals.
            pass
    mode = manifest_config.get("mode")
    expected_sessions: set[int] | None = None
    expected_quota: int | None = None
    workload_config = manifest_config.get("workload", {})
    if isinstance(workload_config, dict):
        sessions = workload_config.get("sessions")
        quota = workload_config.get("tokens_per_tick")
        if (
            isinstance(sessions, int)
            and not isinstance(sessions, bool)
            and sessions > 0
        ):
            # Fresh-process-per-point makes gateway IDs exactly 1..N.
            expected_sessions = set(range(1, sessions + 1))
        if (
            isinstance(quota, int)
            and not isinstance(quota, bool)
            and quota > 0
        ):
            expected_quota = quota
    scheduler_errors = store.file("scheduler_errors.log")
    if scheduler_errors.is_file() and scheduler_errors.stat().st_size:
        issues.append("scheduler trace reported serialization errors")
    worker_log = store.file("worker.log")
    issues.extend(scan_worker_fatal(worker_log))
    if worker_log.is_file():
        worker_text = worker_log.read_text(encoding="utf-8", errors="replace")
        dead = worker_text.count(" ended: ")
        if dead:
            issues.append(f"{dead} session(s) died mid-run (see worker.log 'ended:' lines)")
        delivery_rows = 0
        short_deliveries = 0
        observed_sessions: set[int] = set()
        full_sessions: set[int] = set()
        malformed_delivery = False
        quota_mismatch = False
        for line in worker_text.splitlines():
            marker = "delivery tpt="
            if marker not in line:
                continue
            payload = line.split(marker, 1)[1]
            tpt_text, separator, delivered = payload.partition(" deliv=")
            if not separator:
                malformed_delivery = True
                continue
            try:
                reported_quota = int(tpt_text)
                counts: list[tuple[int, int]] = []
                for pair in delivered.split(","):
                    session_text, pair_separator, count_text = pair.rpartition(":")
                    if not pair_separator:
                        raise ValueError
                    counts.append((int(session_text), int(count_text)))
            except ValueError:
                malformed_delivery = True
                continue
            session_ids = [session for session, _ in counts]
            if (
                reported_quota <= 0
                or not counts
                or len(set(session_ids)) != len(session_ids)
                or any(session <= 0 or count < 0 for session, count in counts)
                or (
                    expected_sessions is not None
                    and not set(session_ids) <= expected_sessions
                )
            ):
                malformed_delivery = True
                continue
            if expected_quota is not None and reported_quota != expected_quota:
                quota_mismatch = True
            effective_quota = expected_quota or reported_quota
            delivery_rows += 1
            for session, count in counts:
                observed_sessions.add(session)
                if count >= effective_quota:
                    full_sessions.add(session)
                elif session in full_sessions:
                    # As in conveyor, startup fill belongs to TTFA. A session
                    # becomes starvation-eligible after its first full frame.
                    short_deliveries += 1
        if malformed_delivery:
            issues.append("malformed baseline delivery record in worker.log")
        if quota_mismatch:
            issues.append("baseline delivery quota does not match manifest")
        if short_deliveries:
            issues.append(
                f"{short_deliveries} baseline session delivery(ies) below quota "
                "(see worker.log 'delivery' lines)"
            )
        if mode == "paringest" and not delivery_rows:
            issues.append("paringest worker produced no delivery-completeness records")
        if mode == "paringest":
            required_sessions = expected_sessions or observed_sessions
            never_full = required_sessions - full_sessions
            if never_full:
                issues.append(
                    f"{len(never_full)} baseline session(s) never reached full delivery"
                )
    gateway_log = store.file("gateway.log")
    if gateway_log.is_file():
        step_errors = gateway_log.read_text(
            encoding="utf-8", errors="replace"
        ).count("Step error:")
        if step_errors:
            issues.append(f"gateway reported {step_errors} Step error(s)")
    issues.extend(scan_client_health(store.file("client.json")))
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
        client_scratch_results=tuple(
            Path("/tmp") / f"sfd_{index}.json" for index in range(config.client_shards)
        ),
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
