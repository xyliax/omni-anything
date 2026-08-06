arXiv:2601.10323v1 [cs.CV] 15 Jan 2026

<div style="text-align: center;"></div>


# ROMA: Real-time Omni-Multimodal Assistant with Interactive Streaming Understanding

Xueyun Tian♡, Wei Li, Bingbing Xu♠, Heng Dong♣, Yuanzhuo Wang♠, Huawei Shen♡

♠CAS Key Laboratory of AI Safety, Institute of Computing Technology, CAS, Beijing, China

♡University of Chinese Academy of Sciences, Beijing, China

♣Tsinghua University, Beijing, China

{tianxueyun23z, xubingbing, wangyuanzhuo, shenhuawei}@ict.ac.cn

weiliucasict@email.comdrdby@email.com

## Abstract

Recent Omni-multimodal Large Language Models show promise in unified audio, vision, and text modeling. However, streaming audio-video understanding remains challenging, as existing approaches suffer from disjointed capabilities: they typically exhibit incomplete modality support or lack autonomous proactive monitoring. To address this, we present ROMA, a real-time omni-multimodal assistant for unified reactive and proactive interaction. ROMA processes continuous inputs as synchronized multimodal units, aligning dense audio with discrete video frames to handle granularity mismatches. For online decision-making, we introduce a lightweight speak head that decouples response initiation from generation to ensure precise triggering without task conflict. We train ROMA with a curated streaming dataset and a two-stage curriculum that progressively optimizes for streaming format adaptation and proactive responsiveness. To standardize the fragmented evaluation landscape, we reorganize diverse benchmarks into a unified suite covering both proactive (alert, narration) and reactive (QA) settings. Extensive experiments across 12 benchmarks demonstrate ROMA achieves state-of-the-art performance on proactive tasks while competitive in reactive settings, validating its robustness in unified real-time omni-multimodal understanding. Our project page is available at here $ ^{1} $.

## 1 Introduction

Recent advances in omni-multimodal large language models (OLLMs), such as GPT-4o (Hurst et al., 2024), have enabled unified modeling of speech, vision, and text. This progress facilitates real-world streaming audio-video understanding, defined as combining reactive and proactive capabilities (Figure 1). In the reactive setting, the model

<div style="text-align: center;"><img src="imgs/img_in_image_box_615_443_1050_871.jpg" alt="Image" width="36%" />

ROMA's Streaming Understanding Ability
Proactive
Event-Driven Alert
(Notify me when a bird pops out from behind a tree.)
Real-Time Narration
(What is occurring with the camera lens?)
Reactive
Reactive QA
(What is the woman doing?) (What is the last step to complete the soup?)
cooking - a then slicing
ple of wst then up.

</div>


<div style="text-align: center;">Figure 1: ROMA's streaming understanding capabilities. It supports proactive tasks, including event alerts and narration, alongside reactive question answering.</div>


answers after the query, whereas in the proactive setting, it follows an instruction to continuously monitor the input stream and respond only when conditions are met. Unifying these capabilities is vital for real-world utility, yet the divergent interaction paradigms make it challenging (Horvitz, 1999; Xi et al., 2025; Driess et al., 2023).

Despite the critical need for such unification, existing studies typically lack unified modality support and streaming capabilities. Specifically, speech-centric streaming models (Défossez et al., 2024; Zhang et al., 2025) focus on audio generation but lack visual perception. Conversely, while some approaches address streaming video understanding (Chen et al., 2024; Zhang et al., 2024b), they typically neglect synchronized audio and are confined to specific tasks (e.g., alert or narration). Consequently, unified streaming audio-video understanding remains largely under-explored.

To realize such unification faces two challenges.

 $ ^{1} $https://eureka-maggie.github.io/ROMA_show/

1

First, audio and video exhibit mismatched temporal granularities. While naturally synchronized, audio signals are dense and continuous, whereas video comprises sparse, discrete frames. Under such heterogeneity, maintaining robust cross-modal alignment and fusion demands precise synchronization. Second, effective streaming interaction requires real-time proactive decision-making. Upon integrating these asynchronous signals, the model must continuously synthesize context to determine both response timing and content, conditioned strictly on the stream prefix.

To address these challenges, we propose ROMA, a Real-time Omni-Multimodal Assistant with interactive streaming understanding. To tackle the granularity mismatch, ROMA segments continuous audio into one-second intervals synchronized with video frames, forming temporally aligned units that are processed sequentially as the stream unfolds. We further adapt chunked Time-aligned Multimodal RoPE (TMRoPE) (Xu et al., 2025a) to enforce a shared temporal timeline. For proactive decision-making, ROMA introduces a lightweight speak head parallel to the standard language modeling (LM) head to explicitly predict response timing, decoupling timing from content generation to prevent task interference. Finally, we support this system with a custom streaming dataset and a two-stage training curriculum, progressively optimizing the model for cross-modal streaming format adaptation and proactive responsiveness.

For a comprehensive evaluation, streaming audio-video understanding demands assessing both reactive and proactive capabilities. However, as compared in Table 1, existing benchmarks suffer from inconsistent taxonomies and fragmented protocols, often failing to cover both interaction modes. To enable unified comparison, we reorganize the evaluation landscape into two standardized settings: a proactive mode that tests the ability to autonomously trigger responses at precise moments, and a reactive mode that emphasizes understanding temporal evolution in standard QA. Empirically, ROMA consistently outperforms existing streaming VideoLLMs across both modes. Furthermore, evaluations on open-ended audio-query QA against open-source OLLMs confirm its superior capability in unified audio-video understanding.

In summary, our contributions are as follows:

• Unified streaming framework: We formally define the task of streaming audio-video understanding and propose ROMA, an omnimultimodal assistant unifying reactive and proactive capabilities, supported by a curated dataset and a two-stage curriculum.



• Standardized evaluation benchmark: We establish a comprehensive streaming benchmark by reorganizing fragmented tasks into unified reactive and proactive settings to facilitate rigorous and consistent comparison.

- Superior performance and analysis: ROMA achieves state-of-the-art results across proactive benchmarks while competitive on reactive and open-ended QA. Extensive analysis verifies the efficacy of our timing mechanisms and training strategies.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Benchmark</td><td style='text-align: center; word-wrap: break-word;'>Alert</td><td style='text-align: center; word-wrap: break-word;'>Narration</td><td style='text-align: center; word-wrap: break-word;'>Reactive QA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingBench\n(Lin et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamBench\n(Wu et al., 2024a)</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OVO-Bench\n(Niu et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SVBench\n(Yang et al., 2025b)</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniMMI\n(Wang et al., 2025b)</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OVBench\n(Huang et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr></table>

<div style="text-align: center;">Table 1: Coverage of key streaming ability across representative streaming video benchmarks.</div>


## 2 Related Works

Reactive Models Most existing streaming systems are studied in the reactive setting, answering only after the query arrives. Within this regime, memory-based methods maintain long-range context for coherent understanding over evolving streams (Qian et al., 2024; Zhang et al., 2024a; Wang et al., 2024b; Zhang et al., 2024b; Xiong et al., 2025; Wang et al., 2025a; Zhao et al., 2025), and KV-cache based methods optimize efficiency via scheduling or compression (Di et al., 2025; Ning et al., 2025; Yang et al., 2025a; Xu et al., 2025c; Chen et al., 2025b). Recent omnimultimodal models also adhere to this reactive protocol: MiniCPM-o 2.6 (Yao et al., 2024), Qwen2.5-Omni (Xu et al., 2025a), and Qwen3-Omni (Xu et al., 2025b) support low-latency interaction, and Stream-Omni (Zhang et al., 2025) enables visually-conditioned speech generation, yet none explicitly model proactive monitoring and triggering.

2

<div style="text-align: center;"><img src="imgs/img_in_image_box_141_146_1048_552.jpg" alt="Image" width="76%" />

Audio

</div>


<div style="text-align: center;">Figure 2: Model Architecture. Streaming inputs are processed as aligned multimodal units. The speak head determines response timing, activating the LM head (illustrated via narration) upon crossing a probability threshold.</div>


Proactive Models In contrast, proactive streaming prioritizes continuous monitoring and time-sensitive triggering (e.g., alerts and real-time narration). Proactive VideoLLMs leverage online formats or explicit decision modeling to determine intervention timing (Chen et al., 2024; Yang et al., 2025d; Li et al., 2025; Yang et al., 2025c; Qian et al., 2025), with some explicitly targeting live narration (Chen et al., 2025a). However, these approaches remain predominantly video-centric, neglecting streaming audio.

Streaming Video Understanding Benchmarks

Recent benchmarks prioritize time-sensitive, interactive evaluation (Table 1). Streaming Bench (Lin et al., 2024) and OVO-Bench (Niu et al., 2025) assess temporal perception, while StreamBench (Wu et al., 2024a) and SVBench (Yang et al., 2025b) focus on long-horizon memory. Moreover, OmniMMI (Wang et al., 2025b) and OVBench (Huang et al., 2025) incorporate proactive capabilities, including real-time narration and alerts.

Tables 1 and 10 summarizes prior works.

## 3 Method

To unify reactive answering and proactive timing over continuous inputs, ROMA integrates architectural designs with a tailored training strategy. Section 3.1 presents the model architecture, utilizing chunked TMRoPE and a speak head for alignment and timing control. Section 3.2 details the training and inference pipeline, encompassing dataset construction and a two-stage fine-tuning recipe.

### 3.1 Model Architecture

As illustrated in Figure 2, ROMA processes streaming omni-modal inputs via a unified LLM backbone. We introduce a speak head parallel to the LM head to decouple interaction timing from content generation. This architecture addresses temporal alignment and proactive decision-making through the following mechanisms.

Multimodal units for temporally aligned streaming inputs. To support unified streaming understanding across modalities, we organize audio and video into fixed-interval multimodal units. Following the input format and tokenization of Qwen2.5-Omni, we treat all audio and video signals within each one-second interval as a unit. We align audio with video frames sampled from the same interval, extract their features, and wrap them with special tokens. This retains Qwen2.5-Omni's native format for compatibility while grounding audio in the preceding visual context:

<div style="text-align: center;"><img src="imgs/img_in_image_box_623_1217_1040_1262.jpg" alt="Image" width="35%" />

<|vision_bos|><|audio_bos|>[video tokens][audio tokens] <|audio_eos|><|vision_eos|>

</div>


These multimodal units are fed into the LLM backbone sequentially as the stream unfolds. This process ensures that the model continuously accumulates aligned cross-modal context from the stream prefix, establishing a temporal basis for subsequent causal decision-making.

Chunk-Level Temporal Position Encoding We adapt Qwen2.5-Omni's Time-aligned Multimodal RoPE (TMRoPE) to chunked audio-video streams to support incremental encoding as units arrive.

3

Each one-second unit interleaves visual and auditory tokens, assigning time-aligned 3D position IDs (temporal, height, and width) to preserve their cross-modal correspondence. Consistent with the pre-trained vision encoder, multi-frame visual inputs are temporally aggregated into a fused representation during encoding. All video tokens within a unit therefore share a constant temporal ID. In contrast, audio tokens retain fine-grained temporal IDs at a 40ms resolution to preserve auditory temporal fidelity. To ensure boundary alignment, <|vision_bos|> and <|audio_bos|> share the same base position ID, subsequent units extend the global timeline by continuing from the maximum position ID of the previous unit.

<div style="text-align: center;"><img src="imgs/img_in_image_box_141_574_577_673.jpg" alt="Image" width="36%" />

Chunked TMRoPE

vibob (1.1.1) (1.1.2) (1.1.3) (1.1.4) (1.1.5) (1.1.6) (1.1.7) (1.1.8) (1.1.9) (1.1.10) (1.1.11) (1.1.12) (1.1.13) (1.1.14) (1.1.15) (1.1.16) (1.1.17) (1.1.18) (1.1.19) (1.1.20) (1.1.21) (1.1.22) (1.1.23) (1.1.24) (1.1.25) (1.1.26) (1.1.27) (1.1.28) (1.1.29) (1.1.30) (1.1.31) (1.1.32) (1.1.33) (1.1.34) (1.1.35) (1.1.36) (1.1.37) (1.1.38) (1.1.39) (1.1.40) (1.1.41) (1.1.42) (1.1.43) (1.1.44) (1.1.45) (1.1.46) (1.1.47) (1.1.48) (1.1.49) (1.1.50) (1.1.51) (1.1.52) (1.1.53) (1.1.54) (1.1.55) (1.1.56) (1.1.57) (1.1.58) (1.1.59) (1.1.60) (1.1.61) (1.1.62) (1.1.63) (1.1.64) (1.1.65) (1.1.66) (1.1.67) (1.1.68) (1.1.69) (1.1.70) (1.1.71) (1.1.72) (1.1.73) (1.1.74) (1.1.75) (1.1.76) (1.1.77) (1.1.78) (1.1.79) (1.1.80) (1.1.81) (1.1.82) (1.1.83) (1.1.84) (1.1.85) (1.1.86) (1.1.87) (1.1.88) (1.1.89) (1.1.90) (1.1.91) (1.1.92) (1.1.93) (1.1.94) (1.1.95) (1.1.96) (1.1.97) (1.1.98) (1.1.99) (1.1.100) (1.1.101) (1.1.102) (1.1.103) (1.1.104) (1.1.105) (1.1.106) (1.1.107) (1.1.108) (1.1.109) (1.1.110) (1.1.111) (1.1.112) (1.1.113) (1.1.114) (1.1.115) (1.1.116) (1.1.117) (1.1.118) (1.1.119) (1.1.120) (1.1.121) (1.1.122) (1.1.123) (1.1.124) (1.1.125) (1.1.126) (1.1.127) (1.1.128) (1.1.129) (1.1.130) (1.1.131) (1.1.132) (1.1.133) (1.1.134) (1.1.135) (1.1.136) (1.1.137) (1.1.138) (1.1.139) (1.1.140) (1.1.141) (1.1.142) (1.1.143) (1.1.144) (1.1.145) (1.1.146) (1.1.147) (1.1.148) (1.1.149) (1.1.150) (1.1.151) (1.1.152) (1.1.153) (1.1.154) (1.1.155) (1.1.156) (1.1.157) (1.1.158) (1.1.159) (1.1.160) (1.1.161) (1.1.162) (1.1.163) (1.1.164) (1.1.165) (1.1.166) (1.1.167) (1.1.168) (1.1.169) (1.1.170) (1.1.171) (1.1.172) (1.1.173) (1.1.174) (1.1.175) (1.1.176) (1.1.177) (1.1.178) (1.1.179) (1.1.180) (1.1.181) (1.1.182) (1.1.183) (1.1.184) (1.1.185) (1.1.186) (1.1.187) (1.1.188) (1.1.189) (1.1.190) (1.1.191) (1.1.192) (1.1.193) (1.1.194) (1.1.195) (1.1.196) (1.1.197) (1.1.198) (1.1.199) (1.1.200) (1.1.201) (1.1.202) (1.1.203) (1.1.204) (1.1.205) (1.1.206) (1.1.207) (1.1.208) (1.1.209) (1.1.210) (1.1.211) (1.1.212) (1.1.213) (1.1.214) (1.1.215) (1.1.216) (1.1.217) (1.1.218) (1.1.219) (1.1.220) (1.1.221) (1.1.222) (1.1.223) (1.1.224) (1.1.225) (1.1.226) (1.1.227) (1.1.228) (1.1.229) (1.1.230) (1.1.231) (1.1.232) (1.1.233) (1.1.234) (1.1.235) (1.1.236) (1.1.237) (1.1.238) (1.1.239) (1.1.240) (1.1.241) (1.1.242) (1.1.243) (1.1.244) (1.1.245) (1.1.246) (1.1.247) (1.1.248) (1.1.249) (1.1.250) (1.1.251) (1.1.252) (1.1.253) (1.1.254) (1.1.255) (1.1.256) (1.1.257) (1.1.258) (1.1.259) (1.1.260) (1.1.261) (1.1.262) (1.1.263) (1.1.264) (1.1.265) (1.1.266) (1.1.267) (1.1.268) (1.1.269) (1.1.270) (1.1.271) (1.1.272) (1.1.273) (1.1.274) (1.1.275) (1.1.276) (1.1.277) (1.1.278) (1.1.279) (1.1.280) (1.1.281) (1.1.282) (1.1.283) (1.1.284) (1.1.285) (1.1.286) (1.1.287) (1.1.288) (1.1.289) (1.1.290) (1.1.291) (1.1.292) (1.1.293) (1.1.294) (1.1.295) (1.1.296) (1.1.297) (1.1.298) (1.1.299) (1.1.300) (1.1.301) (1.1.302) (1.1.303) (1.1.304) (1.1.305) (1.1.306) (1.1.307) (1.1.308) (1.1.309) (1.1.310) (1.1.311) (1.1.312) (1.1.313) (1.1.314) (1.1.315) (1.1.316) (1.1.317) (1.1.318) (1.1.319) (1.1.320) (1.1.321) (1.1.322) (1.1.323) (1.1.324) (1.1.325) (1.1.326) (1.1.327) (1.1.328) (1.1.329) (1.1.330) (1.1.331) (1.1.332) (1.1.333) (1.1.334) (1.1.335) (1.1.336) (1.1.337) (1.1.338) (1.1.339) (1.1.340) (1.1.341) (1.1.342) (1.1.343) (1.1.344) (1.1.345) (1.1.346) (1.1.347) (1.1.348) (1.1.349) (1.1.350) (1.1.351) (1.1.352) (1.1.353) (1.1.354) (1.1.355) (1.1.356) (1.1.357) (1.1.358) (1.1.359) (1.1.360) (1.1.361) (1.1.362) (1.1.363) (1.1.364) (1.1.365) (1.1.366) (1.1.367) (1.1.368) (1.1.369) (1.1.370) (1.1.371) (1.1.372) (1.1.373) (1.1.374) (1.1.375) (1.1.376) (1.1.377) (1.1.378) (1.1.379) (1.1.380) (1.1.381) (1.1.382) (1.1.383) (1.1.384) (1.1.385) (1.1.386) (1.1.387) (1.1.388) (1.1.389) (1.1.390) (1.1.391) (1.1.392) (1.1.393) (1.1.394) (1.1.395) (1.1.396) (1.1.397) (1.1.398) (1.1.399) (1.1.400) (1.1.401) (1.1.402) (1.1.403) (1.1.404) (1.1.405) (1.1.406) (1.1.407) (1.1.408) (1.1.409) (1.1.410) (1.1.411) (1.1.412) (1.1.413) (1.1.414) (1.1.415) (1.1.416) (1.1.417) (1.1.418) (1.1.419) (1.1.420) (1.1.421) (1.1.422) (1.1.423) (1.1.424) (1.1.425) (1.1.426) (1.1.427) (1.1.428) (1.1.429) (1.1.430) (1.1.431) (1.1.432) (1.1.433) (1.1.434) (1.1.435) (1.1.436) (1.1.437) (1.1.438) (1.1.439) (1.1.440) (1.1.441) (1.1.442) (1.1.443) (1.1.444) (1.1.445) (1.1.446) (1.1.447) (1.1.448) (1.1.449) (1.1.450) (1.1.451) (1.1.452) (1.1.453) (1.1.454) (1.1.455) (1.1.456) (1.1.457) (1.1.458) (1.1.459) (1.1.460) (1.1.461) (1.1.462) (1.1.463) (1.1.464) (1.1.465) (1.1.466

</div>


<div style="text-align: center;">Figure 3: Chunked TMRoPE. Seamlessly extends the global timeline to streaming inputs by assigning cumulative positional IDs across discrete units.</div>


Speak Head To enable autonomous intervention timing, we design a lightweight speak head. As illustrated in Figure 2, this module is implemented as a two-layer MLP, parallel to the LM head, on top of the streaming backbone. Upon processing each multimodal unit (one second of context), the speak head evaluates the current stream prefix and outputs a probability for a binary decision indicating whether a response is required. A response is triggered if this probability exceeds a threshold; otherwise, the model remains silent and continues consuming the stream. This design decouples the timing decision from text generation, mitigating interference from generative biases. Leveraging findings that upper layers encode high-level features (Tenney et al., 2019; Belrose et al., 2023), we compute the speak head input as a learnable weighted combination of hidden states from the last K layers, with K=4 in our experiments.

### 3.2 Training and Inference Pipeline

#### 3.2.1 Dataset Construction

To enable end-to-end proactive and reactive supervision, we construct a comprehensive streaming dataset structured into two categories and three sub-tasks (Figure 4). Detailed processing pipelines are provided in Appendix A.4.

Online Proactive (27K) To equip the model with the ability to continuously monitor streams and trigger alerts, we curate data from DiDeMo (Anne Hendricks et al., 2017), OOPS (Epstein et al., 2020), and Charades-STA (Zhou et al., 2018). We reformulate these samples into alert-style tasks (e.g., “Alert me when [event] happens”) to train the model in event-driven temporal grounding.



Online Narration (109K) To foster continuous event tracking and incremental summarization, we construct narration samples from MM-DuetIT (Wang et al., 2024a), COIN (Tang et al., 2019), YouCook2 (Zhou et al., 2018), and ActivityNet (Caba Heilbron et al., 2015). Unlike prior works that use dense supervision, we specifically train the model to generate captions only at segment transitions, enabling it to provide concise, real-time updates as the visual context evolves.

Reactive QA (540K) To stabilize general audio-video understanding, we aggregate large-scale reactive QA data from InternVid (Wang et al., 2023), CogStream (Zhao et al., 2025), and others (Chen et al., 2023; Yang et al., 2022; Yao et al., 2025; Fu et al., 2025). These samples cover past events, temporal ordering, and future reasoning.

To ensure unified processing, we synthesize text queries into speech, training the model to handle audio instructions under streaming inputs.

<div style="text-align: center;"><img src="imgs/img_in_image_box_613_958_1050_1228.jpg" alt="Image" width="36%" />

ROMA's Streaming Dataset
Total: 676,731 samples
27,207 108,986 540,538
Proactive Data
Event-Driven Alert Real-Time Narration
"Alert me when [a]t occurs."
video
🔄 "Describe the video in real time."
video
🔄 "Two toy trolls are placed together."
video
🔄 "A person pick up the smallest one."
video
🔄 "He puts it into a plastic bag."
🔄 "Speak Head Label = 1"
🔄 "Speak Head Label = 0"
Reactive Data
Backward Tracing
video 🎯 ...
video 🎯 ...
What do you see and hear in the video?
Forward Prediction
video 🎯 ...
video 🎯 ...
What action should I take next in order to put rice into the lunch box?
Modality Alignment
video 🎯 ...
video 🎯 ...
What is this? Answer the question with a single phrase.

</div>


<div style="text-align: center;">Figure 4: Overview of ROMA's Streaming Dataset. Statistics, task taxonomy, and sample formats.</div>


#### 3.2.2 A Two-Stage Fine-Tuning Recipe

Training an end-to-end streaming omni-multimodal model from scratch is computationally prohibitive. We fundamentally view streaming capability as a transfer problem: adapting a strong foundation model optimized for processing complete videos to handle incremental streams. We thus propose a simple yet effective two-stage recipe. Stage 1 adapts

4

the model to the streaming multimodal input format, while Stage 2 learns precise response timing and proactive policies. In both stages, we freeze all encoders and fine-tune the remaining parameters  $ \theta $.

Stage 1: Streaming Template Alignment This stage mitigates the distribution shift between offline training and streaming inference. We utilize reactive QA datasets to adapt the model to the multimodal unit streaming format. Samples are restructured into sequential units X to simulate streaming, with the audio query and text response Y appended.

We optimize the standard autoregressive language modeling objective over the response tokens. Let  $ \mathcal{D}_{\mathrm{QA}} $ denote the reactive QA dataset. For a sample  $ (X, Y) \sim \mathcal{D}_{\mathrm{QA}} $, where  $ Y = \{y_1, \ldots, y_L\} $ represents the answer sequence, the loss is:

 $$ \mathcal{L}_{\mathrm{L M}}=-\mathbb{E}_{(X,Y)\sim\mathcal{D}_{\mathrm{Q A}}}\left[\sum_{i=1}^{L}\log P(y_{i}\mid y_{<i},X;\theta)\right] $$ 

This stage ensures the model retains its audio-video understanding while adapting to streaming inputs.

Stage 2: Time-Aware Decision Making With the backbone adapted to streaming inputs, this stage activates the speak head to learn when to respond. We formulate response timing as a binary classification task at each multimodal unit step. The positive labels are task-dependent: for proactive alerts, valid triggers lie within the event window; for narration, they align with segment boundaries. To mitigate trigger sparsity, we balance the loss using  $ w_{pos} = N_{neg}/N_{pos} $ derived from dataset statistics.

Let  $ p_t $ be the speak head's predicted probability at time step  $ t $, and  $ z_t \in \{0,1\} $ be the ground truth label. The timing loss is formulated as a weighted Binary Cross-Entropy (BCE):

 $$ \begin{aligned}\mathcal{L}_{time}=-\mathbb{E}_{X\sim\mathcal{D}_{stream}}\Bigg[&\frac{1}{T}\sum_{t=1}^{T}\Big(w_{pos}z_{t}\log p_{t}\\&+\left(1-z_{t}\right)\log(1-p_{t})\Big)\Bigg].\end{aligned} $$ 

To prevent generation quality degradation while optimizing purely for timing, we mix a small portion of the Stage 1 reactive QA data ( $ D_{QA} $) during training. The final objective is a joint optimization:

 $$ \mathcal{L}_{\mathrm{t o t a l}}=\mathcal{L}_{\mathrm{t i m e}}+\lambda\cdot\mathcal{L}_{\mathrm{L M}}, $$ 

where  $ \mathcal{L}_{\mathrm{LM}} $ is calculated only on the mixed QA samples to maintain linguistic competence, and  $ \lambda $ balances the two objectives.

#### 3.2.3 Inference Procedure

During inference, we strictly follow the training configuration. Video frames are uniformly sampled at 2 fps, and each frame is resized so that the number of pixels does not exceed 65,536. We maintain a persistent KV cache across the stream, so each step only encodes the current multimodal unit. Under this setup, encoding one unit takes 0.3697 seconds on average.

## 4 Unified Streaming Evaluation Framework

Effective streaming understanding demands models capable of answering queries and autonomously determining interaction timing. Addressing the fragmentation in existing benchmarks (Table 1), we establish a unified framework comprising two primary settings: proactive interaction, where the model autonomously monitors the stream to trigger responses, and reactive interaction, where it answers queries based on accumulated context.

### 4.1 Proactive Streaming Interaction

In the proactive setting, the model receives an instruction at the start and must process the stream to determine both the precise timing and content of the response. We categorize this into two sub-tasks: event-driven alert and real-time narration.

#### 4.1.1 Event-Driven Alert

This task evaluates the model's temporal awareness, specifically its ability to detect transient events and trigger immediate notifications. We assess this capability under two settings.

Static Temporal Grounding. Following MM-Duet on QVHighlights (Lei et al., 2021) and Charades-STA (Gao et al., 2017), ROMA incrementally predicts response probabilities for each multimodal unit. For QVHighlights, we rank times-tamps by normalized probabilities, reporting mAP (ranking quality) and HIT@1 (top-1 accuracy). For localization on Charades-STA, we threshold probabilities to predict spans, reporting R@0.5 and R@0.7 (recall at 0.5 and 0.7 temporal overlap).

Dynamic Streaming Decision. This configuration enforces a strict streaming protocol where the model makes instantaneous decisions conditioned exclusively on the current multimodal unit. We conduct a comprehensive evaluation across OmniMMI (PA), StreamingBench (PO), and OVOBench (CRR, REC), spanning both single-event

5

alerts and multi-event recurrence. Specifically, for OVO-Bench, we reformulate the original QA-centric annotations into streaming alert targets to evaluate instantaneous responsiveness. To mitigate transient probability fluctuations, we employ a sliding window mechanism. Success is determined by the temporal inclusion of the autonomously triggered response within the ground-truth interval.

See Appendix A.3 for detailed settings.

#### 4.1.2 Real-Time Narration

We define streaming narration as the incremental summarization of evolving events devoid of future context. To evaluate this capability, we employ two settings: a continuous YouCook2 adaptation, constructed by concatenating annotated clips to enforce generation at segment transitions, and the OVO-Bench (SSR) task, where responses are triggered via prediction thresholds and appended to the streaming context. Performance is assessed using the F1 score for temporal localization, BERTScore for the semantic quality of aligned responses, and a GPT-4o-based evaluation of coherence, alignment, and conciseness (detailed in Figure 12).

### 4.2 Reactive QA

In the reactive setting, the model must interpret temporal evolution to answer questions constrained to the causal video history. We utilize OVO-Bench and StreamingBench for standardized evaluation, employing text-based queries to ensure fairness against VideoLLMs baselines and reporting accuracy. To further approximate real-world interaction, we extend the assessment to Video-MME and EgoSchema using synthesized speech inputs. This setting evaluates comprehensive audio-video understanding, with open-ended responses scored by GPT-4o (detailed in Figure 11).

## 5 Experiment

### 5.1 Implementation Details

To address trigger sparsity, we set the positive weight  $ w_{pos} = 3 $ in the weighted BCE loss. For inference, we adopt a pipelined real-time approximation: the model processes unit  $ t $ while simultaneously acquiring unit  $ t + 1 $. To ensure synchronization, we cap generation at 25 tokens (approx. 1s) per segment, allowing longer responses to continue across subsequent units. Please refer to Appendix A.5 for detailed training configurations and complete decoding protocols.

### 5.2 Experimental Results

Baseline Methods In the proactive setting, we limit comparison to streaming-capable models: VideoLLM-Online (the basis for many efficiency-focused architectures), MMDuet, and Dispider. We reproduce results using accessible implementations, defaulting to reported figures otherwise. For Reactive QA, we benchmark against representative streaming VideoLLMs. To assess full-modality understanding, we extend evaluation to open-source omni-modal models, including Qwen2.5-Omni, MiniCPM-o, and VITA-1.5.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td colspan="2">QVHighlight Charades-STA</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>mAP / HIT@1</td><td style='text-align: center; word-wrap: break-word;'>R@0.5 / 0.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TimeChat</td><td style='text-align: center; word-wrap: break-word;'>14.5 / 23.9</td><td style='text-align: center; word-wrap: break-word;'>32.2 / 13.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VTimeLLM</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>31.2 / 11.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HawkEye</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>31.4 / 14.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VTG-LLM</td><td style='text-align: center; word-wrap: break-word;'>16.5 / 33.5</td><td style='text-align: center; word-wrap: break-word;'>33.8 / 15.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>31.3 / 49.6</td><td style='text-align: center; word-wrap: break-word;'>42.4 / 18.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>53.7 / 53.0</td><td style='text-align: center; word-wrap: break-word;'>44.3 / 19.9</td></tr><tr><td colspan="3">- Ablation Study</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>50.3 / 44.7</td><td style='text-align: center; word-wrap: break-word;'>28.2 / 10.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ K = 1 $</td><td style='text-align: center; word-wrap: break-word;'>46.4 / 47.4</td><td style='text-align: center; word-wrap: break-word;'>32.4 / 13.1</td></tr><tr><td colspan="3">- Sensitivity Analysis</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>47.5 / 52.5</td><td style='text-align: center; word-wrap: break-word;'>42.2 / 18.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>47.3 / 49.1</td><td style='text-align: center; word-wrap: break-word;'>38.0 / 16.4</td></tr></table>

<div style="text-align: center;">Table 2: Comparison with existing methods on QV Highlights and Charades-STA benchmarks.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>PA</td><td style='text-align: center; word-wrap: break-word;'>PO</td><td style='text-align: center; word-wrap: break-word;'>CRR</td><td style='text-align: center; word-wrap: break-word;'>REC</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online</td><td style='text-align: center; word-wrap: break-word;'>0.50</td><td style='text-align: center; word-wrap: break-word;'>4.13</td><td style='text-align: center; word-wrap: break-word;'>27.08</td><td style='text-align: center; word-wrap: break-word;'>14.29</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>22.00</td><td style='text-align: center; word-wrap: break-word;'>29.44</td><td style='text-align: center; word-wrap: break-word;'>16.67</td><td style='text-align: center; word-wrap: break-word;'>12.77</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>25.34</td><td style='text-align: center; word-wrap: break-word;'>48.75</td><td style='text-align: center; word-wrap: break-word;'>18.05</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>M4-a</td><td style='text-align: center; word-wrap: break-word;'>25.50</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>37.50</td><td style='text-align: center; word-wrap: break-word;'>53.60</td><td style='text-align: center; word-wrap: break-word;'>35.42</td><td style='text-align: center; word-wrap: break-word;'>33.81</td></tr><tr><td colspan="5">- Ablation Study</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>34.50</td><td style='text-align: center; word-wrap: break-word;'>50.80</td><td style='text-align: center; word-wrap: break-word;'>25.00</td><td style='text-align: center; word-wrap: break-word;'>13.13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Speak Head</td><td style='text-align: center; word-wrap: break-word;'>12.50</td><td style='text-align: center; word-wrap: break-word;'>12.00</td><td style='text-align: center; word-wrap: break-word;'>0.00</td><td style='text-align: center; word-wrap: break-word;'>6.46</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K = 1</td><td style='text-align: center; word-wrap: break-word;'>26.00</td><td style='text-align: center; word-wrap: break-word;'>56.40</td><td style='text-align: center; word-wrap: break-word;'>31.25</td><td style='text-align: center; word-wrap: break-word;'>24.32</td></tr><tr><td colspan="5">- Sensitivity Analysis</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>31.00</td><td style='text-align: center; word-wrap: break-word;'>52.76</td><td style='text-align: center; word-wrap: break-word;'>39.58</td><td style='text-align: center; word-wrap: break-word;'>31.54</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>31.00</td><td style='text-align: center; word-wrap: break-word;'>52.15</td><td style='text-align: center; word-wrap: break-word;'>37.50</td><td style='text-align: center; word-wrap: break-word;'>26.74</td></tr></table>

Table 3: Comparison across single-alert (PA, PO, CRR) and recurring alert (REC) benchmarks.

Event-Driven Alert In static temporal grounding (Table 2), ROMA advances temporal localization on QVHighlights (53.7 mAP) and Charades-STA

6

(44.3/19.9 R@0.5/0.7), confirming that incremental speak probabilities provide enhanced temporal saliency for precise ranking and prediction. In the dynamic setting (Table 3), ROMA demonstrates strong efficacy on single-alert tasks: it excels on PA and PO while remaining competitive on CRR, validating its precise proactive triggering and robust evidence accumulation. Furthermore, ROMA dominates on the REC benchmark, validating its recurrence modeling for tracking repeated instances.

Real-Time Narration As shown in Table 4, ROMA achieves the best temporal triggering accuracy, obtaining an F1 score of 35.21 on YouCook2 and 14.54 on OVO-Bench (SSR), which indicates more precise alignment between generated responses and the annotated narration windows. It also achieves the highest GPT-4o score on both benchmarks. This score averages three criteria (story coherence, alignment to ground truth, and conciseness), with the per-criterion breakdown in Table 9, suggesting more coherent and better-aligned narration when generation is triggered online and the outputs are carried forward as context.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td colspan="3">YouCook2</td><td colspan="3">OVO-Bench (SSR)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F1</td><td style='text-align: center; word-wrap: break-word;'>BERT</td><td style='text-align: center; word-wrap: break-word;'>GPT</td><td style='text-align: center; word-wrap: break-word;'>F1</td><td style='text-align: center; word-wrap: break-word;'>BERT</td><td style='text-align: center; word-wrap: break-word;'>GPT</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TimeChat</td><td style='text-align: center; word-wrap: break-word;'>21.70</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VTG-LLM</td><td style='text-align: center; word-wrap: break-word;'>17.50</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online</td><td style='text-align: center; word-wrap: break-word;'>18.82</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.17</td><td style='text-align: center; word-wrap: break-word;'>10.24</td><td style='text-align: center; word-wrap: break-word;'>0.84</td><td style='text-align: center; word-wrap: break-word;'>0.18</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>17.81</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.23</td><td style='text-align: center; word-wrap: break-word;'>9.02</td><td style='text-align: center; word-wrap: break-word;'>0.79</td><td style='text-align: center; word-wrap: break-word;'>0.31</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>35.21</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.39</td><td style='text-align: center; word-wrap: break-word;'>14.54</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.42</td></tr><tr><td colspan="7">- Ablation Study</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>31.42</td><td style='text-align: center; word-wrap: break-word;'>0.81</td><td style='text-align: center; word-wrap: break-word;'>0.34</td><td style='text-align: center; word-wrap: break-word;'>8.88</td><td style='text-align: center; word-wrap: break-word;'>0.80</td><td style='text-align: center; word-wrap: break-word;'>0.33</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Speak Head</td><td style='text-align: center; word-wrap: break-word;'>9.25</td><td style='text-align: center; word-wrap: break-word;'>0.79</td><td style='text-align: center; word-wrap: break-word;'>0.24</td><td style='text-align: center; word-wrap: break-word;'>3.39</td><td style='text-align: center; word-wrap: break-word;'>0.77</td><td style='text-align: center; word-wrap: break-word;'>0.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K = 1</td><td style='text-align: center; word-wrap: break-word;'>34.43</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.37</td><td style='text-align: center; word-wrap: break-word;'>9.64</td><td style='text-align: center; word-wrap: break-word;'>0.78</td><td style='text-align: center; word-wrap: break-word;'>0.32</td></tr><tr><td colspan="7">- Sensitivity Analysis</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>27.82</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.45</td><td style='text-align: center; word-wrap: break-word;'>10.38</td><td style='text-align: center; word-wrap: break-word;'>0.57</td><td style='text-align: center; word-wrap: break-word;'>0.38</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>35.55</td><td style='text-align: center; word-wrap: break-word;'>0.81</td><td style='text-align: center; word-wrap: break-word;'>0.47</td><td style='text-align: center; word-wrap: break-word;'>13.48</td><td style='text-align: center; word-wrap: break-word;'>0.75</td><td style='text-align: center; word-wrap: break-word;'>0.34</td></tr></table>

<div style="text-align: center;">Table 4: Streaming narration results on YouCook2 and OVO-Bench (SSR). We report F1 for temporal window alignment, and use BERTScore and averaged GPT-4o scores to assess narration quality.</div>


Reactive QA On OVO-Bench (Table 6), ROMA leads in both “Real-time Visual Perception” and “Backward Tracing”. Its superiority over streaming baselines highlights enhanced sensitivity to time-localized cues and robust utilization of historical evidence under truncated contexts. On Streaming-Bench (Table 7), ROMA maintains high accuracy and secures the top rank on “Omni-Source Understanding” benchmark. Attributed to preserving aligned audio during training, which bolsters audio–visual integration. In full-modality evaluation (Table 5), ROMA attains the best performance on Video-MME (without subtitles) and remains competitive on EgoSchema. Notably, these results utilize spoken queries with joint audio–visual inputs to approximate conversational interaction, distinct from text-prompted prior work.



Overall, ROMA strengthens temporal awareness and streaming decision-making, optimizing timing and content via audio-video joint modeling.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>Video-MME</td><td style='text-align: center; word-wrap: break-word;'>EgoSchema</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-Omni</td><td style='text-align: center; word-wrap: break-word;'>20.50</td><td style='text-align: center; word-wrap: break-word;'>58.40</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VITA-1.5</td><td style='text-align: center; word-wrap: break-word;'>28.56</td><td style='text-align: center; word-wrap: break-word;'>45.40</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o</td><td style='text-align: center; word-wrap: break-word;'>19.37</td><td style='text-align: center; word-wrap: break-word;'>55.20</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>33.30</td><td style='text-align: center; word-wrap: break-word;'>55.40</td></tr><tr><td colspan="3">- Ablation Study</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>33.00</td><td style='text-align: center; word-wrap: break-word;'>50.20</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o speak head</td><td style='text-align: center; word-wrap: break-word;'>9.11</td><td style='text-align: center; word-wrap: break-word;'>12.80</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K = 1</td><td style='text-align: center; word-wrap: break-word;'>34.56</td><td style='text-align: center; word-wrap: break-word;'>54.00</td></tr><tr><td colspan="3">- Sensitivity Analysis</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>33.20</td><td style='text-align: center; word-wrap: break-word;'>52.60</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>33.10</td><td style='text-align: center; word-wrap: break-word;'>54.80</td></tr></table>

<div style="text-align: center;">Table 5: Full-modality QA results on Video-MME (no subtitles) and EgoSchema, evaluated with spoken questions to approximate real conversational interaction.</div>


### 5.3 Ablation Study

Single-Stage vs. Two-Stage Training We validate the two-stage curriculum by mixing all data and training directly with the stage-2 objective. This variant consistently degrades on tasks that require online timing and triggering, most notably on dynamic decision making (e.g., REC) and streaming narration (Table 3, Table 4). The results indicate that progressive training is important for learning well-calibrated temporal decision making under streaming input.

Speak Head for Response Gating We replace the speak head with a ‘<lsilencel>’ token following prior work, and cast triggering as next-token prediction with a reweighted loss. Lacking explicit probabilities, we omit QVHighlights and Charades-STA, instead evaluating triggering based on the first non-‘<lsilencel>’ token.

7


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td colspan="6">Real-time Visual Perception</td><td colspan="3">Backward Tracing</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OCR</td><td style='text-align: center; word-wrap: break-word;'>ACR</td><td style='text-align: center; word-wrap: break-word;'>ATR</td><td style='text-align: center; word-wrap: break-word;'>STU</td><td style='text-align: center; word-wrap: break-word;'>FPD</td><td style='text-align: center; word-wrap: break-word;'>OJR</td><td style='text-align: center; word-wrap: break-word;'>EPM</td><td style='text-align: center; word-wrap: break-word;'>ASI</td><td style='text-align: center; word-wrap: break-word;'>HLD</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online</td><td style='text-align: center; word-wrap: break-word;'>8.05</td><td style='text-align: center; word-wrap: break-word;'>23.85</td><td style='text-align: center; word-wrap: break-word;'>12.07</td><td style='text-align: center; word-wrap: break-word;'>14.04</td><td style='text-align: center; word-wrap: break-word;'>45.54</td><td style='text-align: center; word-wrap: break-word;'>21.20</td><td style='text-align: center; word-wrap: break-word;'>22.22</td><td style='text-align: center; word-wrap: break-word;'>18.80</td><td style='text-align: center; word-wrap: break-word;'>12.18</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>13.42</td><td style='text-align: center; word-wrap: break-word;'>11.93</td><td style='text-align: center; word-wrap: break-word;'>14.66</td><td style='text-align: center; word-wrap: break-word;'>11.80</td><td style='text-align: center; word-wrap: break-word;'>14.85</td><td style='text-align: center; word-wrap: break-word;'>10.33</td><td style='text-align: center; word-wrap: break-word;'>10.44</td><td style='text-align: center; word-wrap: break-word;'>8.78</td><td style='text-align: center; word-wrap: break-word;'>0.54</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider</td><td style='text-align: center; word-wrap: break-word;'>57.72</td><td style='text-align: center; word-wrap: break-word;'>49.54</td><td style='text-align: center; word-wrap: break-word;'>62.07</td><td style='text-align: center; word-wrap: break-word;'>44.94</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>51.63</td><td style='text-align: center; word-wrap: break-word;'>48.48</td><td style='text-align: center; word-wrap: break-word;'>55.41</td><td style='text-align: center; word-wrap: break-word;'>4.30</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream-7B</td><td style='text-align: center; word-wrap: break-word;'>24.16</td><td style='text-align: center; word-wrap: break-word;'>29.36</td><td style='text-align: center; word-wrap: break-word;'>28.45</td><td style='text-align: center; word-wrap: break-word;'>33.71</td><td style='text-align: center; word-wrap: break-word;'>25.74</td><td style='text-align: center; word-wrap: break-word;'>28.80</td><td style='text-align: center; word-wrap: break-word;'>39.06</td><td style='text-align: center; word-wrap: break-word;'>37.16</td><td style='text-align: center; word-wrap: break-word;'>5.91</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>63.09</td><td style='text-align: center; word-wrap: break-word;'>53.21</td><td style='text-align: center; word-wrap: break-word;'>68.10</td><td style='text-align: center; word-wrap: break-word;'>39.33</td><td style='text-align: center; word-wrap: break-word;'>69.31</td><td style='text-align: center; word-wrap: break-word;'>58.15</td><td style='text-align: center; word-wrap: break-word;'>55.89</td><td style='text-align: center; word-wrap: break-word;'>47.30</td><td style='text-align: center; word-wrap: break-word;'>23.66</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>- Ablation Study</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>63.09</td><td style='text-align: center; word-wrap: break-word;'>55.05</td><td style='text-align: center; word-wrap: break-word;'>63.79</td><td style='text-align: center; word-wrap: break-word;'>37.64</td><td style='text-align: center; word-wrap: break-word;'>61.39</td><td style='text-align: center; word-wrap: break-word;'>55.43</td><td style='text-align: center; word-wrap: break-word;'>55.22</td><td style='text-align: center; word-wrap: break-word;'>45.95</td><td style='text-align: center; word-wrap: break-word;'>27.96</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Speak Head</td><td style='text-align: center; word-wrap: break-word;'>61.07</td><td style='text-align: center; word-wrap: break-word;'>55.05</td><td style='text-align: center; word-wrap: break-word;'>63.97</td><td style='text-align: center; word-wrap: break-word;'>39.89</td><td style='text-align: center; word-wrap: break-word;'>65.35</td><td style='text-align: center; word-wrap: break-word;'>54.89</td><td style='text-align: center; word-wrap: break-word;'>53.87</td><td style='text-align: center; word-wrap: break-word;'>47.97</td><td style='text-align: center; word-wrap: break-word;'>29.03</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ K = 1 $</td><td style='text-align: center; word-wrap: break-word;'>61.47</td><td style='text-align: center; word-wrap: break-word;'>55.05</td><td style='text-align: center; word-wrap: break-word;'>68.10</td><td style='text-align: center; word-wrap: break-word;'>39.89</td><td style='text-align: center; word-wrap: break-word;'>65.35</td><td style='text-align: center; word-wrap: break-word;'>60.33</td><td style='text-align: center; word-wrap: break-word;'>56.57</td><td style='text-align: center; word-wrap: break-word;'>46.62</td><td style='text-align: center; word-wrap: break-word;'>20.97</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>- Sensitivity Analysis</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>64.43</td><td style='text-align: center; word-wrap: break-word;'>51.38</td><td style='text-align: center; word-wrap: break-word;'>68.97</td><td style='text-align: center; word-wrap: break-word;'>39.33</td><td style='text-align: center; word-wrap: break-word;'>64.36</td><td style='text-align: center; word-wrap: break-word;'>60.87</td><td style='text-align: center; word-wrap: break-word;'>54.88</td><td style='text-align: center; word-wrap: break-word;'>46.62</td><td style='text-align: center; word-wrap: break-word;'>20.97</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>65.10</td><td style='text-align: center; word-wrap: break-word;'>54.13</td><td style='text-align: center; word-wrap: break-word;'>68.97</td><td style='text-align: center; word-wrap: break-word;'>38.20</td><td style='text-align: center; word-wrap: break-word;'>70.30</td><td style='text-align: center; word-wrap: break-word;'>61.41</td><td style='text-align: center; word-wrap: break-word;'>56.57</td><td style='text-align: center; word-wrap: break-word;'>46.27</td><td style='text-align: center; word-wrap: break-word;'>22.58</td></tr></table>

<div style="text-align: center;">Table 6: Reactive QA results on OVO-Bench (excluding Forward Active Responding), evaluating time-sensitive understanding across Real-time Visual Perception and Backward Tracing.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td colspan="7">Real-Time Visual Understanding</td><td colspan="2">Omni-Source Understanding</td><td style='text-align: center; word-wrap: break-word;'>Contextual Understanding</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OP</td><td style='text-align: center; word-wrap: break-word;'>CR</td><td style='text-align: center; word-wrap: break-word;'>CS</td><td style='text-align: center; word-wrap: break-word;'>ATP</td><td style='text-align: center; word-wrap: break-word;'>EU</td><td style='text-align: center; word-wrap: break-word;'>TR</td><td style='text-align: center; word-wrap: break-word;'>PR</td><td style='text-align: center; word-wrap: break-word;'>SU</td><td style='text-align: center; word-wrap: break-word;'>ACP</td><td style='text-align: center; word-wrap: break-word;'>CT</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-Online</td><td style='text-align: center; word-wrap: break-word;'>39.07</td><td style='text-align: center; word-wrap: break-word;'>40.06</td><td style='text-align: center; word-wrap: break-word;'>34.49</td><td style='text-align: center; word-wrap: break-word;'>31.05</td><td style='text-align: center; word-wrap: break-word;'>45.96</td><td style='text-align: center; word-wrap: break-word;'>32.40</td><td style='text-align: center; word-wrap: break-word;'>31.48</td><td style='text-align: center; word-wrap: break-word;'>34.16</td><td style='text-align: center; word-wrap: break-word;'>42.49</td><td style='text-align: center; word-wrap: break-word;'>27.89</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream</td><td style='text-align: center; word-wrap: break-word;'>25.89</td><td style='text-align: center; word-wrap: break-word;'>43.57</td><td style='text-align: center; word-wrap: break-word;'>24.91</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>27.33</td><td style='text-align: center; word-wrap: break-word;'>13.08</td><td style='text-align: center; word-wrap: break-word;'>18.52</td><td style='text-align: center; word-wrap: break-word;'>25.20</td><td style='text-align: center; word-wrap: break-word;'>23.87</td><td style='text-align: center; word-wrap: break-word;'>48.70</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider</td><td style='text-align: center; word-wrap: break-word;'>74.92</td><td style='text-align: center; word-wrap: break-word;'>75.53</td><td style='text-align: center; word-wrap: break-word;'>74.10</td><td style='text-align: center; word-wrap: break-word;'>73.08</td><td style='text-align: center; word-wrap: break-word;'>74.44</td><td style='text-align: center; word-wrap: break-word;'>59.52</td><td style='text-align: center; word-wrap: break-word;'>76.14</td><td style='text-align: center; word-wrap: break-word;'>62.91</td><td style='text-align: center; word-wrap: break-word;'>62.16</td><td style='text-align: center; word-wrap: break-word;'>45.80</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>76.96</td><td style='text-align: center; word-wrap: break-word;'>78.91</td><td style='text-align: center; word-wrap: break-word;'>77.92</td><td style='text-align: center; word-wrap: break-word;'>82.05</td><td style='text-align: center; word-wrap: break-word;'>74.84</td><td style='text-align: center; word-wrap: break-word;'>72.90</td><td style='text-align: center; word-wrap: break-word;'>82.41</td><td style='text-align: center; word-wrap: break-word;'>61.79</td><td style='text-align: center; word-wrap: break-word;'>65.91</td><td style='text-align: center; word-wrap: break-word;'>51.06</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>- Ablation Study</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>75.51</td><td style='text-align: center; word-wrap: break-word;'>85.71</td><td style='text-align: center; word-wrap: break-word;'>76.19</td><td style='text-align: center; word-wrap: break-word;'>78.23</td><td style='text-align: center; word-wrap: break-word;'>59.77</td><td style='text-align: center; word-wrap: break-word;'>61.05</td><td style='text-align: center; word-wrap: break-word;'>73.21</td><td style='text-align: center; word-wrap: break-word;'>60.00</td><td style='text-align: center; word-wrap: break-word;'>59.67</td><td style='text-align: center; word-wrap: break-word;'>23.38</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Speak Head</td><td style='text-align: center; word-wrap: break-word;'>76.13</td><td style='text-align: center; word-wrap: break-word;'>70.49</td><td style='text-align: center; word-wrap: break-word;'>74.14</td><td style='text-align: center; word-wrap: break-word;'>82.40</td><td style='text-align: center; word-wrap: break-word;'>72.86</td><td style='text-align: center; word-wrap: break-word;'>70.80</td><td style='text-align: center; word-wrap: break-word;'>84.78</td><td style='text-align: center; word-wrap: break-word;'>63.20</td><td style='text-align: center; word-wrap: break-word;'>64.91</td><td style='text-align: center; word-wrap: break-word;'>51.69</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ K = 1 $</td><td style='text-align: center; word-wrap: break-word;'>76.69</td><td style='text-align: center; word-wrap: break-word;'>82.03</td><td style='text-align: center; word-wrap: break-word;'>78.86</td><td style='text-align: center; word-wrap: break-word;'>82.05</td><td style='text-align: center; word-wrap: break-word;'>74.84</td><td style='text-align: center; word-wrap: break-word;'>72.90</td><td style='text-align: center; word-wrap: break-word;'>79.63</td><td style='text-align: center; word-wrap: break-word;'>59.76</td><td style='text-align: center; word-wrap: break-word;'>64.49</td><td style='text-align: center; word-wrap: break-word;'>50.53</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>- Sensitivity Analysis</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>75.61</td><td style='text-align: center; word-wrap: break-word;'>81.25</td><td style='text-align: center; word-wrap: break-word;'>76.97</td><td style='text-align: center; word-wrap: break-word;'>82.37</td><td style='text-align: center; word-wrap: break-word;'>71.70</td><td style='text-align: center; word-wrap: break-word;'>75.08</td><td style='text-align: center; word-wrap: break-word;'>81.48</td><td style='text-align: center; word-wrap: break-word;'>62.20</td><td style='text-align: center; word-wrap: break-word;'>65.62</td><td style='text-align: center; word-wrap: break-word;'>50.00</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>75.61</td><td style='text-align: center; word-wrap: break-word;'>80.47</td><td style='text-align: center; word-wrap: break-word;'>79.18</td><td style='text-align: center; word-wrap: break-word;'>82.37</td><td style='text-align: center; word-wrap: break-word;'>73.58</td><td style='text-align: center; word-wrap: break-word;'>75.08</td><td style='text-align: center; word-wrap: break-word;'>82.41</td><td style='text-align: center; word-wrap: break-word;'>63.10</td><td style='text-align: center; word-wrap: break-word;'>65.34</td><td style='text-align: center; word-wrap: break-word;'>47.34</td></tr></table>

<div style="text-align: center;">Table 7: Reactive QA results on StreamingBench (excluding PO), evaluating real-time understanding under streaming input across Real-Time Visual Understanding, Omni-Source Understanding, and Contextual Understanding.</div>


Last-Layer vs. Last-4-Layer Aggregation We ablate four-layer aggregation by restricting the speak head to the final layer  $ (K=1) $. This notably degrades temporal grounding and dynamic triggering (Tables 2, 3) while leaving timestamp-conditioned understanding largely unaffected (Tables 6, 7). This confirms multi-layer aggregation yields robust signals essential for streaming.

### 5.4 Sensitivity analysis

We sweep the positive weight  $ w_{pos} $ in the weighted BCE loss of the speak head to mitigate the class imbalance from sparse speaking timestamps. We observe that  $ w_{pos} $ is critical for proactive tasks (Tables 2–4), while reactive understanding and full-modality QA remain insensitive (Tables 5, 6). Overall,  $ w_{pos} = 3 $ yields the most balanced performance. See Appendix A.2 for sensitivity analysis on inference-time triggering thresholds.



## 6 Conclusion

We introduce ROMA, a real-time omnimultimodal assistant that redefines streaming interaction as the unification of proactive and reactive paradigms. ROMA is the first framework to excel in both modes. To achieve this, we construct a streaming dataset and training recipe that enhances temporal modeling and decision-making. Furthermore, we standardize evaluation through a unified protocol tailored to this dual paradigm, where ROMA demonstrates superior performance. Finally, we provide a systematized overview of prior methods to facilitate future research.

8

## Limitations

While optimized for streaming interaction, the model remains susceptible to distortions such as signal degradation and audio–video asynchrony. Additionally, while capable of continuous streaming, capturing extremely long-term dependencies spanning hours remains constrained by finite context windows and memory. Finally, optimizing the trade-off between inference efficiency and response quality under strict resource constraints remains a critical direction for future work.

#### Ethical Statement

This work utilizes publicly available datasets consistent with their original licenses. While ROMA enables proactive monitoring capabilities, we acknowledge the potential risk of misuse for unauthorized surveillance or privacy infringement. This model is intended for research purposes; due to the possibility of hallucinations or biases inherited from the base LLM, human oversight is strictly required for critical real-world applications.

## References

Lisa Anne Hendricks, Oliver Wang, Eli Shechtman, Josef Sivic, Trevor Darrell, and Bryan Russell. 2017. Localizing moments in video with natural language. In Proceedings of the IEEE international conference on computer vision, pages 5803–5812.

Nora Belrose, Zach Furman, Logan Smith, Danny Ha-lawi, Igor Ostrovsky, Lev McKinney, Stella Biderman, and Jacob Steinhardt. 2023. Eliciting latent predictions from transformers with the tuned lens. arXiv preprint arXiv:2303.08112.

Fabian Caba Heilbron, Victor Escorcia, Bernard Ghanem, and Juan Carlos Niebles. 2015. Activitynet: A large-scale video benchmark for human activity understanding. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 961–970.

Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin, Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing Mao, and Mike Zheng Shou. 2024. Videollm-online: Online video large language model for streaming video. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 18407–18418.

Joya Chen, Ziyun Zeng, Yiqi Lin, Wei Li, Zejun Ma, and Mike Zheng Shou. 2025a. Livecc: Learning video llm with streaming speech transcription at scale. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 29083–29095.

Yi Chen, Yuying Ge, Yixiao Ge, Mingyu Ding, Bohao Li, Rui Wang, Ruifeng Xu, Ying Shan, and Xihui Liu. 2023. Egoplan-bench: Benchmarking multi-modal large language models for human-level planning. arXiv preprint arXiv:2312.06722.

Yilong Chen, Xiang Bai, Zhibin Wang, Chengyu Bai, Yuhan Dai, Ming Lu, and Shanghang Zhang. 2025b. Streamkv: Streaming video question-answering with segment-based kv cache retrieval and compression. arXiv preprint arXiv:2511.07278.

Alexandre Défossez, Laurent Mazaré, Manu Orsini, Amélie Royer, Patrick Pérez, Hervé Jégou, Edouard Grave, and Neil Zeghidour. 2024. Moshi: a speech-text foundation model for real-time dialogue. arXiv preprint arXiv:2410.00037.

Shangzhe Di, Zhelun Yu, Guanghao Zhang, Haoyuan Li, Tao Zhong, Hao Cheng, Bolin Li, Wanggui He, Fangxun Shu, and Hao Jiang. 2025. Streaming video question-answering with in-context video kv-cache retrieval. arXiv preprint arXiv:2503.00540.

Danny Driess, Fei Xia, Mehdi SM Sajjadi, Corey Lynch, Aakanksha Chowdhery, Ayzaan Wahid, Jonathan Tompson, Quan Vuong, Tianhe Yu, Wenlong Huang, and 1 others. 2023. Palm-e: An embodied multimodal language model.

Dave Epstein, Boyuan Chen, and Carl Vondrick. 2020. Oops! predicting unintentional action in video. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 919–929.

Shenghao Fu, Qize Yang, Yuan-Ming Li, Yi-Xing Peng, Kun-Yu Lin, Xihan Wei, Jian-Fang Hu, Xiaohua Xie, and Wei-Shi Zheng. 2025. Vispeak: Visual instruction feedback in streaming videos. arXiv preprint arXiv:2503.12769.

Jiyang Gao, Chen Sun, Zhenheng Yang, and Ram Nevatia. 2017. Tall: Temporal activity localization via language query. In Proceedings of the IEEE international conference on computer vision, pages 5267–5275.

Eric Horvitz. 1999. Principles of mixed-initiative user interfaces. In Proceedings of the SIGCHI conference on Human Factors in Computing Systems, pages 159–166.

Zhenpeng Huang, Xinhao Li, Jiaqi Li, Jing Wang, Xiangyu Zeng, Cheng Liang, Tao Wu, Xi Chen, Liang Li, and Limin Wang. 2025. Online video understanding: Ovbench and videochat-online. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 3328–3338.

Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh, Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, and 1 others. 2024. Gpt-4o system card. arXiv preprint arXiv:2410.21276.

9

Jie Lei, Tamara L Berg, and Mohit Bansal. 2021. Detecting moments and highlights in videos via natural language queries. Advances in Neural Information Processing Systems, 34:11846–11858.

Wei Li, Bing Hu, Rui Shao, Leyang Shen, and Liqiang Nie. 2025. Lion-fs: Fast & slow video-language thinker as online video assistant. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 3240–3251.

Junming Lin, Zheng Fang, Chi Chen, Zihao Wan, Fuwen Luo, Peng Li, Yang Liu, and Maosong Sun. 2024. Streamingbench: Assessing the gap for mlms to achieve streaming video understanding. arXiv preprint arXiv:2411.03628.

Zhenyu Ning, Guangda Liu, Qihao Jin, Wenchao Ding, Minyi Guo, and Jieru Zhao. 2025. Livevlm: Efficient online video understanding via streaming-oriented kv cache and retrieval. arXiv preprint arXiv:2505.15269.

Junbo Niu, Yifei Li, Ziyang Miao, Chunjiang Ge, Yuanhang Zhou, Qihao He, Xiaoyi Dong, Haodong Duan, Shuangrui Ding, Rui Qian, and 1 others. 2025. Ovobench: How far is your video-llms from real-world online video understanding? In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 18902–18913.

Rui Qian, Shuangrui Ding, Xiaoyi Dong, Pan Zhang,

Yuhang Zang, Yuhang Cao, Dahua Lin, and Jiaqi

Wang. 2025. Dispider: Enabling video llms with active real-time interaction via disentangled perception, decision, and reaction. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 24045–24055.

Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuangrui Ding, Dahua Lin, and Jiaqi Wang. 2024. Streaming long video understanding with large language models. Advances in Neural Information Processing Systems, 37:119336–119360.

ByteDance Seed, Jiaze Chen, Tiantian Fan, Xin Liu, Lingjun Liu, Zhiqi Lin, Mingxuan Wang, Chengyi Wang, Xiangpeng Wei, Wenyuan Xu, and 1 others. 2025. Seed1. 5-thinking: Advancing superb reasoning models with reinforcement learning. arXiv preprint arXiv:2504.13914.

Yemin Shi, Yu Shu, Siwei Dong, Guangyi Liu, Jaward Sesay, Jingwen Li, and Zhiting Hu. 2025. Voila: Voice-language foundation models for real-time autonomous interaction and voice role-play. arXiv preprint arXiv:2505.02707.

Yansong Tang, Dajun Ding, Yongming Rao, Yu Zheng, Danyang Zhang, Lili Zhao, Jiwen Lu, and Jie Zhou. 2019. Coin: A large-scale dataset for comprehensive instructional video analysis. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 1207–1216.

Ian Tenney, Dipanjan Das, and Ellie Pavlick. 2019. Bert rediscovers the classical nlp pipeline. arXiv preprint arXiv:1905.05950.

Haibo Wang, Bo Feng, Zhengfeng Lai, Mingze Xu, Shiyu Li, Weifeng Ge, Afshin Dehghan, Meng Cao, and Ping Huang. 2025a. Streambridge: Turning your offline video large language model into a proactive streaming assistant. arXiv preprint arXiv:2505.05467.

Yi Wang, Yinan He, Yizhuo Li, Kunchang Li, Jiashuo Yu, Xin Ma, Xinhao Li, Guo Chen, Xinyuan Chen, Yaohui Wang, and 1 others. 2023. Internvid: A large-scale video-text dataset for multimodal understanding and generation. arXiv preprint arXiv:2307.06942.

Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang, Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. 2024a. VideoIIM knows when to speak: Enhancing time-sensitive video comprehension with video-text duet interaction format. arXiv preprint arXiv:2411.17991.

Yuxuan Wang, Yueqian Wang, Bo Chen, Tong Wu, Dongyan Zhao, and Zilong Zheng. 2025b. Omnimni: A comprehensive multi-modal interaction benchmark in streaming video contexts. In Proceedings of the Computer Vision and Pattern Recognition Conference, pages 18925–18935.

Yuxuan Wang, Cihang Xie, Yang Liu, and Zilong Zheng. 2024b. VideoSlamb: Long-context video understanding with recurrent memory bridges. arXiv preprint arXiv:2409.01071.

Cheng-Kuang Wu, Zhi Rui Tam, Chieh-Yen Lin, Yun Nung Vivian Chen, and Hung-yi Lee. 2024a. Streambench: Towards benchmarking continuous improvement of language agents. Advances in Neural Information Processing Systems, 37:107039–107063.

Shiwei Wu, Joya Chen, Kevin Qinghong Lin, Qimeng Wang, Yan Gao, Qianli Xu, Tong Xu, Yao Hu, Enhong Chen, and Mike Zheng Shou. 2024b. Videoollm-mod: Efficient video-language streaming with mixture-of-depths vision computation. Advances in Neural Information Processing Systems, 37:109922–109947.

Zhiheng Xi, Wenxiang Chen, Xin Guo, Wei He, Yiwen Ding, Boyang Hong, Ming Zhang, Junzhe Wang, Senjie Jin, Enyu Zhou, and 1 others. 2025. The rise and potential of large language model based agents: A survey. Science China Information Sciences, 68(2):121101.

Haomiao Xiong, Zongxin Yang, Jiazuo Yu, Yunzhi Zhuge, Lu Zhang, Jiawen Zhu, and Huchuan Lu. 2025. Streaming video understanding and multi-round interaction with memory-enhanced knowledge. arXiv preprint arXiv:2501.13468.

Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan, Kai Dang, and 1 others. 2025a. Qwen2. 5-omni technical report. arXiv preprint arXiv:2503.20215.

10

Jin Xu, Zhifang Guo, Hangrui Hu, Yunfei Chu, Xiong Wang, Jinzheng He, Yuxuan Wang, Xian Shi, Ting He, Xinfa Zhu, Yuanjun Lv, Yongqi Wang, Dake Guo, He Wang, Linhan Ma, Pei Zhang, Xinyu Zhang, Hongkun Hao, Zishan Guo, and 19 others. 2025b. Qwen3-omni technical report. arXiv preprint arXiv:2509.17765.

Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He, Kelly Peng, Yao Lu, and Song Han. 2025c. Streaming vlm: Real-time understanding for infinite video streams. arXiv preprint arXiv:2510.09608.

Haolin Yang, Feilong Tang, Lingxiao Zhao, Xiang An, Ming Hu, Huifa Li, Xinlin Zhuang, Yifan Lu, Xiaofeng Zhang, Abdalla Swikir, and 1 others. 2025a. Streamagent: Towards anticipatory agents for streaming video understanding. arXiv preprint arXiv:2508.01875.

Pinci Yang, Xin Wang, Xuguang Duan, Hong Chen, Runze Hou, Cong Jin, and Wenwu Zhu. 2022. Avqa: A dataset for audio-visual question answering on videos. In Proceedings of the 30th ACM international conference on multimedia, pages 3480–3491.

Zhenyu Yang, Yuhang Hu, Zemin Du, Dizhan Xue, Shengsheng Qian, Jiahong Wu, Fan Yang, Weiming Dong, and Changsheng Xu. 2025b. Svbench: A benchmark with temporal multi-turn dialogues for streaming video understanding. arXiv preprint arXiv:2502.10810.

Zhenyu Yang, Kairui Zhang, Yuhang Hu, Bing Wang, Shengsheng Qian, Bin Wen, Fan Yang, Tingting Gao, Weiming Dong, and Changsheng Xu. 2025c. Livestar: Live streaming assistant for real-world online video understanding. arXiv preprint arXiv:2511.05299.

Zhiwei Yang, Chen Gao, Jing Liu, Peng Wu, Guansong Pang, and Mike Zheng Shou. 2025d. Assistpda: An online video surveillance assistant for video anomaly prediction, detection, and analysis. arXiv preprint arXiv:2503.21904.

Linli Yao, Yicheng Li, Yuancheng Wei, Lei Li, Shuhuai Ren, Yuanxin Liu, Kun Ouyang, Lean Wang, Shicheng Li, Sida Li, and 1 others. 2025. Timechat-online: 80% visual tokens are naturally redundant in streaming videos. In Proceedings of the 33rd ACM International Conference on Multimedia, pages 10807–10816.

Yuan Yao, Tianyu Yu, Ao Zhang, Chongyi Wang, Junbo Cui, Hongji Zhu, Tianchi Cai, Haoyu Li, Weilin Zhao, Zhihui He, and 1 others. 2024. Minicpm-v: A gpt-4v level mlm on your phone. arXiv preprint arXiv:2408.01800.

Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu, Jiashi Feng, Jifeng Dai, and Xiaojie Jin. 2024a. Flash-vstream: Memory-based real-time understanding for long video streams. arXiv preprint arXiv:2406.08085.

Pan Zhang, Xiaoyi Dong, Yuhang Cao, Yuhang Zang, Rui Qian, Xilin Wei, Lin Chen, Yifei Li, Junbo Niu, Shuangrui Ding, and 1 others. 2024b. Internlmxcomposer2.5-omnilive: A comprehensive multimodal system for long-term streaming video and audio interactions. arXiv preprint arXiv:2412.09596.

Shaolei Zhang, Shoutao Guo, Qingkai Fang, Yan Zhou, and Yang Feng. 2025. Stream-omni: Simultaneous multimodal interactions with large language-vision-speech model. arXiv preprint arXiv:2506.13642.

Zicheng Zhao, Kangyu Wang, Shijie Li, Rui Qian, Weiyao Lin, and Huabin Liu. 2025. Cogstream: Context-guided streaming video question answering. arXiv preprint arXiv:2506.10516.

Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, and 1 others. 2023. Judging llm-as-a-judge with mt-bench and chatbot arena. Advances in neural information processing systems, 36:46595–46623.

Yaowei Zheng, Richong Zhang, Junhao Zhang, Yanhan Ye, Zheyan Luo, Zhangchi Feng, and Yongqiang Ma. 2024. Llamafactory: Unified efficient fine-tuning of 100+ language models. In Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 3: System Demonstrations), Bangkok, Thailand. Association for Computational Linguistics.

Luowei Zhou, Chenliang Xu, and Jason Corso. 2018. Towards automatic learning of procedures from web instructional videos. In Proceedings of the AAAI conference on artificial intelligence, volume 32.

11

### A Appendix

### A.1 Related Works

To address the fragmented landscape of streaming multimodal models, we unify representative methods in a comparative analysis along two axes: supported input modalities and interaction capabilities. We observe that many works described as “streaming” in fact adopt a question-injection protocol, where a query is issued at a predetermined timestamp and the model answers using only the preceding context. As a result, they primarily study long-horizon processing via KV-cache compression and external memory, rather than continuous online interaction with response-timing decisions. In contrast, the few systems that support online streaming interaction typically span all three interaction types. LiveCC is a notable exception: it focuses on fixed-rate real-time narration and therefore does not require deciding when to respond. Moreover, LION-FS, VideoLLM-MoD, and LiveStar mainly introduce efficiency improvements on top of the VideoLLM-online pipeline. Accordingly, we use VideoLLM-online as the representative baseline. Overall, Table 10 shows that our method is the first open-source model to enable full omni-modal streaming while natively supporting proactive response, real-time narration, and reactive QA within a unified framework.

We also summarize commonly used benchmarks for streaming evaluation in Table 1. Although these benchmarks are often described as “streaming”, they target different capabilities, and their coverage is uneven, which motivates us to consolidate them into a unified evaluation protocol.

### A.2 Sensitivity Analysis

Sensitivity analysis confirms robust performance (Figure 5). In static settings, mAP remains stable while HIT@1 shows only slight sensitivity to variations in the window size. Dynamic tasks exhibit a broad operating regime with smooth degradation, indicating no brittle reliance on specific parameters. Narration is likewise insensitive to speak head probability thresholds, justifying a fixed default without additional tuning (Table 8).

### A.3 Evaluation Details

We specify evaluation protocols for our streaming interaction tasks. For PO, we preprocess each sample to replicate the original benchmark by cropping the video to the annotated ask time and injecting the

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Window size w</th><th style='text-align: center;'>mAP</th><th style='text-align: center;'>HIT@1</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>3</td><td style='text-align: center;'>53.15</td><td style='text-align: center;'>52.1</td></tr>
    <tr><td style='text-align: center;'>4</td><td style='text-align: center;'>53.45</td><td style='text-align: center;'>51.1</td></tr>
    <tr><td style='text-align: center;'>5</td><td style='text-align: center;'>53.7</td><td style='text-align: center;'>53.02</td></tr>
    <tr><td style='text-align: center;'>6</td><td style='text-align: center;'>53.73</td><td style='text-align: center;'>51.7</td></tr>
    <tr><td style='text-align: center;'>7</td><td style='text-align: center;'>53.68</td><td style='text-align: center;'>50.4</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 5: Sensitivity analysis on window size on QVHighlight.</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Chart</th><th style='text-align: center;'>thr</th><th style='text-align: center;'>w</th><th style='text-align: center;'>R@0.5</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.4</td><td style='text-align: center;'>2</td><td style='text-align: center;'>42.96</td></tr>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.45</td><td style='text-align: center;'>2</td><td style='text-align: center;'>44.22</td></tr>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.5</td><td style='text-align: center;'>2</td><td style='text-align: center;'>41.08</td></tr>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.4</td><td style='text-align: center;'>3</td><td style='text-align: center;'>44.25</td></tr>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.45</td><td style='text-align: center;'>3</td><td style='text-align: center;'>44.30</td></tr>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.5</td><td style='text-align: center;'>3</td><td style='text-align: center;'>40.94</td></tr>
    <tr><td style='text-align: center;'>(a)</td><td style='text-align: center;'>0.4</td><td style='text-align: center;'>4</td><td style='text-align: center;'>42.93</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.4</td><td style='text-align: center;'>2</td><td style='text-align: center;'>16.91</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.45</td><td style='text-align: center;'>2</td><td style='text-align: center;'>17.07</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.5</td><td style='text-align: center;'>2</td><td style='text-align: center;'>15.78</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.4</td><td style='text-align: center;'>3</td><td style='text-align: center;'>20.11</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.5</td><td style='text-align: center;'>3</td><td style='text-align: center;'>19.87</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.4</td><td style='text-align: center;'>4</td><td style='text-align: center;'>17.82</td></tr>
    <tr><td style='text-align: center;'>(b)</td><td style='text-align: center;'>0.5</td><td style='text-align: center;'>4</td><td style='text-align: center;'>17.98</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 6: Sensitivity analysis on window size and threshold on Charades-STA.</div>


question at that timestamp, ensuring strictly causal temporal ordering. While Streaming VLM baselines take text prompts, our model takes a speech rendering of the same text to benchmark native multimodal processing. For streaming baselines (e.g., VideoLLM-Online and MMDuet), we record the first-response timestamp and report accuracy as the fraction of samples whose first-response time is within  $ \pm2 $ seconds of the annotated ground-truth time. For REC, a model gets one point if its chosen response time falls within the annotated event interval. Each segment is evaluated once, and we report the micro success rate. For CRR, we award one point if the first response after the ask time occurs after the annotated clue time, validating that the model waits for necessary visual evidence before answering. Hyperparameters were determined via validation sets as follows: QVHighlight window size = 5; Charades-STA window size = 3 with threshold = 0.45; PA window size = 5 with threshold = 0.5; PO window size = 4 with threshold = 0.2; REC window size = 2 with threshold = 0.7; CRR window size = 2 with threshold = 0.7; YouCook2 threshold = 0.975; SSR threshold = 0.97.

Due to space constraints, in the main table we report only the average score on the narration task, computed as the mean of the three GPT-4o-based evaluation dimensions. We present the full breakdown in Table 9.

12


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Probability Threshold</td><td colspan="3">YouCook2</td><td colspan="3">OVO-Bench (SSR)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F1</td><td style='text-align: center; word-wrap: break-word;'>BERTScore</td><td style='text-align: center; word-wrap: break-word;'>GPT-Eval</td><td style='text-align: center; word-wrap: break-word;'>F1</td><td style='text-align: center; word-wrap: break-word;'>BERTScore</td><td style='text-align: center; word-wrap: break-word;'>GPT-Eval</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.965</td><td style='text-align: center; word-wrap: break-word;'>35.36</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.52 / 0.28 / 0.31</td><td style='text-align: center; word-wrap: break-word;'>15.53</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.59 / 0.28 / 0.29</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.970</td><td style='text-align: center; word-wrap: break-word;'>35.05</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.50 / 0.29 / 0.33</td><td style='text-align: center; word-wrap: break-word;'>14.54</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.59 / 0.33 / 0.34</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.975</td><td style='text-align: center; word-wrap: break-word;'>35.21</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.53 / 0.29 / 0.36</td><td style='text-align: center; word-wrap: break-word;'>14.58</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.62 / 0.32 / 0.33</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.980</td><td style='text-align: center; word-wrap: break-word;'>34.90</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.55 / 0.28 / 0.36</td><td style='text-align: center; word-wrap: break-word;'>15.15</td><td style='text-align: center; word-wrap: break-word;'>0.84</td><td style='text-align: center; word-wrap: break-word;'>0.59 / 0.33 / 0.36</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>0.985</td><td style='text-align: center; word-wrap: break-word;'>34.07</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.52 / 0.29 / 0.31</td><td style='text-align: center; word-wrap: break-word;'>14.73</td><td style='text-align: center; word-wrap: break-word;'>0.84</td><td style='text-align: center; word-wrap: break-word;'>0.62 / 0.29 / 0.35</td></tr></table>

<div style="text-align: center;">Table 8: Sensitivity analysis of the probability threshold on real-time narration, presenting performance metrics (F1, BERTScore, GPT-Eval) across different triggering thresholds on YouCook2 and OVO-Bench (SSR).</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td colspan="3">YouCook2</td><td colspan="3">SSR</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>F1</td><td style='text-align: center; word-wrap: break-word;'>BERTScore</td><td style='text-align: center; word-wrap: break-word;'>GPT-Eval</td><td style='text-align: center; word-wrap: break-word;'>F1</td><td style='text-align: center; word-wrap: break-word;'>BERTScore</td><td style='text-align: center; word-wrap: break-word;'>GPT-Eval</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TimeChat</td><td style='text-align: center; word-wrap: break-word;'>21.70</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VTG-LLM</td><td style='text-align: center; word-wrap: break-word;'>17.50</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online</td><td style='text-align: center; word-wrap: break-word;'>18.82</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.33 / 0.05 / 0.12</td><td style='text-align: center; word-wrap: break-word;'>10.24</td><td style='text-align: center; word-wrap: break-word;'>0.84</td><td style='text-align: center; word-wrap: break-word;'>0.39 / 0.02 / 0.14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet</td><td style='text-align: center; word-wrap: break-word;'>17.81</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.31 / 0.26 / 0.12</td><td style='text-align: center; word-wrap: break-word;'>9.02</td><td style='text-align: center; word-wrap: break-word;'>0.79</td><td style='text-align: center; word-wrap: break-word;'>0.42 / 0.29 / 0.21</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>35.21</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.53 / 0.29 / 0.36</td><td style='text-align: center; word-wrap: break-word;'>14.54</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.59 / 0.33 / 0.34</td></tr><tr><td colspan="7">- Ablation Study</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mixed Training</td><td style='text-align: center; word-wrap: break-word;'>31.42</td><td style='text-align: center; word-wrap: break-word;'>0.81</td><td style='text-align: center; word-wrap: break-word;'>0.47 / 0.30 / 0.24</td><td style='text-align: center; word-wrap: break-word;'>8.88</td><td style='text-align: center; word-wrap: break-word;'>0.80</td><td style='text-align: center; word-wrap: break-word;'>0.52 / 0.34 / 0.13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o Speak Head</td><td style='text-align: center; word-wrap: break-word;'>9.25</td><td style='text-align: center; word-wrap: break-word;'>0.79</td><td style='text-align: center; word-wrap: break-word;'>0.32 / 0.32 / 0.09</td><td style='text-align: center; word-wrap: break-word;'>3.39</td><td style='text-align: center; word-wrap: break-word;'>0.77</td><td style='text-align: center; word-wrap: break-word;'>0.41 / 0.30 / 0.08</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ K = 1 $</td><td style='text-align: center; word-wrap: break-word;'>34.43</td><td style='text-align: center; word-wrap: break-word;'>0.82</td><td style='text-align: center; word-wrap: break-word;'>0.51 / 0.30 / 0.31</td><td style='text-align: center; word-wrap: break-word;'>9.64</td><td style='text-align: center; word-wrap: break-word;'>0.78</td><td style='text-align: center; word-wrap: break-word;'>0.49 / 0.24 / 0.22</td></tr><tr><td colspan="7">- Sensitivity Analysis</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 2 $</td><td style='text-align: center; word-wrap: break-word;'>27.82</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.62 / 0.27 / 0.46</td><td style='text-align: center; word-wrap: break-word;'>10.38</td><td style='text-align: center; word-wrap: break-word;'>0.57</td><td style='text-align: center; word-wrap: break-word;'>0.63 / 0.21 / 0.29</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>$ w_{pos} = 4 $</td><td style='text-align: center; word-wrap: break-word;'>35.55</td><td style='text-align: center; word-wrap: break-word;'>0.81</td><td style='text-align: center; word-wrap: break-word;'>0.64 / 0.27 / 0.49</td><td style='text-align: center; word-wrap: break-word;'>13.48</td><td style='text-align: center; word-wrap: break-word;'>0.75</td><td style='text-align: center; word-wrap: break-word;'>0.54 / 0.20 / 0.28</td></tr></table>

<div style="text-align: center;">Table 9: Streaming narration results on YouCook2 and OVO-Bench (SSR). We report F1 for temporal window alignment, and use BERTScore and GPT-4o scores to assess narration quality.</div>


### A.4 Data Construction Details

Proactive Data Processing Since the original temporal annotations in DiDeMo and CharadesSTA are often coarse, simply using them for streaming supervision introduces noise. We therefore re-annotate event windows using Doubao-Seed-1.6-thinking (Seed et al., 2025) to obtain precise start and end timestamps. For timing supervision, we label every second within the refined ground-truth event window as a positive trigger, ensuring the model learns robust event sensitivity.

Narration Data Processing Raw videos often contain unlabeled gaps that induce hallucination during training. We mitigate this by excising these intervals and concatenating annotated segments into continuous, semantically dense streams with recalibrated timestamps. For timing supervision, we discard the broad-window labeling of prior work (e.g., MMDuetIT) in favor of strict transition-based triggering. This yields precise supervision for incremental narration via multi-turn SFT.

Audio Query Synthesis To simulate real-world interaction, we synthesize text queries via TTS and overlay them onto original audio tracks. We strictly align these spoken queries with streaming units to enforce audio-driven instruction following.



### A.5 Implementation Details

Training Configuration. We sample videos at 2 FPS and resize frames to a maximum of 65,536 pixels. The model is trained using LLaMA-Factory (Zheng et al., 2024) with a sequence length of 32K on 32 H20 GPUs (using a global batch size of 512). Proactive samples are specifically formatted as multi-turn dialogues to handle multiple triggers within a single stream.

Streaming Decoding Logic. Following the pipelined setting, if a response exceeds the 25-token budget, we append an <|endoftext|>(<eot>) token to signal an unfinished utterance. Decoding resumes in the subsequent segment and terminates only when <|im_end|> is generated.

13


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>Inputs</td><td style='text-align: center; word-wrap: break-word;'>Alert</td><td style='text-align: center; word-wrap: break-word;'>Narration</td><td style='text-align: center; word-wrap: break-word;'>Reactive QA</td><td style='text-align: center; word-wrap: break-word;'>Description</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Moshi (Defossez et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>A full-duplex speech-text model enabling low-latency, real-time voice dialogue without vision.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Voila (Shi et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>A</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Real-time voice-language model with expressive role-play and vocal styles.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoStreaming (Qian et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Streaming framework with hierarchical memory for coherent long-video understanding.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Flash-VStream (Zhang et al., 2024a)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Real-time system with lightweight memory for low-latency long video processing.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLaMB (Wang et al., 2024b)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Long-context model with recurrent memory bridges to propagate information over time.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>InternLM-XComposer2.5 (Zhang et al., 2024b)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Multimodal streaming system with layered memory for long-term video-audio interaction.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamChat (Xiong et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Streaming agent using hierarchical memory to sustain long-context, multi-round dialogue.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamBridge (Wang et al., 2025a)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Plug-and-play buffer turning offline Video-LLMs into proactive streaming assistants.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>CogStream (Zhao et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>QA framework keeping only memory-critical context for efficient reasoning.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ReKV (Di et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Retrieves historical KV-cache as in-context memory instead of re-encoding past frames.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveVLM (Ning et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Optimizes streaming KV-cache update/retrieval for efficient long-horizon processing.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamAgent (Yang et al., 2025a)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Uses KV-based temporal memory to anticipate events and respond proactively.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamingVLM (Xu et al., 2025c)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Manages rolling KV-cache to support infinite video streams under bounded computation.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>StreamKV (Chen et al., 2025b)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Segments and compresses KV-cache, keeping only salient past segments within budget.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveCC (Chen et al., 2025a)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>Trained with continuous speech transcription for real-time narration of long videos.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-online (Chen et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Online model for temporally aligned dialogue via a LIVE training framework.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>AssistPDA (Yang et al., 2025d)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Surveillance assistant unifying anomaly prediction and interactive analysis.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LION-FS (Li et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Uses fast-slow thinking with selective tokenization for efficient streaming.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VideoLLM-MoD (Wu et al., 2024b)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Enables efficient streaming by letting each layer skip a subset of tokens directly.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LiveStar (Yang et al., 2025c)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Uses perplexity-based timing and streaming-aware attention for proactive understanding.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MMDuet (Wang et al., 2024a)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Adopts a video-text duet format to insert replies during continuous playback.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Dispider (Qian et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Disentangles perception, decision, and reaction for asynchronous responses.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-o2.6 (Yao et al., 2024)</td><td style='text-align: center; word-wrap: break-word;'>T+V+A</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Omni model supporting low-latency streaming speech over text, audio, and video.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen2.5-Omni (Xu et al., 2025a)</td><td style='text-align: center; word-wrap: break-word;'>T+V+A</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Dense Thinker–Talker model with streaming encoders for real-time perception.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Qwen3-Omni (Xu et al., 2025b)</td><td style='text-align: center; word-wrap: break-word;'>T+V+A</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Natively omni-modal MoE architecture for high-concurrency streaming generation.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Stream-Omni (Zhang et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V+A</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Efficient modality alignment enabling speech interaction grounded on visual inputs.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ViSpeak (Fu et al., 2025)</td><td style='text-align: center; word-wrap: break-word;'>T+V+A</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>Vision-centric framework producing instruction-like feedback from evolving streams.</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ROMA (Ours)</td><td style='text-align: center; word-wrap: break-word;'>T+V+A</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>End-to-end streaming OLLM processing time-aligned chunks for proactive interaction.</td></tr></table>

<div style="text-align: center;">Table 10: Comparison of different streaming multimodal methods. Note: T=Text, V=Visual, A=Audio. ✓ supports the ability, X does not.</div>


14

### A.6 Case Study

Event-Triggered Alert We present two event-

triggered alert cases: one where the target event

occurs only once (Figure 7), and another where it

recurs multiple times (Figure 8). Compared with

several representative VideoLLMs, our model trig-

gers at more accurate times.

Narration In the narration task, the model must choose when to speak during a long streaming video and provide concise summaries of events observed so far without access to future content. As shown in Figure 9, compared with VideoLLMs, our outputs are more succinct and our response timings align more closely with key event boundaries, leading to more accurate online narration.

Reactive QA With audio queries in the reactive QA setting (Figure 10), ROMA correctly localizes the relevant segment in the long video and extracts the key visual evidence. In contrast, MiniCPM-o misidentifies the segment, while Qwen2.5-Omni often responds with unnecessary follow-up questions.

### A.7 Evaluation Prompt

LLM-as-a-judge is a widely adopted paradigm for scalable evaluation, given its strong alignment with human preferences (Zheng et al., 2023). Accordingly, we employ GPT-4o as a reliable scorer for our open-ended tasks. Detailed prompts are provided in Figures 11 and 12.

15

<div style="text-align: center;"><img src="imgs/img_in_image_box_144_214_1044_617.jpg" alt="Image" width="75%" />

Proactive (Single Alert)

Question: Let me know if the video shows sailors in white uniforms marching in a parade.
Ground Truth: 12s-28s

ROMA (Ours)
17.0s | [Alert]

MMDuet
6.5s | No, the video shows people walking on the street.

VideoLLM-Online
0.0s | [Video Time = 0s) Assistant: Yes, it appears to be a parade with sailors in white uniforms marching.

An example from OmniMMI (PA)

</div>


<div style="text-align: center;">Figure 7: Qualitative comparison on the single-alert proactive task. While MMDuet and VideoLLM-Online exhibit premature triggering and hallucination before the target event appears, ROMA accurately accumulates visual evidence to release a precise alert at 17.0s, aligning with the ground truth interval (12s–28s).</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_144_873_1041_1377.jpg" alt="Image" width="75%" />

Proactive (Recurring Alert)

00:00
10:00
Question: In the video, the man/woman is [showing something to the camera] repetitively. Remind me every time when he/she finishes one.

Ground Truth: (0.0s–5.0s)-(6.0s–13.0s)-(15.0s–18.0s)

ROMA(Ours) MMDuet
7.0s | [Alert]
15.0s | [Alert]

VideoLLM-Online
2.5s | The man is holding a white cloth and a dog.
4.0s | The man puts a white cloth on the table.
5.5s | The man puts a white cloth on the table.
7.0s | The man puts a white cloth on the table.
8.5s | The man in a white sweater and black pants is holding a white cloth and a brown cloth.
10.0s | The man puts a brown coat on the table.
11.5s | The man puts a brown coat on the table.
13.0s | The man puts the clothes on the table.
14.5s | The man puts a brown coat on the table.
16.0s | The man puts a brown coat on the table and then picks up a red book.
17.5s | pick up the clothes.
19.0s | The person is holding a brown bag and a book.

An example from OVO-Bench (REC)

</div>


<div style="text-align: center;">Figure 8: Qualitative comparison on the recurring-alert task. While MMDuet suffers from continuous over-generation without distinguishing event boundaries, ROMA effectively tracks the repetitive action, releasing distinct alerts at 7.0s and 15.0s to capture the recurring instances.</div>


16

<div style="text-align: center;"><img src="imgs/img_in_image_box_142_388_1045_1206.jpg" alt="Image" width="75%" />

Narration

00:00
06:00
12:00
18:00
24:00
30:00
36:00
42:00
48:00
54:00
60:00
66:00
72:00
78:00
84:00
90:00

Question: Describe various activity events occurring in the video in real time.

Ground Truth:
6.0s | cut the goose liver into small slices
12.0s | season them with salt and pepper
22.0s | sprinkle with flour on both sides
30.0s | heat the apple in a pan with some oil
48.0s | sprinkle some salt on top of the apples and add some butter
81.0s | cook the liver on another pan with oil

ROMA (Ours)
7.0s | Cut the liver into slices.
13.0s | Season the liver with salt and pepper.
24.0s | Sprinkle flour on both sides of the liver.
42.0s | Add apples to the pan and move them around.
59.0s | Add butter to the pan and shake the pan occasionally.
71.0s | Place the liver in the pan and cook until browned.

ROMA (Ours)
7.0s | Cut the liver into slices.
13.0s | Season the liver with salt and pepper.
24.0s | Sprinkle flour on both sides of the liver.
42.0s | Add apples to the pan and move them around.
59.0s | Add butter to the pan and shake the pan occasionally.
71.0s | Place the liver in the pan and cook until browned.

MMDuet
5.0s | A person is cutting a piece of meat into slices on a cutting board.
11.0s | sprinkle salt and pepper
16.0s | sprinkle flour on the meat
21.0s | add seasoning and flour to the meat
34.0s | pour oil into the pan
40.0s | fry meat
46.0s | fry the meat
52.0s | fry the meat
58.0s | add butter
64.0s | fry the meat
70.0s | add the ingredients to the pan
83.0s | put the liver into the pan
87.0s | fry meat

VideoLLM-Online
0.0s | (Video Time = 0s) Assistant. You cut the meat with a knife.

An example from YouCook2

</div>


<div style="text-align: center;">Figure 9: Qualitative comparison on the real-time narration task. While MMDuet suffers from severe repetition and redundant over-generation, ROMA effectively tracks the procedural evolution, generating concise, time-aligned descriptions that correspond strictly to the distinct ground truth events.</div>


1/

<div style="text-align: center;">Reactive QA</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_144_561_1044_1024.jpg" alt="Image" width="75%" />

Reactive QA

00:00          05:00          10:00          15:00          20:00          25:00
30:00          35:00          40:00          45:00          50:00

80:00          85:00          90:00          95:00          100:00

Question: Which was the duration of the male protagonist's morning work in the video?

Ground Truth: Two hours and forty-five minutes. (9:15-12:00)

ROMA (Ours)
Answer: From 9:15 to 12:00.
MiniCPM-o 2.6
Answer: The male protagonist's morning work lasted from 07:15 to 09:15, which is a total of two hours.

Qwen2.5-Omni
Answer: The male protagonist's morning work in the video lasted from 9:15 to 12:15. So, it was about 3 hours. If you have any other questions about the video, feel free to ask!

An example from Video-MME

</div>


<div style="text-align: center;">Figure 10: Qualitative comparison on the reactive QA task. While baseline models suffer from temporal misalignment or hallucinated intervals when querying specific activity durations, ROMA accurately retrieves the exact start and end timestamps (9:15–12:00) to derive the correct answer.</div>


18

Evaluation Prompt for Open-Ended Audio-Query Assessment

""

You are an AI assistant tasked with evaluating whether a response matches the correct answer to a given question.

## Evaluation Rules
(1) Output 1 if the response matches the answer exactly or with synonymous/ equivalent wording.
- Synonyms, paraphrases, or different surface forms of the same meaning count as matches.
- Responses containing the correct answer with irrelevant details count as matches.
- Responses providing sufficient information to infer the correct answer count as matches.

(2) Output 0 if the response is incorrect, contradictory, or completely irrelevant to the question.
- If the answer and the response address different topics, or if the response does not answer the question.
- If the response introduces additional details that change the meaning of the answer, mark as 0.

## Examples
Example 1:
Question: What is the genre of this video?
Answer: It is a news report that introduces the history behind Christmas decorations.
Response: It's a Christmas-themed video, filled with festive decorations and a warm, cozy atmosphere. It really captures that classic holiday spirit. What do you think?
Your output: 0

Example 2:
Question: How many birds are above the fireplace?
Answer: 2.
Response: One bird is above the fireplace, and another is below.
Your output: 1

Your Turn:
Question: {question}
Answer: {ground_truth}
Response: {prediction}
Your output:
""

<div style="text-align: center;">Figure 11: Full prompt provided to GPT-4o for open-ended evaluation with audio queries on Video-MME and EgoSchema.</div>


19

<div style="text-align: center;"><img src="imgs/img_in_image_box_143_268_1050_1335.jpg" alt="Image" width="76%" />

Evaluation Prompt for Narration Task Evaluation

""

You are an expert evaluator for video narration quality. Your task is to compare a reference description of a video (ground truth) with a model-generated description for the same video, and output THREE scores between 0 and 1.

You must consider the model response as a SINGLE long story (it may contain multiple sentences describing different moments in the video).

IMPORTANT: Higher scores are always better.

Definitions:

1. coherence (story coherence):
   - How internally coherent and well-structured is the model-generated story by itself?
   - Does it read like a reasonable, temporally plausible sequence of actions and states?
   - Penalize contradictions, abrupt jumps, and incoherent, rambling structure.
   - 1.0 = very coherent and well-structured; 0.0 = completely incoherent.

2. alignment (semantic alignment with ground truth):
   - How well does the model-generated story capture the key actions and steps in the ground truth?
   - Consider whether important actions/events are present, correctly described, and roughly in a reasonable order.
   - Hallucinated major steps that clearly do not appear in the ground truth should reduce this score.
   - 1.0 = almost all key content in GT is covered with correct semantics; 0.0 = almost completely unrelated.

3. conciseness (relevant non-redundancy / brevity):
   - This score measures whether the model response is concise GIVEN IT IS RELEVANT to the ground truth.
   - If the model response is largely unrelated to the ground truth (low semantic overlap, wrong topic, ignores the video), conciseness MUST be near 0, even if the response is short.
   - Penalize heavy repetition of similar sentences, long irrelevant digressions, and obvious padding.
   - However, do NOT penalize necessary detail that genuinely helps describe the steps.
   - 1.0 = succinct, minimal redundancy while preserving essential details; 0.0 = extremely repetitive / rambling / full of irrelevant filler / irrelevant with the groundtruth.

Empty or meaningless model responses (or responses that ignore the task) should receive low scores, typically near 0 for all dimensions.

Output format (VERY IMPORTANT):
- You MUST output valid JSON with exactly the following keys:
  {"coherence": <float>, "alignment": <float>, "conciseness": <float>}
- Each value must be a number between 0 and 1 (inclusive).
- Do NOT output any extra text or explanation.

</div>


<div style="text-align: center;">Figure 12: Prompt used to instruct GPT-4o to evaluate narration quality along three criteria: story coherence, alignment with ground truth, and conciseness.</div>


20