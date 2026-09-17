# MaleCNS 与连接组学基础：带出处的结构化报告

> 目标读者：有神经科学/ML 背景、但从未接触过连接组（connectome）的人。
> 每条论断后附来源 URL。无法溯源者显式标注 **待核实**。
> 术语保留英文原文（body ID、neuropil、hemilineage 等）。

---

## 0. MaleCNS 数据卡（速查）

| 项 | 值 | 来源 |
|---|---|---|
| 全称 | Male CNS Connectome（MaleCNS / MCNS），成年雄蝇**全中枢神经系统**（脑 + 视叶 + 腹神经索 VNC，颈连接完整） | [male-cns.janelia.org](https://male-cns.janelia.org/) |
| 神经元数 | **166,691**（preprint 摘要）；门户与 MRC LMB 新闻作 **166,700** | [bioRxiv API 摘要](https://api.biorxiv.org/details/biorxiv/10.1101/2025.10.09.680999)；[Codex 数据集卡片](https://codex.flywire.ai/api/download)；[MRC LMB](https://mrclmb.ac.uk/news-events/articles/first-complete-connectome-of-male-fly-central-nervous-system-allows-for-unprecedented-male-female-brain-comparison/) |
| 细胞类型数 | **11,691**（preprint）/ **11,710**（正式发表） | 同上两条 |
| 版本 | v0.9 2025-10-05；**v1.0 2026-06-08**；Cell 正式发表 2026-09-03 | [Release Notes](https://male-cns.janelia.org/release/) |
| 论文 | Berg et al., *Sexual dimorphism in the complete connectome of the Drosophila male central nervous system*；bioRxiv 10.1101/2025.10.09.680999v2；Cell 2026 (S0092-8674(26)00942-6) | [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.10.09.680999v2)；[Cell](https://www.cell.com/cell/fulltext/S0092-8674\(26\)00942-6) |
| **体素分辨率（发布数据）** | **8 nm 各向同性**（对齐后的 EM 灰度体 + v1.0 神经元分割体都是 8 nm isotropic） | [Download 页](https://male-cns.janelia.org/download/)；Neuroglancer 场景 JSON `dimensions: {x:[8e-9,"m"], y:[8e-9,"m"], z:[8e-9,"m"]}` [场景文件](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json) |
| 其他体素分辨率 | 细胞核分割 16 nm 各向同性；脑 neuropil ROI 256 nm（max value 96）；VNC neuropil ROI 256 nm（max value 27） | [Download 页](https://male-cns.janelia.org/download/) |
| 成像方式 | 与 MaleCNS 同一标本的视叶连接组论文明确写 **focused ion beam milling + SEM (FIB-SEM)** | [Nern et al. 2025 Nature 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-025-08746-0%22&resultType=core&format=json)；[Janelia Optic Lobe 页](https://www.janelia.org/project-team/flyem/optic-lobe) |
| 成像像素/切片厚度（4×4×40 nm？） | **待核实**：门户只公布重建后的 8 nm 体素；未找到 MaleCNS 论文中可公开抓取的 4×4×40 nm 原文 | — |
| 性二态 | 114 dimorphic、262 male-specific、69 female-specific、7,205 isomorphic 类型（preprint）；Janelia 页面表述为「262 sex-specific + 114 sexually dimorphic，占中央脑 4.8%」 | [bioRxiv API](https://api.biorxiv.org/details/biorxiv/10.1101/2025.10.09.680999)；[Janelia Male CNS 页](https://www.janelia.org/project-team/flyem/male-cns-connectome) |
| 连接数（默认阈值下） | Codex 统计 **6,242,118** 条 connection（MCNS 默认 min = 5 synapses） | [Codex](https://codex.flywire.ai/api/download)、[Codex FAQ](https://codex.flywire.ai/faq) |
| 人力成本 | 「相当于 **44 年**人力」（AI + 人工 proofreading 合计） | [MRC LMB](https://mrclmb.ac.uk/news-events/articles/first-complete-connectome-of-male-fly-central-nervous-system-allows-for-unprecedented-male-female-brain-comparison/) |
| 许可 | CC-BY | [male-cns.janelia.org](https://male-cns.janelia.org/) |
| 访问 | neuPrint `male-cns:v1.0`、Clio、Codex（MCNS v1.0）、Neuroglancer、Google bucket `gs://flyem-male-cns/v1.0/` | [Explore](https://male-cns.janelia.org/explore/)、[Download](https://male-cns.janelia.org/download/) |

---

## 1. 什么是连接组？dense EM 连接组 vs mesoscale 投射连接组

### 1.1 connectome 的定义
- 连接组是「神经系统的接线图——神经元及其之间突触连接的地图」。FlyWire/Codex 的入门定义原文：*"A connectome is a wiring diagram of a brain or nervous system - a map of its neurons and the synaptic connections between them."* — [Codex](https://codex.flywire.ai/api/download)
- 连接组是**有向图**：节点=神经元，边=突触连接；边的属性包括突触数、所在区域（neuropil）、预测神经递质类型；节点属性包括层级分类、标识 label、递质预测、side 等。同一对节点可因不同脑区而存在多条边。 — [Codex FAQ](https://codex.flywire.ai/faq)
- FAFB 论文对「够格叫 connectome」的判据是：**整脑范围内神经元形态都被重建、主要通路被正确识别**。文中强调其重建"complete enough to deserve the name connectome"，并给出与 *C. elegans*（300 神经元、约 10⁴ 突触）和果蝇 1 龄幼虫（3,000 神经元、5×10⁵ 突触）的对比。 — [Dorkenwald et al. 2024, PMC11446842](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)

### 1.2 dense（稠密）vs sparse（稀疏）重建
- **Dense**：整个体积都被分割，数据集**力图包含每一个神经元**。
- **Sparse**：只有被人挑出来追踪的神经元才存在于数据集中；**「不存在」不能推出「动物体内没有」**。
- 来源：[Virtual Fly Brain — EM Imaging and Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)

### 1.3 dense EM 连接组 vs mesoscale 投射连接组（flycircuit / FlyLight）
关键差别有三层：**分辨率层级**（突触级 vs 投射级）、**覆盖方式**（稠密 vs 稀疏/驱动系）、**是否给出突触计数**。

| 维度 | dense EM 连接组（MaleCNS / FAFB / hemibrain） | mesoscale（FlyCircuit / FlyLight） |
|---|---|---|
| 成像 | 电子显微镜，平面分辨率约个位数 nm | 光学显微镜（共聚焦），单细胞或驱动系表达模式 |
| 数据单元 | 每一个神经元 + 每一处突触 | 每个图像一个被分割的神经元（FlyCircuit）或一个 GAL4/LexA/split-GAL4 表达模式（FlyLight） |
| 是否给出突触计数 | 是（edge weight = 突触数） | 否 |
| 规模 | MaleCNS 166,691 神经元；FAFB 139,255 神经元 | FlyCircuit 1.0（Chiang2010）在 VFB 有 **16,127** 条单神经元记录 |
| 覆盖 | 稠密（全脑/全 CNS） | 稀疏抽样，且是**投射形态**而非连接 |

- FlyCircuit：Chiang lab 用 GAL4 系随机标记（stochastic labelling）产生**单神经元**图像集，「每张图一个被分割的神经元」；NBLAST 最初就是针对它开发的。 — [VFB FlyCircuit 文档](http://raw.larval.flylight.virtualflybrain.org/docs/data/lm/flycircuit/)
- FlyLight：生产 GAL4/LexA/**Split-GAL4 驱动系**大规模解剖数据集，目标是覆盖绝大多数细胞类型；已发布 3,060 个成体 + 1,373 个幼虫细胞类型特异性 split-GAL4 系，以及约 **74,000** 张单神经元 GAL4（Gen1 MCFO）图像。NeuronBridge 用来在 LM 与 EM 之间做形态检索。 — [Janelia FlyLight](https://www.janelia.org/project-team/flylight)；[NeuronBridge 说明](https://www.janelia.org/project-team/flyem/male-cns-connectome)
- **两种数据的接口**：MaleCNS 官方推荐用 NeuronBridge 把 FlyLight 目录（或自己的 LM 图像）匹配到 MaleCNS 的 EM 神经元，并用 `navis`/`VVDViewer` 把 LM 与 EM 叠加。 — [Janelia Male CNS 页](https://www.janelia.org/project-team/flyem/male-cns-connectome)
- **不可混用的理由（关键教学点）**：edge 是「某个重建报告了这两个神经元之间的突触，以及有多少个」，是**某一个数据集的证据，不是生物学事实**。部分重建中真实存在的连接可能缺失；弱 edge 可能是分割伪影。任何计数都必须归属于它来自的那个连接组。 — [VFB Connectivity Data](https://www.virtualflybrain.org/docs/data/connectivity/)

---

## 2. 现代 EM 连接组流水线（逐步）

VFB 把流程概括为四段：**固定并切片 → 在能看到突触的分辨率下成像 → 判定体素属于哪个神经元 → 判定哪两个神经元相连**。并强调：*"Each stage introduces its own kind of error, and knowing which stage a number came from is most of what you need to interpret it."* — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)

### 2.1 组织制备 / 染色 / 包埋
- FlyEM 的 hemibrain 样本制备方法引自其公开 protocol（biorxiv 855130）。 — [Janelia Hemibrain 页「Technologies」](https://www.janelia.org/project-team/flyem/hemibrain)
- MaleCNS 的样本为 5 日龄雄蝇，wildtype Canton S × w¹¹¹⁸ 杂交后代，12 h 昼夜节律饲养（检索片段；原文出处为 MaleCNS 论文 Methods）。 — **待核实**（无法直接抓取 MaleCNS 论文正文；该句来自搜索引擎索引到的 MaleCNS/相关 biorxiv Methods 片段）

### 2.2 切片 + 成像：ssTEM / SBEM / FIB-SEM 三条技术路线
- **ssTEM（serial-section TEM）**：组织被物理切成超薄切片，再用透射电镜逐张成像。并行成像使 TEM 最快，因此最先扩展到全脑：**FAFB 切片厚度 40 nm，平面成像 4 × 4 nm**。代价是切片可能丢失、折叠、形变，且切片厚度决定粗糙的 z 分辨率。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)，引 [Zheng et al. 2018 Cell](https://doi.org/10.1016/j.cell.2018.06.019)、[Bock et al. 2011 Nature](https://doi.org/10.1038/nature09802)
- **FIB-SEM**：聚焦离子束削掉极薄一层，成像 block face，循环往复——**没有物理切片可丢**，z 分辨率接近各向同性。历史问题是慢；enhanced FIB-SEM + **hot-knife**（把脑切成厚 slab 分别成像再拼接）使其可用于大体积。**hemibrain、MANC、optic lobe 体积都是 FIB-SEM。** — 同上，引 [Hayworth et al. 2015 Nat Methods](https://doi.org/10.1038/nmeth.3292)、[Xu et al. 2017 eLife](https://doi.org/10.7554/eLife.25916)
- **Hemibrain 实例**：用 hot knife 把脑切成较厚 slab，每片用 FIB-SEM 成像，得到**纳米级各向同性**数据，再把不同切片的图像仔细拼接，目标是把边界像差降到最低。 — [Janelia Hemibrain 页](https://www.janelia.org/project-team/flyem/hemibrain)
- **SBEM（serial block-face SEM）**：Denk & Horstmann 2004 提出，VFB 明确说明在这批果蝇数据集里**较少使用**。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)
- 注意：VFB 数据集页把 MaleCNS 的 Imaging Technique 标为 **serial block face SEM (SBFSEM)**，而同一标本的视叶论文写 FIB-SEM。 — [VFB male-cns 数据集页](http://www.virtualflybrain.org/blog/2022/01/01/male-cns-berg2025/) vs [Nern et al. 2025](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-025-08746-0%22&resultType=core&format=json)。这两条元数据冲突，**建议以论文 Methods 为准（待核实）**。

### 2.3 图像对齐（alignment）
- FAFB 图像在 FlyWire 分割时被**重新对齐**，因此同一坐标在原始 FAFB（FAFB14）与 FlyWire（FAFB14.1）之间通常相差约 1 μm；两个空间之间有形变场可以互相映射。 — [fafbseg 文档](https://fafbseg-py.readthedocs.io/en/latest/source/intro.html)
- 多切片/多 slab 的「仔细拼接」本身是成像流程的一环，目的是降低边界像差。 — [Janelia Hemibrain 页](https://www.janelia.org/project-team/flyem/hemibrain)

### 2.4 分割（segmentation）与 agglomeration
- 早期重建是**人工逐节点描骨架**，CATMAID 为此而生（Saalfeld 2009；Schneider-Mizell 2016）。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)
- 现代重建自动优先：**flood-filling networks** 迭代地生长预测对象来分割神经元（[Januszewski et al. 2018 Nat Methods](https://doi.org/10.1038/s41592-018-0049-4)）。输出从来不是正确的，含两类错误：
  - **split**：一个神经元被切碎成多块；
  - **merge**：两个神经元被融合成一个。
- Codex 的描述：cell segments 由 AI 从 EM 图像自动生成，cell reconstructions 由 FlyWire 社区从 segments **拼装（proofread）**。 — [Codex About FlyWire](https://codex.flywire.ai/about_flywire)
- 在 FlyWire 底层（chunkedgraph，类八叉树结构）里，**supervoxel 是不可变的原子单位，root ID 是 supervoxel 的集合**；任何编辑（增删 supervoxel）都产生新的 root ID。这就是「agglomeration」在数据模型上的样子。 — [fafbseg: FlyWire segmentation 教程](https://fafbseg-py.readthedocs.io/en/latest/_sources/source/tutorials/flywire_segments.rst.txt)
- FlyEM 的工程经验（top-down 策略）：先人工标注 >100,000 个 soma；取覆盖约 25% 预测突触的最大 segment 作为 working set（约 100 万 segment）；取其最大者作 anchor set（约 30 万）；对 anchor 做大范围 false merge 检查与 cleaving；再 focus proofread 决策。 — [Janelia: Recipe for a Connectome](https://www.janelia.org/project-team/flyem/blog/recipe-for-a-connectome)

### 2.5 突触检测（synapse detection）与突触伙伴预测
- 突触与形态是**分开标注**的。果蝇的突触靠超微结构识别：**presynaptic T-bar** 与其对面的 postsynaptic profile；在全脑尺度上由分类器而非人眼完成（[Buhmann et al. 2021 Nat Methods](https://doi.org/10.1038/s41592-021-01183-7)）。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)
- FlyWire 现状：突触由 **[Yu et al. 2025](https://www.biorxiv.org/content/10.1101/2025.07.11.664377v1)** 的方法检测（"Princeton synapses"）；在此之前发布的突触由 **[Buhmann et al. 2021](https://www.nature.com/articles/s41592-021-01183-7)** 预测，并用 **[Heinrich et al. 2018](https://link.springer.com/chapter/10.1007/978-3-030-00934-2_36)** 精修。 — [Codex About FlyWire](https://codex.flywire.ai/about_flywire)
- Yu et al. 2025 的量化改进：在最困难区域 **F-score 最多提高 0.23**；控制区域性能保持；在细胞类型内的神经元聚类提升 **8–9%**；仅凭连接模式预测神经元类型归属的加权 F-score 从 Buhmann 的 **0.91 提升到 0.93**。 — [Yu et al. 2025 摘要](https://www.biorxiv.org/content/10.1101/2025.07.11.664377v1)
- MaleCNS 侧：**「与之前的重建一样，我们收集了独立的 validation ground-truth 来评估突触识别性能」**，Fig. S8E 给出 T-bar 单独与「以突触为单位（pre/post 两个成分都正确预测）」的 precision-recall 曲线。 — MaleCNS 论文（[Cell](https://www.cell.com/cell/fulltext/S0092-8674\(26\)00942-6)／[ScienceDirect 索引片段](https://www.sciencedirect.com/science/article/pii/S0092867426009426)）；具体 PR 数值 **待核实**
- **可验证的旁证**：MaleCNS v1.0 的 Neuroglancer 场景里**确实带有官方突触 ground-truth 图层** `malecns-v1.0-synapse-ground-truth-lines` 与 `-boxes`，以及 `synapse-groundtruth`。 — [场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)

### 2.6 proofreading（人工校对）
见第 8 节。

### 2.7 注释（annotation）
- MaleCNS 的细胞体注释以 **16 nm 核分割**为基础，「经过人工复核」。 — [Download 页](https://male-cns.janelia.org/download/)
- FlyWire 的层级注释（side、flow、super class、cell class、cell type、Hemibrain type、nerve、hemi-lineage）由 **Schlegel et al.（Jefferis lab）** 提供；递质类型由 **Eckstein, Bates et al.** 预测；NBLAST 形态相似度分数由 Philipp Schlegel 计算。 — [Codex About FlyWire](https://codex.flywire.ai/about_flywire)
- **细胞分型是「加上的」，不是「观测到的」**：EM 神经元上的 type 是把形态与连接跟已知类型比对后做出的注释。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)

### 2.8 分辨率汇总

| 数据集 | 成像方式 | 成像平面/切片 | 发布/计算用体素 | 来源 |
|---|---|---|---|---|
| FAFB（Zheng et al. 2018） | ssTEM | **4 × 4 nm 平面，40 nm 切片** | FlyWire 视图用 **4, 4, 40 nm** 坐标系 | [VFB](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)；[Codex FAQ](https://codex.flywire.ai/faq) |
| hemibrain | enhanced FIB-SEM + hot knife | 纳米级各向同性 | **8×8×8 nm** | [Janelia Hemibrain](https://www.janelia.org/project-team/flyem/hemibrain)；[navis-flybrains 源码注释](https://raw.githubusercontent.com/navis-org/navis-flybrains/refs/heads/main/flybrains/core.py) |
| MANC | FIB-SEM | — | **8×8×8 nm** | [VFB](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)；[navis-flybrains](https://raw.githubusercontent.com/navis-org/navis-flybrains/refs/heads/main/flybrains/core.py) |
| **MaleCNS** | FIB-SEM（与视叶同一标本） | **待核实**（未找到 4×4×40 的原文） | **8×8×8 nm**（对齐 EM 与 v1.0 分割均为 8 nm isotropic） | [Download 页](https://male-cns.janelia.org/download/)；[场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json) |

> 关键概念：**「成像分辨率」≠「数据体素分辨率」**。FAFB 是 4×4×40 各向异性成像，但下游常以 4/4/40 或重采样网格存储；FlyEM 数据集把体素各向同性化到 8 nm 后再做分割与发布。

---

## 3. ID、突触、连接、权重、min confidence、≥5 阈值

### 3.1 body ID / root ID / segment ID

| 名称 | 是什么 | 会不会变 | 来源 |
|---|---|---|---|
| **root ID** | FlyWire 里一个**神经元**的 ID（例如 `720575940618780781`）。它是一组 **supervoxel** 的集合。 | **会变**：每次编辑（merge/split）都生成新 root ID，并使旧 root ID 失效。旧 ID 不会被删除，仍能在 neuroglancer 里调出 mesh，但可能与你手上的元数据版本不共存。 | [fafbseg 教程](https://fafbseg-py.readthedocs.io/en/latest/_sources/source/tutorials/flywire_segments.rst.txt) |
| **segment ID** | 一般指分割体里的一个标签值（voxel label）。在 FlyWire 语境下 "segments" 常和 root ID 混用，但**原子单位是 supervoxel**；`locs_to_supervoxels` → `supervoxels_to_roots` 是显式的两级映射。 | supervoxel 不可变；segment/root 标签可变 | 同上 |
| **body ID** | Janelia neuPrint/FlyEM 体系的神经元 ID（例：hemibrain `bodyId` 5813027016；MaleCNS 场景里属性名是 `body_pre_u32` / `body_post_u32`）。语义 = 一个「body」（一段完整的神经元重建）。 | 随数据集版本变化 | [neuprint-python Queries](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)；[MaleCNS 场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json) |

**为什么 ID 会随版本变化**：proofreading 不断进行，数据集以「快照/物化」形式发布。FlyWire 用 **materialization**（几乎每晚一次的快照）把「注释 ↔ 坐标 ↔ 当前 root ID」绑定起来。若某 root ID 比最新 materialization 更新、只在两次物化之间短暂存在、或从未在任何物化中共存，查询元数据就会出问题。**实践建议：选定一个 materialization 并全程使用**。 — [fafbseg 教程](https://fafbseg-py.readthedocs.io/en/latest/_sources/source/tutorials/flywire_segments.rst.txt)

**为什么 MaleCNS 与 FlyWire 的 ID 不可互换**（三条独立理由，都可溯源）：
1. **不同的分割后端与 ID 命名空间**。FlyWire 用 CAVE/chunkedgraph 的 root ID（数十位大整数）；MaleCNS 用 neuPrint 的 `bodyId`（如 17920、65161、12781 这种小整数）与 `body_pre_u32`。 — [fafbseg](https://fafbseg-py.readthedocs.io/en/latest/_sources/source/tutorials/flywire_segments.rst.txt)；[neuprint-python](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)；[MaleCNS 场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)
2. **不同个体、不同性别**。MaleCNS 是一个雄蝇；FlyWire FAFB 是一个雌蝇。存在 sex-specific / dimorphic 类型（男 262 + 114 vs 女 69），连「同一类型」都不一定一一对应。 — [bioRxiv 摘要](https://api.biorxiv.org/details/biorxiv/10.1101/2025.10.09.680999)
3. **跨数据集只能靠坐标变换后的形态/连接匹配，不能靠 ID**。MaleCNS 官方把 FlyWire v783、hemibrain v1.2.1、MANC v1.2、BANC 的 mesh **变换到 MaleCNS 空间**后作为共视图层提供；跨空间的变换由 `navis-flybrains` 提供。也就是说，官方给的桥是**空间变换 + 形态/连接匹配**，不是 ID 映射。 — [Explore 页](https://male-cns.janelia.org/explore/)；[Download 页](https://male-cns.janelia.org/download/)；[场景 JSON 中的 `flywire-meshes`/`hemibrain-meshes`/`manc-meshes`/`banc-meshes`](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)
   - 补充：连 FAFB 内部两套分割（FlyWire 与 Google）的 ID 也不同；FAFB14 与 FlyWire 坐标还差约 1 μm。 — [fafbseg](https://fafbseg-py.readthedocs.io/en/latest/source/intro.html)
   - 补充：FlyWire 有自己的版本间 ID 映射工具（Codex → Tools → **Map Root IDs**）；MaleCNS 目前没有对外开放的同类跨版本映射工具说明。 — [Codex FAQ](https://codex.flywire.ai/faq)

### 3.2 connection vs synapse vs weight

- **synapse（突触）**：一个 pre 位置与一个 post 位置之间的**一条连接**。FAFB 论文的图注定义得极清楚：*"Synaptic boutons in the fly brain are often polyadic such that there are multiple postsynaptic partners per presynaptic bouton. **Each link between a pre- and a postsynaptic location is a synapse.**"* — [Dorkenwald et al. 2024, PMC11446842 Fig.1e 图注](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)
- **connection（连接）/ edge（边）**：一对神经元之间的**一条有向边**，其权重是该对之间被检出的**突触个数**。
  - Codex 的判据：*"Connectivity is directed: an edge goes from the presynaptic cell to the postsynaptic cell. A pair of cells is considered connected when the total synapse count for that pair meets the selected minimum threshold."* — [Codex FAQ](https://codex.flywire.ai/faq)
  - neuPrint 的 `:ConnectsTo` 边属性 `weight` = 该 body 对的连接强度（突触数）；ROI 分层会让同一批突触在 `roi_counts_df` 里被**重复计数**（因为在层级 ROI 中一个突触会落在多个 ROI 内）。 — [neuprint-python Queries](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)
- **weight（权重）**：就是突触计数，不是「概率」也不是「电流」。neuPrint 还提供更细的权重族：`weightHP`（high-precision，只统计置信度高于数据集 `preHPThreshold`/`postHPThreshold` 的突触）、`weightAxonAxon`、`weightAxonDendrite`、`weightDendriteDendrite`、`weightDendriteAxon`（后四个只在有 axon/dendrite 极性信息的数据集里存在）。 — [neuprint-python Queries](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)、[fetch_meta 字段列表](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)

**为什么「突触数」≠「连接数」（数量级差异，可直接引用）**
- FAFB：**139,255 个神经元之间约 5,450 万（54.5 M）个突触**； — [Dorkenwald et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)
- 同一数据集在 Codex 数据集卡片上只有 **3,732,460 条 connection** ——因为那里的「connection」是**满足默认 ≥5 突触阈值的边数**。 — [Codex](https://codex.flywire.ai/api/download)、[Codex FAQ](https://codex.flywire.ai/faq)
- 也就是说：**synapse count 是「点对数」，connection count 是「去重后的细胞对 + 阈值过滤后的边数」**。同一个数据集，换个阈值就得到不同的 connection 数，这正是这个区分最好的教学演示。

### 3.3 「min confidence」与「≥5 synapses」

- **min confidence**：突触检测器对每个突触点输出的置信度分数，按阈值过滤。可溯源的具体证据：
  - MaleCNS v1.0 **所有连通性导出文件的文件名都带 `-minconf-0.5`**（`body-annotations-...-minconf-0.5.feather`、`body-stats-...-minconf-0.5.feather`、`connectome-weights-...-minconf-0.5.feather`、`syn-points-...-minconf-0.5.feather`、`syn-partners-...-minconf-0.5.feather`），即这些表是按**置信度阈值 0.5** 导出的。 — [Download 页](https://male-cns.janelia.org/download/)
  - 每个突触点带两个置信度字段：`syn-partners` 表的列 `conf_pre`、`conf_post`；`syn-points` 表按 pre/post 分行并用 `kind` 列区分 `PreSyn`/`PostSyn`。 — [Download 页](https://male-cns.janelia.org/download/)
  - 场景里还直接暴露 `predicted_nt_prob`（递质概率）与 **`nt_tbar_confidence_score`**（T-bar 层面的置信度）两个属性。 — [场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)
  - neuPrint 侧的对应物是 `weightHP` + 元数据里的 `preHPThreshold` / `postHPThreshold`（"high precision" 阈值）。 — [neuprint-python Queries / fetch_meta](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)
  - **官方没有逐字定义 `minconf-0.5` 这个数的含义**（是 cleft score？是 pre/post 置信度取 min？）→ **待核实**
- **≥5 synapses 阈值**：把「突触计数 < 5 的细胞对」从连接图里删掉。Codex 给出的**各数据集默认最小阈值**是数据集相关的：

| 数据集 | 默认最小突触数 |
|---|---|
| FAFB (FlyWire) | **5+** |
| BANC | **3+** |
| MANC | **1+** |
| MAOL（雄性视叶） | **1+** |
| **MCNS（MaleCNS）** | **5+** |
来源：[Codex FAQ](https://codex.flywire.ai/faq)

- **为什么弱边要砍掉**：*"An edge is a count of detected synapses, subject to both false positives and misses. **Weak edges (one or two synapses) are the least reliable and are commonly thresholded out.**"* 另外 **connectivity 会继承分割错误**：一次 merge 会凭空造出动物体内不存在的连接，一次 split 会把一个神经元的连接分给两个对象。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)
- VFB 层面「跨数据集连接查询」的默认权重阈值也是 **5 synapses**，「除非你准备逐条去看那些弱边」。 — [VFB Connectivity Data](https://www.virtualflybrain.org/docs/data/connectivity/)
- Codex 允许**提高**阈值但不能低于数据集默认值；Connection/Pathways 工具遵守此限制。 — [Codex FAQ](https://codex.flywire.ai/faq)

---

## 4. Neuropil（神经毡区）与缩写表

### 4.1 什么是 neuropil，在 FlyEM 数据里如何定义
- neuropil 是**突触发生所在的区域**（相对地，soma/cell body 层与纤维束 tract 是另外的解剖分区）。FAFB 论文把果蝇脑**基于 neuropil 划分为空间上定义的区域**。 — [Dorkenwald et al. 2024 Fig.1d](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)
- 注释是**继承 + 人工精修**得到的，不是自动生成的：MaleCNS 的脑 neuropil 分区「由 JRC2018M 模板中的 ROI 迁移初始化，再人工精修」；VNC 分区「人工精修」。 — [Download 页](https://male-cns.janelia.org/download/)；MaleCNS 论文同一表述见 [Cell 索引片段](https://www.cell.com/cell/fulltext/S0092-8674\(26\)00942-6)
- ROI 是**层级结构（hierarchy）**：一个突触可能同时落在多个 ROI 里 → 按 ROI 汇总会重复计数。neuPrint 用「primary ROI」（互不重叠）来避免这一点。 — [neuprint-python Queries](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)
- **MaleCNS v1.0 实际的分区规模**（直接数 Neuroglancer 场景中的 ROI 图层）：
  - `fullbrain-roi-v5`（脑 neuropil 主分区）：segment 值 1–86, 93, 94, 96 → **约 90 个脑 ROI**
  - `malecns-subcompartments-v3`（亚分区）：约 200 个段值 → 脑区亚隔间
  - `malecns-vnc-neuropil-roi-v0`：段值 5–27 → **23 个 VNC neuropil**
  - `malecns-vnc-nerve-roi-v2`：段值 2–37 → **36 条 nerve**
  - 还有 optic lobe 的 `ME(R/L)-columns/layers`、`LO`、`LOP`、`OL(R)-v0`，以及 `brain-defects` / `vnc-defects`（已知数据缺陷区）
  - 来源：[场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)
  - 与 Download 页一致：脑 ROI 体积 max value 96、VNC ROI 体积 max value 27 → 约 90 个脑区、23 个 VNC 区。 — [Download 页](https://male-cns.janelia.org/download/)

### 4.2 入门必需的 6 个 neuropil（含功能一句话）

| 缩写 | 全称 | 一句话功能 | 来源 |
|---|---|---|---|
| **AL** | antennal lobe 触角叶 | 嗅觉第一级中枢，嗅觉受体神经元在此换元给投射神经元 | [neuprint-python 的 hemibrain ROI 树](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)（AL(L)/AL(R) 为 primary ROI）；FAFB 论文把嗅觉环路列为经典分析对象 [PMC11446842](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/) |
| **MB** | mushroom body 蘑菇体 | 嗅觉学习与记忆的核心；Kenyon cell 为内在神经元；ROI 树里进一步分为 CA(calyx)、aL、a'L、bL、b'L、gL（即 α/α'/β/β'/γ 叶） | 同上（ROI 树示例含 CA、aL、a'L、bL、b'L、gL、PED） |
| **CX** | central complex 中央复合体 | 导航与运动控制；含 **EB**（ellipsoid body 椭球体）、**FB**（fan-shaped body 扇形体）、**NO**（noduli 小结）、**PB**（protocerebral bridge 脑桥）、**AB**（asymmetric body） | 同上（hemibrain ROI 树 `CX → AB/EB/FB/NO/PB`） |
| **SEZ / GNG** | subesophageal zone 食管下区 / gnathal ganglia 颚神经节 | 味觉、机械感觉等多种功能；SEZ 是 FAFB 相对 hemibrain 的关键增益区，也是下行神经元胞体所在 | [Dorkenwald et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)；neuprint-python ROI 树列出 `GNG*` |
| **LA / ME / LO / LOP** | lamina 薄板 / medulla 髓质 / lobula 小叶 / lobula plate 小叶板（FBbt 规范缩写就是 **LA/ME/LO/LOP**；常见的 LAM/MED/LOB 不是规范写法） | 视叶四层；MaleCNS 的 ROI 图层里 ME、LO、LOP 都按 **column（柱）+ layer（层）** 细分，左右半球各自一套 | [场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)；全称见 4.4 节的 FBbt 核验表 |
| **VNC / GNG** | ventral nerve cord 腹神经索（= 昆虫的「脊髓」） | MaleCNS 覆盖脑 + 视叶 + VNC 且颈连接完整；VNC neuropil 分 23 区、nerve 36 条 | [male-cns.janelia.org](https://male-cns.janelia.org/)；[Download 页](https://male-cns.janelia.org/download/)；[场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json) |

### 4.3 其他会在 MaleCNS/hemibrain 里碰到的缩写

neuPrint 官方文档直接打印出的 hemibrain ROI 层级片段（可视为「标准列表的一部分」）：
```
hemibrain
 +-- AL(L)*   +-- AL(R)*   +-- AOT(R)
 +-- CX
 |   +-- AB(L)*  +-- AB(R)*  +-- EB*  +-- FB*  +-- NO*  +-- PB*
 +-- GC      +-- GF(R)     +-- GNG*    +-- INP
```
来源：[neuprint-python Queries 的 `fetch_roi_hierarchy` 示例输出](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)（`*` = primary ROI）

### 4.4 经 FBbt 本体核验的缩写 → 全称 → 功能表

> **核验方法（可复现）**：FBbt（果蝇解剖本体）把 Ito-2014 的 neuropil 缩写存为 `exact_synonym`，其中很多被标为 **"BrainName official abbreviation"**。可以直接查 EBI OLS4 API：
> `https://www.ebi.ac.uk/ols4/api/search?q=<TERM>&ontology=fbbt&rows=N&fieldList=label,obo_id,exact_synonyms,description`
> 下表每一行都是这样核验出来的（不是从二手资料抄的）。

| 缩写 | 全称（FBbt ID） | 一句话功能 | 来源 |
|---|---|---|---|
| AL | antennal lobe 触角叶（adult FBbt:00007401；syn. AL、adult olfactory lobe） | 嗅觉一级中继；嗅神经的 glomerular 靶区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=adult%20antennal%20lobe&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| MB | mushroom body 蘑菇体（FBbt:00005801；syn. MB、corpora pedunculata） | 联想学习与记忆；Kenyon cell 系统 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=mushroom%20body&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| CA | mushroom body calyx 蘑菇体萼（FBbt:00003685；**BrainName official abbreviation**） | Kenyon cell 的主要树突输入区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=mushroom%20body%20calyx&ontology=fbbt&rows=5&fieldList=label,obo_id,exact_synonyms) |
| PED | mushroom body pedunculus 蘑菇体柄（FBbt:00003687） | Kenyon cell 轴突束：萼 → 各叶 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=mushroom%20body%20pedunculus&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| aL / bL / a'L / b'L / gL（α/β/α′/β′/γ 叶） | adult MB alpha-lobe FBbt:00110657、beta FBbt:00110658、alpha′ FBbt:00013691、beta′ FBbt:00013694、gamma FBbt:00013695；hemibrain ROI 字符串就是 `aL(R) bL(R) a'L(R) b'L(R) gL(R)` | MB 输出叶；α/β 与 α′/β′/γ 是两股 Kenyon cell 流 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=alpha%20lobe&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms)；[neuprint-python](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html) |
| SEZ | subesophageal zone 食管下区（FBbt:00051068；adult FBbt:00110639） | 味觉/摄食的运动前区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=adult%20subesophageal%20zone&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| GNG | gnathal ganglion 颚神经节（FBbt:00004013；syn. GNG、SOG、SEG、subesophageal ganglion）—— **GNG 是 hemibrain 的 ROI 名** | 与 SEZ 等价的神经节 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=gnathal%20ganglion&ontology=fbbt&rows=5&fieldList=label,obo_id,exact_synonyms) |
| AMMC | antennal mechanosensory and motor center 触角机械感觉与运动中心（FBbt:00003982；syn. AMMC、AMC） | Johnston 器/风感毛的机械感觉靶区；位于 saddle 内 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=antennal%20mechanosensory%20and%20motor%20center&ontology=fbbt&rows=3&fieldList=label,obo_id,exact_synonyms) |
| LA | lamina 薄板（FBbt:00003708；syn. LA、La） | 视叶第一层；R1–R6 终末与 cartridge | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=lamina&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| ME | medulla 髓质（FBbt:00003748；syn. ME、Med） | 视叶第二层；运动/方向柱 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=medulla&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| LO | lobula 小叶（FBbt:00003852；syn. LO、Lob） | 视叶第三层；物体运动 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=lobula&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| LOP | lobula plate 小叶板（FBbt:00003885；syn. LOP、LoP） | 宽场运动/视动反应 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=lobula%20plate&ontology=fbbt&rows=3&fieldList=label,obo_id,exact_synonyms) |
| AME | accessory medulla 副髓质（FBbt:00045003；syn. AME、aMe） | 昼夜节律起搏器；Hofbauer–Buchner eyelet 的靶区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=accessory%20medulla&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| AOTU | anterior optic tubercle 前视结节（FBbt:00007059；syn. AOTU、OTU、OPTU）；外侧区 AOTUl / L-AOTU（FBbt:00047046）；hemibrain ROI `AOT(R)` | 偏振光/颜色信息向中央复合体的中继 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=anterior%20optic%20tubercle&ontology=fbbt&rows=3&fieldList=label,obo_id,exact_synonyms) |
| CX | central complex 中央复合体（hemibrain 复合 ROI；子区 = AB/EB/FB/NO/PB） | 朝向/转向/记忆中枢 | [neuprint-python](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html) |
| EB | ellipsoid body 椭球体（FBbt:00003678） | CX 朝向计算/环形吸引子输出 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=ellipsoid%20body&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| FB | fan-shaped body 扇形体（FBbt:00003679；syn. FB、fb） | CX 分层的正中 neuropil；睡眠/转向 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=fan-shaped%20body&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| NO | nodulus 小结（FBbt:00003680；syn. NO、no、Nod、ventral tubercle） | CX 输出；有 NO1/NO2/NO3 亚区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=nodulus&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| PB | protocerebral bridge 脑桥（FBbt:00003668；**BrainName official abbreviation**，syn. PCB） | CX 柱状输入，18 个 glomeruli | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=protocerebral%20bridge&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| AB | asymmetrical body 不对称体（FBbt:00110172；左右分别为 00051239 / 00051240） | CX 相关，左右不对称 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=asymmetric%20body&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| SMP | superior medial protocerebrum 上内侧原脑（FBbt:00007055） | 高阶多模态联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=superior%20medial%20protocerebrum&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| SLP | superior lateral protocerebrum 上外侧原脑（FBbt:00007054） | 高阶视觉/嗅觉联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=superior%20lateral%20protocerebrum&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| SIP | superior intermediate protocerebrum 上中间原脑（FBbt:00045032） | SMP/SLP 之间的联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=superior%20intermediate%20protocerebrum&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| INP | inferior neuropils 下神经毡（FBbt:00040037；syn. INP、inferior protocerebrum） | 下原脑集合 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=inferior%20neuropils&ontology=fbbt&rows=5&fieldList=label,obo_id,exact_synonyms) |
| IPS | inferior posterior slope 下后斜坡（FBbt:00045046；syn. VMCpov） | 后腹侧原脑区域 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=inferior%20posterior%20slope&ontology=fbbt&rows=5&fieldList=label,obo_id,exact_synonyms) |
| SPS | superior posterior slope 上后斜坡（FBbt:00045040；syn. VMCpod） | 后背侧原脑区域 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=superior%20posterior%20slope&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| AVLP | anterior ventrolateral protocerebrum 前腹侧原脑（FBbt:00040043） | 听觉/机械感觉联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=anterior%20ventrolateral%20protocerebrum&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| PVLP | posterior ventrolateral protocerebrum 后腹侧原脑（FBbt:00040042） | 视觉/机械感觉联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=posterior%20ventrolateral%20protocerebrum&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| PLP | posterior lateral protocerebrum 后外侧原脑（FBbt:00040044） | 后部联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=posterior%20lateral%20protocerebrum&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| CRE | crepine（adult FBbt:00045037；syn. CRE、IPa）；hemibrain `CRE(R)`、`CRE(-ROB,-RUB)(R)` | MB 旁的运动前/联合区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=adult%20crepine&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| LAL | lateral accessory lobe 侧副叶（adult FBbt:00003681；syn. LAL、vbo、ventral body） | CX 的运动前输出 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=adult%20lateral%20accessory%20lobe&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| ICL | inferior clamp 下夹（FBbt:00040049；syn. DMP、IPv、ventral inferior protocerebrum） | CX 邻接的 clamp/bridge 复合体 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=inferior%20clamp&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| SCL | superior clamp 上夹（FBbt:00040048；syn. SPP） | CX 邻接 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=superior%20clamp&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| IB | inferior bridge 下桥（FBbt:00040050） | CX 邻接 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=inferior%20bridge&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| BU | bulb 球（FBbt:00003682；**BrainName official abbreviation**；syn. ltr、IST、mimpr） | 约 80 个 microglomeruli；AOTU → CX 中继 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=bulb&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| GA | gall 虫瘿（FBbt:00040060；syn. GA，IDFP 的背/腹 spindle bodies） | CX 邻接 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=gall&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| ATL | antler 鹿角（FBbt:00045039） | 从 inferior bridge 延伸到 SLP 边缘的薄区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=antler&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| WED | wedge 楔（FBbt:00045027；syn. WED、IVLP、VLCi、inferior VLP = inferior ventrolateral protocerebrum） | 最腹侧的 VLP 区；接收 AMMC 输入 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=wedge&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| SAD | saddle 鞍（FBbt:00045048） | 覆盖 gnathal ganglia；内含 AMMC | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=saddle&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| **FLA** | **flange 凸缘（FBbt:00045050；syn. TRd = dorsal tritocerebrum 背侧三分脑）** | 位于前 saddle 之上、median bundle 根部 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=flange&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| **PRW** | **prow 船首（FBbt:00040051；syn. TRv = ventral tritocerebrum 腹侧三分脑）** | 食管下方最前/最上方的区域；含 superior pharyngeal sensory centre | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=prow&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| CAN | cantle（FBbt:00045051；syn. PENPp、PONPp、posterior perioesophageal neuropils） | 后围食管区 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=cantle&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| GOR | gorget（FBbt:00040039；syn. VMCs、supracommissural VMC） | inferior clamp 下方、向 noduli 内侧延伸的薄板 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=GOR&ontology=fbbt&rows=3&fieldList=label,obo_id,exact_synonyms) |
| EPA | epaulette 肩章（FBbt:00040040） | 腹侧复合体的小成对区域 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=EPA&ontology=fbbt&rows=3&fieldList=label,obo_id,exact_synonyms) |
| VES | vest 背心（FBbt:00040041） | 腹侧复合体中最大、最内侧的区域 | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=vest&ontology=fbbt&rows=6&fieldList=label,obo_id,exact_synonyms) |
| GC | great commissure 大连合（FBbt:00047941；syn. VPC2；adult FBbt:00007080） | 主要连合；hemibrain ROI `GC` | [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=great%20commissure&ontology=fbbt&rows=4&fieldList=label,obo_id,exact_synonyms) |
| GF | giant fiber 巨纤维（hemibrain ROI `GF(R)`） | 逃逸回路的下行神经元 | [neuprint-python](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html) |

**仍未核验（不要在页面当事实写）**：`LH`（OLS 只返回侧角**神经元** LHN FBbt:00048293，未找到 neuropil 术语）、`SNP`（hemibrain ROI `SNP(R)` 有实例但无 FBbt 全称）、`ACA`/`ROB`/`RUB`（只出现在 `MB(+ACA)(R)`、`CRE(-ROB,-RUB)(R)` 里）、`RID`、`RO`、`ALA`、`UNS`，以及 `LAM`/`MED`/`LOB` 这三个「三字母版」——**FBbt 里的规范缩写是 LA / ME / LO / LOP**，MaleCNS 场景里用的是 ME/LO/LOP。

**一个很有用的结构发现**：**PRW 与 FLA 就是腹侧与背侧三分脑（TRv / TRd）** —— 这正好解释了 lineage 命名里出现的 "TR" 前缀。另外 WED = IVLP，说明 Ito-2014 的多个名字其实是同一个域的别名，**页面应始终「缩写 + 全称」并列打印**。

**VNC 侧命名（MANC/BANC 用，来自 MANC 论文而非 FBbt）**：LegNp 腿神经毡；VAC 腹侧联合中心；mVAC 内侧 VAC；IntNp 中间神经毡；LTct 下 tectulum；IntTct 中间 tectulum；上 tectulum 又分为 NTct（颈）/ WTct（翅）/ HTct（平衡棒）；ANm 腹神经节 mesh；Ov ovoid；T1/T2/T3 胸神经节；SEZ 食管下区。 — [eLife reviewed preprint 97766](https://elifesciences.org/reviewed-preprints/97766)；[malevnc issue 讨论](https://github.com/natverse/malevnc/issues/45#issuecomment-1133566849)
**VNC 命名法权威出处**：Court R, Namiki S, Armstrong JD, et al. *A Systematic Nomenclature for the Drosophila Ventral Nerve Cord.* **Neuron 107(6):1071–1079.e2 (2020)**. [DOI](https://doi.org/10.1016/j.neuron.2020.08.005)

### 4.5 各数据集定义多少个 neuropil 区

| 数据集 | 脑 | VNC | 来源 |
|---|---|---|---|
| **FlyWire FAFB** | **78 个脑区** | —（FAFB 不含 VNC） | 「…refine the subdivision of **78 anatomical brain regions** of Drosophila」「**Of the 78 FAFB regions**, 68% showed increased Moran's index values」 — [bioRxiv 2025.07.10.664244](https://www.biorxiv.org/content/10.1101/2025.07.10.664244v1.full) |
| **hemibrain** | **待核实**（ROI 是**嵌套层级**而非扁平清单：`AL(L)/AL(R)`、`AOT(R)`、`CX → AB(L)/AB(R)/EB/FB/NO/PB`、`GC`、`GF(R)`、`GNG`、`INP`…） | —（hemibrain 只含中央脑 + 视叶） | [neuprint-python](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html) |
| **MaleCNS** | ROI 索引 **最大值 96** | ROI 索引 **最大值 27** | 见下 |
| **MANC** | —（只有 VNC） | **待核实**（定义了 6 个腿神经毡 + LTct/IntTct/NTct/WTct/HTct + 腹神经节 mesh） | [eLife reviewed preprint 97766](https://elifesciences.org/reviewed-preprints/97766) |

**MaleCNS Download 页原文（逐字确认）** — [Download 页](https://male-cns.janelia.org/download/)：
- 脑：`gs://flyem-male-cns/rois/fullbrain-roi-v4` — "Brain neuropil compartment segmentation, **initialized via transfer from ROIs in JRC2018M and refined manually**." / "256nm isotropic resolution" / **"Voxels are stored as `uint64`, but max value is `96`."**
- VNC：**正确的 bucket 名是 `gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0`**（不带 `malecns-` 前缀的写法是错的） — "VNC neuropil compartment segmentation, **refined manually**." / "256nm isotropic resolution" / **"Voxels are stored as `uint64`, but max value is `27`."**
- ⚠️ 页面需注明：这两个数是 **ROI 分割体的「索引最大值」（即不同标签值的个数）**，与 neuPrint 里「命名 ROI 的条数」不是严格同一个量。

**Codex Neuropils 应用的现状（如果页面想链接它）**：需要 Google 登录；未登录抓取只会返回登录页；`/api/neuropils`、`/app/neuropil_list` 均 404。想在 FAFB 里拿区域名，可改用注释仓库中 `Supplemental_file4_hemilineages_clustering.csv` 的 `nps` 列（每个神经元 top-3 支配 neuropil）。 — [Codex FAQ](https://codex.flywire.ai/faq)；[flywire_annotations](https://github.com/flyconnectome/flywire_annotations)

> **命名法的权威出处（必引）**：Ito K, Shinomiya K, Ito M, Armstrong JD, Boyan G, Hartenstein V, Harzsch S, Heisenberg M, Homberg U, Jenett A, Keshishian H, Restifo LL, Rössler W, Simpson JH, Strausfeld NJ, Strauss R, Vosshall LB; Insect Brain Name Working Group. *A systematic nomenclature for the insect brain.* **Neuron 81(4):755–765 (2014)**. [DOI](https://doi.org/10.1016/j.neuron.2013.12.017)
> 该文摘要明确写出了这套命名法**为什么存在**：「insect brains 的描述一直缺乏统一命名……**neuropil 边界不清使连接组学难以精确记录神经元投射位置**」，因此一个跨物种联盟以 *Drosophila melanogaster* 为参考框架建立了**层级命名系统**。 — 同上
- Codex 提供专门的 Neuropils / Brain Regions 浏览器（FAFB 可用），可用于逐条核对。 — [Codex FAQ](https://codex.flywire.ai/faq)

---

## 5. Hemilineage（半谱系）

### 5.1 neuroblast lineage 与 hemilineage 是什么
- 果蝇中央脑神经元分成**约 100 对左右的分组，称为 lineage（谱系）；每个 lineage 来自单个不对称分裂的 neuroblast**。 — [Lovick et al. 2013, Dev Biol 384(2):228–257 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID%3A23880429&format=json&resultType=core)
- 果蝇神经系统由**数量不多、遗传上确定的 lineage（谱系）** 模块建成。Type I lineage：单个 stem-cell 样 **neuroblast** 产生约 **100–150 个神经元**；少数限于背内侧脑的 Type II lineage 更大（约 500 个神经元）。 — [Lovick et al. 2015, Dev Neurobiol, PMC4713354](https://pmc.ncbi.nlm.nih.gov/articles/PMC4713354/)
- **神经母细胞不对称分裂** → 一个持续分裂的大女儿细胞（自我更新）+ 一个较小的 ganglion mother cell (GMC)，GMC 再分裂一次产生两个 postmitotic 细胞。**hemilineage 正是 GMC 分裂的产物**：同一个 GMC 产生的两个神经元并不对等，形成 **"A" 与 "B" 神经元**。 — 同上（Lovick 2015）；原始出处 [Truman et al. 2010](https://doi.org/10.1242/dev.041749)
- **Truman 2010 摘要的逐字结论**：*"In all cases, the 'A' (**Notch(ON)**) sibling assumes one fate and the 'B' (**Notch(OFF)**) sibling assumes another, and this relationship holds throughout the neurogenic period, resulting in two major neuronal classes: the A and B hemilineages."* 以及 *"Apparent monotypic lineages typically result from the **death of one sibling** throughout the lineage, resulting in a single, surviving hemilineage. **Projection neurons are predominantly from the B hemilineages, whereas local interneurons are typically from A hemilineages.**"* — [Truman et al. 2010, Development 137(1):53–61](https://doi.org/10.1242/dev.041749)
- **A/B 神经元在轴突轨迹上系统性不同**：所有 A 神经元捆成一束，B 神经元捆成另一束；文献里常说的 "branched secondary axon tract (SAT)" 实际就是 A-tract 与 B-tract 的合并。**在很多（若非全部）SAT 不分支的情形下，其中一个 hemilineage 被凋亡清除。** — [Lovick et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4713354/)
- ⚠️ **重要纠正**：A/B ↔ Notch-ON/OFF ↔ dorsal/ventral 这条**固定**映射只在**编号的胚胎/VNC 体系**里成立；**脑内成体 lineage 名字里的方位后缀（`_dorsal`/`_ventral`/`_medial`…）不是 Notch 代码**，而是逐 lineage 不同的位置标签，Notch 归属需要逐 lineage 查。详见 5.2 末尾。 — [FBbt:00049894 editor note](https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?iri=http://purl.obolibrary.org/obo/FBbt_00049894)
- hemilineage 身份与**神经递质表型**高度相关，这一点有独立的全脑数据支持：*"neurons that develop together largely express only one fast-acting transmitter (acetylcholine, glutamate, or GABA)"* — [Eckstein, Bates et al. 2024 Cell 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2024.03.016%22&resultType=core&format=json)
- 除了 hemilineage，还有更细的 **sublineage**：在某个时间窗内**先后出生**的一组神经元，轴突可走同一条 SAT 但选择不同靶区（例如蘑菇体四个 lineage 中不同时间窗出生的神经元分别生成 γ 叶、α/β 叶、α′/β′ 叶）。 — [Lovick et al. 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4713354/)
- FAFB 资源明确「incorporated annotations of cell classes and types, nerves, **hemilineages** and predictions of neurotransmitter identities」。 — [Dorkenwald et al. 2024 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE%3A%22Neuronal%20wiring%20diagram%20of%20an%20adult%20brain%22&resultType=core&format=json)
- Schlegel et al. 2024 把 hemilineage 列为**发育单元（developmental units）**，与 class/cell type 一起做系统层级注释。 — [Schlegel et al. 2024 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-024-07686-5%22&resultType=core&format=json)

### 5.2 命名：两套并行体系，且 MaleCNS 数据里两套都在

**这是本节最重要的结论**：FlyWire/MaleCNS 里的 `ito_lee_*` 与 `hartenstein_*` **不是两种分组，而是同一个发育单元的两种名字**。FBbt 本体把这件事写得很明确——它给每个 lineage 术语打上带方案名的 synonym：
- `ito_lee_*` ↔ synonym 类型 **"name in Ito/Lee brain lineage nomenclature scheme"**
- `hartenstein_*` ↔ synonym 类型 **"name in Hartenstein brain lineage nomenclature scheme"**

**逐字证据**：FBbt:00100654 "BAmv3 lineage neuron" 同时带 exact synonyms **"ALad1 lineage neuron"**（Ito/Lee 方案）与 "BAmv3 lineage neuron"（Hartenstein 方案）；FBbt:00050098 "adult LHd1 lineage clone" 的定义是 *"A clone of neurons in the adult brain, all of which develop from **neuroblast DPLd (LHd1)**"*，带 "adult DPLd lineage clone"（Hartenstein）与 "adult LHd1 lineage clone"（Ito/Lee）两个 synonym。 — [FBbt:00100654](https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?iri=http://purl.obolibrary.org/obo/FBbt_00100654)、[FBbt:00050098](https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?iri=http://purl.obolibrary.org/obo/FBbt_00050098)
**可核对的跨表对应关系**：`ALad1 ≡ BAmv3`、`LHd1 ≡ DPLd`、`AOTUv1 ≡ DALcm2`、`SLPav2 ≡ BLD2`。

**MaleCNS 数据里两套都在**：MaleCNS 的 soma 属性同时带 **`itoleeHl`** 与 **`trumanHl`**，Neuroglancer 着色器里可同时显示（`color_by_itoleeHl` / `color_by_trumanHl`）。 — [MaleCNS Neuroglancer 场景 JSON，`soma-points` 图层 shader](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)

**Ito/Lee 前缀（在 FBbt 中枚举了完整的成体 lineage clone 集合，共 20 个）**：
**AL、AOTU、CL、CRE、DL、DM、EB、FLA、LAL、LH、MB、PB、PS、SIP、SLP、SMP、VES、VLP、VPN、WED**
完整标签集（去掉尾部序号/后缀）：ALad1、ALl1、ALlv1、ALv1、ALv2、AOTUv1–v4、CLp1、CLp2、CREa1、CREa2、CREl1、DL1、DL2、DM1–DM6、EBa1、FLAa1–FLAa3、LALv1、LHa1–LHa4、LHd1、LHd2、LHl1–LHl4、LHp1、LHp2、MBp、MBp1–MBp4、PBp1、PSa1、PSp1–PSp3、SIPa1、SIPp1、SLPad1、SLPal1–SLPal5、SLPa&l1、SLPav1–SLPav3、SLPp&v1、SLPpl1–SLPpl3、SLPpm1–SLPpm4、SMPad1–SMPad4、SMPpd1、SMPpd2、SMPpv1、SMPpv2、SMPp&v1、VESa1、VESa2、VLPa1、VLPa2、VLPd1、VLPd&p1、VLPl1、VLPl2、VLPl4、VLPl&d1、VLPl&p1、VLPl&p2、VLPp1、VLPp2、VLPp&l1、VPNd1–VPNd4、VPNl&d1、VPNp1–VPNp3、VPNp&v1、VPNv1–VPNv3、WEDa1、WEDa2、WEDd1、WEDd2。
— 查询：`https://www.ebi.ac.uk/ols4/api/search?q=lineage%20clone&ontology=fbbt&rows=400&fieldList=label,obo_id`
**Ito/Lee 前缀的含义（可由 FBbt 交叉引用读出，标注为推断）**：前 2–3 个字母对应该 lineage 的**主要投射靶 neuropil**。例：ALad1 ≡ BAmv3，而 FBbt:00067346 说 BAmv3 "generates … **antennal lobe** projection neuron"；LHd1 ≡ DPLd（lateral horn）；AOTUv1 ≡ DALcm2（anterior optic tubercle）；SLPav2 ≡ BLD2（superior lateral protocerebrum）；MBp1 = 蘑菇体 calyx 背中部的 neuroblast；VPNl&d1 ≡ BLAvm2/BLAl2，其两组「collectively innervate the **lateral horn and superior lateral protocerebrum**」。 — [OLS4: ALad1](https://www.ebi.ac.uk/ols4/api/search?q=ALad1&ontology=fbbt&rows=10&fieldList=label,obo_id,description)、[OLS4: VPNl](https://www.ebi.ac.uk/ols4/api/search?q=VPNl&ontology=fbbt&rows=15&fieldList=label,obo_id,description)
> **标为推断**：FBbt 只给交叉引用，**没有**「Ito/Lee 前缀 = neuropil 缩写」这条通则的原文句子 → 待核实。

**Hartenstein 前缀（已核验）**：**BA**（BAmv1/3、BAmd1、BAlc、BAla1/2、BAlp2/4）、**BLA**（BLAv1、BLAvm、BLAd1/2、BLAl1/2）、**BLD**（BLD1/2/3/5）、**BLP**（BLP1/5）、**BLV**（BLVp1/2）、**CM**（CM4）、**CP**（CP1–CP4）、**DAL**（DALcm1/2、DALcl1/2、DALl1/2、DALd、DALv3）、**DPL**（DPLam、DPLal2、DPLc2/4/5、DPLd、DPLl2/3、DPLp2、DPLpv）、**DILP**。
有出处的全称展开：
- **BA = baso-anterior 基前**：FBbt:00100563 neuroblast BAlp1 "generates a **basoanterior** secondary lineage"；baso-anterior synaptic neuropil domain 缩写即 BA（FBbt:00007128）
- **BLA = basolateral anterior 基侧前**：FBbt:00100614 neuroblast BLAd1 "Neuroblast found in a relatively dorsal location in the **basolateral anterior (BLA) group** during the larval stage (Pereanu and Hartenstein, 2006)"
- **CM = centromedial 中央内侧**：FBbt:00050252 neuroblast CM4 "Type II **centromedial** neuroblast of the posterior deutocerebrum"
- **CP = centro-posterior 中央后；DPL = dorso-posterior lateral 背侧后外**：FBbt:00007120 "Tract … formed by axons converging from the **dorso-posterior and centro-posterior lateral** compartments"；FBbt:00052217 "…composed of fibers of the **DPLpv** lineage"；FBbt:00052220 "…composed of fibers of the **CP2/3** lineages"
- 来源：[OLS4 baso-anterior](https://www.ebi.ac.uk/ols4/api/search?q=%22basal%20anterior%22&ontology=fbbt&rows=15&fieldList=label,obo_id,description)、[OLS4 baso-lateral](https://www.ebi.ac.uk/ols4/api/search?q=baso-lateral&ontology=fbbt&rows=50&fieldList=label,obo_id,description)、[OLS4 CM4](https://www.ebi.ac.uk/ols4/api/search?q=CM4&ontology=fbbt&rows=8&fieldList=label,obo_id,description)、[OLS4 dorso-posterior lateral](https://www.ebi.ac.uk/ols4/api/search?q=dorso-posterior%20lateral&ontology=fbbt&rows=20&fieldList=label,obo_id,description)
- **SAT（secondary axon tract）概念**："All neurons of a lineage project as one or a few axon tracts (**secondary axon tracts, SATs**) with characteristic trajectories… In the neuropil, SATs assemble into larger fiber bundles (fascicles)…" — Lovick et al. 2013 摘要，[EuropePMC](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID%3A23880429&format=json&resultType=core)
- **仍未核验的展开**：BAlc/BAlp 超出 "basoanterior" 的部分、BLD、BLP、BLV、DAL/DAM/DPM 的已发表全称、TR（tritocerebral）、LB、GA、MX、MD → 待核实

**⚠️ 后缀约定——直接回答「LH、VL、DL… 的 v/d 是 Notch-ON/OFF 吗？」：不是固定规则。**
- 在 FlyWire 注释表里，后缀是下划线后的**完整方位词**（`_dorsal`、`_ventral`、`_medial`、`_anterior`、`_posterior`、`_lateral`），**而且用的轴是逐 lineage 不同的**。
- FBbt 中存在方位性 hemilineage 术语的 lineage（成对轴）：DALl2 lateral/medial、BLD5 lateral/medial、CM4 dorsal/ventral、BAlp2 anterior/posterior、DPLal2 dorsal/ventral、DPLl3 anterior/posterior、DPLl2 anterior/posterior、DPLp2 anterior/posterior（+ medial ventral）、DPLpv anterior/posterior、CP1 dorsal/ventral、BLAd2 dorsal/ventral、BLAl1 lateral/medial、BLD1 dorsal/posterior、BLD3 anterior/dorsal、BLVp1 anterior/posterior、BLVp2 anterior/posterior、BLAv1 medial/posterior、BLAvm medial/posterior、BLP1 posterior/ventral。 — `https://www.ebi.ac.uk/ols4/api/search?q=%22hemilineage%20neuron%22&ontology=fbbt&rows=400&fieldList=label,obo_id`
- 只有**一部分** lineage 同时有显式 Notch 术语：DALcm1、BAmd1、DALcm2、DALcl1、DALcl2、BAmv1、BAlc、DPLc5（"X Notch ON/OFF hemilineage neuron"）。
- **决定性证据**：DALcm1 的 Notch 映射被**明确写成推断而非定义**——FBbt:00049894 "DALcm1 Notch OFF hemilineage neuron" 的 editor note：*"**Ventral hemilineage = Notch OFF judged by comparison of figures in Schlegel et al. (2024) and Lee et al. (2020)**"*；FBbt:00049895：*"**Medial hemilineage = Notch ON judged by comparison of figures…**"* → 也就是说 DALcm1 用的是 medial/ventral 轴，其 Notch 归属是逐篇论文比对出来的。 — [FBbt:00049894](https://www.ebi.ac.uk/ols4/api/ontologies/fbbt/terms?iri=http://purl.obolibrary.org/obo/FBbt_00049894)
- 反例：FBbt:00053606 "CM4 dorsal hemilineage neuron" 定义为 "…belongs to the hemilineage with **somas in a relatively dorsal cluster** in the adult" —— 纯位置描述，不提 Notch；FBbt:00053598 "BLVp2 anterior hemilineage neuron" 被定义为胞体在相对 **lateral** 的簇（标签与定义不一致，进一步说明这些 tag 是位置性的）。
- **页面实用规则**：把后缀读成**形态/位置标签**；Notch ON/OFF 需要**逐 lineage 查**（FBbt 只对部分 lineage 有显式术语）。
- **唯一严格成立的固定约定**在**编号的胚胎/VNC 体系**（Truman/Lacin 的 A/B 编号）里：**A = Notch ON = dorsal；B = Notch OFF = ventral**。证据：FBbt:00051313 标签 "NB7-1 Notch ON hemilineage primary neuron" 带 synonyms "NB7-1 **dorsal** hemilineage primary neuron" 与 "NB7-1 hemilineage **A** primary neuron"；FBbt:00051310 "NB7-1 Notch OFF…" 带 "NB7-1 hemilineage B primary neuron"；FBbt:00051309 "NB1-2 Notch OFF…" 带 "NB1-2 **ventral** hemilineage primary neuron"。 — [OLS4](https://www.ebi.ac.uk/ols4/api/search?q=%22Notch%20ON%20hemilineage%20neuron%22&ontology=fbbt&rows=300&fieldList=label,obo_id)
  （附带一个本体数据不一致：FBbt:00051313 的**定义文本**误写成 "Notch OFF"，可作为一个诚实的脚注。）
- **序号是组内索引，不是 hemilineage 索引**：FBbt 把 BLAd1–BLAd4 都定义为 "in the basolateral anterior (BLA) group"；DPLc2/DPLc4 则被描述为 "forms a paired lineage"。
- **名字里的 `&`**（VPNl&d1、SLPa&l1、SMPp&v1、SLPp&v1、VLPl&d1…）标记**合并/未拆解的组**：FBbt:00050013 editor note——"BLAvm2 and BLAl2 **not in Pereanu and Hartenstein (2006) or later (but pre-connectome) Hartenstein papers**"。
- **`__prim`**（ALad1__prim、DILP__prim、BAmv3__prim）：注释表的 `is_hemilineage` 列把这些行标为 `part_of_lineage` / `primary_lineage`，故后缀**很可能**意为 "primary"（推断）；**README 未定义 → 待核实**。
- `is_hemilineage` 列的**有出处的取值词汇表**：`H(NT)`（依据 Eckstein et al. 2024 的递质信息推断为 hemilineage）、`2L_1NT`（2 个 lineage，所有神经元同一预测递质）、`H`、`H/L`、`H?`、`H_2NT`、`Hp`、`L`、`T2`（type II lineage），以及数据中出现的 `part_of_lineage`/`primary_lineage`。 — [supplemental_files/README.md](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/README.md)

**真实出现的名字（可直接对照）**：注释表 `Supplemental_file3_summary_with_ngl_links.csv` 前几行的 `ito_lee_hemilineage | hartenstein_hemilineage` 配对：
`ALad1 | BAmv3` · `ALad1__prim | BAmv3__prim` · `ALl1_dorsal | BAlc_dorsal` · `ALl1_ventral | BAlc_ventral` · `ALlv1 | BAlp4` · **`ALv1 | BAla1`** · `ALv2 | BAla2` · `AOTUv1_medial | DALcm2_medial` · `AOTUv1_ventral | DALcm2_ventral` · `AOTUv2 | DALl1` · `AOTUv3_dorsal | DALcl1_dorsal` · `AOTUv4_ventral | DALcl2_ventral` · `CLp1 | DPLc4` · `CLp2 | CP4` · `CREa1_dorsal | BAmd1_dorsal` · `CREa2_medial | DALcm1_medial` · `CREl1 | DALv3` · `DILP__prim | DILP__prim` · `DL1_dorsal | CP2_dorsal`
— [原始 CSV](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/Supplemental_file3_summary_with_ngl_links.csv)（注：抓取工具在 ~150 KB 处截断，故只能读到前约 24 行）
VFB 中 MaleCNS 神经元的 lineage 标签形如 `lineage_MBp2`、`lineage_VLPp&l1_DPLpv`、`lineage_VLPl&p1_BLVp2`（Ito/Lee 名 + Hartenstein 名并列，**正好印证两套并存**）。 — [VFB male-cns 数据集页](http://www.virtualflybrain.org/blog/2022/01/01/male-cns-berg2025/)

> **权威数据源**（需要精确、完整清单时用这些，而不是猜）：
> - `Supplemental_file1_neuron_annotations.tsv` —— 列名直接就是 **`ito_lee_hemilineage`、`hartenstein_hemilineage`、`ito_lee_lineage`、`hartenstein_lineage`**
> - `Supplemental_file3_summary_with_ngl_links.csv` —— 每个 hemilineage 的汇总 + neuroglancer 链接
> - `Supplemental_file4_hemilineages_clustering.csv` —— **用 NBLAST 对 hemilineage 聚类生成 morphology group** 的细节；其 `nps` 列是每个神经元 top-3 支配 neuropil
> - `Supplemental_file5_hemibrain_meta.csv` —— hemibrain v1.2.1 元数据
> - 列定义：https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/README.md
> - **仓库自己的警告**：Codex「presents a mix of annotations from different sources which **likely diverge** from the systematic and cross-checked annotations presented here.」 — [README](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/README.md)

### 5.3 为什么连接组论文用 hemilineage 分组
1. **它就是这个系统的克隆/发育单位**：「All neurons of a lineage project as one or a few axon tracts (secondary axon tracts, SATs) with characteristic trajectories, thereby representing **unique hallmarks**.」 — [Lovick et al. 2013, Dev Biol 384(2):228–257 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID%3A23880429&format=json&resultType=core)。旁证：*"the adult specific cells in a given lineage are remarkably similar and typically project to only one or two initial targets."* — [Truman et al. 2004, Development 131(20):5167–5184 摘要](https://doi.org/10.1242/dev.01371)
2. **它是本体里正式注释的一个层级**：Schlegel et al. 2024 的注释覆盖 "neuronal classes, cell types and **developmental units (hemilineages)**" — [DOI](https://doi.org/10.1038/s41586-024-07686-5)；FlyWire 注释表用一整对列（`ito_lee_hemilineage`/`hartenstein_hemilineage`）承载它。 — [README](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/README.md)
3. **它被用来生成 morphology group（这是「分组/正则」最直接的有源证据）**：仓库 README——*"`Supplemental_file3_hemilineages_clustering.csv` contains details on the **NBLAST clustering of hemilineages that generated the morphology groups**"*；已移除的 `morphology_group` 列的定义是「coarse morphological grouping **based on hemilineage clustering**」。 — [README](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/README.md) + [supplemental_files/README.md](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/README.md)
4. **它被写进细胞类型定义本身**：例如 FBbt 中依据 Schlegel et al. 2024 定义的细胞类型会写 "It belongs to the **VPNl&d1 dorsal hemilineage** (Schlegel et al., 2024; Dorkenwald et al., 2024)"。FBbt 也把 hemilineage 归组当成活的难题：FBbt:00050012 editor note——"Hemilineage classes not created for this NB as **three groups were identified in Schlegel et al. (2024) and it is unclear how hemilineages should be grouped**." — [OLS4 VPNl](https://www.ebi.ac.uk/ols4/api/search?q=VPNl&ontology=fbbt&rows=15&fieldList=label,obo_id,description)
5. **它与递质强相关（三条独立证据）**：
   (a) Truman et al. 2010 摘要：projection neuron 主要来自 **B** hemilineage，local interneuron 主要来自 **A** hemilineage。 — [DOI](https://doi.org/10.1242/dev.041749)
   (b) FBbt 的 hemilineage 定义直接带递质数据：FBbt:00051455 "hemilineage 1A secondary neuron" —— "In the adult, these neurons are **cholinergic** (Lacin et al., 2019)"；FBbt:00051457 "hemilineage 9A" —— "**GABAergic**"；FBbt:00051456 "hemilineage 8A" —— "**glutamatergic**"；FBbt:00053056 "hemilineage 0B" —— "**octopaminergic** (Pop et al., 2020)"。 — `https://www.ebi.ac.uk/ols4/api/search?q=hemilineage&ontology=fbbt&rows=500&fieldList=label,obo_id`
   (c) FlyWire 的 `is_hemilineage` 列**本身就用递质证据来判断一个条目是 1 个还是 2 个 hemilineage**：`H(NT)` = "we guess that this is a hemilineage … based on the neurotransmitter information from Eckstein et al. (2024)"。 — [supplemental_files/README.md](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/README.md)
6. 在 MaleCNS 里可用于**交互式筛选**（Clio 支持按 hemilineage 过滤）。 — [male-cns.janelia.org](https://male-cns.janelia.org/)

**两条引文更正（重要）**：
- 「Developmental architecture of adult-specific lineages…」是 **Truman JW, Schuppe H, Shepherd D, Williams DW (2004)**, *Development* **131(20):5167–5184**，标题含 "**in the ventral CNS** of Drosophila" —— **不是 2010 年**，也不存在同名的 Truman 2010 论文。 — [DOI](https://doi.org/10.1242/dev.01371)
- Bates et al. 2020 的嗅觉投射神经元连接组论文在 ***Current Biology***（30(16):3183–3199.e6, [DOI](https://doi.org/10.1016/j.cub.2020.06.042)），**不是 eLife**。
- 相关：Ito M, Masuda N, Shinomiya K, Endo K, Ito K. *Systematic analysis of neural projections reveals clonal composition of the Drosophila brain.* **Curr Biol 23(8):644–655 (2013)**，[DOI](https://doi.org/10.1016/j.cub.2013.03.015)（这是 "Ito/Lee" 里的 Ito）。
- 补充：*"Insect brains develop from ~100 neuroblasts per hemisphere that divide systematically to form 'lineages' of sister neurons, that project to their target neuropils along anatomically characteristic tracts."* — Kandimalla, Omoto, Hong & Hartenstein 2023, J Comp Physiol A 209(4):679–720，[DOI](https://doi.org/10.1007/s00359-023-01616-y)
- **待核实**：一句明确的「hemilineage 作为稀疏性/正则化先验」的方法学原文（Schlegel 2024/2021 的所有全文端点在本轮检索中均失败：EuropePMC `/fullTextXML` → HTTP 406，nature.com → idp 重定向）。上面第 3 条（NBLAST 聚类 hemilineage → morphology group）是目前最接近该论断的可溯源证据。

---

## 6. 神经递质预测（nt_type / consensus_nt）

### 6.1 怎么预测
- **原理**：连接的方向不能从接线图看出**符号（兴奋/抑制）**，但符号由释放的递质决定。人工神经网络**从突触前位点的电镜图像**直接预测递质类型。 — [Eckstein, Bates et al. 2024 Cell 摘要](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2024.03.016%22&resultType=core&format=json)
- **主类**：模型训练预测 **6 种递质**：acetylcholine (ACh)、glutamate (Glu)、GABA、serotonin (5-HT)、dopamine (DA)、octopamine (OA)。 — 同上
- **用了哪些超微结构特征**：论文明确「visualize the ultrastructural features used for prediction, discovering **subtle but significant differences** between transmitter phenotypes」——即预测确实基于突触前超微结构（在果蝇里主要就是 **T-bar 及突触囊泡**的形态特征），而不是靠旁路信息。 — 同上
- **性能（这是可引用的核心数字）**：**单个突触 87%，单个神经元 94%，已知细胞类型 91%**（跨整个果蝇脑）。 — 同上

### 6.2 MaleCNS 里实际存在的递质类别与字段
MaleCNS v1.0 场景中 T-bar/突触的 `predicted_nt` 编码**恰好是 7 类 + unknown**：

```
acetylcholine_code 0 | dopamine_code 1 | gaba_code 2 | glutamate_code 3
histamine_code 4 | octopamine_code 5 | serotonin_code 6 | unknown_nt_code 7
```
并且每个突触带 `predicted_nt_prob`（概率）与 `nt_tbar_confidence_score`（T-bar 置信度）两个连续量。
— [MaleCNS Neuroglancer 场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)

对照 FlyWire：Codex 说明递质类型由 Eckstein, Bates et al. 预测，并同时展示**预测值 + confidence score**，以及（若有）来自人工整理的 **verified** 递质/神经肽；**预测字段与 verified 字段可能冲突**，应把 verified 当整理注释、predicted 当模型输出。 — [Codex About FlyWire](https://codex.flywire.ai/about_flywire)；[Codex FAQ](https://codex.flywire.ai/faq)

MaleCNS 的扁平文件里，递质单独成表：
- `body-neurotransmitters-male-cns-v1.0.feather`（每个神经元的**聚合**递质预测）
- `tbar-neurotransmitters-male-cns-v1.0.feather`（**每个突触前位点**的递质预测概率）
— [Download 页](https://male-cns.janelia.org/download/)

**注意 MaleCNS 中的字段命名**：Download 页把逐突触表命名为 `tbar-neurotransmitters`，说明 MaleCNS 的递质预测是在 **T-bar** 层面做出的（对应场景里的 `nt_tbar_confidence_score`、`tbar_fanout`），再聚合到神经元层面得到 `consensus_nt` 类的量。 — [Download 页](https://male-cns.janelia.org/download/)；[场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)
> 官方页面**未逐字给出 `consensus_nt` 的定义与「聚合时的不确定性百分比」** → **待核实**

### 6.3 为什么「小分子 Glu」在两可之间
**待核实** —— 我没有找到可公开抓取的、把「果蝇中谷氨酸可兴奋也可抑制」这一点写清楚并经 MaleCNS/FlyWire 官方文档确认的原文。
可溯源的相邻事实（可用于教学，但**不等于**该论断的出处）：
- Eckstein et al. 把 Glu 与 ACh、GABA 并列称为**三种快速递质（fast-acting transmitter）**，并发现同 hemilineage 神经元大体只表达其中一种。 — [Eckstein et al. 2024](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2024.03.016%22&resultType=core&format=json)
- VFB 明确指出：**连接组本身不含符号信息**，「The sign of a connection is not visible in the wiring diagram」，符号只能由递质预测间接推断。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)
- Schlegel et al. 提到果蝇存在「inhibitory」相关分析（MeSH 含 Neural Inhibition），并在蘑菇体中给出「维持 excitation/inhibition ratio」的稳态证据。 — [Schlegel et al. 2024](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-024-07686-5%22&resultType=core&format=json)
- 果蝇中 Glu 既可作为兴奋性递质（如神经肌肉接头）也可作为抑制性递质（部分中枢回路）——这是领域常识，但**本报告未能定位到权威一手来源**，故标注 **待核实**，建议引用时改用一篇专门的 Glu/GABA 综述。

**MaleCNS 的递质不确定性具体数值**：**待核实**（可预期在 MaleCNS 论文的 body-neurotransmitters 说明与 Fig. S 里；本报告未能抓取论文正文）。

---

## 7. FlyEM 细胞类型命名空间（cell_type / resolved_type / super_class / class / hemilineage / side / neurotransmitter_type）

### 7.1 各字段含义（以 Codex 的官方字段表为准）

| 字段 | 官方说明（译） | 来源 |
|---|---|---|
| `root_id` | 细胞的 ID；**跨数据版本唯一，但被 proofreading 改动后可能被替换** | [Codex FAQ](https://codex.flywire.ai/faq) |
| `label` | 细胞鉴定过程中人类给的可读标签；一个细胞可有 0 个或多个 label | 同上 |
| `name` | 自动分配的 name（基于最主要的输入/输出区域）；跨版本唯一，但被 proofreading 影响后会变 | 同上 |
| `group` | 自动分配的 group name（同上依据） | 同上 |
| `side` | 神经元**胞体（soma）**所在侧/半球 | 同上 |
| `neuromere` | 胞体所在的神经体节（neuromere） | 同上 |
| `flow` | 「flow」，指神经元在脑内的归属/包含关系 | 同上 |
| `super_class` | 细胞分型属性，表示细胞的功能或其他性质 | 同上 |
| `class` | 细胞分型属性 | 同上 |
| `sub_class` | 细胞分型属性 | 同上 |
| `cell_type` | 细胞分型属性 | 同上 |
| **`resolved_type`** | **主细胞类型（当被赋予多个类型时取的那个）** | 同上 |
| `hemilineage` | 来自 Janelia hemibrain 数据集的谱系 | 同上 |
| `nerve` | 神经类型（若适用） | 同上 |
| `nt_type` | 神经递质类型（**预测**） | 同上 |
| `nt_type_verified` | **人工验证**过的神经递质类型 | 同上 |
| `neuropeptide_verified` | 人工验证过的神经肽 | 同上 |
| `dimorphism` | 性二态标注 | 同上 |
| `gene` | 基因表达 | 同上 |
| `input_neuropils` / `output_neuropils` | 上游突触所在 / 下游突触所在的脑区 | 同上 |
| `mirror_twin_root_id` | 镜像孪生细胞的 ID（可选） | 同上 |
| `connectivity_tag` | 网络分析描述符（rich club、broadcaster、integrator、attractor、repeller、reciprocal、feedforward-loop participant、3-cycle participant 等） | 同上 |

补充（Codex 对「注释层」的说明）：
- **Cell types** 由多个来源整合，Type 多于一个时 Codex 会选一个 **primary/resolved type**。
- **Community labels** 是 FlyWire 社区贡献的自由文本标识标签。
- **Hierarchical classification** 字段包括 **flow、super class、class、sub class、side、neuromere、nerve、hemilineage**。
— [Codex FAQ](https://codex.flywire.ai/faq)

### 7.2 `resolved_type` 与 `cell_type` 的区别（一句话）
`cell_type` 可能是一个细胞上被赋予的若干类型之一；`resolved_type` 是从中**裁决出的主类型**（Codex 整合多来源时的去重/调和结果）。 — [Codex FAQ](https://codex.flywire.ai/faq)

### 7.3 FlyWire `super_class` 的 9 个类别（有权威来源）

FlyBase DAO（果蝇解剖发育本体）issue #1641 明确列出「一篇即将发表的论文需要 9 个 superclass，覆盖 FlyWire 数据集中几乎所有神经元，**依据胞体位置与投射靶区**」：

| 提议名称 | 胞体位置 | 轴突投射位置 |
|---|---|---|
| **sensory neuron** 感觉神经元 | 外周 | 脑 |
| **ascending neuron** 上行神经元 | VNC | 脑 |
| **central brain intrinsic neuron** 中央脑内在神经元 | 中央脑 | 中央脑（轴突+树突） |
| **optic lobe intrinsic neuron** 视叶内在神经元 | 视叶 | 视叶（轴突+树突） |
| **visual projection neuron** 视觉投射神经元 | 视叶 | 中央脑 |
| **visual centrifugal neuron** 视觉离心神经元 | 中央脑 | 视叶 |
| **motor neuron** 运动神经元 | 脑 | 外周 |
| **descending neuron** 下行神经元 | 脑 | VNC |
| **endocrine neuron** 内分泌神经元 | 脑 | ring gland 咽侧体/环腺 |

来源：[FlyBase DAO issue #1641「Neuronal "superclasses" for FlyWire」](https://github.com/FlyBase/drosophila-anatomy-developmental-ontology/issues/1641)（原文即列出上表；issue 已关闭并标记 priority for next release）

对应的 FlyBase 本体术语（issue 中同时给出）：optic lobe intrinsic neuron = `FBbt_00007577`；visual projection neuron = `FBbt_00048287`；sensory neuron = `FBbt_00005124`；motor neuron = `FBbt_00005123`；adult ascending neuron = `FBbt_00048301`；adult descending neuron = `FBbt_00047511`。 — 同上

**MaleCNS 侧的对应关系**：FlyWire 注释仓库 v3.0.0 起新增 `supertype` 列，其说明是「**matches the corresponding entry in neuPrint for the MaleCNS**」——也就是说 MaleCNS/neuPrint 与 FlyWire 的 superclass 体系已被显式对齐。 — [flywire_annotations README changelog](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/README.md)

**视叶的分组在 MaleCNS 官方页面上被明确命名（与上表一致）**：Optic Lobe Intrinsic Neurons、Optic Lobe Connecting Neurons、Visual Projection Neurons、Visual Centrifugal Neurons；数量为约 16,000 内在（150 型）、32,000 connecting（90+ 型）、4,500 投射（350 型）、280+ 离心（100+ 型）。 — [Janelia Optic Lobe 页](https://www.janelia.org/project-team/flyem/optic-lobe)

**Codex 里可用的结构化查询示例**：`super_class == sensory`、`class == JON`、`nt_type != GABA`、`hemilineage == ...`、`resolved_type == ...`。 — [Codex FAQ](https://codex.flywire.ai/faq)

---

## 8. Proofreading

### 8.1 是什么
- 自动分割**从来不是正确的产物**，含 **split**（一个神经元被切碎）与 **merge**（两个神经元被融合）两类错误；**proofreading 就是人工修正它们**。FlyWire 把这一步组织成对 FAFB 体积的社区协作。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)，引 [Dorkenwald et al. 2022 Nat Methods (FlyWire 平台)](https://doi.org/10.1038/s41592-021-01330-0)
- FlyWire 的证明流程与数据管理后端是 **CAVE**（Connectome Annotation Versioning Engine）；proofreading 工具包括 **neu3 / neuTu / neuroglancer**。 — [Dorkenwald et al. 2024 Fig.1c](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)；[Recipe for a Connectome](https://www.janelia.org/project-team/flyem/blog/recipe-for-a-connectome)
- **「proofread/annotated cell」意味着什么**：该神经元的 supervoxel 集合已经过人工合/拆修正，因而其形态与连接在该数据版本内被当作可信；Codex 的发布快照「generally include cells marked as proofread in the source project」，因此**未 proofread 的细胞可能根本不在你快照里**。 — [Codex FAQ](https://codex.flywire.ai/faq)

### 8.2 为什么重要
- 这是「**能让数据回答生物学问题**」的前提：FAFB 论文明确写了它的图（wiring diagram）「sufficiently complete to be designated a 'connectome'」，且用与 hemibrain 在重叠区域的一致性来论证「自然个体间变异 + 不完美重建造成的噪声总体上不大」。 — [Dorkenwald et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)
- 反过来，**proofreading 不到位会污染连接图**：一次 merge 会凭空造出动物体内不存在的连接；一次 split 会分裂连接。 — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)
- 也正因如此，**「cell type 计数与连接强度」在版本间会变**，且「缺失」不等于「不存在」。 — [VFB Connectivity Data](https://www.virtualflybrain.org/docs/data/connectivity/)

### 8.3 已有的量化/工作量数字
| 数字 | 含义 | 来源 |
|---|---|---|
| **约 44 年人力** | MaleCNS 重建（AI + 人工 proofreading）的等效人力 | [MRC LMB 新闻（2026-09-03）](https://mrclmb.ac.uk/news-events/articles/first-complete-connectome-of-male-fly-central-nervous-system-allows-for-unprecedented-male-female-brain-comparison/) |
| **~1,000 decisions/天/人**，目标 merge rate > 50% | FlyEM 的 proofreading 产出率基准 | [Recipe for a Connectome](https://www.janelia.org/project-team/flyem/blog/recipe-for-a-connectome) |
| 约 50 名 proofreader，每人训练 ≥2 个月 | hemibrain 规模的人力配置 | 同上 |
| 各步骤工作量估算（如 anchor segment 大范围 false-merge 检查 1–2 min/segment ≈ 6 proofreading 年；working set 内所有决策约 200 万条 ≈ 10 年） | top-down 流程的成本模型 | 同上 |
| 「无法靠人工标注百万级突触来实质改进整体准确率」——标注 1 亿连接的 10% 约需 50 proofreading 年 | 为什么突触检测只能靠迭代抽样重训 | 同上 |
| FlyWire 的 proofreading 累计工时「只能是粗略估计」 | 官方对精度的谨慎表述 | [Dorkenwald et al. 2024 预印本 PMC10327113](https://pmc.ncbi.nlm.nih.gov/articles/PMC10327113/) |
| Codex 有 **Labeling Leaderboard**、**Challenge**（Max Clique / VNC Matching / Minimum Feedback / Visual Columns）等众包校对与标注机制 | 社区校对的组织形式 | [Codex 导航与 FAQ](https://codex.flywire.ai/about_flywire) |

### 8.4 自动分割的准确率/错误率
- **可引用的官方量化入口**：FAFB 论文 **Extended Data Fig. 2「Completeness and accuracy of FlyWire's reconstruction」** 是这一数字的权威来源。 — [figures/9](https://preview-www.nature.com/articles/s41586-024-07558-y/figures/9)（本报告**未能读取该图的实际数值** → **具体百分比待核实**）
- **突触检测（而非形态分割）的准确率**：Yu et al. 2025 报告在最难区域 F-score 提升最多 0.23；细胞类型聚类改善 8–9%；连接模式预测类型的加权 F-score 0.93（vs 0.91）。 — [Yu et al. 2025](https://www.biorxiv.org/content/10.1101/2025.07.11.664377v1)
- **递质预测准确率**（常被误当成分割准确率）：单突触 87%、单神经元 94%、已知细胞类型 91%。 — [Eckstein et al. 2024](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2024.03.016%22&resultType=core&format=json)
- **MaleCNS 的对应验证**：论文 Fig. S8E 给出 T-bar 单独、以及「以突触为单位（pre/post 两成分都正确）」的 precision-recall；Fig. S9e 是同一组图的另一版本（检索索引中两种编号并存）。 — MaleCNS 论文（[Cell](https://www.cell.com/cell/fulltext/S0092-8674\(26\)00942-6)）；**PR 曲线的具体数值待核实**
- **MaleCNS 提供的独立证据层**：`malecns-v1.0-synapse-ground-truth-lines`、`-boxes`、`synapse-groundtruth` 三个官方图层可直接在 Neuroglancer 中打开核查。 — [场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)
- **切片级误区提醒**：自动分割的"准确率"高度依赖怎么算——按 voxel、按 segment、按 synapse、按 cell type 得到的数字可以差一个数量级。VFB 的原话：*"knowing which stage a number came from is most of what you need to interpret it."* — [VFB EM Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)

---

## 9. 果蝇之外：EM 连接组的世界（用于给 MaleCNS 定位）

> ⚠️ **引用陷阱（必须先说）**：下表中 FAFB / BANC / MCNS 在 Codex 上的「connections」是**满足最小突触阈值后的神经元对边数**（FAFB 5+、MCNS 5+、BANC 3+），**不是突触数**，不能和「~5,000 万突触」并列比较。 — [Codex FAQ](https://codex.flywire.ai/faq)

| 项目 | 物种/组织 | 体积 | 体素/成像 | 规模（细胞） | 突触 | 来源 |
|---|---|---|---|---|---|---|
| **C. elegans（1986）** | 线虫 | 整只虫 | TEM 连续切片（手工） | 雌雄同体 **302 个神经元**（118 类） | **约 5,000 化学突触 + 2,000 神经肌肉接头 + 600 间隙连接** | White et al. 1986, Phil. Trans. R. Soc. B 314:1–340，[DOI](https://doi.org/10.1098/rstb.1986.0056)；LMB 称其为连接组学起点 [MRC LMB](https://mrclmb.ac.uk/news-events/articles/first-complete-connectome-of-male-fly-central-nervous-system-allows-for-unprecedented-male-female-brain-comparison/) |
| **C. elegans（2019 重做）** | 线虫两性 | 整只虫 | — | 雌雄同体 **302 神经元** + 132 肌肉 + 26 末端器官（460 节点）；雄性 **385 神经元** + 155 肌肉 + 39 末端器官（579 节点） | 雌雄同体 **4,887 化学边 + 1,447 间隙连接边**；雄性 **5,315 + 1,755** | Cook et al. 2019 Nature 571:63–71，[DOI](https://doi.org/10.1038/s41586-019-1352-7)、[PMC6889226](https://pmc.ncbi.nlm.nih.gov/articles/PMC6889226/)、数据 [wormwiring.org](https://wormwiring.org/) |
| **果蝇 1 龄幼虫** | 果蝇幼虫 | 全 CNS | ssTEM | **3,000 个神经元** | **5×10⁵ 个突触** | [Dorkenwald et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)；[MRC LMB](https://mrclmb.ac.uk/news-events/articles/first-complete-connectome-of-male-fly-central-nervous-system-allows-for-unprecedented-male-female-brain-comparison/) |
| **hemibrain（2020）** | 雌蝇中央脑一部分 | 约半脑，26 万亿像素 | **8×8×8 nm³**，FIB-SEM + hot knife | 约 **25,000 个神经元**（其中约 **20,000 uncropped**），**4,000+ 个细胞类型** | **>2,000 万条连接（connections，非单突触数）**；另有文献口径「1,400 万突触」 | [Janelia Hemibrain](https://www.janelia.org/project-team/flyem/hemibrain)；[Google Research 发布博文](https://research.google/blog/releasing-the-drosophila-hemibrain-connectome-the-largest-synapse-resolution-map-of-brain-connectivity/)；[Dorkenwald et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/) |
| **FAFB / FlyWire（2024）** | 雌蝇全脑 | 全脑 | **4 × 4 nm 平面、40 nm 切片**（ssTEM） | **139,255 个神经元** | **5×10⁷（约 5,450 万）化学突触**；Codex 默认 5+ 阈值下 **3,732,460 条连接** | [Dorkenwald et al. 2024 (DOI)](https://doi.org/10.1038/s41586-024-07558-y)、[PMC11446842](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/)；[Codex](https://codex.flywire.ai/api/download)、[Codex FAQ](https://codex.flywire.ai/faq) |
| **MANC v1.2.1** | 雄蝇腹神经索 | 完整 VNC | 8×8×8 nm，FIB-SEM | 约 **23,000 个神经元**；Codex 记 **23,665** | 官方页：**1,000 万个突触前位点、7,400 万个突触后密度**；Codex 默认 1+ 阈值下 **5,305,638 条连接** | [Janelia MANC](https://www.janelia.org/project-team/flyem/manc-connectome)；[Codex](https://codex.flywire.ai/api/download) |
| **MAOL v1.1** | 雄蝇右视叶 | 单侧视叶 | FIB-SEM | **52,445**（Codex）；论文口径约 53,000 神经元 → **732 个类型** | Codex 默认 1+ 阈值下 **6,484,936 条连接** | [Codex](https://codex.flywire.ai/api/download)；[Nern et al. 2025 Nature](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-025-08746-0%22&resultType=core&format=json) |
| **BANC（2026）** | 雌蝇脑 + 神经索 | 全 CNS | 4 nm 平面，ssEM | 官方 README：约 **188,000 个神经元**；Codex v888 快照（仅 proofread 细胞）**158,262** | 官方 README：约 **1.99 亿个预测突触**；Codex 默认 3+ 阈值下 **3,037,361 条连接** | [BANC-project README](https://github.com/htem/BANC-project)；Bates, Phelps, Kim, Yang et al., [Nature 2026 DOI](https://doi.org/10.1038/s41586-026-10735-w)、数据 [DOI](https://doi.org/10.7910/DVN/7WTH1N)；[Codex](https://codex.flywire.ai/api/download) |
| **MICrONS（2025）** | 小鼠视觉皮层（VISp + VISlm/VISrl/VISal，除 L1 极端层外全层） | **立方毫米级**（in vivo 尺寸 1.3 × 0.87 × 0.82 mm³） | 27,972 张 40 nm 标称切片（26,652 张实际成像）；平面约 **4 nm**；对齐体 **8 nm**；原始 **2 PB**；连续成像约 6 个月 | **>200,000 个细胞**；核分割 144,120（subvolume 65）；拆分多胞体对象后 **84,035 个独立分割神经元**；**75,909 个**做过功能成像的兴奋性神经元 | **5.24 亿个突触 cleft**（1.86 亿 + 3.37 亿）；检测 precision 96%、recall 89%，伙伴分配准确率 98% | MICrONS Consortium, Nature 640:435–447 (2025)，[DOI](https://doi.org/10.1038/s41586-025-08790-w)、[PMC11981939](https://pmc.ncbi.nlm.nih.gov/articles/PMC11981939/)、[门户](https://www.microns-explorer.org/) |
| **H01（2024）** | 人前中颞回（anterior middle temporal gyrus） | **略大于 1 立方毫米**（5,019 张切片，平均 33.9 nm 厚，共 0.170 mm；校正后 1.05 mm³） | 平面 **4 × 4 nm²**（压缩校正后 5.55 × 4 nm）；**z ≈ 33–34 nm**（不是 40 nm） | **约 57,000 个细胞**；**胶质:神经元 ≈ 2:1**，寡突胶质细胞最多 | **149,871,669 个突触**（≈1.5 亿）；分类后 1.113 亿兴奋性 / 3,860 万抑制性 | Shapson-Coe et al., Science 384:eadk4858 (2024)，[DOI](https://doi.org/10.1126/science.adk4858)、[PMC11718559](https://pmc.ncbi.nlm.nih.gov/articles/PMC11718559/)、[数据集站](https://h01-release.storage.googleapis.com/landing.html) |
| **MaleCNS v1.0（2026）** | **雄蝇全 CNS** | 脑中 + 视叶 + VNC（含完整颈连接） | **8 nm 各向同性**（发布体）；成像方式 FIB-SEM（同一标本的视叶论文口径） | **166,691 个神经元**、**11,691 个类型** | Codex 默认 5+ 阈值下 **6,242,118 条连接**；突触总数 **待核实** | 见第 0 节 |

**数据量 / 成本对照（可引用的「尺度感」数字）**
- MICrONS：原始 **2 PB**；H01：原始 1.8 PB → 对齐体 **约 1.4 PB**，是「第一个超过 1 PB 的 EM 数据集」，成像耗时 **326 天**。 — [PMC11981939](https://pmc.ncbi.nlm.nih.gov/articles/PMC11981939/)、[PMC11718559](https://pmc.ncbi.nlm.nih.gov/articles/PMC11718559/)
- MaleCNS：等效 **44 年**人力。 — [MRC LMB](https://mrclmb.ac.uk/news-events/articles/first-complete-connectome-of-male-fly-central-nervous-system-allows-for-unprecedented-male-female-brain-comparison/)
- **PROOFREADING 比例是这批数据集最诚实的一把尺子**：MICrONS 有 84,035 个独立分割神经元，但只有 **85 个兴奋性神经元是「axon + dendrite 全校对」**、1,188 个校对了树突、1,433 个校对了轴突（累计 1,046,656 次编辑）；H01 只**随机全校对 104 个神经元**。 — [PMC11981939](https://pmc.ncbi.nlm.nih.gov/articles/PMC11981939/)、[PMC11718559](https://pmc.ncbi.nlm.nih.gov/articles/PMC11718559/)
- H01 的「petavoxel」框架来自 Crick 1993 年「一立方毫米脑组织的精确接线图」的设想。 — [Shapson-Coe et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11718559/)

**Hen egg / 鸡胚视网膜：待核实（找不到任何一手来源）**
- 经 bioRxiv、Europe PMC、EMPIAR、ZEISS、Frontiers 多轮定向检索，**没有找到任何鸡/母鸡全视网膜连接组，也没有名为 "Hen egg" 的数据集**。没有一手来源 → 不给数字。
- 唯一能确认存在的近邻资源是**人中央凹视网膜连接组**：Kim et al., PNAS 123(33):e2603286123 (2026)，[DOI](https://doi.org/10.1073/pnas.2603286123)、[预印本](https://www.biorxiv.org/content/10.1101/2025.04.05.647403v3)（纳米级重建，约 3,000 个细胞分为 51 个神经元类型 + 3 个胶质类型；摘要未给 mm³ 体积或突触总数）。
- 禽类视网膜确实存在的工作是**光学显微镜**而非 volEM：[Front. Cell. Neurosci. 2025](https://doi.org/10.3389/fncel.2025.1558605)。
- **注意区分「H01 的 1 mm³ 人皮层」与「hen egg」**，不要混用。

**MaleCNS 的定位（一句话）**：它是**首个雄蝇、首个把脑与 VNC 通过完整颈连接起来的全 CNS 突触级连接组**，规模与 FAFB 同量级但覆盖范围更大（多了整个 VNC 与完整 SEZ），因此可以与 FAFB/雌蝇做首次全脑、突触分辨率的跨性别比较。 — [Janelia Male CNS 页](https://www.janelia.org/project-team/flyem/male-cns-connectome)

---

## 附录 A：无法溯源 / 需要回填的条目清单（显式 待核实）

1. **MaleCNS 的成像像素与切片厚度（4×4×40 nm？）** —— 门户只公布重建后的 8 nm 体素；未找到可公开抓取的论文原文。
2. **MaleCNS 的成像方式在 VFB 与论文间冲突**（SBFSEM vs FIB-SEM）。
3. **MaleCNS 论文 Fig. S8E/S9e 的 precision-recall 具体数值**（T-bar 与 synapse 两个口径）。
4. **MaleCNS 的 `consensus_nt` 定义与递质预测不确定性（误差率）百分比**。
5. **`minconf-0.5` 中 0.5 的精确定义**（cleft score？pre/post 置信度的 min？）。
6. **FlyWire/FAFB 自动分割的错误率百分比**（Extended Data Fig. 2 的实际数值未读到）。
7. **果蝇中「小分子谷氨酸既可兴奋也可抑制」的一手权威来源**。
8. **神经递质预测中 biogenic amines 与 neuropeptides 在 MaleCNS 里的完整类别与验证状态**（MaleCNS 场景只暴露 7 类 + unknown；neuropeptide 在 MaleCNS 的 `body-annotations` 里是否存在**待核实**）。
9. **neuropil 缩写中的以下几条**（第 4.4 节的其余条目均已由 FBbt 核验）：`LH`（OLS 只返回侧角神经元 LHN FBbt:00048293，未找到 neuropil 术语）、`SNP`、`ACA`、`ROB`、`RUB`、`RID`、`RO`、`ALA`、`UNS`，以及 `LAM`/`MED`/`LOB` 这三个「三字母版」（FBbt 的规范缩写是 LA/ME/LO/LOP）。
10. **hemilineage 后缀与 Notch 的映射** —— 已确认**不是**固定规则（见 5.2 末尾）：后缀是**逐 lineage 不同的位置标签**，只有一部分 lineage 有显式 Notch 术语。仍需逐 lineage 补齐：FBbt 中有显式 Notch ON/OFF 术语的 lineage 共多少个。
10b. **Hartenstein 前缀的已发表全称**：BLD、BLP、BLV、DAL、DAM、DPM、TR、LB、GA、MX、MD（BA/BLA/CM/CP/DPL 已核验）。
10c. **注释表 `__prim` 后缀的确切含义**（推断为 "primary"，README 未定义）。
10d. **hemibrain 与 MANC 的 neuropil 总数**（hemibrain ROI 是嵌套层级而非扁平清单；MANC 只有定性描述）。
10e. **「hemilineage 作为稀疏性/正则化先验」的方法学原文** —— Schlegel 2024/2021 的所有全文端点本轮均失败（EuropePMC `/fullTextXML` → HTTP 406，nature.com → idp 重定向）；最接近的可溯源证据是「NBLAST 聚类 hemilineage → morphology group」。
10f. **「Ito/Lee 前缀 = 投射靶 neuropil 缩写」这条通则的原文句子** —— FBbt 只提供交叉引用（如 ALad1 ≡ BAmv3），没有通则陈述；本报告按推断处理。
11. **MaleCNS 的突触总数**（论文摘要未给；Codex 只给阈值后的连接数）。
12. **H01 的神经元/胶质/轴突分别计数**（论文只给 ~57,000 总细胞数 + 胶质:神经元 2:1 的比例；由比例反推的 ~19k/38k 是算术推断，不是论文数字）。
13. **hemibrain 的单突触总数**（"20 million" 官方口径是 *connections*，不是单突触数；文献里的「1,400 万突触」为二手口径）。
14. **C. elegans「~7,000 化学突触 / ~2,000 间隙连接 / ~500 间隙连接」** —— 无一手来源支持；1986 年确证数字是 ~5,000 化学突触、2,000 NMJ、600 间隙连接。1986 年工作「耗时多少年」也**待核实**。
15. **「Hen egg / 鸡胚视网膜」数据集** —— **完全找不到一手来源**，应视为未确认，而不只是未引用。
16. **H01 的体素 z 分辨率是 ~33–34 nm，不是 40 nm**；若页面写「4×4×40 nm」，需注明是近似。
17. **Codex Neuropils 应用需要 Google 登录**；`/api/neuropils`、`/app/neuropil_list` 均 404，因此**无法直接链接或抓取 Codex 的 neuropil 列表**。替代方案：用 `Supplemental_file4_hemilineages_clustering.csv` 的 `nps` 列（每个神经元 top-3 支配 neuropil）。
18. **`LAM`/`MED`/`LOB` 在 MaleCNS 场景里实际写作 ME/LO/LOP**，不要与 FBbt 的 LA 混用（第 4.2 节表格中的 LAM/MED/LOB 是常见误写，请以 4.4 节的 LA/ME/LO/LOP 为准）。

## 附录 B：最值得直接读的一手来源（推荐顺序）

1. [male-cns.janelia.org](https://male-cns.janelia.org/) → [Download 页](https://male-cns.janelia.org/download/)（数据产品与分辨率的第一手说明）
2. [MaleCNS Neuroglancer 场景 JSON](https://storage.googleapis.com/flyem-male-cns/v1.0/male-cns-v1.0.json)（**最高信息密度**：分辨率、ROI 清单与数量、递质编码、逐突触属性名、ground-truth 图层、跨数据集 mesh 图层）
3. [VFB — EM Imaging and Reconstruction](https://www.virtualflybrain.org/docs/concepts/em-reconstruction/)（流水线四阶段 + 每阶段误差来源，带一手文献）
4. [VFB — Connectivity Data](https://www.virtualflybrain.org/docs/data/connectivity/)（edge 的语义、跨数据集重叠陷阱、默认 5 突触阈值）
5. [Codex FAQ](https://codex.flywire.ai/faq)（字段表、阈值表、坐标系、ID 语义）
6. [Codex About FlyWire](https://codex.flywire.ai/about_flywire)（数据来源与致谢归属）
7. [fafbseg — FlyWire segmentation 教程](https://fafbseg-py.readthedocs.io/en/latest/_sources/source/tutorials/flywire_segments.rst.txt)（root ID / supervoxel / materialization）
8. [neuprint-python Queries](https://connectome-neuprint.github.io/neuprint-python/docs/queries.html)（weight / weightHP / bodyId / ROI 层级)
9. [Dorkenwald et al. 2024 Nature（PMC11446842）](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446842/) 与 [Schlegel et al. 2024 Nature（PMID 39358521）](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-024-07686-5%22&resultType=core&format=json)
10. [Eckstein, Bates et al. 2024 Cell](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2024.03.016%22&resultType=core&format=json)（递质预测 87/94/91%）
11. [Yu et al. 2025（新突触检测）](https://www.biorxiv.org/content/10.1101/2025.07.11.664377v1)
12. [Janelia: Recipe for a Connectome](https://www.janelia.org/project-team/flyem/blog/recipe-for-a-connectome)（工程视角的 proofreading 成本模型）
13. **EBI OLS4 查 FBbt 本体** —— 本报告用来核验全部 neuropil 缩写与 hemilineage 命名方案的方法，可直接复现：
    - neuropil 缩写：`https://www.ebi.ac.uk/ols4/api/search?q=<TERM>&ontology=fbbt&rows=20&fieldList=label,obo_id,exact_synonyms,description`
    - 全部成体 lineage clone：`https://www.ebi.ac.uk/ols4/api/search?q=lineage%20clone&ontology=fbbt&rows=400&fieldList=label,obo_id`
    - hemilineage 神经元：`https://www.ebi.ac.uk/ols4/api/search?q=%22hemilineage%20neuron%22&ontology=fbbt&rows=400&fieldList=label,obo_id`
14. **FlyWire 注释表原始 CSV**（含 `ito_lee_hemilineage` / `hartenstein_hemilineage` 双列）：
    [Supplemental_file3_summary_with_ngl_links.csv](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/Supplemental_file3_summary_with_ngl_links.csv)
    [Supplemental_file1_neuron_annotations.tsv](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/Supplemental_file1_neuron_annotations.tsv)
    [列定义 README](https://raw.githubusercontent.com/flyconnectome/flywire_annotations/main/supplemental_files/README.md)
15. [Court et al. 2020 果蝇 VNC 系统命名法](https://doi.org/10.1016/j.neuron.2020.08.005)（MANC/BANC 的 VNC 区域名）
16. [Ito et al. 2014 昆虫脑系统命名法](https://doi.org/10.1016/j.neuron.2013.12.017)（Ito-2014 的原始出处；其缩写在本体里被标为 "BrainName official abbreviation"）

> **写页面时的引用纪律**：本报告对**每一条**都给了 URL；标 **待核实** 的条目在附录 A 中逐条列出。最容易被写错的三处是：(1) 把 Codex 的「connections」当突触数；(2) 把 hemilineage 的后缀当 Notch 代码；(3) 把 H01 的 z 步长写成 40 nm（实际 ~33–34 nm）。
