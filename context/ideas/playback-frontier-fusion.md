# Prefill–decode 融合 / playback frontier（设想）

未进入事实层；非现行主线（现行主线是按时间表调度的尾部 KV conveyor）。快照日期：2026-08-07。

## 方向

同一交互 tick 内，prefill 新输入与 decode 输出可能重复扫描同一份会话历史。
以 playback frontier——模型自身输出中已实际播放给用户的位置，作为下一步 attention 的因果可见边界（区别于已生成但未播出的 token）——定义时间因果 mask，将共享历史快照的两条路径合并执行，并用 fork / commit 处理打断与提交。

## 未决

- 与现有 vLLM / omni 引擎路径的真实重复扫描成本。已知参照：`context/papers/` 内 POD-Attention（prefill–decode 全重叠）与 Sarathi-Serve（chunked prefill）；E1 实测 tick 内 prefill 完成即入 decode 批、无跨会话屏障（FINDINGS C1）
- 与 KV conveyor staging 生命周期如何共存
- 最小可测实验是什么

## 表述

在完成最小测量前，不声称新颖性或性能收益。
