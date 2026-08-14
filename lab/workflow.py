"""The one chronological run workflow, shared by every experiment.

An experiment runner declares WHAT to launch (a :class:`RunPlan`: argv, env,
cwd, evidence names, issue scanners); this module owns WHEN and the safety
rails: provenance manifest before anything launches, worker until readiness,
auxiliary services, the client under a watchdog, and — on every exit path —
process-group teardown plus the terminal ``status.json`` verdict.

Terminal states: ``success`` (exit 0 and zero issues), ``failed`` (anything
else), ``interrupted`` (operator SIGINT/SIGTERM; neither success nor a
pathology). A run directory is retained in every state.
"""

from __future__ import annotations

import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from environment.verify import collect_software
from lab.artifacts import SCHEMA_VERSION, RunStore, utc_now
from lab.probes import collect_git, collect_gpu, collect_host, collect_third_party_pins
from lab.process import ProcessGroup, tail_text


READY_POLL_S = 0.5


@dataclass(frozen=True)
class Launch:
    """One child process: manifest name, argv, receiving log artifact, cwd, env."""

    name: str
    command: tuple[str, ...]
    log: str
    cwd: Path
    env: dict[str, str] | None = None


def _no_issues(store: RunStore) -> list[str]:
    return []


@dataclass(frozen=True)
class RunPlan:
    """Everything experiment-specific about one run, declared up front."""

    experiment: str
    run_id: str
    root: Path
    worker_python: Path
    gpu: int
    output_root: Path
    config: dict[str, Any]
    worker: Launch
    ready_file: Path
    startup_timeout_s: int
    client: Launch
    client_timeout_s: int
    services: tuple[Launch, ...] = ()
    # The pinned client hardcodes its output location; when set, the file is
    # moved into the run directory as client.json after the client exits.
    client_result: Path | None = None
    required_artifacts: tuple[str, ...] = ()
    collect_issues: Callable[[RunStore], list[str]] = _no_issues
    manifest_extra: dict[str, Any] = field(default_factory=dict)

    def launches(self) -> tuple[Launch, ...]:
        return (self.worker, *self.services, self.client)


def build_manifest(plan: RunPlan, argv: Sequence[str]) -> dict[str, Any]:
    """Collect provenance before creating the run directory or launching a GPU process."""
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": plan.run_id,
        "experiment": plan.experiment,
        **plan.manifest_extra,
        "started_at": utc_now(),
        "command": list(argv),
        "process_commands": {launch.name: list(launch.command) for launch in plan.launches()},
        "git": collect_git(plan.root),
        "third_party": collect_third_party_pins(plan.root),
        "software": collect_software(plan.worker_python),
        "hardware": {"host": collect_host(), "gpu": collect_gpu(plan.gpu)},
        "config": plan.config,
    }


def wait_for_ready(
    process: subprocess.Popen[bytes], ready_file: Path, log: Path, timeout_s: int
) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if ready_file.is_file():
            return
        if process.poll() is not None:
            tail = tail_text(log, 12)
            raise RuntimeError(f"worker exited before readiness (code {process.returncode})\n{tail}")
        time.sleep(READY_POLL_S)
    raise TimeoutError(f"worker did not become ready within {timeout_s}s")


def _raise_interrupt(signum, frame):  # pragma: no cover - trivial trampoline
    raise KeyboardInterrupt


def execute(plan: RunPlan, argv: Sequence[str]) -> tuple[int, Path]:
    """Execute one run and always leave a terminal ``status.json`` behind."""
    manifest = build_manifest(plan, argv)
    store = RunStore.create(plan.output_root, plan.run_id, manifest)
    processes = ProcessGroup()
    workflow_issues: list[str] = []
    exit_code = 1
    interrupted = False
    try:  # SIGTERM joins SIGINT on the interrupted path (only the main thread may install)
        previous_sigterm = signal.signal(signal.SIGTERM, _raise_interrupt)
    except ValueError:
        previous_sigterm = None
    try:
        store.write_status(
            state="running", phase="worker-startup", started_at=manifest["started_at"]
        )
        worker = _start(processes, store, plan.worker)
        wait_for_ready(
            worker, plan.ready_file, store.file(plan.worker.log), plan.startup_timeout_s
        )
        for service in plan.services:
            _start(processes, store, service)
        store.write_status(state="running", phase="client", started_at=manifest["started_at"])
        client = _start(processes, store, plan.client)
        try:
            exit_code = client.wait(timeout=plan.client_timeout_s)
        except subprocess.TimeoutExpired:
            exit_code = 124
            workflow_issues.append(
                f"client exceeded its {plan.client_timeout_s}s watchdog and was terminated"
            )
        if plan.client_result is not None and plan.client_result.is_file():
            plan.client_result.replace(store.file("client.json"))
    except KeyboardInterrupt:
        interrupted = True
        exit_code = 130
    finally:
        if previous_sigterm is not None:
            signal.signal(signal.SIGTERM, previous_sigterm)
        processes.cleanup()
        plan.ready_file.unlink(missing_ok=True)
        status = store.finalize(
            required=plan.required_artifacts,
            exit_code=exit_code,
            extra_issues=(*workflow_issues, *plan.collect_issues(store)),
            interrupted=interrupted,
        )

    print(tail_text(store.file(plan.client.log), 12))
    print(f"run_id: {plan.run_id}")
    print(f"artifacts: {store.path}")
    print(f"status: {status['state']}")
    return (0 if status["state"] == "success" else exit_code or 1), store.path


def _start(processes: ProcessGroup, store: RunStore, launch: Launch) -> subprocess.Popen[bytes]:
    return processes.start(
        list(launch.command), store.file(launch.log), cwd=launch.cwd, env=launch.env
    )
