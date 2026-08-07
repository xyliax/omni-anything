"""Process orchestration for one artifact-safe E1 run.

This module deliberately contains the chronological workflow.  Configuration,
host inspection, and evidence bookkeeping live in neighboring modules so the
control flow remains short enough to audit.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any, Sequence

from .artifacts import SCHEMA_VERSION, ArtifactStore, make_run_id, utc_now
from .config import RunConfig
from .preflight import (
    collect_git,
    collect_gpu,
    collect_host,
    collect_cuda_layout,
    collect_python_environment,
    collect_third_party_pins,
    find_fix1_marker,
    resolve_model_revision,
    resolve_model_path,
    run_preflight,
)


WORKER_FATAL = ("EngineCore failed to start", "CUDA out of memory", "OutOfMemoryError")


class RunSignal(KeyboardInterrupt):
    """A termination signal converted into normal runner unwinding."""

    def __init__(self, signum: int):
        super().__init__(signal.Signals(signum).name)
        self.signum = signum


def raise_run_signal(signum: int, _frame: object) -> None:
    raise RunSignal(signum)


@dataclass
class ProcessGroup:
    """Processes started in private sessions and terminated only by recorded PGID."""

    processes: list[subprocess.Popen[bytes]] = field(default_factory=list)
    handles: list[IO[bytes]] = field(default_factory=list)

    def start(
        self,
        command: Sequence[str],
        log_path: Path,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> subprocess.Popen[bytes]:
        handle = log_path.open("xb")
        try:
            process = subprocess.Popen(
                list(command),
                cwd=cwd,
                env=env,
                stdout=handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except BaseException:
            handle.close()
            raise
        self.handles.append(handle)
        self.processes.append(process)
        return process

    def cleanup(self, timeout_s: float = 10.0) -> None:
        live = [process for process in self.processes if process.poll() is None]
        for process in reversed(live):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + timeout_s
        while live and time.monotonic() < deadline:
            live = [process for process in live if process.poll() is None]
            if live:
                time.sleep(0.1)
        for process in reversed(live):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for process in self.processes:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
        for handle in self.handles:
            handle.close()


def build_manifest(
    config: RunConfig,
    argv: Sequence[str],
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Collect provenance before creating the run directory or launching a GPU process."""
    git = collect_git(config.root)
    software = collect_python_environment(config.worker_python)
    fix1 = find_fix1_marker(config.worker_python)
    cuda_layout = collect_cuda_layout(config.worker_python)
    run_id = make_run_id(config, git["commit"])
    ready_file = config.output_root / run_id / ".worker-ready"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "experiment": "e1",
        "mode": config.mode,
        "started_at": utc_now(),
        "command": list(argv),
        "process_commands": {
            "worker": worker_command(config, ready_file),
            "gateway": gateway_command(config),
            "client": client_command(config, run_id),
            "gpu_monitor": gpu_monitor_command(config),
        },
        "git": git,
        "third_party": collect_third_party_pins(config.root),
        "model": {"id": config.model, "revision": resolve_model_revision(config)},
        "software": {**software, "fix1": fix1, "cuda_layout": cuda_layout},
        "hardware": {"host": collect_host(), "gpu": collect_gpu(config.gpu)},
        "config": config.manifest_config(),
    }
    return run_id, manifest, git, software, cuda_layout


def worker_command(config: RunConfig, ready_file: Path) -> list[str]:
    model = resolve_model_path(config) or config.model
    command = [
        str(config.worker_python),
        "-u",
        str(config.worker_path),
        "--model",
        str(model),
        "--port",
        str(config.worker_port),
        "--gpu-mem",
        str(config.gpu_memory_utilization),
        "--max-model-len",
        str(config.max_model_len),
        "--max-num-seqs",
        str(config.max_num_seqs),
        "--tpt",
        str(config.tokens_per_tick),
        "--max-audio-chunks",
        str(config.max_audio_chunks),
        "--window-frames",
        "0",
        "--wait-budget-s",
        str(config.wait_budget_s),
        "--ready-file",
        str(ready_file),
    ]
    if config.mode == "paringest":
        command.extend(["--seed-tokens", str(config.seed_tokens)])
    return command


def worker_environment(config: RunConfig, store: ArtifactStore) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": str(config.gpu),
        "HF_HUB_OFFLINE": "1",
        "VLLM_NO_USAGE_STATS": "1",
        "METRONOME_ROOT": str(config.metronome_root),
        "METRONOME_STATLOG": str(store.file("kv.log")),
        "INGEST_WORKERS": str(config.ingest_workers),
    })
    if config.trace and config.mode == "paringest":
        env["PERREQ_LOG"] = str(store.file("per_request.log"))
        env["PERITER_LOG"] = str(store.file("per_iteration.log"))
    if config.trace:
        env["OMNI_SCHEDULER_TRACE"] = str(store.file("scheduler.log"))
        env["OMNI_SCHEDULER_TRACE_ERRORS"] = str(store.file("scheduler_errors.log"))
        trace_path = str(
            config.root
            / "observability"
            / "vllm_scheduler_trace"
        )
        env["PYTHONPATH"] = trace_path + os.pathsep + env.get("PYTHONPATH", "")
    return env


def wait_for_worker(process: subprocess.Popen[bytes], ready_file: Path, log: Path, timeout_s: int) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if ready_file.is_file():
            return
        if process.poll() is not None:
            tail = tail_text(log, 12)
            raise RuntimeError(f"worker exited before readiness (code {process.returncode})\n{tail}")
        if log.is_file():
            text = log.read_text(encoding="utf-8", errors="replace")
            if any(marker in text for marker in WORKER_FATAL):
                raise RuntimeError(f"worker reported a fatal startup error\n{tail_text(log, 12)}")
        time.sleep(3)
    raise TimeoutError(f"worker did not become ready within {timeout_s}s")


def tail_text(path: Path, lines: int) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def gateway_command(config: RunConfig) -> list[str]:
    return [
        str(config.gateway_path),
        "--port",
        str(config.gateway_port),
        "--worker",
        f"127.0.0.1:{config.worker_port}",
        "--period-ms",
        str(config.period_ms),
        "--tpt",
        str(config.tokens_per_tick),
    ]


def client_command(config: RunConfig, run_id: str) -> list[str]:
    return [
        str(config.client_python),
        "-u",
        "experiments/sustained_fd.py",
        "--uri",
        f"ws://127.0.0.1:{config.gateway_port}",
        "--shards",
        str(config.client_shards),
        "--m",
        str(config.sessions // config.client_shards),
        "--duration",
        str(config.duration_s),
        "--chunk-ms",
        str(config.chunk_ms),
        "--budget-ms",
        str(config.period_ms),
        "--tag",
        run_id,
    ]


def gpu_monitor_command(config: RunConfig) -> list[str]:
    return [
        "nvidia-smi",
        f"--id={config.gpu}",
        "--query-gpu=timestamp,index,uuid,name,utilization.gpu,memory.used,power.draw",
        "--format=csv,noheader,nounits",
        "--loop=5",
    ]


def import_client_result(config: RunConfig, store: ArtifactStore, run_id: str) -> None:
    source = config.metronome_root / "results" / "sustained_fd" / f"{run_id}.json"
    if not source.is_file():
        raise RuntimeError(f"client did not produce {source}")
    with source.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    payload["artifact"] = {"schema_version": SCHEMA_VERSION, "run_id": run_id}
    store.write_json("client.json", payload)
    source.unlink()


def run(config: RunConfig, argv: Sequence[str]) -> tuple[int, Path]:
    """Execute one run and always leave a terminal ``status.json`` behind."""
    run_id, manifest, git, software, cuda_layout = build_manifest(config, argv)
    store = ArtifactStore.create(config.output_root, run_id, manifest)
    processes = ProcessGroup()
    exit_code = 1
    requested_state: str | None = None
    error: str | None = None
    ready_file = store.file(".worker-ready")
    handled_signals = (signal.SIGTERM, signal.SIGHUP)
    previous_handlers = {signum: signal.getsignal(signum) for signum in handled_signals}
    for signum in handled_signals:
        signal.signal(signum, raise_run_signal)

    try:
        store.write_status(state="running", phase="preflight", started_at=manifest["started_at"])
        run_preflight(config, git, software, manifest["software"]["fix1"], cuda_layout)

        store.write_status(state="running", phase="worker-startup", started_at=manifest["started_at"])
        worker = processes.start(
            worker_command(config, ready_file),
            store.file("worker.log"),
            cwd=config.root,
            env=worker_environment(config, store),
        )
        wait_for_worker(worker, ready_file, store.file("worker.log"), config.startup_timeout_s)

        gateway = processes.start(
            gateway_command(config),
            store.file("gateway.log"),
            cwd=config.metronome_root,
        )
        time.sleep(3)
        if gateway.poll() is not None:
            raise RuntimeError(f"gateway exited during startup (code {gateway.returncode})")

        processes.start(
            gpu_monitor_command(config),
            store.file("gpu.csv"),
            cwd=config.root,
        )
        client_env = os.environ.copy()
        client_env["FD_PHASE_STAGGER"] = "1"
        store.write_status(state="running", phase="client", started_at=manifest["started_at"])
        client = processes.start(
            client_command(config, run_id),
            store.file("client.txt"),
            cwd=config.metronome_root,
            env=client_env,
        )
        exit_code = client.wait()
        if exit_code:
            raise RuntimeError(f"client exited with code {exit_code}")
        import_client_result(config, store, run_id)
    except RunSignal as exc:
        exit_code = 128 + exc.signum
        requested_state = "interrupted"
        error = f"run interrupted by {signal.Signals(exc.signum).name}"
    except KeyboardInterrupt:
        exit_code = 130
        requested_state = "interrupted"
        error = "run interrupted by SIGINT"
    except Exception as exc:
        exit_code = exit_code or 1
        error = f"{type(exc).__name__}: {exc}"
        with store.file("runner_error.log").open("x", encoding="utf-8") as handle:
            traceback.print_exc(file=handle)
    finally:
        processes.cleanup()
        ready_file.unlink(missing_ok=True)
        status = store.finalize(
            config,
            exit_code=exit_code,
            requested_state=requested_state,
            error=error,
        )
        for signum, previous in previous_handlers.items():
            signal.signal(signum, previous)

    print(tail_text(store.file("client.txt"), 12))
    print(f"run_id: {run_id}")
    print(f"artifacts: {store.path}")
    print(f"status: {status['state']}")
    return (0 if status["state"] == "success" else exit_code or 1), store.path
