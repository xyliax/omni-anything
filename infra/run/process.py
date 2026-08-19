"""Process-group orchestration primitives shared by GPU experiments."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Sequence


def tail_text(path: Path, lines: int) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


@dataclass
class ProcessGroup:
    """Processes started in private sessions and terminated only by recorded PGID.

    ``start_new_session=True`` gives every child its own process group; killing
    by that recorded PGID is the only reliable way to stop vLLM's spawned
    EngineCore children. Logs are opened ``xb`` so an existing artifact is
    never appended to.
    """

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
