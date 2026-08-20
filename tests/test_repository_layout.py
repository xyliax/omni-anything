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
OBSOLETE_CONTEXT_PATH = re.compile(r"(?<![.\w/])" + "context" + r"/")
OBSOLETE_RUNS_LAYER = re.compile(r"results/[\w-]+/" + "runs")
# Directories dissolved by the 2026-08-19 system/measurement/infra split.
# Path-position forms only (lookbehind): the bare words remain legal prose.
OBSOLETE_SPLIT_PATHS = tuple(
    re.compile(r"(?<![.\w/-])" + name + r"/") for name in ("la" + "b", "trace" + "kit", "environ" + "ment")
)
# Python module form of the same dissolved packages (the README once kept
# advertising the old trace-export module path because only the slash form
# was guarded).
OBSOLETE_MODULE_FORM = re.compile(
    r"(?<![.\w])(" + "|".join(("la" + "b", "trace" + "kit", "environ" + "ment")) + r")"
    r"\.(workflow|artifacts|probes|process|collect|collectors|parse|bundle|perfetto|verify)\b"
)
# engines/ is spawned by path, never imported; nothing enforces that at runtime
# (no __init__.py is a marker, not a mechanism — PEP 420 would still import it).
ENGINES_IMPORT = re.compile(r"(?m)^\s*(from|import)\s+" + "engines" + r"\b")
OBSOLETE_ENGINE_HOMES = (
    "experiments/" + "baseline/worker",
    "experiments/" + "conveyor/worker",
    "experiments/" + "conveyor/gateway",
)
OBSOLETE_DOCUMENTS = (
    "docs/architecture.md",
    "docs/experiment-log.md",
    "docs/metronome.md",
    "infra/env/README.md",
)


def run_directories() -> list[Path]:
    return [
        run
        for experiment in (ROOT / "results").iterdir()
        if experiment.is_dir()
        for run in experiment.iterdir()
        if run.is_dir() and run.name != "aggregates"
    ]


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
    for base in (".github", "docs", "engines", "experiments", "infra", "tests"):
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
        # Tolerate a stale directory that holds only gitignored bytecode caches:
        # an in-place pull from a pre-split checkout leaves the old dirs behind
        # with nothing but __pycache__ inside — a migration artifact, not a
        # returning container.
        for name in ("harness", "calibration", "observability", "context", "lab", "tracekit", "environment"):
            root = ROOT / name
            if not root.exists():
                continue
            residue = [
                path
                for path in root.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            ]
            self.assertEqual(residue, [], f"{name}/ has returned with content: {residue[:3]}")
        for name in OBSOLETE_STRINGS[-4:]:
            self.assertFalse((ROOT / "experiments" / name).exists(), name)
        for name in OBSOLETE_DOCUMENTS:
            self.assertFalse((ROOT / name).exists(), f"superseded document returned: {name}")

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
            match = OBSOLETE_CONTEXT_PATH.search(text)
            self.assertIsNone(
                match,
                f"obsolete path {match.group(0)!r} in {path.relative_to(ROOT)}"
                if match
                else "",
            )
            match = OBSOLETE_RUNS_LAYER.search(text)
            self.assertIsNone(
                match,
                f"obsolete runs/ layer {match.group(0)!r} in {path.relative_to(ROOT)}"
                if match
                else "",
            )
            for pattern in OBSOLETE_SPLIT_PATHS:
                match = pattern.search(text)
                self.assertIsNone(
                    match,
                    f"obsolete pre-split path {match.group(0)!r} in {path.relative_to(ROOT)}"
                    if match
                    else "",
                )
            for stale in OBSOLETE_ENGINE_HOMES:
                self.assertNotIn(
                    stale, text, f"obsolete engine home {stale!r} in {path.relative_to(ROOT)}"
                )
            match = OBSOLETE_MODULE_FORM.search(text)
            self.assertIsNone(
                match,
                f"obsolete module form {match.group(0)!r} in {path.relative_to(ROOT)}"
                if match
                else "",
            )

    def test_engines_is_never_imported(self) -> None:
        for path in scan_targets():
            if path.suffix != ".py":
                continue
            match = ENGINES_IMPORT.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(
                match,
                f"engines/ must be spawned by path, not imported: "
                f"{match.group(0).strip()!r} in {path.relative_to(ROOT)}"
                if match
                else "",
            )

    def test_markdown_links_resolve(self) -> None:
        markdown_files = [ROOT / "README.md", ROOT / "AGENTS.md"]
        for base in ("docs", "engines", "experiments", "infra"):
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

    def test_run_directories_use_run_id_shape(self) -> None:
        for run in run_directories():
            self.assertRegex(
                run.name,
                RUN_ID,
                f"{run.relative_to(ROOT)} is not a run-id directory",
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
        for run in run_directories():
            status = json.loads((run / "status.json").read_text(encoding="utf-8"))
            self.assertIn(status["state"], {"success", "failed", "interrupted"}, run.name)

    def test_aggregate_sources_and_artifacts_are_valid(self) -> None:
        for aggregates in (ROOT / "results").glob("*/aggregates"):
            runs = aggregates.parent
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
