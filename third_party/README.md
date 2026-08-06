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

- `third_party/*` 只读参考。实验改动放在 `harness/`、patch 或 fork，不直接改上游树再当实验代码。
- 不要把模型权重、大数据集放进本目录。
- 加入前评估：是否会显著胀大本仓库历史；偶尔阅读用 shallow clone 即可，不必 subrepo。

## 候选上游（需要钉死时再 `subrepo clone`）

| 名称 | 上游 | 备注 |
| --- | --- | --- |
| vllm-omni | https://github.com/vllm-project/vllm-omni | serving 栈对照 |
| moshi | https://github.com/kyutai-labs/moshi | 双工语音 |
| moshi-finetune | https://github.com/kyutai-labs/moshi-finetune | 同上 |
| personaplex | https://github.com/NVIDIA/personaplex | 工业双工参考 |
| DuplexOmni | https://github.com/MuyeHuang/DuplexOmni | 曾钉 `4c93fd0` |
| JoyAI-VL-Interaction | https://github.com/jd-opensource/JoyAI-VL-Interaction | 曾钉 `9d07596` |
| ThinkStream | https://github.com/CASIA-IVA-Lab/ThinkStream | 流式思考 |
| VST | https://github.com/1ranGuan/VST | Video Streaming Thinking |
| EasyVideoR1 | https://github.com/cyuQ1n/EasyVideoR1 | 曾钉 `7ab338b`；偏 video RL |
| MMDuet2 | https://github.com/yellow-binary-tree/MMDuet2 | 偏 video RL |
| uni-agent | https://github.com/verl-project/uni-agent | 偏 agent RL |
| DualAxisRM | https://github.com/MM-Speech/DualAxisRM | 小参考 |
| videollm-online | https://github.com/showlab/videollm-online | 含大体积 demo 媒体 |
| jiuwenswarm | https://github.com/openJiuwen-ai/jiuwenswarm | 曾钉 `de623dd` @ develop；体积大、旧集成线 |
