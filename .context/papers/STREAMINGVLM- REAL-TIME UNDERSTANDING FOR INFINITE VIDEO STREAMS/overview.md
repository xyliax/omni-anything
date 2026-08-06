- **Title:** STREAMINGVLM: Real-Time Understanding for Infinite Video Streams
- **Summary:** StreamingVLM shows that long-horizon real-time video understanding can be made practical by aligning overlapped-chunk SFT with inference-time KV-cache reuse, attention sinks, recent text/vision windows, and bounded contiguous RoPE.
- **Paper Type:** system
- **Venue:** ICLR 2026; arXiv:2510.09608v2
- **Authors:** Ruyi Xu* (MIT), Guangxuan Xiao* (MIT), Yukang Chen (NVIDIA), Liuning He (MIT), Yao Lu (NVIDIA), Song Han (MIT/NVIDIA)
- **Keywords:** streaming VLM, infinite video, KV cache, attention sink, sliding window attention, contiguous RoPE, video captioning, sports commentary
- ## Quick Reference
    - **Why Read:** A concrete recipe for turning a finite-context VLM into a low-latency streaming video commentator: train with short overlapped chunks, then infer with reusable compact KV state rather than recomputing overlapping windows.
      claim_kind:: analyst_assessment
      evidence:: E2, E3, E5, E14
    - **One-Sentence Contribution:** StreamingVLM improves real-time infinite-stream video captioning by fine-tuning Qwen2.5-VL-7B on overlapped interleaved video-text chunks and serving it with attention-sink plus recent text/vision KV reuse and contiguous RoPE.
      evidence:: E3, E4, E5, E9
    - **Mental Model:** A rolling commentator notebook: pin the opening instructions, keep the latest transcript, keep only the last visual moments, and renumber the remaining pages so the model never sees out-of-range positions.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of long-game pairwise captioning wins, constant per-token latency, and VQA transfer without VQA-specific fine-tuning.
      evidence:: E11, E13, E14
        - C1: On Inf-Streams-Eval, StreamingVLM in infinite mode reports 66.18% win rate against GPT-4o mini in 100 s chunk mode, 87.81% against LiveCC chunk mode, and 99.12% against LiveCC infinite mode.
          evidence:: E7, E11
        - C2: In the latency test, StreamingVLM keeps roughly 0.05 s/token through 1000 s of processed video and is reported to support 8 FPS real-time commentary on one NVIDIA H100.
          evidence:: E14
        - C3: Without VQA SFT, StreamingVLM improves over Qwen2.5-VL-7B-Instruct on LongVideoBench from 54.70 to 59.00 and on OVOBench Realtime from 56.00 to 61.96.
          evidence:: E13
    - **Main Caveat:** Trust is strongest for English sports commentary under an LLM-as-judge protocol; broader video domains, human preference validation, variance across judges/runs, and exact reproducibility of GPT-5 cleaning/judging are less established in the supplied text.
      claim_kind:: analyst_assessment
      evidence:: E6, E7, E10
- ## Argument Map
    - **Problem and Stakes:** The paper targets VLMs that must process near-infinite video streams and respond in real time without latency or memory increasing with stream length. The stakes are practical assistants, embodied agents, and autonomous systems where full attention is quadratic/unbounded and naive sliding windows either lose coherence or recompute too much.
      evidence:: E2
    - **Prior Gap:** Existing video VLMs mostly operate on finite clips, while text-side streaming/KV eviction methods do not directly solve cross-modal training-inference mismatch. The paper argues that training on extremely long videos is infeasible, so a short-context training procedure must induce the same recency and cache structure used at test time.
      evidence:: E2, E18
    - **Key Insight:** Approximate the streaming inference attention pattern during SFT rather than training on full long videos: use overlapped full-attention chunks with per-second interleaved vision/text, then infer with a compact reusable KV cache and bounded position indices. This makes the model expect the same kinds of context that will survive online eviction.
      evidence:: E3, E4, E5
    - **Claims:** The paper supports four main falsifiable claims: better long-stream captioning, real-time stable inference, transfer to VQA, and necessity of the proposed cache/position/training design choices.
      evidence:: E11, E13, E14, E15
        - C1: StreamingVLM improves long-horizon sports captioning, reporting 66.18% win rate versus GPT-4o mini chunk mode and 87.81% versus LiveCC chunk mode on Inf-Streams-Eval.
          evidence:: E11
        - C2: KV reuse with fixed retained context keeps inference real time, with reported 0.05 s/token through 1000 s and 8 FPS support on one H100.
          evidence:: E14
        - C3: Streaming SFT improves general video QA without VQA-specific fine-tuning, especially on long-horizon and real-time benchmarks.
          evidence:: E13
        - C4: Contiguous RoPE, recent visual retention, and overlapped/data-curated SFT are material contributors, not cosmetic engineering details.
          evidence:: E15, E16, E17
- ## Mechanism and Design
    - **Core Mechanism:** StreamingVLM maintains a compact KV cache containing attention-sink text tokens, a recent text window, and a recent vision window; older vision is evicted first, and text history is retained asymmetrically for discourse coherence. The reported default in Figure 3 is 512 sink tokens, 512 recent text tokens, and 16 seconds of recent vision.
      evidence:: E3
    - **Data / Control Flow:** The system first builds aligned sports video/commentary streams with ASR and GPT cleaning, then trains on overlapped 24 s/12 s chunks with interleaved per-second V/T tokens, and finally serves a live stream by appending new states, evicting outside-window tokens, and shifting RoPE indices. The previous text used in training is compressed to the first T_sink and last T_window tokens to match inference.
      evidence:: E5, E6, E7
        - Data preparation uses WhisperX ASR over five sports, GPT-5 keep/edit/delete cleaning, and separate SFT/evaluation/annealing segment pipelines.
          evidence:: E6, E7, E8
        - SFT uses full attention inside short overlapped chunks, with loss only on aligned text positions and placeholders for seconds without narration.
          evidence:: E5, E7
        - Online inference avoids recomputing overlapping windows by reusing cached KV for retained sink/text/vision tokens and assigning contiguous positions after eviction.
          evidence:: E3, E4
    - **Design Decisions:** The three main design choices are asymmetric cache retention, contiguous RoPE, and overlapped-chunk SFT; each directly addresses a failure mode of full attention or naive sliding windows. The closest tested alternatives are native RoPE, ReKV-style eviction, no/altered windows, and non-overlapping or weaker data training.
      evidence:: E12, E15, E16, E17
        - Need: preserve discourse while bounding compute; choice: sink plus long text window plus short vision window; tradeoff: the model can only use old visual facts if they survive in text or sink-like context.
          claim_kind:: analyst_assessment
          evidence:: E3, E16
        - Need: avoid out-of-distribution position growth after many evictions; choice: left-shift contiguous RoPE, including 3D RoPE for Qwen-VL visual tokens; tested alternative native RoPE drops sharply in infinite mode.
          evidence:: E4, E15
        - Need: teach streaming behavior without quadratic long-context training; choice: overlapped full-attention chunks with interleaved V/T at one-second cadence; alternative non-overlap performs worse in the reported ablation.
          evidence:: E5, E17
    - **Implementation Surface:** The reported implementation fine-tunes Qwen2.5-VL-Instruct-7B in two stages: 525K Inf-Streams SFT samples plus 526K Live-WhisperX samples, followed by 14K high-quality annealing samples, using about 128 H100-days. The paper reports the public GitHub URL, but gives more algorithmic detail about cache/RoPE behavior than low-level kernel or serving-stack detail.
      evidence:: E1, E9
- ## Evaluation and Evidence
    - **Setup:** Captioning is evaluated on Inf-Streams-Eval, a 20-game benchmark averaging 2.12 hours per game, plus Livecc-Sports-3K CC; pairwise commentary quality is judged by GPT-5 with references. VQA transfer is evaluated on VideoMME, MVBench, LongVideoBench, and OVOBench, and GPT-4o mini is only evaluated in chunk mode on Inf-Streams-Eval.
      evidence:: E7, E10
    - **Claim-Evidence Matrix:** The evidence is primarily empirical: win-rate tables for captioning, accuracy tables for VQA, latency traces for serving, and ablations over RoPE/cache/data/training strategy. The strongest support is for the integrated system under the paper's own sports-streaming setting.
      claim_kind:: analyst_assessment
      evidence:: E11, E13, E14, E15
        - C1 captioning quality: supported by Inf-Streams-Eval and Livecc-Sports-3K win rates, with the caveat that GPT-4o mini is evaluated only in 100 s chunk mode on Inf-Streams-Eval.
          claim_kind:: analyst_assessment
          evidence:: E10, E11
        - C2 real-time efficiency: supported by per-token latency over increasing processed video length and the reported 8 FPS single-H100 setting.
          evidence:: E14
        - C3 VQA transfer: supported by direct comparison against the Qwen2.5-VL-7B-Instruct base model on four public video QA suites.
          evidence:: E13
        - C4 component necessity: supported by ablations over native versus contiguous RoPE, visual/text windows and sink size, Live-WhisperX versus Inf-Streams data, annealing data, and overlap strategy.
          evidence:: E15, E16, E17
    - **Headline Results:** The headline is that StreamingVLM beats strong captioning baselines on long sports streams while keeping latency flat, and the same SFT improves some general video QA metrics. The most important caveat is that the captioning metric is pairwise LLM judging rather than human evaluation with statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E7, E11, E13, E14
        - Captioning: StreamingVLM^infinity reports 66.18% win rate vs GPT-4o^dagger, 87.81% vs Livecc^dagger, and 99.12% vs Livecc^infinity on Inf-Streams-Eval.
          evidence:: E11
        - Efficiency: the latency trace reports StreamingVLM at 0.05 s/token through 1000 s, while full attention exceeds limits/OOM and overlapping windows remain inefficient.
          evidence:: E14
        - VQA: relative to Qwen2.5-VL-7B-Instruct, StreamingVLM improves MVBench by 1.82, LongVideoBench by 4.30, and OVOBench Realtime by 5.96, while VideoMME remains 65.10.
          evidence:: E13
    - **Ablations and Sensitivity:** The ablations are unusually diagnostic for a systems-style VLM paper: they test position extrapolation, retained-context allocation, training data, and training/inference consistency. They show that the system is not just a cache trick; model behavior depends on being trained for the same interleaved streaming context it will see at inference.
      claim_kind:: analyst_assessment
      evidence:: E12, E15, E16, E17
        - RoPE: native infinite inference drops to 25.09% win rate against GPT-4o^dagger, while contiguous infinite inference reaches 66.18%, supporting the bounded-position argument.
          evidence:: E15
        - Windows: removing visual context hurts, and the paper identifies 16 s as a good visual window; Appendix A.3 says sink size affects performance and plateaus at larger sizes.
          evidence:: E16
        - Data/strategy: win rate vs GPT-4o^dagger rises from 32.17 with Live-WhisperX to 63.46 with Inf-Streams-Train and 66.18 after high-quality annealing; the paper also reports overlap outperforming non-overlap.
          evidence:: E17
    - **Reproducibility Gaps:** The paper reports a GitHub URL, model base, sample counts, compute budget, and major benchmark settings, but the supplied text does not provide random seeds, repeat counts, statistical uncertainty, complete judging/cleaning prompts, or enough low-level serving details to independently audit latency. Reuse of the data pipeline may also depend on access/licensing for full sports videos and proprietary GPT-5 judging/cleaning behavior.
      claim_kind:: analyst_assessment
      evidence:: E1, E6, E7, E9, E14
- ## Technical Judgment
    - **What Holds Up:** The core systems idea is credible because it attacks the actual serving bottleneck: overlapping-window recomputation is replaced by fixed-size KV reuse, while contiguous RoPE prevents the retained cache from carrying ever-growing positions. The ablation evidence is aligned with the mechanism: native RoPE collapses in infinite mode, ReKV disrupts the fine-tuned context format, and the latency trace stays flat only for the proposed cache policy.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E12, E14, E15
    - **Where It May Fail:** The approach may fail on tasks requiring precise retrieval of old visual evidence that was never verbalized into retained text, because the design intentionally keeps only recent vision tokens. Generalization is also uncertain outside English sports streams and LLM-judge commentary, since the main data/evaluation pipeline is sports-focused and window sizes are scenario-sensitive hyperparameters.
      claim_kind:: analyst_assessment
      evidence:: E3, E6, E7, E16
    - **Relation to Other Work:** Technically, StreamingVLM is closest to StreamingLLM-style attention sinks plus sliding windows, but extends the recipe to cross-modal streams with interleaved vision/text and 3D contiguous RoPE. Compared with training-free KV eviction such as ReKV, the paper's central distinction is training-inference alignment: the model is fine-tuned to expect the same cache format that serving will preserve.
      claim_kind:: analyst_assessment
      evidence:: E12, E18
    - **Transferable Lesson:** For streaming foundation-model systems, do not treat cache eviction as an inference-only optimization: choose the retained-state interface first, then train with short synthetic contexts whose attention pattern approximates that interface. Bounded positional indices are part of that interface, not an implementation afterthought, whenever the model uses relative/rotary position encodings over unbounded streams.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E15, E17
- ## Glossary
  collapsed:: true
    - Attention sink / T_sink: Early retained text tokens, including system and previous text, kept in the KV cache to stabilize attention over long streaming inference.
    - T_window: The recent text-token window retained in the streaming KV cache; intended to preserve discourse and long-term memory in compressed textual form.
    - V_window: The recent vision-token window retained in the streaming KV cache; the reported default covers 16 seconds of video.
    - Contiguous RoPE: A position-indexing scheme that left-shifts RoPE indices after eviction so retained and incoming tokens remain contiguous and bounded rather than growing with total stream length.
    - Overlapped-chunk SFT: Training strategy that splits streams into overlapping short chunks, applies full attention within each chunk, and interleaves vision/text at one-second intervals to mimic streaming inference.
    - Inf-Streams-Eval: The paper's long-stream sports-commentary benchmark: 20 full games averaging 2.12 hours, evaluated by GPT-5 pairwise voting with references.
    - Chunk mode vs. infinite mode: Chunk mode processes independent fixed segments with previous text; infinite mode runs continuously over the full stream while reusing past KV/output state.
    - Win rate: Pairwise LLM-as-judge preference share of model A over model B; higher is better, but results depend on judge model, references, and prompt protocol.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/metadata | Title block | high
      locator:: paper header
      quote:: arXiv:2510.09608v2 [cs.CV] 31 May 2026. Published as a conference paper at ICLR 2026. STREAMINGVLM: REAL-TIME UNDERSTANDING FOR INFINITE VIDEO STREAMS. Ruyi Xu, Guangxuan Xiao, Yukang Chen, Liuning He, Yao Lu, Song Han. MIT, NVIDIA. https://github.com/mit-han-lab/streaming-vlm
    - **E2:** problem/paper_statement | Abstract and Introduction | high
      locator:: Abstract; Section 1
      quote:: VLMs could power real-time assistants and autonomous agents, but they face a critical challenge: understanding near-infinite video streams without escalating latency and memory usage. Processing entire videos with full attention leads to quadratic computational costs and poor...
    - **E3:** system_design/implementation_detail | 2.1 Inference Scheme of Streaming VLM | high
      locator:: Figure 3; Streaming-aware KV Cache
      quote:: We keep 512 attention-sink tokens to stabilize attention, a long text window of 512 recent tokens to preserve long-term memory, and a short vision window covering 16 seconds to track ongoing actions. The key idea is to maintain a compact and stable KV cache by reusing previous...
    - **E4:** optimization/implementation_detail | 2.1 Inference Scheme of Streaming VLM | high
      locator:: Contiguous RoPE paragraph
      quote:: When earlier tokens are removed, the RoPE indices of subsequent and incoming tokens are shifted so that their positions remain numerically contiguous with the last retained token. Once the video length surpasses the total window size, the effective RoPE indices stop growing an...
    - **E5:** method/paper_statement | 2.2 Training Strategy | high
      locator:: overlapped-chunk full-attention description
      quote:: We split a long video stream into consecutive chunks of length W frames, with temporal overlap O frames between C_i and C_{i+1}. Each chunk is treated as a training instance in which vision and text tokens are sampled and interleaved at 1 s intervals. We apply full attention w...
    - **E6:** experiment_setup/paper_statement | 2.3.1 Video Collection and ASR; 2.3.2 Data Cleaning | high
      locator:: data pipeline
      quote:: We collected game videos from five sports: basketball, soccer, ice hockey, baseball, and American football... obtaining an initial corpus of videos with a total duration of over 6,000 hours. We set rules and used GPT to clean these data... 46.32% were kept, 37.89% were edited,...
    - **E7:** experiment_setup/paper_statement | 2.3.3 SFT and Evaluation Data Segmentation | high
      locator:: SFT and Inf-Streams-Eval construction
      quote:: Under the training setup in Section 2.2, we split videos with W = 24 s and O = 12 s... For evaluation, we create a new benchmark, Inf-Streams-Eval. It contains 20 full games with an average length of 2.12 hours... For scoring, a larger model (we use gpt-5) votes between two mo...
    - **E8:** method/paper_statement | 2.3.4 High-Quality Annealing Data | high
      locator:: annealing data construction
      quote:: We first slice all data without overlap, requiring each clip to be 16–64 seconds long with internal silence no longer than 3 seconds... Across all games, we obtained 52,530 new samples. Then... GPT-5 [determines] whether the proportion of real-time commentary exceeds 80%... on...
    - **E9:** experiment_setup/paper_statement | 3.1 Experimental Setup | high
      locator:: Training paragraph
      quote:: We fine-tune StreamingVLM from Qwen2.5-VL-Instruct-7B. Step 1 teaches the model the infinite streaming inference pattern. We train on our SFT set (525K streaming samples) and on LiveCC's Live-WhisperX-526K (526K streaming samples). Step 2 uses our high-quality annealing data (...
    - **E10:** experiment_setup/paper_statement | 3.1 Experimental Setup | high
      locator:: Baselines and Benchmark paragraphs
      quote:: Due to design limits, GPT-4o mini is evaluated on Inf-Streams-Eval in the chunk setting, not the infinite mode used by StreamingVLM. LiveCC7B-Instruct is tested in both chunked and infinite settings... For video understanding, we evaluate StreamingVLM on four public suites: Vi...
    - **E11:** result/experiment_result | 3.2.1 Captioning | high
      locator:: Table 1
      quote:: Table 1 reports StreamingVLM^infinity on Inf-Streams-Eval with win rates 66.18 against GPT-4o^dagger, 87.81 against Livecc^dagger, and 99.12 against Livecc^infinity. On Livecc-Sports-3K cc it reports 47.33 against LLaVA, 45.59 against GPT-4o, 44.21 against Gemini, and 56.19 ag...
    - **E12:** result/experiment_result | 3.2.1 Captioning | high
      locator:: Table 2; ReKV comparison
      quote:: We observe a paradox for training-free ReKV: models without task-specific fine-tuning perform poorly, yet models that are specially fine-tuned rely on a fixed context format that ReKV's eviction policy disrupts, often yielding no output. Table 2 reports StreamingVLM (+ReKV) wi...
    - **E13:** result/experiment_result | 3.2.2 VQA | high
      locator:: Table 3
      quote:: Without any VQA fine-tuning, StreamingVLM delivers consistent accuracy gains across all tasks. Table 3 reports Qwen-2.5-VL-7B-Instruct at 67.34, 65.10, 54.70, 56.00 on MVBench, Video MME, LongVideoBench, OVOBench Realtime, and StreamingVLM at 69.16, 65.10, 59.00, 61.96.
    - **E14:** result/experiment_result | 3.3 Efficiency Tests | high
      locator:: Figure 7 and efficiency paragraph
      quote:: Figure 7 reports per-token latency versus video length. Full attention soon exceed the limit and OOM... Streaming VLM keeps fixed context length and reuses KV, maintains lower and stable latency, and supports real-time commentary at 8 FPS on a single NVIDIA H100. The table sho...
    - **E15:** ablation/ablation | 3.4.1 Contiguous RoPE | high
      locator:: Table 4
      quote:: Native RoPE degrades sharply on infinite streams because its index grows fast and exceeds the training range. Table 4 reports Native^infinity at 25.09 against GPT-4o^dagger, 59.42 against Livecc^dagger, and 60.32 against Livecc^infinity, while Contiguous^infinity reaches 66.18...
    - **E16:** ablation/ablation | 3.4.2 Sliding Window and Sink; A.3 Sensitivity Analysis | high
      locator:: Table 5; Table 8
      quote:: The right table in Table 5 shows that a 16 s visual window is a good choice... keeping 0 s of vision context leads to a clear drop. Appendix A.3 states that sink token size noticeably impacts final performance, generally larger T_sink capacities yield better win rates, and gai...
    - **E17:** ablation/ablation | 3.4.3 Training Strategy and Dataset | high
      locator:: Table 6 and Table 7
      quote:: Compared with a model trained only on Live-WhisperX-526K, training on the overlapped SFT data strengthens perception of infinite video, yielding clear gains +31.29 on Inf-Streams-Eval. Table 6 reports 32.17, 63.46, and 66.18 win rate against GPT-4o^dagger for Live-WhisperX, +I...
    - **E18:** prior_work/paper_statement | 4 Related Work | high
      locator:: Long-context and streaming inference; streaming video LLMs
      quote:: The text community has proposed attention sink + sliding window, RoPE extension and continuity, and KV cache compression/eviction such as H2O, SnapKV, and ReKV. However, these methods are mostly tested on text, and alignment between streaming training and inference remains und...
