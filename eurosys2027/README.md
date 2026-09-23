# EuroSys 2027 Paper Workspace

这是 Pilarius 位于仓库根目录的独立论文写作工作区。它属于论文表达层而不是项目事实源；问题定义、机制语义、实验协议、当前结论和精确证据仍分别由仓库中的 canonical owner 持有。

## Current Scope

- 目标 venue：EuroSys 2027 秋季轮；正文截止 2026-09-24，标题与摘要已于 2026-09-17 注册（[`planning/abstract-submission.txt`](planning/abstract-submission.txt)）。
- 当前阶段：九章正文（Introduction、Background and Motivation、Design、Implementation、Evaluation、Discussion、Related Work、Conclusion，加摘要）已按 [`../docs/PAPER.md`](../docs/PAPER.md) 骨架转写；数字与结论保持空位，等待 formal evidence（开放阻塞项见其[材料依赖表](../docs/PAPER.md#material-dependencies)）。图 1 已定稿并进入 Introduction；图 2 与设计总览图待画（分工见 [`planning/figure-drawing-guide.md`](planning/figure-drawing-guide.md)）。
- 待办的稿件审阅意见：[`planning/manuscript-review-2026-09-15.md`](planning/manuscript-review-2026-09-15.md) 的 R1 到 R8 尚未落实。
- 主稿入口：[`main.tex`](main.tex)；补充材料入口：[`supplement.tex`](supplement.tex)。
- 官方规则摘要：[`planning/submission-checklist.md`](planning/submission-checklist.md)；模板 provenance：[`vendor/acmart/UPSTREAM.md`](vendor/acmart/UPSTREAM.md)。

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
make paper        # 生成 paper.pdf
make supplement   # 生成 supplement.pdf
make check        # 编译并做格式检查
```

每次 `make paper` 成功后，可读的 PDF 复制为本目录下的 `paper.pdf`（补充材料为 `supplement.pdf`），直接打开即可；`build/` 只放 latexmk 的中间文件，不必进入。两个 PDF 已加入 `.gitignore`，不入库。latexmk 按内容校验增量编译：源文件未变时数十毫秒返回，改动一章约一到两秒，全量重编约五秒。`make check` 会做几项基本检查：PDF 是否生成、页面尺寸、文档类的双栏与匿名选项，以及源文件里是否出现被禁止的格式改动；它不能替代提交前人工审计。

## Writing Workflow

叙事骨架、取材关系与写作流程集中在 [`../docs/PAPER.md`](../docs/PAPER.md)：按各章步骤骨架转写正文，沿锚点回 owner 文档取论证与关键句措辞；遇【空位】查材料依赖表。页面预算按 EuroSys 2027 的 12 页技术内容规划，参考量级为 Intro 1.5、Background/Motivation 1.5、Design 3、Implementation 1、Evaluation 3.75、Related Work 0.75、Discussion 与 Conclusion 0.5；超出时删内容不改版式。未获 formal evidence 的数字保持 `TBD`，不能从旧日志复制。

图件流程：作者用 Draw.io 手绘，`figures/` 只放 `.drawio` 源文件和导出的 PDF；画法、caption、待画清单与导出要求在 [`planning/figure-drawing-guide.md`](planning/figure-drawing-guide.md)。

每次使用 AI 辅助写作、分析或画图，都更新 [`planning/ai-use-log.md`](planning/ai-use-log.md)。

## Directory Map

```text
eurosys2027/
├── main.tex                     anonymous review manuscript
├── supplement.tex               optional separate supplement
├── macros.tex                   paper-local notation and draft helpers
├── references.bib               bibliography database
├── paper.pdf                    latest build output (ignored by git)
├── sections/                    one source file per paper section
├── figures/                     Draw.io sources and exported PDFs
├── planning/                    venue checklists, related-work matrix, figure guide, review notes, AI-use log
├── scripts/                     non-destructive format checks
├── build/                       latexmk intermediates (ignored by git)
└── vendor/acmart/               pinned ACM template and provenance
```

## Important Boundary

本目录可以包含措辞、标题、图设计和未完成的论证，但不能成为数字、状态或机制语义的新 owner。草稿与 owner 冲突时，以 owner 为准；写作过程中发现的新事实要先通过项目的 evidence transaction 接受，再回填正文。
