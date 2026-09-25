#!/usr/bin/env python3
"""Verify the pinned ``cuda13_vllm023`` profile without starting a GPU workload.

Library and CLI in one module: ``collect_software`` produces the report (the
runners embed it in every run manifest), ``runtime_issues`` is the single
validity predicate over that report, and ``main`` prints the verdict.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_PACKAGES = {
    "vllm": "0.23.0",
    "torch": "2.11.0",
    "flashinfer-python": "0.6.12",
    "transformers": "4.57.6",
}


def capture(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def collect_software(python: Path) -> dict[str, Any]:
    """One subprocess in the worker venv: package versions, CUDA runtime,
    FIX 1 marker, and CUDA 13 wheel layout. GPU-heavy imports stay out of
    the calling process."""
    script = r'''
import importlib.metadata as md
import json, platform, site, sys
from pathlib import Path

versions = {}
for name in ("vllm", "torch", "flashinfer-python", "transformers", "grpcio", "numpy"):
    try:
        versions[name] = md.version(name)
    except md.PackageNotFoundError:
        versions[name] = None
try:
    import torch
    cuda_runtime = torch.version.cuda
except Exception as exc:
    cuda_runtime = None
    versions["torch_import_error"] = repr(exc)

try:
    base = Path(md.distribution("vllm").locate_file(""))
    paths = list(base.glob("vllm/**/mm_encoder_attention.py"))
    fix1 = {"candidates": [str(p) for p in paths],
            "marked": [str(p) for p in paths if "METRONOME FIX 1" in p.read_text(errors="replace")]}
except Exception as exc:
    fix1 = {"error": repr(exc), "candidates": [], "marked": []}

roots = [Path(p) / "nvidia" / "cu13" for p in site.getsitepackages()]
roots = [p for p in roots if p.is_dir()]
cuda_layout = {"roots": [str(p) for p in roots], "valid": False}
if roots:
    root = roots[0]
    cuda_layout.update(lib64_exists=(root / "lib64").exists(),
                       libcudart_link_exists=(root / "lib" / "libcudart.so").exists())
    cuda_layout["valid"] = cuda_layout["lib64_exists"] and cuda_layout["libcudart_link_exists"]

print(json.dumps({"python": platform.python_version(), "executable": sys.executable,
                  "packages": versions, "cuda_runtime": cuda_runtime,
                  "fix1": fix1, "cuda_layout": cuda_layout}))
'''
    try:
        return json.loads(capture([str(python), "-c", script]))
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return {"error": str(exc), "executable": str(python), "packages": {},
                "fix1": {"marked": []}, "cuda_layout": {"valid": False}}


def runtime_issues(software: dict[str, Any]) -> list[str]:
    """The single composite validity predicate for the locked runtime profile,
    over a ``collect_software`` report."""
    issues: list[str] = []
    if software.get("error"):
        issues.append(f"cannot inspect worker Python: {software['error']}")
    packages = software.get("packages", {})
    for package, expected in EXPECTED_PACKAGES.items():
        if packages.get(package) != expected:
            issues.append(f"expected {package} {expected}, found {packages.get(package)!r}")
    if not str(software.get("cuda_runtime") or "").startswith("13."):
        issues.append(f"expected a CUDA 13 runtime, found {software.get('cuda_runtime')!r}")
    if not software.get("fix1", {}).get("marked"):
        issues.append("vLLM METRONOME FIX 1 marker was not found")
    if not software.get("cuda_layout", {}).get("valid"):
        issues.append("CUDA 13 wheel compatibility links are missing; rerun infra/env/setup.sh")
    return issues


def driver_issues(version: str) -> list[str]:
    """CUDA 13.x requires the R580 driver family or newer."""
    try:
        if int(version.split('.')[0]) >= 580:
            return []
    except (ValueError, AttributeError):
        pass
    return [f'CUDA 13 runtime requires NVIDIA driver >= 580; found {version!r}']


def collect_device(python: Path, gpu: int) -> dict[str, Any]:
    """Small BF16 execution probe on exactly the requested physical device."""
    try:
        row = capture(['nvidia-smi', f'--id={gpu}',
                       '--query-gpu=name,uuid,driver_version,memory.total',
                       '--format=csv,noheader,nounits'])
        name, uuid, driver, memory = (part.strip() for part in row.split(',', 3))
        report = dict(index=gpu, name=name, uuid=uuid, driver=driver, memory_mib=int(memory))
        report['issues'] = driver_issues(driver)
        if report['issues']:
            return report
        script = '''
import json, torch
assert torch.cuda.is_bf16_supported(), 'BF16 is unavailable on this GPU'
a = torch.ones((32, 32), device='cuda', dtype=torch.bfloat16)
b = a @ a
torch.cuda.synchronize()
assert torch.equal(b.cpu(), torch.full((32, 32), 32, dtype=torch.bfloat16))
print(json.dumps(dict(capability=torch.cuda.get_device_capability(),
                     torch_arch_list=torch.cuda.get_arch_list(), bf16_execution=True)))
'''
        env = {**os.environ, 'CUDA_VISIBLE_DEVICES': uuid}
        result = subprocess.run([str(python), '-c', script], env=env,
                                capture_output=True, text=True, timeout=120, check=True)
        report.update(json.loads(result.stdout))
        return report
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, 'stderr', '') or str(exc)
        return {'index': gpu, 'issues': [f'GPU execution check failed: {detail}']}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--worker-python",
        type=Path,
        default=root / ".venv-vllm023" / "bin" / "python",
        help="Python executable used to start the vLLM worker",
    )
    parser.add_argument('--gpu', type=int, help='also verify driver and a small BF16 GPU operation')
    args = parser.parse_args()
    software = collect_software(args.worker_python.expanduser())
    issues = runtime_issues(software)
    result = {
        "valid": not issues,
        "issues": issues,
        "expected_packages": EXPECTED_PACKAGES,
        "software": software,
    }
    if args.gpu is not None:
        result['gpu'] = collect_device(args.worker_python.expanduser(), args.gpu)
        issues.extend(result['gpu']['issues'])
        result['valid'] = not issues
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
