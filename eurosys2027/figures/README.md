# Figure Assets

> 图 1 与设计总览图已进入 v4 手绘阶段：**`.drawio` 为源文件（作者手绘，待创建）**，本目录现存的 `{svg,pdf,png}` 是 v3 matplotlib 预览的冻结参考，`.drawio` 版落地后替换删除。设计契约见各 spec；内部一致性不等于实测或最终论文审定。

| Figure | Purpose | Specification | Files |
| --- | --- | --- | --- |
| 1 | 动机：对齐轮次的多会话周期负载下，聚合 KV 穿越容量而共享空闲窗逐周期重现；单会话恢复时序对比（reactive vs cyclic） | [Intro spec](../planning/figure-1-motivated-example.md) | `figure1-motivated-example.drawio`（待创建）；`{svg,pdf,png}` 为冻结预览 |
| 2 | 设计总览：连续 residency swimlane、均匀相位网格、容量门控因果链（带圈序号）、共享链路窗口、pool 对齐基线对照 | [Design spec](../planning/figure-2-design-overview.md) | `figure2-design-overview.drawio`（待创建）；`{svg,pdf,png}` 为冻结预览 |

## Production

作者用 Draw.io 手绘 `.drawio`（一页一图，元素分组命名），导出 vector PDF（crop）供 LaTeX、PNG 供审阅，与 spec 的参数表/事件模型逐项对照。agent 可读改 XML、渲染检查并按 spec 审计。旧 matplotlib 生成器已随 v4 退役；其事件常数保留在两份 spec 的参数表中。

## Rules

- 先改 spec，再改图；caption 与语义不得偏离 owner 文档。
- 机制图数字是示意设定，不是实测、模拟器结果或性能预测；实验结果图另须 formal `EVIDENCE-*`。
- 7 in 宽度下注释 8 pt、轴/lane 标签 9 pt；图内文字预算见各 spec；调色板与灰度规则见各 spec 的 visual vocabulary（深蓝 `#28769B`、浅蓝 `#EAF2F7`、橙 `#B87519`、墨 `#263642`、灰 `#9CA9B2`）。
- 不含作者、单位、私有路径、仓库 URL 或模型/设备绑定。
- 历史 `planning/figure-2-evidence-map.md` 对应旧 TikZ 图，当前语义映射由各 spec 持有。
