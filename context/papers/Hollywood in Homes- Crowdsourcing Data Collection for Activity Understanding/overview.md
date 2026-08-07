- **Title:** Hollywood in Homes: Crowdsourcing Data Collection for Activity Understanding
- **Summary:** Hollywood in Homes shows that the data-creation process itself can be crowdsourced to build Charades, a controlled but diverse household-activity benchmark whose baseline failures expose fine-grained person-object interaction and captioning gaps.
- **Paper Type:** dataset
- **Venue:** arXiv 2016
- **Authors:** Gunnar A. Sigurdsson, Gul Varol, Xiaolong Wang, Ali Farhadi, Ivan Laptev, and Abhinav Gupta; Carnegie Mellon University, Inria, University of Washington, and The Allen Institute for AI
- **Keywords:** activity understanding, crowdsourced dataset collection, Charades, household activities, action recognition, video captioning, temporal localization, human-object interaction
- ## Orientation
    - **Background:** This is about activity understanding: teaching vision systems to recognize what people are doing over time, not just which objects appear in one image. The prerequisite idea is that datasets shape model behavior, because models learn the situations a dataset makes common.
      claim_kind:: analyst_assessment
    - **The Problem in Plain Words:** Everyday household behavior is visually ordinary, so people rarely upload clean examples of it online, yet home robots and assistive tools need to understand exactly that kind of behavior.
      claim_kind:: analyst_assessment
    - **Why It Is Hard:** The data must be realistic, diverse, annotated over time, and still controllable enough that learning tasks have clear labels.
      claim_kind:: analyst_assessment
    - **Key Idea in One Breath:** Move the filming pipeline into workers' homes: ask people to write small scripts, act them out, and let other workers verify and annotate the resulting videos.
      claim_kind:: analyst_assessment
- ## Quick Reference
    - **Why Read:** Read this as a dataset-design paper for activity understanding, the vision problem of recognizing what people do over time: it attacks the missing-data gap for ordinary household behavior that web and movie sources underrepresent.
      claim_kind:: analyst_assessment
      evidence:: E2, E13
    - **One-Sentence Contribution:** Hollywood in Homes improves household activity data collection by turning online workers into script writers, actors, and annotators, producing Charades with free-text descriptions, action labels, and labels with start and end times (temporal localization).
      evidence:: E1, E3, E6
    - **Mental Model:** Think of it as a distributed home movie studio: the researchers provide a small prop list and task list, many people improvise ordinary scenes at home, and separate viewers check what actually happened.
      claim_kind:: analyst_assessment
    - **Best Evidence:** The strongest evidence is the combination of dataset scale, controlled annotations, and weak baseline performance measured by mean average precision (mAP), a metric that averages precision over ranked predictions.
      evidence:: E1, E9, E12
        - Supports C1: Charades v1.0; contemporary video datasets in Table 1 as context; dataset origin, action density, labels, and temporal localization; 6.8 actions per video, 157 classes, and about 67K labels from 267 homes; supported as dataset-scale evidence.
          evidence:: E1, E14
        - Supports C3: action classification on Charades; Random, C3D, AlexNet, Two-Stream, Improved Dense Trajectories (IDT), and late-fusion Combined baselines; mAP; Combined reaches 18.6% versus Random 5.9%; supported but without variance or repeat counts.
          evidence:: E9
        - Supports C4: sentence prediction on scripts and descriptions; Sequence to Sequence - Video to Text (S2VT) versus human descriptions; CIDEr caption similarity; S2VT scores 0.17/0.14 while humans score 0.51/0.53; supported but baseline-era only.
          evidence:: E12
    - **Main Caveat:** The evidence proves Charades was challenging for 2016 baselines, but the collection is still scripted and acted, and the experiments do not report uncertainty, repeat counts, hardware budgets, or modern model comparisons.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E9, E12
- ## Argument Map
    - **Problem and Stakes:** The paper argues that models meant for real homes need training examples of ordinary object-centered activities, not only static images, sports clips, movies, or lab scenes. The stakes are representation learning for object state, human-object interaction, context, video description, and future robot perception.
      evidence:: E1, E2
    - **Prior Gap:** Internet and movie datasets provide scale but bias toward entertaining or edited actions, while in-house and first-person daily-activity datasets provide control but not the same diversity or scalability. ActivityNet is presented as complementary because it uses YouTube daily activities but remains uncontrolled and professionally edited.
      evidence:: E13, E14
    - **Key Insight:** The collection bottleneck can be shifted from finding naturally uploaded videos to creating ordinary videos on demand, while preserving diversity by distributing the filming across workers' real homes. The control lever is not a lab set but a vocabulary-constrained script prompt.
      evidence:: E3, E4, E5
    - **Claims:** The paper's main claims are about a collection method, the resulting dataset, and the difficulty that dataset exposes for recognition and captioning systems.
      evidence:: E1, E3, E9
        - C1: Hollywood in Homes can produce a large, controlled, and diverse dataset of realistic household activities rather than relying on web search, movies, or lab recording.
          evidence:: E1, E3, E5
        - C2: Charades supplies dense multi-action videos with temporal localization and object interaction labels, making it useful for household activity, context, and description benchmarks.
          evidence:: E1, E6, E7
        - C3: Standard action-recognition baselines struggle on Charades, especially when actions differ mainly by the object being manipulated or by fine-grained interaction.
          evidence:: E9, E10
        - C4: Video captioning baselines can produce coherent language on Charades but remain far from human descriptions in relevance.
          evidence:: E11, E12
- ## Mechanism and Design
    - **Core Mechanism:** The method uses Amazon Mechanical Turk (AMT), an online marketplace for paid tasks, to distribute the whole data lifecycle: workers write scripts, other workers act and record them in homes, and additional workers verify and annotate the videos. This turns crowdsourcing from a labeling tool into a controlled content-creation pipeline.
      evidence:: E3, E5, E6
    - **Data / Control Flow:** The pipeline starts with a constrained text prompt, turns that prompt into a home-recorded video, verifies whether the video matches the prompt, and then derives descriptions, object labels, action classes, and temporal intervals. The resulting artifact links free text, object interaction, multi-action labels, and action timing for each video.
      evidence:: E4, E5, E6
        - Script step: workers receive a room, sampled objects, and sampled actions, then write a short realistic paragraph so the dataset remains both guided and human-imagined.
          evidence:: E4
        - Video step: workers record roughly half-minute videos in their own homes, using the script as direction and bringing natural variation in rooms, objects, clothing, and behavior.
          evidence:: E5
        - Annotation step: workers describe the observed video, verify object lists and action presence, and mark action start and end points to create temporal localization.
          evidence:: E6
    - **Design Decisions:** The central tradeoff is controlled diversity: the researchers restrict the vocabulary enough to benchmark actions, but leave the scene and paragraph construction open enough to preserve human variation. They also spend collection budget on recruitment, retention, and verification because filming is more inconvenient than ordinary annotation.
      evidence:: E4, E5, E6
        - Need: enough examples per category; design choice: seed scripts with curated rooms, objects, and actions; closest alternative: free web search or free-form filming; tradeoff: better control but bounded vocabulary.
          evidence:: E4
        - Need: realistic household scenarios; design choice: let workers compose short paragraphs with selected ingredients; closest alternative: lab-written scripts; tradeoff: more human bias and diversity but less precise semantic control.
          evidence:: E4, E7
        - Need: usable videos and labels; design choice: separate verification and exhaustive action annotation, especially for the test set; closest alternative: trust the recorder's self-report; tradeoff: higher cost for better label reliability.
          evidence:: E5, E6, E8
    - **Implementation Surface:** The implementation surface is a set of AMT tasks and interfaces rather than a new recognition algorithm: script writing, filming, line-up verification, object verification, action verification, and temporal interval labeling. The paper states that code and interfaces would be released with the dataset, but does not provide enough in-paper detail to reproduce the full worker workflow alone.
      evidence:: E5, E6
- ## Evaluation and Evidence
    - **Setup:** The evaluation uses a worker-disjoint train/test split and multi-label classification, meaning one video may contain several action labels, measured by mAP. Baselines include hand-crafted motion features, object-image convolutional neural network features, two-stream video networks, 3D convolutional features, late fusion, and sentence-prediction baselines evaluated with caption metrics.
      evidence:: E8, E9, E11
    - **Claim-Evidence Matrix:** The evidence is strongest for dataset construction and baseline difficulty, moderate for detailed failure analysis, and weakest for claims about long-term generalization beyond the collected household-script setting.
      claim_kind:: analyst_assessment
      evidence:: E1, E8, E9, E12
        - C1: supported by the reported collection pipeline, worker diversity, and dataset size, but the paper's realism claim is bounded by scripted acting rather than passive observation.
          claim_kind:: analyst_assessment
          evidence:: E1, E3, E5
        - C2: supported by the reported number of descriptions, action intervals, object labels, actions per video, and comparison to contemporary datasets.
          evidence:: E1, E6, E7, E14
        - C3: supported by low mAP for several standard baselines and by confusion among actions sharing objects or functionally similar objects.
          evidence:: E9, E10
        - C4: supported by caption metrics where S2VT is the strongest baseline but remains far below human captions, plus examples showing coherent but irrelevant outputs.
          evidence:: E11, E12
    - **Headline Results:** The headline result is that Charades is not saturated by then-standard action and captioning methods: late fusion is best among action baselines, but absolute action mAP is low, and S2VT remains well below human caption scores. The paper also finds that fine-grained object interactions drive many classification confusions.
      evidence:: E9, E10, E12
        - Action classification: Combined late fusion scores 18.6% mAP, IDT scores 17.2%, and Random scores 5.9%; this supports C3 but no variance or repeated-run uncertainty is reported.
          evidence:: E9
        - Object-interaction failure: the Combined baseline mostly confuses actions involving the same object, while actions without a specific object interaction reach 38.9% mAP; this sharpens C3.
          evidence:: E10
        - Sentence prediction: S2VT is the strongest baseline, but its CIDEr is 0.17 on scripts and 0.14 on descriptions versus human 0.51 and 0.53; this supports C4.
          evidence:: E12
    - **Ablations and Sensitivity:** The clearest sensitivity study is for IDT feature design: combining HOG, HOF, and MBH descriptors and using more Gaussian mixture components improves mAP. The paper does not provide a causal ablation of the collection pipeline itself, such as removing script constraints or changing verification depth.
      evidence:: E15
    - **Reproducibility Gaps:** Reported: dataset split sizes, label precision, baseline families, selected hyperparameters, and a promise to release code/interfaces. Not reported: random seeds, repeated runs, confidence intervals, hardware/resource budgets, exact AMT interface details, and complete training scripts inside the paper.
      claim_kind:: analyst_assessment
      evidence:: E5, E8, E9, E11, E15
- ## Technical Judgment
    - **What Holds Up:** The data-generation logic is coherent: a constrained vocabulary gives benchmark coverage, human-written scripts create plausible sequences, home recording adds environmental variation, and separate verification reduces label noise. The evaluation also cleanly connects the dataset's intended difficulty to baseline failures on multi-action recognition and caption relevance.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E6, E8, E9, E12
    - **Where It May Fail:** Benefits may diminish when the target behavior is unscripted, culturally specific, safety-critical, rare, or outside the curated indoor-object vocabulary. Generality is also limited by the fact that the empirical difficulty is shown with 2016 baselines and without statistical uncertainty.
      claim_kind:: analyst_assessment
      evidence:: E4, E5, E9, E12
    - **Relation to Other Work:** Compared with YouTube datasets such as UCF101, Sports1M, and ActivityNet, Charades trades natural upload behavior for controlled household coverage; compared with movie-description datasets, it removes entertainment editing; compared with in-house cooking or daily-living datasets, it scales diversity through distributed homes. The paper positions these sources as complementary rather than universally inferior.
      evidence:: E13, E14
    - **Transferable Lesson:** When naturally occurring data is missing, crowdsource the generative process, not just the labels: constrain the task enough to make benchmark categories reliable, then let many participants supply the variation that a lab cannot cheaply stage. This pattern transfers to other domains where the desired behavior is ordinary, private, or under-uploaded.
      claim_kind:: analyst_assessment
      evidence:: E3, E4, E5, E6
- ## Glossary
  collapsed:: true
    - activity understanding: Computer vision task of recognizing actions, object interactions, and temporal context in video.
    - crowdsourcing: Using many distributed workers to create, verify, or label data; in this paper it includes filming, not only annotation.
    - script: A short paragraph describing ordinary household actions that a worker acts out in a video.
    - temporal localization: Labeling when an action starts and ends inside a video, rather than only saying the action appears somewhere.
    - action class: A benchmark label for a type of action, often tied to an object interaction such as opening a refrigerator.
    - multi-label classification: Classification where one video can be assigned several action labels at the same time.
    - mean average precision: Ranking metric commonly used when each class has positives and negatives; higher is better.
    - Improved Dense Trajectories: A hand-crafted video feature method that tracks local motion patterns and encodes them for action recognition.
    - two-stream network: A video recognition model family that combines appearance information from frames with motion information across frames.
    - Sequence to Sequence - Video to Text: A video captioning baseline that combines convolutional visual features with a recurrent language model.
    - CIDEr: Caption similarity metric used to compare generated descriptions against human reference descriptions.
- ## Evidence Index
  collapsed:: true
    - **E1:** metadata/paper_statement | Abstract and The Charades v1.0 Dataset | high
      locator:: Abstract; Introduction dataset paragraph
      quote:: The dataset is composed of 9,848 annotated videos with an average length of 30 seconds, showing activities of 267 people from three continents, and over 15% of the videos have more than one person.
    - **E2:** problem/paper_statement | 1 Introduction | high
      locator:: Introduction, web-video bias discussion
      quote:: But how do we find these boring videos of our daily lives? If we search common activities such as drinking from a cup, riding a bike on video sharing websites such as YouTube, we observe a highly-biased sample of results.
    - **E3:** method/paper_statement | 1 Introduction | high
      locator:: Hollywood in Homes overview
      quote:: We take the Hollywood filming process to the homes of hundreds of people on Amazon Mechanical Turk. AMT workers follow the three steps of filming process: script generation; video direction and acting based on scripts; and video verification.
    - **E4:** method/implementation_detail | 2.1 Generating Scripts | high
      locator:: Script vocabulary and AMT prompt
      quote:: We found 15 types of rooms to cover most of typical homes. From movie-script term statistics we curated a list of 40 objects and 30 actions to be used as seeds for script generation.
    - **E5:** implementation/implementation_detail | 2.2 Generating Videos | high
      locator:: Worker recruitment, cost, and verification
      quote:: To maximize the diversity of scenes, objects, clothing and behaviour of people, we ask the workers themselves to record the 30 second videos by following collected scripts.
    - **E6:** method/implementation_detail | 2.3 Annotations | high
      locator:: Annotation procedure
      quote:: Using the generated scripts, all verb, preposition, noun triplets were analyzed, and the most frequent grouped into 157 action classes. For all the chosen action classes in each video, another set of workers was asked to label the starting and ending point.
    - **E7:** result/paper_statement | 3 Charades v1.0 Analysis | medium
      locator:: Dataset statistics and co-occurrence analysis
      quote:: Since we have control over the data acquisition process, instead of using Internet search, there are on average 6.8 relevant actions in each video. These actions occur in various orders and context, similar to our daily lives.
    - **E8:** experiment_setup/paper_statement | 4 Applications | medium
      locator:: Train/test split and label precision
      quote:: The resulting training and test sets contain 7,985 and 1,863 videos, respectively. The number of annotated action intervals are 49,809 and 16,691 for training and test. The label precision for the data is 95.6%.
    - **E9:** result/experiment_result | 4.1 Action Classification | medium
      locator:: Table 2 and baseline discussion
      quote:: Table 2 reports mAP for action classification: Random 5.9, C3D 10.9, AlexNet 11.3, Two-Stream-B 11.9, Two-Stream 14.3, IDT 17.2, and Combined 18.6.
    - **E10:** result/experiment_result | 4.1 Action Classification | medium
      locator:: Figure 7 discussion
      quote:: The majority of the confusion is among actions that interact with the same object, and there is confusion among objects with similar functional properties. Evaluation of action recognition on actions with no specific object of interaction results in 38.9% mAP.
    - **E11:** experiment_setup/paper_statement | 4.2 Sentence Prediction | high
      locator:: Task setup and baselines
      quote:: The dataset contains sentences that have been used to create the video, as well as multiple video descriptions obtained manually for recorded videos. Captions are evaluated using CIDEr, BLEU, ROUGE, and METEOR metrics.
    - **E12:** result/experiment_result | 4.2 Sentence Prediction | medium
      locator:: Table 4 and Figure 8 discussion
      quote:: Table 4 shows S2VT as the strongest baseline. Its CIDEr scores are 0.17 for script prediction and 0.14 for description prediction, while human performance is 0.51 and 0.53 respectively.
    - **E13:** prior_work/paper_statement | 1 Introduction | high
      locator:: Related dataset discussion
      quote:: Standard approaches in the past have used videos downloaded from the Internet, gathered from movies or recorded in controlled environments. Movies however are still exciting and do not capture the scenes, objects or actions of daily living.
    - **E14:** gap/paper_statement | 1 Introduction | medium
      locator:: Table 1
      quote:: Table 1 compares Charades with ActivityNet, UCF101, HMDB51, THUMOS, Sports 1M, MPII-Cooking, ADL, and MPII-MD across actions per video, classes, labelled instances, total videos, origin, type, and temporal localization.
    - **E15:** ablation/ablation | 4.1 Action Classification | medium
      locator:: Table 3
      quote:: Table 3 studies improved trajectories with HOG, HOF, MBH, descriptor combinations, and GMM cluster counts. Performance improves from 12.3 mAP with HOG at K=64 to 17.2 with HOG+HOF+MBH at K=256.
