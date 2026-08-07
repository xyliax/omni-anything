"""Verification primitives for the locked ``cuda13_vllm023`` runtime profile."""

from __future__ import annotations

import json
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


def collect_python_environment(python: Path) -> dict[str, Any]:
    """Inspect the selected Python without importing GPU-heavy packages here."""
    script = r'''
import importlib.metadata as md
import json, platform, sys
names = ("vllm", "torch", "flashinfer-python", "transformers", "grpcio", "numpy")
versions = {}
for name in names:
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
print(json.dumps({"python": platform.python_version(), "executable": sys.executable,
                  "packages": versions, "cuda_runtime": cuda_runtime}))
'''
    try:
        return json.loads(capture([str(python), "-c", script]))
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return {"error": str(exc), "executable": str(python), "packages": {}}


def find_fix1_marker(python: Path) -> dict[str, Any]:
    """Locate the version-specific vLLM FIX 1 marker recorded by the profile."""
    script = r'''
import importlib.metadata as md
import json
from pathlib import Path
try:
    base = Path(md.distribution("vllm").locate_file(""))
    paths = list(base.glob("vllm/**/mm_encoder_attention.py"))
    marked = [str(p) for p in paths if "METRONOME FIX 1" in p.read_text(errors="replace")]
    print(json.dumps({"candidates": [str(p) for p in paths], "marked": marked}))
except Exception as exc:
    print(json.dumps({"error": str(exc), "candidates": [], "marked": []}))
'''
    try:
        return json.loads(capture([str(python), "-c", script]))
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return {"error": str(exc), "candidates": [], "marked": []}


def collect_cuda_layout(python: Path) -> dict[str, Any]:
    """Check compatibility links required by the CUDA 13 wheel layout."""
    script = r'''
import json, site
from pathlib import Path
candidates = [Path(p) / "nvidia" / "cu13" for p in site.getsitepackages()]
roots = [p for p in candidates if p.is_dir()]
result = {"roots": [str(p) for p in roots], "valid": False}
if roots:
    root = roots[0]
    result.update({
        "lib64": str(root / "lib64"),
        "lib64_exists": (root / "lib64").exists(),
        "libcudart_link_exists": (root / "lib" / "libcudart.so").exists(),
    })
    result["valid"] = result["lib64_exists"] and result["libcudart_link_exists"]
print(json.dumps(result))
'''
    try:
        return json.loads(capture([str(python), "-c", script]))
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return {"error": str(exc), "roots": [], "valid": False}
