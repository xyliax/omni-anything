"""Immutable run directories and machine-readable run status.

The store is intentionally small and independent from GPU libraries.  It can
be tested in ordinary CI and reused by future E-series runners.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .config import RunConfig


SCHEMA_VERSION = 1
FATAL_WORKER_PATTERN = re.compile(
    r"EngineCore failed to start|OutOfMemoryError|CUDA out of memory|"
    r"scheduler trace initialization failed",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_run_id(config: RunConfig, commit: str, now: datetime | None = None) -> str:
    """Build a sortable and descriptive ID; directory creation enforces uniqueness."""
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    label = f"_{sanitize_label(config.label)}" if config.label else ""
    trace = "_trace" if config.trace else ""
    return (
        f"{stamp}_e1_{config.mode}{trace}_n{config.sessions}_p{config.period_ms}"
        f"_mml{config.max_model_len}_seed{config.seed_tokens}_{commit[:7]}{label}"
    )


def sanitize_label(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not clean:
        raise ValueError("label must contain at least one letter or digit")
    return clean[:48]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def required_artifacts(config: RunConfig) -> tuple[str, ...]:
    names = ["client.json", "client.txt", "gateway.log", "gpu.csv", "kv.log", "worker.log"]
    if config.trace:
        names.append("scheduler.log")
        if config.mode == "paringest":
            names.extend(("per_request.log", "per_iteration.log"))
    return tuple(sorted(names))


@dataclass
class ArtifactStore:
    """Own one newly-created run directory; existing directories are never opened."""

    path: Path

    @classmethod
    def create(cls, output_root: Path, run_id: str, manifest: dict[str, object]) -> "ArtifactStore":
        output_root.mkdir(parents=True, exist_ok=True)
        path = output_root / run_id
        path.mkdir(mode=0o755)  # exist_ok=False is the no-overwrite guarantee.
        store = cls(path)
        store.write_json("manifest.json", manifest)
        store.write_status(state="running", phase="created", started_at=manifest["started_at"])
        return store

    def file(self, name: str) -> Path:
        if Path(name).name != name:
            raise ValueError(f"artifact name must be a basename: {name}")
        return self.path / name

    def write_json(self, name: str, value: object) -> None:
        """Atomically replace runner-owned metadata, never raw evidence files."""
        target = self.file(name)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, target)

    def write_status(self, *, state: str, phase: str, **fields: object) -> None:
        status = {
            "schema_version": SCHEMA_VERSION,
            "state": state,
            "phase": phase,
            "updated_at": utc_now(),
            **fields,
        }
        self.write_json("status.json", status)

    def inventory(self, names: Iterable[str]) -> dict[str, dict[str, object]]:
        result: dict[str, dict[str, object]] = {}
        for name in names:
            path = self.file(name)
            if path.is_file():
                result[name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        return result

    def finalize(
        self,
        config: RunConfig,
        *,
        exit_code: int,
        requested_state: str | None = None,
        error: str | None = None,
    ) -> dict[str, object]:
        """Validate evidence and write the terminal status document."""
        required = required_artifacts(config)
        missing = [name for name in required if not self.file(name).is_file()]
        empty = [name for name in required if self.file(name).is_file() and not self.file(name).stat().st_size]
        scheduler_errors = self.file("scheduler_errors.log")
        issues = [f"missing artifact: {name}" for name in missing]
        issues += [f"empty artifact: {name}" for name in empty]
        if scheduler_errors.is_file() and scheduler_errors.stat().st_size:
            issues.append("scheduler trace reported serialization errors")
        worker_log = self.file("worker.log")
        if worker_log.is_file():
            worker_text = worker_log.read_text(encoding="utf-8", errors="replace")
            if FATAL_WORKER_PATTERN.search(worker_text):
                issues.append("worker log contains a fatal error")
        client_json = self.file("client.json")
        if client_json.is_file():
            try:
                with client_json.open(encoding="utf-8") as handle:
                    client_errors = int(json.load(handle).get("err", 0))
                if client_errors:
                    issues.append(f"client reported {client_errors} session error(s)")
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                issues.append("client.json is not a valid result document")
        if error:
            issues.append(error)

        state = requested_state or ("success" if exit_code == 0 and not issues else "failed")
        if state == "success" and (exit_code or issues):
            state = "failed"
        artifact_names = sorted(
            path.name for path in self.path.iterdir()
            if path.is_file() and path.name != "status.json" and not path.name.startswith(".")
        )
        status = {
            "schema_version": SCHEMA_VERSION,
            "state": state,
            "phase": "complete",
            "updated_at": utc_now(),
            "finished_at": utc_now(),
            "exit_code": exit_code,
            "validation": {
                "valid": state == "success",
                "required": list(required),
                "missing": missing,
                "empty": empty,
                "issues": issues,
            },
            "artifacts": self.inventory(artifact_names),
        }
        self.write_json("status.json", status)
        return status
