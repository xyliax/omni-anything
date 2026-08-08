# Metronome baseline（third_party/metronome pin）

`third_party/metronome/` 是 [19PINE-AI/metronome](https://github.com/19PINE-AI/metronome)（论文 arXiv:2607.02640）的只读参考代码，以 git-subrepo 挂入，pin `2783a90`，更新命令 `git subrepo pull third_party/metronome`。
实验改动一律落在本仓库 `harness/` 或自有 patch，不动 pin 内代码；读写细则的 owner 是 `third_party/AGENTS.md`。
本文内 `experiments/…`、`paper/…`、`worker/…`、`proto/…` 与 `RESULTS_*.md` 等相对路径均相对 `third_party/metronome/`。

## 四个 baseline 角色

| 角色 | 开关 | 内容 |
| --- | --- | --- |
| 主 baseline | `WINDOW=0`（`experiments/run_stream_gateway.sh` 默认） | vanilla vLLM-realtime：每路一个常驻 resumable request，context 无界增长 |
| 第二 baseline | `WINDOW=15`（30 s 窗） | 应用层 request recycling：到窗边界丢弃并重建上下文，代价是 re-encode |
| 竞争对照 | `INENGINE_SWA=<tokens>` | in-engine windowed KV：引擎内滑窗释放 block，有损截断 |
| 正交可叠加 | `ONLINE_ADMIT=1` → `--online-admit --admit-target 0.7` | AIMD 准入：从每帧延迟反馈发现 `N*`（可调度并发数 / schedulable concurrency），与 KV 策略正交 |

竞争对照那一行是本仓库方案的正面对立面：in-engine windowed KV 用有损截断换有界显存；KV conveyor（scheduled tail-KV offloading）走无损路线，用暂存换等效容量。
paper §2 把 swap 分析性排除、断言 resident 是唯一预算兼容选择，其两个假设（全量轮换 baseline、tick 内无空隙）经 FINDINGS E3 证伪，conveyor 的对照位置正在这里。
这套脚手架不覆盖本仓库负载的两条路径：注入（`proto/inference.proto` 有 `SessionInput.text`，gateway 从不填、streaming worker 也不读）与负载下的 cancellation（gRPC `Step` 认 `s.cancel`，但只有 CPU 侧模拟测试）。两者都要在此之上自加。

## 两条必须继承的方法论

fresh-per-point（`experiments/run_fresh_sweep.sh`，每个数据点重新加载并拆除一次 worker）：长活 worker 顺序扫点会产生扫点污染，即前一点的残留状态污染后一点的读数，对策是 fresh process per datapoint。
相位错开（`FD_PHASE_STAGGER=1`，`experiments/sustained_fd.py` 默认开）：让各路音频窗口互不重合；关掉时多路会流相同且相位对齐的音频，prefix cache 把 encode+prefill 去重，容量读数虚高。

## 引用纪律

归因以 paper 为准：`paper/body.tex` 明写 "The failure is a memory cliff, not a compute drift"，机制是亚稳态竞速：池占用线性上升 ρ(t) = ρ0 + N·r·t，当饱和时刻 t_sat 与会话时长同量级时，填充速率 r 的常规波动就把不同运行推到崩溃边界的两侧。
repo 工作笔记 `RESULTS_METRONOME_OVER_VLLM.md` 里的 "attention drift" 是废弃旧说；上游自己的订正把短爆发「N=128 崩溃」这类数字归为扫点污染（FINDINGS E1）。
未复核的墙钟秒数不引用。1601ms 等待帽（worker `--wait-budget-s` = 0.8×tick）读数无法区分成因：compute-bound 与 memory-bound 透过同一个等待帽读作同一个数（FINDINGS B4），不能单独用来定性。

可引用的结论形状（本仓库跨验证只取这一类）：

- vanilla 高并发触发 memory cliff 时计算远未饱和：paper 定性原话 "memory kills sessions whose compute the GPU could easily carry"；崩溃时刻的 GPU util 百分比 paper 与仓库均未给出，任何具体数值不可引。
- KV 受限后 deadline 先于显存绑定：`N*`≈209 是 AIMD 在线实测，小于同一张卡上显存外推的约 500 常驻会话上限（`paper/body.tex`）。
