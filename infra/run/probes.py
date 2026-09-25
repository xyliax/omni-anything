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


def collect_source_patch(root: Path) -> bytes:
    """Reconstruct first-party diagnostics, including newly added source files.

    Raw results are never embedded recursively. Untracked files outside the
    source/documentation directories are not treated as executable inputs.
    """
    patch = subprocess.check_output(
        ["git", "diff", "--binary", "HEAD", "--", ".", ":!results/**"], cwd=root)
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "-z", "--",
         "engines", "experiments", "infra", "tests", "docs"], cwd=root)
    for raw in untracked.split(b"\0"):
        if not raw:
            continue
        result = subprocess.run(
            ["git", "diff", "--no-index", "--binary", "--", "/dev/null", os.fsdecode(raw)],
            cwd=root, capture_output=True)
        if result.returncode not in (0, 1):
            raise RuntimeError(f"cannot capture untracked source patch: {os.fsdecode(raw)}")
        patch += result.stdout
    return patch


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


def model_cache_root() -> Path:
    """Match huggingface_hub's cache environment precedence without importing it."""
    default_home = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'huggingface'
    hf_home = Path(os.environ.get('HF_HOME', default_home))
    legacy_cache = os.environ.get('HUGGINGFACE_HUB_CACHE', str(hf_home / 'hub'))
    return Path(os.environ.get('HF_HUB_CACHE', legacy_cache)).expanduser()


def resolve_model_snapshot(model: str, revision: str) -> Path:
    """The HF-cache snapshot for a pinned revision — the revision lock's enforcement point.

    Raises instead of returning ``None``: this feeds the worker's ``--model``
    argv directly, and a silent miss once launched a worker with the literal
    string "None" as its model path.
    """
    cache_name = "models--" + model.replace("/", "--")
    cache = model_cache_root()
    snapshot = cache / cache_name / "snapshots" / revision
    if not revision or not snapshot.is_dir():
        raise RuntimeError(
            f"pinned model snapshot not in the HF cache: {model}@{revision or '<unset>'} "
            f"(expected {snapshot}); run `bash infra/env/setup.sh --download-models` first"
        )
    return snapshot


def model_snapshot_issues(snapshot: Path) -> list[str]:
    """Reject incomplete downloads before a costly worker launch."""
    import json
    required = {'config.json', 'tokenizer_config.json', 'preprocessor_config.json'}
    if not any((snapshot / name).is_file() for name in ('tokenizer.json', 'tokenizer.model')):
        required.add('tokenizer.json')
    index = snapshot / 'model.safetensors.index.json'
    if index.is_file():
        try:
            weights = json.loads(index.read_text())['weight_map']
            if not weights:
                raise ValueError('empty weight map')
            required.update(weights.values())
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return [f'invalid safetensors index: {index}: {exc}']
    else:
        required.add('model.safetensors')
    return [f'missing or empty model file: {snapshot / name}' for name in sorted(required)
            if not (snapshot / name).is_file() or (snapshot / name).stat().st_size == 0]
