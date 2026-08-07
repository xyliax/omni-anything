# 静态执行特化（设想）

未进入事实层；非现行主线（现行主线是按时间表调度的尾部 KV conveyor）。快照日期：2026-08-07。

## 方向

利用双工前台中重复、可预测的执行形状，探索静态计算图或 AOT 执行特化（引擎侧词汇：shape specialization、piecewise compilation、CUDA graph capture），减少动态规划、kernel launch、内存准备与 shape 处理的固定开销。

## 未决

- 特化对象是 micro-prefill、完整前台一 tick、混合 batch signature，还是其他执行单元
- 哪些形状在目标负载中足够稳定且高频（论文负载已冻结为文本代理双工协议，见 `docs/experiments.md`；TML 交互模型负载为参考形态）
- 现有引擎（CUDA graph capture、piecewise compilation、shape bucketing、编译路径）已覆盖到哪里
- 预期收益、适用硬件、实现复杂度和验证实验

## 表述

在完成负载定义、已有工作刷新和最小测量前，不声称新颖性或性能收益。与 KV conveyor 主线的关系未定义。
