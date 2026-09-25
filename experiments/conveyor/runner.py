"""Conveyor run assembly: what is launched and what counts as an issue.

Same shape as the matched Metronome runner. Conveyor adds release slots,
partial KV eviction, and optional KV prefetch. New KV-management evidence is
written to ``kv_events.log``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

from infra.run.artifacts import RunStore, make_run_id, scan_client_health, scan_worker_fatal
from infra.run.probes import resolve_model_snapshot
from infra.run.workflow import Launch, RunPlan, execute
from infra.trace.collect import (
    apply_scheduler_trace, apply_gpu_activity, apply_transfer_observation, gpu_monitor_command,
)
from infra.trace.gpu_activity import gpu_activity_issues, parse_transfer_events

from .config import ConveyorConfig, model, platform, workload


# The client self-terminates after --duration; the slack covers connection
# ramp and shutdown. Beyond this the watchdog kills the run and records an
# issue instead of hanging an unattended sweep forever.
CLIENT_WATCHDOG_SLACK_S = 120


def worker_command(config: ConveyorConfig, ready_file: Path) -> list[str]:
    selected = model.PRESETS[config.model_preset]
    snapshot = resolve_model_snapshot(selected['id'], selected['revision'])
    cmd = [
        str(config.worker_python),
        "-u",
        str(config.worker_path),
        "--model",
        str(snapshot),
        '--model-family', selected['family'],
        "--port",
        str(platform.WORKER_PORT),
        "--gpu-mem",
        str(config.gpu_memory_utilization),
        "--max-model-len",
        str(config.max_model_len),
        "--max-num-seqs",
        str(config.max_num_seqs),
        "--output-token-cap",
        str(config.output_token_cap),
        "--max-audio-chunks",
        str(workload.MAX_AUDIO_CHUNKS),
        "--initial-context-tokens",
        str(config.initial_context_tokens),
        "--preload-sessions",
        str(config.sessions if config.initial_context_tokens else 0),
        "--host-offload-gib",
        str(config.host_offload_gib),
    ]
    if config.kv_pool_gib is not None:   # optional exact-byte cap; default full pool
        cmd += ["--kv-pool-gib", str(config.kv_pool_gib)]
    if config.enforce_eager:
        cmd += ['--enforce-eager']
    if config.max_num_batched_tokens is not None:
        cmd += ['--max-num-batched-tokens', str(config.max_num_batched_tokens)]
    if config.sync_scheduling and not config.kv_eviction_enabled:
        cmd += ["--sync-scheduling"]
    if config.prefetch != "off":
        cmd += ["--prefetch", config.prefetch]   # push trigger lives in the worker
    if config.kv_eviction_enabled and config.retained_prefix_blocks is None:
        # Fixed-tail mode uses a worker timer and RPC. Retained-prefix mode is
        # applied at the engine's idle transition and needs no worker timer.
        cmd += [
            "--evict-tail-blocks", str(config.evict_tail_blocks),
            "--eviction-delay-s", str(config.eviction_delay_s),
        ]
    cmd += ["--ready-file", str(ready_file)]
    return cmd


def worker_environment(config: ConveyorConfig, run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("OMNI_SESSION_MANAGER", "OMNI_GPU_ACTIVITY", "OMNI_GPU_TRACE_SECONDS",
                "OMNI_TRANSFER_EVENTS", "OMNI_PREFETCH", "OMNI_RETAINED_PREFIX_BLOCKS",
                "OMNI_HOLD_KV_EVICTION", "OMNI_KV_EVICTION", "OMNI_ADMISSION_PROFILE",
                'OMNI_SERVICE_EVENTS', 'OMNI_SERVICE_PRELOAD', 'OMNI_RESIDENT_ONLY', 'OMNI_RESIDENT_LIMIT'):
        env.pop(key, None)
    env.update({
        'OMNI_COPY_SUBMISSION': config.copy_submission,
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
    if config.session_manager:
        env["OMNI_SESSION_MANAGER"] = "1"
        env["OMNI_RESTORE_LEAD_S"] = str(config.restore_lead_s)
        env["OMNI_PREFETCH_MIN_FREE"] = str(config.prefetch_min_free)
        apply_transfer_observation(env, run_dir)
    if config.admission_profile:
        env['OMNI_ADMISSION_PROFILE'] = str(Path(config.admission_profile).resolve())
    if config.cohort_manifest:
        env['OMNI_SERVICE_EVENTS'] = str(run_dir / 'service_events.jsonl')
    if config.resident_control:
        env['OMNI_RESIDENT_ONLY'] = '1'
        env['OMNI_RESIDENT_LIMIT'] = str(config.resident_limit)
        env['OMNI_RESTORE_LEAD_S'] = str(config.restore_lead_s)
        env['OMNI_RETAINED_PREFIX_BLOCKS'] = '1'
    if config.gpu_trace:
        apply_gpu_activity(env, run_dir)
    if config.kv_eviction_enabled:
        # KV management lives in the spawned EngineCore process; inject it
        # by prepending the engine_patch dir AHEAD of the trace collector dir
        # (only the first sitecustomize on sys.path is imported — engine_patch's
        # chain-loads the trace collector when tracing is also on).
        env["OMNI_KV_EVICTION"] = "1"
        env["OMNI_KV_EVENTS_LOG"] = str(run_dir / "kv_events.log")
        if config.prefetch != "off":
            # Engine-side gate for omni_prefetch. The worker flag only enables
            # the release-time trigger; validation ensures eviction is enabled.
            # the PYTHONPATH prepend below always covers it.
            env["OMNI_PREFETCH"] = "1"
            env["OMNI_PREFETCH_MIN_FREE"] = str(config.prefetch_min_free)
        if config.retained_prefix_blocks is not None:
            # Retained-prefix mode evicts beyond K at the idle transition.
            env["OMNI_RETAINED_PREFIX_BLOCKS"] = str(config.retained_prefix_blocks)
            if config.initial_context_tokens:
                # Initial-context preloading is state construction. Release the
                # hold at the barrier without evicting there.
                env["OMNI_HOLD_KV_EVICTION"] = "1"
    if config.kv_eviction_enabled or config.gpu_trace or config.cohort_manifest:
        patch_dir = config.root / "engines" / "conveyor" / "worker" / "engine_patch"
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(patch_dir), str(config.root), env.get("PYTHONPATH", "")])
        )
    return env


def gateway_command(config: ConveyorConfig) -> list[str]:
    cmd = [
        str(config.gateway_path),
        "--port",
        str(platform.GATEWAY_PORT),
        "--worker",
        f"127.0.0.1:{platform.WORKER_PORT}",
        "--period-ms",
        str(workload.PERIOD_MS),
        "--slots",
        str(config.slots),
        "--output-token-cap",
        str(config.output_token_cap),
    ]
    if config.cohort_manifest:
        cmd.append('--admission')
    return cmd


def gateway_environment(run_dir: Path, config=None) -> dict[str, str]:
    env = os.environ.copy()
    env["GW_TICKLOG"] = str(run_dir / "gateway_ticks.log")
    env.pop('GW_SERVICE_EVENTS', None)
    if config is not None and config.cohort_manifest:
        env['GW_SERVICE_EVENTS'] = str(run_dir / 'gateway_frames.jsonl')
    return env


def client_command(config: ConveyorConfig, run_id: str) -> list[str]:
    if config.cohort_manifest:
        return [str(config.worker_python), '-u',
                str(config.root / 'experiments/conveyor/cohort_client.py'),
                '--manifest', str(Path(config.cohort_manifest).resolve()),
                '--uri', f'ws://127.0.0.1:{platform.GATEWAY_PORT}',
                '--output', str(config.output_root / run_id / '.cohort-client.json'),
                '--timeout', str(config.duration_s),
                '--barrier', str(config.sessions if config.capacity_slo else 0)]
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
    issues.extend(scan_client_health(store.file("client.json")))
    kv_events_log = store.file("kv_events.log")
    if kv_events_log.is_file():
        evictions = 0
        with kv_events_log.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                fields = line.split()
                if len(fields) > 1 and fields[1] == "E":
                    evictions += 1
        if not evictions:
            issues.append("KV eviction enabled but kv_events.log recorded zero evictions")
        elif worker_log.is_file():
            eviction_errors = worker_log.read_text(
                encoding="utf-8", errors="replace"
            ).count("KV eviction s")
            if eviction_errors:
                issues.append(f"{eviction_errors} KV-eviction RPC failure(s) (see worker.log)")
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
        output_cap = workload_config.get("output_token_cap")
        if (
            isinstance(sessions, int)
            and not isinstance(sessions, bool)
            and sessions > 0
            and isinstance(output_cap, int)
            and not isinstance(output_cap, bool)
            and output_cap > 0
        ):
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
            if malformed_delivery:
                issues.append("malformed conveyor delivery record in gateway_ticks.log")
    if manifest.is_file() and kv_events_log.is_file():
        # A requested prefetch with no L issue event would masquerade as evidence.
        # Only L lines
        # count — R-only would mean completions without issues (impossible),
        # and demand L lines flow regardless of the mechanism.
        engine = manifest_config.get("engine", {})
        if not isinstance(engine, dict):
            engine = {}
        if engine.get("prefetch", "off") != "off" or engine.get("session_manager"):
            prefetched = 0
            with kv_events_log.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    parts = line.split()
                    if len(parts) > 1 and parts[1] == "L" and "trigger=prefetch" in line:
                        prefetched += 1
            if not prefetched:
                issues.append("prefetch enabled but kv_events.log recorded zero prefetch loads")
    observations = manifest_config.get("observations")
    observations = observations if isinstance(observations, dict) else {}
    engine = manifest_config.get("engine")
    engine = engine if isinstance(engine, dict) else {}
    if observations.get("gpu_trace"):
        issues.extend(gpu_activity_issues(
            store.file("gpu_activity.json"),
            store.file("transfer_events.jsonl") if engine.get("session_manager") else None))
    if engine.get("session_manager"):
        try:
            transfers = parse_transfer_events(store.file("transfer_events.jsonl"))
            if any(row["event"] == "error" for row in transfers):
                issues.append("Session Manager transfer service reported an error")
            if any(row['event'] == 'plan_review' and not row.get('feasible') for row in transfers):
                issues.append('admission plan review reported an infeasible forecast')
            if not any(row["event"] == "published" and row.get("direction") == "H2D" for row in transfers):
                issues.append("Session Manager recorded no completed H2D copies")
        except (OSError, ValueError, KeyError, TypeError):
            issues.append("invalid Session Manager transfer events")
    admission = manifest_config.get('admission') or {}
    if not isinstance(admission, dict):
        issues.append('invalid admission manifest configuration')
        admission = {}
    if admission.get('cohort'):
        try:
            cohort = json.loads(store.file('client.json').read_text())
            expected = {row['id'] for row in admission['cohort']}
            completed = cohort['sessions']
            if (cohort.get('kind') != 'finite_cohort'
                    or cohort.get('total') != len(expected)
                    or cohort.get('completed') != len(expected)
                    or len(completed) != len(expected)
                    or {row['id'] for row in completed} != expected
                    or any(not row.get('completed') or row.get('err') for row in completed)):
                issues.append('finite cohort did not complete every offered session')
        except (OSError, ValueError, TypeError, KeyError):
            issues.append('invalid finite-cohort client result')
    if manifest_config.get('service_slo'):
        from infra.trace.service import evaluate_run
        metrics = evaluate_run(store.path, manifest_config)
        store.write_json('service_metrics.json', metrics)
        if metrics['verdict'] != 'pass':
            issues.append('service SLO ' + metrics['verdict'] + ': ' + '; '.join(metrics['reasons']))
    return issues


def trace_control(config, action):
    return Launch(f'gpu_trace_{action}',
        (str(config.worker_python), str(config.root / 'engines/conveyor/worker/control.py'),
         '--address', f'127.0.0.1:{platform.WORKER_PORT}', '--action', f'gpu_trace_{action}'),
        f'gpu_trace_{action}.log', cwd=config.root)


def plan(config: ConveyorConfig, run_id: str) -> RunPlan:
    run_dir = config.output_root / run_id
    ready_file = run_dir / ".worker-ready"
    return RunPlan(
        experiment='baseline' if config.resident_control else config.experiment_name,
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
                env=gateway_environment(run_dir, config),
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
        ),
        before_client=(trace_control(config, 'start'),) if config.gpu_trace else (),
        after_client=(trace_control(config, 'stop'),) if config.gpu_trace else (),
        client_timeout_s=config.duration_s + CLIENT_WATCHDOG_SLACK_S,
        client_result=(run_dir / '.cohort-client.json' if config.cohort_manifest else
                       config.metronome_root / "results" / "sustained_fd" / f"{run_id}.json"),
        client_scratch_results=tuple(
            Path("/tmp") / f"sfd_{index}.json" for index in range(0 if config.cohort_manifest else config.client_shards)
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
