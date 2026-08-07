#!/usr/bin/env python3
"""Verify the pinned ``cuda13_vllm023`` profile without starting a GPU workload."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from environment.verification import (
    EXPECTED_PACKAGES,
    collect_cuda_layout,
    collect_python_environment,
    find_fix1_marker,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worker-python",
        type=Path,
        default=ROOT / ".venv-vllm023" / "bin" / "python",
        help="Python executable used to start the vLLM worker",
    )
    args = parser.parse_args()
    python = args.worker_python.expanduser()
    software = collect_python_environment(python)
    fix1 = find_fix1_marker(python)
    cuda_layout = collect_cuda_layout(python)
    packages = software.get("packages", {})
    package_versions_valid = all(packages.get(name) == version for name, version in EXPECTED_PACKAGES.items())
    result = {
        "valid": (
            package_versions_valid
            and str(software.get("cuda_runtime") or "").startswith("13.")
            and bool(fix1.get("marked"))
            and cuda_layout.get("valid", False)
        ),
        "expected_packages": EXPECTED_PACKAGES,
        "software": software,
        "fix1": fix1,
        "cuda_layout": cuda_layout,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
