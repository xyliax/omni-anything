# TransRAC: Encoding Multi-scale Temporal Correlation with Transformers for Repetitive Action Counting

Huazhang Hu$^{1*}$, Sixun Dong$^{1*}$, Yiqun Zhao$^{1}$, Dongze Lian$^{1,2}$, Zhengxin Li$^{1\dagger}$, Shenghua Gao$^{1,3,4\dagger}$

$^{1}$Shanghai Tech University  $^{2}$National University of Singapore

$^{3}$Shanghai Engineering Research Center of Intelligent Vision and Imaging

$^{4}$Shanghai Engineering Research Center of Energy Efficient and Custom AI IC

{huhzh, dongsx, v-zhaoyq, liandz, lizhx, gaoshh}@shanghaitech.edu.cn

## Abstract

Counting repetitive actions are widely seen in human activities such as physical exercise. Existing methods focus on performing repetitive action counting in short videos, which is tough for dealing with longer videos in more realistic scenarios. In the data-driven era, the degradation of such generalization capability is mainly attributed to the lack of long video datasets. To complement this margin, we introduce a new large-scale repetitive action counting dataset covering a wide variety of video lengths, along with more realistic situations where action interruption or action inconsistencies occur in the video. Besides, we also provide a fine-grained annotation of the action cycles instead of just counting annotation along with a numerical value. Such a dataset contains 1,451 videos with about 20,000 annotations, which is more challenging. For repetitive action counting towards more realistic scenarios, we further propose encoding multi-scale temporal correlation with transformers that can take into account both performance and efficiency. Furthermore, with the help of fine-grained annotation of action cycles, we propose a density map regression-based method to predict the action period, which yields better performance with sufficient interpretability. Our proposed method outperforms state-of-the-art methods on all datasets and also achieves better performance on the unseen dataset without fine-tuning. The dataset and code are available $ ^{1} $.

## 1. Introduction

Planetary motion, the change of seasons, and heartbeats, these periodic movements that are everywhere in our lives. They can be modeled by the Newtonian mechanics, or detected with the aid of sensors for the understanding of the world or our bodies. In computer vision, the detection of repetitive/periodic motions also plays an important role, such as in human activity, where the counting of some physical exercise movements benefits people in fitness detection and planning. Although one can use some sensors (e.g., gravity sensors) on the human body, vision-based approaches enable non-invasive and thus make third-view-based video analysis possible and promising. Repetitive action counting in computer vision is also useful as an auxiliary cue for other human-centric video analysis applications, such as pedestrian detection [27] and 3D reconstruction [18,29].



Despite this importance, repetitive action counting methods in computer vision has rarely been explored. Previous papers [5, 39] tend to count repetitive actions in short videos, such as some simple videos grabbed from the Kinetics dataset [11]. However, these videos lack some realistic scenarios, which limits the application of the method in more realistic scenarios due to the following two points:

• Restricted video length. The previous datasets [5,17,30,39] typically contain only short videos (e.g., 0.4-30 s), however, methods are likely to be deployed to long videos in real scenarios. For instance, we count push-ups or jump-jacks with a video length of 60 s. Counting actions in such long videos is more challenging because there might exist various anomalies in real scenarios, such as the action being interrupted with internal or external reasons (Fig. 1a), or the inconsistency between action periods (Fig. 1b). These anomalies might cause the previous algorithm to fail or obtain sub-optimal performance, affecting the generalization of the algorithm to real scenarios.

 $ ^{*} $These authors contributed equally to this work.

• Inadequate annotations. In previous datasets [5, 17, 30, 39], the number of repetitive actions in a video

 $ ^{†} $Corresponding authors.

 $ ^{1} $https://svip-lab.github.io/dataset/RepCount_dataset.html

<div style="text-align: center;"><img src="imgs/img_in_image_box_98_143_575_283.jpg" alt="Image" width="38%" />

A break

</div>


<div style="text-align: center;">(a) Interruption during the actions (squats)</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_615_142_1090_288.jpg" alt="Image" width="38%" />

☐
☐
☐
☐

</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_99_316_577_468.jpg" alt="Image" width="39%" />



</div>


<div style="text-align: center;">(c) Long video with numerical cycles (60 seconds) (punch jacks)</div>


<div style="text-align: center;">(b) Inconsistent action cycles (push up)</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_611_311_1090_464.jpg" alt="Image" width="39%" />

www.ErinWischun.com
www.ErinWischunn.com
start:0.60s end:5.69s
start:8.33s end:10.71s

</div>


<div style="text-align: center;">(d) Annotations in the form of start and end of each cycle (front raise)</div>


<div style="text-align: center;">Figure 1. The features of our proposed dataset RepCount: (a) anomaly case (interruption during actions); (b) anomaly case (inconsistent action cycles); (c) long video that consists of numerical action cycles; (d) the fine-grained labeling protocol.</div>


is simply labeled as a numerical value. Although the count number serves as an ultimate predictive goal, such coarse-grained annotation deprives the interpretability of the algorithm. The model only predicts a numerical value during training or inference, which makes it difficult to evaluate the model more completely. As argued in some crowd counting papers [21,28,37,41], the total number of repetitive actions is correct, but the position of the intermediate cycles might be wrong.

In data-driven deep learning approaches, the dataset is the key to algorithmic innovation. To tackle the above problems, we collect a large-scale human-centric dataset, which is closer to the real one. As shown in Fig. 1c, there are a large number of variations in video length, while the interruptions or inconsistent action cycles occur in some videos. For more accurate performance evaluation and model interpretability, we provide a more fine-grained annotation of the action cycles, such as Fig. 1d. Further, we also collect a part containing student activity videos captured in a fully realistic scenario (in local school), which is significantly different from the previous datasets where the videos are crawled from YouTube. Fig. 2 provides an overview of our dataset. Such a dataset is more challenging and has the potential to become a new benchmark for repetitive action counting.

To perform repetitive action counting, previous methods [5] generally take a fixed number of frames for prediction. Such an approach might be reasonable in relatively short videos. For example, TSN [38] extracts three frames for action recognition of trimmed videos, where the information characterizing the action is concentrated on certain keyframes. However, for long videos in the real scenario, extracting fixed frames will result in sub-optimal performance. Since the video duration varies very much (e.g. from 4s to 88s) and if the number of selected frames is too small, high-frequency actions will be neglected. On the contrary, if too many frames are selected, it might cause a waste of computational resources. Another alternative is to sample the video with the same frequency for both long and short videos. However, some actions are very fast (e.g., jumping rope) and some are very slow (e.g., push-ups). Sampling with a fixed frequency would either lead to performance degradation or would not be efficient enough. To balance performance and efficiency, we propose a multi-scale temporal correlation encoding network with transformers that can take care of not only high and low-frequency actions but also long and short videos. This approach allows the model to automatically select its adapted scale to compute the correlation matrix for final count prediction. Furthermore, thanks to the fine-grained annotation of action cycles in our dataset (see Fig. 1d), we also propose a density map regression-based method to predict action periods, which not only yields better performance but is also more beneficial for the interpretability of the model.



We summarize our contributions in three-fold:

- We introduce a new dataset, named RepCount, which consists of 1,451 videos and about 20,000 fine-grained annotations. Such a dataset allows for a large number of video length variations and contains anomaly cases, thus is more challenging.

- A new multi-scale temporal correlation encoding network with transformers, which can take care of not only high and low frequency actions, but also long and short videos, is designed for repetitive action counting.

- The proposed method outperforms state-of-the-art methods on our proposed dataset and all other datasets. Fur

thermore, we also achieve better performance on the unseen dataset without fine-tuning.

## 2. Related Works

Temporal auto-correlation. The temporal auto-correlation function is widely used in motion recognition [3, 14, 15] and human identification [13]. Auto-correlation in time series contains periodic information [25, 36]. The most common method to represent auto-correlation is the vector inner product. Vaswani et al. [35] obtain the auto-correlation matrices by multiplying query matrices and key matrices. Panagiotakis et al. [25] implement attention mechanism for video frame series to construct the auto-correlation matrices of video frames. With auto-correlation matrices, the cycle information from time series can be found to count the number of repetitive actions.

Video feature extraction. For a long time, spatial and temporal convolution dominated the area of video feature extraction, such as C3D [34], I3D [2], P3D [26]. However, limited by the small receptive field of the convolution kernel, a convolution-based method is hard to capture the long-range dependencies on the temporal domain. ViT [4] and its variants bring a pioneering change for the Computer Vision field. However, due to the quadratic computational complexity and complex structure, training of the transformer-based model is costly [12]. Video Swin Transformer [23] is a proper backbone due to its trade-off, which was pretrained on a large dataset.

Counting in computer vision. Counting from images or videos [1, 17, 19, 20, 24, 30, 39, 40] is a very important field in Computer Vision. It has high application value in object detection [31], public transport [16] and physical exercises [32]. Zhang et al. [39] propose a context-aware and scale-insensitive framework for temporal repetition counting. [40] incorporate visual signal with corresponding sight signal to motion counting for the first time.

Density map. The application of a density map enhances the effect of crowd counting [21, 28, 37, 41]. The density map is generated from plot maps by convolving with a Gaussian kernel. The density map applies 2D planar spatial distribution to represent the spatial distribution and the local probability distribution. [41] apply 2D density maps to achieve dense crowd counting. In [33], the extracted features are passed to the density regressor to generate a density map. In many neural network architectures, it could be regarded as an intermediate representation layer. A periodic density map preserves more information and gives the spatial distribution.

Period annotation. Currently, data-driven learning methods have become an essential approach in computer vision. In the scenario of repetition counting, most datasets only label the period cycle count [5, 11, 39]. Researchers have to use generated data synthesized from real data and artificial data for training. [17] first proposed Synthetic data for the training model. However, such data are based on the assumption that the motion is continuous, uninterrupted, uniformly distributed, and with similar periods. [5] naively divided the count of periods by the number of frames to get the period length. This is far from the real motion situation. Therefore, a dataset with periodic fine-grained annotation is invaluable.



## 3. Our Proposed Dataset

Existing repetition counting datasets, mainly including Countix [5] and UCFRep [39], have been widely consumed for the evaluation of repetition counting models. In these datasets, video clips that are collected from YouTube cover a variety of perspectives, dimension sizes and action categories. Typically, the total number of repetitive actions in a video clip is labeled as its ground truth. While these datasets significantly contributed to modeling the repetition counting problem, there still exist several non-negligible limitations that increase the gap between the scenarios illustrated in the videos and realistic ones, such as i) no interruption to actions, either from internal or external; ii) only containing uniform action frequency in an individual video; iii) the lack of long-range videos; iv) coarse-grained ground truth annotation, etc. In particular, the last point hinders the development of more sophisticated models.

To overcome these limitations, we introduce a novel repetition counting dataset called RepCount that contains videos with significant variations in length and allows for multiple kinds of anomaly cases, as demonstrated in Fig. 2. These video data collaborate with fine-grained annotations that indicate the beginning and end of each action period. Furthermore, the dataset consists of two subsets namely Part-A and Part-B. The videos in Part-A are fetched from YouTube, while the others in Part-B record simulated physical examinations by junior school students and teachers. Therefore, flexible strategies of data splitting for training and evaluation could be adopted according to the specific demand. Then we introduce the data collection, annotation and statistics in detail.

Dataset collection. According to the source of data, our dataset consists of two parts. For part-A, we collected 1,041 video clips from YouTube. The type of actions includes workout activities (squatting, pulling-up, front-raising, etc.), athletic events (rowing, pommel horse, etc.) and other repetitive actions (soccer juggling). We select the video that represents at least one integral series of actions in line with human habits. Also, the videos usually contain some irrelevant actions like speaking and relaxation. For the most important, the interruption during an action series is preferable, which may result in difficulties for accurate counting. We use the open-source script YouTube

<div style="text-align: center;"><img src="imgs/img_in_image_box_99_148_1093_463.jpg" alt="Image" width="81%" />

(a) Dataset Part-A
(b) Dataset Part-B

</div>


<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Video duration (in seconds)</th><th style='text-align: center;'>Num. of videos</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>5</td><td style='text-align: center;'>25</td></tr>
    <tr><td style='text-align: center;'>10</td><td style='text-align: center;'>295</td></tr>
    <tr><td style='text-align: center;'>15</td><td style='text-align: center;'>105</td></tr>
    <tr><td style='text-align: center;'>20</td><td style='text-align: center;'>120</td></tr>
    <tr><td style='text-align: center;'>25</td><td style='text-align: center;'>140</td></tr>
    <tr><td style='text-align: center;'>30</td><td style='text-align: center;'>125</td></tr>
    <tr><td style='text-align: center;'>35</td><td style='text-align: center;'>165</td></tr>
    <tr><td style='text-align: center;'>40</td><td style='text-align: center;'>100</td></tr>
    <tr><td style='text-align: center;'>45</td><td style='text-align: center;'>90</td></tr>
    <tr><td style='text-align: center;'>50</td><td style='text-align: center;'>55</td></tr>
    <tr><td style='text-align: center;'>55</td><td style='text-align: center;'>45</td></tr>
    <tr><td style='text-align: center;'>60</td><td style='text-align: center;'>110</td></tr>
    <tr><td style='text-align: center;'>65</td><td style='text-align: center;'>5</td></tr>
    <tr><td style='text-align: center;'>70</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>75</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>80</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>85</td><td style='text-align: center;'>2</td></tr>
  </tbody>
</table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Repetition count</th><th style='text-align: center;'>Num. of videos</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>2-4</td><td style='text-align: center;'>110</td></tr>
    <tr><td style='text-align: center;'>4-6</td><td style='text-align: center;'>310</td></tr>
    <tr><td style='text-align: center;'>6-8</td><td style='text-align: center;'>180</td></tr>
    <tr><td style='text-align: center;'>8-10</td><td style='text-align: center;'>310</td></tr>
    <tr><td style='text-align: center;'>10-12</td><td style='text-align: center;'>100</td></tr>
    <tr><td style='text-align: center;'>12-14</td><td style='text-align: center;'>90</td></tr>
    <tr><td style='text-align: center;'>14-16</td><td style='text-align: center;'>70</td></tr>
    <tr><td style='text-align: center;'>16-18</td><td style='text-align: center;'>50</td></tr>
    <tr><td style='text-align: center;'>18-20</td><td style='text-align: center;'>40</td></tr>
    <tr><td style='text-align: center;'>20-22</td><td style='text-align: center;'>35</td></tr>
    <tr><td style='text-align: center;'>22-24</td><td style='text-align: center;'>30</td></tr>
    <tr><td style='text-align: center;'>24-26</td><td style='text-align: center;'>25</td></tr>
    <tr><td style='text-align: center;'>26-28</td><td style='text-align: center;'>20</td></tr>
    <tr><td style='text-align: center;'>28-30</td><td style='text-align: center;'>18</td></tr>
    <tr><td style='text-align: center;'>30-32</td><td style='text-align: center;'>15</td></tr>
    <tr><td style='text-align: center;'>32-34</td><td style='text-align: center;'>12</td></tr>
    <tr><td style='text-align: center;'>34-36</td><td style='text-align: center;'>10</td></tr>
    <tr><td style='text-align: center;'>36-38</td><td style='text-align: center;'>8</td></tr>
    <tr><td style='text-align: center;'>38-40</td><td style='text-align: center;'>6</td></tr>
    <tr><td style='text-align: center;'>40-42</td><td style='text-align: center;'>5</td></tr>
    <tr><td style='text-align: center;'>42-44</td><td style='text-align: center;'>4</td></tr>
    <tr><td style='text-align: center;'>44-46</td><td style='text-align: center;'>3</td></tr>
    <tr><td style='text-align: center;'>46-48</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>48-50</td><td style='text-align: center;'>2</td></tr>
    <tr><td style='text-align: center;'>50-52</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>52-54</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>54-56</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>56-58</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>58-60</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>60-62</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>62-64</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>64-66</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>66-68</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>68-70</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>70-72</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>72-74</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>74-76</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>76-78</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>78-80</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>80-82</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>82-84</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>84-86</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>86-88</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>88-90</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>90-92</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>92-94</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>94-96</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>96-98</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>98-100</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>100-102</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>102-104</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>104-106</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>106-108</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>108-110</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>110-112</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>112-114</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>114-116</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>116-118</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>118-120</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>120-122</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>122-124</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>124-126</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>126-128</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>128-130</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>130-132</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>132-134</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>134-136</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>136-138</td><td style='text-align: center;'>1</td></tr>
    <tr><td style='text-align: center;'>138-140</td><td style='text-align: center;'>1</td></tr>
  </tbody>
</table>

<div style="text-align: center;">(c) Data analysis</div>


<div style="text-align: center;">Figure 2. The summary of proposed benchmark RepCount: The first two columns represent the part-A and part-B respectively, the right column shows the statistics of video length and repetition count of our dataset.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2"></td><td rowspan="2">UCFRep</td><td rowspan="2">Countix</td><td colspan="3">Ours</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>part-A</td><td style='text-align: center; word-wrap: break-word;'>part-B</td><td style='text-align: center; word-wrap: break-word;'>part-A + part-B</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Sources</td><td style='text-align: center; word-wrap: break-word;'>Subset of UCF101</td><td style='text-align: center; word-wrap: break-word;'>Subset of Kinetics</td><td style='text-align: center; word-wrap: break-word;'>Youtube</td><td style='text-align: center; word-wrap: break-word;'>Local school</td><td style='text-align: center; word-wrap: break-word;'>Collected by ourselves</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Num. of videos</td><td style='text-align: center; word-wrap: break-word;'>526</td><td style='text-align: center; word-wrap: break-word;'>8757</td><td style='text-align: center; word-wrap: break-word;'>1041</td><td style='text-align: center; word-wrap: break-word;'>410</td><td style='text-align: center; word-wrap: break-word;'>1451</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Duration Avg.  $ \pm $ Std.</td><td style='text-align: center; word-wrap: break-word;'>$ 8.15 \pm 4.29 $</td><td style='text-align: center; word-wrap: break-word;'>$ 6.13 \pm 3.08 $</td><td style='text-align: center; word-wrap: break-word;'>$ 30.67 \pm 17.54 $</td><td style='text-align: center; word-wrap: break-word;'>$ 28.53 \pm 16.06 $</td><td style='text-align: center; word-wrap: break-word;'>$ 29.359 \pm 16.02 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Duration Min./Max</td><td style='text-align: center; word-wrap: break-word;'>$ 2.08/33.84 $</td><td style='text-align: center; word-wrap: break-word;'>$ 0.2/10.0 $</td><td style='text-align: center; word-wrap: break-word;'>4.0/88.0</td><td style='text-align: center; word-wrap: break-word;'>5.56/79.16</td><td style='text-align: center; word-wrap: break-word;'>4.0/88.0</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Count Avg.  $ \pm $ Std.</td><td style='text-align: center; word-wrap: break-word;'>6.66</td><td style='text-align: center; word-wrap: break-word;'>$ 6.84 \pm 6.76 $</td><td style='text-align: center; word-wrap: break-word;'>$ 14.99 \pm 14.70 $</td><td style='text-align: center; word-wrap: break-word;'>$ 9.27 \pm 4.36 $</td><td style='text-align: center; word-wrap: break-word;'>$ 15.932 \pm 15.65 $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Count Min./ Max</td><td style='text-align: center; word-wrap: break-word;'>3/54</td><td style='text-align: center; word-wrap: break-word;'>2/73</td><td style='text-align: center; word-wrap: break-word;'>1/141</td><td style='text-align: center; word-wrap: break-word;'>1/32</td><td style='text-align: center; word-wrap: break-word;'>1/141</td></tr></table>

<div style="text-align: center;">Table 1. Dataset statistic of Countix [5], UCFRep [39] and the proposed RepCount. Our dataset is larger than the previous datasets in terms of average duration and average annotations.</div>


download $ ^{2} $ to download the videos and edit them to keep only useful clips. The length of each video clip is 20-40 seconds in major. For part B, we record the videos of exercises such as sitting- and pulling-up done by volunteers.

Dataset annotation. The existing repetition counting datasets simplify the problem by assuming that the actions are periodically uniform and not interrupted by irrelevant situations. Thus they have only coarse-grained annotations in the form of a single-valued total [5] or two timestamps that indicate the start and end time of the whole action [39]. Our protocol for fine-grained annotation is as follows: i) each individual video is assigned to two volunteers; ii) start and end time of every action cycle are labeled; iii) the annotations are cross-validated by comparing that from two volunteers, which should be inspected and revised if they differ more than 1 in total. Following the protocol, each movement cycle is precisely positioned on the time axis, which enables the design and training for models with better interpretability.

Dataset statistics. The summary of our dataset is shown in Tab. 1. In brief, we provide 1,451 videos collaborated with 19,280 annotations. The videos from our dataset have an average length of 39.359 seconds, which is 4-5 times the length of videos from other datasets. Each video clip in our dataset contains 15.932 action cycles in average, while that is 6.66 for UCFRep and 6.84 for Countix. Furthermore, part-B is constructed for the validation of model generalization. The graphical statistics is shown in the right part of Fig. 2. Our dataset is featured with more realistic scenarios and fine-grained annotations.



## 4. TransRAC Model

Given a long-duration video that has more than 15 repetitive activities happening in the content, our goal is to count the number of repetitive actions. To achieve this, we propose the model called TransRAC that contains three stages: the encoder, temporal correlation, and period predictor. The video subsequences V are fed into the encoder, then the output X is used to calculate the correlation matrix C by  $ C = \phi(X) $. At last, using period predictor  $ D = \tau(C) $ predict the final output density map.

 $ ^{2} $https://ytdl-org.github.io/youtube-dl/index.html

<div style="text-align: center;"><img src="imgs/img_in_image_box_103_156_1091_484.jpg" alt="Image" width="80%" />

 $ 64 \times 4 \times H \times W $

</div>


<div style="text-align: center;">Figure 3. TransRAC architecture. We used three sliding windows with step sizes 1, 2, and 4 to generate the video sequence with an overlap: red, orange, and yellow. Then extract features from multi-scale video sequences by the encoder. Calculate the correlation matrix in three scales, respectively. After concatenating three correlation matrices into one, make it throughout the remaining network and output the final density map.</div>


### 4.1. Encoder

As shown in Fig. 3, the encoder is  $ X = \phi(V) $. In order to explain the function  $ \phi $, firstly, assuming that we have a sequence of  $ N $ frames  $ F = [f_1, f_2, \ldots, f_N] $. we extract the three scale video subsequence  $ V $ from the original as the input of  $ \phi $. Then we feed the video sequence  $ V $ into the encoder  $ \phi $ to produce multi-scale embeddings  $ X = [X_1, X_4, X_8]^T $, where  $ X_1 = [x_1^1, x_1^2, \ldots, x_1^N]^T $.  $ X_4 $ and  $ X_8 $ are similar to  $ X_1 $.

Video sequences of multi-scale. We extract three scale subsequences from the video: single-frame, 4-frames, and 8 frames indicating the video subsequence of multi-scale (V) in Fig. 3. As Eq. (1),  $ V_1 $,  $ V_4 $,  $ V_8 $ indicates the element length of the V. In the video sampling, we use a sliding window with a step size of 2 to obtain  $ V_4 $ and a step size of 4 to get  $ V_8 $. And we also need to pad the video to ensure the same temporal dimension of output three scale sequences.

 $$ \left\{\begin{array}{c}V_{1}=\{\{f_{1}\};\{f_{2}\};\cdots\}\\ V_{4}=\{\{f_{1},\ldots,f_{4}\};\{f_{3},\ldots,f_{6}\};\cdots\}\\ V_{8}=\{\{f_{1},\ldots,f_{8}\};\{f_{5},\ldots,f_{12}\};\cdots\}\end{array}\right. $$ 

Spatio-temporal features. The video swin transformer [23] is used to extract 3d features from individual video subsequences of different scales. It can easily capture the long-range dependencies using the self-attention mechanism; at the same time, with the hierarchical design, it can also capture the local dependencies, which is more suitable for the image.

Let video subsequence  $ V_i $, where  $ i \in \{1, 4, 8\} $, pass through the feature extraction block to extract the features. Three kinds of video clips with different scales can match different period lengths (e.g. jump jacks and squat) better. The resulting features of each scale are of size  $ 7 \times 7 \times t \times 768 $, where the  $ t $ is equal to a 2-fold compression in the temporal dimension. Then all these feature were concatenated in temporal dimension as a feature block.



Temporal context. To take into account more temporal context, we apply a layer of 3D convolution after the feature extractor, which has  $ 3 \times 3 \times 512 $ filters with ReLU activation. After that, we use a Global 3D Max-pooling layer over the spatial dimensions to reduce model parameters and obtain the final result X of encoder  $ \phi $ as the embeddings in Fig. 3. The above operations are carried on different scale video subsequences to the extent that we can obtain more information on the time domain.

### 4.2. Temporal correlation and Self-attention

The correlation of embeddings can be expressed as $C_i = \Psi(X_i)$. We need to compute every correlation $c_p^i$ between $x_p^i$ embeddings with other $x_p^j$, where $j \in \{1,2,\ldots,N\}$ and $j \neq i$, such that we can use the embedding $X_p$ to obtain the correlation matrix $C_p = [c_p^1, c_p^2, \ldots, c_p^H]^T$, $p \in \{1,4,8\}$ and $H$ is the number of attention-head.

Correlation matrix. For the temporal locations of the activities, we use transformers [35] with correlation-matrix and self-attention mechanism to encode multi-scale temporal correlation layers. After encoder the video sequences, we can get embeddings  $ X_i $ for each scale  $ V_i $, where  $ i \in 1, 4, 8 $. And the shape of all embeddings for every scale is  $ 64 \times 512 $ as Fig. 3. Then We use the self-attention mechanism to calculate the correlation matrix. One scale embeddings  $ X_i $ is multiplied with two matrices of weights for obtaining keys matrix called  $ K $ and query matrix called  $ Q $. Then we could use  $ K $ and  $ Q $ to calculate attention scores,

which should be called correlation in this paper.

Self-attention. We construct the correlation matrix C by  $ C = f(Q, K) $, where  $ f(\cdot) $ is known as dot product attention. And as Fig. 3 showed, these are two more important points that We use 4-heads with 512 dimensions (not eight heads which is more usual [35]) and multi-scale embeddings to calculate the correlation. Therefore, after the self-attention layer, concatenating three scales' features into one, we could get the shape of output is  $ [N, N, M \times H] $. M means how many scales we have. H and N are the numbers of heads and input frames independently. Furthermore in details, N, M and H in TransRAC are 64, 3 and 4, respectively.

### 4.3. Period Predictor

In Fig. 3, $D = \tau(C)$ shows feed $C$, where $C$ is concatenated from $C_1$, $C_2$ and $C_3$, to the density map predictor which outputs none element for each video subsequence: the value of density the $D = [d_1, d_2, \ldots, d_N]$ represents the distribution of period. A more detailed version can be seen in Fig. 3.

Density map. The most straightforward advantage of the approach of density map is that it has a strong ability for explanation.. Therefore, We use the density map predicto as our period predictor. The density map contains the global information of the entire video. Each row of the density map indicates the frame's position in the local cycle and the distribution of the frame in the global video. We also compared density map regressor with classifiers in ablation experiments and found density maps performed. And more details for comparisons between the two predictors can be seen in Sec. 5. For more implementation details can be seen in the supplementary material.

### 4.4. Losses

Our dataset, RepCount, is annotated with each position of each motion period in the temporal dimension. Pass those labels through the Gaussian function  $ G(x) $ to get the ground truth. The process of Gaussianization can be seen in the supplementary material. Therefore, using MSE (Mean Squared Error) as the loss function tends to be a good choice.

### 4.5. Inference

To compare the network’s performance purely from an academic view, we have not taken any measures to improve the prediction accuracy which is used in previous work [5]. The way to infer the counting of repetitions has the following operations:

Sample video. For a video with any length of fewer than two minutes, we directly sample 64 frames. If the input video has less than 64 frames, we will implement padding in the temporal domain.

Calculating. These frames are input into the model to obtain the prediction results of density map  $ D = [d_1, d_2, \ldots, d_N] $. Applying a linear sum to obtain the predicted value  $ \hat{p} $ of the number of action periods, where  $ d_i $ means the value of density map.



## 5. Experiments

There are five central parts in this section. First of all, we explain some existing benchmarks and the evaluation matrices used in popular repetition counting. Secondly, We illustrate the advantages and capabilities of fine-grained annotations in detail. By visualizing and comparing the predictions for different sports, we propose conjectures and solutions. Then we evaluate our model performance and compare it to other methods, which were trained on our dataset RepCount, on the existing benchmarks. At last, we make an ablation study to justify our model design.

### 5.1. Benchmarks and Evaluation Matrices

We evaluate our method on the four video datasets: our test set of RepCount part-A, ours RepCount part-B and UCF Rep [39]. As illustrated in Tab. 1, Ours (part-A+part-B) contains videos with more count and longer duration than all existing datasets. The previous work [5,39] mainly uses two matrices for evaluating repetition counting in videos: Off-By-One (OBO) count error. If the predicted count is within one count of the ground truth, we can consider this video are counted correctly. Otherwise, it is a situation of counting error. It represents the error rate of repetition count over the entire dataset.

Mean Absolute Error. This metric means normalized absolute error between the ground truth count and the predicted count. OBO and MAE are defined as follows:

 $$ \mathrm{O B O}=\frac{1}{N}\sum_{i=1}^{N}[\left|\widetilde{c}_{i}-c_{i}\right|\leq1], $$ 

 $$ \mathrm{MAE}=\frac{1}{N}\sum_{i=1}^{N}\frac{\left|\widetilde{c}_{i}-c_{i}\right|}{\widetilde{c}_{i}}, $$ 

where  $ \widetilde{c} $ is the ground truth repetition counts. N is the number of given videos.

### 5.2. Implementation Details

We implement our method with PyTorch. The encoder, Video Swin Transformer tiny [23], was pre-trained on the Kinetics400. Using three columns to obtain input video sequences and feeding them into the encoder. Then we apply 2D convolution to fuse multi-scaled correlation matrix. The hidden layer dimension of transformer-based period predictor is 512. Limited by the memory of GPU, the parameters of the pre-trained encoder were frozen during the training

process. We train our remaining layers of the model for 16K steps with a declining learning rate of  $ 8 \times 10^{-6} $ and optimized by the Adam optimizer using a batch size of 16. Additional details are provided on the code.

### 5.3. Fine-grained Annotation

Observing from the Fig. 4, it is easy to find accurate periodic location information on the ground truth, which is essential for accurately counting. As each kind of action has different characteristics, some activities, such as bench press, will be completed speed rate highly, due to the excellent energy of people at the beginning. However, at the end of the action, the rate will slow down. On the other hand, the period length of specific actions can be more uniform. As the examples of Fig. 4 shown, "front-raise" is easier for the man to finish in a stable period. It is because we annotated the data in a more fine-grained way, by which we can get the locations of all kinds of actions from our dataset, we have the opportunity to fine-tune the structure of the model for different needs. Of course, there is no chance to set the density map as a predictor of our model without fine-grained annotations. Overall, a more fine-grained annotation is necessary to precisely help the model count the number of periods.

<div style="text-align: center;"><img src="imgs/img_in_image_box_102_747_557_997.jpg" alt="Image" width="37%" />

Ground
Truth
Prediction
Ground
Truth
Prediction

</div>


<div style="text-align: center;">Figure 4. Visualization of density map. Here are comparisons between the ground truth and prediction result from our model. We can see from the first pair that the duration of videos in our dataset varies.</div>


### 5.4. Evaluation and Comparison

We evaluate the effectiveness of the model from multiple aspects. When we compare the TransRAC proposed with RepNet on RepCount (Part-A and Part-B) and UCFRep datasets, for a fair comparison, we modify the last fully-connection layer of RepNet [5] to make it capable of handling those videos containing more than 32 action periods. Unless otherwise specified, we train the networks on RepCount Part-A and validate them on the test set of Part-A, obtaining the results shown in Tab. 2. In addition, we compare some SOTA action recognition methods [6,7,23] and change output layers accordingly to adapt to our task. Farther more, we also compare the SOTA method [10] in the action segmentation field. More detail can be seen in the supplementary materials. One can observe that TransRAC, our model outperforms them by a notable margin on all the considered datasets.



Generalization. From Tab. 3, it also can be seen that the TransRAC model generalizes well on multiple datasets.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>X3D [7]</td><td style='text-align: center; word-wrap: break-word;'>0.9105</td><td style='text-align: center; word-wrap: break-word;'>0.1059</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TANet [6]</td><td style='text-align: center; word-wrap: break-word;'>0.6624</td><td style='text-align: center; word-wrap: break-word;'>0.0993</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Video SwinT [23]</td><td style='text-align: center; word-wrap: break-word;'>0.5756</td><td style='text-align: center; word-wrap: break-word;'>0.1324</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Huang et al. [10]</td><td style='text-align: center; word-wrap: break-word;'>0.5267</td><td style='text-align: center; word-wrap: break-word;'>0.1589</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RepNet [5]</td><td style='text-align: center; word-wrap: break-word;'>0.9950</td><td style='text-align: center; word-wrap: break-word;'>0.0134</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Zhang et al. [39]</td><td style='text-align: center; word-wrap: break-word;'>0.8786</td><td style='text-align: center; word-wrap: break-word;'>0.1554</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>0.4431</td><td style='text-align: center; word-wrap: break-word;'>0.2913</td></tr></table>

<div style="text-align: center;">Table 2. Performance of different methods on RepCount part-A test when trained on the same train set of RepCount.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount B</td><td colspan="2">UCFRep</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>MAE  $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>MAE  $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>RepNet [5]</td><td style='text-align: center; word-wrap: break-word;'>0.9994</td><td style='text-align: center; word-wrap: break-word;'>0.0025</td><td style='text-align: center; word-wrap: break-word;'>0.9985</td><td style='text-align: center; word-wrap: break-word;'>0.009</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>0.7839</td><td style='text-align: center; word-wrap: break-word;'>0.091</td><td style='text-align: center; word-wrap: break-word;'>0.6401</td><td style='text-align: center; word-wrap: break-word;'>0.324</td></tr></table>

<div style="text-align: center;">Table 3. Performance of different methods on RepCount part-B and UCFRep when trained on the same train set of RepCount part-A.</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_622_898_1090_1172.jpg" alt="Image" width="38%" />

Ground Truth Prediction
Ground Truth Prediction

</div>


<div style="text-align: center;">Figure 5. Visualization of bad cases. Here are results of two bad cases our model predicted. In the first case, another people is moving</div>


While our TransRAC performs well on the major part of the data, there still are some failure cases, as Fig. 5 shown. For the top one in Fig. 5, we achieve a bad predicted result because there is more than one person moving in the video. The failure case on the bottom indicates that the frame extracting strategy could diminish the performance.

of our model in some extreme situations. It can be seen that there is an apparent difference between the predicted density map and the ground truth, especially in the left part. As this sample video has a total number of frames of 772, most of the actions concentrate in the first 400 frames, neither the ground truth density map nor the output of our model is capable of handling such imbalance.

### 5.5. Ablation Studies

We perform several ablations to justify the decisions made while designing TransRAC. We train our model on a train set of part-A and then evaluate the model on the test set of part-A. More ablation experiments can be seen in the supplementary material.

Correlation matrix. In Tab. 4, We compare the impact of applying different correlation matrix to our model. Temporal self-similarity matrix (TSM) [5] applies squared euclidean distance as the similarity function. But we found using the self-attention mechanism to calculate the correlation matrix is better. Since the experiment illustrates the self-attention mechanism could substantially improve the performance of our model, our model uses the self-attention mechanism.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Correlation matrix</td><td style='text-align: center; word-wrap: break-word;'>MAE  $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>TSM</td><td style='text-align: center; word-wrap: break-word;'>0.5678</td><td style='text-align: center; word-wrap: break-word;'>0.2251</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Self-attention (Ours)</td><td style='text-align: center; word-wrap: break-word;'>0.4431</td><td style='text-align: center; word-wrap: break-word;'>0.2913</td></tr></table>

<div style="text-align: center;">Table 4. Result of our model applying different correlation matrix when trained on training set of RepCount part-A.</div>


Density map. We build four models to verify the effectiveness of the density map, as shown in the first four rows of Tab. 5. We could conclude that using density map regressor as the period predictor is significantly better than original classifiers. As shown in the third and the four rows of Tab. 5, if we replace the classifiers with density map regressor, RepNet's performance has been significantly improved. The comparison result indicates that the Density map is more suitable for repetitive action counting.

Multi-scale. In Tab. 5, we compare the impact of applying different scales. We find that the multi-scale model performs better than the single-scale model when the number of frames is equal. The experiment demonstrates that more temporal features at different scales can obtain more period information. It is evident that multi-scale fused method brings a considerable benefit for model.

## 6. Conclusion

In this paper, considering the tough problems of existing methods in dealing with long videos in more realistic scenarios, we propose a new large-scale repetitive ac-


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ResNet [9] + CLS</td><td style='text-align: center; word-wrap: break-word;'>0.9950</td><td style='text-align: center; word-wrap: break-word;'>0.0134</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ResNet [9] + DM</td><td style='text-align: center; word-wrap: break-word;'>0.6905</td><td style='text-align: center; word-wrap: break-word;'>0.0811</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SwinT [22] + CLS</td><td style='text-align: center; word-wrap: break-word;'>0.7027</td><td style='text-align: center; word-wrap: break-word;'>0.118</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>SwinT [22] + DM</td><td style='text-align: center; word-wrap: break-word;'>0.6781</td><td style='text-align: center; word-wrap: break-word;'>0.138</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours (Scale-1)</td><td style='text-align: center; word-wrap: break-word;'>0.6595</td><td style='text-align: center; word-wrap: break-word;'>0.1854</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours (Scale-4)</td><td style='text-align: center; word-wrap: break-word;'>0.5434</td><td style='text-align: center; word-wrap: break-word;'>0.2649</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours (Scale-8)</td><td style='text-align: center; word-wrap: break-word;'>0.6657</td><td style='text-align: center; word-wrap: break-word;'>0.192</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours (Multi)</td><td style='text-align: center; word-wrap: break-word;'>0.4431</td><td style='text-align: center; word-wrap: break-word;'>0.2913</td></tr></table>

<div style="text-align: center;">Table 5. The result of ablation study when models trained on RepCount part-A. ResNet+CLS indicates the original structure of RepNet [5]. ResNet + DM indicates replacing the last layers with the density map regressor. The same applies to swinT which indicates swin-transformer. Ours (Scale-X) indicates the single column without multi-scale correlation, where X represent  $ V_{1} $,  $ V_{2} $, and  $ V_{3} $. Ours (Multi) indicates our proposed structure.</div>


tion counting dataset. Such a dataset covers a wide variety of video lengths where action interruption or action inconsistencies situations occur in the video, this is more realistic. For model interpretability and more accurate evaluation, we further provide fine-grained annotation. The overall dataset contains 1,451 videos with about 20,000 annotations, which is more challenging and has the potential to be a new benchmark. To balance the performance and efficiency, we propose to encode multi-scale temporal correlation with a transformer to tackle the repetitive action counting problems in realistic scenarios. We also propose a density map regression-based method to predict the action period, which yields better performance with sufficient interpretability. Extensive experiments show that our method achieves state-of-the-art results on all datasets and also achieves better performance on the unseen dataset without fine-tuning.

Broader Impact and Limitations. The proposed dataset is about the counting of repetitive actions, which means videos from our dataset are human-centric. The abuse of our dataset may cause privacy leaks. The usage of our dataset is limited to academic research. The proposed method predicts results based on the dataset, which may include some negative social impacts. Thus, the results conducted by our method may reflect the bias from the dataset. Other technical limitations are talked about in the Sec. 5.

Acknowledgements. The work was supported by National Key R&D Program of China (2018AAA0100704), NSFC #61932020, #62172279, Science and Technology Commission of Shanghai Municipality (Grant No. 20ZR1436000), and “Shuguang Program” supported by Shanghai Education Development Foundation and Shanghai Municipal Education Commission.

## References

[1] Carlos Arteta, Victor Lempitsky, and Andrew Zisserman. Counting in the wild. In European Conference on Computer Vision, 2016. 3

[2] Joao Carreira and Andrew Zisserman. Quo vadis, action recognition? a new model and the kinetics dataset. In proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pages 6299–6308, 2017. 3

[3] Chen Chen, Baochang Zhang, Zhenjie Hou, Junjun Jiang, Mengyuan Liu, and Yun Yang. Action recognition from depth sequences using weighted fusion of 2d and 3d autocorrelation of gradients features. Multimedia Tools and Applications, 76(3):4651–4669, 2017. 3

[4] Alexey Dosovitskiy, Lucas Beyer, Alexander Kolesnikov, Dirk Weissenborn, Xiaohua Zhai, Thomas Unterthiner, Mostafa Dehghani, Matthias Minderer, Georg Heigold, Sylvain Gelly, et al. An image is worth 16x16 words: Transformers for image recognition at scale. arXiv preprint arXiv:2010.11929, 2020. 3

[5] Debidatta Dwibedi, Yusuf Aytar, Jonathan Tompson, Pierre Sermanet, and Andrew Zisserman. Counting out time: Class agnostic video repetition counting in the wild. In IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), June 2020. 1, 2, 3, 4, 6, 7, 8

[6] Zhaoyang Liu et al. Tam: Temporal adaptive module for video recognition. In ICCV, 2021. 7

[7] Christoph Feichtenhofer. X3d: Expanding architectures for efficient video recognition. In CVPR, 2020. 7

[8] Hongwei Guo. A simple algorithm for fitting a gaussian function [dsp tips and tricks]. IEEE Signal Processing Magazine, 28(5):134–137, 2011. 2

[9] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), June 2016. 8

[10] Yifei Huang, Yusuke Sugano, and Yoichi Sato. Improving action segmentation via graph-based temporal reasoning. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 14024–14034, 2020. 7, 3

[11] Will Kay, Joao Carreira, Karen Simonyan, Brian Zhang, Chloe Hillier, Sudheendra Vijayanarasimhan, Fabio Viola, Tim Green, Trevor Back, Paul Natsev, et al. The kinetics human action video dataset. arXiv preprint arXiv:1705.06950, 2017. 1, 3

[12] Nikita Kitaev, Lukasz Kaiser, and Anselm Levskaya. Reformer: The efficient transformer, 2020. 3

[13] Takumi Kobayashi and Nobuyuki Otsu. A three-way autocorrelation based approach to human identification by gait. In IEEE Workshop on Visual Surveillance, volume 1, page 4. Citeseer, 2006. 3

[14] Takumi Kobayashi and Nobuyuki Otsu. Three-way autocorrelation approach to motion recognition. Pattern Recognition Letters, 30(3):212–221, 2009. 3

[15] Takumi Kobayashi and Nobuyuki Otsu. Motion recognition using local auto-correlation of space-time gradients. Pattern Recognition Letters, 33(9):1188–1195, 2012. 3

[16] Paulius Lengvenis, Rimvydas Simutis, Vygandas Vaitkus, and Rytis Maskeliūnas. Application of computer vision systems for passenger counting in public transport. Elektronika ir Elektrotechnika, 19(3):69–72, 2013. 3

[17] Ofir Levy and Lior Wolf. Live repetition counting. In Proceedings of the IEEE International Conference on Computer Vision (ICCV), December 2015. 1, 3

[18] Xiu Li, Hongdong Li, Hanbyul Joo, Yebin Liu, and Yaser Sheikh. Structure from recurrent motion: From rigidity to recurrence. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), June 2018. 1

[19] Dongze Lian, Xianing Chen, Jing Li, Weixin Luo, and Shenghua Gao. Locating and counting heads in crowds with a depth prior. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2021. 3

[20] Dongze Lian, Jing Li, Jia Zheng, Weixin Luo, and Shenghua Gao. Density map regression guided detection network for rgb-d crowd counting and localization. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 1821–1830, 2019. 3

[21] Weizhe Liu, Mathieu Salzmann, and Pascal Fua. Context-aware crowd counting. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 5099–5108, 2019. 2, 3

[22] Ze Liu, Yutong Lin, Yue Cao, Han Hu, Yixuan Wei, Zheng Zhang, Stephen Lin, and Baining Guo. Swin transformer: Hierarchical vision transformer using shifted windows. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), pages 10012–10022, October 2021. 8

[23] Ze Liu, Jia Ning, Yue Cao, Yixuan Wei, Zheng Zhang, Stephen Lin, and Han Hu. Video swin transformer. arXiv preprint arXiv:2106.13230, 2021. 3, 5, 6, 7

[24] Erika Lu, Weidi Xie, and Andrew Zisserman. Class-agnostic counting. In Asian conference on computer vision, pages 669–684. Springer, 2018. 3

[25] Costas Panagiotakis, Giorgos Karvounas, and Antonis Argyros. Unsupervised detection of periodic segments in videos. In 2018 25th IEEE International Conference on Image Processing (ICIP), pages 923–927. IEEE, 2018. 3

[26] Zhaofan Qiu, Ting Yao, and Tao Mei. Learning spatiotemporal representation with pseudo-3d residual networks. In proceedings of the IEEE International Conference on Computer Vision, pages 5533–5541, 2017. 3

[27] Yang Ran, Isaac Weiss, Qinfen Zheng, and Larry S. Davis. Pedestrian detection via periodic motion analysis. Int. J. Comput. Vis., 71(2):143–160, 2007. 1

[28] Viresh Ranjan, Hieu Le, and Minh Hoai. Iterative crowd counting. In Proceedings of the European Conference on Computer Vision (ECCV), September 2018. 2, 3

[29] Evan Ribnick, Nikos Papanikolopoulos, Evan Ribnick, and Nikolaos Papanikolopoulos. 3d reconstruction of periodic motion from a single view.

[30] Tom F. H. Runia, Cees G. M. Snoek, and Arnold W. M. Smeulders. Real-world repetition estimation by div, grad and curl. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), June 2018. 1, 3

[31] Nilakorn Seenouvong, Ukrit Watchareeruetai, Chaiwat Nuthong, Khamphong Khongsomboon, and Noboru Ohnishi. A computer vision based vehicle detection and counting system. In 2016 8th International Conference on Knowledge and Smart Technology (KST), pages 224–227. IEEE, 2016. 3

[32] Andrea Soro, Gino Brunner, Simon Tanner, and Roger Wattenhofer. Recognition and repetition counting for complex physical exercises with deep learning. Sensors, 19(3):714, 2019. 3

[33] Xin Tan, Chun Tao, Tongwei Ren, Jinhui Tang, and Gangshan Wu. Crowd counting via multi-layer regression. In Proceedings of the 27th ACM International Conference on Multimedia, pages 1907–1915, 2019. 3

[34] Du Tran, Lubomir Bourdev, Rob Fergus, Lorenzo Torresani, and Manohar Paluri. Learning spatiotemporal features with 3d convolutional networks. In Proceedings of the IEEE international conference on computer vision, pages 4489–4497, 2015. 3

[35] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. In Advances in neural information processing systems, pages 5998–6008, 2017. 3, 5, 6

[36] Michail Vlachos, Philip Yu, and Vittorio Castelli. On periodicity detection and structural periodic similarity. In Proceedings of the 2005 SIAM international conference on data mining, pages 449–460. SIAM, 2005. 3

[37] Jia Wan and Antoni Chan. Adaptive density map generation for crowd counting. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), October 2019. 2, 3

[38] Limin Wang, Yuanjun Xiong, Zhe Wang, Yu Qiao, Dahua Lin, Xiaoou Tang, and Luc Val Gool. Temporal segment networks: Towards good practices for deep action recognition. In ECCV, 2016. 2

[39] Huaidong Zhang, Xuemiao Xu, Guoqiang Han, and Shengfeng He. Context-aware and scale-insensitive temporal repetition counting. In IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), June 2020. 1, 3, 4, 6, 7

[40] Yunhua Zhang, Ling Shao, and Cees G. M. Snoek. Repetitive activity counting by sight and sound. CoRR, abs/2103.13096, 2021. 3

[41] Yingying Zhang, Desen Zhou, Siqin Chen, Shenghua Gao, and Yi Ma. Single-image crowd counting via multi-column convolutional neural network. In 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pages 589–597, 2016. 2, 3

# Encoding Multi-scale Temporal Correlation with Transformers for Repetitive Action Counting

Supplementary Material

### A. Extra experiments

### A.1. Density map

Gaussianization. Assuming we have the label as $Y = [y_1, y_2, \ldots, y_n]$. A pair of $y_i$ and $y_j$ represents the frames at the beginning and end of a repetition action where $j = i+1$. To calculate the Gaussian function [8] with 99% confidence interval shown below, we need to figure out the mean $\mu$ and the variance $\sigma$. Because of 99% confidence interval meaning $\mu \pm 3\sigma$, we could get $\mu$ and $\sigma$ by $y_{i,j} = \mu \pm 3\sigma$, where $i$ and $j$ is the pair of the frames.

Therefore, through the Gaussian function  $ g_\sigma(x) $, we can get the probability density distribution  $ G_\sigma(y) $ from  $ y_i $ to  $ y_j $. Then  $ d_k $ can take the integral by Eq. (4). At last, we could get the predict results of density map  $ D = [d_1, d_2, \ldots, d_n] $.

 $$ d_{k}=\int_{y_{k}-0.5}^{y_{k}+0.5}G_{\sigma}(y)d y,\quad k\in[i,j] $$ 

To compare different generate methods of density map, We adjust the mean  $ \mu $ of the Gaussian function to the beginning frame of one period or the ending and retrain the model which has a merging density map predictor. Then we obtain the output of different positions by adjusting the weight of predict density maps.


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Generate density map</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Begin</td><td style='text-align: center; word-wrap: break-word;'>0.5295</td><td style='text-align: center; word-wrap: break-word;'>0.2052</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Mid</td><td style='text-align: center; word-wrap: break-word;'>0.4936</td><td style='text-align: center; word-wrap: break-word;'>0.2052</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>End</td><td style='text-align: center; word-wrap: break-word;'>0.5192</td><td style='text-align: center; word-wrap: break-word;'>0.192</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Merge</td><td style='text-align: center; word-wrap: break-word;'>0.5142</td><td style='text-align: center; word-wrap: break-word;'>0.2009</td></tr></table>

<div style="text-align: center;">Table 6. The density maps with different mean $\mu$ of the Gaussian function $G$. Begin is means the density map generated with $G$, where the $\mu$ is the beginning frame. Similarly, End represents the $\mu$ is the ending frame. Mid is as same as our model TranRAC.</div>


The result as the Tab. 6 shown, Merging density maps does not give the models better performance. Because the amount of video frames is 64, moving  $ \mu $ to begin or end will lose the information of the first period or the last. The density map generated by the mean in the mid-frame has the best effort.

### A.2. Sample rate

We conducted the experiment to verify the impact of adding the number of video frames. Due to our model based on the density map, we use a one-dimensional spatial distribution to represent the distribution of periods in time.




<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours(single)-64</td><td style='text-align: center; word-wrap: break-word;'>0.6595</td><td style='text-align: center; word-wrap: break-word;'>0.185</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours(single)-128</td><td style='text-align: center; word-wrap: break-word;'>0.6191</td><td style='text-align: center; word-wrap: break-word;'>0.191</td></tr></table>

<div style="text-align: center;">Table 7. Experiment results of model with different sample rate when trained on train set of RepCount part-A. 64 and 128 indicate different frame sample number from initial videos.</div>


Experimental results show that increasing video frames can improve the performance of density maps to a certain extent (see Tab. 7). A better result in terms of MAE error is achieved when we select 128 frames of a video.

### A.3. Scale ablation

We verify the effect of different scales by building tree pipelines, where the input of Encoder  $ \phi $ with distinct length video subsequences. As shown in the one to three rows of Tab. 10, because the different temporal scales of video subsequence extract information in their scale, they have different performances of repetition counting. Concatenating the multi-scale video sequences contributes to capturing different period length actions and brings the model greater robustness.

### A.4. Receptive field

Usually, a more large video subsequence of scale has a more substantial receptive field. And considering the more large sample rate will extract more video information, we compared the different video subsequences of scale at different sample rates.

As Tab. 11 indicated, when the sample rate is the little one, 64 frames extracted from one original video, single-frame is as similar as 8-frames. But increasing the sample rate to 128, The performance of 8-frames is far better than that of single-frames.

We believe that there is an optimal scale of video subsequence for the same dataset under the same sampling rate. Due to the operation of sampling video to the fixed number of frames, the duration of per repetitive action will be shorter with the decrease of the sample rate. Large-scale video sequences will lose their advantages when the sample rate is 64 frames per video because of the shorter duration. But when the sampling rate increases to 128, there


<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Division</td><td colspan="2">Regular setting</td><td colspan="2">Open-set setting</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Num. of videos</td><td style='text-align: center; word-wrap: break-word;'>Total frames</td><td style='text-align: center; word-wrap: break-word;'>Num. of videos</td><td style='text-align: center; word-wrap: break-word;'>Total frames</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Train</td><td style='text-align: center; word-wrap: break-word;'>758</td><td style='text-align: center; word-wrap: break-word;'>637,545</td><td style='text-align: center; word-wrap: break-word;'>655</td><td style='text-align: center; word-wrap: break-word;'>560,402</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>val</td><td style='text-align: center; word-wrap: break-word;'>131</td><td style='text-align: center; word-wrap: break-word;'>109,854</td><td style='text-align: center; word-wrap: break-word;'>130</td><td style='text-align: center; word-wrap: break-word;'>77,103</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>test</td><td style='text-align: center; word-wrap: break-word;'>152</td><td style='text-align: center; word-wrap: break-word;'>129,993</td><td style='text-align: center; word-wrap: break-word;'>256</td><td style='text-align: center; word-wrap: break-word;'>239,887</td></tr></table>

<div style="text-align: center;">Table 8. Regular setting and Open-setting of RepCount partA</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">Method</td><td colspan="2">regular setting</td><td colspan="2">Open-set setting</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO $ \uparrow $</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Huang et al. [10]</td><td style='text-align: center; word-wrap: break-word;'>0.5267</td><td style='text-align: center; word-wrap: break-word;'>0.1589</td><td style='text-align: center; word-wrap: break-word;'>1.0000</td><td style='text-align: center; word-wrap: break-word;'>0.0000</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>0.4431</td><td style='text-align: center; word-wrap: break-word;'>0.2913</td><td style='text-align: center; word-wrap: break-word;'>0.6249</td><td style='text-align: center; word-wrap: break-word;'>0.2040</td></tr></table>

<div style="text-align: center;">Table 9. Performance of different methods on two settings of RepCount partA.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="2">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Method</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scale-1</td><td style='text-align: center; word-wrap: break-word;'>0.6595</td><td style='text-align: center; word-wrap: break-word;'>0.1854</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scale-4</td><td style='text-align: center; word-wrap: break-word;'>0.5434</td><td style='text-align: center; word-wrap: break-word;'>0.2649</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scale-8</td><td style='text-align: center; word-wrap: break-word;'>0.6657</td><td style='text-align: center; word-wrap: break-word;'>0.192</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Ours</td><td style='text-align: center; word-wrap: break-word;'>0.4431</td><td style='text-align: center; word-wrap: break-word;'>0.2913</td></tr></table>

<div style="text-align: center;">Table 10. The experimental results of pipelines with different scales. Scale-i, where  $ i \in \{1,4,8\} $, represents the temporal length of video subsequence, which is the input of Encoder  $ \phi $. The Ours, means cancatenating three scales video subsequence together, have the lowest MAE. We build all the above models by extracting 64 frames from the original video.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="3">RepCount A</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Sample rates</td><td style='text-align: center; word-wrap: break-word;'>Scales</td><td style='text-align: center; word-wrap: break-word;'>MAE $ \downarrow $</td><td style='text-align: center; word-wrap: break-word;'>OBO  $ \uparrow $</td></tr><tr><td rowspan="2">64</td><td style='text-align: center; word-wrap: break-word;'>Scale-1</td><td style='text-align: center; word-wrap: break-word;'>0.6595</td><td style='text-align: center; word-wrap: break-word;'>0.185</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scale-8</td><td style='text-align: center; word-wrap: break-word;'>0.6657</td><td style='text-align: center; word-wrap: break-word;'>0.192</td></tr><tr><td rowspan="2">128</td><td style='text-align: center; word-wrap: break-word;'>Scale-1</td><td style='text-align: center; word-wrap: break-word;'>0.6191</td><td style='text-align: center; word-wrap: break-word;'>0.191</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Scale-8</td><td style='text-align: center; word-wrap: break-word;'>0.4926</td><td style='text-align: center; word-wrap: break-word;'>0.2302</td></tr></table>

<div style="text-align: center;">Table 11. Performance of different scales at different sample rates. The first column, sample rates, indicates different frame sample number from initial videos. Scale-i, where  $ i \in \{1,8\} $, represents the temporal length of video subsequence.</div>


is more difference reflected between different video sub-sequence scales. Although single-frame has improved the MAE and OBO, the progress of 8-frames is more excellent.

### A.5. Compare to action segmentation

We elaborate the definitions and differences between action segmentation and repetitive action counting. Given an input video, action segmentation is to segment the temporal bound for different types of actions but repetitive action counting aims to count the number of repetitive action [5,39]. Two main differences are as follows: i) for action segmentation, the same action continuously repeating many times will be segmented into a single temporal bound. Thus, it is difficult to handle videos with high-frequency repetitive actions. However, the variation in the frequency of repetitive action is huge, e.g., the min/max cycle length is 0.1/10.96 in our dataset, which degenerates action segmentation method; ii) action segmentation can only address predefined action types and cannot handle open-set setting, where action types in the test set that do not exist in the training set. However, repetitive counting is to record repeated actions regardless of the action category.



To verify the above differences, we further perform experiments in Tab. 9. Under both settings of Tab. 8, our method achieves better performance compared to action segmentation [10]. Therefore, our task is not a trivial case of action segmentation.

### B. Dataset description

### B.1. Data duration

The duration in Table 1 means video length, not the cycle length of each action, which shows that our dataset contains longer videos. In addition, not only the short action but the diversity of actions makes the task harder and more useful. The min/max cycle length between Ours and UCF526 [39] is (0.1/10.96 vs 0.12/6.76), which shows our dataset is more challenging.

### B.2. Open-set setting

We add an open-set setting to demonstrate the better ability of our method when dealing with unseen action types in the training set. Therefore, we re-split the RepCount partA into a new train/val and test subset. For regular settings, videos are divided randomly. For Open-set setting, the action types in train/val/test are disjoint, where the actions in the test set do not appear in the training set. More details show in Tab. 8.