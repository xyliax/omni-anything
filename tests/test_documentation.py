from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
import zipfile
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
CJK = re.compile(r"[\u3400-\u9fff]")
RUN_ID = re.compile(r"20\d{6}_\d{6}_[A-Za-z0-9_.-]+")
DEPRECATED_SOURCE_PATTERNS = {
    "project-specific KV parking vocabulary": re.compile(
        r"(?<![A-Za-z0-9])(?:un)?park(?:ed|ing|s)?(?![A-Za-z0-9])|omni_park|OMNI_PARK",
        re.IGNORECASE,
    ),
    "anonymous cache-population vocabulary": re.compile(
        r"anonymous[-_ ](?:material\w*|preload\w*)", re.IGNORECASE
    ),
    "incorrect deadline vocabulary": re.compile(
        r"hard[-_ ](?:tick[-_ ])?deadline|inelastic[-_ ]deadline", re.IGNORECASE
    ),
    "output cap described as a requirement": re.compile(
        r"delivery[-_ ]quota|tokens[-_ ]required[-_ ]per[-_ ]tick|quota[-_ ]met",
        re.IGNORECASE,
    ),
    "deprecated buffered-output vocabulary": re.compile(
        r"take[-_ ]from[-_ ]stock|(?<![A-Za-z0-9])inventory(?![A-Za-z0-9])|inv[-_ ]backlog",
        re.IGNORECASE,
    ),
    "deprecated release-offset vocabulary": re.compile(
        r"phase[-_ ](?:is[-_ ]a[-_ ]resource|stagger(?:ing)?|offset(?:[-_ ]scheduling)?)",
        re.IGNORECASE,
    ),
    "obsolete background-result story": re.compile(
        r"agent[-_ ](?:result[-_ ])?injection|result[-_ ]injection", re.IGNORECASE
    ),
    "paper-facing comparison shorthand": re.compile(
        r"(?<![A-Za-z0-9])arms?(?![A-Za-z0-9])", re.IGNORECASE
    ),
    "deprecated initial-context vocabulary": re.compile(
        r"warm[-_ ]start|seed[-_ ]tokens", re.IGNORECASE
    ),
    "ambiguous capacity-boundary metaphor": re.compile(
        r"capacity[-_ ](?:wall|boundary|saturation)|memory[-_ ]cliff", re.IGNORECASE
    ),
    "misspelled system proper noun": re.compile(
        r"(?<![A-Za-z0-9])Conveyer(?![A-Za-z0-9])", re.IGNORECASE
    ),
    "deprecated analytical-scenario label": re.compile(
        r"paper[-_ ]configuration", re.IGNORECASE
    ),
}
DEPRECATED_PROSE_PATTERNS = {
    "initial context called a seed": re.compile(r"\bseed(?:ed|ing|s)?\b", re.IGNORECASE),
    "historical queue pathology in current narrative": re.compile(r"\bdeadlock\b", re.IGNORECASE),
}
CONTEXT_NARRATIVE_PATTERNS = {
    "obsolete background-result writeback": re.compile(r"后台结果写回", re.IGNORECASE),
    "obsolete foreground/background scope": re.compile(
        r"前台双工.*后台智能体", re.IGNORECASE | re.DOTALL
    ),
    "obsolete per-period deadline claim": re.compile(
        r"每(?:个)?周期.*deadline", re.IGNORECASE | re.DOTALL
    ),
    "unsupported complete-overlap claim": re.compile(
        r"迁移.*计算完全重叠|计算.*迁移完全重叠", re.IGNORECASE | re.DOTALL
    ),
}
CONTEXT_AUTHORED_ROOTS = (ROOT / ".context" / "ideas", ROOT / ".context" / "slides")
CONTEXT_TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".svg", ".html", ".xml"}
ACTIVE_TEXT_SUFFIXES = {
    ".cfg",
    ".go",
    ".in",
    ".ini",
    ".json",
    ".lock",
    ".md",
    ".mod",
    ".patch",
    ".proto",
    ".py",
    ".rst",
    ".sh",
    ".sum",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


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
        paths.append(path)
    return tuple(sorted(paths))


def active_first_party_sources() -> tuple[Path, ...]:
    roots = (
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        ROOT / ".github",
        ROOT / "docs",
        ROOT / "engines",
        ROOT / "experiments",
        ROOT / "infra",
        ROOT / "tests",
        ROOT / "results" / "README.md",
    )
    paths: list[Path] = []
    for entry in roots:
        candidates = (entry,) if entry.is_file() else entry.rglob("*")
        for path in candidates:
            if not path.is_file() or path.suffix.lower() not in ACTIVE_TEXT_SUFFIXES:
                continue
            relative = path.relative_to(ROOT)
            if relative == Path("docs/agent/legacy-experiment-log.md"):
                continue
            if relative == Path("tests/test_documentation.py"):
                continue
            if "__pycache__" in relative.parts:
                continue
            paths.append(path)
    return tuple(sorted(set(paths)))


def text_for_terminology_scan(path: Path) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    relative = path.relative_to(ROOT)
    if relative == Path("docs/problem.md"):
        # The glossary must retain old names in its fourth, explicitly
        # deprecated column so readers can migrate historical material. Scan
        # every other column and all prose normally.
        sanitized: list[str] = []
        in_glossary = False
        for line in lines:
            if line.startswith("| Preferred term |"):
                in_glossary = True
            elif in_glossary and not line.startswith("|"):
                in_glossary = False
            if in_glossary and line.startswith("|"):
                cells = line.split("|")
                if len(cells) >= 6:
                    cells[-2] = " [deprecated aliases omitted from guard] "
                    line = "|".join(cells)
            sanitized.append(line)
        lines = sanitized
    return "\n".join(lines)


def pptx_text(path: Path) -> str:
    """Extract all presentation XML text so ignored decks cannot bypass guards."""

    fragments: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = sorted(
                name
                for name in archive.namelist()
                if name.startswith("ppt/") and name.endswith(".xml")
            )
            for name in members:
                root = ET.fromstring(archive.read(name))
                fragments.append("".join(node.text or "" for node in root.iter()))
    except (OSError, zipfile.BadZipFile, ET.ParseError) as error:
        raise AssertionError(f"unreadable context presentation: {path.relative_to(ROOT)}") from error
    return "\n".join(fragments)


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
    def test_deprecated_identifier_variants_are_guarded(self) -> None:
        examples = {
            "project-specific KV parking vocabulary": "OMNI_UNPARK_KV",
            "anonymous cache-population vocabulary": "anonymous_materialization",
            "incorrect deadline vocabulary": "hard_tick_deadline",
            "output cap described as a requirement": "tokens_required_per_tick",
            "deprecated buffered-output vocabulary": "delivery_inventory_depth",
            "deprecated release-offset vocabulary": "phase_offset_scheduling",
            "obsolete background-result story": "agent_result_injection",
            "paper-facing comparison shorthand": "baseline_arm_config",
            "deprecated initial-context vocabulary": "warm_start",
            "ambiguous capacity-boundary metaphor": "capacity_wall",
            "misspelled system proper noun": "OMNI_CONVEYER_MODE",
            "deprecated analytical-scenario label": "paper_configuration",
        }
        for description, example in examples.items():
            self.assertRegex(example, DEPRECATED_SOURCE_PATTERNS[description], description)

    def test_deprecated_terms_do_not_reenter_active_sources(self) -> None:
        failures: list[str] = []
        for path in active_first_party_sources():
            text = text_for_terminology_scan(path)
            patterns = dict(DEPRECATED_SOURCE_PATTERNS)
            if path.suffix in {".md", ".json"}:
                patterns.update(DEPRECATED_PROSE_PATTERNS)
            for description, pattern in patterns.items():
                match = pattern.search(text)
                if match:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {description}: {match.group(0)!r}"
                    )
        self.assertEqual(failures, [], "\n".join(failures))

    def test_ignored_project_context_cannot_reintroduce_obsolete_narratives(self) -> None:
        failures: list[str] = []
        metadata = sorted(ROOT.rglob(".DS_Store"))
        failures.extend(f"forbidden metadata file: {path.relative_to(ROOT)}" for path in metadata)

        patterns = {
            **DEPRECATED_SOURCE_PATTERNS,
            **DEPRECATED_PROSE_PATTERNS,
            **CONTEXT_NARRATIVE_PATTERNS,
        }
        for context_root in CONTEXT_AUTHORED_ROOTS:
            if not context_root.exists():
                continue
            for path in sorted(context_root.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT)
                if path.name.startswith("~$"):
                    failures.append(f"forbidden Office lock file: {relative}")
                    continue
                if path.suffix.lower() == ".pptx":
                    text = pptx_text(path)
                elif path.suffix.lower() in CONTEXT_TEXT_SUFFIXES:
                    text = path.read_text(encoding="utf-8", errors="replace")
                else:
                    failures.append(f"unscannable authored context artifact: {relative}")
                    continue
                for description, pattern in patterns.items():
                    match = pattern.search(text)
                    if match:
                        failures.append(f"{relative}: {description}: {match.group(0)!r}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_output_generation_and_gateway_delivery_are_separate(self) -> None:
        problem = (ROOT / "docs/problem.md").read_text(encoding="utf-8")
        experiments = (ROOT / "docs/experiments.md").read_text(encoding="utf-8")
        contract = next(
            item
            for item in load_registry("contracts.json")["contracts"]
            if item["id"] == "CONTRACT-OUTPUT-CAP"
        )

        for fact in (
            "是抽象模型中的生成上限，不是最低交付量",
            "模型生成进度与用户可见交付是两个不同对象",
            "问题定义不选择其中一种 output architecture",
            "精确生成与交付口径由 [`Experiments`](experiments.md) 定义",
        ):
            self.assertIn(fact, problem)
        for fact in (
            "两个当前 first-party worker 都设置 `ignore_eos=True`",
            "matched Metronome baseline 运行到每段 \\(M+8\\) 的 cap",
            "Conveyor 运行到每段 \\(M\\) 的 cap",
            "不提供模型自然短输出或 learned silent-token behavior 的证据",
            "且不等于 \\(m_{i,k}\\)",
        ):
            self.assertIn(fact, experiments)
        for worker in (
            ROOT / "engines/baseline/worker/stream_server.py",
            ROOT / "engines/conveyor/worker/stream_server.py",
        ):
            self.assertIn("ignore_eos=True", worker.read_text(encoding="utf-8"))
        self.assertIn("generated-token count is distinct from gateway delivery", contract["rule"])
        self.assertIn("ignore_eos=True", contract["rule"])

    def test_human_core_is_small_and_explicit(self) -> None:
        actual = {path.name for path in (ROOT / "docs").glob("*.md")}
        self.assertEqual(actual, EXPECTED_DOCS_MARKDOWN)
        ownership = load_registry("ownership.json")
        expected = {str(path.relative_to(ROOT)) for path in HUMAN_DOCS}
        self.assertEqual(set(ownership["human_core"]), expected)

    def test_human_headings_follow_paper_style_and_are_spaced(self) -> None:
        for path in HUMAN_DOCS:
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                if not re.match(r"^#{1,6}\s+", line):
                    continue
                finding = re.match(r"^### FINDING-[A-Z]\d+\s+—\s+(.+)$", line)
                if finding:
                    self.assertIsNotNone(
                        CJK.search(finding.group(1)),
                        f"finding title must explain the stable ID in Chinese: "
                        f"{path.relative_to(ROOT)}:{index + 1}",
                    )
                else:
                    self.assertIsNone(
                        CJK.search(line),
                        f"paper-style heading must be English: "
                        f"{path.relative_to(ROOT)}:{index + 1}",
                    )
                if index + 1 < len(lines):
                    self.assertEqual(
                        lines[index + 1],
                        "",
                        f"heading must be followed by a blank line: "
                        f"{path.relative_to(ROOT)}:{index + 1}",
                    )

    def test_system_separates_research_mechanisms_from_delivery_implementation(self) -> None:
        text = (ROOT / "docs" / "system.md").read_text(encoding="utf-8")
        mechanisms = text.split("## Research Mechanisms", 1)[1].split(
            "## Release-Offset Scheduling", 1
        )[0]
        table = mechanisms.split("| 机制 |", 1)[1].split("\n\n", 1)[0]
        mechanism_rows = [
            line
            for line in table.splitlines()
            if line.startswith("| ") and not line.startswith("| ---")
        ]
        self.assertEqual(len(mechanism_rows), 3)
        for mechanism in (
            "释放偏移调度（release-offset scheduling）",
            "带主机后备的 KV 部分逐出（partial KV eviction with host backing）",
            "KV 预取（KV prefetching）",
        ):
            self.assertTrue(any(mechanism in row for row in mechanism_rows), mechanism)
        for implementation_detail in (
            "output delivery",
            "transport",
            "cache-key 注册",
        ):
            self.assertIn(implementation_detail, mechanisms)
            self.assertNotIn(implementation_detail, table)

        delivery = text.split("## Output Delivery", 1)[1].split("## One Session Cycle", 1)[0]
        for fact in (
            "同步返回、异步流、缓冲消费或额外媒体处理",
            "不改变释放偏移、部分逐出和 KV 预取的定义",
            "模型生成推进和用户可见结果推进必须分别观察",
            "不能把“调用仍在返回”直接当成",
        ):
            self.assertIn(fact, delivery)
        self.assertIn(
            "首个既不 GPU-resident 也不 host-backed 的 coverage gap",
            text,
        )
        for logical_component in (
            "Session Controller",
            "Serving Frontend",
            "Scheduler and KV Residency Manager",
            "GPU KV Pool",
            "Host KV Backing",
            "User-Visible Output Path",
        ):
            self.assertIn(logical_component, text)
        self.assertIn("这个逻辑分层不要求特定进程边界或 IPC", text)

    def test_mutable_experiment_details_stay_in_experiments_owner(self) -> None:
        narrative_docs = (
            ROOT / "README.md",
            ROOT / "docs/problem.md",
            ROOT / "docs/system.md",
            ROOT / "docs/findings.md",
        )
        forbidden = {
            "single-device scope": r"单张\s*GPU|single[- ]GPU",
            "current model or output stack": (
                r"Qwen2\.5-Omni|Thinker|Talker|Code2Wav|RTX\s*3090"
            ),
            "mutable environment profile": r"cuda13_vllm023|\.venv-vllm023|PCIe(?:\s+Gen3)?",
            "current comparator identity": r"Metronome|paringest",
            "runner or interface field": (
                r"\bStep\b|M\+8|max_tokens|ignore_eos|deadline_met|tokens_per_tick|"
                r"st\.tokens|prefetch_kv|free\(request\)|evict_blocks|"
                r"SimpleCPUOffloadConnector|WAITING_FOR_REMOTE_KVS"
            ),
            "implementation wiring or log": (
                r"gRPC|msgpack|ZMQ|sitecustomize|nvidia-smi|"
                r"gateway_ticks\.log|scheduler\.log|residency\.log|"
                r"kv_events\.log|per_request\.log"
            ),
            "single diagnostic point": (
                r"N\s*=\s*8|K\s*=\s*128|4096|120\s*s|0\.29|0\.99|70\s*ms"
            ),
        }
        failures: list[str] = []
        for path in narrative_docs:
            text = path.read_text(encoding="utf-8")
            for description, pattern in forbidden.items():
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {description}: {match.group(0)!r}"
                    )
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        scope_match = re.search(
            forbidden["single-device scope"]
            + "|"
            + forbidden["current model or output stack"],
            root_agents,
            flags=re.IGNORECASE,
        )
        if scope_match:
            failures.append(
                f"AGENTS.md: current prototype narrowed project scope: {scope_match.group(0)!r}"
            )
        self.assertEqual(failures, [], "\n".join(failures))

    def test_research_classification_has_one_owner_and_is_not_regressed(self) -> None:
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Research Classification", root_agents)
        for category in ("Research mechanism", "System requirement", "Implementation choice"):
            self.assertIn(f"| {category} |", root_agents)
        for criterion in ("paper claim", "因果假设", "独立 ablation", "可替换实现"):
            self.assertIn(criterion, root_agents)

        ownership = load_registry("ownership.json")
        self.assertEqual(ownership["domains"]["research_classification"], "AGENTS.md")
        current_docs = (
            ROOT / "README.md",
            ROOT / "docs/system.md",
            ROOT / "docs/experiments.md",
            ROOT / "docs/findings.md",
            ROOT / "engines/AGENTS.md",
            ROOT / "engines/conveyor/AGENTS.md",
            ROOT / "experiments/conveyor/AGENTS.md",
            ROOT / "results/README.md",
        )
        for path in current_docs:
            current = path.read_text(encoding="utf-8")
            self.assertNotIn("取现货交付", current, path.relative_to(ROOT))
            self.assertNotIn("take-from-stock delivery", current.lower(), path.relative_to(ROOT))
            self.assertNotIn("四个机制", current, path.relative_to(ROOT))

        findings = (ROOT / "docs/findings.md").read_text(encoding="utf-8")
        current_state_table = findings.split("| 候选机制 |", 1)[1].split("\n\n", 1)[0]
        current_state_rows = [
            line
            for line in current_state_table.splitlines()
            if line.startswith("| ") and not line.startswith("| ---")
        ]
        self.assertEqual(len(current_state_rows), 3)
        self.assertNotIn("EVIDENCE-H2-METRICS", current_state_table)
        h2 = findings.split("### FINDING-H2", 1)[1].split("### FINDING-H3", 1)[0]
        self.assertIn("测量语义发现", h2)
        self.assertIn("不是研究机制", h2)

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
        edges = {edge["id"]: edge for edge in load_registry("dynamic-edges.json")["edges"]}
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
        self.assertTrue(required <= set(edges), required - set(edges))
        self.assertIn("/tmp/sfd_", edges["EDGE-CLIENT-SHARD-RESULT"]["binding"])
        self.assertIn("hazards", edges["EDGE-CLIENT-SHARD-RESULT"])
        self.assertIn("safety", edges["EDGE-CLIENT-SHARD-RESULT"])
        for runner in (
            ROOT / "experiments/baseline/runner.py",
            ROOT / "experiments/conveyor/runner.py",
        ):
            runner_text = runner.read_text(encoding="utf-8")
            self.assertIn("client_scratch_results=", runner_text)
            self.assertIn('Path("/tmp") / f"sfd_', runner_text)

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
        self.assertGreaterEqual(len(findings), 15)

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

    def test_exact_run_ids_stay_out_of_human_docs(self) -> None:
        for path in HUMAN_DOCS:
            match = RUN_ID.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(match, f"exact run id in {path.relative_to(ROOT)}")

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

    def test_problem_has_background_to_problem_story(self) -> None:
        text = (ROOT / "docs" / "problem.md").read_text(encoding="utf-8")
        background = text.split("## Background", 1)[1].split("## Problem Statement", 1)[0]
        for heading in (
            "### From Turn-Based Requests to Streaming Interaction",
            "### Why KV Cache Becomes a Capacity Constraint",
            "### Why Request-Level Serving Control Is Insufficient",
        ):
            self.assertIn(heading, background)
        for concept in (
            "request/response",
            "continuous batching",
            "prefix caching",
            "streaming interaction session",
            "periodic interaction session",
            "KV cache",
            "GPU capacity",
            "host-to-device",
            "Recompute the history",
            "Reload on demand",
        ):
            self.assertIn(concept, background)
        self.assertLess(text.index("## Background"), text.index("## Problem Statement"))
        self.assertLess(text.index("## Problem Statement"), text.index("## Workload Model"))

    def test_experiment_record_template_matches_contract(self) -> None:
        contract = load_registry("contracts.json")["experiment_record_v1"]
        template = json.loads(
            (ROOT / "docs" / "agent" / "records" / "template.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(template), set(contract["required_fields"]))

    def test_readme_python_entrypoints_support_help(self) -> None:
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

    def test_readme_has_a_human_documentation_guide(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Documentation Guide", text)
        for owner in ("Problem", "System", "Experiments", "Findings"):
            self.assertIn(f"[`{owner}`]", text)
        self.assertIn("代码已实现不等于机制已验证", text)
        self.assertIn("若陈述看似冲突", text)
        self.assertIn("### Agent Documentation", text)
        self.assertIn("Agent 文档不是第二套项目事实", text)
        for layer in ("Task Router", "system-map", "dynamic-edges", "change-impact"):
            self.assertIn(layer, text)


if __name__ == "__main__":
    unittest.main()
