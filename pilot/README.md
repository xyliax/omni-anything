# pilot/ — problem-discovery 阶段的模拟器证据（已降级，非 paper 数据）

按 PAPER-EXPERIMENTS 数据纪律：本目录内容仅支撑 PROBLEM.md/STORY.md 的动机叙事，
**不作为 paper 实验数据**（paper 数字全部来自 E 系列真栈实验，见 results/paper/）。

现状与去留：
- `S1_density.*`：密度→显存墙 pilot——已被 E1 真栈证据完全取代，仅存档；
- `S2_cancellation.*` / `S3_injection.*`：**E4 设计先验的唯一来源**（40% 作废概率、
  LogNormal 注入长度、伤害由相位决定）——E4 真栈数据落地后可整目录删除；
- `make_plots.py` + `CONCLUSIONS.md`：与上同生命周期；
- 模拟器代码在 `../simulator/`（E6 载具，M4 重校验后用于外推,不属于本目录）。
