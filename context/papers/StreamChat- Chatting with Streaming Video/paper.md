                                                                             StreamChat: Chatting with Streaming Video

                                                        Jihao Liu1,2,∗            Zhiding Yu2  Shiyi Lan2 Shihao Wang2,5,∗ Rongyao Fang1
                                                                                 Jan Kautz2 Hongsheng Li1,3,4  Jose M. Alvarez2
                                                                                                          1                         2
                                                                                                              CUHK MMLab                NVIDIA
                                                                                             3                                  4
                                                                                                 Shanghai AI Laboratory             CPII under InnoHK
                                                                                                   5
                                                                                                       The Hong Kong Polytechnic University




arXiv:2412.08646v2 [cs.CV] 30 Mar 2025
                                           (11s) Question: What you are seeing now is my POV. Please describe my surrounding environment.                                                        Video Stream




                                           (11s) Text stream: You are standing in a dim room with a carpet on the floor and a door to your left that is slightly ajar… some furniture and items scattered…
                                                                                                                                                                                                 Video Stream




                                           You can see a television turned on and a guitar leaning against the wall. The lighting in the room is dim...atmosphere feels quiet and somewhat cluttered. (22s)


                                         Figure 1. Example of StreamChat on streaming video. In the example, the question is asked at the 11th second. As the model outputs its
                                         text steam, it continuously follows the dynamic content of the streaming video and uses up-to-date video content to answer the question.

                                                                        Abstract                                               streaming interaction scenarios compared to state-of-the-art
                                                                                                                               video LMMs. Our project page is at StreamChat.
                                             This paper presents StreamChat, a novel approach that
                                         enhances the interaction capabilities of Large Multimodal
                                         Models (LMMs) with streaming video content. In streaming
                                                                                                                               1. Introduction
                                         interaction scenarios, existing methods rely solely on visual
                                         information available at the moment a question is posed,                              The recent surge of large language models (LLMs) [4, 12,
                                         resulting in significant delays as the model remains unaware                          21, 39, 44, 55] and large multimodal models (LMMs) [10,
                                         of subsequent changes in the streaming video. StreamChat                              24, 53, 57] has unlocked numerous application scenarios, in-
                                         addresses this limitation by innovatively updating the visual                         cluding visual instruction following [31–34] and long video
                                         context at each decoding step, ensuring that the model uti-                           understanding [69, 80]. Notably, frontier models such as
                                         lizes up-to-date video content throughout the decoding pro-                           GPT-4o [41] and Gemini [51] have shown remarkable pro-
                                         cess. Additionally, we introduce a flexible and efficient cross-                      ficiency when interacting with streaming videos, attracting
                                         attention-based architecture to process dynamic streaming                             considerable interest in the field. While recent open ap-
                                         inputs while maintaining inference efficiency for streaming                           proaches [7, 63, 67, 77] have emerged to enhance streaming
                                         interactions. Furthermore, we construct a new dense instruc-                          video processing, they still fall short in interaction fluency
                                         tion dataset to facilitate the training of streaming interaction                      and perceptual capabilities.
                                         models, complemented by a parallel 3D-RoPE mechanism                                      To enable effective interaction with streaming videos,
                                         that encodes the relative temporal information of visual and                          LMMs must not only accurately identify the visual content
                                         text tokens. Experimental results demonstrate that Stream-                            of each frame but also track dynamic changes in the stream-
                                         Chat achieves competitive performance on established image                            ing video, leveraging the latest visual information to answer
                                         and video benchmarks and exhibits superior capabilities in                            questions, as illustrated in Figure 1. Despite notable progress
                                            ∗ Work done during an internship at NVIDIA                                         in video understanding of LMMs [11, 52, 68, 76, 81], ex-
                                               Corresponding authors                                                           isting models often overlook the crucial need to capture


                                                                                                                           1
                                                                             question, which is different from the streaming interaction
   Text stream                               0   1     2      …
   (existing models)                                                         scenarios where the video content is dynamically changing
                                                                             during the answering process. To bridge this gap, we create
                                                                             a new dense instruction dataset based on existing dense cap-
 Video stream          0   …     t-1         t   t+1   t+2     …             tion datasets. One dense instruction data consists of several
                                  Question                                   (time interval, instruction, answer) triplets, with each word
                                                                             of the instruction-answer pairs annotated with a timestamp
   Text stream
                                                                             in a heuristic manner. During training, we employ atten-
                                             0   1     2       …
      (StreamChat)                                                           tion masks to ensure that each text token can only attend to
                                                                             video information before its corresponding timestamp. This
Figure 2. Comparison of context in the decoding process with                 method effectively simulates the conditions of streaming
existing models. For each text token, the black and blue arrows              interaction throughout the training process.
indicate the beginning and end of the utilized visual context, respec-           Importantly, we do not directly input the absolute times-
tively. While existing models (top) use a fixed visual context when          tamp of each token into the model, as these timestamps are
decoding, StreamChat (bottom) aligns the video and text streams
                                                                             unavailable during inference. Instead, we propose a parallel
temporally and dynamically updates its visual context based on the
                                                                             3D-RoPE mechanism that allows each token to be aware of
streaming video.
                                                                             its relative temporal position within the video. We use three
                                                                             components in RoPE [49] to represent temporal, height, and
dynamic changes, negatively impacting the interaction expe-                  width, respectively. Unlike existing approaches that arrange
rience. Specifically, current methods typically rely on video                video and text in an interleaved manner [49, 57], our method
information only up to the moment a question is asked; how-                  organizes them in a parallel way to ensure that visual and
ever, the streaming content may change significantly during                  text tokens at the same timestamp share the same tempo-
the decoding process, leaving the model unaware of these                     ral context in RoPE, which enhances the continuity during
updates. For instance, assume a question is posed at time t                  streaming interactions.
and the model takes t′ seconds to answer the question, exist-                    Through extensive experiments, we demonstrate that
ing methods only utilize the video content from the interval                 StreamChat not only achieves competitive performance on
0 to t to answer the question, leaving the model unaware of                  established image and video benchmarks but also signifi-
any changes that occur between t and t + t′ . This delay can                 cantly improves capabilities in streaming interaction scenar-
be particularly detrimental in highly dynamic video environ-                 ios. Specifically, we create a benchmark designed to eval-
ments or when the answer to a question is lengthy, resulting                 uate LMMs in streaming interaction scenarios. We demon-
in a suboptimal user experience. We illustrate the problem                   strate that our StreamChat-7B outperforms the state-of-the-
in Figure 2 (top).                                                           art LLaVA-Video-72B model.
    To address these limitations, we propose StreamChat, a
novel approach that enables LLMs to interact dynamically
with streaming video content. The core idea is to provide                    2. Methods
the LLM with the latest video information at each decoding
step, allowing it to better capture video dynamics and adjust                Recent advancements in large multimodal models
its responses accordingly, which is illustrated in Figure 2                  (LMMs) [11, 52, 68, 76, 81] have significantly improved
(bottom). Mechanistically, StreamChat enhances the model’s                   the models’ video understanding capabilities. However, in
ability to interact with streaming video data, ensuring more                 streaming interaction scenarios, LMMs must also accurately
temporally aligned responses, as demonstrated in Figure 1.                   capture the dynamic changes of the streaming video content,
To effectively handle the dynamic visual inputs of streaming                 which is overlooked by existing models. To bridge this gap,
videos, we design a flexible and efficient architecture based                we propose StreamChat, a novel LMM that can interact
on cross-attention mechanism [3, 12, 56], bridging the LLM                   smoothly with streaming videos and track the latest changes
and visual inputs in StreamChat. The cross-attention design                  in the videos to refine its answers. In this section, we
facilitates processing variable-length inputs in the streaming               outline the methodology underlying StreamChat, detailing
scenario and is more efficient when dealing with a large                     the architectural innovations and techniques employed
number of visual tokens.                                                     to enable dynamic interaction with streaming video. We
    To facilitate the training of streaming interaction models,              begin by describing the StreamChat architecture design
we introduce a dense instruction dataset to train StreamChat.                in Section 2.1 and then introduce how we generate and
Existing video instruction-tuning datasets [17, 22, 26, 50,                  construct our training data in Section 2.2. Finally, we
81] primarily focus on offline video understanding, i.e., the                discuss the development of our training and inference
model can perceive the complete video before answering a                     pipeline in Section 2.3.


                                                                         2
                                                                         The                             video                               describe
              Visual tokens                 Text tokens                  (0, 0, 0)                       (1, 1, 1)                            (t, t, t)       Time

                                                                         (0,0,0)     (0,0,1)   (0,0,2)   (1,1,1)     (1,1,2)   (1,1,3)        (t, t, t)   …     …


                                                                         (0,1,0)     (0,1,1)   (0,1,2)   (1,2,1)     (1,2,2)   (1,2,3)   …       …        …     …
                                                     Q
                                                                         (0,2,0)     (0,2,1)             (1,3,1)     (1,3,2)                     …        …   (t,t+h,
                                                                                               (0,2,2)                         (1,3,3)
                                                                                                                                                               t+w)
                               K&V
                                          Cross-attention
                                                                       Figure 4. The parallel 3D-RoPE. For visual and text tokens at the
                                              Linear gate
                                                                       same timestamp, they share the same temporal position.

                                          Self-attention
                                                                       to improve the convergence speed during training.
                                                                           We further utilize V-FFN experts to enhance the vi-
                 V-FFN                         FFN                     sual representations throughout the LLM’s forward process.
                                                                       Specifically, after each cross-attention block, we update the
                 Linear gate                                           visual tokens with a V-FFN expert and feed the updated to-
                                                                       kens into the subsequent cross-attention block. In contrast
                                     xN                                to previous cross-attention-based models [3, 8, 12, 72] that
                                                                       utilize the same visual representations for all cross-attention
Figure 3. The StreamChat architecture. We utilize cross-               blocks, our V-FFN experts allow the visual representations
attention blocks to bridge the visual and text tokens and V-FFN        to better align with the LLM’s hidden status and improve
blocks to update the visual tokens throughout the LLM’s forward        the final performance. Practically, these V-FFN experts are
process. Those two blocks’ outputs are scaled with a linear gate       initialized from the LLM’s FFN instead of training from
mechanism.                                                             scratch to inherit the pretrained knowledge of the LLM.
                                                                           Previous cross-attention-based models [3, 12] typically
                                                                       employ a tanh-gating mechanism to ensure that the language
2.1. StreamChat Architecture
                                                                       model produces the same results as the original LLM at the
To support streaming video content, we design a flexible               early stage and stabilize the training. However, the tanh
and efficient architecture capable of handling dynamic video           function suffers from the gradient vanishing problem, which
inputs through the cross-attention mechanism. Additionally,            results in suboptimal performance. Instead, we introduce a
we introduce visual feedforward network (V-FFN) experts                linear gate to scale the output of cross-attention and V-FFN
to enhance the visual representations throughout the large             blocks to a relatively small range during the initial training
language model’s (LLM) forward process. We also propose                phase following CaiT [54]. The linear gate mechanism miti-
a parallel 3D-RoPE mechanism to better encode the tem-                 gates the gradient problem while also stabilizing the training
poral information in streaming interaction scenarios. The              process.
architecture is illustrated in Figure 3.
                                                                       Parallel 3D-RoPE. To better model the positional infor-
Cross attention. We build a cross-attention-based archi-               mation of streaming video and text, we propose parallel
tecture to bridge the visual and text tokens. Given an input           3D-RoPE that extends traditional 1D-RoPE [49] to 3D space
streaming video, we utilize a pretrained vision model to ex-           with a parallel arrangement of visual and text tokens. Specifi-
tract visual tokens for each sampled frame separately. To              cally, we split the embedding of RoPE into three components.
integrate these visual tokens with the LLM, we insert several          For text tokens, these components are identical to represent
cross-attention blocks into the LLM architecture, where text           the temporal location of each token. For visual tokens, these
tokens serve as queries and visual tokens act as keys and val-         three components represent the temporal, height, and width
ues. The visual tokens are dynamically updated during the              locations of each token. Unlike previous approaches that
interaction process, and the cross-attention design facilitates        arrange the visual and text tokens in an interleaved man-
processing these dynamic inputs. Moreover, compared to                 ner [57], we use a parallel way to arrange them, as illustrated
self-attention-based architectures (e.g., LLaVA [33]), cross-          in Figure 4. Given a text token and a visual token at the
attention is significantly more efficient when the visual to-          same timestamp, we apply the same temporal index for them.
kens are much more than the text tokens, especially in stream-         Our intuition is that in the streaming setting, one specific
ing interactions, where we have high frames per second                 timestamp’s text and visual tokens are happening simultane-
(FPS) for inference. In practice, our cross-attention blocks           ously, and therefore should share the same temporal location
share parameters with the self-attention blocks of the LLM             instead of an interleaved location. The parallel arrangement


                                                                   3
is crucial for the high FPS inference in the streaming setting,       Attention mask. To ensure that the token at time <t> does
where the traditional arrangement may have a significant              not attend to video frames occurring after <t>, we utilize
temporal positional gap between two adjacent text tokens              attention mask to block such attention. This mechanism is
while our approach ensures their continuity.                          crucial for maintaining the temporal integrity of the stream-
                                                                      ing interaction, allowing the model to focus only on relevant
2.2. Dense Instruction Data                                           visual information available at each decoding step.
Existing video instruction-tuning datasets [17, 22, 26, 50,
81] have made significant progress in offline video under-            Inference. During inference, StreamChat employs a paral-
standing, i.e., the model can see the whole video before an-          lel approach to ensure efficient processing of the streaming
swering a question. However, these datasets are not suitable          video content. Specifically, we utilize a separate thread to
for training streaming interaction models, where the input is         continuously read the video stream and store the extracted
a streaming video and each text token can only see part of the        visual tokens in a First-In-First-Out (FIFO) queue. When the
video. For instance, a text token at timestamp t can only per-        LLM requires decoding to generate a response, it acquires
ceive video frames at and before timestamp t. To tackle this          the latest video tokens from the FIFO queue. The model
problem, we create a new video instruction-tuning dataset             then incorporates this current information to decode the next
from the existing dense caption datasets, whose captions are          token, ensuring that its responses are informed by the most
paired with timestamp intervals.                                      up-to-date video stream context. This design not only en-
    Given a video with its dense caption, we prompt an LLM            hances the relevance of the model’s outputs but also supports
(e.g., Gemini-1.5-Pro [51]) to pick a start time of one video         seamless streaming interactions, allowing users to engage
segment and then generate an instruction-answer pair based            with dynamic video content effectively.
on the caption of this segment. We instruct the LLM to fo-
cus on streaming interaction scenarios and generate relevant
                                                                      3. Experiment Setups
instructions. To enhance the diversity of the instruction data,
we initially generate 5k pairs and conduct a clustering to            In this section, we outline the experimental setups employed
eliminate highly similar instructions. We manually review             in our study. We build our model using the SigLIP vision
the remaining examples and use them as in-context exam-               encoder [75] with PaliGemma weights [6] and 7B/14B Qwen
ples for subsequent data generation. Ultimately, we collect           2.5 LLM [52]. We utilize a Multi-Layer Perceptron (MLP)
a total of 51k examples from two dense caption datasets,              adapter [33] to align the hidden dimensions of the vision and
Ego4D [17] and Vript [70], with one representing the ego-             language components.
centric environment and the other one representing the natu-
ral environment.                                                      3.1. Pretraining
2.3. Training and Inference                                           We implement a two-stage pretraining process and grad-
                                                                      ually unfreeze the pretrained parameters for more effec-
Data arrangement. Given the initial instruction data with             tive pretraining. In both stages, we utilize a combina-
coarse temporal annotations, i.e., in the form of (time inter-        tion of ReCap data from LLaVA-Next [32], part of In-
val, instruction, answer), we employ a heuristic approach             ternVL pretraining data [10], MMC4 [84], and dense caption
to assign timestamps to each word in the instruction data.            datasets [17, 22, 50, 70, 83]. In stage 1, we only train the
For instance, consider a triplet where the time interval is           MLP adapter for alignment. We train the MLP for 5000 steps
5-10 seconds, the instruction is “What is the person in the           with a maximum learning rate of 5 × 10−4 and batch size of
video doing now?” and the answer is “The person is cooking            512. In stage 2, we further unfreeze the vision encoder and
right now.” To generate fine-grained temporal annotations,            the visual feedforward network (V-FFN) experts to achieve
we transform this coarse-grained triplet into a sequence of           deeper alignment. We train for 5000 steps with a maximum
words including time indicators. The transformation results           learning rate of 2 × 10−5 and batch size of 512. For the
in the following format:                                              dense caption datasets, we employ 1 frame per second (FPS)
                                                                      and a maximum of 40 frames for training. For other video
 Instruction:<5>What is the person in the video doing now?
                                                                      data, we uniformly sample 40 frames for training. In total,
 Answer:<5>The <6>person <7>is <8>cooking <9>right <10>now.
                                                                      we utilize 5.1 million samples for pretraining.
   Here, <t> represents the t-th second. The intuition be-
hind this design is that the instruction is input by the user
                                                                      3.2. Instruction Tuning
instantaneously, while the answer is decoded token by token           We construct a comprehensive instruction-tuning dataset
by the model. For this example, we assume the model de-               mainly based on Eagle-1.8M [45]. In addition, we incorpo-
codes one token per second. Note that the <t> indicators are          rate our dense instruction dataset and LLaVA-Video [81] for
not directly input to the model but serve solely for reference.       instruction tuning. We unfreeze all the parameters and train


                                                                  4
                                                                     StreamChat Wins                         Tie                 StreamChat Loses
                                           StreamChat-7B                                                                                 StreamChat-14B
     VILA-1.5-8B                    55%                         30%             15%                 VILA-1.5-8B                   52%                       26%             22%

    VILA-1.5-13B                     58%                         27%            15%                VILA-1.5-13B                      62%                        19%          19%

    VILA-1.5-40B                   53%                       24%             23%                   VILA-1.5-40B                    56%                         26%           18%

  LLaVA-Video-7B                44%                   22%                34%                     LLaVA-Video-7B                 45%                   21%               34%

 LLaVA-Video-72B              37%                    32%                  31%                   LLaVA-Video-72B               41%                   24%                 35%

                   0%              25%              50%             75%             100%                           0%             25%              50%             75%               100%

Figure 5. Comparison of StreamChat with leading video LMMs on streaming evaluation. We use StreamChat-7B/-14B as one of the
candidate models and report the win/tie/loss rate against VILA or LLaVA-Video models. Our StreamChat models demonstrate stronger
streaming interaction capabilities, and can even outperform LLaVA-Video-72B which uses a much larger base LLM.


  (1s) Question: Describes the scene transition of the video.                                                                                                             Video Stream




  Ours: (1s) … transitions from a dark … to a bright … with a yellow background and a rotating gear … ends with a bright yellow background and the text "ГОРОД ИНСТРУМЕНТА”…

  VILA: (1s) … starts with a black screen, then transitions to a blurry image of a person's face. The person appears to be wearing a hat and has a beard. The image is not clear …

  LLaVA-V: (1s) …transitions from a completely black screen to a small, bright light in the center. The light gradually grows larger and brighter … becomes a large, glowing orb.


  (21s) Question: Describe the environments and creatures featured in the current and subsequent video segment.                                                           Video Stream




  Ours: (21s) The current…serene ocean with a whale breaking the surface … a flock of birds flying … mountains in the background. The subsequent…vibrant underwater scene…

  VILA: (21s) …a large whale swimming in the ocean. The whale is seen from different angles, … massive size and the intricate patterns on its body … ocean water is a deep blue…

  LLaVA-V: (21s) … features a serene ocean environment with a large whale swimming gracefully. The whale's tail is prominently visible, creating a dynamic and captivating scene.



Figure 6. Qualitative evaluation of StreamChat on streaming video. In the example shown, the questions are asked at the first second
(top) and the 21st second (bottom), respectively. Our model can capture the dynamic video content and adapt its answer accordingly. In
comparison, VILA and LLaVA-Video fail to follow the streaming video and exhibit factual errors (highlighted in red).


on the dataset combination for 1 epoch. We use a maximum                                          4. Streaming Evaluation
learning rate of 2 × 10−5 and a batch size of 768. For the
dense instruction data, we use 1 FPS and a maximum of                                             To evaluate large multimodal models’ (LMMs) streaming
32 frames for training. For other video instruction data, we                                      interaction capabilities, we construct a streaming evaluation
uniformly sample 32 frames for training. In total, we use 2.9                                     benchmark from existing dense caption datasets. Based on
million samples for instruction tuning.                                                           the dense caption of a video, we prompt Gemini-1.5-Pro
                                                                                                  to generate an instruction-answer pair for a specific times-
                                                                                                  tamp. We remove samples that are not related to streaming


                                                                                            5
                                          # Vis Tok.                                                                       TextVQA    RealworldQA
                                                        MMEP    MMB   MMMUV      MMStarV    SEEDI    GQA   SQAI    AI2D
                            Method
              Private models
                           GPT-4V       UNK. 1409 75.8 56.8 57.1 69.1 36.8 75.7 78.2 78.0 61.4
                     Gemini-1.0 Pro     UNK. 1496 73.6 47.9 42.6 70.7  -   79.5  -    -    -
                     Gemini-1.5 Pro     UNK.   -   -   58.5  -    -    -    -   80.3 73.5 67.5
                           Grok-1.5     UNK.   -   -   53.6  -    -    -    -   88.3 78.1 68.7
              7B-Level Base LLM
               Mini-Gemini-HD-8B        2880           1606    72.7   37.3  -              73.2     64.5   75.1   73.5    70.2       62.1
                  LLaVA-NeXT-8B         2880           1603    72.1   41.7  -              72.7     65.2   72.8   71.6    64.6       60.1
                     Cambrian-1-8B       576           1547    75.9   42.7  -              74.7     64.6   80.4   73.0    71.7       64.2
                     StreamChat-7B      256            1520    74.4   48.1 46.0            74.3     62.4   85.5   76.6    72.4       61.7
              14B-Level Base LLM
              Mini-Gemini-HD-13B        2880           1597    68.6   37.3  -              70.6     63.7   71.9   70.1    70.2       57.5
                 LLaVA-NeXT-13B         2880           1575    70.0   36.2  -              65.6     65.4   73.5   70.0    67.1       59.1
                   Cambrian-1-13B        576           1610    75.7   40.0  -              74.4     64.3   79.3   73.6    72.8       63.0
                   StreamChat-14B       256            1617    79.0   50.1 53.6            75.5     63.3   85.8   79.5    74.4       63.3

Table 1. Comparison of StreamChat with leading LMMs on image benchmarks. StreamChat achieves competitive performance on these
benchmarks while using only 256 visual tokens.


scenarios and manually review and refine each remaining                       answers in 77% of the evaluation cases despite using a much
sample to ensure that the instruction and answer align with                   smaller LLM. While LLaVA-Video models excel in offline
the video content and timestamp. Ultimately, we collect 100                   video understanding, StreamChat-7B outperforms them in
evaluation samples, with 80 sourced from Vript [70] and 20                    streaming interaction scenarios, highlighting the importance
from Ego4D [17].                                                              of capturing video dynamics during streaming inference. Fur-
   Following [33, 34], we use Gemini-1.5-Pro as the judge                     thermore, we observe that our StreamChat-14B demonstrates
for performance evaluation. Given a video and its corre-                      overall better performance than StreamChat-7B, indicating
sponding instruction, we infer two candidate models to pre-                   that scaling the base LLM can also improve the streaming
dict their respective answers. We then feed the ground truth                  interaction performance.
answer along with the outputs from the two models to the
judge. The judge is required to evaluate the two answers on                   4.2. Qualitative Results
adherence, helpfulness, relevance, and accuracy. We prompt                    We provide a qualitative evaluation of StreamChat’s capa-
the judge to determine which model’s answer is better or if                   bilities on streaming video, as illustrated in Figure 6. In the
both are tied in terms of quality and then require it to pro-                 example, we pose a question at a specific timestamp. While
vide a detailed justification explaining its reasoning based                  previous methods only answer the question using the visual
on the judgment. We use our StreamChat model as one of                        context up to the moment the question is asked, Stream-
the candidate models and calculate the overall win rate in                    Chat can dynamically update its visual context alongside the
comparison to the other models.                                               streaming video and adapt its answer accordingly. We show
                                                                              that StreamChat can better capture dynamic video content
4.1. Quantitative Results
                                                                              and provide more accurate answers. In contrast, VILA [29]
We show the comparison between StreamChat and other                           and LLaVA-Video [81] struggle to maintain temporal align-
video LLMs in Figure 5. The frames per second (FPS) is                        ment with the streaming video and exhibit factual errors
set to 5. We use 32 frames for StreamChat and LLaVA-                          (highlighted in red).
Video [81] models, and 16 frames for VILA [29] since us-
ing 32 would exceed its context range. Our results demon-                     5. Benchmark Results
strate that our StreamChat models exhibit superior stream-
ing interaction capabilities compared to LLaVA-Video and                      We evaluate the performance of StreamChat models on pop-
VILA models. Notably, compared to VILA-1.5-40B, our                           ular image [9, 13, 19, 20, 23, 35, 37, 46, 64, 74] and video
StreamChat-7B model produces equally or more preferable                       benchmarks [14, 26, 38, 42, 62, 65, 73, 82] using the LMMs-


                                                                      6
                                                                                                                 PerceptionTest   LongVideoBench
                                              # Frames   ActNet-QA   EgoSchema       MLVU    MVBench   NExT-QA                                        VideoMME
                               Method
                    Private models
                               GPT-4V UNK.               57.0  -   49.2 43.5                             -           -            61.3             59.9/63.3
                               GPT-4o UNK.                -    -   64.6  -                               -           -            66.7             71.9/77.2
                      Gemini-1.5-Flash UNK.              55.3 65.7  -    -                               -           -            61.6             70.3/75.0
                        Gemini-1.5-Pro UNK.              57.5 72.2  -    -                               -           -            64.0             75.0/81.3
                    7B-Level Base LLM
                            LongVA-7B 128                50.0  -   56.3                      -   68.3  -    -   52.6/54.3
                            IXC-2.5-7B  64               52.8  -   37.3                     69.1 71.0 34.4  -   55.8/58.8
                            PLLaVA-7B   16               56.3  -    -                       46.6  -    -   40.2     -
                     VideoLLaMA2-7B     16               50.2 51.7 48.5                     54.6  -    -    -   47.9/50.3
                        StreamChat-7B   40               54.9 48.4 63.9                     53.3 78.5 63.0 54.2 58.6/62.8
                    14B+ Level Base LLM
                             VILA-40B UNK.               58.0 58.0  -    -   67.9 54.0  -   60.1/61.1
                          PLLaVA-13B    16               56.3  -    -   50.1  -    -   45.6     -
                          PLLaVA-34B    16               60.9  -    -   58.1  -    -   53.2     -
                    VideoLLaMA2-72B     16               55.2 63.9 61.2 62.0  -    -    -   61.4/63.1
                       StreamChat-14B   40               55.9 57.2 66.6 55.2 79.4 63.7 57.1 63.1/66.3

Table 2. Comparison of StreamChat with leading LMMs on video benchmarks. StreamChat achieves competitive performance on these
benchmarks and even outperforms models with a much larger base LLM. StreamChat’s cross-attention-based architecture is efficient in
processing a large number of video frames.


Eval library [78]. Note that to maintain StreamChat’s effi-                          Importantly, our model remains efficient even when process-
ciency for streaming interactions, we do not employ multiple                         ing more frames for inference, as our cross-attention-based
vision encoders [45, 53] or image tiling techniques [10, 32],                        architecture mitigates the heavy computation associated with
which could compromise performance on benchmarks re-                                 self-attention across frames.
quiring high-resolution inputs.
    The performance of StreamChat on image benchmarks                                6. Ablation Studies
is presented in Table 1. StreamChat demonstrates strong
results compared to Cambrian-1, which utilizes multiple vi-                          We use a relatively efficient setting for ablation studies. We
sion encoders, and LLaVA-NeXT, which employs image                                   shrink the total training steps to 2000 while keeping other
tiling. Notably, our StreamChat-7B achieves a score of 48.1                          hyperparameters the same as our full training. In the instruc-
on the MMMU benchmark, surpassing LLaVA-NeXT-8B                                      tion tuning stage, unless otherwise specified, we employ
and Cambrian-1-8B by 6.4 and 5.4 points, respectively. Ad-                           a combination of our dense instruction dataset and Eagle-
ditionally, StreamChat outperforms both LLaVA-NeXT and                               1.8M [45] and train on the combination for 1 epoch. The
Cambrian-1 on TextVQA, despite using significantly fewer                             training hyperparameters are the same as our full training.
visual tokens. Overall, StreamChat achieves competitive per-                             We present the results of our ablation study in Table 3,
formance on image benchmarks while ensuring computation                              where we ablate our architectural designs and the proposed
efficiency.                                                                          dense instruction dataset. We compare performance across
    We present StreamChat’s performance on video bench-                              four image benchmarks, four video benchmarks, and our
marks in Table 2. Our model significantly outperforms                                streaming evaluation. In the streaming evaluation, we em-
PLLaVA [68] and VideoLLaMA2 [11], using a 7B-level base                              ploy our StreamChat solution (last row) as one of the can-
LLM. Specifically, we achieve scores of 58.6/62.8 on the                             didate models and report the performance of other models
VideoMME benchmark [14], outperforming VideoLLaMA2-                                  relative to StreamChat.
7B by 10.7/11.5 points. Moreover, StreamChat-14B demon-                                  Our experiment results indicate that the architectural en-
strates superior performance compared to VILA-40B and                                hancements we introduced lead to improved overall perfor-
VideoLLaMA2-72B, which utilize much larger base LLMs.                                mance. Specifically, the StreamChat model outperforms the


                                                                                 7
                                                                          TextVQA   RealworldQA           MVBench   PerceptionTest    VideoMME
                    Linear Param. Dense                MMMUV   AI2D                               MLVU                                           StreamEval
          V-FFN
                     Gate Reuse Instruction                                                                                                      Win/Tie/Loss
             ✗        ✓      ✓       ✓      46.7 75.7 62.7 57.8 58.2                                     47.3       49.3             51.1         18/46/36
             ✓        ✗      ✓       ✓      45.1 74.8 60.7 58.3 60.0                                     49.4       51.8             52.4         25/45/30
             ✓        ✓      ✗       ✓      44.4 72.4 46.9 46.3 53.5                                     43.4       46.6             47.1         20/33/47
             ✓        ✓      ✓       ✗      46.0 76.5 62.5 59.4 57.0                                     49.0       52.8             51.3         25/34/41
             ✓        ✓      ✓       ✓      45.2 76.1 63.3 58.0 59.7                                     49.5       51.1             52.6            -/-/-
Table 3. Ablation study results. StreamEval indicates our proposed streaming evaluation, in which we use our final solution (last row) as
one of the candidate models and report other models’ performance against our final solution.


version without the visual feedforward network (V-FFN) ex-                      ternVL2 [10], LLaVA-OneVision [24], and Qwen2-VL [57]
perts on 8 out of 9 benchmarks. Additionally, we observe                        have demonstrated even better performance than state-of-the-
that using a tanh gate facilitates faster convergence during                    art closed models like GPT-4o [41] or Gemini-1.5-Pro [51],
the early stages of training; however, it ultimately results in                 paving the path for research of LMMs.
poorer final performance compared to the linear gate. The
linear gate improves performance on 6 out of 9 benchmarks
when compared to the tanh gate. Furthermore, we observe a                       Multimodal Video Models. More recent LMMs also in-
significant training instability when not reusing the LLM’s                     corporate video understanding capability to support a wider
parameter, which also leads to poor final performance. Our                      range of application scenarios [25, 29, 57, 68, 71, 76]. To
final solution substantially outperforms the model without                      support extreme long video understanding, various tech-
parameter reuse across all evaluated benchmarks.                                niques are proposed to process more video frames during
   When compared to the model trained without dense in-                         training and inference [47, 48, 69, 80]. Additionally, to
struction data, our final solution performs comparably on                       reduce the redundancy of video information, more recent
existing image and video benchmarks. However, in the                            approaches also propose to compress the video via spatial
streaming evaluation, we demonstrate that training on our                       or temporal compression [27, 36, 60, 61]. However, these
dense instruction dataset significantly enhances interaction                    methods focus on offline video understanding, where the
capabilities. Our final solution produces equally or more                       entire video is available beforehand. In contrast, Stream-
preferable answers in 75% of the evaluation cases, indi-                        Chat focuses on processing streaming video, which is more
cating that reliance on existing image or video instruction                     suitable for real-world applications and interaction.
tuning datasets alone is insufficient for effective streaming
interactions.
                                                                               Streaming Video Models. The advent of streaming video
7. Related Works                                                               models began with OpenAI’s GPT-4o [41], which has
                                                                               demonstrated remarkable proficiency in real-time interac-
Large Multimodal Models. Large multimodal models                               tion with streaming videos, attracting considerable interest
(LMMs) have garnered significant attention for their ro-                       in the field. Following this landmark development, sev-
bust zero-shot capabilities across various tasks, includ-                      eral subsequent works have aimed to enhance large mul-
ing image captioning [30] and visual question answering                        timodal models for processing streaming video content.
(VQA) [16, 18, 40]. Notably, Flamingo [2] showcases vi-                        Notable approaches include methods such as VideoLLM-
sual in-context learning by training on extensive interleaved                  online [7], Flash-VStream [77], and subsequent meth-
image-text datasets. GPT-4V [1] exhibits emerging image-                       ods [15, 28, 43, 59, 63, 66, 67, 79] , which focus on improv-
understanding capabilities, providing coherent responses to                    ing the fluency or responsiveness of models during streaming
user queries. In the open-source domain, LLaVA repro-                          video processing. However, unlike these existing models,
duces aspects of GPT-4V’s functionality by fine-tuning on                      which often rely on fixed video content up to the moment a
generated instruction-following data. Subsequent works, in-                    question is posed to answer questions, our work emphasizes
cluding LLaVA-1.5 [31], Qwen-VL [5], and CogVLM [58],                          the dynamic updating of the visual context during the decod-
aim to enhance model capabilities through architectural re-                    ing process, thereby significantly enhancing the interactive
finements, improved training methodologies, and higher-                        experience and mitigating the detrimental delays inherent in
quality training datasets. More recently, open models like In-                 highly dynamic environments.


                                                                      8
8. Conclusion                                                             [6] Lucas Beyer, Andreas Steiner, André Susano Pinto, Alexan-
                                                                              der Kolesnikov, Xiao Wang, Daniel Salz, Maxim Neumann,
This paper presents StreamChat, a novel approach that en-                     Ibrahim Alabdulmohsin, Michael Tschannen, Emanuele
hances the real-time interaction capabilities of large mul-                   Bugliarello, et al. Paligemma: A versatile 3b vlm for transfer.
timodal models (LMMs) with streaming video content.                           arXiv preprint arXiv:2407.07726, 2024. 4
StreamChat is built on a flexible and efficient cross-attention-          [7] Joya Chen, Zhaoyang Lv, Shiwei Wu, Kevin Qinghong Lin,
based architecture with visual feedforward network (V-FFN)                    Chenan Song, Difei Gao, Jia-Wei Liu, Ziteng Gao, Dongxing
experts. By continuously updating the visual context at each                  Mao, and Mike Zheng Shou. Videollm-online: Online video
decoding step, StreamChat effectively captures the dynamic                    large language model for streaming video. In Proceedings of
changes of streaming video content, leading to temporally                     the IEEE/CVF Conference on Computer Vision and Pattern
aligned responses. We also introduce a dense instruction                      Recognition, pages 18407–18418, 2024. 1, 8
dataset to facilitate the training of streaming interaction mod-          [8] Kaibing Chen, Dong Shen, Hanwen Zhong, Huasong Zhong,
                                                                              Kui Xia, Di Xu, Wei Yuan, Yifei Hu, Bin Wen, Tianke Zhang,
els, alongside a parallel 3D-RoPE mechanism to better ar-
                                                                              et al. Evlm: An efficient vision-language model for visual
range the streaming video and text. Our extensive evalua-
                                                                              understanding. arXiv preprint arXiv:2407.14177, 2024. 3
tions on both established image and video benchmarks and a
                                                                          [9] Lin Chen, Jinsong Li, Xiaoyi Dong, Pan Zhang, Yuhang Zang,
novel streaming benchmark demonstrate that StreamChat not                     Zehui Chen, Haodong Duan, Jiaqi Wang, Yu Qiao, Dahua
only achieves competitive performance on existing bench-                      Lin, et al. Are we on the right way for evaluating large vision-
marks but also excels in streaming interaction scenarios.                     language models? arXiv preprint arXiv:2403.20330, 2024.
                                                                              6
9. Limitations                                                           [10] Zhe Chen, Jiannan Wu, Wenhai Wang, Weijie Su, Guo Chen,
                                                                              Sen Xing, Muyan Zhong, Qinglong Zhang, Xizhou Zhu,
While StreamChat demonstrates significant advancements in                     Lewei Lu, et al. Internvl: Scaling up vision foundation models
streaming interaction capabilities for large multimodal mod-                  and aligning for generic visual-linguistic tasks. In Proceed-
els (LMMs), several limitations remain. One limitation is                     ings of the IEEE/CVF Conference on Computer Vision and
that the timestamps for each text token are generated heuris-                 Pattern Recognition, pages 24185–24198, 2024. 1, 4, 7, 8
tically from coarse-grained temporal annotation rather than              [11] Zesen Cheng, Sicong Leng, Hang Zhang, Yifei Xin, Xin
being manually annotated. This reliance on heuristics may                     Li, Guanzheng Chen, Yongxin Zhu, Wenqi Zhang, Ziyang
introduce inaccuracies in temporal alignment, particularly in                 Luo, Deli Zhao, et al. Videollama 2: Advancing spatial-
complex video scenarios where precise timing is crucial.                      temporal modeling and audio understanding in video-llms.
                                                                              arXiv preprint arXiv:2406.07476, 2024. 1, 2, 7
                                                                         [12] Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Ab-
References
                                                                              hishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil
 [1] Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad,                 Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The
     Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko                llama 3 herd of models. arXiv preprint arXiv:2407.21783,
     Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4                  2024. 1, 2, 3
     technical report. arXiv preprint arXiv:2303.08774, 2023. 8          [13] Chaoyou Fu, Peixian Chen, Yunhang Shen, Yulei Qin, Meng-
 [2] Jean-Baptiste Alayrac, Jeff Donahue, Pauline Luc, Antoine                dan Zhang, Xu Lin, Zhenyu Qiu, Wei Lin, Jinrui Yang, Xiawu
     Miech, Iain Barr, Yana Hasson, Karel Lenc, Arthur Mensch,                Zheng, et al. Mme: A comprehensive evaluation bench-
     Katherine Millican, Malcolm Reynolds, et al. Flamingo: a                 mark for multimodal large language models. arXiv preprint
     visual language model for few-shot learning. Advances in                 arXiv:2306.13394, 2023. 6
     Neural Information Processing Systems, 35:23716–23736,              [14] Chaoyou Fu, Yuhan Dai, Yondong Luo, Lei Li, Shuhuai
     2022. 8                                                                  Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang
 [3] Jean-Baptiste Alayrac, Jeff Donahue, Pauline Luc, Antoine                Shen, Mengdan Zhang, et al. Video-mme: The first-ever
     Miech, Iain Barr, Yana Hasson, Karel Lenc, Arthur Mensch,                comprehensive evaluation benchmark of multi-modal llms in
     Katherine Millican, Malcolm Reynolds, et al. Flamingo:                   video analysis. arXiv preprint arXiv:2405.21075, 2024. 6, 7
     a visual language model for few-shot learning. Advances             [15] Chaoyou Fu, Haojia Lin, Zuwei Long, Yunhang Shen, Meng
     in neural information processing systems, 35:23716–23736,                Zhao, Yifan Zhang, Xiong Wang, Di Yin, Long Ma, Xiawu
     2022. 2, 3                                                               Zheng, et al. Vita: Towards open-source interactive omni
 [4] Jinze Bai, Shuai Bai, Yunfei Chu, Zeyu Cui, Kai Dang, Xi-                multimodal llm. arXiv preprint arXiv:2408.05211, 2024. 8
     aodong Deng, Yang Fan, Wenbin Ge, Yu Han, Fei Huang, et al.         [16] Yash Goyal, Tejas Khot, Douglas Summers-Stay, Dhruv Ba-
     Qwen technical report. arXiv preprint arXiv:2309.16609,                  tra, and Devi Parikh. Making the v in vqa matter: Elevating
     2023. 1                                                                  the role of image understanding in visual question answering.
 [5] Jinze Bai, Shuai Bai, Shusheng Yang, Shijie Wang, Sinan                  In Proceedings of the IEEE conference on computer vision
     Tan, Peng Wang, Junyang Lin, Chang Zhou, and Jingren                     and pattern recognition, pages 6904–6913, 2017. 8
     Zhou. Qwen-vl: A frontier large vision-language model with          [17] Kristen Grauman, Andrew Westbury, Eugene Byrne, Zachary
     versatile abilities. arXiv preprint arXiv:2308.12966, 2023. 8            Chavis, Antonino Furnari, Rohit Girdhar, Jackson Hamburger,


                                                                     9
     Hao Jiang, Miao Liu, Xingyu Liu, et al. Ego4d: Around the          [30] Tsung-Yi Lin, Michael Maire, Serge J. Belongie, James Hays,
     world in 3,000 hours of egocentric video. In Proceedings of             Pietro Perona, Deva Ramanan, Piotr Dollár, and C. Lawrence
     the IEEE/CVF Conference on Computer Vision and Pattern                  Zitnick. Microsoft coco: Common objects in context. In
     Recognition, pages 18995–19012, 2022. 2, 4, 6                           ECCV, 2014. 8
[18] Danna Gurari, Qing Li, Abigale J Stangl, Anhong Guo, Chi           [31] Haotian Liu, Chunyuan Li, Yuheng Li, and Yong Jae Lee.
     Lin, Kristen Grauman, Jiebo Luo, and Jeffrey P Bigham.                  Improved baselines with visual instruction tuning. arXiv
     Vizwiz grand challenge: Answering visual questions from                 preprint arXiv:2310.03744, 2023. 1, 8
     blind people. In Proceedings of the IEEE conference on             [32] Haotian Liu, Chunyuan Li, Yuheng Li, Bo Li, Yuanhan Zhang,
     computer vision and pattern recognition, pages 3608–3617,               Sheng Shen, and Yong Jae Lee. Llava-next: Improved reason-
     2018. 8                                                                 ing, ocr, and world knowledge, 2024. 4, 7
[19] Drew A Hudson and Christopher D Manning. Gqa: A new                [33] Haotian Liu, Chunyuan Li, Qingyang Wu, and Yong Jae Lee.
     dataset for real-world visual reasoning and compositional               Visual instruction tuning. Advances in neural information
     question answering. In CVPR, 2019. 6                                    processing systems, 36, 2024. 3, 4, 6
[20] Aniruddha Kembhavi, Mike Salvato, Eric Kolve, Minjoon
                                                                        [34] Jihao Liu, Xin Huang, Jinliang Zheng, Boxiao Liu, Jia Wang,
     Seo, Hannaneh Hajishirzi, and Ali Farhadi. A diagram is
                                                                             Osamu Yoshie, Yu Liu, and Hongsheng Li. Mm-instruct:
     worth a dozen images. In Computer Vision–ECCV 2016:
                                                                             Generated visual instructions for large multimodal model
     14th European Conference, Amsterdam, The Netherlands,
                                                                             alignment. arXiv preprint arXiv:2406.19736, 2024. 1, 6
     October 11–14, 2016, Proceedings, Part IV 14, pages 235–
     251. Springer, 2016. 6                                             [35] Yuan Liu, Haodong Duan, Yuanhan Zhang, Bo Li, Songyang
                                                                             Zhang, Wangbo Zhao, Yike Yuan, Jiaqi Wang, Conghui He,
[21] Jacob Devlin Ming-Wei Chang Kenton and Lee Kristina
                                                                             Ziwei Liu, et al. Mmbench: Is your multi-modal model an
     Toutanova. BERT: Pre-training of deep bidirectional trans-
                                                                             all-around player? arXiv preprint arXiv:2307.06281, 2023. 6
     formers for language understanding. In Proceedings of
     NAACL-HLT, page 2. Minneapolis, Minnesota, 2019. 1                 [36] Zhijian Liu, Ligeng Zhu, Baifeng Shi, Zhuoyang Zhang, Yum-
[22] Ranjay Krishna, Kenji Hata, Frederic Ren, Li Fei-Fei, and               ing Lou, Shang Yang, Haocheng Xi, Shiyi Cao, Yuxian Gu,
     Juan Carlos Niebles. Dense-captioning events in videos. In              Dacheng Li, et al. Nvila: Efficient frontier visual language
     Proceedings of the IEEE international conference on com-                models. arXiv preprint arXiv:2412.04468, 2024. 8
     puter vision, pages 706–715, 2017. 2, 4                            [37] Pan Lu, Swaroop Mishra, Tony Xia, Liang Qiu, Kai-Wei
[23] Bohao Li, Rui Wang, Guangzhi Wang, Yuying Ge, Yixiao Ge,                Chang, Song-Chun Zhu, Oyvind Tafjord, Peter Clark, and
     and Ying Shan. Seed-bench: Benchmarking multimodal llms                 Ashwin Kalyan. Learn to explain: Multimodal reasoning
     with generative comprehension, 2023. 6                                  via thought chains for science question answering. In The
                                                                             36th Conference on Neural Information Processing Systems
[24] Bo Li, Yuanhan Zhang, Dong Guo, Renrui Zhang, Feng Li,
                                                                             (NeurIPS), 2022. 6
     Hao Zhang, Kaichen Zhang, Yanwei Li, Ziwei Liu, and Chun-
     yuan Li. Llava-onevision: Easy visual task transfer. arXiv         [38] Karttikeya Mangalam, Raiymbek Akshulakov, and Jitendra
     preprint arXiv:2408.03326, 2024. 1, 8                                   Malik. Egoschema: A diagnostic benchmark for very long-
[25] KunChang Li, Yinan He, Yi Wang, Yizhuo Li, Wenhai                       form video language understanding. Advances in Neural
     Wang, Ping Luo, Yali Wang, Limin Wang, and Yu Qiao.                     Information Processing Systems, 36, 2024. 6
     Videochat: Chat-centric video understanding. arXiv preprint        [39] Ben Mann, N Ryder, M Subbiah, J Kaplan, P Dhariwal,
     arXiv:2305.06355, 2023. 8                                               A Neelakantan, P Shyam, G Sastry, A Askell, S Agarwal,
[26] Kunchang Li, Yali Wang, Yinan He, Yizhuo Li, Yi Wang,                   et al. Language models are few-shot learners. arXiv preprint
     Yi Liu, Zun Wang, Jilan Xu, Guo Chen, Ping Luo, et al.                  arXiv:2005.14165, 1, 2020. 1
     Mvbench: A comprehensive multi-modal video understand-             [40] Kenneth Marino, Mohammad Rastegari, Ali Farhadi, and
     ing benchmark. In Proceedings of the IEEE/CVF Conference                Roozbeh Mottaghi. Ok-vqa: A visual question answering
     on Computer Vision and Pattern Recognition, pages 22195–                benchmark requiring external knowledge. In Proceedings
     22206, 2024. 2, 4, 6                                                    of the IEEE/cvf conference on computer vision and pattern
[27] Yanwei Li, Chengyao Wang, and Jiaya Jia. Llama-vid: An im-              recognition, pages 3195–3204, 2019. 8
     age is worth 2 tokens in large language models. In European        [41] OpenAI. Hello gpt-4o. https://openai.com/index/
     Conference on Computer Vision, pages 323–340. Springer,                 hello-gpt-4o/, 2024. 1, 8
     2024. 8                                                            [42] Viorica Pătrăucean, Lucas Smaira, Ankush Gupta, Adrià Re-
[28] Junming Lin, Zheng Fang, Chi Chen, Zihao Wan, Fuwen                     casens Continente, Larisa Markeeva, Dylan Banarse, Skanda
     Luo, Peng Li, Yang Liu, and Maosong Sun. Streamingbench:                Koppula, Joseph Heyward, Mateusz Malinowski, Yi Yang,
     Assessing the gap for mllms to achieve streaming video un-              Carl Doersch, Tatiana Matejovicova, Yury Sulsky, Antoine
     derstanding. arXiv preprint arXiv:2411.03628, 2024. 8                   Miech, Alex Frechette, Hanna Klimczak, Raphael Koster, Jun-
[29] Ji Lin, Hongxu Yin, Wei Ping, Pavlo Molchanov, Mohammad                 lin Zhang, Stephanie Winkler, Yusuf Aytar, Simon Osindero,
     Shoeybi, and Song Han. Vila: On pre-training for visual                 Dima Damen, Andrew Zisserman, and João Carreira. Per-
     language models. In Proceedings of the IEEE/CVF Confer-                 ception test: A diagnostic benchmark for multimodal video
     ence on Computer Vision and Pattern Recognition, pages                  models. In Advances in Neural Information Processing Sys-
     26689–26699, 2024. 6, 8                                                 tems, 2023. 6


                                                                   10
[43] Rui Qian, Xiaoyi Dong, Pan Zhang, Yuhang Zang, Shuangrui             [56] A Vaswani. Attention is all you need. Advances in Neural
     Ding, Dahua Lin, and Jiaqi Wang. Streaming long video un-                 Information Processing Systems, 2017. 2
     derstanding with large language models. Advances in Neural           [57] Peng Wang, Shuai Bai, Sinan Tan, Shijie Wang, Zhihao Fan,
     Information Processing Systems, 37:119336–119360, 2024. 8                 Jinze Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin
[44] Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee,                  Ge, et al. Qwen2-vl: Enhancing vision-language model’s
     Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and                    perception of the world at any resolution. arXiv preprint
     Peter J Liu. Exploring the limits of transfer learning with a             arXiv:2409.12191, 2024. 1, 2, 3, 8
     unified text-to-text transformer. Journal of machine learning        [58] Weihan Wang, Qingsong Lv, Wenmeng Yu, Wenyi Hong, Ji
     research, 21(140):1–67, 2020. 1                                           Qi, Yan Wang, Junhui Ji, Zhuoyi Yang, Lei Zhao, Xixuan
[45] Min Shi, Fuxiao Liu, Shihao Wang, Shijia Liao, Subhashree                 Song, et al. Cogvlm: Visual expert for pretrained language
     Radhakrishnan, De-An Huang, Hongxu Yin, Karan Sapra,                      models. arXiv preprint arXiv:2311.03079, 2023. 8
     Yaser Yacoob, Humphrey Shi, et al. Eagle: Exploring the
                                                                          [59] Yueqian Wang, Xiaojun Meng, Yuxuan Wang, Jianxin Liang,
     design space for multimodal llms with mixture of encoders.
                                                                               Jiansheng Wei, Huishuai Zhang, and Dongyan Zhao. Vide-
     arXiv preprint arXiv:2408.15998, 2024. 4, 7
                                                                               ollm knows when to speak: Enhancing time-sensitive video
[46] Amanpreet Singh, Vivek Natarajan, Meet Shah, Yu Jiang, Xin-
                                                                               comprehension with video-text duet interaction format. arXiv
     lei Chen, Dhruv Batra, Devi Parikh, and Marcus Rohrbach.
                                                                               preprint arXiv:2411.17991, 2024. 8
     Towards vqa models that can read. In Proceedings of the
                                                                          [60] Yuxuan Wang, Cihang Xie, Yang Liu, and Zilong Zheng.
     IEEE/CVF conference on computer vision and pattern recog-
                                                                               Videollamb: Long-context video understanding with recurrent
     nition, pages 8317–8326, 2019. 6
                                                                               memory bridges. arXiv preprint arXiv:2409.01071, 2024. 8
[47] Enxin Song, Wenhao Chai, Guanhong Wang, Yucheng Zhang,
     Haoyang Zhou, Feiyang Wu, Haozhe Chi, Xun Guo, Tian                  [61] Yuetian Weng, Mingfei Han, Haoyu He, Xiaojun Chang, and
     Ye, Yanting Zhang, et al. Moviechat: From dense token to                  Bohan Zhuang. Longvlm: Efficient long video understand-
     sparse memory for long video understanding. In Proceedings                ing via large language models. In European Conference on
     of the IEEE/CVF Conference on Computer Vision and Pattern                 Computer Vision, pages 453–470. Springer, 2024. 8
     Recognition, pages 18221–18232, 2024. 8                              [62] Haoning Wu, Dongxu Li, Bei Chen, and Junnan Li.
[48] Enxin Song, Wenhao Chai, Tian Ye, Jenq-Neng Hwang, Xi                     Longvideobench: A benchmark for long-context interleaved
     Li, and Gaoang Wang. Moviechat+: Question-aware sparse                    video-language understanding, 2024. 6
     memory for long video question answering. arXiv preprint             [63] Shiwei Wu, Joya Chen, Kevin Qinghong Lin, Qimeng Wang,
     arXiv:2404.17176, 2024. 8                                                 Yan Gao, Qianli Xu, Tong Xu, Yao Hu, Enhong Chen, and
[49] Jianlin Su. Totary position embedding, 2024. 2, 3                         Mike Zheng Shou. Videollm-mod: Efficient video-language
[50] Yansong Tang, Dajun Ding, Yongming Rao, Yu Zheng,                         streaming with mixture-of-depths vision computation. arXiv
     Danyang Zhang, Lili Zhao, Jiwen Lu, and Jie Zhou. Coin:                   preprint arXiv:2408.16730, 2024. 1, 8
     A large-scale dataset for comprehensive instructional video          [64] x.ai. Grok-1.5 vision preview. 6
     analysis. In Proceedings of the IEEE/CVF Conference on               [65] Junbin Xiao, Xindi Shang, Angela Yao, and Tat-Seng Chua.
     Computer Vision and Pattern Recognition, pages 1207–1216,                 Next-qa: Next phase of question-answering to explaining tem-
     2019. 2, 4                                                                poral actions. In Proceedings of the IEEE/CVF Conference
[51] Gemini Team, Rohan Anil, Sebastian Borgeaud, Yonghui                      on Computer Vision and Pattern Recognition (CVPR), pages
     Wu, Jean-Baptiste Alayrac, Jiahui Yu, Radu Soricut, Johan                 9777–9786, 2021. 6
     Schalkwyk, Andrew M Dai, Anja Hauth, et al. Gemini: a
                                                                          [66] Zhifei Xie and Changqiao Wu. Mini-omni: Language models
     family of highly capable multimodal models. arXiv preprint
                                                                               can hear, talk while thinking in streaming. arXiv preprint
     arXiv:2312.11805, 2023. 1, 4, 8
                                                                               arXiv:2408.16725, 2024. 8
[52] Qwen Team. Qwen2.5: A party of foundation models, 2024.
                                                                          [67] Zhifei Xie and Changqiao Wu. Mini-omni2: Towards open-
     1, 2, 4
                                                                               source gpt-4o model with vision, speech and duplex. arXiv
[53] Shengbang Tong, Ellis Brown, Penghao Wu, Sanghyun Woo,
                                                                               preprint arXiv:2410.11190, 2024. 1, 8
     Manoj Middepogu, Sai Charitha Akula, Jihan Yang, Shusheng
     Yang, Adithya Iyer, Xichen Pan, et al. Cambrian-1: A fully           [68] Lin Xu, Yilin Zhao, Daquan Zhou, Zhijie Lin, See Kiong Ng,
     open, vision-centric exploration of multimodal llms. arXiv                and Jiashi Feng. Pllava: Parameter-free llava extension from
     preprint arXiv:2406.16860, 2024. 1, 7                                     images to videos for video dense captioning. arXiv preprint
[54] Hugo Touvron, Matthieu Cord, Alexandre Sablayrolles,                      arXiv:2404.16994, 2024. 1, 2, 7, 8
     Gabriel Synnaeve, and Hervé Jégou. Going deeper with               [69] Fuzhao Xue, Yukang Chen, Dacheng Li, Qinghao Hu, Ligeng
     image transformers. In Proceedings of the IEEE/CVF inter-                 Zhu, Xiuyu Li, Yunhao Fang, Haotian Tang, Shang Yang, Zhi-
     national conference on computer vision, pages 32–42, 2021.                jian Liu, et al. Longvila: Scaling long-context visual language
     3                                                                         models for long videos. arXiv preprint arXiv:2408.10188,
[55] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Am-                2024. 1, 8
     jad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya             [70] Dongjie Yang, Suyuan Huang, Chengqiang Lu, Xiaodong
     Batra, Prajjwal Bhargava, Shruti Bhosale, et al. Llama 2:                 Han, Haoxin Zhang, Yan Gao, Yao Hu, and Hai Zhao.
     Open foundation and fine-tuned chat models. arXiv preprint                Vript: A video is worth thousands of words. arXiv preprint
     arXiv:2307.09288, 2023. 1                                                 arXiv:2406.06040, 2024. 4, 6


                                                                     11
[71] Yuan Yao, Tianyu Yu, Ao Zhang, Chongyi Wang, Junbo Cui,               [84] Wanrong Zhu, Jack Hessel, Anas Awadalla, Samir Yitzhak
     Hongji Zhu, Tianchi Cai, Haoyu Li, Weilin Zhao, Zhihui He,                 Gadre, Jesse Dodge, Alex Fang, Youngjae Yu, Ludwig
     et al. Minicpm-v: A gpt-4v level mllm on your phone. arXiv                 Schmidt, William Yang Wang, and Yejin Choi. Multimodal
     preprint arXiv:2408.01800, 2024. 8                                         c4: An open, billion-scale corpus of images interleaved with
[72] Jiabo Ye, Haiyang Xu, Haowei Liu, Anwen Hu, Ming Yan, Qi                   text. Advances in Neural Information Processing Systems, 36,
     Qian, Ji Zhang, Fei Huang, and Jingren Zhou. mplug-owl3:                   2024. 4
     Towards long image-sequence understanding in multi-modal
     large language models. arXiv preprint arXiv:2408.04840,
     2024. 3
[73] Zhou Yu, Dejing Xu, Jun Yu, Ting Yu, Zhou Zhao, Yueting
     Zhuang, and Dacheng Tao. Activitynet-qa: A dataset for
     understanding complex web videos via question answering. In
     Proceedings of the AAAI Conference on Artificial Intelligence,
     pages 9127–9134, 2019. 6
[74] Xiang Yue, Yuansheng Ni, Kai Zhang, Tianyu Zheng, Ruoqi
     Liu, Ge Zhang, Samuel Stevens, Dongfu Jiang, Weiming Ren,
     and Yuxuan Sun. Mmmu: A massive multi-discipline multi-
     modal understanding and reasoning benchmark for expert agi.
     In CVPR, 2024. 6
[75] Xiaohua Zhai, Basil Mustafa, Alexander Kolesnikov, and
     Lucas Beyer. Sigmoid loss for language image pre-training.
     In Proceedings of the IEEE/CVF International Conference
     on Computer Vision, pages 11975–11986, 2023. 4
[76] Hang Zhang, Xin Li, and Lidong Bing. Video-llama: An
     instruction-tuned audio-visual language model for video un-
     derstanding. arXiv preprint arXiv:2306.02858, 2023. 1, 2,
     8
[77] Haoji Zhang, Yiqin Wang, Yansong Tang, Yong Liu, Jiashi
     Feng, Jifeng Dai, and Xiaojie Jin. Flash-vstream: Memory-
     based real-time understanding for long video streams. arXiv
     preprint arXiv:2406.08085, 2024. 1, 8
[78] Kaichen Zhang, Bo Li, Peiyuan Zhang, Fanyi Pu,
     Joshua Adrian Cahyono, Kairui Hu, Shuai Liu, Yuanhan
     Zhang, Jingkang Yang, Chunyuan Li, and Ziwei Liu. Lmms-
     eval: Reality check on the evaluation of large multimodal
     models, 2024. 7
[79] Pan Zhang, Xiaoyi Dong, Yuhang Cao, Yuhang Zang, Rui
     Qian, Xilin Wei, Lin Chen, Yifei Li, Junbo Niu, Shuangrui
     Ding, et al. Internlm-xcomposer2. 5-omnilive: A comprehen-
     sive multimodal system for long-term streaming video and
     audio interactions. arXiv preprint arXiv:2412.09596, 2024. 8
[80] Peiyuan Zhang, Kaichen Zhang, Bo Li, Guangtao Zeng,
     Jingkang Yang, Yuanhan Zhang, Ziyue Wang, Haoran Tan,
     Chunyuan Li, and Ziwei Liu. Long context transfer from
     language to vision. arXiv preprint arXiv:2406.16852, 2024.
     1, 8
[81] Yuanhan Zhang, Jinming Wu, Wei Li, Bo Li, Zejun Ma, Ziwei
     Liu, and Chunyuan Li. Video instruction tuning with synthetic
     data. arXiv preprint arXiv:2410.02713, 2024. 1, 2, 4, 6
[82] Junjie Zhou, Yan Shu, Bo Zhao, Boya Wu, Shitao Xiao, Xi
     Yang, Yongping Xiong, Bo Zhang, Tiejun Huang, and Zheng
     Liu. Mlvu: A comprehensive benchmark for multi-task long
     video understanding. arXiv preprint arXiv:2406.04264, 2024.
     6
[83] Luowei Zhou, Nathan Louis, and Jason J Corso. Weakly-
     supervised video object grounding from text by loss weighting
     and object interaction. arXiv preprint arXiv:1805.02834,
     2018. 4


                                                                      12
