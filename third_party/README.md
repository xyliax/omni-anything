# third_party/

外部参考代码统一挂在此目录，使用 **[git-subrepo](https://github.com/ingydotnet/git-subrepo)**（不是 git submodule）。

普通 `git clone` 即可拿到完整树，无需 `--recursive`。

## 当前 pins

| 路径 | 上游 | 钉死 commit | 用途 |
| --- | --- | --- | --- |
| `metronome/` | https://github.com/19PINE-AI/metronome | `2783a90` | 真双工 serving baseline harness；纪律见 `../METRONOME-NOTE.md` |

## 操作

```bash
# 新增
git subrepo clone <upstream-url> third_party/<name>

# 拉上游（在钉死策略允许时）
git subrepo pull third_party/<name>

# 查看状态
git subrepo status third_party/<name>
```

每个 subrepo 目录内有 `.gitrepo` 元数据（由 git-subrepo 维护，一般不要手改）。

## 纪律

- `third_party/*` 只读参考。实验改动放在仓库自己的 `harness/`、patch 或 fork，不直接改上游树再当实验代码。
- 不要把模型权重、大数据集放进本目录。
- 体积很大、与 RP1 仅弱相关的 clone（例如历史 streaming-RL 栈、带 demo 视频的仓库）优先放在 `Project-Duplex` 仓外，不要默认 subrepo 进本仓库。

## 候选（尚未挂入）

与双工 / serving 相关、需要钉死再读代码时可按需加入：

- `vllm-omni` — https://github.com/vllm-project/vllm-omni
- `moshi` / `moshi-finetune` — kyutai-labs
- `personaplex` — NVIDIA
- `DuplexOmni` — MuyeHuang/DuplexOmni

加入前评估：是否会显著胀大本仓库历史；若只是偶尔阅读，仓外 shallow clone 更合适。
