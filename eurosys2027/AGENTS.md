# 论文写作规则

本目录是表达层，不是项目事实 owner。按任务读取对应正文和 owner，不默认加载整个 docs、外部论文或历史评审。

| 内容 | Owner |
| --- | --- |
| 问题、范围、术语 | `docs/problem.md` |
| 设计、状态与未决算法 | `docs/system.md` |
| 配置、指标、实验协议 | `docs/experiments.md` |
| 已登记证据与限制 | `docs/findings.md`；精确来源按 ID 查 `docs/agent/evidence.json` |
| 章节、图件状态与写作待办 | `docs/PAPER.md` |

- 作者最新说明优先于旧文档。冲突先澄清并更新对应 owner；不能用旧实现限制未定的论文设计，也不能将作者的设计说明当成实现证明。
- prototype、measured path、模型、模态、输出、硬件及拓扑不自动成为最终论文范围；experiment 矩阵未冻结时保持变量与证据边界。外部模型可作有来源的具体例子，不据例子冻结 scope。
- 假设、设计要求、实现与结果分开。仅将根 `AGENTS.md` 定义的 research mechanism 写成贡献；数字注明来源性质与配置，项目测量通过 `EVIDENCE-*` 追溯，外部推导引用原始参数。
- 用简明专业的正文解释行为、原因和证据。作者备忘、审核规则、旧命名和实现待办不进入正文。术语以 `docs/problem.md#terminology` 为准，tick 表示周期起点，deadline 表示期望完成时刻；slot 与 manager 不自动构成贡献。
- review 稿保持双盲。不改模板、字号、行距、栏距或 caption 字号压缩篇幅。
- TeX 一句一行，空行表示段落。先对齐问题、设计与评估，再扩写正文。
- 作者维护 Draw.io 图件；agent 可读取核对，修改须遵循作者授权。`figures/` 只放 `.drawio` 和导出 PDF，不另建画图指南。导出使用 `drawio -x -f pdf --crop -p <页码> -o <out.pdf> figures/figure.drawio` 后执行 `pdfcrop --margins 1 <out.pdf> <out.pdf>`，用 `pdffonts` 检查字体嵌入。
- 实质 AI 使用记入 `planning/ai-use-log.md`，只记录日期、工具、工作内容和作者复核责任。该记录供披露，不是设计记忆或当前待办；不得默认整份读取。

从本目录运行 `make check`，再按根 `AGENTS.md` 的改动类型运行 pytest。venue 规则和模板来源分别维护于 `planning/submission-checklist.md` 与 `vendor/acmart/UPSTREAM.md`；变更时同步核对。
