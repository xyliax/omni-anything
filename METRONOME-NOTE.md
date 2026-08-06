# 这个仓库为什么在这里（本地标记，不属于 Metronome 原仓库）

这是 [github.com/19PINE-AI/metronome](https://github.com/19PINE-AI/metronome)（论文 arXiv:2607.02640，
截至 2026-08 唯一公开的真双工 GPU serving 工作）的**只读参考代码**，用 **git-subrepo**
挂在 `third_party/metronome/`（pin `2783a90`，与原先 submodule pin 相同）。

更新上游：`git subrepo pull third_party/metronome`（不要在该目录里直接改代码再当上游回推）。

## 用途：复用它的对照实验脚手架，不是复用它的 idea

omni-anything 的下一步实验（见 `IDEA-KV-CONVEYOR.md` §五验证计划）
要在真实软件栈上搭 baseline。Metronome 论文对比用的 baseline 谱系正是我们要的：

- **vanilla vLLM-realtime**（vLLM 0.23 resumable request，KV cache 无界常驻）——我们的主 baseline，
  `experiments/run_stream_gateway.sh` 里 `WINDOW=0`
- 应用层 request recycling（`WINDOW=15`）——第二 baseline
- 它自己的 in-engine windowed KV（`INENGINE_SWA`）——对我们是**竞争方案对照组**（有损 vs KV conveyor 无损）
- AIMD 准入（`ONLINE_ADMIT=1`）——正交机制，可叠加对照

整套栈：WebSocket 客户端 → Go tick gateway（`gateway-go/`）→ gRPC 批量 Step（`proto/`）→ vLLM worker（`worker/stream_server.py`）。

## 必须继承的方法论（他们踩坑修正过的）

1. **fresh-per-point 启动**（`experiments/run_fresh_sweep.sh`）：长活 worker 顺序扫点会污染结果
2. **相位错开**（`FD_PHASE_STAGGER=1`）：否则 prefix cache 去重会让容量看起来虚高
3. **tick 校验**（`experiments/sustained_fd.py`）：worker 自报的 gpu_ms 会漏报慢拍

## 对 omni-anything 的关键空白确认

- 工具结果**注入**未实现（协议里有 `SessionInput.text`，但 gateway 不发、0.23 worker 忽略）
- 负载下**cancellation / barge-in** 未测（cancel 测试只是 CPU 侧模拟）
- 这两项正是 omni-anything 负载要素②，需要我们自己加到这套脚手架上

## 引用它的数字时注意

仓库 `RESULTS_METRONOME_OVER_VLLM.md` 有严格性订正：早期「vanilla 配置 N=128 短爆发崩溃」是
扫点污染留下的假象；**真正的瓶颈是分钟级 drift**（fresh 启动 N=96、跑 300 秒，从 3ms 漂到 1601ms）。
omni-anything 文档中引用的「N=128 于约 148 秒触及 memory cliff」说法待复查（见 memory: metronome-repo-baseline-reuse）。

**不要修改 `third_party/metronome/` 里的代码来做我们的实验**——需要改动（如加注入路径）时，fork 或把改动
以 patch / `harness/` 副本形式放在 omni-anything 里管理，保持 subrepo 可随时 `git subrepo pull` 对齐上游。
