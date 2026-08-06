# Current Reference Notes

Updated: 2026-08-06

本目录只保存与当前 focus 直接相关、可自包含阅读的 curated notes。  
当前 focus：TML interaction-model 场景（前台 omni 双工持续交互，后台 agent 异步工作并写回共享时间线）。

## 白名单

| 文件 | 作用 | 使用边界 |
| --- | --- | --- |
| `thinking-machines-interaction-model.md` | TML 公开案例、交互语义、前后台关系 | 场景定义入口；不反推未公开训练/serving |
| `true-duplex-model-product-serving-landscape-2026-08.md` | 真双工模型、产品、公开 serving 规格 | related-work 入口；使用前核查日期 |

RP1 的事实、推导、实验与 paper 计划**不**复制到这里，统一在仓库根文档与 `results/`。

## 防污染规则

- 旧 streaming RL / rollout / Jiuwen 落地叙事不得从 slides 或 paper 库恢复成当前结论
- `../papers/` 是跨主题 digest 库，不是当前 focus，不默认批量读入
- 新建 note 前确认直接服务当前场景；候选 brainstorm 不落盘成“事实笔记”
- 新 note 写清来源、核查日期、事实与推断边界
- `../slides/` 不是 reference source
