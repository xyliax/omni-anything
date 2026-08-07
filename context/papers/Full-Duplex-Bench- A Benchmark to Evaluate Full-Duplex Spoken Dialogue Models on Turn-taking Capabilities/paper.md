arXiv:2503.04721v3 [cs.CL] 16 Aug 2025

# Full-Duplex-Bench: A Benchmark to Evaluate Full-Duplex Spoken Dialogue Models on Turn-taking Capabilities

Guan-Ting Lin $ ^{1} $ Jiachen Lian $ ^{2*} $ Tingle Li $ ^{2*} $ Qirui Wang $ ^{3*} $ Gopala Anumanchipalli $ ^{2} $ Alexander H. Liu $ ^{4} $ Hung-yi Lee $ ^{1} $

 $ ^{1} $Graduate Institute of Communication Engineering, National Taiwan University

 $ ^{2} $UC Berkeley  $ ^{3} $University of Washington  $ ^{4} $MIT CSAIL

Abstract—Spoken dialogue modeling poses challenges beyond text-based language modeling, requiring real-time interaction, turn-taking, and backchanneling. While most Spoken Dialogue Models (SDMs) operate in half-duplex mode—processing one turn at a time—emerging full-duplex SDMs can listen and speak simultaneously, enabling more natural conversations. However, current evaluations remain limited, focusing mainly on turn-based metrics or coarse corpus-level analyses. To address this, we introduce Full-Duplex-Bench, a benchmark that systematically evaluates key interactive behaviors: pause handling, backchanneling, turn-taking, and interruption management. Our framework uses automatic metrics for consistent, reproducible assessment and provides a fair, fast evaluation setup. By releasing our benchmark and code, we aim to advance spoken dialogue modeling and foster the development of more natural and engaging SDMs.

Index Terms—Full-Duplex Dialogue, Benchmark, Spoken Language Models, Turn-Taking

## I. INTRODUCTION

Natural spoken dialogue is characterized by complex dynamics [1], [2]. Different from text-based language modeling, spoken dialogue involves problems beyond language understanding for communication, such as turn-taking [2]–[4], and backchanneling [5]. These fundamental aspects facilitate mutual understanding, engagement, and social connection. Over the years, Spoken Dialogue Models (SDMs) have become a major research focus, particularly with the rise of voice assistants.

Existing SDMs can be broadly categorized into two types: (1) Half-duplex SDMs: These models operate based on a turn-by-turn protocol, processing one audio stream at a time and switching roles in response to turn-changing signals. (2) Full-duplex SDMs: These models can simultaneously listen and speak, allowing them to capture the subtle timing of spoken conversation. They process continuous audio streams and model overlapping speech, pauses, and background noise. Furthermore, these models can capture essential spoken interaction behaviors, such as backchanneling, offering more natural and context-aware responses.

Although half-duplex SDMs have been the dominant approach, they often sound less natural than human speakers, who seamlessly listen and speak at the same time. Recent progress

<div style="text-align: center;"><img src="imgs/img_in_image_box_695_494_1061_819.jpg" alt="Image" width="29%" />

Evaluation Dimensions Criterions
1. Pause Handling
2. Backchanneling
3. Smooth Turn Taking
4. User Interruption

Not interrupting at natural pause
Backchannel at proper timing
Turn the turn in time
Shift focus to interrupting query
Model stream
User stream
Full-duplex SLM
?
output.wav
Post-processing

</div>


<div style="text-align: center;">Fig. 1: Overview pipeline of Full-Duplex-Bench. We feed user audio streams to a full-duplex SDM, which produces time-synchronous output. We then perform post-processing to align both streams at the transcript level, enabling automatic evaluation along multiple dimensions.</div>


in models like GPT-4o voice mode has sparked an interest in full-duplex capabilities for more human-like dialogues. Consequently, many new SDMs have emerged [6]–[12], with different architectures to enable real-time communication. As an increasing number of these systems are proposed, fair and open evaluation is critical to guide future advances in spoken dialogue research.

Evaluating SDMs is challenging because human conversation requires understanding a wide range of information and interpreting complex interactions within speech signals. Previous benchmarks have largely focused on: Content-based evaluation, measuring performance on tasks such as spoken question answering [13]–[17]; Instruction-following evaluation, assessing a system's ability to follow directives [18], [19]; and Paralinguistic evaluation, examining factors like emotion or speaking style [20]–[25]. However, these benchmarks mostly assume turn-based interactions, leaving the real-time aspects of full-duplex models under-explored.

Some recent studies attempt to evaluate interaction timing

 $ ^{*} $Equal contribution, listed alphabetically.

<div style="text-align: center;">TABLE I: Overview of full-duplex speech language models. “—” indicates properties that are not publicly available or unspecified. “E2E” denotes end-to-end speech modeling (without relying on text), “#ch” indicates the number of speech input channels, “Interrupt” refers to interruption handling, “BC” represents backchanneling capability, and “S2S Release” shows whether the complete speech-to-speech pipeline is publicly released.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Model</td><td style='text-align: center; word-wrap: break-word;'>Date</td><td style='text-align: center; word-wrap: break-word;'>E2E</td><td style='text-align: center; word-wrap: break-word;'>#ch</td><td style='text-align: center; word-wrap: break-word;'>Interrupt</td><td style='text-align: center; word-wrap: break-word;'>BC</td><td style='text-align: center; word-wrap: break-word;'>S2S</td><td style='text-align: center; word-wrap: break-word;'>Release</td></tr><tr><td colspan="8">Transparent Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dGSLM [26]</td><td style='text-align: center; word-wrap: break-word;'>2022/3</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>FSM [27]</td><td style='text-align: center; word-wrap: break-word;'>2024/5</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-Duplex [28]</td><td style='text-align: center; word-wrap: break-word;'>2024/6</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>VITA [9]</td><td style='text-align: center; word-wrap: break-word;'>2024/8</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SyncLLM [6]</td><td style='text-align: center; word-wrap: break-word;'>2024/9</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Parrot [29]</td><td style='text-align: center; word-wrap: break-word;'>2024/9</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MiniCPM-Duo [30]</td><td style='text-align: center; word-wrap: break-word;'>2024/9</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Moshi [7]</td><td style='text-align: center; word-wrap: break-word;'>2024/10</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SALMONN-omni [31]</td><td style='text-align: center; word-wrap: break-word;'>2024/11</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MinMo [11]</td><td style='text-align: center; word-wrap: break-word;'>2025/1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>OmniFlatten [32]</td><td style='text-align: center; word-wrap: break-word;'>2025/1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RTTL-DG [33]</td><td style='text-align: center; word-wrap: break-word;'>2025/1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>2</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Freeze-Omni [10]</td><td style='text-align: center; word-wrap: break-word;'>2024/11</td><td style='text-align: center; word-wrap: break-word;'>✗</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✓</td></tr><tr><td colspan="8">Closed-source Commercial Models</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>GPT-4o Voice Mode</td><td style='text-align: center; word-wrap: break-word;'>2024/5</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini Live</td><td style='text-align: center; word-wrap: break-word;'>2024/8</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>DouBao</td><td style='text-align: center; word-wrap: break-word;'>2025/1</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Nova Sonic [34]</td><td style='text-align: center; word-wrap: break-word;'>2025/4</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'>✓</td><td style='text-align: center; word-wrap: break-word;'>-</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>✗</td></tr></table>

in full-duplex dialogue. dGSLM [26] examines voice activity patterns by comparing model outputs to ground truth gaps, interpausal units, and pauses. However, the corpus-level statistics are difficult to interpret, and the ground truth is based on a specific dialogue dataset. Recently, Talking-Turns [35] trains a specialized judge model to evaluate alignment with conversational behaviors. However, this model is trained on a specific dialogue dataset, which may limit its generalizability to other dialogue types. Moreover, the evaluation relies on user studies, making the results difficult to reproduce due to variations in participants. While these works provide valuable insights, they highlight the need for a more unified and reproducible approach to evaluating full-duplex SDMs in real-world scenarios.

In this paper, we present Full-Duplex-Bench, the first scenario-driven benchmark for systematically evaluating key turn-taking behaviors in human-to-machine full-duplex spoken dialogue models (SDMs), as illustrated in Figure 1. The benchmark evaluates models under realistic conversational events such as backchannels and user interruptions, focusing on four critical aspects of real-time interaction: pause handling, backchanneling, turn-taking, and user interruption management. Our unified framework offers objective behavior detection, rapid diagnostic metrics, and an open, reproducible toolkit, enabling consistent and reliable cross-model comparisons. The metrics are intentionally descriptive rather than prescriptive, allowing developers to prioritize behaviors according to specific application requirements. Designed for efficiency and full automation, the benchmark supports rapid large-scale evaluation and provides deeper insights into how existing systems manage interactive dynamics in real time. We publicly release the benchmark and codebase to facilitate further research and the development of more engaging and conversational SDMs $ ^{1} $.

II. RELATED WORKS

### A. Full-duplex Spoken Dialogue Models

Recent advances in SDMs have increasingly focused on full-duplex capabilities. We categorize existing full-duplex SDMs into two main groups: Transparent Models, which offer detailed architecture and implementation, and Closed-Source Commercial Systems, which are accessible only through demos. Table I summarizes the key characteristics of these models.

Transparent Models: These models are publicly available with open-source implementations or detailed technical descriptions, enabling reproducibility and deeper analysis. They fall into two subcategories:

Cascaded Models. These systems follow a modular pipeline structure, typically integrating ASR, LLM, and TTS components. Wang et al. [27] introduce control, speak, and listen tokens in an LLM framework with perceptual inputs. MiniCPMDuplex [28] and MiniCPM-Duo [30] apply time-sliced token windows for synchronous dialogue modeling. VITA [9] and Freeze-Omni [10] operate on raw speech inputs, improving latency while maintaining internal reliance on text. While cascaded approaches offer flexibility and stronger semantic modeling, they often suffer from cross-module latency and the loss of nuanced speech features, driving growing interest in end-to-end alternatives.

End-to-End Models. These models jointly model speaker and listener audio streams. dGSLM [26] employs a Siamese network with cross-attention for two-channel dialogue. Moshi [7] uses parallel processing streams to handle real-time user speech and supports overlaps and interruptions. SyncLLM [6] introduces time-synchronous audio chunks modeling for two-channel speech. OmniFlatten [32] flattens and processes speech and text tokens jointly. SALMONN-omni [31] and MinMo [11] inject state tokens to improve turn-taking modeling. Parrot [29] predicts next-token pairs across streams, while RTTL-DG [33] uses a dialogue manager to control generation timing. By operating directly on audio data, end-to-end approaches have the

 $ ^{1} $Data and code are released in https://github.com/DanielLin94144/Full-Duplex-Bench.

potential to capture a wider range of speech features—including paralinguistic and non-verbal cues—as well as dialogue behaviors such as backchanneling.

Closed-Source Commercial Systems: Several commercial models have demonstrated full-duplex capabilities through public demos. These systems—such as GPT-4o Voice Mode $ ^{2} $, Gemini Live $ ^{3} $, Doubao $ ^{4} $, and Nova Sonic [34]—are not open-sourced and lack publicly available architectural details. Nonetheless, we include them in Table I. Their emergence underscores the need for open and standardized benchmarks to evaluate interaction quality across both transparent research models and proprietary commercial systems.

### B. Evaluation Benchmarks

Benchmarks offer a common framework for comparing models and understanding their performance. In the speech community, several benchmarks have been proposed to evaluate specific aspects of speech models. The SUPERB series [36]–[38] evaluates self-supervised speech representations across a variety of tasks. Recent advances in universal spoken language models have resulted in benchmarks that evaluate both understanding and generation. These can be grouped as follows: Multi-task Instruction Following: Dynamic-SUPERB [18], [19], Voicebench [39], and AIR-Bench [22] test models' ability to perform a range of tasks based on specific instructions. Semantic Understanding: For low-level language skills such as syntax and grammar, benchmarks like ZeroSpeech [40] and datasets such as Spoken-StoryCloze [41] have been introduced. Higher-level comprehension, including spoken question answering, is measured by benchmarks like Llama-Question [14] and Spoken-Question. Paralinguistic Perception: VoxDialogue [20], SDEval [21], and StyleTalk [23] evaluate the ability to produce natural responses by considering features such as emotion, gender, and accent. Talking-Turns [35] trains a judge model on a specific dialogue dataset to assess conversational alignment, but its generalizability is limited. Its reliance on user studies also hinders reproducibility. These limitations highlight the need for a unified, reproducible framework for evaluating full-duplex SDMs. To this end, we propose a benchmark with an automatic evaluation pipeline and behavior-specific metrics for assessing conversational performance.

## III. FULL-DUPLEX-BENCH FRAMEWORK

For clarity, we first define several key terms that will be used in this paper:

Backchannel: In natural conversations, listeners often provide short verbal or nonverbal signals, known as backchannels, to indicate active engagement and understanding. These backchannels include utterances such as “mm-hmm,” and “uhhuh”, which typically occur while another person is speaking. Effective backchanneling enhances conversational fluidity by signaling attentiveness without disrupting the speaker. Generally, backchanneling refers to short utterances produced by the listener while the speaker is talking.



In this work, we classify a speech segment as backchanneling if it meets the following criteria: (1) it has a short duration of less than 1 second; and (2) it contains fewer than two words. This ensures that speech is delivered at a reasonable pace and that brief utterances do not interrupt the current speaker's turn. The concept of backchanneling differs across the literature [42], [43], so developing a comprehensive detector is beyond the scope of this paper and is left for future work.

Takeover (TO): A takeover occurs when the model effectively assumes control of the conversation, dominating the turn and granting minimal opportunity for the user to speak. In this work, takeover is treated as a binary variable. If the model merely responds with silence or a backchannel, no takeover is deemed to have occurred. Conversely, any other non-silent speech that is not a backchannel indicates the model's attempt to take over. Formally,

 $$ \mathrm{TO}=\left\{\begin{aligned}&0,&if~silence~or~backchannel\\ &1,&otherwise\end{aligned}\right. $$ 

Takeover Rate (TOR): To quantify how often takeovers occur, we define the TOR as the average value of the binary TO variable across the dataset:  $ \text{TOR} = \frac{1}{N} \sum_{i=1}^{N} \text{TO}_i $, where  $ N $ is the total number of dialogue turns, and  $ \text{TO}_i $ is the binary takeover variable for sample  $ i $.

### A. Overview

As illustrated in Figure 1, our framework employs a unified speech input (denoted as “input.wav”) to simulate real-time user interactions with SDMs, enabling controlled evaluations across various dimensions. For each aspect, we design targeted test samples, collect the model's speech responses (“output.wav”), and use an ASR model (Nvidia parakeet-tdt-0.6b-v2 $ ^{5} $ to produce word-level, time-aligned transcriptions (“output.json”). Dedicated metrics are then applied to assess performance in each dimension.

### B. Evaluation Dimensions

Figure 2 illustrates the following four evaluation dimensions.

1) Pause Handling

Humans naturally pause and hesitate during conversations. Pauses can occur between consecutive turns or within the same sentence. These pauses are often not intended to yield the turn but rather to maintain control of the conversation. Therefore, taking over the turn during such pauses is undesirable and may lead to user dissatisfaction. Effective pause handling ensures that the model does not interrupt when a speaker takes a natural pause.

Research Question: Can the model recognize when the other speaker is still holding the turn and understand that it should not take over?

 $ ^{2} $https://openai.com/index/hello-gpt-4o/

 $ ^{3} $https://blog.google/products/gemini/made-by-google-gemini-ai-updates/
 $ ^{4} $https://team.doubao.com/en/special/realtime_voice

 $ ^{5} $https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2

<div style="text-align: center;"><img src="imgs/img_in_image_box_315_106_901_434.jpg" alt="Image" width="47%" />

1. Pause Handling
2. Backchanneling
3. Smooth Turn Taking
4. User Interruption
5. Wait I want to ...
6. User
7. User
8. User
9. User
10. User
11. User
12. User
13. User
14. User
15. User
16. User
17. User
18. User
19. User
20. User
21. User
22. User
23. User
24. User
25. User
26. User
27. User
28. User
29. User
30. User
31. User
32. User
33. User
34. User
35. User
36. User
37. User
38. User
39. User
40. User
41. User
42. User
43. User
44. User
45. User
46. User
47. User
48. User
49. User
50. User
51. User
52. User
53. User
54. User
55. User
56. User
57. User
58. User
59. User
60. User
61. User
62. User
63. User
64. User
65. User
66. User
67. User
68. User
69. User
70. User
71. User
72. User
73. User
74. User
75. User
76. User
77. User
78. User
79. User
80. User
81. User
82. User
83. User
84. User
85. User
86. User
87. User
88. User
89. User
90. User
91. User
92. User
93. User
94. User
95. User
96. User
97. User
98. User
99. User
100. User
101. User
102. User
103. User
104. User
105. User
106. User
107. User
108. User
109. User
110. User
111. User
112. User
113. User
114. User
115. User
116. User
117. User
118. User
119. User
120. User
121. User
122. User
123. User
124. User
125. User
126. User
127. User
128. User
129. User
130. User
131. User
132. User
133. User
134. User
135. User
136. User
137. User
138. User
139. User
140. User
141. User
142. User
143. User
144. User
145. User
146. User
147. User
148. User
149. User
150. User
151. User
152. User
153. User
154. User
155. User
156. User
157. User
158. User
159. User
160. User
161. User
162. User
163. User
164. User
165. User
166. User
167. User
168. User
169. User
170. User
171. User
172. User
173. User
174. User
175. User
176. User
177. User
178. User
179. User
180. User
181. User
182. User
183. User
184. User
185. User
186. User
187. User
188. User
189. User
190. User
191. User
192. User
193. User
194. User
195. User
196. User
197. User
198. User
199. User
200. User
201. User
202. User
203. User
204. User
205. User
206. User
207. User
208. User
209. User
210. User
211. User
212. User
213. User
214. User
215. User
216. User
217. User
218. User
219. User
220. User
221. User
222. User
223. User
224. User
225. User
226. User
227. User
228. User
229. User
230. User
231. User
232. User
233. User
234. User
235. User
236. User
237. User
238. User
239. User
240. User
241. User
242. User
243. User
244. User
245. User
246. User
247. User
248. User
249. User
250. User
251. User
252. User
253. User
254. User
255. User
256. User
257. User
258. User
259. User
260. User
261. User
262. User
263. User
264. User
265. User
266. User
267. User
268. User
269. User
270. User
271. User
272. User
273. User
274. User
275. User
276. User
277. User
278. User
279. User
280. User
281. User
282. User
283. User
284. User
285. User
286. User
287. User
288. User
289. User
290. User
291. User
292. User
293. User
294. User
295. User
296. User
297. User
298. User
299. User
300. User
301. User
302. User
303. User
304. User
305. User
306. User
307. User
308. User
309. User
310. User
311. User
312. User
313. User
314. User
315. User
316. User
317. User
318. User
319. User
320. User
321. User
322. User
323. User
324. User
325. User
326. User
327. User
328. User
329. User
330. User
331. User
332. User
333. User
334. User
335. User
336. User
337. User
338. User
339. User
340. User
341. User
342. User
343. User
344. User
345. User
346. User
347. User
348. User
349. User
350. User
351. User
352. User
353. User
354. User
355. User
356. User
357. User
358. User
359. User
360. User
361. User
362. User
363. User
364. User
365. User
366. User
367. User
368. User
369. User
370. User
371. User
372. User
373. User
374. User
375. User
376. User
377. User
378. User
379. User
380. User
381. User
382. User
383. User
384. User
385. User
386. User
387. User
388. User
389. User
390. User
391. User
392. User
393. User
394. User
395. User
396. User
397. User
398. User
399. User
400. User
401. User
402. User
403. User
404. User
405. User
406. User
407. User
408. User
409. User
410. User
411. User
412. User
413. User
414. User
415. User
416. User
417. User
418. User
419. User
420. User
421. User
422. User
423. User
424. User
425. User
426. User
427. User
428. User
429. User
430. User
431. User
432. User
433. User
434. User
435. User
436. User
437. User
438. User
439. User
440. User
441. User
442. User
443. User
444. User
445. User
446. User
447. User
448. User
449. User
450. User
451. User
452. User
453. User
454. User
455. User
456. User
457. User
458. User
459. User
460. User
461. User
462. User
463. User
464. User
465. User
466. User
467. User
468. User
469. User
470. User
471. User
472. User
473. User
474. User
475. User
476. User
477. User
478. User
479. User
480. User
481. User
482. User
483. User
484. User
485. User
486. User
487. User
488. User
489. User
490. User
491. User
492. User
493. User
494. User
495. User
496. User
497. User
498. User
499. User
500. User
501. User
502. User
503. User
504. User
505. User
506. User
507. User
508. User
509. User
510. User
511. User
512. User
513. User
514. User
515. User
516. User
517. User
518. User
519. User
520. User
521. User
522. User
523. User
524. User
525. User
526. User
527. User
528. User
529. User
530. User
531. User
532. User
533. User
534. User
535. User
536. User
537. User
538. User
539. User
540. User
541. User
542. User
543. User
544. User
545. User
546. User
547. User
548. User
549. User
550. User
551. User
552. User
553. User
554. User
555. User
556. User
557. User
558. User
559. User
560. User
561. User
562. User
563. User
564. User
565. User
566. User
567. User
568. User
569. User
570. User
571. User
572. User
573. User
574. User
575. User
576. User
577. User
578. User
579. User
580. User
581. User
582. User
583. User
584. User
585. User
586. User
587. User
588. User
589. User
590. User
591. User
592. User
593. User
594. User
595. User
596. User
597. User
598. User
599. User
600. User
601. User
602. User
603. User
604. User
605. User
606. User
607. User
608. User
609. User
610. User
611. User
612. User
613. User
614. User
615. User
616. User
617. User
618. User
619. User
620. User
621. User
622. User
623. User
624. User
625. User
626. User
627. User
628. User
629. User
630. User
631. User
632. User
633. User
634. User
635. User
636. User
637. User
638. User
639. User
640. User
641. User
642. User
643. User
644. User
645. User
646. User
647. User
648. User
649. User
650. User
651. User
652. User
653. User
654. User
655. User
656. User
657. User
658. User
659. User
660. User
661. User
662. User
663. User
664. User
665. User
666. User
667. User
668. User
669. User
670. User
671. User
672. User
673. User
674. User
675. User
676. User
677. User
678. User
679. User
680. User
681. User
682. User
683. User
684. User
685. User
686. User
687. User
688. User
689. User
690. User
691. User
692. User
693. User
694. User
695. User
696. User
697. User
698. User
69

</div>


<div style="text-align: center;">Fig. 2: Illustration of the four evaluation dimensions in Full-Duplex-Bench. (1) Pause Handling: the model stays silent during user pauses; (2) Backchanneling: the model offers short, timely acknowledgments; (3) Smooth Turn-taking: the model takes the turn in time; and (4) User Interruption: the model handles sudden user input with appropriate, well-timed responses.</div>


Metric: The ideal model behavior is to avoid taking over the turn while the user is speaking. To evaluate this, we use the Takeover Rate (TOR). A lower TOR signifies better pause management, indicating that the model effectively waits for the user's turn to end. In contrast, a higher TOR suggests that the model is more likely to take over the conversation before the user has yielded the turn.

#### 2) Backchanneling

Drawing on the definition in Section III, we assess whether the model, when interacting with a dominant speaker, actively listens and provides backchannels at suitable moments to facilitate dialogue engagement. A model exhibiting human-like backchanneling behavior should respond at the right times and with an appropriate frequency.

Research Question: Can the model determine when to offer backchannels in a human-like manner without interrupting the speaker?

Metric: To measure how well the models generate backchannel cues, we use three metrics:

- TOR: As with pause handling, the model should avoid dominating the turn, so a lower TOR is preferable.

- Backchannel Frequency (Freq): Each backchannel event is counted and normalized by duration (events per second). When the model does not take over the turn (TOR = 0), a higher backchanneling frequency indicates that the model responds backchannel more often, but this does not necessarily imply better or more natural behavior, as it also depends on timing and context.

- Jensen-Shannon Divergence (JSD): This captures the difference between the model's predicted timing of backchannels and actual human timing. The model outputs a probability distribution  $ P $, where  $ P(i) $ denotes the likelihood of a backchannel occurring in time window i. The ground truth distribution Q is derived from human-annotated backchannel timings (details in III-C), aligned to the same set of time windows. To measure the similarity between P and Q, we compute the Jensen–Shannon Divergence (JSD) as:



 $$ \mathbf{J}\mathbf{S}\mathbf{D}(P||Q)=\frac{1}{2}\sum_{i}P(i)\log\frac{P(i)}{M(i)}+\frac{1}{2}\sum_{i}Q(i)\log\frac{Q(i)}{M(i)}, $$ 

where  $ M(i) = \frac{1}{2}(P(i) + Q(i)) $, and i indexes the discrete time windows. JSD ranges from 0 (perfect alignment) to 1 (complete divergence), providing a symmetric and bounded measure of similarity between model predictions and human backchannel behavior. We only calculate this metric when the model does not take over the turn, where each backchannel event is counted as one-hot and normalized into a probability distribution. If the model stays silent throughout, we assume a uniform probability distribution, treating it as a random baseline without backchannel knowledge.

#### 3) Smooth Turn Taking

Effective turn-taking is crucial for maintaining a natural and engaging conversation. In human dialogue, smooth turn transitions occur when speakers respond promptly without excessive delay or overlap. A well-designed model should be capable of recognizing turn boundaries and responding with appropriate timing to ensure fluid interactions.

Research Question: Can the model detect the end of a speaker's turn and respond promptly without long pauses?

Metric: We measure the averaged response latency, the time (in seconds) between the end of the user's speech and the start of the model's response. Lower latency values indicate smoother turn-taking. In cases where the model fails to respond, we record the TOR. The latency is calculated only when TO equals 1. This avoids averaging with non-takeover periods, which would introduce significant variance due to periods of silence.

#### 4) User Interruption

In human conversations, interruptions are common and can occur when a listener interjects mid-turn to clarify, disagree, or shift the discussion. A well-designed conversational model should be able to recognize and adapt to such interruptions by adjusting its response appropriately. Effective handling of

<div style="text-align: center;">TABLE II: The number of samples for each dataset and task.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Dataset</td><td style='text-align: center; word-wrap: break-word;'>Task</td><td style='text-align: center; word-wrap: break-word;'># of Samples</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Candor</td><td style='text-align: center; word-wrap: break-word;'>Pause Handling</td><td style='text-align: center; word-wrap: break-word;'>216</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Candor</td><td style='text-align: center; word-wrap: break-word;'>Smooth Turn-Taking</td><td style='text-align: center; word-wrap: break-word;'>119</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ICC</td><td style='text-align: center; word-wrap: break-word;'>Backchannel</td><td style='text-align: center; word-wrap: break-word;'>55</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Synthetic</td><td style='text-align: center; word-wrap: break-word;'>User Interruption</td><td style='text-align: center; word-wrap: break-word;'>200</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Synthetic</td><td style='text-align: center; word-wrap: break-word;'>Pause Handling</td><td style='text-align: center; word-wrap: break-word;'>137</td></tr></table>

interruptions ensures that the model remains responsive and coherent, even when the dialogue flow is disrupted.

Research Question: Can the model detect and adapt to user interruptions while maintaining a coherent and timely response?

Metric: The evaluation consists of three measures:

- TOR: TOR is measured to ensure the model takes the turn following an interruption (ideally TOR = 1). The below metrics are calculated only when the TO is 1.

- GPT-4o Score: A large language model evaluates the quality of the system's response (coherence, relevance, and adaptability) on a scale from 0 to 5. Higher scores indicate better performance.

- Latency After Interruption: The averaged time taken for the model to respond after an interruption, with lower averaged latency indicating smoother interaction.

### C. Data Curation

The overall evaluation set of Full-Duplex-Bench is shown in the Table II. We explain how we collect the data for each evaluation dimension as follows:

Candor (Pause Handling, Smooth Turn-taking): We utilize Candor [43], an 850-hour dataset of open-ended, spontaneous speech conversations with two-channel recordings, as our primary data source. To construct suitable data samples for our benchmark:

For the pause handling task, we first apply voice activity detection to identify segments with no overlapping speech, ensuring that only one speaker is active. We then select turns containing an internal pause between 0.4 and 1.0 seconds. This range is informed by prior research showing that pauses of around one second are perceived as a natural upper bound in English conversation [44], and that pauses within this range can influence listener impressions [45]. We exclude turns shorter than 5 seconds and remove cases where the speech immediately before or after the pause consists of backchannel responses. For the smooth turn-taking task, we compute the gap between each pair of consecutive turns and retain only those where all gaps are less than 0.4 seconds. This threshold is based on findings that smooth conversational transitions in English typically occur within 200–250 milliseconds [46], and we conservatively set 0.4 seconds as an upper bound. We further require no overlapping speech, each turn to be longer than 4 seconds, and that the utterances are not backchanneling. To give evaluated models sufficient time to respond, we append 5 seconds of silence at the end of the input stream.

After automatic filtering, all retained segments are manually reviewed with dual-channel evidence (whether the partner is silent or entering, and whether there is hesitation or fluent continuation).

ICC (Backchannel): Umair et al. [47] use the In Conversation Corpus (ICC) to collect Transition Relevance Places (TRPs), which are points in a speaker's utterance that signal appropriate moments for the listener to respond. This dataset consists of 28.33 minutes of high-quality informal American English dialogues, capturing responses from 118 native speakers with no prior expertise in turn-taking research. Participants were instructed to provide brief backchannel responses (e.g., "hmm," "yes") whenever they found it appropriate. Their responses were recorded on individual audio channels, synchronized with the stimulus audio. On average, 59 participants responded to each stimulus turn. This allows for estimating both the likelihood of perceiving a TRP at a given moment and the distribution of these perceived response locations. By segmenting the audio into 200-ms time windows and normalizing the backchannel counts, we generate a ground truth backchannel distribution Q for computing JSD for each stimulus.



Synthetic Data (User Interruption, Pause Handling): To address the scarcity of user interruptions in existing public datasets, we generated synthetic dialogues using GPT-4o [48], which include both contextual turns and interruption turns. Text-to-Speech synthesis was performed using ChatTTS $ ^{6} $, with 10 different speaker voices randomly assigned across samples to enhance diversity. For each input stream fed to the evaluated model, the interrupting speech is played around 7 seconds after the preceding utterance. Additionally, we append 15 seconds of silence after the interruption to allow the model time to respond.

For the synthetic pause handling task, we leverage the [uv_break] tag supported by ChatTTS to insert controlled pauses into the speech, enabling us to evaluate each model's robustness to intra-turn pauses. In total, we collect 200 samples for user interruption and 137 samples for pause handling.

## IV. MODELS UNDER EVALUATION

Since many models do not release complete speech-to-speech checkpoints (see Table I, column "S2S Release"), currently we evaluate models with a publicly available speech-to-speech model and inference pipeline. We also include the recently released Gemini Live API as a representative commercial model due to its user-friendly interface.

• dGSLM [26]: A textless speech-to-speech model that generates natural conversations directly from audio. It uses (1) a HuBERT+k-means encoder [49], (2) a dual-tower Transformer for two-channel dialogue modeling, and (3) a HiFi-GAN decoder. Trained on 2,000 hours of phone calls [50], it captures both linguistic and paralinguistic cues. Originally non-interactive, we adapt it for live interaction using the official implementation $ ^{7} $ with our modifications.

- Moshi [7]: A real-time speech-to-speech system combining a 7B LLM (Helium) and neural codec (Mimi) via residual vector quantization. It features an “Inner Monologue” step to improve fluency and supports overlapping speech and

 $ ^{6} $https://github.com/2noise/ChatTTS

 $ ^{7} $https://github.com/facebookresearch/fairseq/tree/main/examples/textless_nlp/dgslm

<div style="text-align: center;">TABLE III: Models comparison. We evaluate several models across different conversational dimensions, where Latency is presented in seconds.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Dimension</td><td colspan="2">Pause Handling</td><td colspan="2">Backchannel</td><td colspan="2">Smooth Turn Taking</td><td colspan="3">User Interruption</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Data</td><td style='text-align: center; word-wrap: break-word;'>Synthetic</td><td style='text-align: center; word-wrap: break-word;'>Candor</td><td colspan="2">ICC</td><td colspan="2">Candor</td><td colspan="3">Synthetic</td><td style='text-align: center; word-wrap: break-word;'></td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Metric</td><td style='text-align: center; word-wrap: break-word;'>TOR ( $ \downarrow $)</td><td style='text-align: center; word-wrap: break-word;'>TOR ( $ \downarrow $)</td><td style='text-align: center; word-wrap: break-word;'>TOR ( $ \downarrow $)</td><td style='text-align: center; word-wrap: break-word;'>Freq ( $ \uparrow $)</td><td style='text-align: center; word-wrap: break-word;'>JSD ( $ \downarrow $)</td><td style='text-align: center; word-wrap: break-word;'>TOR ( $ \uparrow $)</td><td style='text-align: center; word-wrap: break-word;'>Latency ( $ \downarrow $)</td><td style='text-align: center; word-wrap: break-word;'>TOR ( $ \uparrow $)</td><td style='text-align: center; word-wrap: break-word;'>GPT-4o( $ \uparrow $)</td><td style='text-align: center; word-wrap: break-word;'>Latency ( $ \downarrow $)</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>dGSLM</td><td style='text-align: center; word-wrap: break-word;'>0.934</td><td style='text-align: center; word-wrap: break-word;'>0.935</td><td style='text-align: center; word-wrap: break-word;'>0.691</td><td style='text-align: center; word-wrap: break-word;'>0.015</td><td style='text-align: center; word-wrap: break-word;'>0.934</td><td style='text-align: center; word-wrap: break-word;'>0.975</td><td style='text-align: center; word-wrap: break-word;'>0.352</td><td style='text-align: center; word-wrap: break-word;'>0.917</td><td style='text-align: center; word-wrap: break-word;'>0.201</td><td style='text-align: center; word-wrap: break-word;'>2.531</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Moshi</td><td style='text-align: center; word-wrap: break-word;'>0.985</td><td style='text-align: center; word-wrap: break-word;'>0.980</td><td style='text-align: center; word-wrap: break-word;'>1.000</td><td style='text-align: center; word-wrap: break-word;'>0.001</td><td style='text-align: center; word-wrap: break-word;'>0.957</td><td style='text-align: center; word-wrap: break-word;'>0.941</td><td style='text-align: center; word-wrap: break-word;'>0.265</td><td style='text-align: center; word-wrap: break-word;'>1.000</td><td style='text-align: center; word-wrap: break-word;'>0.765</td><td style='text-align: center; word-wrap: break-word;'>0.257</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Freeze-Omni</td><td style='text-align: center; word-wrap: break-word;'>0.642</td><td style='text-align: center; word-wrap: break-word;'>0.481</td><td style='text-align: center; word-wrap: break-word;'>0.636</td><td style='text-align: center; word-wrap: break-word;'>0.001</td><td style='text-align: center; word-wrap: break-word;'>0.997</td><td style='text-align: center; word-wrap: break-word;'>0.336</td><td style='text-align: center; word-wrap: break-word;'>0.953</td><td style='text-align: center; word-wrap: break-word;'>0.867</td><td style='text-align: center; word-wrap: break-word;'>3.615</td><td style='text-align: center; word-wrap: break-word;'>1.409</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Gemini Live</td><td style='text-align: center; word-wrap: break-word;'>0.255</td><td style='text-align: center; word-wrap: break-word;'>0.310</td><td style='text-align: center; word-wrap: break-word;'>0.091</td><td style='text-align: center; word-wrap: break-word;'>0.012</td><td style='text-align: center; word-wrap: break-word;'>0.896</td><td style='text-align: center; word-wrap: break-word;'>0.655</td><td style='text-align: center; word-wrap: break-word;'>1.301</td><td style='text-align: center; word-wrap: break-word;'>0.891</td><td style='text-align: center; word-wrap: break-word;'>3.376</td><td style='text-align: center; word-wrap: break-word;'>1.183</td></tr></table>

interruptions through a multi-stream architecture. We use the official implementation $ ^{8} $.

• Freeze-Omni [10]: A cascaded full-duplex system with a frozen LLM pipeline. VAD triggers chunk-wise encoding, and a classification head predicts dialogue states to control turn-taking. Parallel modules handle streaming, speaking, and monitoring. Evaluated locally using the official server.

• Gemini Live: Based on the official API documentation $ ^{9} $, we use the gemini-2.0-flash-live-001 model. The input.wav file is first converted to 16 kHz PCM-16 format, then divided into 30 ms chunks and streamed to the Gemini Live API. Server-side voice activity detection (VAD) is used to segment the audio and trigger responses. A new session is initiated after each model reply. All generated outputs are aligned with the original input duration, preserving silence in regions where no response is produced.

## V. RESULTS

Table III presents the results across four evaluation dimensions. The key findings are summarized as follows:

sions. The key findings are summarized as follows: Avoiding Interruptions During Speaker Pauses: All three SDMs exhibit high Takeover Rates (TOR) when managing speaker pauses, indicating frequent interruptions during natural breaks. The end-to-end models (dGSLM and Moshi) tend to interrupt more often across both real and synthetic datasets. In contrast, Freeze-Omni, which incorporates a dedicated module for predicting speaking and listening states, demonstrates a significantly lower TOR. This suggests that an explicit turn-taking control module can better manage pauses and may offer improvements if integrated into end-to-end systems. Conversely, Gemini Live achieves the lowest TOR among all models, including open-source ones, and exhibits a higher likelihood of taking over on Candor compared to synthetic data.

Backchanneling Dynamics: We evaluate using TOR, backchannel frequency (Freq), and Jensen-Shannon Divergence (JSD). Similar to pause handling, Moshi frequently takes over the turn, resulting in a high TOR. Both dGSLM and Freeze-Omni achieve lower TORs. Among the three open-sourced SDMs, dGSLM produces the most backchannel responses with more natural timing (Freq = 0.015, JSD = 0.934) when it does not take over the turn. In contrast, Freeze-Omni remains largely silent, producing few backchannel responses. The commercial Gemini Live achieves the lowest TOR and the best JSD, indicating superior ability in identifying appropriate moments for backchanneling.

Latency of Turn-Taking: We assessed TOR and average response latency on the Candor dataset. dGSLM and Moshi exhibit high TORs and respond quickly, with an average latency of around 0.3 seconds. Freeze-Omni, due to its cascaded architecture—which first generates text and then synthesizes speech—exhibits higher latency. Its lower TOR likely reflects missed opportunities to take over the turn, possibly due to failures in detecting turn ends. Interestingly, Gemini Live achieves a TOR of only 0.655, suggesting that even commercial models sometimes fail to take the turn in real dialogue data. Managing User Interruptions: Freeze-Omni handles user interruptions effectively, achieving significantly higher contextual relevance scores while maintaining acceptable latency. This strength is attributed to its 'model-as-a-server' strategy, which leverages a pool of models to manage user barge-ins efficiently. Gemini Live shows comparable performance, with relatively better TOR and latency, though it yields a slightly lower GPT-4o score. In contrast, the end-to-end SDMs struggle with coherence. Moshi responds promptly but yields a lower GPT-4o score (0.765), while dGSLM performs poorly, with high latency and diminished content quality (GPT-4o score: 0.201). These results highlight the challenges end-to-end systems face in preserving semantic coherence during user interruptions.



## VI. CONCLUSION

In this paper, we introduced Full-Duplex-Bench, a benchmark designed to evaluate critical aspects of full-duplex spoken dialogue models. Our framework targets key interaction dimensions—pause handling, backchanneling, smooth turn-taking, and user interruption management—addressing limitations of existing benchmarks that primarily focus on half-duplex settings or coarse corpus-level metrics. To ensure systematic and reproducible evaluation, we propose automatic metrics tailored to real-time interaction. Experiments on full-duplex models reveal distinct model features and highlight areas for improvement. By releasing our data and behavior-specific metrics, we hope Full-Duplex-Bench provides a practical foundation for evaluating full-duplex spoken dialogue systems.

## VII. LIMITATION AND FUTURE WORK

Our framework does not yet link described behaviors to human preferences; users need to determine what constitutes desirable or undesirable behavior according to their specific goals. Future work can integrate human judgment studies to provide the preference. The present analysis is limited to English, and extending the framework to other languages will be essential for assessing cross-linguistic generality.

 $ ^{8} $https://github.com/kyutai-labs/moshi

 $ ^{9} $https://ai.google.dev/gemini-api/docs/live

## REFERENCES

[1] E. A. Schegloff, “Overlapping talk and the organization of turn-taking for conversation,” Language in society, vol. 29, no. 1, pp. 1–63, 2000.

[2] A. Gravano and J. Hirschberg, “Turn-taking cues in task-oriented dialogue,” Computer Speech & Language, vol. 25, no. 3, pp. 601–634, 2011.

[3] S. Duncan, “Some signals and rules for taking speaking turns in conversations.” Journal of personality and social psychology, vol. 23, no. 2, p. 283, 1972.

[4] A. Raux and M. Eskenazi, “Optimizing the turn-taking behavior of task-oriented spoken dialog systems,” ACM Transactions on Speech and Language Processing (TSLP), vol. 9, no. 1, pp. 1–23, 2012.

[5] E. A. Schegloff, Discourse as an interactional achievement: Some uses of "uh huh" and other things that come between sentences. Analyzing discourse: Text and talk/Georgetown University Press, 1982.

[6] B. Veluri, B. Peloquin, B. Yu, H. Gong, and S. Gollakota, “Beyond turn-based interfaces: Synchronous llms as full-duplex dialogue agents,” in Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, 2024, pp. 21390–21402.

[7] A. Défossez, L. Mazaré, M. Orsini, A. Royer, P. Pérez, H. Jégou, E. Grave, and N. Zeghidour, “Moshi: a speech-text foundation model for real-time dialogue,” Kyutai, Tech. Rep., September 2024. [Online]. Available: http://kyutai.org/Moshi.pdf

[8] P. Wang, S. Lu, Y. Tang, S. Yan, W. Xia, and Y. Xiong, “A full-duplex speech dialogue scheme based on large language model,” in The Thirty-eighth Annual Conference on Neural Information Processing Systems, 2024. [Online]. Available: https://openreview.net/forum?id=YawXY6mWiK

[9] C. Fu, H. Lin, Z. Long, Y. Shen, M. Zhao, Y. Zhang, S. Dong, X. Wang, D. Yin, L. Ma et al., “Vita: Towards open-source interactive omni multimodal llm,” arXiv preprint arXiv:2408.05211, 2024.

[10] X. Wang, Y. Li, C. Fu, Y. Shen, L. Xie, K. Li, X. Sun, and L. Ma, “Freeze-omni: A smart and low latency speech-to-speech dialogue model with frozen llm,” arXiv preprint arXiv:2411.00774, 2024.

[11] Q. Chen, Y. Chen, Y. Chen, M. Chen, Y. Chen, C. Deng, Z. Du, R. Gao, C. Gao, Z. Gao et al., “Minmo: A multimodal large language model for seamless voice interaction,” arXiv preprint arXiv:2501.06282, 2025.

[12] S. Ji, Y. Chen, M. Fang, J. Zuo, J. Lu, H. Wang, Z. Jiang, L. Zhou, S. Liu, X. Cheng et al., “Wavchat: A survey of spoken dialogue models,” arXiv preprint arXiv:2411.13577, 2024.

[13] M. Hassid, T. Remez, T. A. Nguyen, I. Gat, A. Conneau, F. Kreuk, J. Copet, A. Defossez, G. Synnaeve, E. Dupoux et al., “Textually pretrained speech language models,” Advances in Neural Information Processing Systems, vol. 36, 2024.

[14] E. Nachmani, A. Levkovitch, R. Hirsch, J. Salazar, C. Asawaroengchai, S. Mariooryad, E. Rivlin, R. Skerry-Ryan, and M. T. Ramanovich, “Spoken question answering and speech continuation using spectrogram-powered LLM,” in The Twelfth International Conference on Learning Representations, 2024. [Online]. Available: https://openreview.net/forum?id=izrOLJov5y

[15] M.-H. Shih, H.-L. Chung, Y.-C. Pai, M.-H. Hsu, G.-T. Lin, S.-W. Li, and H. yi Lee, "Gsqa: An end-to-end model for generative spoken question answering," in Interspeech 2024, 2024, pp. 2970–2974.

[16] G.-T. Lin, P. G. Shivakumar, A. Gourav, Y. Gu, A. Gandhe, H. yi Lee, and I. Bulyko, “Align-slm: Textless spoken language models with reinforcement learning from ai feedback,” 2024. [Online]. Available: https://arxiv.org/abs/2411.01834

[17] G.-T. Lin, Y.-S. Chuang, H.-L. Chung, S. wen Yang, H.-J. Chen, S. A. Dong, S.-W. Li, A. Mohamed, H. yi Lee, and L. shan Lee, "DUAL: Discrete Spoken Unit Adaptive Learning for Textless Spoken Question Answering," in Proc. Interspeech 2022, 2022, pp. 5165–5169.

[18] C.-y. Huang, K.-H. Lu, S.-H. Wang, C.-Y. Hsiao, C.-Y. Kuan, H. Wu, S. Arora, K.-W. Chang, J. Shi, Y. Peng et al., "Dynamic-superb: Towards a dynamic, collaborative, and comprehensive instruction-tuning benchmark for speech," in ICASSP 2024-2024 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). IEEE, 2024, pp. 12136–12140.

[19] C.-y. Huang, W.-C. Chen, S.-w. Yang, A. T. Liu, C.-A. Li, Y.-X. Lin, W.-C. Tseng, A. Diwan, Y.-J. Shih, J. Shi et al., "Dynamic-superb phase-2: A collaboratively expanding benchmark for measuring the capabilities of spoken language models with 180 tasks," arXiv preprint arXiv:2411.05361, 2024.

[20] X. Cheng, R. Hu, X. Yang, J. Lu, D. Fu, Z. Wang, S. Ji, R. Huang, B. Zhang, T. Jin, and Z. Zhao, “Voxdialogue: Can spoken dialogue systems understand information beyond words?” in The Thirteenth International Conference on Learning Representations, 2025. [Online]. Available: https://openreview.net/forum?id=vbmSSIhKAM

[21] J. Ao, Y. Wang, X. Tian, D. Chen, J. Zhang, L. Lu, Y. Wang, H. Li, and Z. Wu, “SD-eval: A benchmark dataset for spoken dialogue understanding beyond words,” in The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track, 2024. [Online]. Available: https://openreview.net/forum?id=PnjbvbblGv

[22] Q. Yang, J. Xu, W. Liu, Y. Chu, Z. Jiang, X. Zhou, Y. Leng, Y. Lv, Z. Zhao, C. Zhou et al., “Air-bench: Benchmarking large audio-language models via generative comprehension,” arXiv preprint arXiv:2402.07729, 2024.

[23] G.-T. Lin, C.-H. Chiang, and H.-y. Lee, “Advancing large language models to capture varied speaking styles and respond properly in spoken conversations,” in Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), L.-W. Ku, A. Martins, and V. Srikumar, Eds. Bangkok, Thailand: Association for Computational Linguistics, Aug. 2024, pp. 6626–6642. [Online]. Available: https://aclanthology.org/2024.acl-long.358

[24] G.-T. Lin, P. G. Shivakumar, A. Gandhe, C.-H. H. Yang, Y. Gu, S. Ghosh, A. Stolcke, H.-Y. Lee, and I. Bulyko, “Paralinguistics-enhanced large language modeling of spoken dialogue,” in ICASSP 2024 - 2024 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP), 2024, pp. 10316–10320.

[25] G.-T. Lin and H.-y. Lee, "Can LLMs understand the implication of emphasized sentences in dialogue?" in Findings of the Association for Computational Linguistics: EMNLP 2024, Y. Al-Onaizan, M. Bansal, and Y.-N. Chen, Eds. Miami, Florida, USA: Association for Computational Linguistics, Nov. 2024, pp. 13391–13401. [Online]. Available: https://aclanthology.org/2024.findings-emnlp.782/

[26] T. A. Nguyen, E. Kharitonov, J. Copet, Y. Adi, W.-N. Hsu, A. Elkahky, P. Tomasello, R. Algayres, B. Sagot, A. Mohamed et al., “Generative spoken dialogue language modeling,” Transactions of the Association for Computational Linguistics, vol. 11, pp. 250–266, 2023.

[27] P. Wang, S. Lu, Y. Tang, S. Yan, W. Xia, and Y. Xiong, “A full-duplex speech dialogue scheme based on large language model,” in The Thirty-eighth Annual Conference on Neural Information Processing Systems, 2024. [Online]. Available: https://openreview.net/forum?id=YawXY6mWiK

[28] X. Zhang, Y. Chen, S. Hu, X. Han, Z. Xu, Y. Xu, W. Zhao, M. Sun, and Z. Liu, "Beyond the turn-based game: Enabling real-time conversations with duplex models," in Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing, Y. Al-Onaizan, M. Bansal, and Y.-N. Chen, Eds. Miami, Florida, USA: Association for Computational Linguistics, Nov. 2024, pp. 11543–11557. [Online]. Available: https://aclanthology.org/2024.emnlp-main.644/

[29] Q. Wang, Z. Meng, W. Cui, Y. Zhang, P. Wu, B. Wu, Z. Zheng, I. King, L. Chen, and P. Zhao, “Parrot: Seamless spoken dialogue interaction with double-channel large language models,” 2025. [Online]. Available: https://openreview.net/forum?id=73EDGbG6mB

[30] W. Xu, S. Wang, W. Zhao, X. Han, Y. Yan, Y. Zhang, Z. Tao, Z. Liu, and W. Che, “Enabling real-time conversations with minimal training costs,” arXiv preprint arXiv:2409.11727, 2024.

[31] W. Yu, S. Wang, X. Yang, X. Chen, X. Tian, J. Zhang, G. Sun, L. Lu, Y. Wang, and C. Zhang, "Salmonn-omni: A codec-free llm for full-duplex speech understanding and generation," arXiv preprint arXiv:2411.18138, 2024.

[32] Q. Zhang, L. Cheng, C. Deng, Q. Chen, W. Wang, S. Zheng, J. Liu, H. Yu, C. Tan, Z. Du et al., “Omniflatten: An end-to-end gpt model for seamless voice conversation,” arXiv preprint arXiv:2410.17799, 2024.

[33] L. Mai and J. Carson-Berdensen, "Real-time textless dialogue generation," arXiv preprint arXiv:2501.04877, 2025.

[34] A. A. G. Intelligence, “Amazon nova sonic: Technical report and model card,” 2025.

[35] S. Arora, Z. Lu, C.-C. Chiu, R. Pang, and S. Watanabe, “Talking turns: Benchmarking audio foundation models on turn-taking dynamics,” in The Thirteenth International Conference on Learning Representations, 2025. [Online]. Available: https://openreview.net/forum?id=2e4ECh0ikn

[36] S. wen Yang, P.-H. Chi, Y.-S. Chuang, C.-I. J. Lai, K. Lakhotia, Y. Y. Lin, A. T. Liu, J. Shi, X. Chang, G.-T. Lin, T.-H. Huang, W.-C. Tseng, K. tik Lee, D.-R. Liu, Z. Huang, S. Dong, S.-W. Li, S. Watanabe, A. Mohamed,

and H. yi Lee, “SUPERB: Speech Processing Universal PERformance Benchmark,” in Proc. Interspeech 2021, 2021, pp. 1194–1198.

[37] G.-T. Lin, C.-L. Feng, W.-P. Huang, Y. Tseng, T.-H. Lin, C.-A. Li, H.-y. Lee, and N. G. Ward, “On the utility of self-supervised models for prosody-related tasks,” in Proc. IEEE SLT, 2023, pp. 1104–1111.

[38] H.-S. Tsai, H.-J. Chang, W.-C. Huang, Z. Huang, K. Lakhotia, S.-W. Yang, S. Dong, A. Liu, C.-I. Lai, J. Shi et al., “Superb-sg: Enhanced speech processing universal performance benchmark for semantic and generative capabilities,” in Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), 2022, pp. 8479–8492.

[39] Y. Chen, X. Yue, C. Zhang, X. Gao, R. T. Tan, and H. Li, “Voicebench: Benchmarking llm-based voice assistants,” arXiv preprint arXiv:2410.17196, 2024.

[40] T. A. Nguyen, M. de Seyssel, P. Rozé, M. Rivière, E. Kharitonov, A. Baevski, E. Dunbar, and E. Dupoux, “The zero resource speech benchmark 2021: Metrics and baselines for unsupervised spoken language modeling,” in NeuRIPS Workshop on Self-Supervised Learning for Speech and Audio Processing, 2020.

[41] N. Mostafazadeh, M. Roth, A. Louis, N. Chambers, and J. Allen, "LSDSem 2017 shared task: The story cloze test," in Proceedings of the 2nd Workshop on Linking Models of Lexical, Sentential and Discourse-level Semantics, M. Roth, N. Mostafazadeh, N. Chambers, and A. Louis, Eds. Valencia, Spain: Association for Computational Linguistics, Apr. 2017, pp. 46–51. [Online]. Available: https://aclanthology.org/W17-0906

[42] N. Ward and W. Tsukahara, “Prosodic features which cue back-channel responses in english and japanese,” Journal of pragmatics, vol. 32, no. 8, pp. 1177–1207, 2000.

[43] A. Reece, G. Cooney, P. Bull, C. Chung, B. Dawson, C. Fitzpatrick, T. Glazer, D. Knox, A. Liebscher, and S. Marin, "The candor corpus: Insights from a large multimodal dataset of naturalistic conversation," Science Advances, vol. 9, no. 13, p. eadf3197, 2023.

[44] G. Jefferson, “Preliminary notes on a possible metric which provides for a ‘standard maximum’ silence of approximately one second in conversation,” Conversation: An Interdisciplinary Approach/Multilingual Matters, 1989.

[45] S. Liu, Y. Nakajima, L. Chen, S. Arndt, M. Kakizoe, M. A. Elliott, and G. B. Remijn, “How pause duration influences impressions of english speech: Comparison between native and non-native speakers,” Frontiers in psychology, vol. 13, p. 778018, 2022.

[46] M. Heldner and J. Edlund, “Pauses, gaps and overlaps in conversations,” Journal of Phonetics, vol. 38, no. 4, pp. 555–568, 2010.

[47] M. Umair, V. Sarathy, and J. Ruiter, “Large language models know what to say but not when to speak,” in Findings of the Association for Computational Linguistics: EMNLP 2024, Y. Al-Onaizan, M. Bansal, and Y.-N. Chen, Eds. Miami, Florida, USA: Association for Computational Linguistics, Nov. 2024, pp. 15503–15514. [Online]. Available: https://aclanthology.org/2024.findings-emnlp.909/

[48] OpenAI, “Gpt-4 technical report,” 2023.

[49] W.-N. Hsu, B. Bolte, Y.-H. H. Tsai, K. Lakhotia, R. Salakhutdinov, and A. Mohamed, “Hubert: Self-supervised speech representation learning by masked prediction of hidden units,” IEEE/ACM transactions on audio, speech, and language processing, vol. 29, pp. 3451–3460, 2021.

[50] C. Cieri, D. Graff, O. Kimball, D. Miller, and K. Walker, "Fisher english training speech part 1 transcripts," Philadelphia: Linguistic Data Consortium, 2004.