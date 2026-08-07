# third_party/

第三方参考代码树，机制是 **git-subrepo**：普通 `git clone` 即完整树。现行结论与实验数字看根 `AGENTS.md` 地图、`docs/` 事实层与 `results/`。

## 读写边界

只读参考树：阅读对照就地进行；实验、插桩与方案改动落 `harness/`、`docs/` 或自有 fork/patch；各 pin 的 `.gitrepo` 由 git-subrepo 维护；模型权重与大数据集放仓外。

实验路径上真正被 harness 引用的只有 `metronome/`。其余 pin 按题打开。

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
