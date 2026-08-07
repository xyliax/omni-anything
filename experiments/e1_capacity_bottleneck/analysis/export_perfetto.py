"""Compatibility entry point for the shared Perfetto exporter.

Use ``python3 -m observability.export_perfetto`` in new automation.
"""

from observability.export_perfetto import (  # noqa: F401
    MissingTimelineDataError,
    export,
    main,
)

# Migration alias for callers that handled the former E1-only exception.
MissingSchedulerTraceError = MissingTimelineDataError

__all__ = [
    "MissingSchedulerTraceError",
    "MissingTimelineDataError",
    "export",
    "main",
]


if __name__ == "__main__":
    main()
