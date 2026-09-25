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
    ap.add_argument('--model-preset', choices=('qwen25_omni', 'minicpm_o45'), help='pinned checkpoint and audio input adapter')
    ap.add_argument('--max-model-len', type=int)
    ap.add_argument('--max-num-seqs', type=int)
    ap.add_argument('--gpu-memory-utilization', type=float)
    ap.add_argument('--max-num-batched-tokens', type=int)
    ap.add_argument('--enforce-eager', action='store_true')
    ap.add_argument("--session-manager", action="store_true", help="independent KV residency and copy control")
    ap.add_argument('--admission-profile', help='JSON of explicit finite-horizon resource estimates')
    ap.add_argument('--cohort-manifest', help='JSON session arrivals, durations and per-session seeds')
    ap.add_argument('--open-loop', action='store_true', help='replay an exogenous schedule with fixed source clocks and one-shot rejection')
    ap.add_argument('--phase-policy', choices=('assigned', 'natural'))
    ap.add_argument('--restore-policy', choices=('pre_tick', 'on_demand', 'after_submit'))
    ap.add_argument('--verify-copies', action='store_true', help='intrusive diagnostic: compare physical KV bytes before publishing copies')
    ap.add_argument('--kv-pool-gib', type=float)
    ap.add_argument('--host-offload-gib', type=float)
    ap.add_argument('--prefetch-min-free', type=float)
    ap.add_argument('--slots', type=int, help='session groups per period; many sessions may share one slot')
    ap.add_argument('--resident-control', action='store_true', help='matched fully resident cohort control, without KV offload')
    ap.add_argument('--resident-limit', type=int, help='maximum active sessions in the resident control')
    ap.add_argument('--capacity-slo', help='explicit stability SLO JSON; enables the all-admitted measurement barrier')
    ap.add_argument('--copy-submission', choices=('native', 'optimized'), help='diagnostic control for the pre-fix CUDA submission path')
    ap.add_argument("--restore-lead-s", type=float, help="restore this long before the next planned tick")
    ap.add_argument("--gpu-trace", action="store_true", help="capture the whole business run; export only after the client exits")
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
