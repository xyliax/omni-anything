# RP2：静态图特化

Updated: 2026-08-06

Status: **Preliminary；目前没有细想，尚未形成可提交的研究点。**

## 暂定方向

利用双工前台中重复、可预测的执行形状，探索静态图或 AOT 执行特化，以减少动态规划、kernel launch、内存准备或 shape handling 的固定开销。

这只是一条工作假设。当前尚未确定：

- 应特化的准确对象是 micro-prefill、完整前台拍、混合 batch signature，还是其他执行单元；
- 哪些形状在真实 TML interaction-model workload 中足够稳定且高频；
- 最强现有引擎 baseline 已覆盖到哪里；
- 相对现有 CUDA Graph、piecewise graph、shape bucket 或编译路径的真实 delta；
- 预期收益、适用硬件、实现复杂度和验证实验。

## 表述纪律

- 不沿用旧 dossier 中“机制已成立”或“现有引擎覆盖不到”的结论。
- 在完成 workload 定义、prior-art refresh 和最小测量前，不声称 novelty 或性能收益。
- 与 RP1 的关系尚未定义；不得为了凑三点而强行绑定。

