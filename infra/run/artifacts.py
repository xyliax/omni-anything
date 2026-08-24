"""The single immutable run-directory implementation for every experiment.

One run = one freshly created directory under ``results/<experiment>/``.
Existing directories are never opened, evidence files are written exactly
once, and a terminal ``status.json`` records validation. Failed runs are
always retained: failure evidence is evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


SCHEMA_VERSION = 2

# Deliberately narrow: a background-thread traceback in worker.log must NOT
# fail a run; only engine-fatal or evidence-contract-breaking signatures do
# (test-pinned).
FATAL_WORKER_PATTERN = re.compile(
    r"EngineCore failed to start|OutOfMemoryError|CUDA out of memory|"
    r"scheduler trace initialization failed|initialization barrier timed out",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sanitize_label(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not clean:
        raise ValueError("label must contain at least one letter or digit")
    return clean[:48]


def make_run_id(label: str) -> str:
    """``<YYYYMMDD>_<HHMMSS>_<label>``: sortable, short, human-readable.

    Everything else (mode, sessions, commit, ...) belongs in manifest.json,
    not in the directory name. Directory creation enforces uniqueness.
    """
    now = datetime.now(timezone.utc)
    return f"{now.strftime('%Y%m%d_%H%M%S')}_{sanitize_label(label)}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_worker_fatal(path: Path) -> list[str]:
    """Return validation issues from a worker log, using the narrow pattern."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if FATAL_WORKER_PATTERN.search(text):
        return ["worker log contains a fatal error"]
    return []


def scan_client_health(path: Path) -> list[str]:
    """Return the shared full-duplex client acceptance issues."""
    if not path.is_file():
        return []
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return ["client.json is not valid JSON"]
    if not isinstance(result, dict):
        return ["client.json is not a JSON object"]
    issues: list[str] = []
    try:
        errors = int(result.get("err", 0))
    except (TypeError, ValueError):
        return ["client.json has an invalid err field"]
    if errors:
        issues.append(f"client reported {errors} session error(s)")
    if result.get("starved") is True:
        issues.append("client received no ticks (starved=true)")
    elif result.get("realtime") is False:
        issues.append("client failed real-time acceptance (realtime=false)")
    return issues


@dataclass
class RunStore:
    """Own one newly-created run directory; existing directories are never opened."""

    path: Path

    @classmethod
    def create(cls, output_root: Path, run_id: str, manifest: dict[str, object]) -> "RunStore":
        output_root.mkdir(parents=True, exist_ok=True)
        path = output_root / run_id
        path.mkdir(mode=0o755)  # exist_ok=False is the no-overwrite guarantee.
        store = cls(path)
        store.write_json("manifest.json", manifest)
        store.write_status(state="running", phase="created", started_at=manifest.get("started_at"))
        return store

    def file(self, name: str) -> Path:
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

    def finalize(
        self,
        *,
        required: Sequence[str],
        exit_code: int,
        extra_issues: Sequence[str] = (),
        interrupted: bool = False,
    ) -> dict[str, object]:
        """Validate evidence and write the terminal status document.

        Exit code 0 can never rescue a run that has issues, and the directory
        is retained in every terminal state. ``interrupted`` (operator SIGINT/
        SIGTERM) is its own terminal state: neither success nor a pathology,
        and the layout guard accepts it.
        """
        missing = [name for name in required if not self.file(name).is_file()]
        empty = [
            name
            for name in required
            if self.file(name).is_file() and not self.file(name).stat().st_size
        ]
        issues = [f"missing artifact: {name}" for name in missing]
        issues += [f"empty artifact: {name}" for name in empty]
        issues += list(extra_issues)

        if interrupted:
            state = "interrupted"
        else:
            state = "success" if exit_code == 0 and not issues else "failed"
        artifacts = {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in sorted(self.path.iterdir())
            if path.is_file() and path.name != "status.json" and not path.name.startswith(".")
        }
        status = {
            "schema_version": SCHEMA_VERSION,
            "state": state,
            "phase": "complete",
            "updated_at": utc_now(),
            "finished_at": utc_now(),
            "exit_code": exit_code,
            "validation": {
                "valid": state == "success",
                "required": sorted(required),
                "missing": missing,
                "empty": empty,
                "issues": issues,
            },
            "artifacts": artifacts,
        }
        self.write_json("status.json", status)
        return status
