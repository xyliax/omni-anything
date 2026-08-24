"""Entry point: ``python -m experiments.conveyor``.

Pure argv translation — this file reads no configuration; constructing and
consuming the config both happen in ``runner``.
"""

from __future__ import annotations

import argparse
import sys

from .runner import run


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="python -m experiments.conveyor",
        description="Run one fresh-worker conveyor point into a new immutable evidence directory.",
    )
    ap.add_argument("--trace", action="store_true", help="enable detailed tracing")
    ap.add_argument("--label", help="human label used in the run ID (default: conveyor-n<sessions>)")
    ap.add_argument("--sessions", type=int, help="concurrent sessions (default: workload constant)")
    ap.add_argument(
        "--duration", dest="duration_s", type=int,
        help="run duration in seconds (default: workload constant)",
    )
    ap.add_argument(
        "--initial-context-tokens",
        type=int,
        default=0,
        help="initial context length to preload per session",
    )
    ap.add_argument(
        "--evict-tail-blocks", type=int,
        help="fixed mode: evict this many tail KV blocks after a session becomes idle",
    )
    ap.add_argument(
        "--retained-prefix-blocks", type=int,
        help="retain this many GPU prefix blocks for an idle session "
             "(overrides --evict-tail-blocks)",
    )
    ap.add_argument(
        "--prefetch", choices=("off", "push"),
        help="KV prefetch: push = copy host-backed blocks into the GPU prefix cache at "
             "input release (requires KV eviction; default: off)",
    )
    ap.add_argument("--gpu", type=int, help="GPU index to run on (default: the usual card)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        code, _ = run(
            [sys.executable, "-m", "experiments.conveyor", *(argv or sys.argv[1:])],
            **vars(args),
        )
    except ValueError as exc:
        parser().error(str(exc))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
