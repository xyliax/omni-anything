# Figure Assets

本目录保存论文图的可复现源文件和最终导出文件。当前已创建机制总览图的 TikZ 源文件与 PDF 导出；其余图仍按 `planning/figures.md` 的状态推进。

## Rules

- 每张图先在 `planning/figures.md` 声明它回答的 reviewer question 和所需 evidence。
- 实验图的数据入口必须解析到 formal `EVIDENCE-*`，不能手抄诊断数字。
- 源数据与 trace parser 留在项目事实/证据层；本目录只保存绘图 specification、可复现调用和导出结果。
- EuroSys 2027 官方要求图在灰度打印、无放大时仍可读；不要只用颜色编码系列。
- 图中文字不得低于 10pt；提交前在 100% 页面尺寸和灰度打印预览中检查。
- review 稿不得包含作者、单位、可识别域名、用户名、绝对路径或仓库 URL。

## Current Assets

- `conveyor-mechanism-overview.tex`: Figure 2 的 TikZ source，展示 predictable next use、release offsets、idle-session partial eviction、host coverage、prefetch 和 safe fallback。
- `conveyor-mechanism-overview.pdf`: 从上述 source 导出的 vector asset；不包含当前模型、硬件、runner、baseline 或实验参数。
