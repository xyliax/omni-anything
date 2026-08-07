"""Run the paired E2 or E3 mechanism matrix and record provenance."""

from __future__ import annotations

import json
import os
import platform
import shutil
import statistics
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .artifacts import RunDirectory, git_state, sha256
from .core import (
    SimulationConfig,
    capacity_extension,
    load_compute_profile,
    simulate,
)
from .cuda_link import measure_h2d


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_E1_RUN = (
    "20260806T210551.398631Z_e1_paringest_trace_n8_p2000_"
    "mml32768_seed0_3139eab_formal-rerun"
)
BYTES_PER_TOKEN = 2 * 28 * 4 * 128 * 2


def source_trace(run_id: str) -> Path:
    return ROOT / "results" / "e1_capacity_bottleneck" / "runs" / run_id / "scheduler.log"


def software_manifest(worker_python: Path) -> dict:
    script = """
import json, torch, transformers, vllm
print(json.dumps({
  'python': __import__('sys').version.split()[0],
  'torch': torch.__version__,
  'cuda_runtime': torch.version.cuda,
  'transformers': transformers.__version__,
  'vllm': vllm.__version__,
}))
"""
    output = subprocess.check_output([str(worker_python), "-c", script], text=True)
    return json.loads(output)


def inspect_gpu(gpu: int) -> dict:
    """Reject a shared GPU carrying work from another process."""
    fields = "index,uuid,name,memory.used,memory.total,driver_version"
    row = subprocess.check_output(
        [
            "nvidia-smi",
            f"--id={gpu}",
            f"--query-gpu={fields}",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).strip().split(", ")
    if len(row) != 6:
        raise RuntimeError(f"unexpected nvidia-smi GPU row: {row}")
    process_output = subprocess.check_output(
        [
            "nvidia-smi",
            f"--id={gpu}",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).strip()
    processes = []
    for line in process_output.splitlines():
        if not line.strip():
            continue
        pid, name, used = line.split(", ", 2)
        processes.append({"pid": int(pid), "name": name, "memory_mib": int(used)})
    external = [process for process in processes if process["pid"] != os.getpid()]
    memory_mib = int(row[3])
    if external:
        raise RuntimeError(f"GPU {gpu} has external compute processes: {external}")
    if not processes and memory_mib > 1024:
        raise RuntimeError(f"GPU {gpu} is not quiet: {memory_mib} MiB in use")
    return {
        "index": int(row[0]),
        "uuid": row[1],
        "name": row[2],
        "memory_used_mib": memory_mib,
        "memory_total_mib": int(row[4]),
        "driver": row[5],
        "compute_processes": processes,
    }


def _distribution(rows: list[dict], key: str) -> dict | None:
    values = sorted(float(row[key]) for row in rows if row.get(key) is not None)
    if not values:
        return None
    def pick(fraction: float) -> float:
        return values[round((len(values) - 1) * fraction)]
    return {
        "count": len(values),
        "median": statistics.median(values),
        "p25": pick(0.25),
        "p75": pick(0.75),
    }


def aggregate_policy(summaries: list[dict], prefix: str) -> dict | None:
    rows = [row for row in summaries if row["arm"].startswith(prefix)]
    if not rows:
        return None
    keys = (
        "transfer_deadline_miss_rate",
        "transfer_queue_p99_ms",
        "output_deadline_miss_rate",
        "staging_peak_sessions",
        "capacity_wall_ms",
    )
    return {"arms": len(rows), **{key: _distribution(rows, key) for key in keys}}


def run_matrix(
    *,
    experiment: str,
    label: str,
    config: SimulationConfig,
    arms: Iterable[tuple[str, bool, str, int]],
    gpu: int,
    h2d_samples: int,
    e1_run: str,
    worker_python: Path,
    output_root: Path | None = None,
    keep_failed: bool = False,
    record_transfers: bool = True,
) -> Path:
    arms = list(arms)
    trace = source_trace(e1_run)
    if not trace.is_file() or trace.stat().st_size == 0:
        raise FileNotFoundError(f"non-empty E1 scheduler trace required: {trace}")
    compute = load_compute_profile(trace)
    if not worker_python.is_file():
        raise FileNotFoundError(f"worker Python does not exist: {worker_python}")
    gpu_before = inspect_gpu(gpu)
    output_root = output_root or ROOT / "results" / experiment / "runs"
    started_at = datetime.now(timezone.utc).isoformat()
    run = RunDirectory(output_root, label)
    manifest = {
        "schema_version": 1,
        "experiment": experiment,
        "run_id": run.path.name,
        "started_at": started_at,
        "evidence_level": "trace-driven CUDA mechanism prototype",
        "claim_boundary": (
            "Uses real E1 vLLM compute timings and fresh pinned H2D timings; "
            "does not claim end-to-end active-block migration inside vLLM."
        ),
        "git": git_state(ROOT),
        "host": {"hostname": platform.node(), "platform": platform.platform()},
        "software": software_manifest(worker_python),
        "hardware": {"gpu_before": gpu_before},
        "model": {
            "id": "Qwen/Qwen2.5-Omni-7B",
            "revision": "ae9e1690543ffd5c0221dc27f79834d0294cba00",
            "thinker_layers": 28,
            "kv_heads": 4,
            "head_dim": 128,
            "kv_dtype_bytes": 2,
            "kv_bytes_per_token": BYTES_PER_TOKEN,
        },
        "compute_profile": compute.as_manifest(),
        "compute_trace_sha256": sha256(trace),
        "config": asdict(config),
        "arms": [
            {"name": name, "conveyor": conveyor, "phase_policy": policy, "seed": seed}
            for name, conveyor, policy, seed in arms
        ],
        "h2d_samples": h2d_samples,
        "record_transfers": record_transfers,
        "simulation_policy": {
            "link": "single serial H2D queue, median-estimated just-in-time EDF groups",
            "content_release": "tick zero host-ready; later ticks after previous compute completion",
            "compute": "single GPU; batch all jobs ready when the next burst starts",
            "writeback": "new-token D2H is accounted as a limitation, not simulated",
        },
    }
    run.write_json("manifest.json", manifest)
    run.start(started_at)

    try:
        link = measure_h2d(
            gpu=gpu,
            size_bytes=config.tail_tokens * BYTES_PER_TOKEN,
            samples=h2d_samples,
        )
        run.write_json("link_calibration.json", link)
        summaries: list[dict] = []
        transfers: list[dict] = []
        for name, conveyor, policy, seed in arms:
            summary, rows = simulate(
                config,
                compute,
                link["samples_ms"],
                conveyor=conveyor,
                phase_policy=policy,
                seed=seed,
            )
            summary["arm"] = name
            summaries.append(summary)
            transfers.extend({"arm": name, **asdict(row)} for row in rows)

        by_name = {summary["arm"]: summary for summary in summaries}
        if "resident_sync" in by_name and "conveyor_tdma" in by_name:
            extension = capacity_extension(
                by_name["resident_sync"], by_name["conveyor_tdma"]
            )
        else:
            extension = None
        final = {
            "experiment": experiment,
            "run_id": run.path.name,
            "link_median_gbps": link["median_gbps"],
            "capacity_extension_tdma_vs_resident": extension,
            "policy_aggregates": {
                "random": aggregate_policy(summaries, "conveyor_random"),
                "tdma": aggregate_policy(summaries, "conveyor_tdma"),
            },
            "arms": summaries,
        }
        if record_transfers:
            run.write_jsonl("transfers.jsonl", transfers)
        run.write_json("summary.json", final)
        run.finish("success")
    except BaseException as exc:
        run.finish("failed", f"{type(exc).__name__}: {exc}")
        if not keep_failed:
            shutil.rmtree(run.path)
        raise
    return run.path
