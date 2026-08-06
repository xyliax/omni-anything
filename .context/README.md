# `.context/` — 文档与背景资料

本目录放**文档性质**的背景材料：论文 digest、curated notes、薄 proposal、slides 草稿。  
**不是** RP1 的事实源；现行结论以仓库根 `AGENTS.md` 文档地图及 `FINDINGS.md` / `PROBLEM.md` 等为准。

| 路径 | 内容 | 默认是否读入 session |
| --- | --- | --- |
| `references/` | 当前 focus 的 curated notes（白名单） | 按题目需要读；先看其 `README.md` |
| `papers/` | 跨主题 paper/digest 资料池 | **否**；仅打开明确需要的单篇 |
| `proposal/` | RP 状态薄 dossier | 需要时看表；不复制实验数字 |
| `slides/` | 表达草稿；**不是**证据或记忆 | 仅做 slide 任务时打开 |
| `archive/` | 已删除历史材料的 tombstone 索引 | **否**；不作为现行结论 |

## 与其它目录的分工

- **根 `AGENTS.md` + 结论/设计 `*.md`**：现行结论与实验设计（唯一事实层）；`README.md` 仅为占位
- **`harness/` / `calibration/` / `results/`**：可运行代码与证据
- **`third_party/`**：第三方**代码**（git-subrepo），不是文档
- **`.context/`**：阅读材料与表达层

## Git 策略

- 入库：Markdown digest、notes、小体量文本
- 默认不入库（见根 `.gitignore`）：`*.pdf`、`*.pptx`、digest 运行日志  
  本地可保留 PDF/PPTX 供阅读；需要时从 arXiv / 原 OneDrive 补回
