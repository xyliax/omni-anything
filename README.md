# omni-anything

单张 GPU 上同时服务两类负载的 serving 研究。
一类是全双工 (full-duplex) 语音前台：按硬 tick 推进（固定周期 T 的硬 deadline 帧），每拍做一次增量 prefill 加几步 decode，交付晚了就是音频断裂，属于正确性事故。
另一类是后台 agent 的结果注入 (injection)：一次工具调用回来几百到几千 token，可以晚几拍落地（弹性注入，delay-tolerant），但必须无损进入同一条会话的上下文。

两者叠在一起，稀缺的资源不是算力而是容量。
每路会话的 KV cache 每一拍都要参与 attention，常驻显存只增不减，会话之间又没有 request 边界可以把历史换出，于是 KV pool 先饱和，算力却大量闲置：池满时引擎每拍的忙时只有 38–55%（`docs/FINDINGS.md` D1，公式与实测互证）。
这种负载全文称 capacity-bound：受限的是 KV pool 的字节容量，而不是 bandwidth-bound 意义上的显存带宽。

候选方案是 KV conveyor：按 tick 时间表把每路会话的尾部 KV 母本 (canonical copy) 从 host DRAM 经 DMA 预取入 HBM 暂存、算完即释放（scheduled tail-KV offloading，谱系为 FlexGen / InfiniGen / vLLM offloading connector / LMCache），等效 KV 容量 = resident M + staging P。

## 实验基座

E 系列真机实验跑在 vLLM 0.23 + Qwen2.5-Omni-7B + RTX 3090 (24GB)，tick = 2s，N = 8 concurrent sessions。
论文主配置是另一套冻结协议（模型、tick 结构、注入负载先验都不同），定义在 `docs/EXPERIMENTS.md`；两套配置的数字不可互相引用。

## 目录

```text
omni-anything/
├── AGENTS.md      agent 工作契约与文档地图
├── docs/          事实层：结论、问题、方案、实验协议
│   ├── PROBLEM.md              问题定义：负载三要素、瓶颈出现顺序、领域空白
│   ├── FINDINGS.md             E 系列发现清单，条目编号 A1..G 是全仓库的证据引用锚点
│   ├── DESIGN.md               KV conveyor 的公式、编排、相关工作对比与边界
│   ├── EXPERIMENTS.md          主张到实验的矩阵、平台决策、负载冻结协议
│   ├── EXPERIMENT-LOG.md       逐次运行的执行记录
│   └── METRONOME.md            Metronome baseline：pin、用法、数字订正
├── harness/       E 系列真机实验组件：driver 脚本、引擎内观测注入、可视化（入口 USAGE.md）
├── calibration/   E0 DMA 微基准：H2D 搬运与 decode 并发时的 step 时间膨胀 κ 与有效带宽
├── results/       运行证据：paper/ 原始日志、figures/ 论文图、viz/ Perfetto trace
├── third_party/   git-subrepo pin（vllm-omni、metronome、moshi、DuplexOmni、personaplex），只读
└── .context/      思考原料，不构成项目事实：references / papers / ideas / slides
```

## 复现

`harness/USAGE.md` 是操作入口：起一次实验敲哪条命令、跑完 30 秒内怎么判读终态、以及哪些读数会骗人。
最容易被骗的一条：客户端 miss = 0% 在会话已经崩溃时照样成立（silent failure，cadence 指标全绿而内容早已过时，`docs/FINDINGS.md` B1），健康判据要看 `kv.log` 的 starvation 信号。
