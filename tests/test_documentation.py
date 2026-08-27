from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from experiments.baseline.config import MODES as BASELINE_MODES
from experiments.shared import model, platform, workload


ROOT = Path(__file__).resolve().parents[1]
HUMAN_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "problem.md",
    ROOT / "docs" / "system.md",
    ROOT / "docs" / "experiments.md",
    ROOT / "docs" / "findings.md",
)
EXPECTED_DOCS_MARKDOWN = {"problem.md", "system.md", "experiments.md", "findings.md"}
AGENT_REGISTRIES = (
    "ownership.json",
    "system-map.json",
    "dynamic-edges.json",
    "contracts.json",
    "change-impact.json",
    "evidence.json",
)
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
HTML_ANCHOR = re.compile(r'<a\s+id="([^"]+)"\s*></a>')
FINDING_HEADING = re.compile(r"(?m)^### (FINDING-[A-Z]\d+)\b")
EVIDENCE_ID = re.compile(r"\bEVIDENCE-[A-Z0-9-]+\b")
RUN_ID = re.compile(r"20\d{6}_\d{6}_[A-Za-z0-9_.-]+")


def load_registry(name: str) -> dict:
    path = ROOT / "docs" / "agent" / name
    return json.loads(path.read_text(encoding="utf-8"))


def owned_markdown_paths() -> tuple[Path, ...]:
    paths: list[Path] = []
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if relative.parts[0] == "third_party":
            continue
        if relative.parts[0] == "results" and relative != Path("results/README.md"):
            continue
        if relative.parts[:2] == ("docs", "papers"):
            continue
        paths.append(path)
    return tuple(sorted(paths))


def resolve_registered_run(run_id: str, run_source: dict[str, str]) -> Path:
    """Resolve an immutable run by a neutral root plus its manifest digest."""

    if set(run_source) != {"root", "manifest_sha256"}:
        raise AssertionError(f"invalid run locator fields: {run_id}")
    relative_root = Path(run_source["root"])
    if len(relative_root.parts) != 2 or relative_root.parts[0] != "results":
        raise AssertionError(f"run locator must name a results/<system> root: {run_id}")
    search_root = ROOT / relative_root
    if not search_root.is_dir():
        raise AssertionError(f"missing registered run root: {run_id}")
    matches = [
        manifest.parent
        for manifest in sorted(search_root.glob("*/manifest.json"))
        if hashlib.sha256(manifest.read_bytes()).hexdigest()
        == run_source["manifest_sha256"]
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"registered manifest digest must resolve exactly once: {run_id} ({len(matches)} matches)"
        )
    return matches[0]


def markdown_slug(heading: str) -> str:
    value = heading.strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[ -]+", "-", value).strip("-")


def document_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = set(HTML_ANCHOR.findall(text))
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            anchors.add(markdown_slug(match.group(1)))
    return anchors


def python_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.add(f"{node.name}.{child.name}")
    return symbols


class DocumentationTests(unittest.TestCase):
    def test_workers_generate_with_ignore_eos(self) -> None:
        for worker in (
            ROOT / "engines/baseline/worker/stream_server.py",
            ROOT / "engines/conveyor/worker/stream_server.py",
        ):
            self.assertIn("ignore_eos=True", worker.read_text(encoding="utf-8"))

    def test_human_core_is_small_and_explicit(self) -> None:
        actual = {path.name for path in (ROOT / "docs").glob("*.md")}
        self.assertEqual(actual, EXPECTED_DOCS_MARKDOWN)
        ownership = load_registry("ownership.json")
        expected = {str(path.relative_to(ROOT)) for path in HUMAN_DOCS}
        self.assertEqual(set(ownership["human_core"]), expected)

    def test_mechanism_tables_agree(self) -> None:
        def first_column(path: Path, marker: str) -> list[str]:
            table = path.read_text(encoding="utf-8").split(marker, 1)[1].split("\n\n", 1)[0]
            return [
                line.split("|")[1].strip()
                for line in table.splitlines()
                if line.startswith("| ") and not line.startswith("| ---")
            ]

        system = first_column(ROOT / "docs" / "system.md", "| 机制 |")
        findings = first_column(ROOT / "docs" / "findings.md", "| 候选机制 |")
        self.assertTrue(system)
        self.assertEqual(sorted(system), sorted(findings))

    def test_research_classification_has_one_owner(self) -> None:
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Research Classification", root_agents)
        for category in ("Research mechanism", "System requirement", "Implementation choice"):
            self.assertIn(f"| {category} |", root_agents)
        for criterion in ("paper claim", "因果假设", "独立 ablation", "可替换实现"):
            self.assertIn(criterion, root_agents)
        ownership = load_registry("ownership.json")
        self.assertEqual(ownership["domains"]["research_classification"], "AGENTS.md")

    def test_agent_registries_are_valid_json(self) -> None:
        for name in AGENT_REGISTRIES:
            data = load_registry(name)
            self.assertEqual(data["schema_version"], 1, name)

    def test_contract_owners_and_file_verification_resolve(self) -> None:
        contracts = load_registry("contracts.json")["contracts"]
        ids = [contract["id"] for contract in contracts]
        self.assertEqual(len(ids), len(set(ids)))
        for contract in contracts:
            for owner in contract["owners"]:
                self.assertTrue(
                    (ROOT / owner).exists(),
                    f"missing owner for {contract['id']}: {owner}",
                )
            for verification in contract["verification"]:
                if verification.endswith((".py", ".md")):
                    self.assertTrue(
                        (ROOT / verification).exists(),
                        f"missing verification for {contract['id']}: {verification}",
                    )

    def test_system_map_paths_and_ids_are_valid(self) -> None:
        system_map = load_registry("system-map.json")
        components = system_map["components"]
        external_nodes = system_map["external_nodes"]
        ids = [component["id"] for component in components]
        self.assertEqual(len(ids), len(set(ids)))
        external_ids = [node["id"] for node in external_nodes]
        self.assertEqual(len(external_ids), len(set(external_ids)))
        self.assertFalse(set(ids) & set(external_ids))
        for node in external_nodes:
            self.assertTrue(node["kind"])
            self.assertTrue(node["locator"])
            self.assertTrue(node["role"])
        for component in components:
            path = ROOT / component["path"]
            self.assertTrue(
                path.exists(),
                f"missing component path for {component['id']}: {component['path']}",
            )
            if path.suffix == ".py":
                known = python_symbols(path)
                for entrypoint in component["entrypoints"]:
                    if entrypoint == "sitecustomize module import":
                        continue
                    self.assertIn(
                        entrypoint,
                        known,
                        f"missing Python entrypoint for {component['id']}: {entrypoint}",
                    )
            elif path.suffix == ".go":
                text = path.read_text(encoding="utf-8")
                for entrypoint in component["entrypoints"]:
                    self.assertRegex(text, rf"\bfunc\s+{re.escape(entrypoint)}\s*\(")

    def test_system_map_covers_every_executable_worker_target(self) -> None:
        components = load_registry("system-map.json")["components"]
        mapped_paths = {component["path"] for component in components}
        expected = {spec.worker for spec in BASELINE_MODES.values()}
        expected.add("engines/conveyor/worker/stream_server.py")
        self.assertTrue(expected <= mapped_paths, expected - mapped_paths)

    def test_dynamic_edges_reference_registered_components(self) -> None:
        system_map = load_registry("system-map.json")
        components = {item["id"] for item in system_map["components"]}
        external = {item["id"] for item in system_map["external_nodes"]}
        edges = load_registry("dynamic-edges.json")["edges"]
        edge_ids = [edge["id"] for edge in edges]
        self.assertEqual(len(edge_ids), len(set(edge_ids)))
        for edge in edges:
            endpoints: list[str] = []
            for key in ("from", "to"):
                value = edge[key]
                endpoints.extend(value if isinstance(value, list) else [value])
            unknown = set(endpoints) - components - external
            self.assertEqual(unknown, set(), f"unknown endpoint in {edge['id']}")
            source = edge["source"]
            if source.startswith(("engines/", "experiments/", "infra/", "third_party/")):
                self.assertTrue((ROOT / source).exists(), f"missing source in {edge['id']}: {source}")
            for verification in edge["verify"]:
                if verification.endswith((".py", ".md")):
                    self.assertTrue(
                        (ROOT / verification).exists(),
                        f"missing verification in {edge['id']}: {verification}",
                    )

    def test_change_impact_rules_resolve_their_actions(self) -> None:
        rules = load_registry("change-impact.json")["rules"]
        ids = [rule["id"] for rule in rules]
        self.assertEqual(len(ids), len(set(ids)))
        for rule in rules:
            self.assertTrue(rule["when"], rule["id"])
            for action in (*rule["inspect"], *rule["verify"]):
                self.assertTrue(
                    (ROOT / action).exists(),
                    f"missing change-impact action for {rule['id']}: {action}",
                )

    def test_dynamic_edge_catalog_covers_runtime_boundaries(self) -> None:
        edges = {edge["id"] for edge in load_registry("dynamic-edges.json")["edges"]}
        required = {
            "EDGE-RUNNER-WORKER",
            "EDGE-RUNNER-GATEWAY",
            "EDGE-RUNNER-CLIENT-CONTROLLER",
            "EDGE-CLIENT-CONTROLLER-SHARDS",
            "EDGE-CLIENT-SHARD-RESULT",
            "EDGE-CLIENT-CONTROLLER-RESULT",
            "EDGE-RUNNER-GPU-MONITOR",
            "EDGE-CLIENT-GATEWAY-WEBSOCKET",
            "EDGE-BASELINE-GATEWAY-WORKER-STEP",
            "EDGE-CONVEYOR-GATEWAY-WORKER-STEP",
            "EDGE-BASELINE-WORKER-ENGINECORE",
            "EDGE-CONVEYOR-WORKER-ENGINECORE",
            "EDGE-SITECUSTOMIZE-ENGINE-PATCH",
            "EDGE-PATCH-LOADER-MODULES",
            "EDGE-CONVEYOR-PATCH-VLLM",
            "EDGE-WORKER-PREFETCH-UTILITY",
            "EDGE-BASELINE-FIX-VLLM",
            "EDGE-TRACE-PATCH-VLLM",
        }
        self.assertTrue(required <= edges, required - edges)

    def test_registered_monkeypatch_targets_exist_in_source(self) -> None:
        edges = {edge["id"]: edge for edge in load_registry("dynamic-edges.json")["edges"]}
        source_sets = {
            "EDGE-CONVEYOR-PATCH-VLLM": tuple(
                (ROOT / "engines/conveyor/worker/engine_patch").glob("*.py")
            ),
            "EDGE-BASELINE-FIX-VLLM": (
                ROOT / "engines/baseline/worker/engine_fix/sitecustomize.py",
            ),
            "EDGE-TRACE-PATCH-VLLM": (
                ROOT / "infra/trace/collectors/vllm_scheduler_trace/sitecustomize.py",
            ),
        }
        for edge_id, sources in source_sets.items():
            text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
            for target in edges[edge_id]["patch_targets"]:
                self.assertRegex(
                    text,
                    rf"\b{re.escape(target)}\s*=",
                    f"stale monkeypatch target in {edge_id}: {target}",
                )

    def test_finding_ids_are_unique_and_covered_by_evidence(self) -> None:
        text = (ROOT / "docs" / "findings.md").read_text(encoding="utf-8")
        findings = FINDING_HEADING.findall(text)
        self.assertEqual(len(findings), len(set(findings)))

        evidence = load_registry("evidence.json")["evidence"]
        evidence_ids = [entry["id"] for entry in evidence]
        self.assertEqual(len(evidence_ids), len(set(evidence_ids)))
        covered = {finding for entry in evidence for finding in entry["supports"]}
        self.assertEqual(set(findings), covered)

        mentioned = set(EVIDENCE_ID.findall(text))
        self.assertTrue(mentioned <= set(evidence_ids), mentioned - set(evidence_ids))

    def test_evidence_sources_resolve_and_formal_runs_are_clean(self) -> None:
        registry = load_registry("evidence.json")
        expected_roles = {
            "formal",
            "diagnostic",
            "legacy-unreconstructable",
            "source-audit",
            "external-source-audit",
        }
        self.assertEqual(set(registry["role_definitions"]), expected_roles)
        run_sources = registry["run_sources"]
        for run_id, run_source in run_sources.items():
            run = resolve_registered_run(run_id, run_source)
            digest = hashlib.sha256((run / "manifest.json").read_bytes()).hexdigest()
            self.assertEqual(digest, run_source["manifest_sha256"], run_id)
            status = json.loads((run / "status.json").read_text(encoding="utf-8"))
            for name, recorded in status["artifacts"].items():
                artifact = run / name
                self.assertTrue(artifact.is_file(), f"missing retained artifact: {run_id}/{name}")
                self.assertEqual(artifact.stat().st_size, recorded["bytes"], f"{run_id}/{name}")
                self.assertEqual(
                    hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    recorded["sha256"],
                    f"retained artifact drift: {run_id}/{name}",
                )
            self.assertTrue(
                set(status["validation"]["required"]) <= set(status["artifacts"]),
                f"required retained artifact lacks digest: {run_id}",
            )

        for entry in registry["evidence"]:
            self.assertIn(entry["role"], expected_roles, entry["id"])
            if entry["role"] == "source-audit":
                self.assertTrue(
                    any(source.get("kind") == "source" for source in entry["sources"]),
                    f"source audit lacks current source: {entry['id']}",
                )
            if entry["role"] == "external-source-audit":
                self.assertTrue(
                    any(
                        source.get("kind") in {"third-party-pin", "dated-context"}
                        for source in entry["sources"]
                    ),
                    f"external audit lacks external source: {entry['id']}",
                )
            for source in entry["sources"]:
                path_text = source.get("path")
                if path_text:
                    self.assertTrue(
                        (ROOT / path_text).exists(),
                        f"missing evidence source for {entry['id']}: {path_text}",
                    )
                if source.get("kind") != "run":
                    continue
                self.assertIn(source["ref"], run_sources, entry["id"])
                run = resolve_registered_run(source["ref"], run_sources[source["ref"]])
                manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
                status = json.loads((run / "status.json").read_text(encoding="utf-8"))
                self.assertIn(status["state"], {"success", "failed", "interrupted"})
                if entry["role"] == "formal":
                    self.assertFalse(manifest["git"]["dirty"], entry["id"])
                    self.assertEqual(status["state"], "success", entry["id"])
                if entry["role"] == "diagnostic" and manifest["git"]["dirty"]:
                    patch = source.get("patch_artifact")
                    self.assertIsNotNone(patch, f"dirty diagnostic lacks patch: {entry['id']}")
                    self.assertTrue((run / patch).is_file(), f"missing diagnostic patch: {patch}")

    def test_owned_markdown_links_and_fragments_resolve(self) -> None:
        for document in owned_markdown_paths():
            for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
                if "://" in target:
                    continue
                file_part, _, fragment = target.partition("#")
                target_path = (
                    document.resolve()
                    if not file_part
                    else (document.parent / file_part).resolve()
                )
                self.assertTrue(
                    target_path.exists(),
                    f"broken link in {document.relative_to(ROOT)}: {target}",
                )
                if fragment and target_path.suffix == ".md":
                    self.assertIn(
                        fragment,
                        document_anchors(target_path),
                        f"broken fragment in {document.relative_to(ROOT)}: {target}",
                    )

    def test_exact_run_ids_stay_out_of_structured_records(self) -> None:
        records = ROOT / "docs" / "agent" / "records"
        for path in records.glob("*.json"):
            match = RUN_ID.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(match, f"exact run id in {path.relative_to(ROOT)}")

    def test_measured_profile_table_matches_executable_constants(self) -> None:
        text = (ROOT / "docs" / "experiments.md").read_text(encoding="utf-8")
        expected_rows = (
            f"| 模型 | {model.ID.rsplit('/', 1)[-1]} |",
            f"| 周期 \\(T\\) | {workload.PERIOD_MS} ms |",
            f"| 默认会话数 | {workload.SESSIONS} |",
            f"| 每周期输出 token 上限 \\(M\\) | {workload.OUTPUT_TOKEN_CAP} |",
            f"| 单 token KV bytes | {model.KV_BYTES_PER_TOKEN // 1024} KiB |",
        )
        for row in expected_rows:
            self.assertIn(row, text)
        self.assertIn(f"| 设备 | {platform.DEVICE_NAME}, 24 GiB, PCIe Gen3 |", text)
        requirements = (
            ROOT / "infra/env/profiles/cuda13_vllm023/requirements.in"
        ).read_text(encoding="utf-8")
        runtime = re.search(r"(?m)^vllm(?:\[[^]]+\])?==(\d+\.\d+)", requirements)
        self.assertIsNotNone(runtime)
        self.assertIn(f"| 运行时 | vLLM {runtime.group(1)} |", text)

    def test_problem_delegates_measured_profile_identity(self) -> None:
        text = (ROOT / "docs" / "problem.md").read_text(encoding="utf-8")
        self.assertNotIn(model.ID.rsplit("/", 1)[-1], text)
        self.assertNotIn(platform.DEVICE_NAME, text)
        self.assertNotRegex(text, r"vLLM\s+\d+\.\d+")

    def test_experiment_record_template_matches_contract(self) -> None:
        contract = load_registry("contracts.json")["experiment_record_v1"]
        template = json.loads(
            (ROOT / "docs" / "agent" / "records" / "template.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(template), set(contract["required_fields"]))

    def test_python_entrypoints_support_help(self) -> None:
        for module in ("experiments.baseline", "infra.trace.perfetto"):
            result = subprocess.run(
                [sys.executable, "-m", module, "--help"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, f"{module}: {result.stderr}")

    def test_readme_is_a_minimal_landing_page(self) -> None:
        lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        headings = [line for line in lines if re.match(r"^#{1,6}\s", line)]
        self.assertEqual(headings, ["# Omni-Anything", "## Getting Started"])
        text = "\n".join(lines)
        for step in ("infra/env/setup.sh", "infra/env/verify.py", "-m experiments.baseline"):
            self.assertIn(step, text)


if __name__ == "__main__":
    unittest.main()
