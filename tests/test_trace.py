"""Trace parsing and Perfetto export on synthetic runs; tests never read retained GPU evidence."""

from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

from infra.trace.bundle import build_bundle
from infra.trace.parse import parse_gpu, parse_kv, parse_kv_events, parse_residency
from infra.trace.perfetto import MissingTimelineDataError, export
from infra.trace.gpu_activity import parse_gpu_activity, gpu_activity_issues, stream_labels
from infra.trace.profile import build_profile, export as export_profile


SCHEDULER_LINES = (
    "100.000 s1ea:53E s2eb:53E\n"
    "100.020 s1ea:1 s2eb:1\n"
    "100.040 s1ea:1 s2eb:1\n"
    "102.000 s1ea:53E s2eb:53E\n"
    "102.020 s1ea:1 s2eb:1\n"
    "102.040 s1ea:1 s2eb:1\n"
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_run_dir(results_root: Path, experiment: str, run_id: str) -> Path:
    run = results_root / experiment / run_id
    run.mkdir(parents=True)
    return run


def make_scheduler_run(results_root: Path, run_id: str = "20260807_000002_engine") -> Path:
    """A minimal baseline-shaped run with a real scheduler trace fixture."""
    run = make_run_dir(results_root, "baseline", run_id)
    write_json(
        run / "manifest.json",
        {
            "schema_version": 2,
            "run_id": run_id,
            "config": {"workload": {"period_ms": 2000}, "platform": {"gpu_sample_period_s": 5}},
        },
    )
    write_json(run / "status.json", {"schema_version": 2, "state": "success", "phase": "complete"})
    (run / "scheduler.log").write_text(SCHEDULER_LINES, encoding="utf-8")
    return run


def read_trace(run: Path) -> dict:
    with gzip.open(run / "derived" / "timeline.trace.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)


class TraceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)

    def write(self, name: str, text: str) -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path


class ParserTests(TraceTestCase):
    def test_stream_roles_use_attribution_not_numeric_ids_or_copy_direction_alone(self) -> None:
        rows = [
            {"device": 0, "context": 1, "stream": 811, "category": "kernel",
             "args": {"requests": ["s1e1"]}},
            {"device": 0, "context": 1, "stream": 7, "category": "gpu_memcpy",
             "args": {"direction": "H2D", "transfer_id": 1}},
            {"device": 0, "context": 1, "stream": 29, "category": "gpu_memcpy",
             "args": {"direction": "D2H", "transfer_id": 2}},
            {"device": 0, "context": 1, "stream": 33, "category": "gpu_memcpy",
             "args": {"direction": "H2D"}},
        ]
        labels = stream_labels(rows)
        self.assertEqual(labels[(0, 1, 811)], "GPU 0 · Model compute")
        self.assertEqual(labels[(0, 1, 7)], "GPU 0 · KV restore H2D")
        self.assertEqual(labels[(0, 1, 29)], "GPU 0 · KV backup D2H")
        self.assertEqual(labels[(0, 1, 33)], "GPU 0 · Copy (unattributed)")
        # Separate contexts with the same role must remain distinguishable.
        rows.append({**rows[1], "context": 2})
        labels = stream_labels(list(reversed(rows)))
        self.assertEqual(labels[(0, 1, 7)], "GPU 0 · KV restore H2D #1")
        self.assertEqual(labels[(0, 2, 7)], "GPU 0 · KV restore H2D #2")

    def test_gpu_device_time_is_preserved_and_copy_correlated(self) -> None:
        path = self.tmp / "gpu_activity.json"
        write_json(path, {"baseTimeNanoseconds": 100_000_000_000, "traceEvents": [
            {"ph": "X", "cat": "user_annotation", "name": "pilarius.copy id=7 H2D req=s1e1",
             "pid": 20, "tid": 30, "ts": 10, "dur": 100},
            {"ph": "X", "cat": "cuda_driver", "name": "cuMemcpyBatchAsync", "pid": 20,
             "tid": 30, "ts": 20, "dur": 50, "args": {"correlation": 9}},
            {"ph": "X", "cat": "gpu_memcpy", "name": "Memcpy HtoD", "ts": 25,
             "dur": 8, "args": {"correlation": 9, "stream": 4, "bytes": 1024}},
        ]})
        activity, = parse_gpu_activity(path)
        self.assertAlmostEqual(activity["time"], 100.000025)
        self.assertAlmostEqual(activity["duration"], .000008)
        self.assertEqual(activity["args"]["transfer_id"], 7)
        self.assertEqual(activity["args"]["requests"], ["s1e1"])
        self.assertEqual(activity["args"]["bytes"], 1024)

    def test_cpu_only_trace_cannot_pass_as_gpu_evidence(self) -> None:
        path = self.tmp / "gpu_activity.json"
        write_json(path, {"baseTimeNanoseconds": 0, "traceEvents": []})
        self.assertEqual(gpu_activity_issues(path), ["GPU activity capture contains no CUDA kernels"])
        write_json(path, {"traceEvents": []})
        with self.assertRaisesRegex(ValueError, "cannot align"):
            parse_gpu_activity(path)

    def test_batch_copy_uses_explicit_gpu_annotation_when_host_api_is_absent(self) -> None:
        path = self.tmp / "gpu_activity.json"
        write_json(path, {"baseTimeNanoseconds": 0, "traceEvents": [
            {"ph": "X", "cat": "gpu_user_annotation", "name": "pilarius.copy id=7 H2D req=s1e1",
             "pid": 0, "tid": 29, "ts": 20, "dur": 10, "args": {"External id": 123}},
            {"ph": "X", "cat": "gpu_memcpy", "name": "Memcpy HtoD", "pid": 0,
             "tid": 29, "ts": 20.001, "dur": 9.998,
             "args": {"device": 0, "stream": 29, "bytes": 4096}},
            {"ph": "X", "cat": "gpu_memcpy", "name": "Memcpy HtoD", "pid": 0,
             "tid": 7, "ts": 21, "dur": .448, "args": {"device": 0, "stream": 7}},
        ]})
        copy, unrelated = parse_gpu_activity(path)
        self.assertEqual(copy["args"]["transfer_id"], 7)
        self.assertEqual(copy["args"]["attribution"], "Kineto GPU annotation")
        self.assertAlmostEqual(copy["duration"], 9.998e-6)
        self.assertEqual(unrelated["args"]["attribution"], "unattributed")
        self.assertNotIn("transfer_id", unrelated["args"])

    def test_gpu_validation_requires_kv_attribution_and_matching_payload(self) -> None:
        path = self.tmp / "gpu_activity.json"
        transfers = self.write("transfer_events.jsonl", json.dumps({
            "schema_version": 1, "event": "submitted", "transfer_id": 7, "bytes": 4096}) + "\n")
        raw = {"baseTimeNanoseconds": 0, "traceEvents": [
            {"ph": "X", "cat": "kernel", "name": "kernel", "ts": 1, "dur": 3,
             "pid": 0, "tid": 7},
            {"ph": "X", "cat": "gpu_user_annotation", "name": "pilarius.copy id=7 H2D req=s1e1",
             "pid": 0, "tid": 29, "ts": 20, "dur": 10},
            {"ph": "X", "cat": "gpu_memcpy", "name": "Memcpy HtoD", "pid": 0,
             "tid": 29, "ts": 20, "dur": 10, "args": {"bytes": 4096}},
        ]}
        write_json(path, raw)
        self.assertEqual(gpu_activity_issues(path, transfers), [])
        raw["traceEvents"][-1]["args"]["bytes"] = 1
        write_json(path, raw)
        self.assertIn("GPU copy bytes disagree", gpu_activity_issues(path, transfers)[0])
        raw["traceEvents"] = raw["traceEvents"][:1]
        write_json(path, raw)
        self.assertIn("no attributed Session Manager H2D", gpu_activity_issues(path, transfers)[0])
    def test_kv_pattern_pre_field_is_optional(self) -> None:
        log = self.write(
            "kv.log", "10.0 kv=0.50 run=8 wait=0 evict=0\n11.0 kv=0.60 run=8 wait=1 evict=0 pre=2\n"
        )
        rows = parse_kv(log, None, None)
        self.assertEqual([row[4] for row in rows], [0, 2])

    def test_gpu_samples_use_their_own_wall_clock(self) -> None:
        rows = parse_gpu(
            self.write(
                "gpu.csv",
                "2026/08/09 14:00:00.000, 3, uuid, name, 50, 1000, 200\n"
                "2026/08/09 14:00:00.200, 3, uuid, name, 70, 1000, 200\n",
            )
        )
        self.assertEqual([row[1] for row in rows], [50, 70])
        self.assertAlmostEqual(rows[1][0] - rows[0][0], 0.2)

    def test_residency_rows_exclude_the_warmup_sentinel(self) -> None:
        rows = parse_residency(
            self.write(
                "residency.log",
                "1755080000.000000 s1e1-abcd:120 s1000000000e1-warm:5\n"
                "1755080000.200000 s1e1-abcd:32 s2e1-efgh:64\n",
            )
        )
        self.assertEqual(rows, [[1755080000.0, [[1, 120]]], [1755080000.2, [[1, 32], [2, 64]]]])

    def test_kv_loads_pair_per_request_and_trigger(self) -> None:
        # A prefetch L and a demand L for the same session may interleave;
        # each R must close its own trigger's window, and trigger-less lines
        # (pre-prefetch logs) read as demand.
        reloads = parse_kv_events(
            self.write(
                "kv_events.log",
                "100.0 L req=s1e1-x cpu_tok=960 gpu_tok=2048 trigger=prefetch\n"
                "100.1 L req=s1e1-x cpu_tok=320 gpu_tok=2048\n"
                "100.2 R req=s1e1-x trigger=prefetch\n"
                "100.3 R req=s1e1-x\n",
            )
        )["reloads"]
        self.assertEqual(
            [(r["trigger"], r["end"]) for r in reloads], [("prefetch", 100.2), ("demand", 100.3)]
        )


class ExportTests(TraceTestCase):
    def test_named_variants_preserve_earlier_exports_and_reject_path_traversal(self) -> None:
        run = make_scheduler_run(self.tmp)
        original = Path(export(run))
        original_profile = Path(export_profile(run))
        before = original.read_bytes(), original_profile.read_bytes()
        variant = Path(export(run, variant="named-streams"))
        profile = Path(export_profile(run, variant="named-streams"))
        self.assertEqual(variant.parent, run / "derived" / "named-streams")
        self.assertEqual(profile.parent, variant.parent)
        self.assertEqual(before, (original.read_bytes(), original_profile.read_bytes()))
        with self.assertRaises(FileExistsError):
            export(run, variant="named-streams")
        with self.assertRaises(FileExistsError):
            export_profile(run, variant="named-streams")
        with self.assertRaises(ValueError):
            export(run, variant="../escape")

    def test_profile_clock_mapping_and_gap_exclude_preload_and_duplicate_sessions(self) -> None:
        events = [
            {"ph": "i", "pid": 1, "tid": 1, "name": "tick", "ts": 40e6},
            *[{"ph": "X", "pid": 1, "tid": sid, "name": "decode", "ts": t * 1e6,
               "dur": 21000, "args": {"timing_scope": "CPU scheduler observation"}} for t in (5, 20, 47.789, 52.023) for sid in (1, 2)],
        ]
        profile = build_profile({"traceEvents": events}, {}, {})
        self.assertEqual(profile["perfetto_offset_s"], 40)
        self.assertEqual(profile["schedule_gaps"], [[7.789, 12.023]])

    def test_profile_preserves_device_times_and_does_not_fill_capture_gaps(self) -> None:
        events = [
            {"ph": "i", "pid": 1, "tid": 1, "name": "tick", "ts": 1000000},
            {"ph": "X", "pid": 1, "tid": 1, "name": "decode", "ts": 1000010, "dur": 5000,
             "args": {"timing_scope": "CPU scheduler observation"}},
            {"ph": "X", "pid": 100, "tid": 7, "name": "Memcpy HtoD", "ts": 1000030.25,
             "dur": .448, "args": {"transfer_id": 5, "bytes": 4096, "direction": "H2D"}},
        ]
        profile = build_profile({"traceEvents": events},
            {"config": {"workload": {"duration_s": 120}}}, {"state": "success"},
            {"kind": "finite_cohort", "makespan_s": 46.65})
        self.assertEqual(profile['cohort_makespan_s'], 46.65)
        gpu = next(t for t in profile["tracks"] if t["scope"] == "gpu")
        self.assertEqual(len(gpu["events"]), 1)
        self.assertAlmostEqual(gpu["events"][0][0], 30.25e-6)
        self.assertAlmostEqual(gpu["events"][0][1], .448e-6)
        self.assertAlmostEqual(profile["gpu_extent"][1], 30.698e-6)
        self.assertEqual(profile["transfers"]["5"]["gpu"][0][3]["bytes"], 4096)
        self.assertGreater(profile["business"][1], profile["gpu_extent"][1])

    def test_profile_is_self_contained_and_rejects_overwrite_or_changed_sources(self) -> None:
        run = make_scheduler_run(self.tmp)
        export(run)
        path = Path(export_profile(run))
        html = path.read_text()
        self.assertIn("DecompressionStream('gzip')", html)
        self.assertNotIn("__PROFILE_DATA__", html)
        self.assertNotIn("<script src=", html)
        with self.assertRaises(FileExistsError):
            export_profile(run)
        another = make_scheduler_run(self.tmp, "20260807_000004_changed")
        export(another)
        (another / "scheduler.log").write_text("changed")
        with self.assertRaisesRegex(ValueError, "source artifact changed"):
            export_profile(another)

    def test_gpu_only_trace_gets_real_stream_lanes(self) -> None:
        run = make_run_dir(self.tmp, "conveyor", "20260924_000000_gpu")
        write_json(run / "gpu_activity.json", {
            "baseTimeNanoseconds": 100_000_000_000,
            "traceEvents": [{"ph": "X", "cat": "kernel", "name": "actual_kernel",
                             "ts": 20, "dur": 7.5, "args": {"device": 0, "stream": 7}}]})
        export(run)
        events = read_trace(run)["traceEvents"]
        kernel = next(e for e in events if e["name"] == "actual_kernel")
        self.assertEqual(kernel["dur"], 7.5)
        self.assertEqual(kernel["args"]["timing_scope"], "CUPTI GPU activity")
        self.assertEqual(kernel["args"]["stream"], 7)
        self.assertEqual(kernel["args"]["stream_role"], "GPU 0 · Compute")
        self.assertTrue(any(e["name"] == "thread_name" and e["args"]["name"] == "GPU 0 · Compute"
                            for e in events))
    def test_load_windows_expose_timing_scope_and_manifest_payload(self) -> None:
        run = make_scheduler_run(self.tmp)
        manifest_path = run / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["config"]["model"] = {"kv_geometry": {"bytes_per_token": 57344}}
        write_json(manifest_path, manifest)
        (run / "kv_events.log").write_text(
            "100.000 L req=s1e1-x cpu_tok=32 gpu_tok=2048 trigger=demand\n"
            "100.010 L req=s1e1-x cpu_tok=1984 gpu_tok=2080 trigger=prefetch\n"
            "100.071 R req=s1e1-x trigger=demand\n"
            "100.110 R req=s1e1-x trigger=prefetch\n"
            "102.000 L req=s2e1-y cpu_tok=16 gpu_tok=0 trigger=demand\n",
            encoding="utf-8",
        )
        export(run)
        windows = [e for e in read_trace(run)["traceEvents"] if "window" in e["name"]]
        self.assertEqual(len(windows), 3)
        demand, prefetch, incomplete = windows
        self.assertEqual(demand["name"], "KV reload window (32 tok)")
        self.assertEqual(demand["dur"], 71000)
        self.assertEqual(demand["args"]["logical_kv_bytes"], 1835008)
        self.assertIn("not DMA duration", demand["args"]["timing_scope"])
        self.assertEqual(demand["args"]["end_event"], "request promotion")
        self.assertEqual(prefetch["name"], "KV prefetch window (1984 tok)")
        self.assertEqual(prefetch["args"]["end_event"], "prefetch completion handled")
        self.assertEqual(incomplete["ph"], "i")
        self.assertIn("completion unobserved", incomplete["name"])

    def test_load_payload_is_unknown_without_run_geometry(self) -> None:
        run = make_scheduler_run(self.tmp)
        (run / "kv_events.log").write_text(
            "100.0 L req=s1e1-x cpu_tok=32 gpu_tok=0 trigger=demand\n"
            "100.1 R req=s1e1-x trigger=demand\n",
            encoding="utf-8",
        )
        export(run)
        window = next(e for e in read_trace(run)["traceEvents"] if "window" in e["name"])
        self.assertNotIn("logical_kv_bytes", window["args"])

    def test_export_never_overwrites_derived_artifacts(self) -> None:
        run = make_scheduler_run(self.tmp)
        export(run)
        with self.assertRaises(FileExistsError):
            export(run)

    def test_run_without_timeline_data_is_rejected(self) -> None:
        run = make_run_dir(self.tmp, "baseline", "20260807_000003_empty")
        write_json(run / "manifest.json", {"schema_version": 2, "config": {}})
        write_json(run / "status.json", {"state": "success"})
        with self.assertRaises(MissingTimelineDataError):
            export(run)
        self.assertFalse((run / "derived").exists())

    def test_scheduler_run_gets_engine_lanes_and_periodic_ticks(self) -> None:
        run = make_scheduler_run(self.tmp)
        bundle = build_bundle(run)
        self.assertTrue(bundle["steps"])
        # period_ms lives in the nested workload section of new manifests.
        self.assertEqual(bundle.get("tick_source"), "periodic_from_manifest")
        export(run)
        engine_slices = [
            event
            for event in read_trace(run)["traceEvents"]
            if event.get("ph") == "X" and event["name"] in {"decode"}
        ]
        self.assertTrue(engine_slices)
