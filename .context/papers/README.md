# Mixed-Topic Paper Digest Library

Updated: 2026-08-06

`.context/papers/` 是**跨主题 paper/digest 资料池**，不是项目状态、related-work shortlist，也不是默认上下文。

这里保留已生成的 digest，包括但不限于：

- 与当前 focus 相关的 interaction model、真双工、实时 serving、长期会话与 KV 管理
- 历史路线留下的 streaming video、proactive interaction、streaming RL、agent RL
- 其它独立主题（如 ViT、flow matching、动作计数）

保留是为了避免重复下载与 digest，**不表示仍属于当前 focus**。

## 使用规则

- 不通过枚举本目录推断当前研究主题
- 不在普通任务中批量读取；只有当前问题明确需要某篇时才打开
- 历史主题 digest 不得自动映射为当前结论或复活旧 proposal
- digest 是阅读辅助；对外引用与精确数字回到 `paper.md` / 本地 `paper.pdf`（若有）与一手来源
- 是否清理与 focus 无关的篇目由用户另行决定

## PDF

`paper.pdf` 默认**不进 Git**（体积大）。本地若缺 PDF，从 arXiv 或原资料源补到对应子目录即可。

## 当前 focus 入口

- 仓库根 `AGENTS.md`（契约与文档地图）
- `.context/references/` 白名单 notes
