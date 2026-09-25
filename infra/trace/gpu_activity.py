"""Parse device activity timestamps; never infer GPU work from CPU spans."""
from __future__ import annotations

import bisect
import json
import math
import re
from collections import defaultdict
from pathlib import Path

GPU_CATEGORIES = {"kernel", "gpu_memcpy", "gpu_memset"}


def stream_labels(activities: list[dict]) -> dict[tuple, str]:
    """Name observed stream roles from attribution, never from CUDA IDs.

    A compute stream may also contain input copies and memset operations.
    Only explicitly attributed Session Manager copies establish a KV role.
    """
    roles = defaultdict(set)
    for row in activities:
        key = (row["device"], row["context"], row["stream"])
        args = row["args"]
        role = roles[key]
        if "transfer_id" in args and args.get("direction") in ("H2D", "D2H"):
            role.add(args["direction"])
        if row["category"] == "kernel":
            role.add("model" if args.get("requests") and "transfer_id" not in args else "compute")
        elif row["category"] == "gpu_memcpy":
            role.add("copy")
    grouped = defaultdict(list)
    for key, role in roles.items():
        parts = []
        if "model" in role:
            parts.append("Model compute")
        elif "compute" in role:
            parts.append("Compute")
        if "H2D" in role:
            parts.append("KV restore H2D")
        if "D2H" in role:
            parts.append("KV backup D2H")
        label = " + ".join(parts) or ("Copy (unattributed)" if "copy" in role else "Auxiliary")
        grouped[(key[0], label)].append(key)
    labels = {}
    for (device, label), keys in grouped.items():
        for index, key in enumerate(sorted(keys), 1):
            suffix = f" #{index}" if len(keys) > 1 else ""
            labels[key] = f"GPU {device} · {label}{suffix}"
    return labels


def parse_gpu_activity(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text())
    base = data.get("baseTimeNanoseconds")
    if not isinstance(base, (int, float)) or not math.isfinite(base):
        raise ValueError("GPU activity lacks baseTimeNanoseconds; cannot align to host epoch")
    events = data["traceEvents"]
    annotations = defaultdict(list)
    gpu_annotations = defaultdict(list)
    for event in events:
        name = event.get("name", "")
        if event.get("ph") != "X" or not name.startswith(("pilarius.copy ", "pilarius.compute ")):
            continue
        match = re.search(r"req=(.*)$", name)
        args = {"requests": match[1].split(",") if match and match[1] else []}
        if transfer := re.search(r"pilarius.copy id=(\d+) (H2D|D2H)", name):
            args.update(transfer_id=int(transfer[1]), direction=transfer[2])
        # Kineto also emits GPU annotations tied to record_function external
        # IDs. Batch-copy APIs may have no exported host API row even though
        # their device activity and this explicit association are present.
        target = gpu_annotations if event.get("cat") == "gpu_user_annotation" else annotations
        target[(event["pid"], event["tid"])].append(
            (event["ts"], event["ts"] + event["dur"], args))
    starts = {}
    for key, ranges in annotations.items():
        ranges.sort(key=lambda r: r[0])
        starts[key] = [r[0] for r in ranges]
    gpu_starts = {}
    for key, ranges in gpu_annotations.items():
        ranges.sort(key=lambda r: r[0])
        gpu_starts[key] = [r[0] for r in ranges]
    correlations = {}
    for event in events:
        if event.get("cat") not in ("cuda_runtime", "cuda_driver"):
            continue
        key = (event["pid"], event["tid"])
        i = bisect.bisect_right(starts.get(key, []), event["ts"]) - 1
        if i >= 0:
            start, end, attribution = annotations[key][i]
            if event["ts"] + event.get("dur", 0) <= end + 1:
                correlation = event.get("args", {}).get("correlation")
                if correlation is not None:
                    correlations[correlation] = attribution
    result = []
    for event in events:
        if event.get("cat") not in GPU_CATEGORIES or event.get("ph") != "X":
            continue
        args = event.get("args", {})
        start, duration = event["ts"], event["dur"]
        if not all(math.isfinite(v) for v in (start, duration)) or duration < 0:
            raise ValueError("invalid GPU activity timestamp/duration")
        attribution = correlations.get(args.get("correlation"), {})
        attribution_source = "CUDA correlation" if attribution else "unattributed"
        if not attribution:
            key = (event.get("pid", args.get("device", 0)),
                   event.get("tid", args.get("stream", 0)))
            i = bisect.bisect_right(gpu_starts.get(key, []), start + .01) - 1
            if i >= 0:
                begin, end, candidate = gpu_annotations[key][i]
                if begin - .01 <= start and start + duration <= end + .01:
                    attribution = candidate
                    attribution_source = "Kineto GPU annotation"
        result.append({
            "time": base / 1e9 + start / 1e6, "duration": duration / 1e6,
            "name": event["name"], "category": event["cat"],
            "device": args.get("device", 0), "context": args.get("context", 0),
            "stream": args.get("stream", event.get("tid", 0)),
            "args": {**args, **attribution, "timing_scope": "CUPTI GPU activity",
                     "attribution": attribution_source},
        })
    return result


def parse_transfer_events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for row in rows:
        if row.get("schema_version") != 1 or not isinstance(row.get("event"), str):
            raise ValueError("invalid transfer event schema")
    return rows


def gpu_activity_issues(path: Path, transfer_path: Path | None = None) -> list[str]:
    if not path.is_file():
        return ["missing GPU activity capture"]
    try:
        activities = parse_gpu_activity(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"invalid GPU activity capture: {exc}"]
    if not any(row["category"] == "kernel" for row in activities):
        return ["GPU activity capture contains no CUDA kernels"]
    issues = []
    if transfer_path is not None:
        try:
            submissions = {r["transfer_id"]: r for r in parse_transfer_events(transfer_path)
                           if r["event"] == "submitted"}
            byte_counts = defaultdict(int)
            h2d = False
            for row in activities:
                args = row["args"]
                if row["category"] == "gpu_memcpy" and "transfer_id" in args:
                    byte_counts[args["transfer_id"]] += int(args["bytes"])
                    h2d |= args.get("direction") == "H2D"
            if not h2d:
                issues.append("GPU capture contains no attributed Session Manager H2D activity")
            for transfer, count in byte_counts.items():
                if transfer not in submissions or count != submissions[transfer]["bytes"]:
                    issues.append(f"GPU copy bytes disagree with submission for transfer {transfer}")
        except (OSError, ValueError, KeyError, TypeError):
            issues.append("cannot validate GPU copy attribution against transfer events")
    return issues
