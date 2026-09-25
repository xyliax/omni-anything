"""Regression guards for the separation between paper scope and current evidence.

The repository deliberately keeps volatile model, hardware, modality, output-path,
and environment details in the experiment/evidence owners.  These tests are small
semantic guards rather than a snapshot of prose: a future refactor must fail if it
silently promotes the current measured path to the project or paper scope.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# These files are the scope-bearing entry points.  docs/experiments.md,
# docs/agent/evidence.json, results/, and external reference directories are
# intentionally excluded because they are allowed to record volatile details.
SCOPE_DOCS = (
    ROOT / "AGENTS.md",
    ROOT / "README.md",
    ROOT / "docs" / "problem.md",
    ROOT / "docs" / "system.md",
    ROOT / "docs" / "findings.md",
    ROOT / "docs" / "PAPER.md",
    ROOT / "eurosys2027" / "AGENTS.md",
)

PAPER_NARRATIVE = (
    ROOT / "eurosys2027" / "sections" / "00-abstract.tex",
    ROOT / "eurosys2027" / "sections" / "01-introduction.tex",
    ROOT / "eurosys2027" / "sections" / "02-background-motivation.tex",
    ROOT / "eurosys2027" / "sections" / "03-design.tex",
    ROOT / "eurosys2027" / "sections" / "04-implementation.tex",
    ROOT / "eurosys2027" / "sections" / "05-evaluation.tex",
    ROOT / "eurosys2027" / "sections" / "06-discussion.tex",
    ROOT / "eurosys2027" / "sections" / "07-related-work.tex",
    ROOT / "eurosys2027" / "sections" / "08-conclusion.tex",
)

# A model or device name can remain in the experiment owner or an external
# citation.  It cannot appear in a scope-bearing document as an unqualified
# definition of this project.
FORBIDDEN_SCOPE_PATTERNS = {
    "single-device deployment": re.compile(
        r"单张\s*GPU|single[- ]GPU|one\s+GPU|sharing\s+one\s+GPU", re.IGNORECASE
    ),
    "current model/output stack": re.compile(
        r"Qwen2\.5-Omni|Thinker(?:-only)?|Talker|Code2Wav|audio[- ]input|RTX\s*3090",
        re.IGNORECASE,
    ),
    "mutable environment instance": re.compile(
        r"cuda13_vllm023|\.venv-vllm023|duration\s+120|120\s*s", re.IGNORECASE
    ),
}


# The root policy permits sourced external model examples. Keep the exception
# local to the declared analysis, require its citations and estimate qualifier,
# and retain the original checks for all other terms and locations.
EXTERNAL_ANALYSIS_BEGIN = "% external-reference-begin: cross-model-cycle-usage"
EXTERNAL_ANALYSIS_END = "% external-reference-end: cross-model-cycle-usage"
EXTERNAL_ANALYSIS_QUALIFIER = "These are illustrative resource estimates."
EXTERNAL_ANALYSIS_TERMS = {"Qwen2.5-Omni", "Thinker"}
PROJECT_MODEL_CLAIM = re.compile(
    r"(?:\bwe\b|\bour (?:system|workloads?|evaluation|paper|scope)\b)"
    r"[^\n]{0,120}\b(?:Qwen2\.5-Omni|Thinker|Talker|Code2Wav)\b",
    re.IGNORECASE,
)


def paper_scope_violations(relative: str, text: str) -> list[str]:
    allowed_span = None
    failures = []
    if EXTERNAL_ANALYSIS_BEGIN in text or EXTERNAL_ANALYSIS_END in text:
        start, end = text.find(EXTERNAL_ANALYSIS_BEGIN), text.find(EXTERNAL_ANALYSIS_END)
        valid_location = relative == "eurosys2027/sections/02-background-motivation.tex"
        valid_markers = (text.count(EXTERNAL_ANALYSIS_BEGIN) == 1
                         and text.count(EXTERNAL_ANALYSIS_END) == 1 and 0 <= start < end)
        if valid_location and valid_markers:
            block = text[start:end]
            citations = set(re.findall(r"\\cite\{([^}]+)\}", block))
            keys = {key for group in citations for key in group.split(",")}
            required_sources = {"qwen2025omni3bconfig", "qwen2025omni7bconfig"}
            if EXTERNAL_ANALYSIS_QUALIFIER in block and required_sources <= keys:
                allowed_span = (start, end)
                if PROJECT_MODEL_CLAIM.search(block):
                    failures.append("external model analysis promotes an example to a project claim")
        if allowed_span is None:
            failures.append("external model analysis lacks its location, boundaries, qualification, or sources")

    for description, pattern in FORBIDDEN_SCOPE_PATTERNS.items():
        for match in pattern.finditer(text):
            if (allowed_span is not None
                    and allowed_span[0] <= match.start() < allowed_span[1]
                    and description == "current model/output stack"
                    and match.group(0) in EXTERNAL_ANALYSIS_TERMS):
                continue
            failures.append(f"{description}: {match.group(0)!r}")
    return failures


class NarrativeScopeTests(unittest.TestCase):
    def test_scope_documents_do_not_promote_the_current_measured_path(self) -> None:
        failures: list[str] = []
        for path in SCOPE_DOCS:
            text = path.read_text(encoding="utf-8")
            for description, pattern in FORBIDDEN_SCOPE_PATTERNS.items():
                match = pattern.search(text)
                if match:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {description}: {match.group(0)!r}"
                    )
        self.assertEqual(failures, [], "\n".join(failures))

    def test_paper_narrative_stays_modality_and_hardware_neutral(self) -> None:
        failures: list[str] = []
        for path in PAPER_NARRATIVE:
            text = path.read_text(encoding="utf-8")
            relative = str(path.relative_to(ROOT))
            failures.extend(f"{relative}: {issue}"
                            for issue in paper_scope_violations(relative, text))
        self.assertEqual(failures, [], "\n".join(failures))

    def test_external_model_example_requires_sources_and_qualification(self) -> None:
        relative = "eurosys2027/sections/02-background-motivation.tex"
        example = "\n".join((EXTERNAL_ANALYSIS_BEGIN, EXTERNAL_ANALYSIS_QUALIFIER,
                              r"Qwen2.5-Omni Thinker \cite{qwen2025omni3bconfig,qwen2025omni7bconfig}.",
                              EXTERNAL_ANALYSIS_END))
        self.assertEqual(paper_scope_violations(relative, example), [])
        for missing in (EXTERNAL_ANALYSIS_QUALIFIER, "qwen2025omni7bconfig", EXTERNAL_ANALYSIS_END):
            with self.subTest(missing=missing):
                self.assertTrue(paper_scope_violations(relative, example.replace(missing, "")))

    def test_external_example_does_not_exempt_other_scope_claims(self) -> None:
        relative = "eurosys2027/sections/02-background-motivation.tex"
        example = "\n".join((EXTERNAL_ANALYSIS_BEGIN, EXTERNAL_ANALYSIS_QUALIFIER,
                              r"Qwen2.5-Omni \cite{qwen2025omni3bconfig,qwen2025omni7bconfig}.",
                              EXTERNAL_ANALYSIS_END))
        self.assertTrue(paper_scope_violations(relative, example + "\nOur system uses Qwen2.5-Omni."))
        for claim in ("single-GPU", "Code2Wav", "RTX 3090", "Our system only supports Qwen2.5-Omni."):
            with self.subTest(claim=claim):
                self.assertTrue(paper_scope_violations(
                    relative, example.replace(EXTERNAL_ANALYSIS_QUALIFIER,
                                              EXTERNAL_ANALYSIS_QUALIFIER + " " + claim)))
        self.assertTrue(paper_scope_violations("eurosys2027/sections/01-introduction.tex", example))

    def test_scope_policy_is_explicit_at_the_agent_entry_points(self) -> None:
        root_agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        eurosys_agents = (ROOT / "eurosys2027" / "AGENTS.md").read_text(encoding="utf-8")
        for text, owner in (
            (root_agents, "AGENTS.md"),
            (readme, "README.md"),
            (eurosys_agents, "eurosys2027/AGENTS.md"),
        ):
            self.assertIn("不自动成为最终论文", text, owner)
            self.assertIn("experiment", text.lower(), owner)
        # The running-example rule moved from the retired planning shells into
        # the paper outline; it must survive there.
        outline = (ROOT / "docs/PAPER.md").read_text(encoding="utf-8")
        self.assertIn("具体例子不限定最终实验范围", outline)

    def test_external_reference_directories_declare_their_boundary(self) -> None:
        for relative in ("docs/papers/AGENTS.md", "docs/references/AGENTS.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("不是项目事实层", text, relative)
            self.assertIn("不得", text, relative)


if __name__ == "__main__":
    unittest.main()
