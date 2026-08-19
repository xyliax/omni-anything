"""Host, git, and GPU probes: provenance snapshots for the run manifest."""

from __future__ import annotations

import configparser
import os
import platform
import socket
import subprocess
from pathlib import Path
from typing import Any

from infra.env.verify import capture


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


def collect_host() -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": platform.processor(),
    }


def collect_gpu(gpu: int) -> dict[str, Any]:
    """Metadata snapshot for the manifest; errors are recorded, not raised."""
    query = "name,uuid,driver_version,memory.total,pci.bus_id"
    try:
        row = capture(
            [
                "nvidia-smi",
                f"--id={gpu}",
                f"--query-gpu={query}",
                "--format=csv,noheader,nounits",
            ]
        )
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


def resolve_model_snapshot(model: str, revision: str) -> Path:
    """The HF-cache snapshot for a pinned revision — the revision lock's enforcement point.

    Raises instead of returning ``None``: this feeds the worker's ``--model``
    argv directly, and a silent miss once launched a worker with the literal
    string "None" as its model path.
    """
    cache_name = "models--" + model.replace("/", "--")
    cache = Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface")) / "hub"
    snapshot = cache / cache_name / "snapshots" / revision
    if not revision or not snapshot.is_dir():
        raise RuntimeError(
            f"pinned model snapshot not in the HF cache: {model}@{revision or '<unset>'} "
            f"(expected {snapshot}); run `bash infra/env/setup.sh --download-models` first"
        )
    return snapshot
