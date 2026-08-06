# `.context/` — 文档与背景资料

本目录放文档类背景材料：论文摘要、精选笔记、研究点状态说明、幻灯片草稿。
不是 RP1 的事实来源；当前结论以仓库根 `AGENTS.md` 的文档地图，以及 `FINDINGS.md`、`PROBLEM.md` 等为准。

| 路径 | 内容 | 默认是否读入会话 |
| --- | --- | --- |
| `references/` | 当前关注方向的精选笔记（白名单） | 按题目需要读；先看该目录的 `README.md` |
| `papers/` | 跨主题论文与摘要资料池 | 否；只打开明确需要的单篇 |
| `proposal/` | 研究点（RP）状态说明 | 需要时看对照表；不复制实验数字 |
| `slides/` | 表达用草稿；不是证据或记忆 | 仅做幻灯片任务时打开 |
| `archive/` | 已删除历史材料的索引 | 否；不作为当前结论 |

## 与其它目录的分工

- 根 `AGENTS.md` + 结论/设计类 `*.md`：当前结论与实验设计（唯一事实层）；根 `README.md` 只是占位
- `harness/` / `calibration/` / `results/`：可运行代码与运行证据
- `third_party/`：第三方代码（git-subrepo 固定版本副本），不是文档
- `.context/`：阅读材料与表达层

## Git 策略

- 入库：Markdown 摘要、笔记、小体量文本
- 默认不入库（见根 `.gitignore`）：`*.pdf`、`*.pptx`、摘要运行日志
  本地可保留 PDF / PPTX 供阅读；需要时从 arXiv 或原 OneDrive 补回
