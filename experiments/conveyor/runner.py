"""Conveyor run assembly: what is launched and what counts as an issue.

Same shape as the baseline runner (commands, environments, and issue scanners
live here; the chronological workflow is ``infra/run/workflow.py``). The differences
are the mechanisms: the staggered gateway takes ``--slots`` and writes a
per-firing tick log, the take-from-stock worker has no wait budget, and park
runs inject the engine patch plus scan park.log for silent failures.
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

from .config import ConveyorConfig, model, platform, workload


# The client self-terminates after --duration; the slack covers connection
# ramp and shutdown. Beyond this the watchdog kills the run and records an
# issue instead of hanging an unattended sweep forever.
CLIENT_WATCHDOG_SLACK_S = 120


def worker_command(config: ConveyorConfig, ready_file: Path) -> list[str]:
    snapshot = resolve_model_snapshot(model.ID, model.REVISION)
    cmd = [
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
        "--seed-tokens",
        str(config.seed_tokens),
        "--pre-seed-sessions",
        str(config.sessions if config.seed_tokens else 0),
        "--host-offload-gib",
        str(config.host_offload_gib),
    ]
    if config.kv_pool_gib is not None:   # optional exact-byte cap; default full pool
        cmd += ["--kv-pool-gib", str(config.kv_pool_gib)]
    if config.sync_scheduling and not config.park_enabled:
        cmd += ["--sync-scheduling"]   # control arm pinning; park implies it
    if config.prefetch != "off":
        cmd += ["--prefetch", config.prefetch]   # push trigger lives in the worker
    if config.park_enabled and config.park_keep_blocks is None:
        # fixed-tail mode: worker-side timer + RPC. Quota mode is engine-side
        # auto-park-on-stop and needs no worker knobs (see worker_environment).
        cmd += [
            "--park-tail-blocks", str(config.park_tail_blocks),
            "--park-delay-s", str(config.park_delay_s),
        ]
    cmd += ["--ready-file", str(ready_file)]
    return cmd


def worker_environment(config: ConveyorConfig, run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": str(config.gpu),
        "HF_HUB_OFFLINE": "1",
        "VLLM_NO_USAGE_STATS": "1",
        "METRONOME_ROOT": str(config.metronome_root),
        "METRONOME_STATLOG": str(run_dir / "kv.log"),
        "INGEST_WORKERS": str(config.ingest_workers),
        "OMNI_STATLOG_PERIOD_S": str(config.kv_log_period_s),
        # any sitecustomize (trace collector or engine_patch) imports vllm
        # before the worker's own setdefault runs; pin the log level here.
        "VLLM_LOGGING_LEVEL": os.environ.get("VLLM_LOGGING_LEVEL", "WARNING"),
    })
    if config.trace:
        env["PERREQ_LOG"] = str(run_dir / "per_request.log")
        env["PERITER_LOG"] = str(run_dir / "per_iteration.log")
        apply_scheduler_trace(
            env,
            run_dir / "scheduler.log",
            run_dir / "scheduler_errors.log",
            run_dir / "residency.log",
        )
    if config.park_enabled:
        # The park primitive lives in the spawned EngineCore process; inject it
        # by prepending the engine_patch dir AHEAD of the trace collector dir
        # (only the first sitecustomize on sys.path is imported — engine_patch's
        # chain-loads the trace collector when tracing is also on).
        env["OMNI_PARK_PATCH"] = "1"
        env["OMNI_PARK_LOG"] = str(run_dir / "park.log")
        if config.prefetch != "off":
            # engine-side gate for omni_reload (the worker's --prefetch only
            # arms the push trigger); prefetch requires park (validated), so
            # the PYTHONPATH prepend below always covers it.
            env["OMNI_PREFETCH"] = "1"
            env["OMNI_PREFETCH_MIN_FREE"] = str(config.prefetch_min_free)
        if config.park_keep_blocks is not None:
            # quota mode: the engine parks each session the instant its slice
            # stops (zero delay, no RPC) — everything beyond K blocks evicted.
            env["OMNI_PARK_KEEP"] = str(config.park_keep_blocks)
            if config.seed_tokens:
                # warm start is state construction: hold auto-park until the
                # barrier's finalize releases the hold without parking; the
                # first normal segment stop establishes the parked posture.
                env["OMNI_PARK_HOLD"] = "1"
        patch_dir = config.root / "engines" / "conveyor" / "worker" / "engine_patch"
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(patch_dir), env.get("PYTHONPATH", "")])
        )
    return env


def gateway_command(config: ConveyorConfig) -> list[str]:
    return [
        str(config.gateway_path),
        "--port",
        str(platform.GATEWAY_PORT),
        "--worker",
        f"127.0.0.1:{platform.WORKER_PORT}",
        "--period-ms",
        str(workload.PERIOD_MS),
        "--slots",
        str(config.slots),
        "--tpt",
        str(workload.TOKENS_PER_TICK),
    ]


def gateway_environment(run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["GW_TICKLOG"] = str(run_dir / "gateway_ticks.log")
    return env


def client_command(config: ConveyorConfig, run_id: str) -> list[str]:
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
    """Conveyor-specific validation on top of the generic artifact checks."""
    issues: list[str] = []
    scheduler_errors = store.file("scheduler_errors.log")
    if scheduler_errors.is_file() and scheduler_errors.stat().st_size:
        issues.append("scheduler trace reported serialization errors")
    issues.extend(scan_worker_fatal(store.file("worker.log")))
    worker_log = store.file("worker.log")
    if worker_log.is_file():
        # a dead session keeps the run cadence-green (silent failure, FINDING-B1):
        # the engine-side death log is the only place it shows.
        dead = worker_log.read_text(encoding="utf-8", errors="replace").count(" ended: ")
        if dead:
            issues.append(f"{dead} session(s) died mid-run (see worker.log 'ended:' lines)")
    gateway_log = store.file("gateway.log")
    if gateway_log.is_file():
        gateway_text = gateway_log.read_text(encoding="utf-8", errors="replace")
        step_errors = gateway_text.count("Step error:")
        if step_errors:
            issues.append(f"gateway reported {step_errors} Step error(s)")
        # a slow-but-alive engine is equally cadence-green under take-from-stock:
        # short deliveries only show as the gateway's [starve] lines.
        starved = gateway_text.count("[starve]")
        if starved:
            issues.append(
                f"{starved} slot firing(s) short-delivered tokens "
                "(engine behind; see gateway.log '[starve]' lines)"
            )
    issues.extend(scan_client_health(store.file("client.json")))
    park_log = store.file("park.log")
    if park_log.is_file():
        # park enabled but never effective would masquerade as evidence (same
        # shape as the dead-session and [starve] scans above).
        # count park lines only: S/L/R lines flow whenever the mirror moves,
        # so raw line count would pass a run where park itself never fired.
        parks = 0
        with park_log.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                fields = line.split()
                if len(fields) > 1 and fields[1].startswith("req="):
                    parks += 1
        if not parks:
            issues.append("park enabled but park.log recorded zero parks")
        elif worker_log.is_file():
            # refusals (incl. unknown request) are normal per-cycle outcomes;
            # only RPC transport failures are never expected.
            park_errors = worker_log.read_text(
                encoding="utf-8", errors="replace"
            ).count("RPC failed")
            if park_errors:
                issues.append(f"{park_errors} park RPC failure(s) (see worker.log)")
    manifest = store.file("manifest.json")
    manifest_config: dict[str, Any] = {}
    if manifest.is_file():
        try:
            loaded_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            config_value = loaded_manifest.get("config", {})
            if isinstance(config_value, dict):
                manifest_config = config_value
        except (json.JSONDecodeError, OSError, TypeError, AttributeError):
            # Generic artifact validation owns malformed manifests. Keep this
            # experiment-specific scanner total so it can still report the
            # independent health failures visible in the remaining logs.
            pass
    workload_config = manifest_config.get("workload", {})
    if isinstance(workload_config, dict):
        sessions = workload_config.get("sessions")
        quota = workload_config.get("tokens_per_tick")
        if (
            isinstance(sessions, int)
            and not isinstance(sessions, bool)
            and sessions > 0
            and isinstance(quota, int)
            and not isinstance(quota, bool)
            and quota > 0
        ):
            full_sessions: set[int] = set()
            malformed_delivery = False
            tick_log = store.file("gateway_ticks.log")
            if tick_log.is_file():
                for line in tick_log.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines():
                    fields = {
                        key: value
                        for field in line.split()
                        if "=" in field
                        for key, value in (field.split("=", 1),)
                    }
                    try:
                        served = int(fields["n"])
                    except (KeyError, ValueError):
                        malformed_delivery = True
                        continue
                    if served == 0:
                        # Empty startup/teardown firings are grid evidence, not
                        # delivery evidence, and intentionally carry no deliv=.
                        continue
                    try:
                        delivered = [
                            tuple(int(value) for value in pair.rsplit(":", 1))
                            for pair in fields["deliv"].split(",")
                        ]
                    except (KeyError, ValueError):
                        malformed_delivery = True
                        continue
                    session_ids = [session for session, _ in delivered]
                    if (
                        served < 0
                        or len(delivered) != served
                        or len(set(session_ids)) != len(session_ids)
                        or any(session <= 0 or count < 0 for session, count in delivered)
                    ):
                        malformed_delivery = True
                        continue
                    full_sessions.update(
                        session for session, count in delivered if count >= quota
                    )
            if malformed_delivery:
                issues.append("malformed conveyor delivery record in gateway_ticks.log")
            expected_sessions = set(range(1, sessions + 1))
            never_full = expected_sessions - full_sessions
            if never_full:
                issues.append(
                    f"{len(never_full)} conveyor session(s) never reached full delivery"
                )
    if manifest.is_file() and park_log.is_file():
        # same shape as the zero-park scan: a requested prefetch that never
        # materialized anything would masquerade as evidence. Only L lines
        # count — R-only would mean completions without issues (impossible),
        # and demand L lines flow regardless of the mechanism.
        engine = manifest_config.get("engine", {})
        if not isinstance(engine, dict):
            engine = {}
        if engine.get("prefetch", "off") != "off":
            prefetched = 0
            with park_log.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    parts = line.split()
                    if len(parts) > 1 and parts[1] == "L" and "trigger=prefetch" in line:
                        prefetched += 1
            if not prefetched:
                issues.append("prefetch enabled but park.log recorded zero prefetch loads")
    return issues


def plan(config: ConveyorConfig, run_id: str) -> RunPlan:
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
                env=gateway_environment(run_dir),
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

    ``knobs`` are the per-run ``ConveyorConfig`` fields; ``None`` values mean
    "use the default" and are dropped before construction.
    """
    config = ConveyorConfig(**{k: v for k, v in knobs.items() if v is not None})
    return execute(plan(config, make_run_id(config.label)), argv)
