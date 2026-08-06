# 当前参考笔记

更新：2026-08-06

本目录只保存与当前关注方向直接相关、可独立阅读的精选笔记。
当前关注：Thinking Machines Lab（TML）interaction model 场景——前台 omni 双工持续交互，后台 agent 异步工作并写回共享时间线。

## 白名单

| 文件 | 作用 | 使用边界 |
| --- | --- | --- |
| `thinking-machines-interaction-model.md` | TML 公开案例、交互语义、前后台关系 | 场景定义入口；不反推未公开的训练或 serving 细节 |
| `true-duplex-model-product-serving-landscape-2026-08.md` | 真双工模型、产品、公开 serving 规格 | 相关工作入口；使用前核查日期 |

RP1 的事实、推导、实验与论文计划不复制到这里，统一在仓库根文档与 `results/`。

## 防污染规则

- 旧的 streaming RL / rollout / Jiuwen 落地叙事，不得从幻灯片或论文库恢复成当前结论
- `../papers/` 是跨主题摘要库，不是当前关注，不默认批量读入
- 新建笔记前确认直接服务当前场景；候选 brainstorm 不落盘成「事实笔记」
- 新笔记写清来源、核查日期、事实与推断边界
- `../slides/` 不是参考来源
