# third_party/

第三方参考代码树。机制是 **git-subrepo**（不是 submodule）。普通 `git clone` 即完整树，无需 `--recursive`。

## 读写边界

| 动作 | 允许 | 落点 |
| --- | --- | --- |
| 阅读对照 | 是 | 本目录下各 pin |
| 改实验/插桩/方案代码 | 是 | 仓库 `harness/`、`docs/` 文档、自有 fork/patch |
| 直接改 `third_party/*` 当实验代码 | **否** | — |
| 下载模型权重、大数据集进本目录 | **否** | — |
| 手改各 pin 内 `.gitrepo` | **否**（git-subrepo 维护） | — |

实验路径上真正被 harness 引用的只有 `metronome/`。其余 pin 默认**按题打开**，不批量读入 session。

## 当前 pins

权威 pin 以各目录 `.gitrepo` 的 `commit` 为准；下表是用途索引。

| 路径 | 上游 | 何时打开 |
| --- | --- | --- |
| `metronome/` | https://github.com/19PINE-AI/metronome | baseline harness、gateway/worker 对照；用法纪律在 `docs/metronome.md` |
| `DuplexOmni/` | https://github.com/MuyeHuang/DuplexOmni | 前台双工 + 后台异步写回；480ms 拍 / 注入通道 |
| `moshi/` | https://github.com/kyutai-labs/moshi | 锁步全双工模型与官方服务端 |
| `personaplex/` | https://github.com/NVIDIA/personaplex | 可控角色/音色双工；规格与 server 形态 |
| `vllm-omni/` | https://github.com/vllm-project/vllm-omni | 上游 omni serving 栈对照 |

## 变更本目录

仅在用户明确要求新增、升级或移除 pin 时操作：

```bash
git subrepo clone <url> third_party/<name>
git subrepo pull third_party/<name>
git subrepo status third_party/<name>
```

- 新增 pin：同步更新本文件 pins 表。
- 升级 pin：`subrepo pull` 后确认 `.gitrepo` commit，并检查 `harness/` 是否仍指向预期路径（尤其 `metronome/`）。
- 不要把弱相关/历史线仓库默认 subrepo 进本目录（视频 RL、agent 训练平台、带大体积 demo 媒体的 clone 等）。

## 与事实源的关系

- 现行结论与实验数字：根 `AGENTS.md` 地图、`docs/` 事实层与 `results/`，不从本目录反推。
- `.context/` 是思考原料（digest / 调研），不是事实层，也不是代码 pin。
