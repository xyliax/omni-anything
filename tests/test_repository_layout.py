from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".yml", ".yaml", ".toml"}
RUN_ID = re.compile(r"20\d{6}_\d{6}_[A-Za-z0-9_.-]+")

# Built by concatenation so this file does not trigger its own scan.
OBSOLETE_STRINGS = (
    "harness" + "/",
    "calibration" + "/data",
    "calibration" + "/bench",
    "observability" + "/",
    "results" + "/paper/",
    "results" + "/figures/",
    "results" + "/viz/",
    "e0_dma_" + "interference",
    "e1_capacity_" + "bottleneck",
    "e2_kv_" + "conveyor",
    "e3_phase_" + "scheduling",
)

def scan_targets() -> list[Path]:
    targets = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "results" / "README.md",
        # third_party pin CONTENTS are exempt (upstream text), but our own
        # boundary doc for that directory obeys the same freshness discipline.
        ROOT / "third_party" / "AGENTS.md",
    ]
    # .github is included deliberately: the CI workflow once kept compiling a
    # directory deleted weeks earlier because nothing scanned it.
    for base in (".github", "docs", "environment", "experiments", "lab", "tracekit", "tests"):
        root = ROOT / base
        if root.is_dir():
            targets.extend(
                path
                for path in root.rglob("*")
                if path.is_file() and path.suffix in TEXT_SUFFIXES
            )
    return targets


class RepositoryLayoutTests(unittest.TestCase):
    def test_obsolete_top_level_containers_do_not_return(self) -> None:
        for name in ("harness", "calibration", "observability"):
            self.assertFalse((ROOT / name).exists(), name)
        for name in OBSOLETE_STRINGS[-4:]:
            self.assertFalse((ROOT / "experiments" / name).exists(), name)

    def test_no_text_references_obsolete_paths(self) -> None:
        """Covers docs/, README.md, and AGENTS.md — including backtick paths.

        The pre-refactor guard scanned only code directories and only
        markdown-style links, so the fact layer rotted invisibly. Plain
        substring scanning over every text layer closes both gaps.
        """
        for path in scan_targets():
            text = path.read_text(encoding="utf-8")
            for obsolete in OBSOLETE_STRINGS:
                self.assertNotIn(
                    obsolete, text, f"obsolete path {obsolete!r} in {path.relative_to(ROOT)}"
                )

    def test_markdown_links_resolve(self) -> None:
        markdown_files = [ROOT / "README.md", ROOT / "AGENTS.md"]
        for base in ("docs", "environment", "experiments", "lab", "tracekit"):
            root = ROOT / base
            if root.is_dir():
                markdown_files.extend(root.rglob("*.md"))
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

    def test_each_experiment_retains_exactly_one_run(self) -> None:
        for runs in (ROOT / "results").glob("*/runs"):
            retained = [run for run in runs.iterdir() if run.is_dir()]
            self.assertEqual(
                len(retained),
                1,
                f"{runs.relative_to(ROOT)} must contain exactly one current run",
            )

    def test_documents_do_not_pin_run_ids(self) -> None:
        for path in scan_targets():
            if path.suffix != ".md":
                continue
            match = RUN_ID.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(
                match,
                f"specific run ID in {path.relative_to(ROOT)}: {match.group(0) if match else ''}",
            )

    def test_formal_runs_have_terminal_status(self) -> None:
        for runs in (ROOT / "results").glob("*/runs"):
            for run in runs.iterdir():
                if not run.is_dir():
                    continue
                status = json.loads((run / "status.json").read_text(encoding="utf-8"))
                self.assertIn(status["state"], {"success", "failed", "interrupted"}, run.name)

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
