- **Title / 标题:** StreamChat: Chatting with Streaming Video / StreamChat：与流式视频聊天
- **Summary / 总结:** Capture continues during decode, and output tokens cannot see future frames. / decode 时继续采集，输出 token 不能看未来帧。
- ## Mechanism / 机制
    - Capture thread + FIFO + dynamically updated visual KV. / 采集线程 + FIFO + 动态视觉 KV。
      evidence:: E3, E4
    - Training and inference use aligned future-frame masking. / 训练和推理使用一致的未来帧屏蔽。
      evidence:: E5
- ## Boundary / 边界
    - No mutual same-time antichain, playback frontier, fused attention, or shared historical KV scan. / 没有同片双向 antichain、播放前沿、融合 attention 或共享历史 KV 扫描。
- ## Evidence Index
  collapsed:: true
    - **E2-E6:** Sections 1-3 and experiments

