# EuroSys 2027 Paper Workspace

这是 Omni-Anything 位于仓库根目录的独立论文写作工作区。它属于论文表达层而不是项目事实源；问题定义、机制语义、实验协议、当前结论和精确证据仍分别由仓库中的 canonical owner 持有。

## Current Scope

- 目标 venue：EuroSys 2027。
- 当前阶段：写作框架、模板和合规检查已经建立；论文正文、数字和结论尚未填充。
- 主稿入口：[`main.tex`](main.tex)。
- 补充材料入口：[`supplement.tex`](supplement.tex)。
- 官方规则摘要：[`planning/submission-checklist.md`](planning/submission-checklist.md)。
- 当前进度：[`planning/progress.md`](planning/progress.md)。
- 模板 provenance：[`vendor/acmart/UPSTREAM.md`](vendor/acmart/UPSTREAM.md)。

## Authoritative Project Sources

写作前按事实域查阅以下 owner，不从本目录反向覆盖它们：

- 研究问题、范围和术语：[`../docs/problem.md`](../docs/problem.md)
- 机制、状态机和端到端流程：[`../docs/system.md`](../docs/system.md)
- 实验配置、指标和协议：[`../docs/experiments.md`](../docs/experiments.md)
- 当前结论、数字与限制：[`../docs/findings.md`](../docs/findings.md)
- exact evidence 与 provenance：[`../docs/agent/evidence.json`](../docs/agent/evidence.json)

## Build

需要本机安装 `latexmk`、`pdflatex` 和 BibTeX。仓库已经 vendor 一份锁定的 ACM production template，因此不依赖系统中碰巧安装的 `acmart` 版本。

```bash
cd eurosys2027
make paper
make supplement
make check
```

输出位于 `build/`。`make check` 会做几项基本检查：PDF 是否生成、页面尺寸、文档类的双栏与匿名选项，以及源文件里是否出现被禁止的格式改动；它不能替代提交前人工审计。

## Writing Workflow

叙事骨架、取材关系与写作流程集中在 [`../docs/PAPER.md`](../docs/PAPER.md)：按各章步骤骨架转写正文，沿锚点回 owner 文档取论证与关键句措辞；遇【空位】查材料依赖表。本目录的 planning 文件承担 venue 规则与流程检查（submission/reviewer checklist、page budget、related-work matrix、ai-use-log）；叙事类 planning 文件已于 2026-09-13 清理为骨架，随正文重建。未获 formal evidence 的数字保持 `TBD`，不能从旧日志复制；每次使用 AI 辅助写作或分析，都更新 [`planning/ai-use-log.md`](planning/ai-use-log.md)。

## Directory Map

```text
eurosys2027/
├── main.tex                     anonymous review manuscript
├── supplement.tex               optional separate supplement
├── macros.tex                   paper-local notation and draft helpers
├── references.bib               bibliography database
├── sections/                    one source file per paper section
├── figures/                     figure assets and figure contracts
├── planning/                    story, evidence, schedule, and checklists
├── scripts/                     non-destructive format checks
└── vendor/acmart/               pinned ACM template and provenance
```

## Important Boundary

本目录可以包含措辞、标题、图设计和未完成的论证，但不能成为数字、状态或机制语义的新 owner。草稿与 owner 冲突时，以 owner 为准；写作过程中发现的新事实要先通过项目的 evidence transaction 接受，再回填正文。
