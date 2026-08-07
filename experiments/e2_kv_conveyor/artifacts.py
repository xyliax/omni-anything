"""Small immutable artifact store for paired E2/E3 mechanism experiments."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_state(root: Path) -> dict[str, Any]:
    def capture(*args: str) -> str:
        return subprocess.check_output(args, cwd=root, text=True).strip()

    status = capture("git", "status", "--porcelain", "--untracked-files=all")
    return {
        "commit": capture("git", "rev-parse", "HEAD"),
        "branch": capture("git", "branch", "--show-current"),
        "dirty": bool(status),
        "status": status.splitlines(),
    }


class RunDirectory:
    def __init__(self, output_root: Path, label: str):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        clean_label = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-.")
        if not clean_label:
            raise ValueError("run label must contain a letter or digit")
        self.path = output_root / f"{stamp}_{clean_label[:80]}"
        self.path.mkdir(parents=True, exist_ok=False)

    def _replace_json(self, name: str, value: Any) -> Path:
        path = self.path / name
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
        return path

    def write_json(self, name: str, value: Any) -> Path:
        path = self.path / name
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return path

    def write_jsonl(self, name: str, rows: list[dict]) -> Path:
        path = self.path / name
        with path.open("x", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        return path

    def start(self, started_at: str) -> None:
        self._replace_json(
            "status.json",
            {
                "state": "running",
                "phase": "created",
                "started_at": started_at,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def finish(self, state: str, error: str | None = None) -> None:
        artifacts = {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(self.path.iterdir())
            if path.is_file() and path.name != "status.json"
        }
        self._replace_json(
            "status.json",
            {
                "state": state,
                "error": error,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "artifacts": artifacts,
            },
        )
