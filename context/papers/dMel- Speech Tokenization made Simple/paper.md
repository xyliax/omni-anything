arXiv:2407.15835v3 [cs.CL] 21 May 2025

# dMel: Speech Tokenization made Simple

Richard He Bai $ ^{*} $

Apple

richardbai@apple.com

Zijin Gu

Apple

zgu26@apple.com

Tatiana Likhomanenko $ ^{*} $

Apple

antares@apple.com

Zakaria Aldeneh

Apple

zaldeneh@apple.com

Ruixiang Zhang

Apple

ruixiangz@apple.com

Navdeep Jaitly

Apple

njaitly@apple.com

## Abstract

Large language models have revolutionized natural language processing by leveraging self-supervised pretraining on vast textual data. Inspired by this success, researchers have investigated various compression-based speech tokenization methods to discretize continuous speech signals, enabling the application of language modeling techniques to discrete tokens. However, audio compressor introduces additional complexity and computational cost, and often fail on out-of-domain audio signals. In this work, we introduce a novel speech representation (dMel) that discretizes mel-filterbank channels into intensity bins, creating a simpler yet more effective representation compared to existing speech tokenization methods. Our approach demonstrates superior performance in preserving audio content, robustness to out-of-domain data, and offers a training-free, natural, and streamable representation. To address the high-dimensional nature of log-mel spectrograms, we propose an efficient parallel encoding and decoding method for high-dimensional tokens using an LM-style transformer architecture. This innovation enables us to develop RichTTS and RichASR—two models sharing the same architecture while achieving comparable or better results than specialized existing methods. Our results demonstrate the effectiveness of dMel in achieving high performance on both speech synthesis and recognition tasks within a unified framework, paving the way for efficient and effective joint modeling of speech and text. The code is available at https://github.com/apple/dmel and demos are available at https://apple.github.io/dmel-demo/.

## 1 Introduction

Large language models (LLMs) have achieved remarkable success in various natural language processing tasks by leveraging self-supervised pretraining on massive amounts of textual data [9]. Inspired by this success, numerous works [8, 38, 50, 44] have sought to extend the language modeling approach to speech processing, aiming to build unified models capable of both speech understanding and generation tasks. However, a key challenge lies in the continuous nature of speech signals, necessitating effective tokenization methods to discretize the input for language model-based processing.

Current speech tokenization approaches can be broadly categorized into two types: semantic (content) tokens and acoustic tokens $ ^{1} $. Semantic tokens, extracted from self-supervised (SSL) pretrained speech models [2, 18], are obtained by first encoding the speech signal into representations and then clustering them into discrete tokens with k-means method. However, such SSL pretrained models are

 $ ^{*} $These authors contributed equally to this work.

 $ ^{1} $We use a word ‘semantic’ with the meaning of ‘content’ to keep prior work notation [8].

Preprint. Under review.

not useful for high fidelity speech synthesis as speaker identity and other details of raw speech are lost in training [8]. Conversely, acoustic tokens can be obtained from audio compression models that are trained to compress the speech signal into codebook indices with residual vector quantization (RVQ) and reconstruction objectives [48, 12]. These tokens prioritize acoustic reconstruction but lose semantic information which can lead to poorer results in generating audio [44].

To combine the advantages of both semantic and acoustic tokens, AudioLM [8] proposed to model both semantic tokens and acoustic tokens with 3 stages: semantic modeling, coarse acoustic modeling, and fine acoustic modeling. The coarse-to-fine modeling strategy is designed to match the residual structure of RVQ based acoustic tokens. This solution addresses both content and speech quality, but its multi-stage hierarchical structure complicates the model and can lead to slower training and inference. Another solution is to combine the semantic and acoustic features together. Zhang et al. [52] proposed to distill the semantic tokens into the acoustic token's first residual channel during the training of the RVQ model in a teacher-student manner. In this way, the new feature can preserve the semantic information better and also reconstruct high quality speech signals.

In this paper, we raise the following fundamental question – do we really need to separate speech into semantic and acoustic tokens first, and process them with idiosyncratic architectures? We propose a simple alternative called dMel (see Figure 1) that discretizes log mel-filterbanks (Mel) energies directly into ordinal bins. Intriguingly, we find that discretizing Mel has little impact on the ability of off-the-shelf Mel vocoders to reconstruct waveforms $ ^{2} $. In Table 1 we show different vocoders to reconstruct waveforms from Mel and discretized Mel (dMel) computed on them, as well as ASR models trained on Mel and dMel.

We find that the word error rate (WER) of an ASR system run on the reconstructed waveforms is quite similar to the WER of the same system run on the ground-truth audio, showing that dMel captures the acoustic information needed to reconstruct good waveforms. Similarly, we find that the WER of ASR models trained on Mel and dMel are similar, indicating that dMel effectively pre-



<div style="text-align: center;">Table 1: Impact of discretization.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">Reconstruction WER (%)</td><td colspan="2">Recognition WER (%)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>P-WaveGAN $ ^{1} $</td><td style='text-align: center; word-wrap: break-word;'>HifiGAN $ ^{2} $</td><td style='text-align: center; word-wrap: break-word;'>Seq2seq $ ^{3} $</td><td style='text-align: center; word-wrap: break-word;'>CTC $ ^{4} $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ground-truth</td><td style='text-align: center; word-wrap: break-word;'>2.02</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mel</td><td style='text-align: center; word-wrap: break-word;'>2.13</td><td style='text-align: center; word-wrap: break-word;'>2.08</td><td style='text-align: center; word-wrap: break-word;'>2.4</td><td style='text-align: center; word-wrap: break-word;'>2.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel</td><td style='text-align: center; word-wrap: break-word;'>2.23</td><td style='text-align: center; word-wrap: break-word;'>2.11</td><td style='text-align: center; word-wrap: break-word;'>2.5</td><td style='text-align: center; word-wrap: break-word;'>2.1</td></tr></table>

 $ ^{*} $ [47] $ ^{1} $, [23] $ ^{2} $, [14] $ ^{3} $, [15] $ ^{4} $ Configurations are detailed in Sec. 3.

serves semantic content. This demonstrates that discretizing Mel has limited impact on information content while providing the benefits of discrete tokens.

By operating on the log mel-filterbanks and preserving the frequency and intensity information (with some loss of resolution from discretization), dMel inherently preserves both semantic and acoustic information in a unified representation, without the need for separate tokenization or additional pretraining of a tokenization model. The key advantages of dMel include:

- Interpretable and complete: Preserves both semantic and acoustic information in an interpretable physics-based representation, with minimal information loss from discretization.

- Model-free and versatile: Directly compatible with any mel-filterbank vocoder for waveform reconstruction, unlike other methods where representations are tightly coupled to specific encoder-decoder architectures.

- Parallel processing: Frequency channels can be modeled independently without complex hierarchical dependencies, enabling efficient processing with decoder-only transformer architectures.

While data-driven tokenization methods can be improved with more diverse training data, they inherently suffer from information loss due to their neural compression—discarding information that may be crucial in unseen conditions. In contrast, mel-spectrogram offers advantages as a physics-based signal representation:

• Robust frequency preservation: Captures frequency components through principled transformation, aligning with human auditory perception's sensitivity to magnitude spectrum.

- Domain-agnostic performance: Demonstrates consistent behavior across acoustic conditions without requiring domain-specific training.

• Proven reliability: Shows robust performance across decades of speech processing research in diverse conditions.

 $ ^{2} $We used vocoders from https://github.com/kan-bayashi/ParallelWaveGAN.

2

<div style="text-align: center;"><img src="imgs/img_in_image_box_295_139_916_445.jpg" alt="Image" width="50%" />

Mel – filterbanks
Encoder
Vocoder
Decoder
Time Series Data
Time Series Coordinates
Time Series Peak Coordinates
Time Series Peak Value
Time Series Peak Frequency
Time Series Peak Value
Embedding
Embedding Coordinates
Embedding Peak Coordinates
Embedding Peak Value

</div>


<div style="text-align: center;">Figure 1: Prior works on speech tokenization use either heavy self-supervised pretrained encoders [2, 18] to extract semantic tokens (and train a separate decoder for it [24]) or learn compression encoder-decoder models with residual vector quantizations [48, 12] to obtain acoustic tokens. By contrast we eliminate the encoder and simply discretize mel-filterbanks (dMel) to encode audio, and use a simple mel-filterbank vocoder [47] to reconstruct speech signals.</div>


Given the high-dimensional nature of log-mel spectrograms, we propose an efficient parallel encoding and decoding method for these high-dimensional tokens using an LM-style transformer architecture. This enables us to develop RichTTS and RichASR—two models sharing the same architecture while achieving comparable or better results than specialized existing methods.

Through comprehensive evaluations, we show that using dMe1 allows us to employ a single decoder-only model to achieve high performance on both automatic speech recognition ASR and TTS tasks. The ASR task validates that dMe1 preserves semantic information, while the TTS task demonstrates that dMe1 is effective for high-fidelity acoustic reconstruction of speech. We also compare dMe1 to other tokenization methods and find that dMe1 achieves the best WER for the ASR task, which indicates that semantic information is well preserved. Additionally, dMe1 achieves a lower WER score for the TTS task when using WhisperX [4] for automatic evaluation, and we find that models trained with dMe1 can generate long and natural speech samples.

## 2 Method

In this section, we first introduce our proposed dMel speech tokenization method, which discretizes log mel-filterbanks energies directly into bins. We then describe our unified LM-style transformer model for ASR and TTS tasks, which leverages dMel for speech tokenization. The model architecture is illustrated in Figure 2.

### 2.1 dMel Speech Tokenizer

Different from existing VQ-VAE [8, 52, 21, 48] based speech tokenizers, we propose a discretized log mel-filterbanks based speech tokenizer. The outline of the discretization method is shown in Figure 1. Later in the paper, we show that this tokenizer allows the model to process the input speech signal efficiently and capture the relevant acoustic features for both ASR and TTS tasks.

We denote tensors as X while  $ X_{i,...} $ denote the  $ (i, ...) $-th component of tensor X. First, the speech tokenizer takes the input speech signal x and computes the log mel-filterbanks representation M:

 $$ \mathbf{M}=\operatorname{M e l}(\mathbf{x}), $$ 

where  $ \text{Mel}(\cdot) $ represents the function that computes the log mel-filterbanks,  $ \mathbf{M} \in \mathbb{R}^{T \times N} $,  $ N $ is the number of log mel-filterbanks and  $ T $ is the number of frames in the spectrogram.

Tokenization To discretize the log mel-filterbanks representation M into speech tokens, we adopt a codebook C. In this paper, we apply a simple linear discretization, so that the codebook  $ C \in \mathbb{R}^{2^K} $

3

<div style="text-align: center;">Table 2: Comparison between different speech tokenizers: dMel (ours), HuBERT-KM and Speech-Tokenizer. For dMel we use N = 80 log-mel-filterbanks (50ms window, 25ms hop distance), and  $ 2^K = 16 $ values of the codebook C. For HuBERT-KM, 200 is chosen according to [28].</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>dMe1</td><td style='text-align: center; word-wrap: break-word;'>HuBERT-KM</td><td style='text-align: center; word-wrap: break-word;'>SpeechTokenizer</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Codebook Size</td><td style='text-align: center; word-wrap: break-word;'>16</td><td style='text-align: center; word-wrap: break-word;'>200</td><td style='text-align: center; word-wrap: break-word;'>1024</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Code Dimension</td><td style='text-align: center; word-wrap: break-word;'>80</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Vocabulary Size</td><td style='text-align: center; word-wrap: break-word;'>16 * 1</td><td style='text-align: center; word-wrap: break-word;'>200 * 1</td><td style='text-align: center; word-wrap: break-word;'>1024 * 8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Frame-rate</td><td style='text-align: center; word-wrap: break-word;'>40Hz</td><td style='text-align: center; word-wrap: break-word;'>50Hz</td><td style='text-align: center; word-wrap: break-word;'>50Hz</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Bit-rate</td><td style='text-align: center; word-wrap: break-word;'>12.8kps</td><td style='text-align: center; word-wrap: break-word;'>0.4kps</td><td style='text-align: center; word-wrap: break-word;'>4kps</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Training-free?</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr></table>

and its values are evenly spaced in the range of the log mel-filterbanks values:

 $$ m=\operatorname*{m i n}_{t,i}(\mathbf{M}_{t,i}),\qquad M=\operatorname*{m a x}_{t,i}(\mathbf{M}_{t,i})\qquad\delta=\frac{M-m}{2^{K}}, $$ 

 $$ \mathbf{C}=\left[m,m+\delta,m+2\delta,\ldots,m+(2^{K}-1)\delta\right]. $$ 

In practice, we compute the minimum  $ m $ and maximum  $ M $ values of log mel-filterbanks across the entire dataset to define the codebook  $ \mathbf{C} $. Then we map a magnitude  $ \mathbf{M}_{t,i} $ of every frequency channel  $ i = 1 \ldots N $ for the time frame  $ t = 1 \ldots T $ into a bin index of the codebook  $ \mathbf{C} $ in the following way:

 $$ \mathbf{S}_{t,i}=\operatorname{Discretize}(\mathbf{M}_{t,i})=\operatorname*{argmin}_{j}|\mathbf{M}_{t,i}-\mathbf{C}_{j}| $$ 

where  $ \mathbf{S} \in \mathbf{B}^{T \times N} $ represents the discretized log mel-filterbanks (dMel) with  $ \mathbf{B} = \{j | j = 1, 2, 3, \ldots, 2^K\} $ and  $ \mathbf{S}_t \in \mathbf{B}^N $ being the  $ t $-th speech token. As the codebook  $ \mathbf{C} $ has  $ 2^K $ distinct values and thus number of bins  $ |\mathbf{B}| = 2^K $, each speech token is represented by  $ N \cdot K $ bits where every  $ K $ bits are used to represent one of  $ N $ frequency channels.

Detokenization To reconstruct the speech signal x from the speech tokens S, we first transform bin indices back to the log mel-filterbanks representation via the codebook C:

 $$ \hat{\mathbf{M}}_{t,i}=\mathbf{C}\mathbf{s}_{t,i}. $$ 

Then, we apply a vocoder [47] to transform reconstructed log mel-filterbanks  $ \mathbf{M}_{t,i} $ back into the time domain signal x. The vocoder is trained independently and is not part of the transformer decoder-based model.

Comparison between Speech Tokenizers In Table2, we compare dMe1 with the baselines in terms of vocabulary size, bit-rate, and frame-rate. First, dMe1 has a much smaller vocabulary, as it is discretized mel-filterbanks energies, allowing all 80 channels to share the same vocabulary since they represent similar energy values. In contrast, neural compression encoders like SpeechTokenizer require separate embeddings for different channels. Also, dMe1 operates at a lower frame-rate while maintaining a higher bit-rate. The reduced frame-rate leads to shorter sequence lengths during both training and inference, which is particularly advantageous when using large models. While a higher bit-rate typically increases model complexity for compression-based tokenizers, this is not the case for dMe1 due to two key factors: i) dMe1 is encoder-free, without any compression encoder; ii) the complexity of the model introduced in Section 2.2 depends only on the vocabulary size and sequence length (frame-rate), not on the code dimensions. In compression-based methods, increasing the bit-rate requires either larger codebooks or additional residual dimensions, leading to increased tokenizer complexity. Moreover, these methods require more complex downstream models to handle the expanded representations. Given recent studies [13, 30] demonstrated that bit-rate does not strongly correlate with downstream model performance, we focus our comparative analysis on frame-rate rather than bit-rate when evaluating different speech tokens for downstream tasks. This approach challenges the conventional assumption that higher bit-rates necessarily yield better results.

### 2.2 Unified Speech-Text Transformer Decoder (RichTTS and RichASR)

Modeling speech and text sequences jointly is essential for a model to understand and generate both modalities. However, it is challenging to design a unified model that can handle both speech-to-text

4

<div style="text-align: center;"><img src="imgs/img_in_image_box_215_145_1007_449.jpg" alt="Image" width="64%" />

Transformer Decoder
input output

Transformer Decoder

3 9 7
... 2 8 2 11
... 2 8 2 11
... 2 8 2 11

Cat sits on mat
<b>3 8 7
... 2 8 2 11
... 2 8 2 11
... 2 8 2 11
... 2 8 2 11

</div>


<div style="text-align: center;">Figure 2: (Left) For a time step  $ t $ encoded dMel from Figure 1 is inputted to the transformer decoder to produce final embeddings for each of the frequency channels in parallel. (Right) Unified Speech-Text Transformer Decoder with speech tokens as dMel.</div>


and text-to-speech effectively. In this work, we apply a unified LM-style transformer model that takes speech and text tokens as input and generates the output tokens in the target sequence. The model is trained in end-to-end on a combined dataset of speech and text pairs, enabling it to learn the joint representations for ASR and TTS tasks. As we show in the rest of the paper, the crucial part for the joint model training is the proper speech tokenization which dMel provides.

Text Encoding For text data, we apply a character-level tokenizer to convert the input text into a sequence of text tokens. The text tokens are passed through an embedding layer, Embed( $ \cdot $) :  $ \{j | j = 1, 2, 3 \ldots L\} \rightarrow \mathbb{R}^D $, where  $ D $ is the embedding dimension and  $ L $ is the vocabulary size. The dimension of the speech token embedding is set to be the same as the text token embedding  $ D $ and no further mapping is required. The motivation for using a character-level tokenizer is to reduce the vocabulary size  $ L $ and improve the model's generalization ability. Also, character tokens can capture the fine-grained linguistic features that are essential for both ASR and TTS tasks.

Speech Encoding For speech signal, we apply the dMel speech tokenizer to convert the input speech signal into a sequence of speech tokens. Then, the speech tokens  $ \mathbf{S} \in \mathbf{B}^{T \times N} $ are passed through a learnable embedding layer,  $ \text{Embed}(\cdot): \mathbf{B} \to \mathbb{R}^d $, and a learnable linear layer,  $ \text{Linear}(\cdot): \mathbb{R}^{N \times d} \to \mathbb{R}^D $, to obtain the speech token representation  $ \mathbf{E} \in \mathbb{R}^{T \times D} $:

 $$ \mathbf{E}_{t}=\operatorname{L i n e a r}(\mathbf{E}^{\prime}{}_{t}),\mathrm{a n d}\mathbf{E}^{\prime}{}_{t}=\operatorname{C o n c a t e n a t e}([\operatorname{E m b e d}(\mathbf{S}_{t,1}),\operatorname{E m b e d}(\mathbf{S}_{t,2}),\ldots,\operatorname{E m b e d}(\mathbf{S}_{t,N})]), $$ 

where  $ \mathbf{E}_t \in \mathbb{R}^D $ is the speech token representation. Here, for every time frame  $ t $, a speech token  $ \mathbf{S}_t $ is processed in parallel and independently for every frequency channel  $ i $ by  $ \text{Embed}(\mathbf{S}_{t,i}) $ mapping, and then embeddings of all frequency channels are stacked together to form one vector representation  $ \mathbf{E}'_t $ for the frame  $ t $. Finally, the speech token embeddings  $ \mathbf{E}_t $ are fed into the LM-style transformer models for further processing.

We also implemented other popular speech tokenizers including HuBERT-KM [24] and SpeechTokenizer [52] for comparison. The main difference among these speech tokenizers is the codebook size and codes dimension, shown in Table 2. For both HuBERT-KM and SpeechTokenizer the speech tokens are mapped via a learnable linear layer from their dimension to the text embedding dimension  $ D $ before feeding into the LM-style transformer model.

Transformer Decoder The transformer decoder is trained end-to-end on a combined dataset of speech and text pairs. For TTS training, the input sequence is constructed by concatenating the speaker embedding (The speaker embeddings are extracted from an independent dvector [43] model $ ^{3} $), text tokens, and speech tokens. For ASR training, the input sequence is constructed by concatenating the speech tokens and text tokens. Both tasks are trained with causal masking, where the model is trained to predict the next token based on the previous tokens. The loss is calculated using the cross-entropy

 $ ^{3} $We use a pretrained model “Speaker Encoder” from the YourTTS [10] repository https://github.com/Edresson/YourTTS.

5

<div style="text-align: center;"><img src="imgs/img_in_image_box_412_139_812_504.jpg" alt="Image" width="32%" />

Transformer Decoder

<b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><b><

</div>


<div style="text-align: center;">Figure 3: Unified Speech-Text Transformer Decoder with speech tokens as dMel where we predict multiple, e.g. two, frames in parallel reducing the frame rate, e.g. by 2x: dMel tokens for every two frames are stacked together to form the input into the decoder and predicted in parallel afterwards.</div>


loss between the predicted tokens and the ground-truth tokens. Loss calculation is skipped on the speech tokens for ASR task and on the text tokens for TTS task. Note, that all frequency channels at time frame t for dMel tokenizer are predicted independently and in parallel, see Figure 2 (left). For positions encoding, to capture the relative distances between tokens in the input sequence, we apply multiplicative relative positional embedding RoPE [41]. This allows the model to learn the positional relationships between speech tokens, text tokens, and speaker embeddings, enhancing its ability to generate coherent output sequences. For positional embeddings we do not distinguish between text, speech and speaker tokens and thus having global positions notation across all of them, see Figure 2.

Context Masking during Training Compared to LMs, audio frames are highly redundant with strong local correlations. This makes long-form generation difficult for models due to exposure bias [6]. To mitigate exposure bias during training, we apply span-masking [35] to the speech token context, masking out multiple random spans of speech frames. The model is trained to predict the next token based on the masked context. This context-masking strategy helps the model learn to generate accurate speech tokens in the presence of missing information, improving its robustness and generalization. It forces the model to attend to the text rather than copying previously inferred speech tokens due to learnt correlations. We also find that span-masking text tokens improve the ASR task.

k-Frame Encoding and Decoding Given the fact that our model can encode and decode multiple channels in parallel, for mel-spectrogram, we are interested in whether the model can do k-frame encoding and decoding in parallel too. As shown in Figure 3, we simply concatenate multiple frames together and using the same technique to encode and decode it as described in previous paragraphs. Our results show that this model is also working well on multi-frame generation in parallel. More results can be found in Section 3.

## 3 Experiments

In this section, we begin by evaluating different speech tokenizers through a common practice in the literature: tokenizing speech into discrete units and then reconstructing the speech to assess the quality of the reconstruction. This approach helps gauge the effectiveness of various tokenization techniques. Following this, we present both TTS and ASR results using an LM-style (decoder-only) model with different speech tokens. While most related work focuses solely on speech synthesis, our study encompasses both speech generation and recognition, providing a more comprehensive evaluation of the tokenization methods. We evaluate the performance of our model mainly on the LibriSpeech dataset and compare it with state-of-the-art speech tokenizers, ASR and TTS models.

6

<div style="text-align: center;">Table 3: Speech reconstruction results on 300 random samples from LibriSpeech test-clean set. WER (%) is evaluated with Hubert Large.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Tokenizer</td><td style='text-align: center; word-wrap: break-word;'>Speech2Unit (M params)</td><td style='text-align: center; word-wrap: break-word;'>Unit2Speech (M params)</td><td style='text-align: center; word-wrap: break-word;'>Frame Rate</td><td style='text-align: center; word-wrap: break-word;'>WER $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>MOS-LQO $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>MOS $ \uparrow $ (95% CI)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GroundTruth</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>2.02</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>3.91 $ \pm $0.12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HuBERT-KM</td><td style='text-align: center; word-wrap: break-word;'>95</td><td style='text-align: center; word-wrap: break-word;'>111</td><td style='text-align: center; word-wrap: break-word;'>50Hz</td><td style='text-align: center; word-wrap: break-word;'>8.71</td><td style='text-align: center; word-wrap: break-word;'>2.06</td><td style='text-align: center; word-wrap: break-word;'>2.74 $ \pm $0.14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>EnCodec</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>7</td><td style='text-align: center; word-wrap: break-word;'>75Hz</td><td style='text-align: center; word-wrap: break-word;'>2.03</td><td style='text-align: center; word-wrap: break-word;'>4.03</td><td style='text-align: center; word-wrap: break-word;'>3.69 $ \pm $0.13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SpeechTokenizer</td><td style='text-align: center; word-wrap: break-word;'>65</td><td style='text-align: center; word-wrap: break-word;'>34</td><td style='text-align: center; word-wrap: break-word;'>50Hz</td><td style='text-align: center; word-wrap: break-word;'>2.41</td><td style='text-align: center; word-wrap: break-word;'>4.19</td><td style='text-align: center; word-wrap: break-word;'>3.77 $ \pm $0.13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mel-HifiGAN</td><td style='text-align: center; word-wrap: break-word;'>n/a</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>80Hz</td><td style='text-align: center; word-wrap: break-word;'>2.08</td><td style='text-align: center; word-wrap: break-word;'>4.52</td><td style='text-align: center; word-wrap: break-word;'>3.80 $ \pm $0.12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-HifiGAN</td><td style='text-align: center; word-wrap: break-word;'>n/a</td><td style='text-align: center; word-wrap: break-word;'>12</td><td style='text-align: center; word-wrap: break-word;'>80Hz</td><td style='text-align: center; word-wrap: break-word;'>2.11</td><td style='text-align: center; word-wrap: break-word;'>4.47</td><td style='text-align: center; word-wrap: break-word;'>3.68 $ \pm $0.13</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mel-PWG</td><td style='text-align: center; word-wrap: break-word;'>n/a</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>80Hz</td><td style='text-align: center; word-wrap: break-word;'>2.13</td><td style='text-align: center; word-wrap: break-word;'>4.40</td><td style='text-align: center; word-wrap: break-word;'>3.27 $ \pm $0.14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-PWG</td><td style='text-align: center; word-wrap: break-word;'>n/a</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>80Hz</td><td style='text-align: center; word-wrap: break-word;'>2.23</td><td style='text-align: center; word-wrap: break-word;'>4.37</td><td style='text-align: center; word-wrap: break-word;'>3.23 $ \pm $0.14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mel-PWG</td><td style='text-align: center; word-wrap: break-word;'>n/a</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>40Hz</td><td style='text-align: center; word-wrap: break-word;'>2.36</td><td style='text-align: center; word-wrap: break-word;'>4.34</td><td style='text-align: center; word-wrap: break-word;'>2.99 $ \pm $0.15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-PWG</td><td style='text-align: center; word-wrap: break-word;'>n/a</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>40Hz</td><td style='text-align: center; word-wrap: break-word;'>2.51</td><td style='text-align: center; word-wrap: break-word;'>4.29</td><td style='text-align: center; word-wrap: break-word;'>2.97 $ \pm $0.15</td></tr></table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'></th><th style='text-align: center;'>No noise</th><th style='text-align: center;'>Music noise</th><th style='text-align: center;'>Speech noise</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Encodec</td><td style='text-align: center;'>4.8</td><td style='text-align: center;'>10.8</td><td style='text-align: center;'>13.4</td></tr>
    <tr><td style='text-align: center;'>Hubert-KM</td><td style='text-align: center;'>12.3</td><td style='text-align: center;'>45.6</td><td style='text-align: center;'>83.7</td></tr>
    <tr><td style='text-align: center;'>SpeechTokenizer</td><td style='text-align: center;'>5.3</td><td style='text-align: center;'>60.6</td><td style='text-align: center;'>22.1</td></tr>
    <tr><td style='text-align: center;'>MiMi</td><td style='text-align: center;'>5.1</td><td style='text-align: center;'>69.4</td><td style='text-align: center;'>21.9</td></tr>
    <tr><td style='text-align: center;'>dMel</td><td style='text-align: center;'>4.6</td><td style='text-align: center;'>8.3</td><td style='text-align: center;'>12.4</td></tr>
    <tr><td style='text-align: center;'>Ground Truth</td><td style='text-align: center;'>4.6</td><td style='text-align: center;'>8.2</td><td style='text-align: center;'>10.9</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 4: Speech reconstruction results on 300 random samples from LibriSpeech test-clean set when noise is added: either background music from [7] dataset or speech noise from test-other. WER (%) is evaluated with WhisperX ASR ("base.en"). Audio examples are in our demo page.</div>


### 3.1 Speech Reconstruction on Clean Speech

We first conduct speech reconstruction experiments with various speech tokenizers on clean speech. Following [52], we randomly sample 300 speech utterances and their ground truth transcriptions from the LibriSpeech test-clean dataset. We use the speech2unit and unit2speech modules to convert the speech signal to speech tokens and then reconstruct the speech signal from the speech tokens. We compute the WER between the ASR outputs from HuBERT-Large [18] $ ^{4} $ on the audio samples and their ground truth transcripts. We also report MOS-LQO (Mean Opinion Score – Listening Quality Objective) score to measure the reconstruction quality using ViSQOL [17]. Finally, we use human evaluation to measure the naturalness of the reconstructed speech using a MOS score with 95% confidence interval. We instruct the human evaluators to rate the naturalness of the reconstructed speech on a scale of 1 to 5, where 1 is the worst and 5 is the best. The results are shown in Table 3.

From Table 3, we can see that semantic tokenization (HuBERT-KM) is poor for speech reconstruction. Meanwhile, acoustic tokenizers that are optimized to reconstruct the signal directly (EnCodec and SpeechTokenizer) do well.

We apply different vocoders to reconstruct the speech signal from log mel-filterbanks, and find that the WER of the reconstructed speech signal is comparable to the acoustic tokenization methods with a fraction of the parameters. Also, log mel-filterbanks achieve a better MOS-LQO score, which indicates that the reconstructed audio is more similar to the original audio. By comparing Mel and

 $ ^{4} $We use checkpoint https://huggingface.co/facebook/hubert-large-ls960-ft.

7

dMe1, we can see that discretization has little impact on WER and MOS-LQO scores. We also find that the exact vocoder matters much less than the frame rate of tokenization: the WER goes from 2.08 to 2.13 when switching from HifiGAN to ParallelWaveGAN (PWG), but it falls from 2.13 to 2.36 when the frame rate is changed from 80Hz to 40Hz. However, even a 1M parameter vocoder operating at a 40Hz frame rate is comparable to the much larger SpeechTokenizer on WER and MOS-LQO metrics.

### 3.2 Speech Reconstruction on Noisy Speech

In addition to the in-domain clean human speech, we also measure speech tokenizer's out-of-domain ability which is neglected in prior work. We compare different speech tokenizations for speech reconstruction under noisy conditions. We synthetically add two kinds of noise signal to the clean audio: i) add music background to the original human speech; ii) add another human speech in low volume as a background to the original human speech. Results are shown in Figure 4: both HuBERT-KM and SpeechTokenizer fail in out-of-domain setting while EnCodec, Mel and dMel show robustness for noisy speech reconstruction. This supports our motivation to explore dMel, training-free and deterministic tokenization, which is able to handle various acoustic conditions.

Considering the efficiency and performance, we choose the dMel speech tokenizer in 40Hz with ParallelWaveGAN vocoder for the following experiments.

### 3.3 LM-Style Text-to-Speech

Here we compare the accuracy and naturalness of speech synthesized by LM-style text-to-speech (TTS) models trained on different tokenization methods. For TTS evaluation, we utilize WhisperX [4] (“base.en” from [34]) to transcribe our generated speech into text and calculate the WER and the character error rate (CER). We report both WER and CER to facilitate comparisons to prior works which have reported only one or the other.

#### 3.3.1 Configurations

We use several open-sourced datasets with paired speech and text transcription to conduct experiments: i) LibriSpeech [31] dataset (CC BY 4.0) consists of English speech recordings (960h, 16kHz) from various speakers (~2k) and conditions; ii) LibriTTS [49] (CC BY 4.0) dataset (500h) derived from LibriSpeech improves on it with the proper sentence split, text normalization and keeping samples 24kHz; iii) VCTK [46] contains 44h of English speech (108 speakers); iv) LJSpeech [19] (public domain in US) is a single speaker English audio recordings of 22kHz with read speech from LibriVox $ ^{5} $. While LibriSpeech is used to train ASR and TTS models, LibriTTS, VCTK and LJSpeech are only used to train the TTS.

We train the LM-style transformers in three different sizes: Small, Base, and Large (see Appendix Table 10). Unless stated otherwise, the Base model is used in all experiments if not stated otherwise. All models use pre-LayerNorm with dropout set to 0.1 for residual, attention and embedding layers and 0.3 for positional embedding. dMe1 uses 16 discrete bins for each channel while text is tokenized with a character vocabulary; the speaker embedding vector has 512 dimensions (see Appendix E for details). In all experiments, training data are sampled to 16kHz.

We trained the TTS model using the same architecture but with three different tokenization methods: HuBERT+KM (with 200 clusters), SpeechTokenizer, and dMe1. Additionally, we present the results from VOX-TLM [28] and USLM [52] for comparison. VOX-TLM is a larger model trained on more data that is initialized from a pretrained LLM (OPT) using HuBERT-KM as the speech tokenizer. USLM comprises an autoregressive (AR) model and a non-autoregressive (NAR) model, both trained with the SpeechTokenizer.

#### 3.3.2 Results

As shown in Table 4 for training on LibriSpeech dataset, our LM-style model with dMel tokenization achieves a WER of 4.3 and a CER of 1.8, significantly outperforming the baseline methods. This indicates that our model can generate more accurate speech with less hallucination and distortion.

 $ ^{5} $https://librivox.org/pages/public-domain/.

8

<div style="text-align: center;">Table 4: Text-to-speech results for different tokenizers. RichTTS is trained on LibriSpeech 960h.WER (%) and CER (%) are evaluated with WhisperX ASR ("base.en") and reported on test-clean.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>WER $ \downarrow $ (%)</td><td style='text-align: center; word-wrap: break-word;'>CER $ \downarrow $ (%)</td><td style='text-align: center; word-wrap: break-word;'>Params</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VOXTLM (HuBERT+KM) $ \dagger $, [28]</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>3.5</td><td style='text-align: center; word-wrap: break-word;'>350M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>USLM (SpeechTokenizer) $ \dagger $, AR+NAR, [52]</td><td style='text-align: center; word-wrap: break-word;'>6.5</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>356M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (HuBERT+KM)</td><td style='text-align: center; word-wrap: break-word;'>9.5</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>258M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (SpeechTokenizer), AR</td><td style='text-align: center; word-wrap: break-word;'>11.4</td><td style='text-align: center; word-wrap: break-word;'>5.9</td><td style='text-align: center; word-wrap: break-word;'>258M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (dMel)</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>1.8</td><td style='text-align: center; word-wrap: break-word;'>258M</td></tr></table>

<div style="text-align: center;">Table 5: WER (%) (evaluated with WhisperX ASR "base.en") and MOS of different TTS models' generations using transcriptions from each evaluation set that corresponds to data used for training.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Model</td><td colspan="3">WER $ \downarrow $ (%)</td><td style='text-align: center; word-wrap: break-word;'>MOS $ \uparrow $ (95% CI)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LJSpeech</td><td style='text-align: center; word-wrap: break-word;'>LibriTTS</td><td style='text-align: center; word-wrap: break-word;'>VCTK</td><td style='text-align: center; word-wrap: break-word;'>VCTK</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GroundTruth</td><td style='text-align: center; word-wrap: break-word;'>2.6</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>3.4</td><td style='text-align: center; word-wrap: break-word;'>4.18 $ \pm $0.10</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Tacotron2, [39]</td><td style='text-align: center; word-wrap: break-word;'>4.4</td><td style='text-align: center; word-wrap: break-word;'>7.3</td><td style='text-align: center; word-wrap: break-word;'>4.2</td><td style='text-align: center; word-wrap: break-word;'>2.91 $ \pm $0.15</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>FastSpeech2, [36]</td><td style='text-align: center; word-wrap: break-word;'>6.1</td><td style='text-align: center; word-wrap: break-word;'>10.2</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>3.03 $ \pm $0.14</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VITS, [10]</td><td style='text-align: center; word-wrap: break-word;'>6.4</td><td style='text-align: center; word-wrap: break-word;'>8.3</td><td style='text-align: center; word-wrap: break-word;'>11.1</td><td style='text-align: center; word-wrap: break-word;'>3.56 $ \pm $0.12</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (dMel)</td><td style='text-align: center; word-wrap: break-word;'>4.0</td><td style='text-align: center; word-wrap: break-word;'>4.5</td><td style='text-align: center; word-wrap: break-word;'>2.2</td><td style='text-align: center; word-wrap: break-word;'>3.34 $ \pm $0.14</td></tr></table>

<div style="text-align: center;">Table 6: results for TTS models trained on LibriSpeech 960h and evaluated on LJSpeech test set.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Sequence Length</td><td style='text-align: center; word-wrap: break-word;'>Tacotron2</td><td style='text-align: center; word-wrap: break-word;'>FastSpeech2</td><td style='text-align: center; word-wrap: break-word;'>VITS</td><td style='text-align: center; word-wrap: break-word;'>RichTTS</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Total WER $ \downarrow $ (%)</td><td style='text-align: center; word-wrap: break-word;'>4.4</td><td style='text-align: center; word-wrap: break-word;'>6.1</td><td style='text-align: center; word-wrap: break-word;'>6.4</td><td style='text-align: center; word-wrap: break-word;'>4.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>10-20 words</td><td style='text-align: center; word-wrap: break-word;'>5.5</td><td style='text-align: center; word-wrap: break-word;'>3.1</td><td style='text-align: center; word-wrap: break-word;'>7.4</td><td style='text-align: center; word-wrap: break-word;'>3.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>20+ words</td><td style='text-align: center; word-wrap: break-word;'>3.3</td><td style='text-align: center; word-wrap: break-word;'>9.1</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>3.0</td></tr></table>

Furthermore, we observed that the AR model trained on SpeechTokenizer tokens exhibits a much higher WER compared to the idiosyncratic coarse to fine models (labeled AR+NAR) developed for these residual tokenizers – indicating that dMel lies on a simpler data manifold.

Given the success of our LM-style dMe1 TTS model, dubbed RichTTS, we further evaluate it on various datasets, including LJSpeech, VCTK, and LibriTTS, and compare it with popular outsourced TTS models, including Tacotron2 [39], FastSpeech2 [36], and VITS [20]. We conduct human evaluation to measure the naturalness of 50 randomly sampled synthesized speech from VCTK test set. RichTTS achieves competitive performance on the TTS task in terms of both MOS and WER demonstrating its effectiveness in generating high-quality synthesized speech, see Table 5. Interestingly, we find that VITS performs poorly on the VCTK WER. We suspect this is because VITS tends to make more mistakes at the beginning of each sequence, and since VCTK comprises short sequences, even one or two word errors can lead to a high WER.

Furthermore, we observed that our model with dMe1 tokenization can generate long audio sequences with high quality. Here, we evaluate the performance of our model on different lengths of text sequences using the LJSpeech test set. Table 6 shows the WER results for our model on text sequences with 10-20 words and more than 20 words. We ignore text sequences with fewer than 10 words, as they are too short and not robust for WER evaluation. From Table 6, we observe that our model achieves competitive performance across different text lengths, demonstrating its robustness and generalization ability in generating synthesized speech for varying text inputs lengths. Additionally, we find that the non-autoregressive (NAR) model FastSpeech2 achieves the lowest WER on shorter sequences but the highest WER on longer sequences. This suggests that NAR models may not be well-suited for generating long audio sequences.

9

<div style="text-align: center;">Table 7: Speech recognition results for different tokenizers measured with WER (%). All models are trained on LibriSpeech 960h.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>dev-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>dev-other $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-other $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>Params</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichASR (SpeechTokenizer)</td><td style='text-align: center; word-wrap: break-word;'>6.5 $ \pm $0.3</td><td style='text-align: center; word-wrap: break-word;'>16.9 $ \pm $0.7</td><td style='text-align: center; word-wrap: break-word;'>6.9 $ \pm $0.4</td><td style='text-align: center; word-wrap: break-word;'>17.5 $ \pm $0.5</td><td style='text-align: center; word-wrap: break-word;'>258M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichASR (HuBERT+KM)</td><td style='text-align: center; word-wrap: break-word;'>5.3 $ \pm $0.1</td><td style='text-align: center; word-wrap: break-word;'>13.7 $ \pm $0.2</td><td style='text-align: center; word-wrap: break-word;'>5.8 $ \pm $0.1</td><td style='text-align: center; word-wrap: break-word;'>13.8 $ \pm $0.1</td><td style='text-align: center; word-wrap: break-word;'>258M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichASR (dMe1)</td><td style='text-align: center; word-wrap: break-word;'>3.8 $ \pm $0.1</td><td style='text-align: center; word-wrap: break-word;'>10.3 $ \pm $0.1</td><td style='text-align: center; word-wrap: break-word;'>4.2 $ \pm $0.2</td><td style='text-align: center; word-wrap: break-word;'>10.4 $ \pm $0.1</td><td style='text-align: center; word-wrap: break-word;'>258M</td></tr></table>

<div style="text-align: center;">Table 8: Comparison of WER (%) for best RichASR trained with dMel tokenization and prior work with LM-style ASR models and HuBERT+KM with subword modeling on top as tokenization.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>Data (h)</td><td style='text-align: center; word-wrap: break-word;'>dev-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>dev-other $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-other $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>Params</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VOXTLM</td><td style='text-align: center; word-wrap: break-word;'>280k</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>6.5</td><td style='text-align: center; word-wrap: break-word;'>17.6</td><td style='text-align: center; word-wrap: break-word;'>350M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VOXTLM</td><td style='text-align: center; word-wrap: break-word;'>280k</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>4.6</td><td style='text-align: center; word-wrap: break-word;'>12.1</td><td style='text-align: center; word-wrap: break-word;'>1.3B</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Decoder-only ASR [11]</td><td style='text-align: center; word-wrap: break-word;'>960</td><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>7.8</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>8.3</td><td style='text-align: center; word-wrap: break-word;'>355M</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichASR (dMel)</td><td style='text-align: center; word-wrap: break-word;'>960</td><td style='text-align: center; word-wrap: break-word;'>3.1</td><td style='text-align: center; word-wrap: break-word;'>8.4</td><td style='text-align: center; word-wrap: break-word;'>3.4</td><td style='text-align: center; word-wrap: break-word;'>8.6</td><td style='text-align: center; word-wrap: break-word;'>355M</td></tr></table>

### 3.4 LM-Style Speech-to-Text

Training an LM-style speech-to-text (ASR) model can test if the speech tokens can preserve the semantic information in the speech signal and support the speech content-based task. We use the same experiments configuration in Section3.3.1 to train ASR models. Table 7 shows results of our model dubbed RichASR, trained with different tokenizations including dMel for the ASR task. Our LM-style model with dMel speech tokenization achieves 4.2% WER on the test-clean and 10.4% WER on the test-other sets outperforming both HuBERT-KM and SpeechTokenizer. We also observe that our model with HuBERT-KM [24] outperforms the SpeechTokenizer [52] for ASR, which is reasonable as semantic tokens are more suitable for the ASR task.

In Table 8, we further compare RichASR with dMel speech tokenizer trained with GPT-2-medium architecture [33] on LibriSpeech 960h with prior work: VOX-TLM [28] that uses larger model trained with more data and initialized from a pretrained LLM (OPT [51]), and HuBERT-KM with additional subword modeling on top as the speech tokenizer; [11] that also uses GPT-2 architecture trained on LibriSpeech 960h and HuBERT-KM with additional subword modeling on top as the speech tokenizer $ ^{6} $. RichASR with dMel outperforms VOX-TLM; it also outperforms [11] on clean sets and a bit behind it on other sets.

The ASR results clearly demonstrate the benefit of using our dMel speech tokenizer for the content-related tasks in speech, as it better preserves the semantic information in the speech signal. Further details and ablations can be found in Appendix E and F.

### 3.5 Ablations

We first investigate the impact of the codebook sizes, shown in Figure 5. The 16-bin configuration used in the paper demonstrates the best overall performance across tasks. While the 32-bin setup slightly outperforms on the ASR test-other set, it shows degraded performance in TTS. This trade-off likely stems from the increased speech vocabulary size, which may pose challenges for accurate prediction. The results may get better with increased data and model size. And 8-bin configuration looses too much information with discretization.

We then ablate the ASR results to understand why ASR LM-style model is behind the state-of-the-art on LibriSpeech. We take two existing transformer ASR baselines, Seq2Seq and CTC, that use 80 log mel-filterbanks and characters as targets. We then modify these baselines by using dMe1 instead (the discretization, embedding layer and linear layer) while keeping all other hyper-parameters the same (we adjust only the SpecAugment time masking max width accordingly to keep total masking in ms the same). Our results (Appendix Table 12) suggest: i) dMe1 brings only small degradation compared to Mel; ii) additional discrepancy is coming from different hop distance in featurization; iii) the main and significant performance degradation is coming from switching to LM-style model. The latter is

 $ ^{6} $We use official codebase to train this model w/o text pretraining as [11] report results only with text pretraining.

10

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Number of Quantization Bins</th><th style='text-align: center;'>Blue</th><th style='text-align: center;'>Orange</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>ASR-clean</td><td style='text-align: center;'>6.6</td><td style='text-align: center;'>4.4</td></tr>
    <tr><td style='text-align: center;'>ASR-other</td><td style='text-align: center;'>16.5</td><td style='text-align: center;'>10.7</td></tr>
    <tr><td style='text-align: center;'>TTS</td><td style='text-align: center;'>7.3</td><td style='text-align: center;'>4.8</td></tr>
    <tr><td style='text-align: center;'>TTS+other</td><td style='text-align: center;'>16.0</td><td style='text-align: center;'>10.2</td></tr>
    <tr><td style='text-align: center;'>TTS+clean</td><td style='text-align: center;'>3.5</td><td style='text-align: center;'>4.7</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 5: ASR and TTS results (WER, %) with dMel speech tokenizer and different number of bins (codebook size) for discretization in dMel. All models are trained on LibriSpeech 960h.</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Model</th><th style='text-align: center;'>k</th><th style='text-align: center;'>Theoretical inference time (FLOPs)</th><th style='text-align: center;'>Word Error Rate (%) ↓</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>dMel</td><td style='text-align: center;'>6</td><td style='text-align: center;'>0.15</td><td style='text-align: center;'>8.8</td></tr>
    <tr><td style='text-align: center;'>HuBERT</td><td style='text-align: center;'>5</td><td style='text-align: center;'>0.20</td><td style='text-align: center;'>7.0</td></tr>
    <tr><td style='text-align: center;'>dMel</td><td style='text-align: center;'>4</td><td style='text-align: center;'>0.22</td><td style='text-align: center;'>5.8</td></tr>
    <tr><td style='text-align: center;'>HuBERT</td><td style='text-align: center;'>3</td><td style='text-align: center;'>0.25</td><td style='text-align: center;'>5.5</td></tr>
    <tr><td style='text-align: center;'>dMel</td><td style='text-align: center;'>2</td><td style='text-align: center;'>0.40</td><td style='text-align: center;'>5.2</td></tr>
    <tr><td style='text-align: center;'>HuBERT</td><td style='text-align: center;'>1</td><td style='text-align: center;'>1.00</td><td style='text-align: center;'>9.5</td></tr>
    <tr><td style='text-align: center;'>SpeechTokenizer</td><td style='text-align: center;'>1</td><td style='text-align: center;'>1.00</td><td style='text-align: center;'>11.5</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Figure 6: Ablation results on k-frame encoding and decoding.</div>


in line with [28] and [11], though was not discussed in detail by any prior work. We hypothesise this gap is due to observed overfitting of the LM-style models.

Finally, we conduct ablation on k-frame parallel encoding and decoding introduced in Section 2.2. The results are shown in Figure 6. As we can see from this figure,  $ k \leq 4 $ yield similar results to single-frame model, while improves both the training and inference efficiency significantly. In contrast, for SpeechTokenizer, even  $ K = 1 $ is worse than dMel with  $ k = 6 $. This is because the residual nature of VQ tokens in SpeechTokenizer where each channel is a residual of the previous channel, which is not suitable for multi-channel parallel decoding.

### 3.6 Unlocking Joint Speech-Text Modeling

Our model design allows us to train a single model for both ASR and TTS tasks leading to a simpler setup. We train a single model with the same architecture and tokenization as RichTTS, by constructing the training data with <text, speech> and <speech, text> pairs for ASR and TTS tasks, respectively. By mixing these two types of data, we can train a single model for both tasks.

Table 9 shows that the joint model is worse on both tasks, but ASR is affected more than TTS. Comparing our results to VOXITM, which initializes its model from pretrained LLM (OPT) and finetunes it with multiple tasks and datasets, we speculate that our joint model needs text-only training to learn a good LM for better ASR performance. Our model structure trivially allows for this text-only training, but we leave those experiments for future work (for further discussion see Appendix F.3).

## 4 Related Work

Speech Tokenization Recent advancements in speech tokenization have primarily focused on two approaches: semantic tokens and acoustic tokens. This section examines these methods, their combinations, and their limitations, highlighting the need for more efficient and generalizable solutions. Semantic tokens, extracted from self-supervised pretrained speech models, have shown promise in capturing high-level content information. Methods like wav2vec [2] and HuBERT [18] employ k-means clustering on speech representations to generate these tokens. While effective in capturing semantic content, these approaches often struggle with preserving fine-grained acoustic details crucial for high-quality speech synthesis. In contrast, acoustic tokens, derived from pretrained audio compression models, excel at preserving low-level acoustic information. Techniques such as SoundStream [48] and EnCodec [12] utilize residual vector quantization (RVQ) with reconstruction objectives. These methods achieve high-quality audio compression but may not capture higher-level semantic structures effectively.

11

<div style="text-align: center;">Table 9: Results of ASR and TTS jointly trained model on LibriSpeech 960h.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">ASR, WER $ \downarrow $ (%)</td><td colspan="2">TTS</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>test-clean</td><td style='text-align: center; word-wrap: break-word;'>test-other</td><td style='text-align: center; word-wrap: break-word;'>WER $ \downarrow $ (%)</td><td style='text-align: center; word-wrap: break-word;'>CER $ \downarrow $ (%)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VOX $ _{TLM} $+OPT, 350M</td><td style='text-align: center; word-wrap: break-word;'>3.5</td><td style='text-align: center; word-wrap: break-word;'>8.7</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>3.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichASR-RichTTS, single models, 258M</td><td style='text-align: center; word-wrap: break-word;'>4.2</td><td style='text-align: center; word-wrap: break-word;'>10.4</td><td style='text-align: center; word-wrap: break-word;'>4.3</td><td style='text-align: center; word-wrap: break-word;'>1.8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichASR-RichTTS, joint model, 258M</td><td style='text-align: center; word-wrap: break-word;'>7.5</td><td style='text-align: center; word-wrap: break-word;'>15.3</td><td style='text-align: center; word-wrap: break-word;'>4.4</td><td style='text-align: center; word-wrap: break-word;'>1.9</td></tr></table>

Recognizing the complementary nature of semantic and acoustic tokens, recent works have attempted to combine these approaches. AudioLM [8] introduced a three-stage model: semantic modeling, coarse acoustic modeling, and fine acoustic modeling. While comprehensive, this approach introduces complexity and computational overhead. AudioPalm [38] further demonstrated the critical importance of large-scale training data and model parameters for effective multi-stage modeling, highlighting potential generalization issues in low-resource scenarios. An alternative hybrid approach, proposed by Zhang et al. [52], attempts to distill semantic information into acoustic tokens during RVQ model training. However, this method still requires additional pretraining and does not fully achieve a single-stage model architecture.

Despite these advancements, several challenges persist in the field of speech tokenization: i) balancing semantic and acoustic information in a unified representation; ii) reducing model complexity and computational requirements; iii) improving generalization to low-resource / out-of-domain data e.g. with mixed speech from multiple speakers, or multiple languages, or changing characteristics of recording equipment/sampling rate etc.; iv) developing truly single-stage tokenizers. Our proposed method, dMe1, addresses these challenges by offering a training-free speech tokenization approach. By directly discretizing log mel-filterbanks into bins, it inherently preserves both semantic and acoustic information in a unified representation, while significantly reducing computational complexity. Concurrently, [25] proposed a different mel-filterbanks based speech tokens: spectral codecs, where disjointed mel-bands are encoded separately and then quantized using an FSQ [29]. Although spectral codecs and dMe1 are both discretizing mel-filterbanks, dMe1 is encoder-free and tested with autoregressive generation tasks, while spectral codecs need encoders and is tested with nonautgressive generation task. Also, our scalar quantization method shares some similarities with FSQ, but FSQ is in a learned latent code space and necessitates an additional bound operation to limit the range of the latent codes.

Speech-Text Modeling Modeling speech and text jointly is a challenging task, as speech signals are continuous and while text is discrete. Existing works have explored various approaches to address this challenge, including usage of separate encoders for different modalities [1, 5]. Bai et al. [3] proposed an encoder-only model A3T for speech-text modeling, by introducing alignment embedding to encourage cross-modal transfer between text and speech. Although A3T achieved good performance on speech synthesis and editing tasks, it cannot generate text and cannot generalize to long-form generation because of its encoder-only architecture and mask-reconstruction training strategy. VioLA [45] also targets a unified speech-text model which can generate speech and text with a single model, but it is specifically designed for the Encodec [12] style feature, and compelled to model speech tokens in a multi-stage hierarchical manner. Maiti et al. [28] proposed a LM-style model VOX-TLM, to model speech and text jointly. However, VOX-TLM is only models the HuBERT semantic tokens, and relies on an external generation model to transform semantic tokens into waveform, but the speaker and acoustic information are lost. In comparison, the model architecture in this paper is a simple, single stage LM-style transformer model, and can handle both the speech generation and text generation tasks.

## 5 Conclusion

In this work, we proposed dMel, a novel train-free speech tokenization method that discretizes log mel-filterbank energies directly into bins. By operating on the authentic log mel-filterbank representation, dMel inherently generalizes to out-of-domain data (e.g. speech with noise or other languages), preserves both semantic and acoustic information in a unified tokenized representation, and is streamable. Our key contribution is the evaluation of dMel within a unified LM-style transformer architecture for speech recognition (ASR) and speech synthesis (TTS) tasks. Our dMel-based

12

ASR model, RichASR, achieved the lowest word error rate among tokenization methods, robustly preserving semantic content. For TTS, dMel's generation yielded the lowest WER, accurately reconstructing speech waveforms. Our dMel-based TTS model, RichTTS, achieved competitive naturalness, lowest error rates, and long audio generation capabilities.

dMe1's simplicity circumvents separate tokenizers or multi-stage modeling, reducing computational overhead and dependence on pretrained models. By unifying semantic and acoustic modeling, dMe1 enables efficient speech-text modeling frameworks. While initial joint TTS-ASR training showed promise, further work is needed. Our primary contribution demonstrates dMe1's effectiveness for high-performing separate TTS and ASR models within a unified LM-style architecture.

## References

[1] Junyi Ao, Rui Wang, Long Zhou, Chengyi Wang, Shuo Ren, Yu Wu, Shujie Liu, Tom Ko, Qing Li, Yu Zhang, et al. SpeechT5: Unified-modal encoder-decoder pre-training for spoken language processing. arXiv preprint arXiv:2110.07205, 2021.

[2] Alexei Baevski, Yuhao Zhou, Abdelrahman Mohamed, and Michael Auli. wav2vec 2.0: A framework for self-supervised learning of speech representations. Advances in neural information processing systems, 33:12449–12460, 2020.

[3] He Bai, Renjie Zheng, Junkun Chen, Mingbo Ma, Xintong Li, and Liang Huang. A $ ^{3} $T: Alignment-aware acoustic and text pretraining for speech synthesis and editing. In International Conference on Machine Learning, pages 1399–1411. PMLR, 2022.

[4] Max Bain, Jaesung Huh, Tengda Han, and Andrew Zisserman. Whisperx: Time-accurate speech transcription of long-form audio. INTERSPEECH 2023, 2023.

[5] Ankur Bapna, Yu-an Chung, Nan Wu, Anmol Gulati, Ye Jia, Jonathan H Clark, Melvin Johnson, Jason Riesa, Alexis Conneau, and Yu Zhang. Slam: A unified encoder for speech and language modeling via speech-text joint pre-training. arXiv preprint arXiv:2110.10329, 2021.

[6] Samy Bengio, Oriol Vinyals, Navdeep Jaitly, and Noam Shazeer. Scheduled sampling for sequence prediction with recurrent neural networks. Advances in neural information processing systems, 28, 2015.

[7] Dmitry Bogdanov, Minz Won, Philip Tovstogan, Alastair Porter, and Xavier Serra. The mtg-jamendo dataset for automatic music tagging. In ML4MD Machine Learning for Music Discovery Workshop, ICML, 2019.

[8] Zalán Borsos, Raphaël Marinier, Damien Vincent, Eugene Kharitonov, Olivier Pietquin, Matt Sharifi, Dominik Roblek, Olivier Teboul, David Grangier, Marco Tagliasacchi, et al. Audiolm: a language modeling approach to audio generation. IEEE/ACM Transactions on Audio, Speech, and Language Processing, 2023.

[9] Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. Language models are few-shot learners. Advances in neural information processing systems, 33:1877–1901, 2020.

[10] Edresson Casanova, Julian Weber, Christopher D Shulby, Arnaldo Candido Junior, Eren Gölge, and Moacir A Ponti. Yourtts: Towards zero-shot multi-speaker tts and zero-shot voice conversion for everyone. In International Conference on Machine Learning, pages 2709–2720. PMLR, 2022.

[11] Qian Chen, Wen Wang, Qinglin Zhang, Siqi Zheng, Shiliang Zhang, Chong Deng, Yukun Ma, Hai Yu, Jiaqing Liu, and Chong Zhang. Loss masking is not needed in decoder-only transformer for discrete-token-based asr. In ICASSP 2024-2024 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), pages 11056–11060. IEEE, 2024.

[12] Alexandre Défossez, Jade Copet, Gabriel Synnaeve, and Yossi Adi. High fidelity neural audio compression. arXiv preprint arXiv:2210.13438, 2022.

13

[13] Alexandre Défossez, Laurent Mazaré, Manu Orsini, Amélie Royer, Patrick Pérez, Hervé Jégou, Edouard Grave, and Neil Zeghidour. Moshi: a speech-text foundation model for real-time dialogue. arXiv preprint arXiv:2410.00037, 2024.

[14] Linhao Dong, Shuang Xu, and Bo Xu. Speech-transformer: a no-recurrence sequence-to-sequence model for speech recognition. In 2018 IEEE international conference on acoustics, speech and signal processing (ICASSP), pages 5884–5888. IEEE, 2018.

[15] Alex Graves, Santiago Fernández, Faustino Gomez, and Jürgen Schmidhuber. Connectionist temporal classification: labelling unsegmented sequence data with recurrent neural networks. In Proceedings of the 23rd International Conference on Machine Learning, pages 369–376, 2006.

[16] Anmol Gulati, James Qin, Chung-Cheng Chiu, Niki Parmar, Yu Zhang, Jiahui Yu, Wei Han, Shibo Wang, Zhengdong Zhang, Yonghui Wu, et al. Conformer: Convolution-augmented transformer for speech recognition. arXiv preprint arXiv:2005.08100, 2020.

[17] Andrew Hines, Jan Skoglund, Anil Kokaram, and Naomi Harte. Visqol: The virtual speech quality objective listener. In IWAENC 2012; international workshop on acoustic signal enhancement, pages 1–4. VDE, 2012.

[18] Wei-Ning Hsu, Benjamin Bolte, Yao-Hung Hubert Tsai, Kushal Lakhotia, Ruslan Salakhutdinov, and Abdelrahman Mohamed. Hubert: Self-supervised speech representation learning by masked prediction of hidden units. IEEE/ACM Transactions on Audio, Speech, and Language Processing, 29:3451–3460, 2021.

[19] Keith Ito and Linda Johnson. The lj speech dataset. https://keithito.com/LJ-Speech-Dataset/, 2017.

[20] Jaehyeon Kim, Jungil Kong, and Juhee Son. Conditional variational autoencoder with adversarial learning for end-to-end text-to-speech. In International Conference on Machine Learning, pages 5530–5540. PMLR, 2021.

[21] Jaehyeon Kim, Keon Lee, Seungjun Chung, and Jaewoong Cho. CLam-TTS: Improving neural codec language model for zero-shot text-to-speech. In The Twelfth International Conference on Learning Representations, 2024. URL https://openreview.net/forum?id=ofzeypWosV.

[22] Sehoon Kim, Amir Gholami, Albert Shaw, Nicholas Lee, Karttikeya Mangalam, Jitendra Malik, Michael W Mahoney, and Kurt Keutzer. Squeezeformer: An efficient transformer for automatic speech recognition. Advances in Neural Information Processing Systems, 35:9361–9373, 2022.

[23] Jungil Kong, Jaehyeon Kim, and Jaekyoung Bae. Hifi-gan: Generative adversarial networks for efficient and high fidelity speech synthesis. Advances in neural information processing systems, 33:17022–17033, 2020.

[24] Kushal Lakhotia, Eugene Kharitonov, Wei-Ning Hsu, Yossi Adi, Adam Polyak, Benjamin Bolte, Tu-Anh Nguyen, Jade Copet, Alexei Baevski, Abdelrahman Mohamed, et al. On generative spoken language modeling from raw audio. Transactions of the Association for Computational Linguistics, 9:1336–1354, 2021.

[25] Ryan Langman, Ante Jukić, Kunal Dhawan, Nithin Rao Koluguri, and Boris Ginsburg. Spectral codecs: Spectrogram-based audio codecs for high quality speech synthesis. arXiv preprint arXiv:2406.05298, 2024.

[26] Matthew Le, Apoorv Vyas, Bowen Shi, Brian Karrer, Leda Sari, Rashel Moritz, Mary Williamson, Vimal Manohar, Yossi Adi, Jay Mahadeokar, and Wei-Ning Hsu. Voicebox: Text-guided multilingual universal speech generation at scale, 2023.

[27] Sang-gil Lee, Wei Ping, Boris Ginsburg, Bryan Catanzaro, and Sungroh Yoon. Bigvgan: A universal neural vocoder with large-scale training. In The Eleventh International Conference on Learning Representations, 2023.

[28] Soumi Maiti, Yifan Peng, Shukjae Choi, Jee-weon Jung, Xuankai Chang, and Shinji Watanabe. Voxtlm: Unified decoder-only models for consolidating speech recognition, synthesis and speech, text continuation tasks. In ICASSP 2024-2024 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), pages 13326–13330. IEEE, 2024.

14

[29] Fabian Mentzer, David Minnen, Eirikur Agustsson, and Michael Tschannen. Finite scalar quantization: Vq-vae made simple. arXiv preprint arXiv:2309.15505, 2023.

[30] Pooneh Mousavi, Luca Della Libera, Jarod Duret, Artem Ploujnikov, Cem Subakan, and Mirco Ravanelli. Dasb–discrete audio and speech benchmark. arXiv preprint arXiv:2406.14294, 2024.

[31] Vassil Panayotov, Guoguo Chen, Daniel Povey, and Sanjeev Khudanpur. Librispeech: an asr corpus based on public domain audio books. In 2015 IEEE international conference on acoustics, speech and signal processing (ICASSP), pages 5206–5210. IEEE, 2015.

[32] Daniel S. Park, William Chan, Yu Zhang, Chung-Cheng Chiu, Barret Zoph, Ekin D. Cubuk, and Quoc V. Le. Specaugment: A simple data augmentation method for automatic speech recognition. In Gernot Kubin and Zdravko Kacic, editors, Interspeech 2019, 20th Annual Conference of the International Speech Communication Association, Graz, Austria, 15-19 September 2019, pages 2613–2617. ISCA, 2019. doi: 10.21437/INTERSPEECH.2019-2680. URL https://doi.org/10.21437/Interspeech.2019-2680.

[33] Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, Ilya Sutskever, et al. Language models are unsupervised multitask learners. OpenAI blog, 1(8):9, 2019.

[34] Alec Radford, Jong Wook Kim, Tao Xu, Greg Brockman, Christine McLeavey, and Ilya Sutskever. Robust speech recognition via large-scale weak supervision. In International Conference on Machine Learning, pages 28492–28518. PMLR, 2023.

[35] Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J Liu. Exploring the limits of transfer learning with a unified text-to-text transformer. Journal of machine learning research, 21(140):1–67, 2020.

[36] Yi Ren, Chenxu Hu, Xu Tan, Tao Qin, Sheng Zhao, Zhou Zhao, and Tie-Yan Liu. Fastspeech 2: Fast and high-quality end-to-end text to speech. arXiv preprint arXiv:2006.04558, 2020.

[37] Andrew Rouditchenko, Ronan Collobert, and Tatiana Likhomanenko. AV-CPL: Continuous pseudo-labeling for audio-visual speech recognition. In ECCV 2024 Workshop - AVGenL: Audio-Visual Generation and Learning, 2024.

[38] Paul K Rubenstein, Chulayuth Asawaroengchai, Duc Dung Nguyen, Ankur Bapna, Zalán Borsos, Félix de Chaumont Quitry, Peter Chen, Dalia El Badawy, Wei Han, Eugene Kharitonov, et al. Audiopalm: A large language model that can speak and listen. arXiv preprint arXiv:2306.12925, 2023.

[39] Jonathan Shen, Ruoming Pang, Ron J Weiss, Mike Schuster, Navdeep Jaitly, Zongheng Yang, Zhifeng Chen, Yu Zhang, Yuxuan Wang, Rj Skerrv-Ryan, et al. Natural tts synthesis by conditioning wavenet on mel spectrogram predictions. In 2018 IEEE international conference on acoustics, speech and signal processing (ICASSP), pages 4779–4783. IEEE, 2018.

[40] Bowen Shi, Wei-Ning Hsu, Kushal Lakhotia, and Abdelrahman Mohamed. Learning audiovisual speech representation by masked multimodal cluster prediction. In International Conference on Learning Representations, 2022. URL https://openreview.net/forum?id=Z1Qlm11uOM.

[41] Jianlin Su, Murtadha Ahmed, Yu Lu, Shengfeng Pan, Wen Bo, and Yunfeng Liu. Roformer: Enhanced transformer with rotary position embedding. Neurocomputing, 568:127063, 2024.

[42] Hawa Toyin. A unified model for text-to-speech and speech-to-text. 2024.

[43] Ehsan Variani, Xin Lei, Erik McDermott, Ignacio Lopez Moreno, and Javier Gonzalez-Dominguez. Deep neural networks for small footprint text-dependent speaker verification. In 2014 IEEE international conference on acoustics, speech and signal processing (ICASSP), pages 4052–4056. IEEE, 2014.

[44] Chengyi Wang, Sanyuan Chen, Yu Wu, Ziqiang Zhang, Long Zhou, Shujie Liu, Zhuo Chen, Yanqing Liu, Huaming Wang, Jinyu Li, et al. Neural codec language models are zero-shot text to speech synthesizers. arXiv preprint arXiv:2301.02111, 2023.

15

[45] Tianrui Wang, Long Zhou, Ziqiang Zhang, Yu Wu, Shujie Liu, Yashesh Gaur, Zhuo Chen, Jinyu Li, and Furu Wei. Viola: Unified codec language models for speech recognition, synthesis, and translation. arXiv preprint arXiv:2305.16107, 2023.

[46] Junichi Yamagishi, Christophe Veaux, and Kirsten MacDonald. Cstr vctk corpus: English multi-speaker corpus for cstr voice cloning toolkit (version 0.92). University of Edinburgh. The Centre for Speech Technology Research (CSTR). https://datashare.ed.ac.uk/handle/10283/2950, 2019.

[47] Ryuichi Yamamoto, Eunwoo Song, and Jae-Min Kim. Parallel wavegan: A fast waveform generation model based on generative adversarial networks with multi-resolution spectrogram. In ICASSP 2020-2020 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), pages 6199–6203. IEEE, 2020.

[48] Neil Zeghidour, Alejandro Luebs, Ahmed Omran, Jan Skoglund, and Marco Tagliasacchi. Soundstream: An end-to-end neural audio codec. IEEE/ACM Transactions on Audio, Speech, and Language Processing, 30:495–507, 2021.

[49] Heiga Zen, Viet Dang, Rob Clark, Yu Zhang, Ron J Weiss, Ye Jia, Zhifeng Chen, and Yonghui Wu. Libritts: A corpus derived from librispeech for text-to-speech. arXiv preprint arXiv:1904.02882, 2019.

[50] Dong Zhang, Shimin Li, Xin Zhang, Jun Zhan, Pengyu Wang, Yaqian Zhou, and Xipeng Qiu. Speechgpt: Empowering large language models with intrinsic cross-modal conversational abilities. arXiv preprint arXiv:2305.11000, 2023.

[51] Susan Zhang, Stephen Roller, Naman Goyal, Mikel Artetxe, Moya Chen, Shuohui Chen, Christopher Dewan, Mona Diab, Xian Li, Xi Victoria Lin, et al. Opt: Open pre-trained transformer language models. arXiv preprint arXiv:2205.01068, 2022.

[52] Xin Zhang, Dong Zhang, Shimin Li, Yaqian Zhou, and Xipeng Qiu. Speechtokenizer: Unified speech tokenizer for speech large language models. arXiv preprint arXiv:2308.16692, 2023.

16

### A Ethics Statement

The development and deployment of speech technologies carry important ethical considerations. While our proposed dMe1 method aims to advance the state-of-the-art in speech-text modeling, it is crucial to highlight potential ethical risks and raise the awareness so that new methods may be developed to mitigate these risks.

Our first main concern is the potential dual-use of speech synthesis technologies for nefarious purposes such as impersonation, misleading audio-visual content generation, or voice spoofing attacks. Proactive measures, including watermarking techniques and robust speaker verification methods, should be explored to counter such risks. The former attempts to build markers into the generated speech that make it easy to detect, while the latter focusses on distinguishing synthetic from real data. Prior work [26] has shown that neural networks can be trained to distinguish speech synthesized from their model from real speech, probably because of artifacts from the use of mel spectral vocoders. While we did not train a network to do so in our work yet (we will create one before code release), the vocoders we use are similar to their work – going from mel spectrogram to raw waveforms. Our model also does not use prosody, phoneme duration and other predictions that more sophisticated TTS systems use to allow the model to perform very well on imitating speaker styles in zero-shot settings. However our model can probably mimic the styles of training speakers very well. It is our hope that releasing our methods will facilitate more research on fake speech verification and watermarking techniques – even if current classifiers are able to perform this detection, the quality of the generative models is improving. It is also our hope that future works will attempt to perform more credit assignment – by providing metrics that show which real data samples a synthetic speech example copies its style and substance from.

Another concern is the perpetuation of societal biases encoded within training data. Speech datasets may exhibit biases along dimensions such as gender, race, age, or socioeconomic status, which could be propagated or amplified by trained models. Rigorous debiasing techniques and careful curation of representative training data are essential to mitigate these risks. On the mitigating side of this equation, we also hope that with better, more controllable TTS systems, ASR systems can improve because more data can be generated for underrepresented segments of the distribution from the TTS models.

Furthermore, the development and deployment of speech technologies should prioritize accessibility and inclusivity. Models should be evaluated for performance across diverse demographics, accents, and language varieties to ensure equitable access and quality of service.

Finally, it is important to foster transparency and accountability in the research and development process. Clear documentation of model capabilities, limitations, and potential failure modes should be provided to enable informed decision-making and responsible usage.

Addressing these ethical considerations requires a multistakeholder approach involving researchers, developers, policymakers, and end-users. By prioritizing ethical principles such as fairness, privacy, and accountability, we can work towards realizing the benefits of speech technologies while mitigating potential risks and adverse societal impacts.

### B Limitations

Because TTS work is tremendously fragmented and clear protocols are not often available for training and evaluation, we reimplemented other tokenizers within our code base using publicly available, official implementations where available: e.g. we used Hubert-KM and speech tokenizer features extraction from the public codebases and plugged them into our LM-style model training. While we made the best effort to tune the tokenization methods and the models, there is always a possibility we missed some details. However, our results seem to tell a consistent story when viewed from multiple angles, and when viewed on multiple datasets. We also did not train on larger model sizes (>1B parameters), larger datasets (>1k hours), or using pretrained models.

The real challenge for modern multimodal LLMs is complex semantic understanding tasks. While our current experiments focus on text-to-speech and speech-to-text tasks, these encompass critical aspects of speech processing. dMel's effective performance within a decoder-only architecture for both tasks suggests potential for broader applications. We recognize the importance of more sophisticated

17

speech understanding tasks and view our work as a foundation for future research leaving other tasks out of scope of the paper. Scaling up pretraining and exploring complex semantic understanding tasks could further validate our approach's versatility across a wider range of multimodal language processing challenges.

We acknowledge that our current scope targets only speech on purpose, as indicated in our title. While dMel may potentially support non-speech tasks, our current exploration and verification focus solely on speech, not general audio. Regarding the “speaker variations” – mel-spectrogram is used for speaker recognition widely, thus it preserves necessary speaker information on which we thus rely in dMel too.

### C Data, Code, Reproducibility

We made the best effort to use publicly available data and official implementations of prior works where it is possible. All data we used are under permissive license for research. We provided as much as detail as is possible without code such as details on our model training and hyperparameters throughout the paper and in the Appendix. We plan to open-source our code upon paper acceptance.

We do not plan to open-source any pre-trained models for sake of privacy, safety and misuse.

### D Subjective Evaluation for TTS

We use crowd-sourcing to collect subjective ratings to compare the naturalness of the reconstructed speech from the different tokenizers. We evaluate the quality of the same (randomly sampled) 50 utterances for each model by collecting around seven ratings per sample. Overall, we collect 3500 ratings from 65 raters. The raters were English-speaking and were paid at least the minimum wage.

We present the raters with a generated speech sample and instruct them to rate how natural it sounds on a five-point Likert scale, where 1 corresponds to very unnatural and 5 corresponds to very natural. Figure 7 shows a screenshot of our subjective test as seen by the rater.

<div style="text-align: center;"><img src="imgs/img_in_image_box_300_824_919_959.jpg" alt="Image" width="50%" />

Please listen to the computer generated speech sample below and rate how natural (i.e., human-like) it sounds on a scale from 1 (very unnatural) to 5 (very natural).
How natural (i.e., human-sounding) is this speech sample?
Very unnatural Somewhat unnatural Neither natural nor unnatural Somewhat natural Very natural

</div>


<div style="text-align: center;">Figure 7: A screenshot of the assessment task, as the crowd-sourced rater sees it.</div>


We noticed human annotators have bias over audio volume so we do volume normalization on top of all reconstructed or generated audio before giving them to human annotators.

We report Mean Opinion Score (MOS) results throughout the paper with confidence intervals calculated using bootstrap resampling with 1000 iterations, providing a reliable estimate of the variability MOS results.

### E Training Details

### E.1 Baselines

For reproducibility, we provide the HuggingFace model cards used in our experiments in Table 5:

• Tacotron2 [39], https://huggingface.co/espnet/espnet/kan-bayashi_vctk_tts_train_xvector_tacotron2_raw_phn_tacotron_g2p_en_no_space_train.loss.ave

• FastSpeech2 [36], https://huggingface.co/espnet/kan-bayashi_vctk_gst_fastspeech2

• VITS [10], https://huggingface.co/espnet/kan-bayashi_vctk_multi_spk_vits

18

• ParallelWaveGAN [47], https://github.com/kan-bayashi/ParallelWaveGAN/blob/master/egs/libritts/voc1/conf/parallel_wavegan.v1.yaml

HifiGAN [23], https://github.com/kan-bayashi/ParallelWaveGAN/blob/master/egs/libritts/voc1/conf/hifigan.v1.yaml

• BigVGAN [27], https://huggingface.co/nvidia/bigvgan_24khz_100band

### E.2 RichASR and RichTTS

For our LM-style model we stack together speaker embedding, speech tokens and text tokens. Both speech and text tokens have prepended begin of sentence token (<bos>) and appended end of sentence token (<eos>).

We train all models using the Adam optimizer with a learning rate of  $ 1e^{-3} $, learning rate warmup of 4k steps for ASR and 5k for TTS, cosine learning rate schedule and gradient clipping of 1.0 for TTS and 0.1 for ASR and joint models. We use dynamic batching to optimize the data packing with total batch size of  $ 1.4h/1.4h/0.7h $ for ASR training and  $ 1h/2h/2h $ for TTS training for Small/Base/Large models. We train TTS models for 100k steps and ASR models 80k steps with mixed precision training and BF16 on A100 and H100 GPUs with 80GB. Both ASR models and TTS models are trained with 8GPUs for less than a day and for 2-4 days for ASR and TTS respectively.

<div style="text-align: center;">Table 10: LM-style transformer model configurations for ASR, TTS and joint models training.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Small</td><td style='text-align: center; word-wrap: break-word;'>Base</td><td style='text-align: center; word-wrap: break-word;'>Large</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># of layers</td><td style='text-align: center; word-wrap: break-word;'>18</td><td style='text-align: center; word-wrap: break-word;'>36</td><td style='text-align: center; word-wrap: break-word;'>48</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># of attention heads</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>4</td><td style='text-align: center; word-wrap: break-word;'>8</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># of hidden units  $ D $</td><td style='text-align: center; word-wrap: break-word;'>512</td><td style='text-align: center; word-wrap: break-word;'>768</td><td style='text-align: center; word-wrap: break-word;'>1536</td></tr><tr><td style='text-align: center; word-wrap: break-word;'># of parameters</td><td style='text-align: center; word-wrap: break-word;'>59M</td><td style='text-align: center; word-wrap: break-word;'>258M</td><td style='text-align: center; word-wrap: break-word;'>1.3B</td></tr></table>

### E.3 LM-Style Speech-to-Text

For ASR training as an augmentation we apply SpecAugment [32] with 2 frequency masks with max width 30 and 10 time masks with max width 50 and ratio 0.1. With ablations we found that SpecAugment masking with average value instead of zero is slightly better. Without applying SpecAugment performance of ASR is 7.3% WER on dev-clean and 20.3% WER on dev-other, which is further can be improved with usage of frequency masking only to 6.4% WER on dev-clean and 16.6% WER on dev-other. Usage of both frequency masking and time masking results in the best performance of Table 7.

We found that span masking is key part of model training to enforce self-attention to attend to speech part as well as to reduce exposure bias. The masking strategy is similar to the one used for TTS training: for every training step with probability $p$ the sample in the minibatch is masked with the mean span of 3 tokens with masking ration of 0.5. We found that the mean span of 1 token or 5 tokens gives the same results; while the mask probability $p$ is the most important hyper-parameter. The optimal value for ASR is found to be 0.8, which is used in all final models.

As we found one best model configuration for the Base model with dMel we then change only i) model size ii) speech tokenization iii) training data (here we increase model dropout to 0.3 for training on train-clean-360 and to 0.5 for training on train-clean-100 as otherwise models drastically overfit); the rest of hyper-parameters stay the same.

### F Ablations

### F.1 LM-Style Text-to-Speech

Scaling results for RichTTS are shown in Table 11.

### F.2 LM-Style Speech-to-Text

ASR ablations for different model sizes, data sizes, and tokenizers are shown in Table 13.

19

<div style="text-align: center;">Table 11: Text-to-speech results for different model sizes with dMel. All models are trained on LibriSpeech 960h dataset. Evaluation is done via speech generation on the full test-clean transcriptions and speakers, and then evaluated WER with WhisperX base.en.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>WER $ \downarrow $ (%)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (dMel), Small</td><td style='text-align: center; word-wrap: break-word;'>8.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (dMel), Base</td><td style='text-align: center; word-wrap: break-word;'>4.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RichTTS (dMel), Large</td><td style='text-align: center; word-wrap: break-word;'>5.4</td></tr></table>

<div style="text-align: center;">Table 12: WER (%) comparison for CTC, Seq2Seq, and LM-style ASR models (~260M) trained on LibriSpeech 960h with dMel and Mel features. We compute 80 log-mel-filterbanks with 25ms (50ms) window and 10ms (25ms) hop distance, denoted as ‘10ms’ (‘25ms’).</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>Features</td><td style='text-align: center; word-wrap: break-word;'>dev-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>dev-other $ \downarrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[16] (RNN-T - Conformer)</td><td style='text-align: center; word-wrap: break-word;'>Mel-10ms</td><td style='text-align: center; word-wrap: break-word;'>1.9</td><td style='text-align: center; word-wrap: break-word;'>4.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>[22] (CTC - Squeezeformer)</td><td style='text-align: center; word-wrap: break-word;'>Mel-10ms</td><td style='text-align: center; word-wrap: break-word;'>2.3</td><td style='text-align: center; word-wrap: break-word;'>5.8</td></tr><tr><td rowspan="4">Seq2Seq [14]</td><td style='text-align: center; word-wrap: break-word;'>Mel-10ms</td><td style='text-align: center; word-wrap: break-word;'>2.4</td><td style='text-align: center; word-wrap: break-word;'>5.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-10ms</td><td style='text-align: center; word-wrap: break-word;'>2.5</td><td style='text-align: center; word-wrap: break-word;'>5.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mel-25ms</td><td style='text-align: center; word-wrap: break-word;'>2.8</td><td style='text-align: center; word-wrap: break-word;'>6.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-25ms</td><td style='text-align: center; word-wrap: break-word;'>2.7</td><td style='text-align: center; word-wrap: break-word;'>6.2</td></tr><tr><td rowspan="4">CTC [15]</td><td style='text-align: center; word-wrap: break-word;'>Mel-10ms</td><td style='text-align: center; word-wrap: break-word;'>2.1</td><td style='text-align: center; word-wrap: break-word;'>5.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-10ms</td><td style='text-align: center; word-wrap: break-word;'>2.1</td><td style='text-align: center; word-wrap: break-word;'>5.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mel-25ms</td><td style='text-align: center; word-wrap: break-word;'>2.1</td><td style='text-align: center; word-wrap: break-word;'>5.4</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel-25ms</td><td style='text-align: center; word-wrap: break-word;'>2.3</td><td style='text-align: center; word-wrap: break-word;'>6.1</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>LM-style</td><td style='text-align: center; word-wrap: break-word;'>dMel-25ms</td><td style='text-align: center; word-wrap: break-word;'>3.4</td><td style='text-align: center; word-wrap: break-word;'>9.5</td></tr></table>

We noticed the results in [11] seems to be the SOTA for LM-style ASR model to the best of our knowledge. However, as many ablations are missed in [11], we took their open-sourced code and run ablations ourselves to have proper comparison with it. The final results, including ablation with dMe1 are shown in Table 14:

• We successfully reproduced [11] results (row 1 and 2).

• Without pretraining (rows 3, 4, 5):

dMel outperforms HuBERT-KM on both clean and other datasets; dMel surpasses BPE on top of HuBERT-KM on clean data, while BPE on HuBERT-KM performs better on other.

• Without pretraining and without speed perturbation (rows 6, 7, 8):

BPE on HuBERT-KM performance decreases significantly after diabling speed perturbation (compare rows 3 and 6), raising questions about its generalizability to other domains, given that BPE tokens are trained on speed-perturbed LibriSpeech data.

Our dMel (row 8) achieves substantially better results than both HuBERT-KM and BPE on HuBERT-KM (rows 7 and 6), demonstrating robust performance even without speed augmentation.

Note that in dMel, we use SpecAugment (masking across time and channels) and [11] also use SpecAugment. According to their code, the time masking is 30%, while channel masking is impossible as there is only 1 channel).

We believe these results demonstrate the effectiveness, simplicity in use, and robustness of our dMel tokenization method, particularly in scenarios where extensive pretraining or domain-specific augmentations may not be feasible.

Note that [11] did not show applicability of BPE on HuBERT-KM or HuBERT-KM to TTS task, while in VOX $ _{TLM} $ (also uses BPE on HuBERT-KM) it is shown that this tokenization is not suited for TTS (the performance is poor). dMe1 in contrary is shown to perform well on TTS task too in addition to ASR.

20

<div style="text-align: center;">Table 13: Our ASR models trained on different subsets (train-clean-100 LS-100, train-clean-360 LS-360, full LibriSpeech LS-960) of LibriSpeech, with different model sizes and different speech tokenizations (greedy decoding is reported). Results are shown across 2 runs with mean WER and standard deviation.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Tokenization</td><td style='text-align: center; word-wrap: break-word;'>Model Size</td><td style='text-align: center; word-wrap: break-word;'>Data</td><td style='text-align: center; word-wrap: break-word;'>dev-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>dev-other $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-other $ \downarrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel</td><td rowspan="2">Base</td><td style='text-align: center; word-wrap: break-word;'>LS-100</td><td style='text-align: center; word-wrap: break-word;'>$ 18.1 \pm 1.0 $</td><td style='text-align: center; word-wrap: break-word;'>$ 39.4 \pm 1.2 $</td><td style='text-align: center; word-wrap: break-word;'>$ 19.0 \pm 1.0 $</td><td style='text-align: center; word-wrap: break-word;'>$ 41.3 \pm 1.1 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel</td><td style='text-align: center; word-wrap: break-word;'>LS-360</td><td style='text-align: center; word-wrap: break-word;'>$ 6.4 \pm 0.4 $</td><td style='text-align: center; word-wrap: break-word;'>$ 20.1 \pm 1.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 6.9 \pm 0.6 $</td><td style='text-align: center; word-wrap: break-word;'>$ 20.5 \pm 0.9 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SpeechTokenizer [52]</td><td rowspan="3">Small</td><td rowspan="3">LS-960</td><td style='text-align: center; word-wrap: break-word;'>$ 6.2 \pm 0.2 $</td><td style='text-align: center; word-wrap: break-word;'>$ 16.8 \pm 0.3 $</td><td style='text-align: center; word-wrap: break-word;'>$ 6.5 \pm 0.2 $</td><td style='text-align: center; word-wrap: break-word;'>$ 17.4 \pm 0.3 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HuBERT+KM [24]</td><td style='text-align: center; word-wrap: break-word;'>$ 5.8 \pm 0.2 $</td><td style='text-align: center; word-wrap: break-word;'>$ 14.6 \pm 0.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 6.0 \pm 0.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 14.9 \pm 0.1 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel</td><td style='text-align: center; word-wrap: break-word;'>$ 6.0 \pm 0.4 $</td><td style='text-align: center; word-wrap: break-word;'>$ 15.2 \pm 0.8 $</td><td style='text-align: center; word-wrap: break-word;'>$ 6.1 \pm 0.4 $</td><td style='text-align: center; word-wrap: break-word;'>$ 15.7 \pm 0.7 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SpeechTokenizer [52]</td><td rowspan="3">Base</td><td rowspan="3">LS-960</td><td style='text-align: center; word-wrap: break-word;'>$ 6.5 \pm 0.3 $</td><td style='text-align: center; word-wrap: break-word;'>$ 16.9 \pm 0.7 $</td><td style='text-align: center; word-wrap: break-word;'>$ 6.9 \pm 0.4 $</td><td style='text-align: center; word-wrap: break-word;'>$ 17.5 \pm 0.5 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HuBERT+KM [24]</td><td style='text-align: center; word-wrap: break-word;'>$ 5.3 \pm 0.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 13.7 \pm 0.2 $</td><td style='text-align: center; word-wrap: break-word;'>$ 5.8 \pm 0.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 13.8 \pm 0.1 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMel</td><td style='text-align: center; word-wrap: break-word;'>$ 3.8 \pm 0.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 10.3 \pm 0.1 $</td><td style='text-align: center; word-wrap: break-word;'>$ 4.2 \pm 0.2 $</td><td style='text-align: center; word-wrap: break-word;'>$ 10.4 \pm 0.1 $</td></tr></table>

<div style="text-align: center;">Table 14: Ablations on the LM-style ASR model with GPT-2 architecture using the setup from [11]: we ablate pretraining with text, speed perturbation and speech tokenization methods. All models are trained on LibriSpeech 960h. We report WER (%) on LibriSpeech validation and test sets.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Tokenization</td><td style='text-align: center; word-wrap: break-word;'>Text Pretraining</td><td style='text-align: center; word-wrap: break-word;'>Speed Perturbation</td><td style='text-align: center; word-wrap: break-word;'>dev-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>dev-other $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-clean $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>test-other $ \downarrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BPE on HuBERT+KM, [11]</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2.9</td><td style='text-align: center; word-wrap: break-word;'>6.2</td><td style='text-align: center; word-wrap: break-word;'>3.0</td><td style='text-align: center; word-wrap: break-word;'>6.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BPE on HuBERT+KM, reproduction</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2.9</td><td style='text-align: center; word-wrap: break-word;'>6.3</td><td style='text-align: center; word-wrap: break-word;'>3.2</td><td style='text-align: center; word-wrap: break-word;'>6.7</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BPE on HuBERT+KM</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>3.6</td><td style='text-align: center; word-wrap: break-word;'>7.8</td><td style='text-align: center; word-wrap: break-word;'>3.8</td><td style='text-align: center; word-wrap: break-word;'>8.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HuBERT+KM</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>5.1</td><td style='text-align: center; word-wrap: break-word;'>8.9</td><td style='text-align: center; word-wrap: break-word;'>5.5</td><td style='text-align: center; word-wrap: break-word;'>9.3</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMe1</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>3.1</td><td style='text-align: center; word-wrap: break-word;'>8.4</td><td style='text-align: center; word-wrap: break-word;'>3.4</td><td style='text-align: center; word-wrap: break-word;'>8.6</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BPE on HuBERT+KM</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>5.4</td><td style='text-align: center; word-wrap: break-word;'>9.7</td><td style='text-align: center; word-wrap: break-word;'>5.3</td><td style='text-align: center; word-wrap: break-word;'>10.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HuBERT+KM</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>6.0</td><td style='text-align: center; word-wrap: break-word;'>10.5</td><td style='text-align: center; word-wrap: break-word;'>6.4</td><td style='text-align: center; word-wrap: break-word;'>10.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dMe1</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>3.7</td><td style='text-align: center; word-wrap: break-word;'>9.7</td><td style='text-align: center; word-wrap: break-word;'>3.9</td><td style='text-align: center; word-wrap: break-word;'>9.5</td></tr></table>

### F.3 Joint Speech-Text Modeling Discussion

We found it to be challenging to train joint model for ASR and TTS, similar to observations as in [28] and e.g. [40, 37] for joint audio-visual speech recognition. Also, there is a very recent research work [42], that also shows training TTS and ASR jointly is challenging, and needs carefully designed model architecture and training loss fusion technique.

One of the reasons is the different pace of learning. Careful consideration of training strategies can mitigate some of the challenges in joint modeling of TTS and ASR tasks, highlighting the complexities inherent in combining these distinct but related tasks within a single model.

Another reason we suspect is the mismatch between train and test time, which is more pronounced for the joint modeling: if we compare individual validation losses per task in joint model to their one-task training counterparts we see they match each other (so training is fine), however the generation (test time which mismatches how the train loss is defined) for both tasks is broken: longer sequences has hallucination and high repetition issues. This could be due to different length of sequences between text and audio and thus learnt attention pattern could be different which creates longer sequences generation issue for the joint model.

Last but not the least, the two tasks have opposite modalities in the input and output, making it rather difficult to model. Most previously researched multi-task work have the same modality in the output. The combination of ASR and TTS is a rather recent phenomenon, such as Viola and VOX.

21