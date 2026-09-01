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
    ROOT / "eurosys2027" / "planning" / "introduction-outline.md",
    ROOT / "eurosys2027" / "planning" / "paper-contract.md",
    ROOT / "eurosys2027" / "planning" / "story-logic.md",
)

PAPER_NARRATIVE = (
    ROOT / "eurosys2027" / "sections" / "01-introduction.tex",
    ROOT / "eurosys2027" / "sections" / "02-background-motivation.tex",
    ROOT / "eurosys2027" / "sections" / "03-design.tex",
    ROOT / "eurosys2027" / "sections" / "04-implementation.tex",
    ROOT / "eurosys2027" / "sections" / "08-discussion.tex",
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
            for description, pattern in FORBIDDEN_SCOPE_PATTERNS.items():
                match = pattern.search(text)
                if match:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {description}: {match.group(0)!r}"
                    )
        self.assertEqual(failures, [], "\n".join(failures))

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
        outline = (ROOT / "eurosys2027/planning/introduction-outline.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("当前不设置 provisional default", outline)

    def test_external_reference_directories_declare_their_boundary(self) -> None:
        for relative in ("docs/papers/AGENTS.md", "docs/references/AGENTS.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("不是项目事实层", text, relative)
            self.assertIn("不得", text, relative)


if __name__ == "__main__":
    unittest.main()
