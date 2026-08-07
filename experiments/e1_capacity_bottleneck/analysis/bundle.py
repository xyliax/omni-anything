"""Compatibility imports for the repository-wide observability data layer.

New code should import :mod:`observability.bundle` directly. This module keeps
older E1 plotting commands working while parsing remains single-sourced.
"""

from observability.bundle import (  # noqa: F401
    RunFiles,
    align_perf_family,
    build_bundle,
    last_token_growth,
    parse_gpu,
    parse_kv,
    parse_per_request,
    parse_scheduler,
    parse_scheduler_absolute,
    percentile,
    read_json,
    resolve_run,
)

__all__ = [
    "RunFiles",
    "align_perf_family",
    "build_bundle",
    "last_token_growth",
    "parse_gpu",
    "parse_kv",
    "parse_per_request",
    "parse_scheduler",
    "parse_scheduler_absolute",
    "percentile",
    "read_json",
    "resolve_run",
]
