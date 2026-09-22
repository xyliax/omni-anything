# Figure Assets

本目录只放图的源文件与供 LaTeX 引用的导出件。画法、caption 与图件分工见 [图件手绘指南](../planning/figure-drawing-guide.md)；图号与各图在论文中的位置以 [docs/PAPER.md 图件计划](../../docs/PAPER.md#figure-plan) 为准。

| 文件 | 内容 | 状态 |
| --- | --- | --- |
| `figure.drawio` | 图 1 源文件（Draw.io，含 `intro` 与 `caption` 两页），作者手绘 | 已画完，细节仍在调整；建议另存为 `figure-intro.drawio` 使基名与导出件一致 |
| `figure-intro.pdf` | 图 1 导出件，`sections/01-introduction.tex` 以 `figure*` 双栏引用 | 当前为由 SVG 经 Chrome 转出的临时版本，作者从 Draw.io 直接导出的 PDF 到位后覆盖 |

图 2（相位与恢复时机）与设计总览图尚未开始，源文件按同样方式命名：`figure-<用途>.drawio` 与 `figure-<用途>.pdf`。

## 导出

从 Draw.io 直接 Export as PDF：选中整页、勾选 crop，字体嵌入由 Draw.io 桌面版自动完成。不要经 SVG 中转：Draw.io 导出的 SVG 把文字放在 `foreignObject` 里并附位图兜底，rsvg、cairosvg 一类工具只会取位图，文字就变成图片。若只有 SVG，可用无头 Chrome 打印成 PDF（`--headless=new --print-to-pdf`），foreignObject 能正常渲染。导出后用 `pdffonts` 确认字体已嵌入、名字是所选字体而不是 Helvetica 回退。

## 规则

- 图内字体与全文图件统一，目前为 Inter；图内标签 8 px 以上（双栏放大 1.25 倍后约 10 pt），图例不低于 7 px。
- 图内不出现具体数值，时间轴用符号刻度，容量线只写名称。
- 颜色语义见指南：蓝色系表示输入侧（音频流、prefill、input tokens），橙色系表示输出侧（decode、语音输出、output tokens），蓝灰表示历史 KV，红色全图只用于容量触顶一处。
- 不含作者、单位、私有路径、仓库 URL 或模型与设备名。
- 先改指南再改图；caption 的术语与 [docs/problem.md 术语表](../../docs/problem.md#terminology) 一致。
