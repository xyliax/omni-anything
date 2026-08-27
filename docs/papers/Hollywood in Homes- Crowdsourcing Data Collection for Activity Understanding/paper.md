arXiv:1604.01753v3 [cs.CV] 26 Jul 2016

# Hollywood in Homes: Crowdsourcing Data Collection for Activity Understanding

Gunnar A. Sigurdsson $ ^{1} $, Gül Varol $ ^{2} $, Xiaolong Wang $ ^{1} $, Ali Farhadi $ ^{3,4} $, Ivan Laptev $ ^{2} $, and Abhinav Gupta $ ^{1,4} $

 $ ^{1} $Carnegie Mellon University  $ ^{2} $Inria  $ ^{3} $University of Washington

 $ ^{4} $The Allen Institute for AI

http://allenai.org/plato/charades/

Abstract. Computer vision has a great potential to help our daily lives by searching for lost keys, watering flowers or reminding us to take a pill. To succeed with such tasks, computer vision methods need to be trained from real and diverse examples of our daily dynamic scenes. While most of such scenes are not particularly exciting, they typically do not appear on YouTube, in movies or TV broadcasts. So how do we collect sufficiently many diverse but boring samples representing our lives? We propose a novel Hollywood in Homes approach to collect such data. Instead of shooting videos in the lab, we ensure diversity by distributing and crowdsourcing the whole process of video creation from script writing to video recording and annotation. Following this procedure we collect a new dataset, Charades, with hundreds of people recording videos in their own homes, acting out casual everyday activities. The dataset is composed of 9,848 annotated videos with an average length of 30 seconds, showing activities of 267 people from three continents, and over 15% of the videos have more than one person. Each video is annotated by multiple free-text descriptions, action labels, action intervals and classes of interacted objects. In total, Charades provides 27,847 video descriptions, 66,500 temporally localized intervals for 157 action classes and 41,104 labels for 46 object classes. Using this rich data, we evaluate and provide baseline results for several tasks including action recognition and automatic description generation. We believe that the realism, diversity, and casual nature of this dataset will present unique challenges and new opportunities for computer vision community.

## 1 Introduction

Large scale visual learning fueled by huge datasets has changed the computer vision landscape [1,2]. Given the source of this data, it's not surprising that most of our current success is biased towards static scenes and objects in Internet images. As we move forward into the era of AI and robotics, however, new questions arise. How do we learn about different states of objects (e.g., cut vs. whole)? How do common activities affect changes of object states? In fact, it is not even yet clear if the success of the Internet pre-trained recognition models

2

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

will transfer to real-world settings where robots equipped with our computer vision models should operate.

Shifting the bias from Internet images to real scenes will most likely require collection of new large-scale datasets representing activities of our boring everyday life: getting up, getting dressed, putting groceries in fridge, cutting vegetables and so on. Such datasets will allow us to develop new representations and to learn models with the right biases. But more importantly, such datasets representing people interacting with objects and performing natural action sequences in typical environments will finally allow us to learn common sense and contextual knowledge necessary for high-level reasoning and modeling.

But how do we find these boring videos of our daily lives? If we search common activities such as “drinking from a cup”, “riding a bike” on video sharing websites such as YouTube, we observe a highly-biased sample of results (see Figure 1). These results are biased towards entertainment—boring videos have no viewership and hence no reason to be uploaded on YouTube!

In this paper, we propose a novel Hollywood in Homes approach to collect a large-scale dataset of boring videos of daily activities. Standard approaches in the past have used videos downloaded from the Internet [3,4,5,6,7,8] gathered from movies [9,10,11] or recorded in controlled environments [12,13,14,15,16,17]. Instead, as the name suggests: we take the Hollywood filming process to the homes of hundreds of people on Amazon Mechanical Turk (AMT). AMT workers follow the three steps of filming process: (1) script generation; (2) video direction and acting based on scripts; and (3) video verification to create one of the largest and most diverse video datasets of daily activities.

There are threefold advantages of using the Hollywood in Homes approach for dataset collection: (a) Unlike datasets shot in controlled environments (e.g., MPII $ ^{[14]} $), crowdsourcing brings in diversity which is essential for generalization. In fact, our approach even allows the same script to be enacted by multiple people; (b) crowdsourcing the script writing enhances the coverage in terms of scenarios and reduces the bias introduced by generating scripts in labs; and (c) most importantly, unlike for web videos, this approach allows us to control the composition and the length of video scenes by proposing the vocabulary of scenes, objects and actions during script generation.

##### The Charades v1.0 Dataset

Charades is our large-scale dataset with a focus on common household activities collected using the Hollywood in Homes approach. The name comes from of a popular American word guessing game where one player acts out a phrase and the other players guess what phrase it is. In a similar spirit, we recruited hundreds of people from Amazon Mechanical Turk to act out a paragraph that we presented to them. The workers additionally provide action classification, localization, and video description annotations. The first publicly released version of our Charades dataset will contain 9,848 videos of daily activities 30.1 seconds long on average (7,985 training and 1,863 test). The dataset is collected in 15 types of indoor scenes, involves interactions with 46 object classes and has a vocabulary of 30 verbs leading to 157 action classes. It has 66,500 temporally localized ac-

Hollywood in Homes: Crowdsourcing Data Collection

3

<div style="text-align: center;"><img src="imgs/img_in_image_box_136_67_492_342.jpg" alt="Image" width="42%" />



</div>


The Charades Dataset

<div style="text-align: center;"><img src="imgs/img_in_image_box_511_66_691_342.jpg" alt="Image" width="21%" />



</div>


<div style="text-align: center;">You Tube</div>


<div style="text-align: center;">Fig. 1. Comparison of actions in the Charades dataset and on YouTube: Reading a book, Opening a refrigerator, Drinking from a cup. YouTube returns entertaining and often atypical videos, while Charades contains typical everyday videos.</div>


tions, 12.8 seconds long on average, recorded by 267 people in three continents. We believe this dataset will provide a crucial stepping stone in developing action representations, learning object states, human object interactions, modeling context, object detection in videos, video captioning and many more. The dataset will be publicly available at http://allenai.org/plato/charades/.

Contributions The contributions of our work are three-fold: (1) We introduce the Hollywood in Homes approach to data collection, (2) we collect and release the first crowdsourced large-scale dataset of boring household activities, and (3) we provide extensive baseline evaluations.

The KTH action dataset [12] paved the way for algorithms that recognized human actions. However, the dataset was limited in terms of number of categories and enacted in the same background. In order to scale up the learning and the complexity of the data, recent approaches have instead tried collecting video datasets by downloading videos from Internet. Therefore, datasets such as UCF101 [8], Sports1M [6] and others [7,4,5] appeared and presented more challenges including background clutter, and scale. However, since it is impossible to find boring daily activities on Internet, the vocabulary of actions became biased towards more sports-like actions which are easy to find and download.

There have been several efforts in order to remove the bias towards sporting actions. One such commendable effort is to use movies as the source of data [18,19]. Recent papers have also used movies to focus on the video description problem leading to several datasets such as MSVD [20], M-VAD [21], and MPII-MD [11]. Movies however are still exciting (and a source of entertainment) and do not capture the scenes, objects or actions of daily living. Other efforts have been to collect in-house datasets for capturing human-object interactions [22] or human-human interactions [23]. Some relevant big-scale efforts in this direction include MPII Cooking [14], TUM Breakfast [16], and the TACoS

4

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

<div style="text-align: center;">Table 1. Comparison of Charades with other video datasets.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>Actions per video</td><td style='text-align: center; word-wrap: break-word;'>Classes</td><td style='text-align: center; word-wrap: break-word;'>Labelled instances</td><td style='text-align: center; word-wrap: break-word;'>Total videos</td><td style='text-align: center; word-wrap: break-word;'>Origin</td><td style='text-align: center; word-wrap: break-word;'>Type</td><td style='text-align: center; word-wrap: break-word;'>Temporal localization</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Charades v1.0</td><td style='text-align: center; word-wrap: break-word;'>6.8</td><td style='text-align: center; word-wrap: break-word;'>157</td><td style='text-align: center; word-wrap: break-word;'>67K</td><td style='text-align: center; word-wrap: break-word;'>10K</td><td style='text-align: center; word-wrap: break-word;'>267 Homes</td><td style='text-align: center; word-wrap: break-word;'>Daily Activities</td><td style='text-align: center; word-wrap: break-word;'>Yes</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ActivityNet [3]</td><td style='text-align: center; word-wrap: break-word;'>1.4</td><td style='text-align: center; word-wrap: break-word;'>203</td><td style='text-align: center; word-wrap: break-word;'>39K</td><td style='text-align: center; word-wrap: break-word;'>28K</td><td style='text-align: center; word-wrap: break-word;'>YouTube</td><td style='text-align: center; word-wrap: break-word;'>Human Activities</td><td style='text-align: center; word-wrap: break-word;'>Yes</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>UCF101 [8]</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>101</td><td style='text-align: center; word-wrap: break-word;'>13K</td><td style='text-align: center; word-wrap: break-word;'>13K</td><td style='text-align: center; word-wrap: break-word;'>YouTube</td><td style='text-align: center; word-wrap: break-word;'>Sports</td><td style='text-align: center; word-wrap: break-word;'>No</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>HMDB51 [7]</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>51</td><td style='text-align: center; word-wrap: break-word;'>7K</td><td style='text-align: center; word-wrap: break-word;'>7K</td><td style='text-align: center; word-wrap: break-word;'>YouTube/Movies</td><td style='text-align: center; word-wrap: break-word;'>Movies</td><td style='text-align: center; word-wrap: break-word;'>No</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>THUMOS&#x27;15 [5]</td><td style='text-align: center; word-wrap: break-word;'>1-2</td><td style='text-align: center; word-wrap: break-word;'>101</td><td style='text-align: center; word-wrap: break-word;'>21K+</td><td style='text-align: center; word-wrap: break-word;'>24K</td><td style='text-align: center; word-wrap: break-word;'>YouTube</td><td style='text-align: center; word-wrap: break-word;'>Sports</td><td style='text-align: center; word-wrap: break-word;'>Yes</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>Sports 1M [6]</td><td style='text-align: center; word-wrap: break-word;'>1</td><td style='text-align: center; word-wrap: break-word;'>487</td><td style='text-align: center; word-wrap: break-word;'>1.1M</td><td style='text-align: center; word-wrap: break-word;'>1.1M</td><td style='text-align: center; word-wrap: break-word;'>YouTube</td><td style='text-align: center; word-wrap: break-word;'>Sports</td><td style='text-align: center; word-wrap: break-word;'>No</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MPII-Cooking [14]</td><td style='text-align: center; word-wrap: break-word;'>46</td><td style='text-align: center; word-wrap: break-word;'>78</td><td style='text-align: center; word-wrap: break-word;'>13K</td><td style='text-align: center; word-wrap: break-word;'>273</td><td style='text-align: center; word-wrap: break-word;'>30 In-house actors</td><td style='text-align: center; word-wrap: break-word;'>Cooking</td><td style='text-align: center; word-wrap: break-word;'>Yes</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ADL [25]</td><td style='text-align: center; word-wrap: break-word;'>22</td><td style='text-align: center; word-wrap: break-word;'>32</td><td style='text-align: center; word-wrap: break-word;'>436</td><td style='text-align: center; word-wrap: break-word;'>20</td><td style='text-align: center; word-wrap: break-word;'>20 Volunteers</td><td style='text-align: center; word-wrap: break-word;'>Ego-centric</td><td style='text-align: center; word-wrap: break-word;'>Yes</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>MPII-MD [11]</td><td style='text-align: center; word-wrap: break-word;'>Captions</td><td style='text-align: center; word-wrap: break-word;'>Captions</td><td style='text-align: center; word-wrap: break-word;'>68K</td><td style='text-align: center; word-wrap: break-word;'>94</td><td style='text-align: center; word-wrap: break-word;'>Movies</td><td style='text-align: center; word-wrap: break-word;'>Movies</td><td style='text-align: center; word-wrap: break-word;'>No</td></tr></table>

Multi-Level [17] datasets. These datasets focus on a narrow domain by collecting the data in-house with a fixed background, and therefore focus back on the activities themselves. This allows for careful control of the data distribution, but has limitations in terms of generalizability, and scalability. In contrast, PhotoCity [24] used the crowd to take pictures of landmarks, suggesting that the same could be done for other content at scale.

Another relevant effort in collection of data corresponding to daily activities and objects is in the domain of ego-centric cameras. For example, the Activities of Daily Living dataset [25] recorded 20 people performing unscripted, everyday activities in their homes in first person, and another extended that idea to animals [26]. These datasets provide a challenging task but fail to provide diversity which is crucial for generalizability. It should however be noted that these kinds of datasets could be crowdsourced similarly to our work.

The most related dataset is the recently released ActivityNet dataset [3]. It includes actions of daily living downloaded from YouTube. We believe the ActivityNet effort is complementary to ours since their dataset is uncontrolled, slightly biased towards non-boring actions and biased in the way the videos are professionally edited. On the other hand, our approach focuses more on action sequences (generated from scripts) involving interactions with objects. Our dataset, while diverse, is controlled in terms of vocabulary of objects and actions being used to generate scripts. In terms of the approach, Hollywood in Homes is also related to [27]. However, [27] only generates synthetic data. A comparison with other video datasets is presented in Table 1. To the best of our knowledge, our approach is the first to demonstrate that workers can be used to collect a vision dataset by filming themselves at such a large scale.

## 2 Hollywood in Homes

We now describe the approach and the process involved in a large-scale video collection effort via AMT. Similar to filming, we have a three-step process for generating a video. The first step is generating the script of the indoor video. The key here is to allow workers to generate diverse scripts yet ensure that we

Hollywood in Homes: Crowdsourcing Data Collection

5

have enough data for each category. The second step in the process is to use the script and ask workers to record a video of that sentence being acted out. In the final step, we ask the workers to verify if the recorded video corresponds to script, followed by an annotation procedure.

### 2.1 Generating Scripts

In this work we focus on indoor scenes, hence, we group together rooms in residential homes (Living Room, Home Office, etc.). We found 15 types of rooms to cover most of typical homes, these rooms form the scenes in the dataset. In order to generate the scripts (a text given to workers to act out in a video), we use a vocabulary of objects and actions to guide the process. To understand what objects and actions to include in this vocabulary, we analyzed 549 movie scripts from popular movies in the past few decades. Using both term-frequency (TF) and TF-IDF [28] we analyzed which nouns and verbs occur in those rooms in these movies. From those we curated a list of 40 objects and 30 actions to be used as seeds for script generation, where objects and actions were chosen to be generic for different scenes.

To harness the creativity of people, and understand their bias towards activities, we crowdsourced the script generation as follows. In the AMT interface, a single scene, 5 randomly selected objects, and 5 randomly selected actions were presented to workers. Workers were asked to use two objects and two actions to compose a short paragraph about activities of one or two people performing realistic and commonplace activities in their home. We found this to be a good compromise between controlling what kind of words were used and allowing the users to impose their own human bias on the generation. Some examples of generated scripts are shown in Figure 2. (see the website for more examples). The distribution of the words in the dataset is presented in Figure 3.

### 2.2 Generating Videos

Once we have scripts, our next step is to collect videos. To maximize the diversity of scenes, objects, clothing and behaviour of people, we ask the workers themselves to record the 30 second videos by following collected scripts.

AMT is a place where people commonly do quick tasks in the convenience of their homes or during downtime at their work. AMT has been used for annotation and editing but can we do content creation via AMT? During a pilot study we asked workers to record the videos, and until we paid up to $3 per video, no worker picked up our task. (For comparison, to annotate a video [29]: 3 workers × 157 questions × 1 second per question × $8/h salary = $1.) To reduce the base cost to a more manageable $1 per video, we have used the following strategies:

Worker Recruitment. To overcome the inconvenience threshold, worker recruitment was increased through sign-up bonuses (211% increased new worker rate) where we awarded a $5 bonus for the first submission. This increased the total cost by 17%. In addition, “recruit a friend” bonuses ($5 if a friend submits

6

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

<div style="text-align: center;"><img src="imgs/img_in_image_box_66_67_759_237.jpg" alt="Image" width="83%" />

Sampled Words
Kitchen
vacuum groceries chair refrigerator pillow
laughing drinking putting washing closing
AMT
"A person is washing their refrigerator. Then, opening it, the person begins putting away their groceries."
"A person opens a refrigerator, and begins drinking out of a jug of milk before closing it."
Scripts
Recorded Videos
Annotations
"A person stands in the kitchen and cleans the fridge. Then start to put groceries away from a bag"
Opening a refrigerator
Pitting groceries得一
Closing a refrigerator
person drinks milk from a fridge, they then walk out of the room."
Opening a refrigerator
Drinking from cup/bottle

</div>


<div style="text-align: center;">Fig. 2. An overview of the three Amazon Mechanical Turk (AMT) crowdsourcing stages in the Hollywood in Homes approach.</div>


15 videos) were introduced, and were claimed by 4% of the workforce, generating indeterminate outreach to the community. US, Canada, UK, and, for a time, India were included in this study. The first three accounted for estimated 73% of the videos, and 59% of the peak collection rate.

Worker Retention. Worker retention was mitigated through performance bonuses every 15th video, and while only accounting for a 33% increase in base cost, significantly increased retention (34% increase in come-back workers), and performance (109% increase in output per worker).

Each submission in this phase was manually verified by other workers to enforce quality control, where a worker was required to select the corresponding sentence from a line-up after watching the video. The rate of collection peaked at 1225 per day from 72 workers. The final cost distribution was: 65% base cost per video, 21% performance bonuses, 11% recruitment bonuses, and 3% verification. The code and interfaces will be made publicly available along with the dataset.

### 2.3 Annotations

Using the generated scripts, all (verb,proposition,noun) triplets were analyzed, and the most frequent grouped into 157 action classes (e.g., pouring into cup, running, folding towel, etc.). The distribution of those is presented in Figure 3.

For each recorded video we have asked other workers to watch the video and describe what they have observed with a sentence (this will be referred to as a description in contrast to the previous script used to generate the video). We use the original script and video descriptions to automatically generate a list of interacted objects for each video. Such lists were verified by the workers. Given the list of (verified) objects, for each video we have made a short list of 4-5 actions (out of 157) involving corresponding object interactions and asked the workers to verify the presence of these actions in the video.

In addition, to minimize the number of missing labels, we expanded the annotation procedure to exhaustively annotate all actions in the video using state-of-the-art crowdsourcing practices [29], where we focused particularly on the test set.

Finally, for all the chosen action classes in each video, another set of workers was asked to label the starting and ending point of the activity in the video, re-

Hollywood in Homes: Crowdsourcing Data Collection

7

sulting in a temporal interval of each action. A visualization of the data collection process is illustrated in Figure 2. On the website we show numerous additional examples from the dataset with annotated action classes.

## 3 Charades v1.0 Analysis

Charades is built up by combining 40 objects and 30 actions in 15 scenes. This relatively small vocabulary, combined with open-ended writing, creates a dataset that has substantial coverage of a useful domain. Furthermore, these combinations naturally form action classes that allow for standard benchmarking. In Figure 3 the distributions of action classes, and most common nouns/verbs/scenes in the dataset are presented. The natural world generally follows a long-tailed distribution [30,31], but we can see that the distribution of words in the dataset is relatively even. In Figure 3 we also present a visualization of what scenes, objects, and actions occur together. By embedding the words based on their co-occurrence with other words using T-SNE [32], we can get an idea of what words group together in the videos of the dataset, and it is clear that the dataset possesses real-world intuition. For example, food, and cooking are close to Kitchen, but note that except for Kitchen, Home Office, and Bathroom, the scene is not highly discriminative of the action, which reflects common daily activities.

Since we have control over the data acquisition process, instead of using Internet search, there are on average 6.8 relevant actions in each video. We hope that this may inspire new and interesting algorithms that try to capture this kind of context in the domain of action recognition. Some of the most common pairs of actions measured in terms of normalized pointwise mutual information (NPMI), are also presented in Figure 3. These actions occur in various orders and context, similar to our daily lives. For example, in Figure 4 we can see that among these five videos, there are multiple actions occurring, and some are in common. We further explore this in Figure 5, where for a few actions, we visualize the most probable actions to precede, and most probable actions to follow that action. As the scripts for the videos are generated by people imagining a boring realistic scenario, we find that these statistics reflect human behaviour.

## 4 Applications

We run several state-of-the-art algorithms on Charades to provide the community with a benchmark for recognizing human activities in realistic home environments. Furthermore, the performance and failures of tested algorithms provide insights into the dataset and its properties.

Train/test set. For evaluating algorithms we split the dataset into train and test sets by considering several constraints: (a) the same worker should not appear in both training and test; (b) the distribution of categories over the test set should be similar to the one over the training set; (c) there should be at least 6 test videos and 25 training videos in each category; (d) the test set should not be dominated by a single worker. We randomly split the workers into two

8

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

<div style="text-align: center;"><img src="imgs/img_in_image_box_70_94_755_949.jpg" alt="Image" width="82%" />

dining glass

</div>


<div style="text-align: center;">Fig. 3. Statistics for actions (gray, every fifth label shown), verbs (green), nouns (blue), scenes (red), and most co-occurring pairs of actions (cyan). Co-occurrence is measured with normalized pointwise mutual information. In addition, a T-SNE embedding of the co-occurrence matrix is presented. We can see that while there are some words that strongly associate with each other (e.g., lying and bed), many of the objects and actions co-occur with many of the scenes. (Action names are abbreviated as necessary to fit space constraints.)</div>


Hollywood in Homes: Crowdsourcing Data Collection

9

<div style="text-align: center;"><img src="imgs/img_in_image_box_135_67_690_612.jpg" alt="Image" width="67%" />

Holding a laptop Closing a laptop Put down laptop Taking a dish Taking a dish
Watching TV Watching laptop Closing a laptop Taking phone Playing on phone
Sitting at table Sitting at table Playing on phone Standing up Watching TV
Watching TV Sneezing Eating Sneezing Fixing hair
Walk in doorway Sneezing Taking box Tidying shelf

</div>


<div style="text-align: center;">Fig. 4. Keyframes from five videos in Charades. We see that actions occur together in many different configurations. (Shared actions are highlighted in color).</div>


groups (80% in training) such that these constraints were satisfied. The resulting training and test sets contain 7,985 and 1,863 videos, respectively. The number of annotated action intervals are 49,809 and 16,691 for training and test.

### 4.1 Action Classification

Given a video, we would like to identify whether it contains one or several actions out of our 157 action classes. We evaluate the classification performance for several baseline methods. Action classification performance is evaluated with the standard mean average precision (mAP) measure. A single video is assigned to multiple classes and the distribution of classes over the test set is not uniform. The label precision for the data is 95.6%, measured using an additional verification step, as well as comparing against a ground truth made from 19 iterations of annotations on a subset of 50 videos. We now describe the baselines.

Improved trajectories. We compute improved dense trajectory features (IDT) [33] capturing local shape and motion information with MBH, HOG and HOF video descriptors. We reduce the dimensionality of each descriptor by half with PCA, and learn a separate feature vocabulary for each descriptor with GMMs

10

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

<div style="text-align: center;"><img src="imgs/img_in_image_box_65_67_762_262.jpg" alt="Image" width="84%" />

Reading a book 13%
Smiling 9%
Taking a book 9%
Taking a book 7%
Smiling at a book 5%
Smiling 7%
Playing with camera 5%
Walk in doorway 6%
Sitting up 3%
Standing up 7%
Put blanket 4%
Throw blanket 4%
Awakening 3%
Smiling 3%
Standing up 13%
Smile 3%
Standing up 3%
Opening a window 3%
Looking at a book 9%
Put camera 9%
Smiling 7%
Standing up 13%
Smiling 10%
Standing up 3%
Smile 3%
Standing up 16%
Standing up 5%
Drink from cup 3%
Holding cup 3%
Sneezing 3%
Standing up 16%
Standing up 22%
Standing up 16%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 22%
Standing up 16%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing up 16%
Standing up 22%
Standing up 13%
Standing up 9%
Standing up 3%
Standing

</div>


<div style="text-align: center;">Fig. 5. Selected actions from the dataset, along with the top five most probable actions before, and after the action. For example, when Opening a window, it is likely that someone was Standing up before that, and after opening, Looking out the window.</div>


<div style="text-align: center;">Table 2. mAP (%) for action classification with various baselines.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'>Random</td><td style='text-align: center; word-wrap: break-word;'>C3D</td><td style='text-align: center; word-wrap: break-word;'>AlexNet</td><td style='text-align: center; word-wrap: break-word;'>Two-Stream-B</td><td style='text-align: center; word-wrap: break-word;'>Two-Stream</td><td style='text-align: center; word-wrap: break-word;'>IDT</td><td style='text-align: center; word-wrap: break-word;'>Combined</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>5.9</td><td style='text-align: center; word-wrap: break-word;'>10.9</td><td style='text-align: center; word-wrap: break-word;'>11.3</td><td style='text-align: center; word-wrap: break-word;'>11.9</td><td style='text-align: center; word-wrap: break-word;'>14.3</td><td style='text-align: center; word-wrap: break-word;'>17.2</td><td style='text-align: center; word-wrap: break-word;'>18.6</td></tr></table>

of 256 components. Finally, we encode the distribution of local descriptors over the video with Fisher vectors [34]. A one-versus-rest linear SVM is used for classification. Training on untrimmed intervals gave the best performance.

Static CNN features. In order to utilize information about objects in the scene, we make use of deep neural networks pretrained on a large collection of object images. We experiment with VGG-16 [35] and AlexNet [36] to compute  $ fc_{6} $ features over 30 equidistant frames in the video. These features are averaged across frames, L2-normalized and classified with a one-versus-rest linear SVM. Training on untrimmed intervals gave the best performance.

Two-stream networks. We use the VGG-16 model architecture [37] for both networks and follow the training procedure introduced in Simonyan et al. [38], with small modifications. For the spatial network, we applied finetuning on ImageNet pre-trained networks with different dropout rates. The best performance was with 0.5 dropout rate and finetuning on all fully connected layers. The temporal network was first pre-trained on the UCF101 dataset and then similarly finetuned on conv4, conv5, and fc layers. Training on trimmed intervals gave the best performance.

Balanced two-stream networks. We adapt the previous baseline to handle class imbalance. We balanced the number of training samples through sampling, and ensured each minibatch of 256 had at least 50 unique classes (each selected uniformly at random). Training on trimmed intervals gave the best performance.

C3D features. Following the recent approach from [39], we extract  $ fc_6 $ features from a 3D convnet pretrained on the Sports-1M video dataset [6]. These features capture complex hierarchies of spatio-temporal patterns given an RGB clip of 16 frames. Similar to [39], we compute features on chunks of 16 frames by sliding 8 frames, average across chunks, and use a one-versus-rest linear SVM. Training on untrimmed intervals gave the best performance.

Hollywood in Homes: Crowdsourcing Data Collection

11

<div style="text-align: center;">Table 3. Action classification evaluation with the state-of-the-art approach on Charades. We study different parameters for improved trajectories, by reporting for different local descriptor sets and different number of GMM clusters. Overall performance improves by combining all descriptors and using a larger descriptor vocabulary.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>HOG</td><td style='text-align: center; word-wrap: break-word;'>HOF</td><td style='text-align: center; word-wrap: break-word;'>MBH</td><td style='text-align: center; word-wrap: break-word;'>HOG+MBH</td><td style='text-align: center; word-wrap: break-word;'>HOG+HOF+MBH</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K=64</td><td style='text-align: center; word-wrap: break-word;'>12.3</td><td style='text-align: center; word-wrap: break-word;'>13.9</td><td style='text-align: center; word-wrap: break-word;'>15.0</td><td style='text-align: center; word-wrap: break-word;'>15.8</td><td style='text-align: center; word-wrap: break-word;'>16.5</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K=128</td><td style='text-align: center; word-wrap: break-word;'>12.7</td><td style='text-align: center; word-wrap: break-word;'>14.3</td><td style='text-align: center; word-wrap: break-word;'>15.4</td><td style='text-align: center; word-wrap: break-word;'>16.2</td><td style='text-align: center; word-wrap: break-word;'>16.9</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>K=256</td><td style='text-align: center; word-wrap: break-word;'>13.0</td><td style='text-align: center; word-wrap: break-word;'>14.4</td><td style='text-align: center; word-wrap: break-word;'>15.5</td><td style='text-align: center; word-wrap: break-word;'>16.5</td><td style='text-align: center; word-wrap: break-word;'>17.2</td></tr></table>

<table border=1 style='margin: auto; width: max-content;'>
  <thead><tr><th style='text-align: center;'>Action classes sorted by size in descending order</th><th style='text-align: center;'>AP</th><th style='text-align: center;'>AP_value</th></tr></thead>
  <tbody>
    <tr><td style='text-align: center;'>Walking in doorway</td><td style='text-align: center;'>48</td><td style='text-align: center;'>58</td></tr>
    <tr><td style='text-align: center;'>Washing in doorway</td><td style='text-align: center;'>45</td><td style='text-align: center;'>55</td></tr>
    <tr><td style='text-align: center;'>Wash window</td><td style='text-align: center;'>44</td><td style='text-align: center;'>54</td></tr>
    <tr><td style='text-align: center;'>Standing up</td><td style='text-align: center;'>43</td><td style='text-align: center;'>53</td></tr>
    <tr><td style='text-align: center;'>Sitting down</td><td style='text-align: center;'>42</td><td style='text-align: center;'>52</td></tr>
    <tr><td style='text-align: center;'>Sitting on chair</td><td style='text-align: center;'>41</td><td style='text-align: center;'>51</td></tr>
    <tr><td style='text-align: center;'>Sitting at table</td><td style='text-align: center;'>40</td><td style='text-align: center;'>50</td></tr>
    <tr><td style='text-align: center;'>Cooking</td><td style='text-align: center;'>39</td><td style='text-align: center;'>49</td></tr>
    <tr><td style='text-align: center;'>Opening door</td><td style='text-align: center;'>38</td><td style='text-align: center;'>48</td></tr>
    <tr><td style='text-align: center;'>Running</td><td style='text-align: center;'>37</td><td style='text-align: center;'>47</td></tr>
    <tr><td style='text-align: center;'>Opening fridge</td><td style='text-align: center;'>36</td><td style='text-align: center;'>46</td></tr>
    <tr><td style='text-align: center;'>Lying on bed</td><td style='text-align: center;'>35</td><td style='text-align: center;'>45</td></tr>
    <tr><td style='text-align: center;'>Tidying floor</td><td style='text-align: center;'>34</td><td style='text-align: center;'>44</td></tr>
    <tr><td style='text-align: center;'>Drinking from cup</td><td style='text-align: center;'>33</td><td style='text-align: center;'>43</td></tr>
    <tr><td style='text-align: center;'>Closing fridge</td><td style='text-align: center;'>32</td><td style='text-align: center;'>42</td></tr>
    <tr><td style='text-align: center;'>Tidying with broom</td><td style='text-align: center;'>31</td><td style='text-align: center;'>41</td></tr>
    <tr><td style='text-align: center;'>Throwing shoes</td><td style='text-align: center;'>30</td><td style='text-align: center;'>40</td></tr>
    <tr><td style='text-align: center;'>Standing on chair</td><td style='text-align: center;'>29</td><td style='text-align: center;'>39</td></tr>
    <tr><td style='text-align: center;'>Taking laptop</td><td style='text-align: center;'>28</td><td style='text-align: center;'>38</td></tr>
    <tr><td style='text-align: center;'>Fixing door/knot</td><td style='text-align: center;'>27</td><td style='text-align: center;'>37</td></tr>
    <tr><td style='text-align: center;'>Grabbing picture</td><td style='text-align: center;'>26</td><td style='text-align: center;'>36</td></tr>
    <tr><td style='text-align: center;'>Washing mirror</td><td style='text-align: center;'>25</td><td style='text-align: center;'>35</td></tr>
    <tr><td style='text-align: center;'>Throwing book</td><td style='text-align: center;'>24</td><td style='text-align: center;'>34</td></tr>
    <tr><td style='text-align: center;'>Closing laptop</td><td style='text-align: center;'>23</td><td style='text-align: center;'>33</td></tr>
    <tr><td style='text-align: center;'>Throwing food</td><td style='text-align: center;'>22</td><td style='text-align: center;'>32</td></tr>
    <tr><td style='text-align: center;'>Put picture somewhere</td><td style='text-align: center;'>21</td><td style='text-align: center;'>31</td></tr>
    <tr><td style='text-align: center;'>Holding mirror</td><td style='text-align: center;'>20</td><td style='text-align: center;'>30</td></tr>
    <tr><td style='text-align: center;'>Laughing at picture</td><td style='text-align: center;'>19</td><td style='text-align: center;'>29</td></tr>
    <tr><td style='text-align: center;'>Throwing bag</td><td style='text-align: center;'>18</td><td style='text-align: center;'>28</td></tr>
    <tr><td style='text-align: center;'>Throwing broom</td><td style='text-align: center;'>17</td><td style='text-align: center;'>27</td></tr>
    <tr><td style='text-align: center;'>Throwing box</td><td style='text-align: center;'>16</td><td style='text-align: center;'>26</td></tr>
  </tbody>
</table>

<div style="text-align: center;">Fig. 6. On the left classification accuracy for the 15 highest and lowest actions is presented for Combined. On the right, the classes are sorted by their size. The top actions on the left are annotated on the right. We can see that while there is a slight trend for smaller classes to have lower accuracy, many classes do not follow that trend.</div>


Action classification results are presented in Table 2, where we additionally consider Combined which combines all the other methods with late fusion.

Notably, the accuracy of the tested state-of-the-art baselines is much lower than in most currently available benchmarks. Consistently with several other datasets, IDT features [33] outperform other methods by obtaining 17.2% mAP. To analyze these results, Figure 6(left) illustrates the results for subsets of best and worst recognized action classes. We can see that while the mAP is low, there are certain classes that have reasonable performance, for example Washing a window has 62.1% AP. To understand the source of difference in performance for different classes, Figure 6(right) illustrates AP for each action, sorted by the number of examples, together with names for the best performing classes. The number of actions in a class is primarily decided by the universality of the action (can it happen in any scene), and if it is common in typical households.

12

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

<div style="text-align: center;"><img src="imgs/img_in_image_box_135_66_695_430.jpg" alt="Image" width="67%" />

True Class Clothes
Door Table
Towel Box
Shoes Chair
Blanket Window
Doorway Broom
Cup Closet
Dishes Couch
Bed
Fridge No Object
Predicted Class Probability (%)

</div>


<div style="text-align: center;">Fig. 7. Confusion matrix for the Combined baseline on the classification task. Actions are grouped by the object being interacted with. Most of the confusion is with other actions involving the same object (squares on the diagonal), and we highlight some prominent objects. Note: (A) High confusion between actions using Blanket, Clothes, and Towel; (B) High confusion between actions using Couch and Bed; (C) Little confusion among actions with no specific object of interaction (e.g. standing up, sneezing).</div>


(writer bias). It is interesting to notice, that while there is a trend for actions with higher number of examples to have higher AP, it is not true in general, and actions such as Sitting in chair, and Washing windows have top-15 performance.

Delving even further, we investigate the confusion matrix for the Combined baseline in Figure 7, where we convert the predictor scores to probabilities and accumulate them for each class. For clearer analysis, the classes are sorted by the object being interacted with. The first aspect to notice is the squares on the diagonal, which imply that the majority of the confusion is among actions that interact with the same object (e.g., Putting on clothes, or Taking clothes from somewhere), and moreover, there is confusion among objects with similar functional properties. The most prominent squares are annotated with the object being shared among those actions. The figure caption contains additional observations. While there are some categories that show no clear trend, we can observe less confusion for many actions that have no specific object of interaction. Evaluation of action recognition on this subset results in 38.9% mAP, which is significantly higher than average. Recognition of fine-grained actions involving interactions with the same object class appears particularly difficult even for the best methods available today. We hope our dataset will encourage new methods addressing activity recognition for complex person-object interactions.

Hollywood in Homes: Crowdsourcing Data Collection

13

<div style="text-align: center;">Table 4. Sentence Prediction. In the script task one sentence is used as ground truth, and in the description task 2.4 sentences are used as ground truth on average. We find that S2VT is the strongest baseline.</div>



<table border=1 style='margin: auto; word-wrap: break-word;'><tr><td style='text-align: center; word-wrap: break-word;'></td><td colspan="5">Script</td><td colspan="5">Description</td></tr><tr><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>RW</td><td style='text-align: center; word-wrap: break-word;'>Random</td><td style='text-align: center; word-wrap: break-word;'>NN</td><td style='text-align: center; word-wrap: break-word;'>S2VT</td><td style='text-align: center; word-wrap: break-word;'>Human</td><td style='text-align: center; word-wrap: break-word;'>RW</td><td style='text-align: center; word-wrap: break-word;'>Random</td><td style='text-align: center; word-wrap: break-word;'>NN</td><td style='text-align: center; word-wrap: break-word;'>S2VT</td><td style='text-align: center; word-wrap: break-word;'>Human</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>CIDEr</td><td style='text-align: center; word-wrap: break-word;'>0.03</td><td style='text-align: center; word-wrap: break-word;'>0.08</td><td style='text-align: center; word-wrap: break-word;'>0.11</td><td style='text-align: center; word-wrap: break-word;'>0.17</td><td style='text-align: center; word-wrap: break-word;'>0.51</td><td style='text-align: center; word-wrap: break-word;'>0.04</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.07</td><td style='text-align: center; word-wrap: break-word;'>0.14</td><td style='text-align: center; word-wrap: break-word;'>0.53</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BLEU $ _{4} $</td><td style='text-align: center; word-wrap: break-word;'>0.00</td><td style='text-align: center; word-wrap: break-word;'>0.03</td><td style='text-align: center; word-wrap: break-word;'>0.03</td><td style='text-align: center; word-wrap: break-word;'>0.06</td><td style='text-align: center; word-wrap: break-word;'>0.10</td><td style='text-align: center; word-wrap: break-word;'>0.00</td><td style='text-align: center; word-wrap: break-word;'>0.04</td><td style='text-align: center; word-wrap: break-word;'>0.05</td><td style='text-align: center; word-wrap: break-word;'>0.11</td><td style='text-align: center; word-wrap: break-word;'>0.20</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BLEU $ _{3} $</td><td style='text-align: center; word-wrap: break-word;'>0.01</td><td style='text-align: center; word-wrap: break-word;'>0.07</td><td style='text-align: center; word-wrap: break-word;'>0.07</td><td style='text-align: center; word-wrap: break-word;'>0.12</td><td style='text-align: center; word-wrap: break-word;'>0.16</td><td style='text-align: center; word-wrap: break-word;'>0.02</td><td style='text-align: center; word-wrap: break-word;'>0.09</td><td style='text-align: center; word-wrap: break-word;'>0.10</td><td style='text-align: center; word-wrap: break-word;'>0.18</td><td style='text-align: center; word-wrap: break-word;'>0.29</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BLEU $ _{2} $</td><td style='text-align: center; word-wrap: break-word;'>0.09</td><td style='text-align: center; word-wrap: break-word;'>0.15</td><td style='text-align: center; word-wrap: break-word;'>0.15</td><td style='text-align: center; word-wrap: break-word;'>0.21</td><td style='text-align: center; word-wrap: break-word;'>0.27</td><td style='text-align: center; word-wrap: break-word;'>0.09</td><td style='text-align: center; word-wrap: break-word;'>0.20</td><td style='text-align: center; word-wrap: break-word;'>0.21</td><td style='text-align: center; word-wrap: break-word;'>0.30</td><td style='text-align: center; word-wrap: break-word;'>0.43</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>BLEU $ _{1} $</td><td style='text-align: center; word-wrap: break-word;'>0.37</td><td style='text-align: center; word-wrap: break-word;'>0.29</td><td style='text-align: center; word-wrap: break-word;'>0.29</td><td style='text-align: center; word-wrap: break-word;'>0.36</td><td style='text-align: center; word-wrap: break-word;'>0.43</td><td style='text-align: center; word-wrap: break-word;'>0.38</td><td style='text-align: center; word-wrap: break-word;'>0.40</td><td style='text-align: center; word-wrap: break-word;'>0.40</td><td style='text-align: center; word-wrap: break-word;'>0.49</td><td style='text-align: center; word-wrap: break-word;'>0.62</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>ROUGE $ _{L} $</td><td style='text-align: center; word-wrap: break-word;'>0.21</td><td style='text-align: center; word-wrap: break-word;'>0.24</td><td style='text-align: center; word-wrap: break-word;'>0.25</td><td style='text-align: center; word-wrap: break-word;'>0.31</td><td style='text-align: center; word-wrap: break-word;'>0.35</td><td style='text-align: center; word-wrap: break-word;'>0.22</td><td style='text-align: center; word-wrap: break-word;'>0.27</td><td style='text-align: center; word-wrap: break-word;'>0.28</td><td style='text-align: center; word-wrap: break-word;'>0.35</td><td style='text-align: center; word-wrap: break-word;'>0.44</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>METEOR</td><td style='text-align: center; word-wrap: break-word;'>0.10</td><td style='text-align: center; word-wrap: break-word;'>0.11</td><td style='text-align: center; word-wrap: break-word;'>0.12</td><td style='text-align: center; word-wrap: break-word;'>0.13</td><td style='text-align: center; word-wrap: break-word;'>0.20</td><td style='text-align: center; word-wrap: break-word;'>0.11</td><td style='text-align: center; word-wrap: break-word;'>0.13</td><td style='text-align: center; word-wrap: break-word;'>0.14</td><td style='text-align: center; word-wrap: break-word;'>0.16</td><td style='text-align: center; word-wrap: break-word;'>0.24</td></tr></table>

### 4.2 Sentence Prediction

Our final, and arguably most challenging task, concerns prediction of free-from sentences describing the video. Notably, our dataset contains sentences that have been used to create the video (scripts), as well as multiple video descriptions obtained manually for recorded videos. The scripts used to create videos are biased by the vocabulary, and due to the writer's imagination, generally describe different aspects of the video than descriptions. The description of the video by other people is generally simpler and to the point. Captions are evaluated using the CIDEr, BLEU, ROUGE, and METEOR metrics, as implemented in the COCO Caption Dataset [40]. These metrics are common for comparing machine translations to ground truth, and have varying degrees of similarity with human judgement. For comparison, human performance is presented along with the baselines where workers were similarly asked to watch the video and describe what they observed. We now describe the sentence prediction baselines in detail:

<div style="text-align: center;"><img src="imgs/img_in_image_box_135_827_692_1073.jpg" alt="Image" width="67%" />

A person is walking into a room and then picks up a broom and puts it on the floor.
Person is standing in front of a mirror, opens a cabinet and takes out of a cabinet.
A person is lying on a bed with a blanket. the person then gets up and walks to the room and sits down.
A person is standing in the kitchen cooking on a stove. they then take a drink from a glass and drink it.
A person is standing in the doorway holding a pillow, the person then takes up and walks to the door and sits down.
GT: A person opens a closed and picks up a pink toy laptop off of the shelf. They close the closet, turn off the light, and exit the room.
GT: A person sweeps the floor and places the dirt into a trash bag.
GT: A person is sitting in a chair while watching something on a laptop. The person then begins to laugh.
GT: A person is cooking on a stove they are making the food in the pot they go to the cabinet and take out a spice they put the spice in the pot.
GT: Person is standing in the doorway holding a pillow, the person then takes up and walks to the door and sits down.
GT: A person walks up and turns a light on and off before going back to sleep.

</div>


<div style="text-align: center;">Fig. 8. Three generated captions that scored low on the CIDEr metric (red), and three that scored high (green) from the strongest baseline (S2VT). We can see that while the captions are fairly coherent, the captions lack sufficient relevance.</div>


14

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

Random Words (RW): Random words from the training set.

Random Sentence (Random): Random sentence from the training set.

Nearest Neighbor (NN): Inspired by Devlin et al. [41] we simply use a 1-Nearest Neighbor baseline computed using AlexNet  $ fc_{7} $ outputs averaged over frames, and use the caption from that nearest neighbor in the training set.

S2VT: We use the S2VT method from Venugopalan et al. [42], which is a combination of a CNN, and a LSTM.

Table 4 presents the performance of multiple baselines on the caption generation task. We both evaluate on predicting the script, as well as predicting the description. As expected, we can observe that descriptions made by people after watching the video are more similar to other descriptions, rather than the scripts used to generate the video. Table 4 also provides insight into the different evaluation metrics, and it is clear that CIDEr offers the highest resolution, and most similarity with human judgement on this task. In Figure 8 few examples are presented for the highest scoring baseline (S2VT). We can see that while the language model is accurate (the sentences are coherent), the model struggles with providing relevant captions, and tends to slightly overfit to frequent patterns in the data (e.g., drinking from a glass/cup).

## 5 Conclusions

We proposed a new approach for building datasets. Our Hollywood in Homes approach allows not only the labeling, but the data gathering process to be crowdsourced. In addition, Charades offers a novel large-scale dataset with diversity and relevance to the real world. We hope that Charades and Hollywood in Homes will have the following benefits for our community:

(1) Training data: Charades provides a large-scale set of 66,500 annotations of actions with unique realism.

(2) A benchmark: Our publicly available dataset and provided baselines enable benchmarking future algorithms.

(3) Object-action interactions: The dataset contains significant and intricate object-action relationships which we hope will inspire the development of novel computer vision techniques targeting these settings.

(4) A framework to explore novel domains: We hope that many novel datasets in new domains can be collected using the Hollywood in Homes approach.

(5) Understanding daily activities: Charades provides data from a unique human-generated angle, and has unique attributes, such as complex co-occurrences of activities. This kind of realistic bias, may provide new insights that aid robots equipped with our computer vision models operating in the real world.

## 6 Acknowledgements

This work was partly supported by ONR MURI N00014-16-1-2007, ONR N00014-13-1-0720, NSF IIS-1338054, ERC award ACTIVIA, Allen Distinguished Investigator Award, gifts from Google, and the Allen Institute for Artificial Intelligence.

Hollywood in Homes: Crowdsourcing Data Collection

15

The authors would like to thank: Nick Rhinehart and the anonymous reviewers for helpful feedback on the manuscript; Ishan Misra for helping in the initial experiments; and Olga Russakovsky, Mikel Rodriguez, and Rahul Sukhantakar for invaluable suggestions and advice. Finally, the authors want to extend thanks to all the workers at Amazon Mechanical Turk.

## References

1. Deng, J., Dong, W., Socher, R., Li, L.J., Li, K., Fei-Fei, L.: Imagenet: A large-scale hierarchical image database. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2009) 248–255.

2. Zhou, B., Lapedriza, A., Xiao, J., Torralba, A., Oliva, A.: Learning deep features for scene recognition using places database. In: Neural Information Processing Systems (NIPS). (2014) 487–495.

3. Caba Heilbron, F., Escorcia, V., Ghanem, B., Carlos Niebles, J.: Activitynet: A large-scale video benchmark for human activity understanding. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2015) 961–970 2, 4

4. Liu, J., Luo, J., Shah, M.: Recognizing realistic actions from videos in the wild. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2009) 1996–2003 2, 3

5. Gorban, A., Idrees, H., Jiang, Y.G., Roshan Zamir, A., Laptev, I., Shah, M., Sukthankar, R.: THUMOS challenge: Action recognition with a large number of classes. http://www.thumos.info/ (2015) 2, 3, 4

6. Karpathy, A., Toderici, G., Shetty, S., Leung, T., Sukthankar, R., Fei-Fei, L.: Large-scale video classification with convolutional neural networks. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2014) 1725–1732 2, 3, 4, 10

7. Kuehne, H., Jhuang, H., Garrote, E., Poggio, T., Serre, T.: HMDB: a large video database for human motion recognition. In: International Conference on Computer Vision (ICCV), IEEE (2011) 2556–2563 2, 3, 4

8. Soomro, K., Roshan Zamir, A., Shah, M.: UCF101: A dataset of 101 human actions classes from videos in the wild. In: CRCV-TR-12-01. (2012) 2, 3, 4

9. Laptev, I., Marszałek, M., Schmid, C., Rozenfeld, B.: Learning realistic human actions from movies. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2008) 1–8 2

10. Rodriguez, M.D., Ahmed, J., Shah, M.: Action mach a spatio-temporal maximum average correlation height filter for action recognition. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2008) 1–8 2

11. Rohrbach, A., Rohrbach, M., Tandon, N., Schiele, B.: A dataset for movie description. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2015) 2, 3, 4

12. Schüldt, C., Laptev, I., Caputo, B.: Recognizing human actions: a local svm approach. In: International Conference on Pattern Recognition (ICPR). Volume 3., IEEE (2004) 32–36 2, 3

13. Gorelick, L., Blank, M., Shechtman, E., Irani, M., Basri, R.: Actions as space-time shapes. Transactions on Pattern Analysis and Machine Intelligence 29(12)(December 2007) 2247–2253 2

14. Rohrbach, M., Amin, S., Andriluka, M., Schiele, B.: A database for fine grained activity detection of cooking activities. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2012) 1194–1201 2, 3, 4

16

Sigurdsson, Varol, Wang, Farhadi, Laptev, Gupta

15. Oh, S., Hoogs, A., Perera, A., Cuntoor, N., Chen, C.C., Lee, J.T., Mukherjee, S., Aggarwal, J., Lee, H., Davis, L., et al.: A large-scale benchmark dataset for event recognition in surveillance video. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2011) 3153–3160 2

16. Kuehne, H., Arslan, A.B., Serre, T.: The language of actions: Recovering the syntax and semantics of goal-directed human activities. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2014) 2, 3

17. Rohrbach, A., Rohrbach, M., Qiu, W., Friedrich, A., Pinkal, M., Schiele, B.: Coherent multi-sentence video description with variable level of detail. In: Pattern Recognition. Springer (2014) 184–195 2, 3

18. Marszalek, M., Laptev, I., Schmid, C.: Actions in context. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2009) 3

19. Ferrari, V., Marín-Jiménez, M., Zisserman, A.: 2d human pose estimation in tv shows. In: Statistical and Geometrical Approaches to Visual Motion Analysis. Springer (2009) 128–147 3

20. Chen, D.L., Dolan, W.B.: Collecting highly parallel data for paraphrase evaluation. In: Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies-Volume 1, Association for Computational Linguistics (2011) 190–200 3

21. Torabi, A., Pal, C., Larochelle, H., Courville, A.: Using descriptive video services to create a large data source for video annotation research. arXiv preprint arXiv:1503.01070 (2015) 3

22. Gupta, A., Davis, L.S.: Objects in action: An approach for combining action understanding and object perception. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2007) 1–8 3

23. Ryoo, M.S., Aggarwal, J.K.: Spatio-temporal relationship match: Video structure comparison for recognition of complex human activities. In: International Conference on Computer Vision (ICCV), IEEE (2009) 1593–1600.

24. Tuite, K., Snavely, N., Hsiao, D.y., Tabing, N., Popovic, Z.: Photocity: training experts at large-scale image acquisition through a competitive game. In: Proceedings of the SIGCHI Conference on Human Factors in Computing Systems, ACM (2011) 1383–1392 4

25. Pirsiavash, H., Ramanan, D.: Detecting activities of daily living in first-person camera views. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2012) 2847–2854 4

26. Iwashita, Y., Takamine, A., Kurazume, R., Ryoo, M.S.: First-person animal activity recognition from egocentric videos. In: International Conference on Pattern Recognition (ICPR), Stockholm, Sweden (August 2014) 4

27. Zitnick, C., Parikh, D.: Bringing semantics into focus using visual abstraction. In: Computer Vision and Pattern Recognition (CVPR), IEEE (2013) 3009–3016 4

28. Salton, G., Michael, J.: McGill. Introduction to modern information retrieval (1983) 24–51 5

29. Sigurdsson, G.A., Russakovsky, O., Farhadi, A., Laptev, I., Gupta, A.: Much ado about time: Exhaustive annotation of temporal data. arXiv preprint arXiv:1607.07429 (2016) 5, 6

30. Zipf, G.K.: The psycho-biology of language. (1935) 7

31. Simoncelli, E.P., Olshausen, B.A.: Natural image statistics and neural representation. Annual review of neuroscience 24(1) (2001) 1193–1216 7

32. Van der Maaten, L., Hinton, G.: Visualizing data using t-sne. Journal of Machine Learning Research 9 (2579-2605) (2008) 85 7

Hollywood in Homes: Crowdsourcing Data Collection

17

33. Wang, H., Schmid, C.: Action recognition with improved trajectories. In: International Conference on Computer Vision (ICCV). (2013) 9, 11

34. Perronnin, F., Sánchez, J., Mensink, T.: Improving the fisher kernel for large-scale image classification. In: European Conference on Computer Vision (ECCV). (2010) 10

35. Simonyan, K., Zisserman, A.: Very deep convolutional networks for large-scale image recognition. In: International Conference on Learning Representations (ICLR). (2015) 10

36. Krizhevsky, A., Sutskever, I., Hinton, G.E.: Imagenet classification with deep convolutional neural networks. In: Neural Information Processing Systems (NIPS). (2012) 10

37. Simonyan, K., Zisserman, A.: Very deep convolutional networks for large-scale image recognition. CoRR abs/1409.1556 (2014) 10

38. Simonyan, K., Zisserman, A.: Two-stream convolutional networks for action recognition in videos. In: Neural Information Processing Systems (NIPS). (2014) 10

39. Tran, D., Bourdev, L., Fergus, R., Torresani, L., Paluri, M.: Learning spatiotemporal features with 3D convolutional networks. In: International Conference on Computer Vision (ICCV). (2015) 10

40. Chen, X., Fang, H., Lin, T., Vedantam, R., Gupta, S., Dolr, P., Zitnick, C.L.: Microsoft coco captions: Data collection and evaluation server. arXiv:1504.00325 (2015) 13

41. Devlin, J., Gupta, S., Girshick, R., Mitchell, M., Zitnick, C.L.: Exploring nearest neighbor approaches for image captioning. arXiv preprint arXiv:1505.04467 (2015) 14

42. Venugopalan, S., Rohrbach, M., Donahue, J., Mooney, R., Darrell, T., Saenko, K.: Sequence to sequence-video to text. In: International Conference on Computer Vision (ICCV). (2015) 4534–4542 14