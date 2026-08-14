- **Title / 标题:** Think-as-You-See / 边看边想
- **Summary / 总结:** Separate video and private-reasoning caches allow frame ingestion and CoT generation to evolve independently under a streaming mask. / 视觉与私有 reasoning 分 cache，在 streaming mask 下独立增长。
- ## Mechanism / 机制
    - `R_t <- V_<=t, R_<t`; future frames are masked. / `R_t` 只看截至当前的帧与历史 reasoning。
      evidence:: E3
    - `C_v` and `C_r` are logically composed for decode and split afterward; positions use separate visual/reasoning axes. / decode 时逻辑合并 `C_v/C_r`，之后拆分；视觉和 reasoning 使用独立位置轴。
      evidence:: E3, E4
- ## Boundary / 边界
    - Reasoning is private, not delivered speech; no playback frontier exists. / reasoning 是私有思考，不是播放语音；没有 playback frontier。
      evidence:: E7
    - Concurrency is algorithmic/dataflow-level; kernel-level overlap and KV scan sharing are not demonstrated. / 并发停留在算法/dataflow 层，没有证明 kernel overlap 或 KV 扫描共享。
      evidence:: E8
- ## Evidence Index
  collapsed:: true
    - **E3-E4:** Section 3.2; Figure 3
    - **E6:** Section 4
    - **E7-E8:** output and systems boundary audit
