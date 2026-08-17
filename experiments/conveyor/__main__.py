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
    ap.add_argument("--seed-tokens", type=int, default=0, help="warm-start prefill tokens per session")
    ap.add_argument(
        "--park-tail-blocks", type=int,
        help="park primitive, fixed mode: destroy this many tail KV blocks per session per slice",
    )
    ap.add_argument(
        "--park-keep-blocks", type=int,
        help="park primitive, quota mode: destroy everything beyond this resident floor "
             "(overrides --park-tail-blocks)",
    )
    ap.add_argument(
        "--prefetch", choices=("off", "push"),
        help="KV prefetch: push = materialize the parked tail at chunk-push time so the "
             "reload copy overlaps FE (requires park; default: off)",
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
