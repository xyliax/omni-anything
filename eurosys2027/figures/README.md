# Figure Assets

> 两图已依据 [机制理解审计](../planning/figure-design-understanding.md) 重画，当前为待作者反馈的预览版；内部状态一致性检查不等于实测或最终论文审定。

本目录保存可复现 SVG、vector PDF 和 PNG 预览。论文用 PDF，PNG 供审阅。当前两图沿用四会话历史示例；Design 采用作者指定的 **1 s 周期、4 slot、4 会话**，Intro 单独展开一个会话的恢复时序对照，尚未替换正文 figure inclusion。

| Figure | Purpose | Specification | Files |
| --- | --- | --- | --- |
| 1 | 动机对照：历史增长、全驻留容量压力、按需恢复与提前恢复的时间差 | [Intro spec](../planning/figure-1-motivated-example.md) | `figure1-motivated-example.{svg,pdf,png}` |
| 2 | 纵向时间剖面：逐块 GPU/Host 状态、容量推迟与重试、共享链路及恢复后等待 | [Design spec](../planning/figure-2-design-overview.md) | `figure2-design-overview.{svg,pdf,png}` |

## Reproduction

根目录运行 `python eurosys2027/scripts/render-kv-figures.py`。Python 3 生成 SVG；`rsvg-convert` 在 PATH 时导出 PDF/PNG。图中参数是示意设定，脚本不读取或缩放实验 trace。

## Rules

- 先改独立 spec / 共享绘图参数，再改生成器，重新导出两图。手改 SVG 会被覆盖。
- 实验设置不等于机制图设置；本例的数字不是实测、模拟器结果或性能预测。
- 真实 trace 仅约束定性关系，原诊断分析记录保留其历史意义。
- 7 in 宽度下字号 ≥10 pt；灰度使用纹理、形状和短标签。
- 不含作者、单位、私有路径、仓库 URL 或模型/设备绑定。
- 实验结果图另须 formal `EVIDENCE-*`；不得把本机制示例当作结果证据。
- 历史 `planning/figure-2-evidence-map.md` 对应旧 TikZ 图，当前语义映射由各 spec 持有。
