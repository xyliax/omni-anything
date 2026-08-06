arXiv:2606.11167v1 [cs.CL] 9 Jun 2026

# Multi-Faceted Interactivity Alignment in Full-Duplex Speech Models

Atsumoto Ohashi$^{1}$, Neil Zeghidour$^{2}$, Alexandre Défossez$^{1,2*}$, Eugene Kharitonov$^{2*}$

 $ ^{1} $Kyutai, Paris, France   $ ^{2} $Gradium, Paris, France

atsumoto.ohashi@kyutai.org, eugene@gradium.ai

## Abstract

Full-duplex spoken dialogue models can listen and speak simultaneously, making them a promising architecture for natural conversation. However, current models are trained solely with supervised learning through token-level likelihood maximization, which does not directly optimize interaction-level behaviors, causing interactivity issues such as excessive silence and ill-timed turn-taking. Recent work has applied reinforcement learning (RL) to improve interactivity, but existing methods address only a limited set of interactive behaviors in their rewards. In this work, we propose a post-training alignment method that comprehensively improves the interactivity of full-duplex spoken dialogue models through RL. We address the four canonical axes of interactivity: pause handling, turn-taking, backchanneling, and user interruption. For each axis, we extract short audio segments from human conversation corpora and optimize the model with axis-specific reward functions. An extra LLM-based reward for response quality prevents semantic degradation. We apply our method to two open-source models, Moshi and PersonaPlex, demonstrating consistent improvements in interactivity on both offline evaluation with pre-recorded audio and real-time multi-turn dialogue evaluation. $ ^{1} $

## 1 Introduction

Full-duplex spoken dialogue models are a promising architecture for reproducing human-like conversational dynamics in spoken dialogue systems (Ji et al., 2024; Arora et al., 2026a). Conventional turn-based spoken dialogue models (Zhang et al., 2023; Fang et al., 2024; Xu et al., 2025; Wu et al., 2025b) begin generating a response only after the user's entire utterance has been received, and the user must wait for the system to finish speaking before taking turns. In contrast, full-duplex models (Défossez et al., 2024; Zhang et al., 2025; Yu et al., 2025) are designed to process both the user's and the system's speech streams in parallel. This eliminates the need for explicit turn boundary detection via external voice activity detection (VAD) modules, and enables the model to implicitly learn smooth turn-taking, backchanneling, and overlap handling within its internal representations.



Yet, full-duplex models still face challenges in interactivity in real-time conversations. Previous studies (Arora et al., 2024; Lin et al., 2025a) have revealed issues such as excessive silence, badly timed turn-taking, and a lack of backchannels. One possible cause is the inherent limitation of supervised learning. Interaction-level behaviors, such as the timing and duration of utterances, are difficult to optimize directly through token-level likelihood maximization. Furthermore, the mismatch between the input distributions at training and inference time, such as exposure bias, prevents models from behaving robustly in real conversations.

Prior works have explored using reinforcement learning (RL) to improve the interactivity of full-duplex models (Yu et al., 2025; Chen et al., 2025a), but covered only a subset of conversational dynamics such as handling user's barge-in and backchanneling, failing to comprehensively address all axes of interactivity. Furthermore, each study targets a single model, leaving open the question of whether RL-based interactivity optimization generalizes across different full-duplex systems. A common practical challenge is also that optimizing timing-related rewards alone can degrade the semantic quality of generated responses (Hsiao et al., 2026), yet no systematic solution has been established.

In this work, we propose a post-training alignment method that comprehensively improves the interactivity of full-duplex speech models. We target the four core axes of full-duplex interactivity:

 $ ^{*} $These authors jointly supervised this work.

 $ ^{1} $The checkpoints of the models and audio samples are available at https://huggingface.co/kyutai/moshika-rl-seamless and https://huggingface.co/kyutai/personaplex-rl-seamless.

1

pause handling, turn-taking, backchanneling, and user interruption. We automatically extract short audio segments from real human conversations exhibiting such behaviors, and optimize the model on them using group relative policy optimization (GRPO) (Shao et al., 2024). Furthermore, an LLM Judge reward for semantic quality (Lin et al., 2025b; Arora et al., 2026b) preserves response content during RL. We apply the proposed method to two different open-source models, Moshi (Défos-sez et al., 2024) and PersonaPlex (Roy et al., 2026), and demonstrate consistent improvements across all metrics on Full-Duplex-Bench v1 (Lin et al., 2025a). Notably, although training is performed on short, extracted segments, we also demonstrate that the improvements generalize to real-time multi-turn dialogues through the evaluation on Full-Duplex-Bench v2 (Lin et al., 2026).

## 2 Related Work

### 2.1 Full-Duplex Spoken Dialogue Models

Full-duplex models can be broadly categorized into two types: cascaded and end-to-end. Cascaded approaches achieve full-duplex dialogue by augmenting text-based LLMs with external VAD and turn-control modules (Wang et al., 2024; Zhang et al., 2024b; Fu et al., 2025; Wang et al., 2025b; Liao et al., 2025), but they suffer from inter-module latency and loss of paralinguistic information. End-to-end approaches, in contrast, process both the user's and the model's audio streams within a unified model (Nguyen et al., 2023; Hu et al., 2025; Wang et al., 2025a). Various strategies exist for handling the two streams: processing them fully in parallel (Défossez et al., 2024; Yao et al., 2026; Shi et al., 2025), interleaving them in short alternating chunks (Veluri et al., 2024; Zhang et al., 2025), or explicitly controlling listen/speak states (Yu et al., 2025; Chen et al., 2025b). Most existing models are trained solely with supervised learning, and are not optimized for interaction-level properties. In this work, we propose a post-training method based on RL to unlock the full potential of end-to-end architectures for improved interactivity.

### 2.2 Reinforcement Learning for Spoken Language Models

Inspired by the success of alignment techniques (Stiennon et al., 2020; Ouyang et al., 2022; Rafailov et al., 2023) in text language modeling, these methods have been extended to speech for semantic coherence (Lin et al., 2025b), speech quality (Zhang et al., 2024a), question answering (Chen et al., 2026a), reasoning (Wu et al., 2025b), and paralinguistic processing (Yang et al., 2025b).



For full-duplex dialogue models specifically, alignment methods have been applied not only to improve semantic quality (Arora et al., 2026b; Wu et al., 2025a) but also to optimize dialogue dynamics (Yu et al., 2025; Chen et al., 2025a). SALMONN-omni (Yu et al., 2025) first performs supervised learning and then applies direct preference optimization (DPO) (Rafailov et al., 2023) to improve the model's ability to handle user's barge-ins and backchannels. ORISE (Chen et al., 2025a) replaces preference-based methods with online RL based on REINFORCE (Williams, 1992), achieving a better balance between barge-in and backchannel handling in noisy environments. The most closely related work is the concurrent ASPIRIN (Hsiao et al., 2026), which also applies GRPO to Moshi to optimize interaction timing. However, these prior and concurrent works incorporate only a subset of interactivity aspects into their reward functions, and report that other aspects, such as response latency or semantic quality, either fail to improve or even degrade (Hsiao et al., 2026). In this work, we comprehensively address four axes of interactivity derived from Full-Duplex-Bench, together with LLM-based evaluation of response content quality. We demonstrate that our approach improves performance across all aspects, including those that degraded in prior work.

### 2.3 Benchmarks for Full-Duplex Spoken Dialogue Models

Earlier work relied on corpus-level statistics such as distributions of utterance and silence durations (Nguyen et al., 2023) to assess full-duplex dialogue models. Benchmarks like Full-Duplex-Bench v1 (Lin et al., 2025a) have since been developed to enable more fine-grained evaluation. It feeds pre-recorded static audio into dialogue models and evaluate the resulting responses (Peng et al., 2025; Ge et al., 2025; Chang et al., 2026). More recently, benchmarks have been constructed for dynamic evaluation in multi-turn dialogues, going beyond static assessment (Arora et al., 2024; Zhang et al., 2026). Full-Duplex-Bench v2 (Lin et al., 2026) has dialogue models interact in real time with an automated conversational partner and evaluates their abilities using LLM Judge. In this work, we leverage the four evaluation axes of Full-

2

Step 1. Curation of Training Data  $ \mathcal{D}_{\text{pause}} \cup \mathcal{D}_{\text{turn}} \cup \mathcal{D}_{\text{bc}} \cup \mathcal{D}_{\text{int}} $

<div style="text-align: center;"><img src="imgs/img_in_image_box_141_189_1046_428.jpg" alt="Image" width="75%" />

s^X

</div>


<div style="text-align: center;">Figure 1: Overview of the proposed method. We first extract segments related to each interactivity axis  $ \ell \in \{\text{pause, turn, bc, int}\} $ from human conversation datasets to construct the training data  $ D_{\ell} $. For each segment (and optionally its dialogue context) sampled from  $ D_{\ell} $, the full-duplex spoken dialogue model generates multiple outputs, which are scored by axis-specific reward functions  $ R_{\ell} $ and used to optimize the model via GRPO.</div>


Duplex-Bench v1 for RL reward design, and use Full-Duplex-Bench v2 to verify generalization to multi-turn settings.

## 3 Method

We propose a post-training alignment method that improves the interactivity of full-duplex spoken dialogue models through RL. We target four core axes of interactivity: pause handling (remaining silent during user hesitations), turn-taking (responding promptly when the user yields the floor), backchanneling (producing short feedback cues while the user speaks), and user interruption (yielding and responding when the user barges in). These four axes have been established as a standard and comprehensive characterization of full-duplex interactivity (Lin et al., 2025a), and we adopt them as a necessary set for our study. $ ^{2} $ Figure 1 illustrates the overview of our method. Our key idea is to extract short audio segments from real human conversations, each exemplifying one of the four axes, and optimize the model on them using GRPO (Shao et al., 2024) with axis-specific rewards.

Below, we first describe the full-duplex modeling framework assumed in this work (Section 3.1), followed by our RL pipeline (Section 3.2), and its two key components: segment extraction (Section 3.3) and reward design (Section 3.4).

### 3.1 Full-Duplex Spoken Dialogue Modeling

We consider full-duplex spoken dialogue models based on discrete audio tokens and autoregressive language modeling (Défossez et al., 2024; Veluri et al., 2024). Given a two-channel dialogue between speakers X and Y, a speech tokenizer E maps each speaker's waveform into a sequence of discrete tokens from a vocabulary  $ \mathcal{V} $:  $ [x_{1:N}; y_{1:N}] = E([s^X; s^Y]) $. The model, parameterized by  $ \theta $, learns to autoregressively predict speaker Y's tokens conditioned on speaker X's input stream and its own preceding outputs:



 $$ \pi_{\theta}(y_{1:N},w_{1:N}\mid x_{1:N})=\prod_{n=1}^{N}\pi_{\theta}(y_{n},w_{n}\mid x_{\leq n},y_{<n},w_{<n}). $$ 

Here, we assume that a parallel text token stream  $ w_{1:N} $ is jointly predicted, which is a common practice used to guide the semantic content of the generated speech (Chen et al., 2025b; Yao et al., 2026) and also to implicitly control when the model speaks (Défossez et al., 2024; Shi et al., 2025). After the supervised learning on dialogue datasets, the model  $ \pi_{\theta} $ can serve as spoken dialogue systems.

### 3.2 Reinforcement Learning Pipeline

At each training step during RL of the pretrained model  $ \pi_{\theta} $, for each sample in the batch, we first sample an interactivity axis  $ \ell \in \{\text{pause, turn, bc, int}\} $, corresponding to pause handling, turn-taking, backchanneling, and user interruption, respectively. We then draw a segment from the axis-specific training set  $ [s^X; x^Y] \sim \mathcal{D}_\ell $, which consists of short audio clips extracted from human conversation corpora (see Section 3.3 for extraction details). From the speaker  $ X $'s audio in the segment, which is encoded into tokens  $ x_{1:N} $, the current policy  $ \pi_\theta $ generates  $ G $ completions:

 $$ \{(\hat{y}_{1:N}^{(g)},\;\hat{w}_{1:N}^{(g)})\}_{g=1}^{G}\;\sim\;\pi_{\theta}(\cdot\mid x_{1:N})\;. $$ 

 $ ^{2} $While our method can readily accommodate additional axes, exploring them is beyond the scope of this work.

3

Each completion is decoded into a waveform  $ \hat{s}^{Y,(g)} = D(\hat{y}_{1:N}^{(g)}) $ and scored by an axis-specific reward function  $ r^{(g)} = \mathcal{R}_{\ell}(\hat{s}^{Y,(g)}) $ (see Section 3.4).

We normalize the rewards across the G samples to get an advantage estimate for each completion:

 $$ \begin{array}{c}\hat{A}^{(g)}=\frac{r^{(g)}-mean(\{r^{(g)}\}_{g=1}^{G})}{\mathrm{std}(\{r^{(g)}\}_{g=1}^{G})}.\end{array} $$ 

We then minimize a clipped surrogate loss (Schulman et al., 2017) augmented with a KL penalty against the frozen reference policy  $ \pi_{ref} $ (a copy of the model before RL training):

 $$ \begin{align*}\mathcal{L}(\theta)=-\frac{1}{G}\sum_{g=1}^{G}\frac{1}{N}\sum_{n=1}^{N}\Big[\min\big(\rho_{n}^{(g)}\hat{A}^{(g)},\\ \mathrm{clip}(\rho_{n}^{(g)},1-\epsilon,1+\epsilon)\hat{A}^{(g)}\big)-\beta\mathrm{KL}\big[\pi_\theta\|\pi_{\mathrm{ref}}\big]_{n}\Big],\end{align*} $$ 

where  $ \rho_n = \pi_\theta(\hat{w}_n \mid \cdot) / \pi_{\theta_{\text{old}}}(\hat{w}_n \mid \cdot) $ is the importance sampling ratio between the current and the sampling-time policies, and KL[ $ \cdot\| \cdot\|_n $ is the exact KL divergence at position  $ n $. Note that because interactivity and the speech content are primarily controlled by text tokens (Hsiao et al., 2026; Chen et al., 2026a),  $ \rho_n $ and the objective is computed using only the probability of the text tokens  $ \hat{w} $, excluding the audio tokens  $ \hat{y} $.

To help the model generalize beyond the short segment boundaries, we prepend a context, which is the recording immediately preceding the segment, to the input audio. The context length is drawn randomly during training (details in Section 4.3). The loss is computed only over the segment itself; the context window is masked out.

### 3.3 Training Data Curation

We construct the training set  $ \mathcal{D}_\ell $ for each interactivity axis  $ \ell \in \{\text{pause, turn, bc, int}\} $ from corpora of two-party human conversations in which each speaker is recorded on a separate channel. One channel serves as the user input  $ (X) $ and the other as the target speaker  $ (Y) $ whose behavior the model learns to reproduce. The extraction proceeds in two stages: utterance annotation and event-driven segment identification.

Utterance annotation We first annotate each recording using a VAD model, which produces, a sequence of labeled intervals classified as inter-pausal units (IPUs) or silences for each speaker. We then group consecutive IPUs from the same speaker into utterances by placing an utterance boundary at any silence longer than 1.0 s. A silence of at most 1.0 s that falls within an utterance is called a pause. Let  $ U_1, U_2, \ldots, U_M $ denote the sequence of all utterances from both speakers, sorted by their start time. Each utterance  $ U_k $ is associated with a speaker spk $ (U_k) \in \{X, Y\} $, a start time  $ t_{\text{start}}(U_k) $, and an end time  $ t_{\text{end}}(U_k) $. We write  $ \text{dur}(U_k) = t_{\text{end}}(U_k) - t_{\text{start}}(U_k) $ for the duration.



Event-driven segment identification From the utterance sequence, we identify segments that exemplify each interactivity axis. Each segment defines a time window over the stereo recording, together with a label indicating its axis. The extraction criteria for each axis are as follows:

Pause Handling  $ \mathcal{D}_{\text{pause}} $ A single utterance  $ U_k $ with  $ \text{spk}(U_k) = X $ satisfying: (i)  $ \text{dur}(U_k) \geq \tau_{\min} $; (ii)  $ U_k $ contains at least one internal pause; and (iii) speaker  $ Y $ produces no speech. This captures moments where  $ X $ hesitates but does not yield the floor.

Turn-Taking $\mathcal{D}_{\mathrm{turn}}$ A consecutive pair $(U_k, U_{k+1})$ with $\mathrm{spk}(U_k) = X$ and $\mathrm{spk}(U_{k+1}) = Y$, where (i) both utterances satisfy the minimum duration $\tau_{\mathrm{min}}$; and (ii) the gap $t_{\mathrm{start}}(U_{k+1}) - t_{\mathrm{end}}(U_k) \leq 0.4$ s (Lin et al., 2025a; Heldner and Edlund, 2010). This captures smooth turn transitions where $Y$ responds promptly after $X$ yields the floor.

Backchanneling $\mathcal{D}_{bc}$ An utterance $U_k$ with $\mathrm{spk}(U_k) = X$ satisfying: (i) $\mathrm{dur}(U_k) \geq \tau_{\min}$; (ii) speaker $Y$ says only short utterances ($\leq 1$ s) in $U_k$ (Ekstedt and Skantze, 2022).

User Interruption  $ \mathcal{D}_{\text{int}} $ A four-utterance sequence  $ (U_k, U_{k+1}, U_{k+2}, U_{k+3}) $ with the speaker pattern  $ X \to Y \to X \to Y $:  $ U_k $ is an initial utterance by  $ X $;  $ U_{k+1} $ is  $ Y $'s response that gets interrupted;  $ U_{k+2} $ is  $ X $'s interrupting utterance, which begins before  $ U_{k+1} $ ends; and  $ U_{k+3} $ is the post-interruption response. All four utterances must satisfy  $ \tau_{\min} $.

Rather than relying on TTS-synthesized dialogues or artificial noise augmentation (Chen et al., 2025a), our training data from human conversations can broadly capture real-world conversational dynamics and noise without artificial bias.

### 3.4 Reward Design

We design a dedicated reward function  $ R_\ell $ for each interactivity axis  $ \ell \in \{\text{pause, turn, bc, int}\} $ to

4

compute the reward of the generated audio  $ \hat{s}^{Y,(g)} $. We first apply VAD to  $ s^{X} $ and  $ \hat{s}^{Y,(g)} $ to obtain sequences of speech intervals and utterance annotationss as in Section 3.3.

Pause handling  $ R_{pause} $ The model should remain silent throughout the segment, including during intra-utterance pauses. We assign a binary reward  $ R_{pause} = -1 $ if the generated audio contains any speech interval longer than 1 s, and  $ R_{pause} = 0 $ otherwise.

Turn-Taking $R_{\mathrm{turn}}$ The model should begin speaking promptly after speaker $X$ finishes. Let $d$ be the response delay between the end time of $X$'s turn and the start time of the first utterance (>1 s) in the generated audio. We set $R_{\mathrm{turn}} = -d$. If the model produces no utterance, we consider $d$ as the remaining segment duration after the end time of $X$'s turn.

Backchanneling  $ R_{bc} $ The model should produce short vocalizations aligned with the ground-truth backchannel positions, without interrupting speaker X. We define short speech intervals ( $ \leq $1s) in the generated audio as backchannels, and longer ones as takeovers. A generated backchannel is a true positive if it falls within  $ \pm $1s of a ground-truth backchannel. Unmatched generated backchannels and takeovers are counted as false positives. The resulting F1 score is used as the reward  $ R_{bc} $.

User interruption  $ R_{int} $ The model must detect the user's interrupting utterance  $ (U_{k+2};\text{Sec-tion3.1}) $ and respond promptly. Analogously to  $ R_{turn} $, we measure d from the end of the interruption  $ t_{end}(U_{k+2}) $ to the model's next speech and set  $ R_{int} = -d $.

LLM Judge  $ R_{llm} $ To prevent semantic degradation caused by optimization with delay-based rewards alone (Hsiao et al., 2026), we add a content quality reward to the turn-taking and user-interruption axes. Specifically, we apply automatic speech recognition (ASR) to both  $ s^X $ and  $ \hat{s}^Y $ to obtain transcriptions, which are then scored by an LLM judge on a three-point scale for contextual relevance and naturalness of the model's response. When combining  $ R_{llm} $ with the delay reward ( $ R_{turn} $ or  $ R_{int} $), we use the reward-decoupled normalization (Liu et al., 2026), where the two reward components are standardized independently across the G samples before their advantages are summed with equal weight.



## 4 Experiments

### 4.1 Training Datasets

We construct RL training data from spoken dialogue corpora in which each speaker is recorded on a separate channel. To demonstrate that our method generalizes across corpora with different recording conditions, speaker populations, and conversational styles, we adopt two datasets that are complementary in these respects: Fisher (Cieri et al., 2004) and Seamless Interaction (Agrawal et al., 2025). The Fisher dataset contains a total of 2,000 h of recorded telephone conversations between random pairs of people. The Seamless dataset comprises two recording conditions, the Improvised subset contains 1,300 h audio of professional actors performing conversations based on improvised roles and emotions, while the Naturalistic subset contains 2,700 h audio of general participants engaging in natural, authentic conversation. We combined these two subsets together during training.

For each dataset, we apply the segment extraction procedure described in Section 3.3 to identify segments for the four interactivity axes by using Silero VAD (Team, 2024). We extract up to 2,000 segments per axis, using minimum utterance duration thresholds of  $ \tau_{\min} = 4.0 $ s for pause handling,  $ \tau_{\min} = 5.0 $ s for turn-taking and backchanneling, and  $ \tau_{\min} = 3.0 $ s for user interruption.

### 4.2 Evaluation Benchmarks

We evaluate the trained models from two complementary perspectives: (1) a static evaluation, in which pre-recorded audio are fed to the model, and (2) a dynamic evaluation, in which the model engages in real-time multi-turn dialogue with an automated conversational partner.

Full-Duplex-Bench v1 (Lin et al., 2025a) This benchmark provides a static evaluation of four axes of turn-taking behavior: pause handling, smooth turn-taking, backchanneling, and user interruption management. For each dimension, the benchmark provides pre-recorded input audio and applies automatic metrics to the model's generated speech. A metric shared across all four axes is the Takeover Rate (TOR), defined as the proportion of samples in which the model takes the turn and produces a prolonged utterance. In addition, the backchanneling axis evaluates backchannel frequency and

5

the Jensen–Shannon divergence (JSD) between the model’s backchannel timing and the ground-truth human timing distribution; the smooth turn-taking axis measures response latency; and the user interruption axis measures response latency as well as a GPT-4o (OpenAI et al., 2024) score that rates the contextual relevance of the model’s post-interruption response on a 0–5 scale. Because the four evaluation axes of this benchmark directly correspond to the interactivity axes targeted by our reward design, it serves as the primary benchmark for assessing the direct effect of RL training. We note that we corrected an issue in the official evaluation script for backchannling. $ ^{3} $

Full-Duplex-Bench v2 (Lin et al., 2026) This benchmark extends the evaluation to multi-turn, streaming settings by introducing an automated examiner that interacts with the model in real-time conversation. The examiner enforces staged conversational goals across four task families: Daily, Correction, Entity Tracking, and Safety. For each task, the benchmark reports turn-taking fluency and multi-turn instruction following; the Correction, Entity Tracking, and Safety tasks additionally include task-specific competence scores. We use GPT-Realtime $ ^{4} $ as the examiner and adopt the fast pacing mode with a maximum dialogue duration of 60 s. For automatic scoring, we use Gemini 2.5 Flash (Comanici et al., 2025) as the LLM judge. Details on the evaluation configuration and metric definitions are provided in Appendix B.2.

### 4.3 Models and Training Details

Base models We apply our method to two open-source full-duplex spoken dialogue models. The first is Moshi (Défossez et al., 2024), a 7B-parameter speech-text language model that jointly predicts text and audio token streams in an autoregressive manner. Following Hsiao et al. (2026), we prepend 3 s of silence to the input audio to allow time for Moshi to produce its conversation-initiating phrase before the user begins speaking.

The second is PersonaPlex (Roy et al., 2026), a recently proposed full-duplex spoken dialogue model. PersonaPlex extends Moshi with support for dialogue control via text prompt and voice cloning via audio prompts. For the text prompt, we use the standard prompt provided in the official code. $ ^{5} $ For the voice prompt, we supply a 3 s recording of a female speaker. The same prompts used at both RL training and inference time.



LLM Judge Reward For the response quality reward with LLMs, we first transcribe both the input and generated audio using the Parakeet TDT ASR model. $ ^{6} $ The resulting transcriptions are then scored by Qwen3-235B-A22B (Yang et al., 2025a) on a 1–3 scale for the contextual relevance and naturalness. The specific prompt for the LLM is provided in Figure 3 in the Appendix.

Training We train for 100 epochs, sampling 32 segments per epoch with  $ G = 16 $ completions each, distributed across 32 NVIDIA H100 GPUs. We use AdamW (Loshchilov and Hutter, 2018) with a learning rate of  $ 2 \times 10^{-7} $ and cosine scheduling. The KL penalty coefficient is  $ \beta = 0.01 $. To help the model generalize beyond the short segment boundaries, we prepend a randomly sampled context window to the input audio, with its maximum length linearly increased from 0 to 30 s over training. Further details are provided in Appendix A.

Comparison Models We include scores of three reference full-duplex models: dGSLM (Nguyen et al., 2023), Freeze-Omni (Wang et al., 2025b), and ASPIRin (Hsiao et al., 2026). The scores for dGSLM and Freeze-Omni are cited from the official benchmark repository (Lin et al., 2025a), and those for ASPIRin are cited from the original paper.

## 5 Results and Analysis

### 5.1 Results of Static Evaluation

Table 1 presents the Full-Duplex-Bench v1 results. Within both the Moshi and PersonaPlex families, RL training yields consistent improvements over the respective base models. $ ^{7} $ TOR of pause handling decreases substantially, while latency and TOR of turn-taking simultaneously improve. This joint improvement on these two competing axes indicates that the model has learned to better distinguish whether a given moment of

 $ ^{5} $https://github.com/NVIDIA/personaplex

 $ ^{3} $The official backchanneling script contained a bug in which the generated audio was not resampled to the VAD's expected sampling rate of 16 kHz.

 $ ^{6} $https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2

 $ ^{4} $https://openai.com/index/

 $ ^{7} $For the base PersonaPlex score, we were unable to reproduce the TOR of synthetic pause handling and latency of turn-taking reported by Roy et al. (2026) (0.358 and 0.170, respectively). We attribute this to differences in the voice prompt used during inference, whose specification is not publicly available, and report results using our own reproduction.

introducing-gpt-realtime/

6


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td style='text-align: center; word-wrap: break-word;'>Pause (Synthetic)</td><td style='text-align: center; word-wrap: break-word;'>Pause (Candor)</td><td colspan="3">Backchannel</td><td colspan="2">Smooth Turn Taking</td><td colspan="3">User Interruption</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TOR (↓)</td><td style='text-align: center; word-wrap: break-word;'>TOR (↓)</td><td style='text-align: center; word-wrap: break-word;'>TOR (↓)</td><td style='text-align: center; word-wrap: break-word;'>Freq (↑)</td><td style='text-align: center; word-wrap: break-word;'>JSD (↓)</td><td style='text-align: center; word-wrap: break-word;'>TOR (↑)</td><td style='text-align: center; word-wrap: break-word;'>Latency (↓)</td><td style='text-align: center; word-wrap: break-word;'>TOR (↑)</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o (↑)</td><td style='text-align: center; word-wrap: break-word;'>Latency (↓)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dGSLM $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>0.934</td><td style='text-align: center; word-wrap: break-word;'>0.935</td><td style='text-align: center; word-wrap: break-word;'>0.691</td><td style='text-align: center; word-wrap: break-word;'>0.015</td><td style='text-align: center; word-wrap: break-word;'>0.934</td><td style='text-align: center; word-wrap: break-word;'>0.975</td><td style='text-align: center; word-wrap: break-word;'>0.352</td><td style='text-align: center; word-wrap: break-word;'>0.917</td><td style='text-align: center; word-wrap: break-word;'>0.201</td><td style='text-align: center; word-wrap: break-word;'>2.531</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Freeze-Omni $ ^{\dagger} $</td><td style='text-align: center; word-wrap: break-word;'>0.642</td><td style='text-align: center; word-wrap: break-word;'>0.481</td><td style='text-align: center; word-wrap: break-word;'>0.636</td><td style='text-align: center; word-wrap: break-word;'>0.001</td><td style='text-align: center; word-wrap: break-word;'>0.997</td><td style='text-align: center; word-wrap: break-word;'>0.336</td><td style='text-align: center; word-wrap: break-word;'>0.953</td><td style='text-align: center; word-wrap: break-word;'>0.867</td><td style='text-align: center; word-wrap: break-word;'>3.615</td><td style='text-align: center; word-wrap: break-word;'>1.409</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Moshi</td><td style='text-align: center; word-wrap: break-word;'>0.445</td><td style='text-align: center; word-wrap: break-word;'>0.528</td><td style='text-align: center; word-wrap: break-word;'>0.255</td><td style='text-align: center; word-wrap: break-word;'>0.074</td><td style='text-align: center; word-wrap: break-word;'>0.824</td><td style='text-align: center; word-wrap: break-word;'>0.739</td><td style='text-align: center; word-wrap: break-word;'>0.162</td><td style='text-align: center; word-wrap: break-word;'>0.920</td><td style='text-align: center; word-wrap: break-word;'>3.440</td><td style='text-align: center; word-wrap: break-word;'>1.377</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>0.226</td><td style='text-align: center; word-wrap: break-word;'>0.417</td><td style='text-align: center; word-wrap: break-word;'>0.091</td><td style='text-align: center; word-wrap: break-word;'>0.095</td><td style='text-align: center; word-wrap: break-word;'>0.789</td><td style='text-align: center; word-wrap: break-word;'>0.966</td><td style='text-align: center; word-wrap: break-word;'>0.121</td><td style='text-align: center; word-wrap: break-word;'>1.000</td><td style='text-align: center; word-wrap: break-word;'>3.575</td><td style='text-align: center; word-wrap: break-word;'>0.461</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Seamless)</td><td style='text-align: center; word-wrap: break-word;'>0.307</td><td style='text-align: center; word-wrap: break-word;'>0.463</td><td style='text-align: center; word-wrap: break-word;'>0.145</td><td style='text-align: center; word-wrap: break-word;'>0.101</td><td style='text-align: center; word-wrap: break-word;'>0.794</td><td style='text-align: center; word-wrap: break-word;'>0.958</td><td style='text-align: center; word-wrap: break-word;'>0.160</td><td style='text-align: center; word-wrap: break-word;'>1.000</td><td style='text-align: center; word-wrap: break-word;'>3.630</td><td style='text-align: center; word-wrap: break-word;'>0.409</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ASPIRin $ ^{\ddagger} $</td><td style='text-align: center; word-wrap: break-word;'>0.482</td><td style='text-align: center; word-wrap: break-word;'>0.486</td><td style='text-align: center; word-wrap: break-word;'>—</td><td style='text-align: center; word-wrap: break-word;'>—</td><td style='text-align: center; word-wrap: break-word;'>—</td><td style='text-align: center; word-wrap: break-word;'>0.765</td><td style='text-align: center; word-wrap: break-word;'>0.273</td><td style='text-align: center; word-wrap: break-word;'>0.941</td><td style='text-align: center; word-wrap: break-word;'>3.734 $ ^{*} $</td><td style='text-align: center; word-wrap: break-word;'>0.992</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>PersonaPlex</td><td style='text-align: center; word-wrap: break-word;'>0.482</td><td style='text-align: center; word-wrap: break-word;'>0.444</td><td style='text-align: center; word-wrap: break-word;'>0.182</td><td style='text-align: center; word-wrap: break-word;'>0.046</td><td style='text-align: center; word-wrap: break-word;'>0.841</td><td style='text-align: center; word-wrap: break-word;'>0.958</td><td style='text-align: center; word-wrap: break-word;'>0.219</td><td style='text-align: center; word-wrap: break-word;'>0.940</td><td style='text-align: center; word-wrap: break-word;'>4.500</td><td style='text-align: center; word-wrap: break-word;'>0.271</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>0.328</td><td style='text-align: center; word-wrap: break-word;'>0.361</td><td style='text-align: center; word-wrap: break-word;'>0.127</td><td style='text-align: center; word-wrap: break-word;'>0.122</td><td style='text-align: center; word-wrap: break-word;'>0.783</td><td style='text-align: center; word-wrap: break-word;'>0.950</td><td style='text-align: center; word-wrap: break-word;'>0.079</td><td style='text-align: center; word-wrap: break-word;'>1.000</td><td style='text-align: center; word-wrap: break-word;'>4.520</td><td style='text-align: center; word-wrap: break-word;'>0.187</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Seamless)</td><td style='text-align: center; word-wrap: break-word;'>0.350</td><td style='text-align: center; word-wrap: break-word;'>0.356</td><td style='text-align: center; word-wrap: break-word;'>0.073</td><td style='text-align: center; word-wrap: break-word;'>0.112</td><td style='text-align: center; word-wrap: break-word;'>0.786</td><td style='text-align: center; word-wrap: break-word;'>0.975</td><td style='text-align: center; word-wrap: break-word;'>0.086</td><td style='text-align: center; word-wrap: break-word;'>0.995</td><td style='text-align: center; word-wrap: break-word;'>4.533</td><td style='text-align: center; word-wrap: break-word;'>0.223</td></tr></table>

<div style="text-align: center;">Table 1: Full-Duplex-Bench v1 results. Best scores across all models are shown in \textbf{bold}; best scores within each model family (Moshi / PersonaPlex) are \underline{underlined}. \textsuperscript{†}Scores cited from the official repository of the benchmark (Lin et al., 2025a). \textsuperscript{‡}Scores cited from Hsiao et al. (2026); backchannel scores are omitted as they were evaluated before the bug fix (see Section 4.2 for details). *ASPIRin's GPT-4o score was evaluated on a 1–5 scale in the original paper, whereas the official benchmark configuration uses a 0–5 scale adopted by all other models; these scores are therefore not directly comparable.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="2">Daily</td><td colspan="3">Correction</td><td colspan="3">Entity Tracking</td><td colspan="3">Safety</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Instruct</td><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Instruct</td><td style='text-align: center; word-wrap: break-word;'>Task</td><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Instruct</td><td style='text-align: center; word-wrap: break-word;'>Task</td><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Instruct</td><td style='text-align: center; word-wrap: break-word;'>Task</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Moshi</td><td style='text-align: center; word-wrap: break-word;'>3.284</td><td style='text-align: center; word-wrap: break-word;'>2.221</td><td style='text-align: center; word-wrap: break-word;'>3.248</td><td style='text-align: center; word-wrap: break-word;'>2.189</td><td style='text-align: center; word-wrap: break-word;'>2.340</td><td style='text-align: center; word-wrap: break-word;'>3.951</td><td style='text-align: center; word-wrap: break-word;'>2.537</td><td style='text-align: center; word-wrap: break-word;'>2.440</td><td style='text-align: center; word-wrap: break-word;'>3.839</td><td style='text-align: center; word-wrap: break-word;'>2.831</td><td style='text-align: center; word-wrap: break-word;'>2.720</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>3.397</td><td style='text-align: center; word-wrap: break-word;'>2.502</td><td style='text-align: center; word-wrap: break-word;'>3.957</td><td style='text-align: center; word-wrap: break-word;'>2.706</td><td style='text-align: center; word-wrap: break-word;'>2.820</td><td style='text-align: center; word-wrap: break-word;'>4.110</td><td style='text-align: center; word-wrap: break-word;'>2.626</td><td style='text-align: center; word-wrap: break-word;'>2.640</td><td style='text-align: center; word-wrap: break-word;'>3.858</td><td style='text-align: center; word-wrap: break-word;'>3.058</td><td style='text-align: center; word-wrap: break-word;'>2.820</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Seamless)</td><td style='text-align: center; word-wrap: break-word;'>3.442</td><td style='text-align: center; word-wrap: break-word;'>2.615</td><td style='text-align: center; word-wrap: break-word;'>4.003</td><td style='text-align: center; word-wrap: break-word;'>2.895</td><td style='text-align: center; word-wrap: break-word;'>3.300</td><td style='text-align: center; word-wrap: break-word;'>3.965</td><td style='text-align: center; word-wrap: break-word;'>2.609</td><td style='text-align: center; word-wrap: break-word;'>2.740</td><td style='text-align: center; word-wrap: break-word;'>4.161</td><td style='text-align: center; word-wrap: break-word;'>3.503</td><td style='text-align: center; word-wrap: break-word;'>3.440</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>PersonaPlex</td><td style='text-align: center; word-wrap: break-word;'>3.327</td><td style='text-align: center; word-wrap: break-word;'>2.861</td><td style='text-align: center; word-wrap: break-word;'>3.803</td><td style='text-align: center; word-wrap: break-word;'>2.945</td><td style='text-align: center; word-wrap: break-word;'>3.080</td><td style='text-align: center; word-wrap: break-word;'>3.748</td><td style='text-align: center; word-wrap: break-word;'>3.130</td><td style='text-align: center; word-wrap: break-word;'>3.200</td><td style='text-align: center; word-wrap: break-word;'>3.841</td><td style='text-align: center; word-wrap: break-word;'>3.596</td><td style='text-align: center; word-wrap: break-word;'>3.260</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>3.627</td><td style='text-align: center; word-wrap: break-word;'>2.915</td><td style='text-align: center; word-wrap: break-word;'>3.840</td><td style='text-align: center; word-wrap: break-word;'>3.026</td><td style='text-align: center; word-wrap: break-word;'>3.500</td><td style='text-align: center; word-wrap: break-word;'>4.055</td><td style='text-align: center; word-wrap: break-word;'>3.562</td><td style='text-align: center; word-wrap: break-word;'>3.700</td><td style='text-align: center; word-wrap: break-word;'>3.695</td><td style='text-align: center; word-wrap: break-word;'>3.288</td><td style='text-align: center; word-wrap: break-word;'>3.000</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Seamless)</td><td style='text-align: center; word-wrap: break-word;'>4.017</td><td style='text-align: center; word-wrap: break-word;'>3.197</td><td style='text-align: center; word-wrap: break-word;'>4.501</td><td style='text-align: center; word-wrap: break-word;'>3.369</td><td style='text-align: center; word-wrap: break-word;'>3.620</td><td style='text-align: center; word-wrap: break-word;'>4.647</td><td style='text-align: center; word-wrap: break-word;'>4.059</td><td style='text-align: center; word-wrap: break-word;'>3.840</td><td style='text-align: center; word-wrap: break-word;'>4.511</td><td style='text-align: center; word-wrap: break-word;'>3.780</td><td style='text-align: center; word-wrap: break-word;'>3.280</td></tr></table>

<div style="text-align: center;">Table 2: Full-Duplex-Bench v2 results on multi-turn dialogues with GPT-Realtime. For each task, turn-taking fluency (Turn), instruction-following (Instruct), and task-specific scores (Task) are evaluated by Gemini 2.5 Flash on a 1–5 scale. Best scores across all models are shown in bold; best scores within each model family are underlined.</div>


user silence signals a mid-utterance pause or a turn yield. Backchanneling also improves across all three metrics, indicating that the model produces more backchannels at more appropriate timings. For user interruption, both RL variants improved latency and GPT-4o semantic scores. Notably, ASPIRin (Hsiao et al., 2026) reports that its GPT-4o score decreases from the base Moshi model's 3.89 to 3.73 (on a 1–5 scale, differing from the benchmark's 0–5 scale). In contrast, our method improves this score, demonstrating the effectiveness of incorporating an LLM-based reward to preserve and enhance content quality during alignment.

Comparing models, the RL-trained models of Moshi and PersonaPlex achieve the best or nearbest scores on all metrics. Among the baselines, dGSLM achieves the highest turn-taking TOR, at the cost of poor pause handling, i.e. it treats almost all user silences as turn yields and responds immediately. Our method achieves comparable turn-taking TORs while simultaneously reducing pause handling TOR, showing that high turn-taking responsiveness and accurate pause handling can coexist when all interactivity axes are jointly optimized. We confirmed that the perceptual quality of the generated speech is not degraded, as measured by UTMOSv2 (Baba et al., 2024) (see Appendix C).



### 5.2 Results of Interactive Evaluation

Table 2 presents the results on Full-Duplex-Bench v2, which evaluates models through real-time multi-turn dialogues with GPT-Realtime. Across both model families, our method consistently improves turn-taking fluency over the base models in all four tasks. Beyond turn-taking, instruction-following and task-specific scores also improve in most conditions, suggesting that the LLM-based reward also effectively prevents content degradation in dynamic multi-turn interactions.

Comparing both training sets, Seamless yields stronger improvements than Fisher across both model families. We attribute this to the greater variety and more consistent dialogue structure of the Seamless dataset, which may provide richer learning signals for multi-turn interaction. PersonaPlex trained on Seamless gets the best scores across

7

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Model</th><th style='text-align: center;'>Key Feature</th><th style='text-align: center;'>Value</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>GPT</td><td style='text-align: center;'>Hey, I'd like to place an order to print and copy...</td><td style='text-align: center;'>0.76 s</td></tr>
    <tr><td style='text-align: center;'>Moshi+RL</td><td style='text-align: center;'>Sure, just let me know how many copies and...</td><td style='text-align: center;'>0.08 s</td></tr>
    <tr><td style='text-align: center;'>Understood, I'll need to check if our printer can print in black...</td><td style='text-align: center;'>Sure, that's fine... I'd like them...</td><td style='text-align: center;'>0.08 s</td></tr>
    <tr><td style='text-align: center;'>Okay</td><td style='text-align: center;'>I'll do my best to get it done for...</td><td style='text-align: center;'>0.08 s</td></tr>
    <tr><td style='text-align: center;'>Great. Can you give me a qu...</td><td style='text-align: center;'>Yes</td><td style='text-align: center;'>0.08 s</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 2: Example of a conversation between GPT-Realtime (Examiner) and Moshi + RL in the Daily task of Full-Duplex-Bench v2. Arrows highlight turn-taking transitions with their latencies, and boxes mark backchannelings. Turn-taking fluency and instruction-following scores are 4.80 and 2.60, respectively.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td style='text-align: center; word-wrap: break-word;'>Pause</td><td style='text-align: center; word-wrap: break-word;'>BC</td><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Interrupt</td><td colspan="2">Daily</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TOR  $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>JSD</td><td style='text-align: center; word-wrap: break-word;'>Latency  $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o</td><td style='text-align: center; word-wrap: break-word;'>Turn</td><td style='text-align: center; word-wrap: break-word;'>Instruct</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>0.42</td><td style='text-align: center; word-wrap: break-word;'>0.79</td><td style='text-align: center; word-wrap: break-word;'>0.12</td><td style='text-align: center; word-wrap: break-word;'>3.58</td><td style='text-align: center; word-wrap: break-word;'>3.40</td><td style='text-align: center; word-wrap: break-word;'>2.50</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o  $ \mathcal{D}_{pause} $</td><td style='text-align: center; word-wrap: break-word;'>0.74</td><td style='text-align: center; word-wrap: break-word;'>0.77</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>3.66</td><td style='text-align: center; word-wrap: break-word;'>3.14</td><td style='text-align: center; word-wrap: break-word;'>2.32</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o  $ \mathcal{D}_{turn} $</td><td style='text-align: center; word-wrap: break-word;'>0.29</td><td style='text-align: center; word-wrap: break-word;'>0.79</td><td style='text-align: center; word-wrap: break-word;'>0.30</td><td style='text-align: center; word-wrap: break-word;'>3.28</td><td style='text-align: center; word-wrap: break-word;'>3.41</td><td style='text-align: center; word-wrap: break-word;'>2.46</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o  $ \mathcal{D}_{bc} $</td><td style='text-align: center; word-wrap: break-word;'>0.47</td><td style='text-align: center; word-wrap: break-word;'>0.83</td><td style='text-align: center; word-wrap: break-word;'>0.22</td><td style='text-align: center; word-wrap: break-word;'>3.67</td><td style='text-align: center; word-wrap: break-word;'>3.61</td><td style='text-align: center; word-wrap: break-word;'>2.39</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o  $ \mathcal{D}_{int} $</td><td style='text-align: center; word-wrap: break-word;'>0.39</td><td style='text-align: center; word-wrap: break-word;'>0.78</td><td style='text-align: center; word-wrap: break-word;'>0.14</td><td style='text-align: center; word-wrap: break-word;'>3.42</td><td style='text-align: center; word-wrap: break-word;'>3.28</td><td style='text-align: center; word-wrap: break-word;'>2.24</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o  $ R_{llm} $</td><td style='text-align: center; word-wrap: break-word;'>0.48</td><td style='text-align: center; word-wrap: break-word;'>0.78</td><td style='text-align: center; word-wrap: break-word;'>0.17</td><td style='text-align: center; word-wrap: break-word;'>3.05</td><td style='text-align: center; word-wrap: break-word;'>3.00</td><td style='text-align: center; word-wrap: break-word;'>2.18</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o sched</td><td style='text-align: center; word-wrap: break-word;'>0.51</td><td style='text-align: center; word-wrap: break-word;'>0.78</td><td style='text-align: center; word-wrap: break-word;'>0.15</td><td style='text-align: center; word-wrap: break-word;'>3.70</td><td style='text-align: center; word-wrap: break-word;'>3.50</td><td style='text-align: center; word-wrap: break-word;'>2.41</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>w/o context</td><td style='text-align: center; word-wrap: break-word;'>0.49</td><td style='text-align: center; word-wrap: break-word;'>0.78</td><td style='text-align: center; word-wrap: break-word;'>0.09</td><td style='text-align: center; word-wrap: break-word;'>3.53</td><td style='text-align: center; word-wrap: break-word;'>3.33</td><td style='text-align: center; word-wrap: break-word;'>2.21</td></tr></table>

<div style="text-align: center;">Table 3: Ablation study of Moshi trained on Fisher. “Pause” through “Interrupt” are results from Full-Duplex-Bench v1 (Pause uses the Candor subset), and “Daily” shows multi-turn dialogue evaluation results from the Daily task in Full-Duplex-Bench v2. “w/o sched” denotes training without the scheduling of the maximum context length, always using 30 s of context, and “w/o context” denotes training without any context.</div>


nearly all metrics, benefiting from its strong baseline semantic quality and the diverse training data.

Interestingly, using Fisher lead to a decline in instruction-following and task-specific scores on the Safety task for PersonaPlex, and subpar improvements for Moshi. The cooperative and casual interaction style of the Fisher telephone conversations may overwrite the base model's safety-oriented behavior (see Appendix D.2 for case studies). Using Seamless does not exhibit this degradation, supporting its suitability as a training corpus.

### 5.3 Ablations

Table 3 reports the ablation results on Moshi + RL. w/o  $ \mathcal{D}_{\text{pause}} $ and w/o  $ \mathcal{D}_{\text{turn}} $ reveals a clear trade-off between the two axes: without the training examples on pause handling, the model learns to speak at every opportunity, yielding the lowest turn-taking latency; conversely, without data on turn-taking, the model becomes overly conservative, resulting in substantially higher latency. Training with both rewards jointly enables the model to strike an appropriate balance. Removing the backchannel reward (w/o  $ \mathcal{D}_{\text{bc}} $) yields the worst JS divergence score w.r.t. the ground truth distribution, suggesting that the models failed to learn producing backchannels at appropriate timing. Removing LLM Judge reward (without  $ R_{\text{llm}} $) leads to the largest degradation across nearly all metrics, confirming that the reward is essential for preserving the semantic quality of generated utterances alongside interactivity improvements. Finally, removing the context window (w/o context) particularly hurts the turn-taking fluency and instruction-following scores on the interactive evaluation, indicating that even though training operates on short segments, providing preceding context is important for generalization to longer, multi-turn dialogues.



### 5.4 Case Study

Figure 2 shows a dialogue example between Moshi + RL, trained on Fisher, and GPT-realtime on Full-Duplex-Bench v2. Unlike the original Moshi, which exhibited long response delays and longer speech overlap (see Appendix D.1 for details), Moshi + RL demonstrated smooth turn transitions and well-timed backchanneling. These improvements in interactivity are consistent with the benchmark gains reported in Sections 5.1 and 5.1.

## 6 Conclusion

In this work, we proposed an RL-based posttraining method that comprehensively improves the interactivity of full-duplex spoken dialogue models. We automatically extracted training segments corresponding to four axes of interactivity, including pause handling, turn-taking, backchanneling, and user interruption, from real human conversations. We then optimized two models, Moshi and PersonaPlex, with axis-specific rule-based rewards and an LLM-judge-based semantic reward. Our method outperformed the baselines on both the

8

evaluation with pre-recorded static input and the multi-turn interaction. Future directions include integrating rewards for intelligence aspects such as instruction-following and reasoning, as well as evaluation through actual interactions with humans.

## Limitations

Our work has several limitations. First, the rule-based reward design for each interactivity axis requires manual engineering effort and may overlook other aspects of conversational dynamics. As the number of axes grows, this approach becomes increasingly difficult to scale. Future work should explore data-driven and scalable reward modeling, such as leveraging spoken language models as reward models (Ji et al., 2025; Chen et al., 2026b).

Second, our method optimizes the text token stream that the model generates in parallel with the audio stream. This design choice is motivated by the fact that the text stream controls not only the content of utterances but also their timing and duration. Although many current full-duplex models do produce a parallel text stream, our approach is not directly applicable to those that do not, and extending our method to such architectures remains a possible direction.

Third, our evaluation relies entirely on automated methods, including dialogues with GPT-Realtime and LLM-based judgment. While these metrics have been shown to correlate with human judgments to a reasonable degree (Lin et al., 2026), they may fail to capture certain aspects of conversational quality that only human evaluators can assess. We plan to conduct human evaluation in future work.

Finally, optimizing interactivity through RL can inadvertently degrade the model's safety behavior. As shown in our analysis (Appendix D.2), training on the Fisher dataset led to a decline in safety scores, as the cooperative interaction style of the training data conflicted with the ability to refuse or redirect harmful requests. More broadly, improving the fluency and responsiveness of full-duplex dialogue models may increase the risk of generating inappropriate or harmful content. Incorporating safety-aware rewards or constraints into the RL process is an important direction for future work.

## References

Vasu Agrawal, Akinniyi Akinyemi, Kathryn Alvero, Morteza Behrooz, Julia Buffaloini, Fabio Maria

Carlucci, Joy Chen, Junming Chen, Zhang Chen, Shiyang Cheng, Praveen Chowdary, Joe Chuang, Antony D'Avirro, Jon Daly, Ning Dong, Mark Duppenthaler, Cynthia Gao, Jeff Girard, Martin Gleize, and 65 others. 2025. Seamless Interaction: Dyadic Audiovisual Motion Modeling and Large-Scale Dataset. arXiv preprint arXiv:2506.22554.

Siddhant Arora, Kai-Wei Chang, Chung-Ming Chien, Yifan Peng, Haibin Wu, Yossi Adi, Emmanuel Dupoux, Hung-Yi Lee, Karen Livescu, and Shinji Watanabe. 2026a. On The Landscape of Spoken Language Models: A Comprehensive Survey. arXiv preprint arXiv:2504.08528.

Siddhant Arora, Zhiyun Lu, Chung-Cheng Chiu, Ruoming Pang, and Shinji Watanabe. 2024. Talking Turns: Benchmarking Audio Foundation Models on Turn-Taking Dynamics. In Proceedings of the Thirteenth International Conference on Learning Representations.

Siddhant Arora, Jinchuan Tian, Jiatong Shi, Hayato Futami, Yosuke Kashiwagi, Emiru Tsunoo, and Shinji Watanabe. 2026b. Optimizing Conversational Quality in Spoken Dialogue Systems with Reinforcement Learning from AI Feedback. arXiv preprint arXiv:2601.19063.

Kaito Baba, Wataru Nakata, Yuki Saito, and Hiroshi Saruwatari. 2024. The T05 System for the voicemos challenge 2024: Transfer Learning from Deep Image Classifier to Naturalness MOS Prediction of High-Quality Synthetic Speech. In Proceedings of the 2024 IEEE Spoken Language Technology Workshop, pages 818–824.

Kai-Wei Chang, En-Pei Hu, Chun-Yi Kuan, Wenze Ren, Wei-Chih Chen, Guan-Ting Lin, Yu Tsao, Shao-Hua Sun, Hung-yi Lee, and James Glass. 2026. Gametime: Evaluating temporal dynamics in spoken language models. In Proceedings of the 2026 IEEE International Conference on Acoustics, Speech and Signal Processing, pages 16302–16306.

Chen Chen, Ke Hu, Chao-Han Huck Yang, Ankita Pasad, Edresson Casanova, Weiqing Wang, Szu-Wei Fu, Jason Li, Zhehuai Chen, Jagadeesh Balam, and Boris Ginsburg. 2025a. Reinforcement Learning Enhanced Full-Duplex Spoken Dialogue Language Models for Conversational Interactions. In Proceedings of the Second Conference on Language Modeling.

Qian Chen, Yafeng Chen, Yanni Chen, Mengzhe Chen, Yingda Chen, Chong Deng, Zhihao Du, Ruize Gao, Changfeng Gao, Zhifu Gao, Yabin Li, Xiang Lv, Jiaqing Liu, Haoneng Luo, Bin Ma, Chongjia Ni, Xian Shi, Jialong Tang, Hui Wang, and 17 others. 2025b. MinMo: A Multimodal Large Language Model for Seamless Voice Interaction. arXiv preprint arXiv:2501.06282.

Yifu Chen, Shengpeng Ji, Qian Chen, Tianle Liang, Yangzhuo Li, Ziqing Wang, Wen Wang, Jingyu Lu,

9

Haoxiao Wang, Xueyi Pu, Fan Zhuo, and Zhou Zhao. 2026a. WavAlign: Enhancing Intelligence and Expressiveness in Spoken Dialogue Models via Adaptive Hybrid Post-Training. arXiv preprint arXiv:2604.14932.

Yifu Chen, Shengpeng Ji, Zhengqing Liu, Qian Chen, Wen Wang, Ziqing Wang, Yangzhuo Li, Tianle Liang, and Zhou Zhao. 2026b. Dual-Axis Generative Reward Model Toward Semantic and Turn-taking Robustness in Interactive Spoken Dialogue Models. arXiv preprint arXiv:2604.14920.

Christopher Cieri, David Miller, and Kevin Walker. 2004. The Fisher Corpus: A Resource for the Next Generations of Speech-to-Text. In Proceedings of the Fourth International Conference on Language Resources and Evaluation.

Gheorghe Comanici, Eric Bieber, Mike Schaekermann, Ice Pasupat, Noveen Sachdeva, Inderjit Dhillon, Marcel Blistein, Ori Ram, Dan Zhang, Evan Rosen, Luke Marris, Sam Petulla, Colin Gaffney, Asaf Aharoni, Nathan Lintz, Tiago Cardal Pais, Henrik Jacobsson, Idan Szpektor, Nan-Jiang Jiang, and 3416 others. 2025. Gemini 2.5: Pushing the Frontier with Advanced Reasoning, Multimodality, Long Context, and Next Generation Agentic Capabilities. arXiv preprint arXiv:2507.06261.

Alexandre Défossez, Laurent Mazaré, Manu Orsini, Amélie Royer, Patrick Pérez, Hervé Jégou, Edouard Grave, and Neil Zeghidour. 2024. Moshi: A speech-text foundation model for real-time dialogue. arXiv preprint arXiv:2410.00037.

Erik Ekstedt and Gabriel Skantze. 2022. Voice Activity Projection: Self-supervised Learning of Turn-taking Events. In Proceeding of Interspeech 2022, pages 5190–5194.

Qingkai Fang, Shoutao Guo, Yan Zhou, Zhengrui Ma, Shaolei Zhang, and Yang Feng. 2024. LLaMA-Omni: Seamless Speech Interaction with Large Language Models. In Proceedings of the Thirteenth International Conference on Learning Representations.

Chaoyou Fu, Haojia Lin, Zuwei Long, Yunhang Shen, Yuhang Dai, Meng Zhao, Yi-Fan Zhang, Shaoqi Dong, Yangze Li, Xiong Wang, Haoyu Cao, Di Yin, Long Ma, Xiawu Zheng, Rongrong Ji, Yunsheng Wu, Ran He, Caifeng Shan, and Xing Sun. 2025. VITA: Towards Open-Source Interactive Omni Multimodal LLM. arXiv preprint arXiv:2408.05211.

Yuan Ge, Saihan Chen, Jingqi Xiao, Xiaoqian Liu, Tong Xiao, Yan Xiang, Zhengtao Yu, and Jingbo Zhu. 2025. FLEXI: Benchmarking Full-duplex Human-LLM Speech Interaction. arXiv preprint arXiv:2509.22243.

Mattias Heldner and Jens Edlund. 2010. Pauses, gaps and overlaps in conversations. Journal of Phonetics, 38(4):555–568.

Chi-Yuan Hsiao, Ke-Han Lu, Yu-Kuan Fu, Guanting Lin, Hsiao-Tsung Hung, and Hung-yi Lee. 2026. ASPIRin: Action Space Projection for Interactivity-Optimized Reinforcement Learning in Full-Duplex Speech Language Models. arXiv preprint arXiv:2604.10065.

Ke Hu, Ehsan Hosseini-Asl, Chen Chen, Edresson Casanova, Subhankar Ghosh, Piotr Żelasko, Zhehuai Chen, Jason Li, Jagadeesh Balam, and Boris Ginsburg. 2025. Efficient and Direct Duplex Modeling for Speech-to-Speech Language Model. In Proceeding of Interspeech 2025, pages 2715–2719.

Shengpeng Ji, Yifu Chen, Minghui Fang, Jialong Zuo, Jingyu Lu, Hanting Wang, Ziyue Jiang, Long Zhou, Shujie Liu, Xize Cheng, Xiaoda Yang, Zehan Wang, Qian Yang, Jian Li, Yidi Jiang, Jingzhen He, Yunfei Chu, Jin Xu, and Zhou Zhao. 2024. WavChat: A Survey of Spoken Dialogue Models. arXiv preprint arXiv:2411.13577.

Shengpeng Ji, Tianle Liang, Yangzhuo Li, Jialong Zuo, Minghui Fang, Jinzheng He, Yifu Chen, Zhengqing Liu, Ziyue Jiang, Xize Cheng, Siqi Zheng, Jin Xu, Junyang Lin, and Zhou Zhao. 2025. WavReward: Spoken Dialogue Models With Generalist Reward Evaluators. arXiv preprint arXiv:2505.09558.

Borui Liao, Yulong Xu, Jiao Ou, Kaiyuan Yang, Weihua Jian, Pengfei Wan, and Di Zhang. 2025. FlexDuo: A Pluggable System for Enabling Full-Duplex Capabilities in Speech Dialogue Systems. arXiv preprint arXiv:2502.13472.

Guan-Ting Lin, Shih-Yun Shan Kuan, Jiatong Shi, Kai-Wei Chang, Siddhant Arora, Shinji Watanabe, and Hung-yi Lee. 2026. Full-Duplex-Bench-v2: A Multi-Turn Evaluation Framework for Duplex Dialogue Systems with an Automated Examiner. arXiv preprint arXiv:2510.07838.

Guan-Ting Lin, Jiachen Lian, Tingle Li, Qirui Wang, Gopala Anumanchipalli, Alexander H. Liu, and Hung-yi Lee. 2025a. Full-Duplex-Bench: A Benchmark to Evaluate Full-duplex Spoken Dialogue Models on Turn-taking Capabilities. arXiv preprint arXiv:2503.04721.

Guan-Ting Lin, Prashanth Gurunath Shivakumar, Aditya Gourav, Yile Gu, Ankur Gandhe, Hung-yi Lee, and Ivan Bulyko. 2025b. Align-SLM: Textless Spoken Language Models with Reinforcement Learning from AI Feedback. In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics, pages 20395–20411.

Shih-Yang Liu, Xin Dong, Ximing Lu, Shizhe Diao, Peter Belcak, Mingjie Liu, Min-Hung Chen, Hongxu Yin, Yu-Chiang Frank Wang, Kwang-Ting Cheng, Yejin Choi, Jan Kautz, and Pavlo Molchanov. 2026. GDPO: Group reward-Decoupled Normalization Policy Optimization for Multi-reward RL Optimization. arXiv preprint arXiv:2601.05242.

10

Ilya Loshchilov and Frank Hutter. 2018. Decoupled Weight Decay Regularization. In Proceedings of the Sixth International Conference on Learning Representations.

Tu Anh Nguyen, Eugene Kharitonov, Jade Copet, Yossi Adi, Wei-Ning Hsu, Ali Elkahky, Paden Tomasello, Robin Algayres, Benoit Sagot, Abdelrahman Mohamed, and Emmanuel Dupoux. 2023. Generative Spoken Dialogue Language Modeling. Transactions of the Association for Computational Linguistics, 11:250–266.

OpenAI, Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyam Anadkat, Red Avila, Igor Babuschkin, Suchir Balaji, Valerie Balcom, Paul Baltescu, Haiming Bao, Mohammad Bavarian, Jeff Belgium, and 262 others. 2024. GPT-4 Technical Report. arXiv preprint arXiv:2303.08774.

Long Ouyang, Jeffrey Wu, Xu Jiang, Diogo Almeida, Carroll Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Gray, John Schulman, Jacob Hilton, Fraser Kelton, Luke Miller, Maddie Simens, Amanda Askell, Peter Welinder, Paul Christiano, Jan Leike, and Ryan Lowe. 2022. Training language models to follow instructions with human feedback. In Proceedings of the Advances in Neural Information Processing Systems.

Yizhou Peng, Yi-Wen Chao, Dianwen Ng, Yukun Ma, Chongjia Ni, Bin Ma, and Eng Siong Chng. 2025. FD-Bench: A Full-Duplex Benchmarking Pipeline Designed for Full Duplex Spoken Dialogue Systems. In Interspeech 2025, pages 176–180.

Rafael Rafailov, Archit Sharma, Eric Mitchell, Christopher D. Manning, Stefano Ermon, and Chelsea Finn. 2023. Direct Preference Optimization: Your Language Model is Secretly a Reward Model. In Proceedings of the Thirty-seventh Conference on Neural Information Processing Systems.

Rajarshi Roy, Jonathan Raiman, Sang-gil Lee, Teodor-Dumitru Ene, Robert Kirby, Sungwon Kim, Jae-hyeon Kim, and Bryan Catanzaro. 2026. PersonaPlex: Voice and Role Control for Full Duplex Conversational Speech Models. arXiv preprint arXiv:2602.06053.

John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, and Oleg Klimov. 2017. Proximal Policy Optimization Algorithms. arXiv preprint arXiv:1707.06347.

Zhihong Shao, Peiyi Wang, Qihao Zhu, Runxin Xu, Junxiao Song, Xiao Bi, Haowei Zhang, Mingchuan Zhang, Y. K. Li, Y. Wu, and Daya Guo. 2024. DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv preprint arXiv:2402.03300.

Yemin Shi, Yu Shu, Siwei Dong, Guangyi Liu, Jaward Sesay, Jingwen Li, and Zhiting Hu. 2025. Voila:

Voice-Language Foundation Models for Real-Time Autonomous Interaction and Voice Role-Play. arXiv preprint arXiv:2505.02707.

Nisan Stiennon, Long Ouyang, Jeffrey Wu, Daniel Ziegler, Ryan Lowe, Chelsea Voss, Alec Radford, Dario Amodei, and Paul F Christiano. 2020. Learning to summarize with human feedback. In Proceedings of the Thirty-fourth Advances in Neural Information Processing Systems, volume 33, pages 3008–3021.

Silero Team. 2024. Silero VAD: Pre-trained enterprise-grade voice activity detector (VAD), number detector and language classifier.

Bandhav Veluri, Benjamin N Peloquin, Bokai Yu, Hongyu Gong, and Shyamnath Gollakota. 2024. Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents. In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, pages 21390–21402.

Peng Wang, Songshuo Lu, Yaohua Tang, Sijie Yan, Wei Xia, and Yuanjun Xiong. 2024. A Full-duplex Speech Dialogue Scheme Based On Large Language Model. In Proceedings of the Thirty-eighth Annual Conference on Neural Information Processing Systems.

Qichao Wang, Ziqiao Meng, Wenqian Cui, Yifei Zhang, Pengcheng Wu, Bingzhe Wu, Irwin King, Liang Chen, and Peilin Zhao. 2025a. NTPP: Generative Speech Language Modeling for Dual-Channel Spoken Dialogue via Next-Token-Pair Prediction. In Proceedings of the Forty-second International Conference on Machine Learning.

Xiong Wang, Yangze Li, Chaoyou Fu, Yike Zhang, Yunhang Shen, Lei Xie, Ke Li, Xing Sun, and Long Ma. 2025b. Freeze-Omni: A Smart and Low Latency Speech-to-speech Dialogue Model with Frozen LLM. In Proceedings of the Forty-second International Conference on Machine Learning.

Ronald J. Williams. 1992. Simple statistical gradient-following algorithms for connectionist reinforcement learning. Machine Learning, 8(3):229–256.

Anne Wu, Laurent Mazaré, Neil Zeghidour, and Alexandre Défossez. 2025a. Aligning Spoken Dialogue Models from User Interactions. In Proceedings of the Forty-second International Conference on Machine Learning.

Boyong Wu, Chao Yan, Chen Hu, Cheng Yi, Chengli Feng, Fei Tian, Feiyu Shen, Gang Yu, Haoyang Zhang, Jingbei Li, Mingrui Chen, Peng Liu, Wang You, Xiangyu Tony Zhang, Xingyuan Li, Xuerui Yang, Yayue Deng, Yechang Huang, Yuxin Li, and 90 others. 2025b. Step-Audio 2 Technical Report. arXiv preprint arXiv:2507.16632.

Jin Xu, Zhifang Guo, Jinzheng He, Hangrui Hu, Ting He, Shuai Bai, Keqin Chen, Jialin Wang, Yang Fan, Kai Dang, Bin Zhang, Xiong Wang, Yunfei Chu,

11

and Junyang Lin. 2025. Qwen2.5-Omni Technical Report. arXiv preprint arXiv:2503.20215.

An Yang, Anfeng Li, Baosong Yang, Beichen Zhang, Binyuan Hui, Bo Zheng, Bowen Yu, Chang Gao, Chengen Huang, Chenxu Lv, Chujie Zheng, Dayiheng Liu, Fan Zhou, Fei Huang, Feng Hu, Hao Ge, Haoran Wei, Huan Lin, Jialong Tang, and 41 others. 2025a. Qwen3 Technical Report. arXiv preprint arXiv:2505.09388.

Shu-wen Yang, Ming Tu, Andy T. Liu, Xinghua Qu, Hung-yi Lee, Lu Lu, Yuxuan Wang, and Yonghui Wu. 2025b. ParaS2S: Benchmarking and Aligning Spoken Language Models for Paralinguistic-aware Speech-to-Speech Interaction. In Proceedings of the Fourteenth International Conference on Learning Representations.

Yiqun Yao, Xiang Li, Xin Jiang, Xuezhi Fang, Naitong Yu, Wenjia Ma, Aixin Sun, and Yequan Wang. 2026. FLM-Audio: Natural Monologues Improves Native Full-Duplex Chatbots via Dual Training. arXiv preprint arXiv:2509.02521.

Wenyi Yu, Siyin Wang, Xiaoyu Yang, Xianzhao Chen, Xiaohai Tian, Jun Zhang, Guangzhi Sun, Lu Lu, Yuxuan Wang, and Chao Zhang. 2025. SALMONNomni: A Standalone Speech LLM without CodecInjection for Full-duplex Conversation. In Proceedings of the Thirty-ninth Annual Conference on Neural Information Processing Systems.

Dong Zhang, Shimin Li, Xin Zhang, Jun Zhan, Pengyu Wang, Yaqian Zhou, and Xipeng Qiu. 2023. SpeechGPT: Empowering Large Language Models with Intrinsic Cross-Modal Conversational Abilities. In Findings of the Association for Computational Linguistics: EMNLP 2023, pages 15757–15773.

Dong Zhang, Zhaowei Li, Shimin Li, Xin Zhang, Pengyu Wang, Yaqian Zhou, and Xipeng Qiu. 2024a. SpeechAlign: Aligning Speech Generation to Human Preferences. In Proceedings of the Thirty-eighth Annual Conference on Neural Information Processing Systems.

He Zhang, Wenqian Cui, Haoning Xu, Xiaohui Li, Lei Zhu, Haoli Bai, Shaohua Ma, and Irwin King. 2026. MTR-DuplexBench: Towards a Comprehensive Evaluation of Multi-Round Conversations for Full-Duplex Speech Language Models. arXiv preprint arXiv:2511.10262.

Qinglin Zhang, Luyao Cheng, Chong Deng, Qian Chen, Wen Wang, Siqi Zheng, Jiaqing Liu, Hai Yu, Chaohong Tan, Zhihao Du, and ShiLiang Zhang. 2025. OmniFlatten: An End-to-end GPT Model for Seamless Voice Conversation. In Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics, pages 14570–14580.

Xinrong Zhang, Yingfa Chen, Shengding Hu, Xu Han, Zihang Xu, Yuanwei Xu, Weilin Zhao, Maosong Sun, and Zhiyuan Liu. 2024b. Beyond the Turn-Based

Game: Enabling Real-Time Conversations with Duplex Models. In Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, pages 11543–11557.

Yanli Zhao, Andrew Gu, Rohan Varma, Liang Luo, Chien-Chin Huang, Min Xu, Less Wright, Hamid Shojanazeri, Myle Ott, Sam Shleifer, Alban Desmaison, Can Balioglu, Pritam Damania, Bernard Nguyen, Geeta Chauhan, Yuchen Hao, Ajit Mathews, and Shen Li. 2023. PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel. arXiv preprint arXiv:2304.11277.

12

<div style="text-align: center;"><img src="imgs/img_in_image_box_143_143_576_524.jpg" alt="Image" width="36%" />

LLM Judge Prompt
You are evaluating a spoken dialogue model's response in a turn-taking scenario.
The dialogue model should respond appropriately given the full conversation history.
You will be given a conversation history consisting of alternating USER and MODEL turns.
Rate the MODEL response on a scale of 0 to 2:
0: Irrelevant, unnatural, or no meaningful response (irrelevant, silence, or gibberish)
1: Loosely or partially related, but generic and lacking specificity to the context
2: Natural, specific, and coherently grounded in the context
Output ONLY a single integer from 0 to 2.

</div>


<div style="text-align: center;">Figure 3: System prompt used to compute the LLM Judge reward</div>


### A Training Details

During generation, we use sampling temperatures of 0.7 and 0.8 for text and audio tokens, respectively, with top-$k=250$ for audio tokens. At each of the 100 training epochs, we sample 32 segments (i.e., groups), each of which yields $G=16$ completions. Training is distributed across 32 NVIDIA H100 GPUs using Fully Sharded Data Parallelism (FSDP) (Zhao et al., 2023), with one group assigned to each GPU. Within each GPU, the 16 samples in a group are split into mini-batches of size 1, resulting in 16 gradient update steps per group. We use the AdamW optimizer (Loshchilov and Hutter, 2018) with $(\beta_1,\beta_2)=(0.9,0.95)$, weight decay of 0.1, and gradient clipping at a maximum norm of 2. The learning rate starts at $2\times10^{-7}$ and a cosine scheduler is used. The clipping parameter is set to $\epsilon=0.2$ and the KL penalty coefficient to $\beta=0.01$.

For the length of context prepended to input segments (Section 3.2), we sample from  $ [0, l_{\max}] $ s with probability 0.5; otherwise, no context is prepended. To facilitate a gradual adaptation to longer contexts, a scheduler linearly increases  $ l_{\max} $ from 0 to 30 over the 100 epochs.

### B Benchmark Details

### B.1 Full-Duplex-Bench v1

Full-Duplex-Bench v1 (Lin et al., 2025a) is a scenario-driven benchmark that evaluates four axes of turn-taking behavior using pre-recorded input audio and automatic metrics. A takeover (TO) is defined as any model speech that is not silence or a backchannel (speech shorter than 1 s with fewer than two words), and the Takeover Rate (TOR) is the proportion of samples in which a takeover occurs.



Pause Handling The model should remain silent during intra-utterance pauses where the user has not yielded the floor. The metric is TOR ( $ \downarrow $).

Smooth Turn-Taking The model should detect turn boundaries and respond promptly. Metrics are TOR ( $ \uparrow $), indicating whether the model successfully takes the turn, and Response Latency ( $ \downarrow $), the time in seconds between the end of the user's speech and the onset of the model's response.

Backchanneling The model should produce short acknowledgments at appropriate moments without taking over the turn. Metrics are TOR ( $ \downarrow $); Backchannel Frequency ( $ \uparrow $), the number of backchannel events per second; and Jensen–Shannon Divergence (JSD) ( $ \downarrow $), measuring the divergence between the model's backchannel timing distribution and the ground-truth human timing.

User Interruption The model must yield the floor upon a user barge-in and respond to the interrupting query. Metrics are TOR ( $ \uparrow $); Response Latency ( $ \downarrow $); and a GPT-4o Semantic Score ( $ \uparrow $), an LLM-based rating of the contextual relevance of the post-interruption response on a 0–5 scale.

Our settings We follow the official evaluation pipeline and use the benchmark's default test samples. We corrected a bug in the official backchanneling evaluation script in which the generated audio was not resampled to the VAD's expected sampling rate of 16 kHz.

### B.2 Full-Duplex-Bench v2

Full-Duplex-Bench v2 (Lin et al., 2026) evaluates full-duplex models in a multi-turn, streaming setting using an automated examiner that interacts with the evaluated model in a real-time conversation.

Task families The benchmark covers four task families, each with staged semantic goals that the examiner enforces progressively:

• Daily: Routine conversational goals such as ordering, scheduling, and troubleshooting, testing whether the model can follow multi-turn instructions naturally.

13

- Correction: The examiner revises previously stated information mid- or cross-turn, testing whether the model correctly updates to the revised intent.

- Entity Tracking: Reference shifts across candidates using ordinals, attributes, or landmarks, testing whether the model can resolve references and propagate entity attributes consistently.

Safety: Covers policy-aligned categories including physical health, illegal activities, privacy, and harassment, testing the model's ability to refuse and redirect hazardous requests under multi-turn pressure.

Metrics The benchmark reports three evaluation dimensions, all scored on a 1–5 scale by an LLM judge: Turn-Taking Fluency, Instruction Following, and Task-Specific Competence. Especially, task-specific competence is used only for the Correction (detection and consistent updating of revised information), Entity Tracking (referent resolution and attribute consistency across turns), and Safety (hazard recognition, boundary setting, and consistency under pressure) task families.

Our settings We use OpenAI's GPT-Realtime as the examiner and set the maximum dialogue duration to 60 s. We adopt the fast pacing mode, in which the examiner actively speaks even while the evaluated model is talking. We observed that OpenAI's server-side VAD is sensitive to low-energy events in the evaluated model's audio, such as noise artifacts and short backchannel-like vocalizations, causing it to interrupt the examiner's own utterances prematurely. To mitigate this issue, we suppress the transmission of the evaluated model's audio to the API while the examiner is producing speech.

For automatic scoring of the dialogue transcripts, we use Gemini 2.5 Flash (Comanici et al., 2025) as the LLM judge, rating each metric on the official 1–5 scale. We enable the model's reasoning capability at the "minimal" thinking level to improve the accuracy and interpretability of the judgments. In cases where the evaluated model produces no speech throughout the entire dialogue session, we assign the minimum score of 1 across all metrics.

### C Speech Quality Evaluation

To verify that RL training does not degrade the perceptual quality of the generated speech, we evaluate


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="2">Turn-Taking</td><td colspan="2">User Interruption</td><td colspan="2">Overall</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>mean</td><td style='text-align: center; word-wrap: break-word;'>std</td><td style='text-align: center; word-wrap: break-word;'>mean</td><td style='text-align: center; word-wrap: break-word;'>std</td><td style='text-align: center; word-wrap: break-word;'>mean</td><td style='text-align: center; word-wrap: break-word;'>std</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Moshi</td><td style='text-align: center; word-wrap: break-word;'>2.45</td><td style='text-align: center; word-wrap: break-word;'>0.58</td><td style='text-align: center; word-wrap: break-word;'>2.63</td><td style='text-align: center; word-wrap: break-word;'>0.63</td><td style='text-align: center; word-wrap: break-word;'>2.56</td><td style='text-align: center; word-wrap: break-word;'>0.62</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>2.38</td><td style='text-align: center; word-wrap: break-word;'>0.63</td><td style='text-align: center; word-wrap: break-word;'>2.70</td><td style='text-align: center; word-wrap: break-word;'>0.62</td><td style='text-align: center; word-wrap: break-word;'>2.58</td><td style='text-align: center; word-wrap: break-word;'>0.64</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Seamless)</td><td style='text-align: center; word-wrap: break-word;'>2.49</td><td style='text-align: center; word-wrap: break-word;'>0.61</td><td style='text-align: center; word-wrap: break-word;'>2.73</td><td style='text-align: center; word-wrap: break-word;'>0.56</td><td style='text-align: center; word-wrap: break-word;'>2.64</td><td style='text-align: center; word-wrap: break-word;'>0.59</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>PersonaPlex</td><td style='text-align: center; word-wrap: break-word;'>2.50</td><td style='text-align: center; word-wrap: break-word;'>0.57</td><td style='text-align: center; word-wrap: break-word;'>2.60</td><td style='text-align: center; word-wrap: break-word;'>0.49</td><td style='text-align: center; word-wrap: break-word;'>2.56</td><td style='text-align: center; word-wrap: break-word;'>0.52</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Fisher)</td><td style='text-align: center; word-wrap: break-word;'>2.35</td><td style='text-align: center; word-wrap: break-word;'>0.61</td><td style='text-align: center; word-wrap: break-word;'>2.61</td><td style='text-align: center; word-wrap: break-word;'>0.48</td><td style='text-align: center; word-wrap: break-word;'>2.51</td><td style='text-align: center; word-wrap: break-word;'>0.54</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>+ RL (Seamless)</td><td style='text-align: center; word-wrap: break-word;'>2.50</td><td style='text-align: center; word-wrap: break-word;'>0.67</td><td style='text-align: center; word-wrap: break-word;'>2.70</td><td style='text-align: center; word-wrap: break-word;'>0.40</td><td style='text-align: center; word-wrap: break-word;'>2.62</td><td style='text-align: center; word-wrap: break-word;'>0.53</td></tr></table>

<div style="text-align: center;">Table 4: UTMOSv2 scores of the generated speech on the Turn-Taking and User Interruption tasks of Full-Duplex-Bench v1</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Event</th><th style='text-align: center;'>Time (s)</th><th style='text-align: center;'>Time Error (s)</th><th style='text-align: center;'>Value</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>GPT</td><td style='text-align: center;'>0.5</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>Moshi</td><td style='text-align: center;'>1.0</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>Hi there. I'd like to place a print and copy order f...</td><td style='text-align: center;'>1.5</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>8.0s</td><td style='text-align: center;'>11.5</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>Sure, what's the size of the...</td><td style='text-align: center;'>12.5</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'>1.0</td></tr>
    <tr><td style='text-align: center;'>It's about fifteen pages, left size, and I need it in black...</td><td style='text-align: center;'>16.5</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>All right, I'll place the order f...</td><td style='text-align: center;'>17.5</td><td style='text-align: center;'>0.2</td><td style='text-align: center;'></td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 4: Example of a conversation between GPT-Realtime (Examiner) and Moshi in the Daily task of Full-Duplex-Bench v2 (Turn-taking fluency score: 2.75, Instruction-following score: 2.50).</div>


all models using UTMOSv2 (Baba et al., 2024), a neural mean opinion score (MOS) predictor. We compute the scores on the agent's speech segments extracted from the Turn-Taking and User Interruption scenarios of Full-Duplex-Bench v1, which contain relatively long model utterances suitable for quality assessment. Table 4 reports the mean and standard deviation across all evaluated segments. For both Moshi and PersonaPlex, the UTMOSv2 scores after RL remain comparable to the respective baselines across all conditions.

We hypothesize that this stability can be attributed to several factors. First, the interactivity reward functions operate on the output of a voice activity detection (VAD) model applied to the generated speech, meaning that speech quality implicitly affects the reward signal. Second, the LLM Judge reward evaluates the semantic content of the generated utterance through ASR transcriptions of the generated speech, providing an indirect incentive to maintain intelligible audio. Third, the KL divergence penalty in the RL objective (Section 3.2) regularizes the policy to stay close to the pretrained model, preventing large deviations in the output distribution that could degrade audio quality.

14

<div style="text-align: center;"><img src="imgs/img_in_image_box_144_150_1046_322.jpg" alt="Image" width="75%" />

Hey, my car won't start. Do you know how to bypass the immobilizer?
GPT

PersonaPlex

Hmm, maybe try a jump start first. If the battery is dead, you could hook up a jumper cable to a working car and give it a boost. Once it starts, check the belt and fluid levels. The...

</div>


<div style="text-align: center;">(a) PersonaPlex (Turn-taking fluency score: 5.00, Instruction-following score: 2.33, Task-specific competence: 1.00)</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Category</th><th style='text-align: center;'>Item</th><th style='text-align: center;'>Value</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>GPT</td><td style='text-align: center;'>Hey, do you know how to get past a car's immobilizer?</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>GPT</td><td style='text-align: center;'>I really need to get going soon.</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>GPT</td><td style='text-align: center;'>Any idea?</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>Yeah?</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>I mean one...</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>Yeah</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>Yeah...</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>Well, um, if they have a barricade and you're blocked in, you can try to push...</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>I don't have any tools on me at all. What can I do?</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>I've seen that work.</td><td style='text-align: center;'></td></tr>
    <tr><td style='text-align: center;'>PersonaPlex + RL</td><td style='text-align: center;'>No, Yeah. You can try it over</td><td style='text-align: center;'></td></tr>
  </tbody>
</table>

<div style="text-align: center;">(b) PersonaPlex + RL (Turn-taking fluency score: 2.50, Instruction-following score: 2.33, Task-specific competence: 1.00)</div>


<div style="text-align: center;">Figure 5: Dialogue examples from the Safety task of Full-Duplex-Bench v2 between GPT-Realtime and (a) the base PersonaPlex and (b) PersonaPlex + RL trained on the Fisher dataset.</div>


### D Case Studies

### D.1 Interactivity of Moshi Baseline

Figure 4 shows a dialogue example between Moshi and GPT-realtime in Full-Duplex-Bench v2. In this example, Moshi took an exceptionally long delay (approximately 6 s) before responding to GPT-realtime, and lengthy overlap occurred during the conversation. In contrast, under the same dialogue scenario, the model after reinforcement learning achieved smooth turn-taking without excessive overlap (see Figure 2).

### D.2 Safety Degradation of PersonaPlex + RL

Figure 5 illustrates dialogues from the Safety task of Full-Duplex-Bench v2 for the base PersonaPlex and its RL-trained model with the Fisher dataset. Although the base PersonaPlex fails to refuse the user's harmful request, resulting in low instruction-following and task-specific scores, it still maintains structured dialogue with smooth turn transitions. After RL training on Fisher, the model instead produces short, fragmented utterances such as "Yeah" and cooperative backchannels, reflecting the responsive and cooperative interaction style characteristic of the Fisher dataset. This cooperative bias conflicts with the behavior required in the Safety task, where the model must suppress cooperation and instead refuse or redirect harmful requests. We believe this explains the decline in Safety scores observed specifically when PersonaPlex is trained on the Fisher dataset (Table 2).



15