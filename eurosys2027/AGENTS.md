# EuroSys 2027 Writing Workspace

本目录专用于 EuroSys 2027 论文写作，是仓库根目录下的独立写作投影，不是项目事实层。

## Read Before Writing

按内容读取对应 owner：

| 写作内容 | 必读 owner |
| --- | --- |
| 问题、范围、术语 | `docs/problem.md` |
| 机制、状态机、设计不变量 | `docs/system.md` |
| evaluated systems、指标、实验协议 | `docs/experiments.md` |
| 数字、结论、限制和证据成熟度 | `docs/findings.md` + `docs/agent/evidence.json` |

## Writing Rules

- 草稿不得覆盖 owner；发生冲突时先更新或澄清 owner，再改论文。
- 只把根 `AGENTS.md` 定义的 research mechanism 写成贡献；system requirement 和 implementation choice 分别进入设计约束或实现章节。
- 论文核心术语必须来自 `docs/problem.md#terminology`。若需新术语，先完成 canonical glossary transaction。
- 任何数字都必须标明实测、模拟器标定、推导或冻结先验，并绑定配置域和 `EVIDENCE-*`。
- diagnostic、legacy-unreconstructable 和 source-audit 证据不得写成 formal performance result。
- review 稿始终保持 double-blind：不写作者、单位、项目主页、可识别仓库链接、acknowledgment 或自我指涉措辞。
- 不修改 `acmart.cls`、页面几何、字号、行距、栏距或 caption 字号来挤页。
- 写作顺序必须遵守 `planning/section-contracts.md`：先 paper contract 与 story logic，再搭 Intro/Background/Design/Implementation 骨架，同时规划 Evaluation，最后才逐段扩写。
- 在 Intro challenge、Design module 和 Evaluation question 尚未一一对应前，不得从代码路径或 patch 细节出发扩写正文。
- 使用 AI 的每次实质性动作更新 `planning/ai-use-log.md`；最终 disclosure 由作者根据 EuroSys/ACM 当时规则确认。
- 新的论文正文只写入 `sections/`、`main.tex`、`supplement.tex`、`references.bib`、`figures/` 或 `planning/`。

## Validation

从本目录运行：

```bash
make check
```

从仓库根运行：

```bash
python -m pytest
```

模板或 venue 规则更新时，必须同步更新 `vendor/acmart/UPSTREAM.md`、`planning/submission-checklist.md` 和 `planning/progress.md`。
