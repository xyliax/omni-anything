"""Host metadata collection and fail-fast preflight checks for E1 runs."""

from __future__ import annotations

import configparser
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

from environment.verification import (
    EXPECTED_PACKAGES,
    capture,
    collect_cuda_layout,
    collect_python_environment,
    find_fix1_marker,
)

from .config import RunConfig


class PreflightError(RuntimeError):
    """Raised before GPU processes start when a run cannot be trusted."""


def collect_git(root: Path) -> dict[str, Any]:
    status = capture(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root)
    return {
        "commit": capture(["git", "rev-parse", "HEAD"], cwd=root),
        "branch": capture(["git", "branch", "--show-current"], cwd=root),
        "dirty": bool(status),
        "status": status.splitlines(),
    }


def collect_third_party_pins(root: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for repo_file in sorted((root / "third_party").glob("*/.gitrepo")):
        parser = configparser.ConfigParser()
        parser.read(repo_file)
        pins[repo_file.parent.name] = parser.get("subrepo", "commit")
    return pins


def collect_gpu(gpu: int) -> dict[str, Any]:
    query = "name,uuid,driver_version,memory.total,pci.bus_id"
    try:
        row = capture([
            "nvidia-smi",
            f"--id={gpu}",
            f"--query-gpu={query}",
            "--format=csv,noheader,nounits",
        ])
        name, uuid, driver, memory, bus = (part.strip() for part in row.split(",", 4))
        return {
            "index": gpu,
            "name": name,
            "uuid": uuid,
            "driver": driver,
            "memory_mib": int(memory),
            "pci_bus_id": bus,
        }
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        return {"index": gpu, "error": str(exc)}


def collect_host() -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": platform.processor(),
    }


def resolve_model_revision(config: RunConfig) -> str | None:
    if config.model_revision:
        return config.model_revision
    cache_name = "models--" + config.model.replace("/", "--")
    reference = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
    reference = reference / "hub" / cache_name / "refs" / "main"
    try:
        return reference.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def resolve_model_path(config: RunConfig) -> Path | None:
    direct = Path(config.model).expanduser()
    if direct.exists():
        return direct.resolve()
    if not config.model_revision:
        return None
    cache_name = "models--" + config.model.replace("/", "--")
    cache = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    snapshot = cache / cache_name / "snapshots" / config.model_revision
    return snapshot if snapshot.is_dir() else None


def ensure_port_available(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise PreflightError(f"TCP port {port} is unavailable: {exc}") from exc


def run_preflight(
    config: RunConfig,
    git: dict[str, Any],
    software: dict[str, Any],
    fix1: dict[str, Any],
    cuda_layout: dict[str, Any],
) -> None:
    """Enforce prerequisites that used to be left to operator memory."""
    errors: list[str] = []
    required_paths = {
        "worker": config.worker_path,
        "gateway": config.gateway_path,
        "worker Python": config.worker_python,
        "client": config.metronome_root / "experiments" / "sustained_fd.py",
    }
    for label, path in required_paths.items():
        if not path.exists():
            errors.append(f"{label} does not exist: {path}")
    if shutil.which(str(config.client_python)) is None:
        errors.append(f"client Python is not on PATH: {config.client_python}")
    if shutil.which("nvidia-smi") is None:
        errors.append("nvidia-smi is not on PATH")
    if git["dirty"] and not config.allow_dirty:
        errors.append("Git worktree is dirty (commit or pass --allow-dirty to record that state)")

    if not config.skip_environment_check:
        packages = software.get("packages", {})
        if software.get("error"):
            errors.append(f"cannot inspect worker Python: {software['error']}")
        for package, expected in EXPECTED_PACKAGES.items():
            if packages.get(package) != expected:
                errors.append(f"expected {package} {expected}, found {packages.get(package)!r}")
        if not str(software.get("cuda_runtime") or "").startswith("13."):
            errors.append(f"expected a CUDA 13 runtime, found {software.get('cuda_runtime')!r}")
        if not fix1.get("marked"):
            errors.append("vLLM METRONOME FIX 1 marker was not found")
        if not cuda_layout.get("valid"):
            errors.append("CUDA 13 wheel compatibility links are missing; rerun environment/setup.sh")
    if config.model_revision and resolve_model_path(config) is None:
        errors.append(
            f"model snapshot {config.model}@{config.model_revision} is not cached; "
            "run environment/setup.sh --download-models"
        )

    for port in (config.worker_port, config.gateway_port):
        try:
            ensure_port_available(port)
        except PreflightError as exc:
            errors.append(str(exc))
    if errors:
        raise PreflightError("preflight failed:\n- " + "\n- ".join(errors))

    if not config.skip_gpu_quiet:
        subprocess.run(
            [
                "bash",
                str(config.root / "experiments" / "e1_capacity_bottleneck" / "wait_for_gpu.sh"),
                str(config.gpu),
                str(config.quiet_seconds),
            ],
            cwd=config.root,
            check=True,
        )
