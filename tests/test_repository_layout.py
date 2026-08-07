from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml", ".toml"}
INDEXED_RUN = re.compile(r"`(20\d{6}(?:T|_)[A-Za-z0-9_.-]+)`")


class RepositoryLayoutTests(unittest.TestCase):
    def test_obsolete_top_level_containers_do_not_return(self) -> None:
        self.assertFalse((ROOT / "harness").exists())
        self.assertFalse((ROOT / "calibration").exists())

    def test_project_text_has_no_obsolete_paths(self) -> None:
        forbidden = (
            "harness" + "/",
            "calibration" + "/",
            "results" + "/paper/",
            "results" + "/figures/",
            "results" + "/viz/",
        )
        roots = (
            ROOT / "environment",
            ROOT / "experiments",
            ROOT / "observability",
            ROOT / "tests",
        )
        for base in roots:
            for path in base.rglob("*"):
                if path.is_file() and path.suffix in TEXT_SUFFIXES:
                    text = path.read_text(encoding="utf-8")
                    for obsolete in forbidden:
                        self.assertNotIn(obsolete, text, f"obsolete path in {path.relative_to(ROOT)}")

    def test_markdown_links_resolve(self) -> None:
        markdown_files = [ROOT / "README.md", ROOT / "AGENTS.md"]
        markdown_files.extend((ROOT / "docs").rglob("*.md"))
        markdown_files.extend((ROOT / "environment").rglob("*.md"))
        markdown_files.extend((ROOT / "experiments").rglob("*.md"))
        markdown_files.extend((ROOT / "observability").rglob("*.md"))
        markdown_files.append(ROOT / "results" / "README.md")
        for document in markdown_files:
            for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                local = target.split("#", 1)[0]
                self.assertTrue(
                    (document.parent / local).resolve().exists(),
                    f"broken link in {document.relative_to(ROOT)}: {target}",
                )

    def test_every_retained_run_is_indexed(self) -> None:
        index = (ROOT / "results" / "README.md").read_text(encoding="utf-8")
        actual = {
            run.name
            for runs in (ROOT / "results").glob("*/runs")
            for run in runs.iterdir()
            if run.is_dir()
        }
        for run_id in actual:
            self.assertIn(f"`{run_id}`", index)
        for run_id in INDEXED_RUN.findall(index):
            self.assertIn(run_id, actual, f"indexed run does not exist: {run_id}")

    def test_formal_runs_have_success_status(self) -> None:
        for experiment in ("e1_capacity_bottleneck", "e2_kv_conveyor", "e3_phase_scheduling"):
            for run in (ROOT / "results" / experiment / "runs").iterdir():
                status = json.loads((run / "status.json").read_text(encoding="utf-8"))
                self.assertEqual(status["state"], "success", run.name)

    def test_aggregate_sources_and_artifacts_are_valid(self) -> None:
        for aggregates in (ROOT / "results").glob("*/aggregates"):
            runs = aggregates.parent / "runs"
            for aggregate in (path for path in aggregates.iterdir() if path.is_dir()):
                manifest = json.loads((aggregate / "manifest.json").read_text(encoding="utf-8"))
                for run_id in manifest["source_runs"]:
                    self.assertTrue((runs / run_id).is_dir(), f"missing aggregate input: {run_id}")
                for name, expected in manifest["artifacts"].items():
                    path = aggregate / name
                    self.assertEqual(path.stat().st_size, expected["bytes"])
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    self.assertEqual(digest, expected["sha256"])


if __name__ == "__main__":
    unittest.main()
