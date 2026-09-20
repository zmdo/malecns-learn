# MaleCNS v1.0 — 定量事实抽取（用于硬件 sizing）

> 抽取范围：本地仓库 `E:\code-design\dianzinao-research\malecns\` 全部文件（含 `README.md`、`malecns-study-guide.md`、`malecns-factcheck-2026-09-17.md`、`MaleCNS_连接组学基础_中文报告.md`、`phase0/1/2.html`、`neuprint.html`、`index.html`、`malecns_scale.py`、`assets/`、`tools/`、`_official/`、`_papers/`）。
> 每条事实后给出**仓库内文件 + 行号**（或逐字引句）；仓库文本给出 URL 时一并附上。
> **找不到的一律写「未找到」，不做推测。**

## 0. 语料与口径警告（先读）

| 事实 | 出处 |
|---|---|
| 仓库内**有 Berg 论文全文**（bioRxiv 预印本 v2，CC-BY 4.0）：`assets/papers/berg.js`，`meta.paras = 201`，`meta.chars = 163440`，`meta.pmcid = "biorxiv:2025.10.09.680999"`，`meta.license = "CC-BY 4.0（预印本）"` | `assets/papers/berg.js` 文件头；引句见该文件 `meta` 字段；PDF <https://www.biorxiv.org/content/biorxiv/early/2025/10/30/2025.10.09.680999.full.pdf> |
| **仓库明确声明正文是预印本、不是 Cell 正式版**，且两版数字有差异（预印本 166,691 神经元 / 11,691 类型；正式版 166,700 / 11,710） | `assets/papers/berg.js` 的 `meta.preprint_note`：「本页正文来自 bioRxiv 预印本（CC-BY 4.0），不是 Cell 正式版。两者数字有差异…引用请以正式版为准」 |
| 下文凡标 **【预印本】** 的数字来自 `berg.js`；标 **【正式版/核查】** 的来自 `malecns-factcheck-2026-09-17.md`；标 **【实测】** 的来自 `phase1.html` 记录的 2026-09-17 neuPrint 匿名 API 实测 | — |
| Cell DOI `10.1016/j.cell.2026.08.015`；Cell 189(18):5504–5526.e15；PMID 42691995 | `malecns-factcheck-2026-09-17.md:16-17`；URL <https://pubmed.ncbi.nlm.nih.gov/42691995/> |

---

## 1. 图的规模、密度与度分布

### 1.1 节点/边/接触点的官方口径

| 量 | 值 | 出处（文件:行 或 引句） |
|---|---|---|
| 神经元数（预印本） | **166,691** | 【预印本】`berg.js` 摘要："This contains 166,691 neurons spanning the brain and nerve cord… and 11,691 types" |
| 神经元数（正式发表 + Codex） | **166,700** | `malecns-factcheck-2026-09-17.md:35`；URL <https://pubmed.ncbi.nlm.nih.gov/42691995/>、<https://male-cns.janelia.org/media/> |
| **图定义（关键引句）** | 「The neuron segmentation and synaptic connections jointly define a connectome graph containing **25.6M edges between 166,391 neurons**.」 | 【预印本】`berg.js` Results（第 20 段）。注意：**166,391 是有 superclass 的神经元**，比 166,691 少 300 |
| 边数（未阈值，官方作者计数 notebook v0.9） | **25,563,426** | `malecns-factcheck-2026-09-17.md:37`；`phase0.html:873`；URL <https://raw.githubusercontent.com/flyconnectome/2025malecns/main/supplemental_data/quantify-neuron-connections.ipynb> |
| 边数（≥5 突触阈值，同 notebook） | **6,237,402** | 同上（`phase0.html:874`） |
| 连接数（Codex MCNS v1.0 界面，默认 5+） | **6,242,118** | `malecns-factcheck-2026-09-17.md:37,48`；URL <https://codex.flywire.ai/api/download?dataset=fafb> |
| 「25,582,938」这个整数 | **无法坐实（待核实）** | `phase0.html:929-930`：「25,582,938 这个整数无法坐实，引用时请改用官方 notebook 的 25,563,426（未阈值）或 6,237,402（≥5 突触）」 |
| 社区 Traced 子图 | 165,122 神经元 / 25,563,197 边 | `malecns-factcheck-2026-09-17.md:36,49`；URL <https://github.com/Ibtisam-Mohammad/Fly.exe> |
| 突触前位点（presynapse）总数 | **46 million** presynapses | 【预印本】`berg.js` Results："46 million presynapses connected to 312 million PSDs were automatically detected with an average precision/recall of 0.82/0.81" |
| 突触后密度（PSD）总数 | **312 million** PSDs | 同上 |
| 「突触接触点」口径 | 124,177,617（整数待核实）；官方新闻 **124.2 million synapses** | `phase0.html:531-534`；URL <https://www.science.org/content/article/new-connectome-shows-all-124-million-contact-points-fruit-fly-s-nervous-system> |
| 细胞类型数 | 11,691（预印本）/ **11,710**（正式版） | `malecns-factcheck-2026-09-17.md:146-147` |
| 成像体积 | **160 teravoxels**，8×8×8 nm 各向同性，**0.082 mm³** | 【预印本】`berg.js` Results："an image volume of 160 teravoxels at 8×8×8 nm isotropic resolution (0.082 mm3 total volume)" |
| 类型级图 | **8,258 节点**（细胞类型），**3.74M 边**（类型间突触连接数加权） | 【预印本】`berg.js` Results："8,258 nodes represent cell types … while 3.74M edges are defined by the number of synaptic connections between types" |

### 1.2 派生量（`malecns_scale.py` 实跑输出，输入 N=166,700 / E=25,582,938 / S=124,177,617）

> 脚本本身 `malecns_scale.py:4-8` 把这组输入标为「official measurements (as given in fragment)」。**其中 E 与 S 已被核查标为待核实**，故下列派生值属「量级可用、精度不可引用」。

| 派生量 | 值 | 脚本行 |
|---|---|---|
| 有序对总数 N(N−1) | 27,788,723,300 | `malecns_scale.py:17-18` |
| 密度 ρ = E/(N(N−1)) | **9.206230e-04 = 0.09206 %** | `malecns_scale.py:19-21` |
| 1 / ρ | 1 条连接 / ~1,086 有序对 | `malecns_scale.py:22-24` |
| 空对比例 | 99.90794 % | `malecns_scale.py:27` |
| **平均入度 = 平均出度** d̄ = E/N | **153.466935** | `malecns_scale.py:63-64` |
| 每神经元平均接收接触点 S/N | **744.9167** | `malecns_scale.py:65` |
| 每条边平均接触点 s̄ = S/E | **4.85392323** | `malecns_scale.py:35-37` |
| 全连接时扇入 N−1 | 166,699 | `malecns_scale.py:66` |
| 稀疏存储 CSR = 4(E+N+1)+4E | **205,330,308 B = 0.191229 GiB** | `malecns_scale.py:87,92-93` |
| 稠密 float32 = 4N² | 111,155,560,000 B = **103.5217 GiB** | `malecns_scale.py:87-89` |
| 稠密/稀疏比 | 541.35× | `malecns_scale.py:94` |
| MaleCNS / FlyWire 神经元比 | 1.19708 | `malecns_scale.py:74` |
| MaleCNS / FlyWire 接触点比 | 2.27849 | `malecns_scale.py:75` |
| 每神经元接触点比（MaleCNS / FlyWire） | 1.903365 | `malecns_scale.py:78` |

`phase0.html:555` 另给：「平均每条连接 4.85 个接触点」= 124,177,617 / 25,582,938 —— 页面自己标注「两个输入里有一个待核实，所以 4.85 请当作量级示意」。
`phase0.html:878` 用未阈值口径给 s̄ ≈ **4.86**，并强调「**s̄ 刚好卡在 5 这个阈值上**」。

### 1.3 **未找到（明确标注）**

- **度分布（in-degree / out-degree distribution）**：仓库中**没有任何 MaleCNS 的度分布图、均值/中位数/极值统计、幂律或重尾拟合**。仓库把「算入度/出度」列为**待做任务**：`malecns-study-guide.md:105`（阶段 3 过关标准「建稀疏矩阵、算入度/出度」）、`:237`（D3–4「算入度/出度/类型统计」）、`phase1.html:922`（「阶段 3 **算完度分布后**，你可以回来验证这个观察」）。
- **最小/最大度、hub 神经元及其最大度**：未找到。仓库只给局部实测点（见 1.4）。
- **扇入/扇出分布**：未找到。
- **小世界（small-world）定量指标**（特征路径长度、σ/ω）：未找到。仓库只有定性表述 `phase1.html:556`（「这本身就是对『小世界网络』的直观感受」）与 Dorkenwald 译文 `notes-dorkenwald-e.js:171`（「这一网络的『小世界』性质在 Lin 等人 49 中有更详细的讨论」）。
- **聚类系数（clustering coefficient）数值**：未找到 MaleCNS 的值。只有一句关于**阈值稳健性**的原文（见 2.4）。
- **互易性（reciprocity）数值**：未找到 MaleCNS 的值。同上。
- **rich club（富俱乐部）**：未找到 MaleCNS 的任何 rich-club 分析。仓库只在两处出现该词：① Codex 字段词汇表 `connectivity_tag` 的取值之一（`MaleCNS_连接组学基础_中文报告.md:452`：「rich club、broadcaster、integrator、attractor、repeller、reciprocal、feedforward-loop participant、3-cycle participant 等」）；② Dorkenwald 译文 `notes-dorkenwald-j.js:18,133`（FlyWire 的 connectivity tags）。

### 1.4 仓库内仅有的「单点度/规模」实测（可作 sanity check，不可当分布）

| 对象 | 值 | 出处 |
|---|---|---|
| DNg13_L bodyId **11074**，DNg13_R bodyId **512006** | 实测 | `phase1.html:721, 883-885`；`tools/test-neuprint-console.js:183-184` |
| DNg13 的 `pre` = 2,127 / `post` = 6,500 / `upstream` = 6,500 / `downstream` = 15,479 | 实测（突触计数，非度） | `phase1.html:726-728` |
| DNg13 输出超类分布：`vnc_intrinsic` **373 个目标**、`vnc_motor` **17 个目标** | 实测 | `phase1.html:901-903` |
| DNg13 输出里 35 个 `ascending_neuron`、42 个其它 `descending_neuron` | 实测 | `phase1.html:917-918` |
| DNg13 最强输入 TOP5：CB0244 w=167、LAL073 w=161、GNG532 w=156、DNg97 w=140、DNpe027 w=127 | 实测（这些是**局部最大权重样本**，不是全库最大） | `phase1.html:734-738` |
| DNg13 最强输出 TOP3：IN08B004 w=159、AN10B009 w=135、Tergopleural/Pleural promotor MN w=60 | 实测 | `phase1.html:745-748` |
| MN9_L bodyId 10331，MN9_R bodyId 16949，`cb_motor` | 实测 | `phase1.html:983` |
| MN9 输入 TOP5：DNge062 w=556、GNG015 w=478、GNG120 w=443、GNG095 w=436、GNG117 w=413 | 实测 | `phase1.html:786-790` |
| BM_Taste = 40 实例，MaleCNS 里唯一的味觉感觉类型 | 实测 | `phase1.html:759, 1013-1015` |
| BM_Taste 下游：94 % 权重落在 cb_intrinsic（327 目标 / 22,063）、descending_neuron（132 目标 / 13,078） | 实测 | `phase1.html:1017-1019` |

**旁证：FlyWire（非 MaleCNS）的度统计**（可作对照，切勿混用）：
- 「In degree and out degree of intrinsic neurons in the fly brain are linearly correlated (R² = 0.76)」（`assets/papers/dorkenwald.js` Fig.3g 图注）
- 「Connections in the fly brain are usually multisynaptic, as in this example of neurons connecting with 71 synapses」（同上 Fig.3e）
- 内在神经元 median path length **685 µm**（同上 Fig.3d 正文）
- `assets/papers/notes-dorkenwald-h.js:161-162`：「阈值选择对**宏观网络统计**（互易性、聚类系数）**不敏感**，但对**度数、密度这类直接计数**敏感」

---

## 2. 突触权重语义、阈值与接触点/连接的关系

### 2.1 定义

| 事实 | 出处 |
|---|---|
| **weight = 该 body 对之间被检出的突触个数**，不是概率、不是电流 | `MaleCNS_连接组学基础_中文报告.md:141`：「weight（权重）：就是突触计数，不是『概率』也不是『电流』」；URL <https://connectome-neuprint.github.io/neuprint-python/docs/queries.html> |
| 「一对神经元之间可以有多个突触」；连接 = 把 A→B 的所有接触点**去重合并**成一条有向边 | `malecns-study-guide.md:27`；`phase0.html:849-852` |
| 权重是**建模选择**，不是数据属性 | `phase0.html:855`「权重是选择，不是事实」 |
| 形式化：`S = Σ_{i,j} c_ji`（接触点总数）；`E = |{(i,j): c_ji ≥ 1}|` | `phase0.html:864-874` |
| 删阈值可证明的上界：被删掉的接触点 ≤ **4E** 个 | `phase0.html:899-900` |
| neuPrint 还提供更细的权重族：`weightHP`（只统计置信度高于 `preHPThreshold`/`postHPThreshold` 的突触）、`weightAxonAxon`、`weightAxonDendrite`、`weightDendriteDendrite`、`weightDendriteAxon` | `MaleCNS_连接组学基础_中文报告.md:141`；URL <https://connectome-neuprint.github.io/neuprint-python/docs/queries.html> |
| ROI 分层会让同一批突触在 `roi_counts_df` 里**重复计数**（层级 ROI 中一个突触落在多个 ROI 内） | `MaleCNS_连接组学基础_中文报告.md:140,178` |

### 2.2 两种口径与「≥5 阈值」的效果

| 事实 | 出处 |
|---|---|
| flat-connectome 三个/七个文件名内嵌 `minconf-0.5` → 按**置信度阈值 0.5** 导出 | `malecns-factcheck-2026-09-17.md:73`；`MaleCNS_连接组学基础_中文报告.md:151`；URL <https://male-cns.janelia.org/download/> |
| neuPrint/Codex 的 **MCNS 默认 ≥5 突触** | `malecns-factcheck-2026-09-17.md:74`；Codex FAQ 原文引句：「Default minimum thresholds are dataset-specific: FAFB 5+ / BANC 3+ / MANC 1+ / MAOL 1+ / **MCNS 5+**」；URL <https://codex.flywire.ai/faq> |
| 各数据集默认最小突触数表 | FAFB **5+**、BANC **3+**、MANC **1+**、MAOL **1+**、MCNS **5+** —— `MaleCNS_连接组学基础_中文报告.md:158-165` |
| **min confidence 作用在突触层，≥5 阈值作用在边层** | `README.md:78` |
| `minconf-0.5` 里 0.5 的**精确定义官方未逐字给出**（cleft score？pre/post 取 min？）→ 待核实 | `MaleCNS_连接组学基础_中文报告.md:155`（原文标注「待核实」，附录 A 第 5 条 `:564`） |
| **阈值效果（核心数字）**：25,563,426 → **6,237,402**，即**只剩 24.4 %**；而接触点 ≈1.242 亿 → 仍约 1.2 亿量级，**基本不动** | `phase0.html:914-915`；`phase0.html:558`「未阈值 2,556 万条边降到 624 万条（约剩 1/4），而接触点仍是 1.24 亿量级」 |
| 为什么选 5：**突触数分布没有任何双峰性可以定阈值**，因此「每条连接 5 个突触」是 **reasonable but arbitrary**（原文引句） | `assets/papers/notes-dorkenwald-h.js:146-148`；Dorkenwald 原文（`assets/papers/dorkenwald.js`）："display any bimodality that could be used to set the threshold. Therefore, the choice of 5 synapses per connection is a reasonable but arbitrary one." |
| 弱边为何砍：VFB 原文 "**Weak edges (one or two synapses) are the least reliable and are commonly thresholded out.**" | `MaleCNS_连接组学基础_中文报告.md:167`；URL <https://www.virtualflybrain.org/docs/concepts/em-reconstruction/> |
| VFB 层面的跨数据集连接查询默认阈值也是 **5 synapses** | `MaleCNS_连接组学基础_中文报告.md:168`；URL <https://www.virtualflybrain.org/docs/concepts/em-reconstruction/> |
| Codex 允许**提高**阈值但不能低于数据集默认值 | `MaleCNS_连接组学基础_中文报告.md:169` |
| **注意**：Berg 预印本正文**没有**出现「≥5 突触」这个阈值约定；预印本给的图是 25.6M 边（未阈值）。≥5 是 Codex/neuPrint 默认与 2025malecns notebook 的 `weight >= 5` | 检索 `berg.js` 全文（"at least 5"/"5 synapses"/">4" 均无正文命中）；`malecns-factcheck-2026-09-17.md:74,78` |

### 2.3 权重分布：仓库里唯一有源的分布陈述（全部来自 Berg 预印本）

| 引句/事实 | 出处 |
|---|---|
| 「the distribution of connectome edge weights is **highly skewed**: most synapses belong to strong edges that are reliably observed within and across datasets; but the **majority of edges are weak and unreliable**」 | 【预印本】`berg.js` Results |
| 「**around 60 % of single-synapse connections** in one hemisphere are **not at all present** in another hemisphere from either the same or another brain」 | 【预印本】`berg.js` Results |
| 要达到「同构边在两性间 90 % 可复现」需 **>10 个突触**（male→female 方向）；反方向阈值 **>7 个突触** | 【预印本】`berg.js` Results：「To achieve a 90% probability of an isomorphic edge in the male also being present in the female dataset, it needs to consist of >10 synapses. In the opposite direction, that threshold is >7 synapses – likely due to the generally stronger edges in the male CNS.」 |
| 「Because edge weight distribution is heavily skewed with many weak edges (Fig S8b), **around 80 % of all cross-matched edges fall below these thresholds**. Crucially though, the remaining above-threshold edges collectively contain **90 % of all synapses in the male (88 % in female)**」 | 【预印本】`berg.js` Results |
| 类型间 3.74M 边中 **381k 边（10 %）**显著异形（FDR-corrected p ≤ 0.1） | 【预印本】`berg.js` Results |
| 图的分块建模里，突触计数（边权）用**离散几何分布**拟合最优 | 【预印本】`berg.js` Methods：「synapse counts (edge weights) are modelled with a discrete geometric distribution, as determined to be optimal in the larval brain」 |

### 2.4 阈值对宏观统计的稳健性（唯一有源的一句）

> 「By analysing the network properties of the FlyWire brain connectome, Lin et al. found that **statistical properties of the whole-brain network, such as reciprocity and clustering coefficient, are robust to our choice of threshold**.」
> — `assets/papers/dorkenwald.js` Methods（Connection threshold）；中文标注见 `assets/papers/notes-dorkenwald-h.js:149-151`。
> ⚠️ 这是 **FlyWire** 的结论，不是 MaleCNS 的测量。

### 2.5 **未找到**

- `connectome-weights-male-cns-v1.0-minconf-0.5.feather` 的 **min / max / median 权重**：未找到（仓库只给「源、目标、接触数」的字段语义与平均 4.85/4.86）。
- 全库最大权重（单位突触数）：未找到。`neuprint.html` 只有一条**用来查**它的预设（预设 21「找权重最高的连接 … ORDER BY w DESC LIMIT 15」，`neuprint.html:355-358`），仓库未记录结果。

---

## 3. 神经递质：类型数、预测方法、置信度、优势递质、符号假设

### 3.1 数量与编码

| 事实 | 出处 |
|---|---|
| **Ground-truth 资源覆盖 10 种递质**：acetylcholine、dopamine、GABA、glutamate、glycine、histamine、nitric oxide、octopamine、serotonin、tyramine；数据为**三态**（−1 不存在 / +1 存在 / 0 未测） | 【预印本】`berg.js` Methods → "Neurotransmitter prediction" |
| **模型只预测 7 类**（网络输出归一化到 7 个分数，和为 1，取最大者） | 【预印本】同上：「The network outputs a normalized score for each of the **7 neurotransmitters** considered」 |
| **Neuroglancer 场景的编码恰好是 7 类 + unknown**：`0 ACh / 1 dopamine / 2 GABA / 3 glutamate / 4 histamine / 5 octopamine / 6 serotonin / 7 unknown` | `_official/male-cns-v1.0.json` 的 `presyn`/`postsyn` 图层 shader（逐字 `#define acetylcholine_code 0` … `#define unknown_nt_code 7`）；亦见 `MaleCNS_连接组学基础_中文报告.md:394-401` |
| 每突触还带两个连续量：`predicted_nt_prob`（概率）与 `nt_tbar_confidence_score`（T-bar 置信度）；另有 `tbar_fanout` | 同上 shader（`prop_predicted_nt_prob()` / `prop_nt_tbar_confidence_score()` / `prop_tbar_fanout()`）；`MaleCNS_连接组学基础_中文报告.md:400` |
| Codex 侧另有 `nt_type`（预测）vs `nt_type_verified` / `neuropeptide_verified`（人工整理），**两者可能冲突** | `MaleCNS_连接组学基础_中文报告.md:446-447`；`phase0.html:1426-1429` |

### 3.2 预测方法与置信度（预印本 Methods 逐条）

| 事实 | 出处 |
|---|---|
| 方法：**ResNet50 图像分类器**，输入为**以 T-bar 为中心、跨度 640 nm³ 的 ROI** | `berg.js` Methods → "Neurotransmitter prediction" |
| 训练：SGD，**100,000 个 mini-batch × 32 体**；AdamW，lr 1×10⁻⁴，β=(0.9,0.999)，λ=0.01 | 同上 |
| 训练集筛选：排除证据置信度 <3 的条目、移除共传递（多个 +1）实例、丢弃同一递质正负证据并存的类型；**80 %/20 % 神经元级划分**并验证到突触级仍然有效 | 同上 |
| 逐神经元聚合：`predictedNt` = 该神经元 preynapse 中最常见的预测 | 同上：「The database records the most frequent prediction among a neuron's presynapses in the predictedNt property」 |
| `celltypePredictedNt` = 同类型全部细胞汇总后最常见的突触前预测；对应置信度字段 `predictedNtConfidence` / `celltypePredictedNtConfidence` | 同上 |
| **置信度的定义**：每个突触前位点按「所属 segment 的整体预测（行）×该位点模型预测（列）」从**突触级混淆矩阵**取一个 confusion score；**segment 置信度 = 其全部突触前 confusion score 的平均** | 同上 |
| **置 unclear 的规则**：神经元/片段 **<50 个突触前位点** 或 `predictedNtConfidence < 0.5` → `predictedNt = unclear`；细胞类型 pooled **<100 个突触前位点** 或 `celltypePredictedNtConfidence < 0.5` → `celltypePredictedNt = unclear` | 同上 |
| **`consensusNt` = `celltypePredictedNt` 的副本**，但：① 有实验 ground truth 时覆盖模型预测；② **所有 octopamine 与 serotonin 结果一律置 unclear**（验证数据太少）；③ **`consensusNt` 是推荐使用字段** | 同上：「Additionally, all octopamine and serotonin results are set to unclear in consensusNt, owing to the relatively scant validation data used for those neurotransmitters. The consensusNt is the recommended property to use in most analyses.」 |
| 模型准确率（Eckstein, Bates et al. 2024，**FlyWire 全脑**）：**单突触 87 % / 单神经元 94 % / 已知细胞类型 91 %** | `MaleCNS_连接组学基础_中文报告.md:391`；URL <https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2024.03.016%22&resultType=core&format=json>；另 `assets/papers/notes-dorkenwald-h.js:130-134`（87 % / 94 %，训练集 3,025 个已知递质类型神经元，**假设 Dale 定律成立**） |
| MaleCNS 侧的独立验证：论文 Fig. S8E / Fig. S9e 给 T-bar 单独与「以突触为单位」的 PR 曲线，**具体数值待核实** | `MaleCNS_连接组学基础_中文报告.md:92,518` |
| 官方未逐字给出 `consensus_nt` 的定义与递质预测不确定性百分比 → **待核实** | `MaleCNS_连接组学基础_中文报告.md:411,563`（附录 A 第 4 条） |
| MaleCNS 的 neuropeptide 是否存在于 `body-annotations` → **待核实** | 同上 `:567`（附录 A 第 8 条） |

### 3.3 优势递质（composition）

| 事实 | 出处 | 适用数据集 |
|---|---|---|
| 全库递质构成：**胆碱能 ≈55 %、谷氨酸能 24 %、GABA 能 14 %、其余 7 %** 为 DA/OA/5-HT | `assets/papers/notes-shiu-d.js:47` | **FlyWire FAFB（雌性、仅脑）**，不是 MaleCNS |
| 613 个味觉响应神经元的递质构成：**ACh 52 % · GABA 25.9 % · Glu 17 % · 5-HT 2.9 % · DA 2.0 % · OA 0.2 %**；抑制性（GABA+Glu）合计 **42.9 %** | `assets/papers/notes-shiu-d.js:49-52` | 同上（FAFB） |
| Berg 预印本只说「feedforward 连接以**兴奋性为主**，feedback 连接的**抑制性比例更大**」，未给 MaleCNS 的递质构成百分比 | 【预印本】`berg.js` Results（"Across levels, feedforward synaptic connections have similar, predominantly excitatory, neurotransmitter compositions, while feedback connections have a larger inhibitory proportion."） | MaleCNS（定性） |

> ⚠️ **MaleCNS 的递质构成百分比：未找到。** 仓库没有任何 MaleCNS 的 ACh/GABA/Glu 计数表。

### 3.4 符号（兴奋/抑制）赋值与最脆弱的假设

| 事实 | 出处 |
|---|---|
| 连接组本身**不含符号信息**：VFB 原文 "**The sign of a connection is not visible in the wiring diagram.**" | `phase0.html:1404-1406`；`MaleCNS_连接组学基础_中文报告.md:417`；URL <https://www.virtualflybrain.org/docs/concepts/em-reconstruction/> |
| 社区建模约定：`s = +1 if ACh; −1 if GABA 或 Glu; 0 if 未知/仅调质/冲突` | `malecns-study-guide.md:127-130`；`phase0.html:944-947` |
| **约 3,718 个细胞递质符号不明**（对应编码 7 = unknown），模型里只能记 0 | `malecns-study-guide.md:130,226`；`phase0.html:1411-1412` —— 页面自标「这个数字来自指南，本次核查**未独立确认**」 |
| 把 Glu 归到抑制侧的理由：果蝇谷氨酸受体包含抑制性类型，「与脊椎动物的直觉相反」 | `phase0.html:1407-1409` |
| **最脆弱的假设 = 谷氨酸的符号**：把「Glu 是抑制性」改成「Glu 是兴奋性」是**唯一一个会实质性破坏结论**的假设 —— 「苦味与 Ir94e 是抑制性的」这一计算结果消失，光遗传实验的**假阳性率从 1 % 飙升到 16 %** | `assets/papers/notes-shiu-d.js:65-69` |
| 该结论的模型侧依据（Shiu，FAFB）：① 假设 GABA 与 Glu 为抑制性；② **每个神经元要么纯抑制要么纯兴奋**；③ cleft score 阈值取 50；④ 取每个突触前位点最高递质预测；⑤ 若 >50 % 突触前位点被判为抑制性则该神经元为抑制性；⑥ **多巴胺能、章鱼胺能、血清素能一律归入兴奋性**（简化） | `assets/papers/notes-shiu-d.js:40-46` |
| 「小分子 Glu 既可能兴奋也可能抑制」的一手权威来源 → **未找到**（报告显式标注待核实） | `MaleCNS_连接组学基础_中文报告.md:413-419` |

---

## 4. 空间结构：位置、脑区数、局部性、跨区距离

### 4.1 体积与体素

| 事实 | 出处 |
|---|---|
| 全 CNS 体积 **0.082 mm³**，体素 **8×8×8 nm 各向同性**，160 teravoxels | 【预印本】`berg.js` Results |
| 发布体素分辨率 8 nm 各向同性（对齐 EM 灰度体 + v1.0 神经元分割体） | `MaleCNS_连接组学基础_中文报告.md:18`；URL <https://male-cns.janelia.org/download/>；场景 JSON `dimensions: {x:[8e-9,"m"], y:[8e-9,"m"], z:[8e-9,"m"]}`（`_official/male-cns-v1.0.json`） |
| 细胞核分割 16 nm 各向同性；脑 neuropil ROI **256 nm**（**max value 96**）；VNC neuropil ROI **256 nm**（**max value 27**） | `MaleCNS_连接组学基础_中文报告.md:19,284-285`；URL <https://male-cns.janelia.org/download/> |
| 成像方式：**eFIB-SEM**，7 台系统，13 个月 | 【预印本】`berg.js` Results |
| 标本：5 日龄雄蝇，Canton-S G1 × w¹¹¹⁸，编号 **Z0720-07m** | 【预印本】`berg.js` Methods EM Sample Preparation；`malecns-factcheck-2026-09-17.md:127` |
| 仓内解码出的 ROI 分割信息（`_official/roi-info.json`，文件内容为 UTF-8 字节数组）：`data_type=uint64`、`num_channels=1`、`compressed_segmentation_block_size=[8,8,8]`；4 级金字塔：256 nm（size 2932×1714×1624）/512 nm（1466×857×812）/1024 nm（733×428×406）/2048 nm（366×214×203） | `_official/roi-info.json`（解码）；下载器 `tools/fetch_roi_volume.py:75-77,108-126`，默认 `--roi fullbrain-roi-v5 --scale 1024_1024_1024` |
| → 派生：256 nm 层覆盖 **750.6 × 438.8 × 415.7 µm**，体积 **≈0.137 mm³** | 由上一行数值计算（**派生值**，非仓库陈述）；注：仓库未记录该 info 文件属于哪个 ROI 图层，故 x/y/z 具体归属存疑 |

### 4.2 神经元 3D 位置与突触位置的数据载体

| 事实 | 出处 |
|---|---|
| soma 点云图层 `soma-points` → `precomputed://gs://flyem-male-cns/v1.0/malecns-v1.0-soma-points`，属性含 `kind`（soma/tosoma）、`is_vnc`、`birthtime`、`itoleeHl`、`trumanHl`、`top_input/output_compartment`、`top_input/output_neuropil`、`assigned_optic_column`、`top_input/output_optic_layer` | `_official/male-cns-v1.0.json` 的 `soma-points` 图层（shader 中 `prop_*` 调用） |
| 突触点云 `presyn` / `postsyn` → `precomputed://gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed/`，逐突触属性：`body_pre_u32`、`body_post_u32`、`predicted_nt`、`predicted_nt_prob`、`nt_tbar_confidence_score`、`tbar_fanout`、`compartment_pre`、`compartment_post`、`primary_roi`、`optic_column`、`optic_layer` | 同上（两张图层 shader 的 `prop_*` 调用） |
| T-bar 体密度图层 `tbar-cloud` → `precomputed://gs://flyem-male-cns/malecns-tbar-point-cloud-512nm-smoothed/`（**512 nm 平滑**） | 同上 |
| 官方突触 ground-truth 图层 3 个：`synapse-groundtruth`（`gs://flyem-male-cns/v1.0/synapse-ground-truth/malecns-v1.0-synapse-ground-truth-lines/`）、`synapse-groundtruth-boxes`、以及场景内的 `synapse-groundtruth` 属性 | 同上；`MaleCNS_连接组学基础_中文报告.md:93,519` |
| 网格坐标为**原始纳米坐标** | `README.md:200`「坐标为原始纳米坐标」；`assets/mcns-meshes.js` 的 `meta.units = "nm (原始坐标)"` |

### 4.3 脑区 / neuropil 计数 —— **仓库内部三套数字不一致，全部列出**

| 来源 | 脑 | VNC | 依据 |
|---|---|---|---|
| **README** | **84 个脑神经毡** | **24 个 VNC 神经毡** | `README.md:194-195`（逐字：`gs://flyem-male-cns/rois/fullbrain-roi-v5/mesh/<NAME>.ngmesh   84 个脑神经毡` / `gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0/mesh/   24 个 VNC 神经毡`） |
| **tools 下载脚本** | 84 | **23** | `tools/fetch_official_meshes.py:5-6`；`tools/fetch_roi_volume.py:5-6`（「VNC 神经毡（23 个）」） |
| **官方 Neuroglancer 场景图层** | `brain-neuropils` 列出 **89 个 segment id**（1–86 与 93、94、96）；`brain-neuropil-subcompartments` **199 个** | `vnc-neuropils` **23 个**；`vnc-nerves` **36 条**（id 2–37） | `_official/male-cns-v1.0.json` 各图层 `segments` 数组（逐个数出）；与 `MaleCNS_连接组学基础_中文报告.md:179-186` 的「约 90 个脑 ROI / 23 个 VNC neuropil / 36 条 nerve」一致 |
| **Download 页口径（经核查转述）** | ROI 索引**最大值 96** | ROI 索引**最大值 27** | `MaleCNS_连接组学基础_中文报告.md:284-285`；并注明「这两个数是 ROI 分割体的『索引最大值』，与 neuPrint 里『命名 ROI 的条数』不是严格同一个量」（`:286`） |
| **本仓库实际打包的网格文件** | **48 个** `.ngmesh` | **24 个** `.ngmesh` | `_official/meshes/fullbrain-roi-v5/` 与 `_official/meshes/malecns-vnc-neuropil-roi-v0/` 目录实枚举（脑：a'L(L)…WED(R) 共 48；VNC：ANm、CV、HTct(UTct-T3)(L/R)、IntTct、LegNp(T1/T2/T3)(L/R)、LTct、mVAC(T1/T2/T3)(L/R)、NTct(UTct-T1)(L/R)、Ov(L/R)、WTct(UTct-T2)(L/R) 共 24） |
| **page 口径** | 约 **90 个 ROI**（亚分区约 200 个） | **23 个**神经毡、**36 条**神经束 | `phase0.html:1168-1169` |

**结论**：拿去写文档时，安全的写法是「脑主分区 **89–96 个索引**（README 称 84 个网格）、VNC neuropil **23 个**（README 称 24 个）、VNC nerve **36 条**」，并注明口径。
分区来源（逐字）：「Brain neuropil compartment segmentation, **initialized via transfer from ROIs in JRC2018M and refined manually**」/「VNC neuropil compartment segmentation, **refined manually**」——`MaleCNS_连接组学基础_中文报告.md:284-285`，URL <https://male-cns.janelia.org/download/>。
正确 bucket：`gs://flyem-male-cns/rois/fullbrain-roi-v5` 与 `gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0`（不带 `malecns-` 前缀的写法是错的，`MaleCNS_连接组学基础_中文报告.md:285`）。
命名法权威：Ito et al. 2014 Neuron 81(4):755–765（DOI 10.1016/j.neuron.2013.12.017）；VNC：Court et al. 2020 Neuron 107(6):1071–1079（DOI 10.1016/j.neuron.2020.08.005）。

视叶的列/层 ROI：场景里左右半球各有 `ME(L/R)-columns`、`ME(L/R)-layers`、`LO(L/R)-columns`、`LO(L/R)-layers`、`LOP(L/R)-columns`、`LOP(L/R)-layers`，共 **12 个视叶列/层图层**（`_official/male-cns-v1.0.json`）。ME 列模块数：**884 个模块**（其中 790 个每类型恰 1 神经元），移除 5 个边缘模块后得 **879 个带六角坐标的列模块**（【预印本】`berg.js` Methods）。

### 4.4 连通性是局部还是长程

| 事实 | 出处 | 数据集 |
|---|---|---|
| 「the connectome provides…」性别特异/异形神经元的突触分布**空间上高度不均匀**，强烈偏好 protocerebrum 的高级整合区；lobula 与 gnathal ganglion 有较弱但仍显著的富集 | 【预印本】`berg.js` Results | **MaleCNS** |
| 「投射组中**最大的权重往往位于单个神经毡内部**，例如髓质内部或扇形体内部」 | `assets/papers/notes-dorkenwald-d.js:157`（Dorkenwald 译文） | **FlyWire** |
| 内在神经元占脑神经元 3/4（139,255 中 118,501 为脑内在） | `assets/papers/dorkenwald.js` Results | **FlyWire** |
| Berg：颈连接（neck connective）是**瓶颈**，下行/上行神经元约束脑↔VNC 的信息流；AN/DN 的 flow utilization 显著高于脑/VNC 内在神经元 | 【预印本】`berg.js` Results | **MaleCNS** |
| Berg：AN 与 DN 之间的连接以轴-树为主，但 **DN 内部 27 %、AN 内部 34 %** 的连接是**树-树（dendro-dendritic）**，另两种配对均为 4 % | 【预印本】`berg.js` Results（Fig 2l） | **MaleCNS** |
| 场景图注：`Fig 2c` 的流向图**省略了突触数少于 20k 的边** | 【预印本】`berg.js` Fig 2c 图注：「Edges with fewer than 20k synapses omitted.」 | MaleCNS（作图口径） |
| maxflow 分析用**每个突触前输入归一化**的图；flow 不利用连接符号 | 【预印本】`berg.js` Results/Methods | MaleCNS |

### 4.5 空间范围（派生自 `assets/mcns-meshes.js`，**抽稀后网格**）

> `assets/mcns-meshes.js` 的 `meta.decimation` 逐字：`method = "vertex clustering (grid snapping)"`, `rawTriangles = 8860924`, `keptTriangles = 31838`, `ratio = 0.0036`；`meta.downloaded_bytes = 159443156`（≈152 MiB）；`meta.structures = 26`。README 另给：原始 8,860,924 三角形 / 283 MB → 仓库内 **31,838 三角形（0.36 %）/ 973 KB**（`README.md:220-225`）。

| 派生量 | 值（nm → µm） |
|---|---|
| 26 个结构合并包围盒 | x 33,022 – 741,808 nm（**708.8 µm**）；y 38,917 – 553,216 nm（**514.3 µm**）；z 81,409 – 1,071,870 nm（**990.5 µm**） |
| 视叶 LA 到腹神经节 VNC-AB 的 z 跨度 | 152,065 → 1,071,870 nm ⇒ **≈920 µm**（头-腹纵跨） |
| 各结构包围盒（用于估算体积/距离的输入，单位 nm）：AL 274946,161025,81409 – 499709,286465,169687；MB 264803,58378,81409 – 505635,286465,292539；CX 330858,108569,139265 – 446979,210683,281514；SEZ 289026,254575,122101 – 494010,378307,332263；LA 33022,118650,152065 – 741808,429819,262654；ME 44818,106569,176467 – 724216,418476,340990；LOP 114250,142882,285286 – 661232,365222,339968；VNC-T1 269056,361728,527616 – 529664,539894,688840；VNC-AB 309504,325887,415051 – 491734,499456,1071870；VNC-INT 336113,366923,544097 – 462090,479969,822016 | `assets/mcns-meshes.js` 各结构 `bbox` |

**视叶 → VNC 的 tract 长度：未找到。** 仓库中**没有任何**通道/轴突束长度测量（nm/µm）的数值。仅有的相关信息：
- 脑与 VNC 在颈连接处拼接时两切面之间残留 **~25° 夹角**（【预印本】`berg.js` Methods：「An angle difference of ∼25 degrees remained between the surfaces.」）
- 场景里存在 `cervical fiber bundle` 概念、被用于分割约束（【预印本】`berg.js` Methods）
- 网格包围盒可作为几何上界（见上表），但**抽稀网格不可用于定量测量**（`README.md:226`：「不可用于体积、表面积等定量测量」）

---

## 5. 数据格式、文件大小与下载/查询接口

### 5.1 flat-connectome feather 清单（**7 个文件，合计约 24 GB**）

> 出处：`malecns-factcheck-2026-09-17.md:225-239`（表格 + 前缀）；`phase0.html:1756-1772`（同表）；`malecns-study-guide.md:75-82`（**旧的错误口径**：3 个文件 1.1 GB，已被核查推翻）。
> URL 前缀：`https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/`
> 官方下载页：<https://male-cns.janelia.org/download/>

| # | 文件名 | 大小 |
|---|---|---|
| 1 | `body-annotations-male-cns-v1.0-minconf-0.5.feather` | **13 MB** |
| 2 | `body-neurotransmitters-male-cns-v1.0.feather` | **42 MB** |
| 3 | `body-stats-male-cns-v1.0-minconf-0.5.feather` | **780 MB** |
| 4 | `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | **1.1 GB** ← 指南里「1.1 GB」的真正出处 |
| 5 | `syn-points-male-cns-v1.0-minconf-0.5.feather` | **12.7 GB** |
| 6 | `syn-partners-male-cns-v1.0-minconf-0.5.feather` | **6.8 GB** |
| 7 | `tbar-neurotransmitters-male-cns-v1.0.feather` | **2.7 GB** |

「如果只是要建连接矩阵，**第 1 + 4 个文件就够**（约 1.1 GB）」——`phase0.html:1770-1772`。
第三方独立记录：「**seven** checksum-locked flat-connectome tables」——`malecns-factcheck-2026-09-17.md:237`，URL <https://github.com/Ibtisam-Mohammad/Fly.exe>

### 5.2 **`connectome-weights-…feather` 的列：仓库只给到语义级**

| 事实 | 出处 |
|---|---|
| 列语义：**源、目标、接触数** | `malecns-study-guide.md:80` 注释逐字：`# 连接权重（源、目标、接触数）` |
| `body-annotations-…feather` = 细胞注释（superclass 等） | `malecns-study-guide.md:79` |
| `body-neurotransmitters-…feather` = 每个神经元的**聚合**递质预测 | `MaleCNS_连接组学基础_中文报告.md:406`；`phase0.html:1393` |
| `tbar-neurotransmitters-…feather` = **每个突触前位点**的递质预测概率 | `MaleCNS_连接组学基础_中文报告.md:407`；`phase0.html:1394` |
| `syn-partners` 表的列含 **`conf_pre`、`conf_post`**（每个突触点两个置信度字段） | `MaleCNS_连接组学基础_中文报告.md:152` |
| `syn-points` 表**按 pre/post 分行**，用 **`kind` 列区分 `PreSyn`/`PostSyn`** | 同上 |
| 权重族字段名（neuPrint 侧）：`weight`、`weightHP`、`weightAxonAxon`、`weightAxonDendrite`、`weightDendriteDendrite`、`weightDendriteAxon`；元数据 `preHPThreshold` / `postHPThreshold` | `MaleCNS_连接组学基础_中文报告.md:141,154`；URL <https://connectome-neuprint.github.io/neuprint-python/docs/queries.html> |

> **未找到**：`connectome-weights-male-cns-v1.0-minconf-0.5.feather` 的**逐字列名清单**（例如是否叫 `body_pre`/`body_post`/`weight`/`syn_count`）。仓库里没有该 feather 的 schema、没有 `read_feather` 代码、没有列名表。最接近的是场景 JSON 里逐突触属性名（`body_pre_u32` / `body_post_u32`，见 4.2）与 neuPrint 边属性名。

### 5.3 neuPrint API（唯一被仓库实际使用的在线接口）

| 事实 | 出处 |
|---|---|
| 端点：`POST https://neuprint.janelia.org/api/custom/custom`，body `{"cypher":"…","dataset":"male-cns:v1.0"}` | `README.md:149-151`；`neuprint.html:263-264,421-423` |
| CORS 开放（无需代理）：`Access-Control-Allow-Origin: *`、`Access-Control-Allow-Headers: Authorization, Content-Type`、`Access-Control-Allow-Methods: GET, POST, OPTIONS` | `README.md:139-143` |
| 匿名只读、**不需要 token** | `README.md:279-281`；`neuprint.html:160-161` |
| curl 示例（仓库逐字） | `README.md:283-286`：`curl -s -X POST 'https://neuprint.janelia.org/api/custom/custom' -H 'Content-Type: application/json' -d '{"cypher":"MATCH (n:Neuron) WHERE n.type = '\''DNg13'\'' RETURN n.bodyId, n.instance","dataset":"male-cns:v1.0"}'` |
| 查询门户 URL：`https://neuprint.janelia.org/?dataset=male-cns%3Av1.0&qt=findneurons` | `malecns-factcheck-2026-09-17.md:209`；`malecns-study-guide.md:65` |
| Python 客户端：`Client("https://neuprint.janelia.org", dataset='male-cns:v1.0', token=token)` | `malecns-factcheck-2026-09-17.md:250`；URL <https://github.com/connectome-neuprint/neuprint-python> |
| **字段名陷阱**：细胞类型字段是 `type` 而**不是** `cellType`（写错不报错、只返回 0 行）；连接关系是 `ConnectsTo`；`upstream`/`downstream` 只是节点计数属性，不能当关系查 | `neuprint.html:174-182`；`phase1.html:1129-1132` |
| 响应含 `columns` / `data` / `debug`（neuPrint 改写后的实际 Cypher） | `neuprint.html:499-522` |

### 5.4 官方 GCS bucket / Neuroglancer 场景（全部 45 个图层）

场景 URL：`https://neuroglancer-demo.appspot.com/#!gs://flyem-male-cns/v1.0/male-cns-v1.0.json`（`README.md:210`；`malecns-study-guide.md:67`）。

`_official/male-cns-v1.0.json` 的 **45 个图层**（按类型）：

```
image        : em-clahe, micro-ct, tbar-cloud
annotation   : soma-points, optic-column-pins, synapse-groundtruth,
               synapse-groundtruth-boxes, presyn, postsyn
segmentation : cns-seg, brain-neuropil-shell, brain-shell, brain-shell-with-lamina,
               vnc-neuropil-shell, vnc-shell, brain-neuropils,
               brain-neuropil-subcompartments, vnc-neuropils, vnc-nerves,
               major-compartments, pointcloud-shells, nuclei, cns-mirror,
               brain-defects, vnc-defects,
               ME(R)-columns, ME(R)-layers, LO(R)-columns, LO(R)-layers,
               LOP(R)-columns, LOP(R)-layers,
               ME(L)-columns, ME(L)-layers, LO(L)-columns, LO(L)-layers,
               LOP(L)-columns, LOP(L)-layers,
               OL(R), OL(R)-release-mask, hemibrain-region,
               hemibrain-meshes, flywire-meshes, manc-meshes, banc-meshes,
               semantic-masks
```

其它官方 GCS 路径（仓库内出现过的）：
- `gs://flyem-male-cns/v1.0/connectome-data/flat-connectome/`（7 个 feather）
- `gs://flyem-male-cns/rois/fullbrain-roi-v5/`（脑 neuropil ROI；`mesh/`、`segment_properties/`、`info`）
- `gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0/`
- `gs://flyem-male-cns/v1.0/segmentation`（+ `type_property`、`type_and_group_property`、`tags_property`、`numeric_properties`、`instance_property`、`flywireType_property`、`meshes-malecns/single-res-meshes`）
- `gs://flyem-male-cns/v1.0/malecns-v1.0-soma-points`
- `gs://flyem-male-cns/v1.0/male-cns-v1.0-synapses-precomputed/`
- `gs://flyem-male-cns/malecns-tbar-point-cloud-512nm-smoothed/`
- `gs://flyem-male-cns/v1.0/synapse-ground-truth/malecns-v1.0-synapse-ground-truth-lines/`
- 数据桶根：`gs://flyem-male-cns`（【预印本】`berg.js` Data availability）

### 5.5 网格文件格式（**仓库内部有一处自相矛盾，解析时注意**）

| 事实 | 出处 |
|---|---|
| 格式名 `neuroglancer_legacy_mesh`；理论规范：`uint32 numVertices` → `float32 positions[nv*3]` → `uint32 indices[...]`，**无每顶点计数表** | `README.md:198-201`（并给规范链接 <https://neuroglancer-docs.web.app/datasource/precomputed/mesh.html>） |
| `README.md:200` 说「无每顶点计数表」；`tools/fetch_official_meshes.py:8-12` 的**文件头 docstring 却声称有** `uint32 numTrianglesPerVertex[numVertices]`，而同文件**实际解析代码**（`:141-149`）写明「**没有**『每顶点三角形数』数组」，并按 `剩余字节 / 12 = 三角形数` 计算 | ⚠️ **仓库内部矛盾**：以 `README.md` + `fetch_official_meshes.py:141-149` 的代码为准，**不要信那个 docstring 头部** |
| 本仓库抽稀预设 | `low` ≈6.5 万三角形（Canvas 2D）；`low --scale 0.5` ≈3.2 万（仓库内版本）；`mid` ≈34 万（WebGL）；`high` 不抽稀（仅离线分析）—— `README.md:247-253` |

### 5.6 稀疏矩阵 / 预处理仓库与 CSV/parquet

| 事实 | 出处 |
|---|---|
| `YijieYin/connectome_data_prep` —— 「**直接拿准备好的稀疏矩阵**（MaleCNS / BANC / FlyWire / hemibrain）」，含 maleCNS 预处理稀疏矩阵 + **axon-dendrite 拆分** | `malecns-study-guide.md:90`；`malecns-factcheck-2026-09-17.md:252`；URL <https://github.com/YijieYin/connectome_data_prep> |
| `YijieYin/connectome_interpreter` —— 有效连接、寻路、回路操作、全脑规模可微模型；PyPI `connectome-interpreter`；notebook 支持 maleCNS/BANC/hemibrain/MANC 切换 | `malecns-study-guide.md:91`；`malecns-factcheck-2026-09-17.md:253`；URL <https://github.com/YijieYin/connectome_interpreter> |
| `flyconnectome/cocoa`（跨数据集共聚类；README 仍写 `male-cns:v0.9`，滞后）、`natverse/malecns`（R，默认 `male-cns:v1.0`，元数据含 `flywireType`/`mancType`/`itoleeHl`）、`navis` + `navis-flybrains`（跨模板空间变换） | `malecns-factcheck-2026-09-17.md:251,254,255` |
| `flyconnectome/2025malecns` —— Berg 补充数据（含 `quantify-neuron-connections.ipynb`，内部 `VERSION='v0.9'`） | `malecns-factcheck-2026-09-17.md:256`；URL <https://github.com/flyconnectome/2025malecns> |
| **CSV 导出**：仓库里唯一的 CSV 导出是 `neuprint.html` 的**前端导出**（把查询结果表导出为 `neuprint-malecns-<时间戳>.csv`，自动处理逗号/引号转义） | `neuprint.html:608-634`（`toCSV()` / `download()`），文件名 `neuprint.html:629` |
| **parquet**：仓库中**完全没有** parquet 相关内容（全库检索 `parquet|read_feather|pyarrow` 无命中） | 检索结果：仅命中 `.csv` 与 `benchmark-results.csv`（`malecns-study-guide.md:150`）、FlyWire 注释仓库的 `Supplemental_file*.csv`（`MaleCNS_连接组学基础_中文报告.md:352-361`）、Codex `/api/download`（`malecns-factcheck-2026-09-17.md:290`） |
| FlyWire 连接组数据 dump：Zenodo `10.5281/zenodo.10676866`（连接）、`10.5281/zenodo.12588557`（flow） | `assets/papers/dorkenwald.js` Data availability |
| Codex 数据集卡片 API：`https://codex.flywire.ai/api/download?dataset=fafb` | `malecns-factcheck-2026-09-17.md:48,135` |

---

## 6. 仿真 / 模拟相关的陈述与参数

### 6.1 仓库对 MaleCNS 仿真的立场

| 事实 | 出处 |
|---|---|
| 「连接组本身**只是接线图**，没有任何动力学」；「仿真里的每一个参数都是**你的假设**，不是数据里读出来的」 | `malecns-study-guide.md:121`；`phase0.html:1581`；`phase0.html:1666`「连接组只是接线图。dt、τm、阈值、不应期、传导延迟……都没有」 |
| 未建模清单（汇报必须声明）：受体层面 E/I 差异、神经调质、电突触、可塑性、学习、神经分支形态学、真实放电率标定 | `malecns-study-guide.md:138`；`phase0.html:1437-1438` |
| Berg 自己认为未来可做：「We are heartened by the recent success of brain-scaled simulation studies」 | 【预印本】`berg.js` Discussion |

### 6.2 社区 LIF 参数（**建模选择，不是测量值**；指南逐字给的 Doomfly 参数）

```
W[j,i] = c[j,i] * s[j] / Σ_k ( c[k,i] * |s[k]| )     # 按突触后神经元总输入接触数归一化，再乘递质符号
s = +1 (ACh) / −1 (GABA 或 Glu) / 0 (未知、仅调质、冲突)
v_next = exp(-dt/tau_m) * v + W·(上一步脉冲) + drive
spike = (v_next >= threshold); 发放后 v_next = 0
dt = 0.1 ms,  tau_m = 20 ms,  不应期 = 2.2 ms,  传导延迟 = 1.8 ms
```
出处：`malecns-study-guide.md:123-136`；`phase0.html:940-947`。

### 6.3 吞吐/硬件（**实测与外推必须分开**）

| 事实 | 性质 | 出处 |
|---|---|---|
| **dt = 0.1 ms 时，1 秒真实时间 = 10,000 步** | 换算 | `malecns-study-guide.md:146` |
| mps-malecns-model（全图，dt=1 ms），Apple Silicon MPS：**44.56 步/s** ⇒ 1 秒真实时间 **22.4 s**；换算到 dt=0.1 ms 约 **224 s** | **实测** | `malecns-study-guide.md:169` |
| Fly64（全图 LIF），M2 MacBook / 16 GB：**~50 步/s** | **实测步率** | `malecns-study-guide.md:170` |
| Doomfly（C++ 事件驱动内核）：慢于实时（README 未给数） | 实测定性 | `malecns-study-guide.md:171` |
| 优化 C++ 多核（Brian2 standalone 类），桌面 CPU：**~3–5 s** | **外推** | `malecns-study-guide.md:172` |
| 同上，笔记本 CPU：**~10–20 s** | 外推 | `malecns-study-guide.md:173` |
| 优化 event-driven CUDA 内核（GeNN 类），单张消费级 GPU：**~1–3 s（接近实时）** | 外推 | `malecns-study-guide.md:174` |
| 每步扫全边表的 cuSPARSE 级矩阵乘，离散 GPU：**~15 s**（按 1.45 ms/步） | 外推 | `malecns-study-guide.md:175` |
| 每步扫全边表的 PyTorch/MPS 写法，Apple GPU：**~200 s** | 实测外推 | `malecns-study-guide.md:176` |
| 外推依据：FlyWire 上 Brian2 CPU 每 1 s 仿真约 1.8–2.7 s ⇒ 神经元更新吞吐约 5×10⁸ 次/秒；MaleCNS = 166,700 × 10,000 ≈ 1.7×10⁹ 次更新/秒生物时间 → 约 3.3 s，再乘 1.2–1.7 规模系数 | 外推链 | `malecns-study-guide.md:178` |
| **没有 MaleCNS 的官方基准**；CPU/GPU 仿真速度**全部为外推**，除 MPS 44.56 步/s 与 Fly64 50 步/s 两个实测点 | 自述局限 | `malecns-study-guide.md:146,291` |
| **CPU**：8 核之后收益递减（步同步、每 0.1 ms 一个全局屏障）；「高主频 8 核 > 低频 16 核」；16.7 万神经元状态数组约 **8 MB**，大 L3 有帮助 | 工程结论 | `malecns-study-guide.md:184` |
| **GPU 显存**：CSR 形式约 **0.2 GB**；COO + 多份权重约 **0.5 GB**；加神经元/突触/延时状态共 **1–2 GB**；**4 GB 能跑，8 GB 舒适**；批处理每条 trial 状态只多约 4 MB | 工程结论（社区实测） | `malecns-study-guide.md:185` |
| **绝对禁止**：N×N 稠密矩阵（166,700² × 4 B = **111 GB**）；每步扫全边表的 numpy/PyTorch 写法（比事件驱动慢 **40–50 倍**） | 禁止项 | `malecns-study-guide.md:186` |
| 派生复核：dense float32 = 111,155,560,000 B = **103.52 GiB**；CSR = 205,330,308 B = **0.191 GiB**；稠密/稀疏 **541×** | 脚本 | `malecns_scale.py:86-97`（实跑输出见 §1.2） |
| 事件驱动为何快：「模型活跃度只有约 **0.3 %**（每步几百个神经元放电）」 | 定量观察 | `malecns-study-guide.md:163` |

### 6.4 同源参考：FlyWire 全脑 LIF 基准（RTX 4070，dt=0.1 ms，138,639 神经元 / 15.1M 连接）

| 后端 | 单 trial（1 s 仿真） | 相对实时 | 批 8（80 s 仿真） |
|---|---|---|---|
| GeNN（GPU） | 0.52 s | **1.94×** | 12.6 s → 6.34× |
| NEST GPU | 1.18 s | 0.85× | 85.2 s → 0.94× |
| Brian2GeNN（GPU） | 1.87 s | 0.53× | 152 s → 0.53× |
| Brian2（CPU，C++ standalone） | 2.66 s | 0.38× | 81.8 s → 0.98× |
| PyTorch（CUDA） | 9.82 s | 0.10× | 498 s → 0.16× |
| Brian2CUDA（GPU） | 11.94 s | **0.084×** | 339 s → 0.24× |

出处：`malecns-study-guide.md:150-159`；数据来自 <https://github.com/eonsystemspbc/fly-brain> 的 `data/benchmark-results.csv`。
独立复现（DGX Spark GB10，20 核 Grace + CUDA 13）：Brian2 CPU **1.8 s**、Brian2CUDA **7.9 s**、PyTorch **12.0 s**；脑+身体（NeuroMechFly）跑 5 秒蝇时间需 **64 秒**计算 —— `malecns-study-guide.md:161`，URL <https://grizzlypeaksoftware.com/articles/p/i-ran-a-fruit-flys-entire-brain-on-my-dgx-spark-then-gave-it-a-body-nxqdy1xn>

### 6.5 真实 LIF 模型参数（**Shiu et al. 2024，FlyWire FAFB（雌性、仅脑），不是 MaleCNS**）

| 参数 | 值 |
|---|---|
| 模型 | LIF + α 突触动力学，**Brian2** 实现 |
| V_resting | −52 mV |
| V_reset | −52 mV（与静息相同） |
| V_threshold | **−45 mV** |
| R_mbr | 10 kΩ·cm² |
| C_mbr | 2 µF·cm⁻² |
| T_refractory | **2.2 ms** |
| τ（突触衰减） | **5 ms** |
| T_dly（放电→膜电位变化的延迟） | **1.8 ms** |
| W_syn | **0.275 mV** —— **唯一的自由参数** |
| W_syn 定标准则 | 「100 Hz 激活糖 GRN 时，MN9 达到其最大放电率的大约 80 %」 |
| 权重构造 | `w_{j,i} = (FlyWire 突触连接权重) × (+1 兴奋 / −1 抑制) × W_syn` |
| 规模 | v630 版全部 **127,400 个已校对神经元** |
| 实验量 | 每个实验 **30 次 1,000 ms 模拟** |
| 成本 | **每 1,000 ms 试验约需 5 分钟 CPU 单线程** |
| cleft score 阈值 | **50** |

全部出处：`assets/papers/notes-shiu-d.js:12-35,42`。

### 6.6 MaleCNS 生态里的仿真/接身体项目

| 项目 | 关键数字 | 出处 |
|---|---|---|
| **Doomfly** <https://github.com/nftechie/doomfly> | **166,700 神经元 / 25,582,938 边**接入 ViZDoom；原生 C++ LIF 内核；**4,184 条 KC→MBON11 连接**上跑多巴胺门控可塑性；公开承认训练失败 | `malecns-study-guide.md:198` |
| **Fly64** <https://github.com/ornata/fly> | 全图接 Super Mario 64；M2 MacBook；**50 步/s** | `malecns-study-guide.md:199` |
| **Fly Dino** <https://github.com/cobanov/flyjump> | **80 神经元子回路 + 243 参数** CEM 训练读出；held-out **99/100**；含回路静默因果对照 | `malecns-study-guide.md:200` |
| **mps-malecns-model** <https://github.com/seohyunjun/mps-malecns-model> | Apple MPS 实验性 LIF，自带 3D 活动 `report.html` | `malecns-study-guide.md:201` |
| **malecns-reservoir-computing** <https://github.com/JangYeongSil69420/malecns-reservoir-computing> | 全图当储备池（Tesla T4），Mackey-Glass 预测 | `malecns-study-guide.md:202` |
| Shiu et al. LIF 全脑模型（FAFB） | 预测准确率约 **91 %**；糖→MN9 标准验证 | `malecns-study-guide.md:210` |
| 通用警告 | 这些项目几乎全是「连接组当固定基底 + 只训练一个小读出层」；动力学/感受器映射/动作解码全是自定假设 | `malecns-study-guide.md:218` |
| 阶段 4 过关标准 | 「刺激已知神经元 → 下游按预期激活，且**静默对照不激活**」 | `malecns-study-guide.md:106,238` |

---

## 7. `neuprint.html` 的 22 条预设 Cypher（**逐字照抄**）

> 文件：`neuprint.html`，`PRESETS` 数组位于 `neuprint.html:267-364`。
> 运行方式：`POST https://neuprint.janelia.org/api/custom/custom`，body `{"cypher": "<下面的语句>", "dataset": "male-cns:v1.0"}`（`neuprint.html:263-264,421-423`）；匿名只读、无需 token。
> 分组：`neuprint.html:268`（基础句式 4 条）、`:285`（通路 A 7 条）、`:318`（通路 B 5 条）、`:338`（探索与统计 6 条）= **22 条**。

### 基础句式

**① 按类型找神经元** — 拿到 bodyId、实例名、超类、递质
```cypher
MATCH (n:Neuron) WHERE n.type = 'DNg13'
RETURN n.bodyId, n.instance, n.superclass, n.consensusNt
```

**② 看某个神经元的上游** — 谁连到它，按权重排序
```cypher
MATCH (m:Neuron)-[r:ConnectsTo]->(n:Neuron {bodyId: 11074})
RETURN m.type, m.bodyId, r.weight
ORDER BY r.weight DESC LIMIT 25
```

**③ 看某个类型的下游** — 它连到谁，按类型聚合
```cypher
MATCH (a:Neuron {type: 'R1-R6'})-[r:ConnectsTo]->(b:Neuron)
RETURN b.type, b.superclass, count(*) AS n, sum(r.weight) AS w
ORDER BY w DESC LIMIT 20
```

**④ 按超类汇总输出** — 一眼看出它主要连去哪一区
```cypher
MATCH (n:Neuron {bodyId: 11074})-[r:ConnectsTo]->(m:Neuron)
RETURN m.superclass, count(DISTINCT m) AS targets, sum(r.weight) AS total
ORDER BY total DESC
```

### 通路 A · 视觉 → 运动

**A1 光感受器 R1-R6 投向谁** — 预期 L2 / L1 / L3
```cypher
MATCH (a:Neuron {type: 'R1-R6'})-[r:ConnectsTo]->(b:Neuron)
RETURN b.type, b.superclass, count(*) AS n, sum(r.weight) AS w
ORDER BY w DESC LIMIT 8
```

**A2 板层细胞 L2 的下一跳** — 预期 Tm2 / Tm1 / Tm4
```cypher
MATCH (a:Neuron {type: 'L2'})-[r:ConnectsTo]->(b:Neuron)
RETURN b.type, b.superclass, count(*) AS n, sum(r.weight) AS w
ORDER BY w DESC LIMIT 8
```

**A3 找到方向选择细胞 T4/T5** — 从 Tm* 往下走
```cypher
MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron)
WHERE a.type IN ['Tm1','Tm2','Tm4'] AND b.type STARTS WITH 'T'
RETURN a.type AS src, b.type AS dst, sum(r.weight) AS w
ORDER BY w DESC LIMIT 12
```

**A4 小叶板切向细胞（LPTC）** — T4/T5 的下游
```cypher
MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron)
WHERE a.type STARTS WITH 'T4' OR a.type STARTS WITH 'T5'
RETURN a.type AS src, b.type AS dst, b.superclass AS sc, sum(r.weight) AS w
ORDER BY w DESC LIMIT 12
```

**A5 DNg13 身份卡** — 两行：L 与 R
```cypher
MATCH (n:Neuron) WHERE n.type = 'DNg13'
RETURN n.bodyId, n.instance, n.superclass, n.consensusNt,
       n.flywireType, n.pre, n.post
```

**A6 DNg13 输出到 VNC 运动神经元** — 验证它确实是下行神经元
```cypher
MATCH (n:Neuron {bodyId: 11074})-[r:ConnectsTo]->(m:Neuron)
WHERE m.superclass = 'vnc_motor'
RETURN m.type, m.instance, r.weight
ORDER BY r.weight DESC LIMIT 8
```

**A7 DNg13 的全部输出超类** — vnc_* 应占绝对多数
```cypher
MATCH (n:Neuron {bodyId: 11074})-[r:ConnectsTo]->(m:Neuron)
RETURN m.superclass, count(*) AS n, sum(r.weight) AS w
ORDER BY w DESC
```

### 通路 B · 糖味觉 → 摄食

**B1 找到 MN9 喙肌运动神经元**
```cypher
MATCH (n:Neuron) WHERE n.type = 'MN9'
RETURN n.bodyId, n.instance, n.superclass
```

**B2 谁在驱动 MN9** — 预期大量 GNG*（食管下区）
```cypher
MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron {type: 'MN9'})
RETURN a.type, a.superclass, sum(r.weight) AS w
ORDER BY w DESC LIMIT 12
```

**B3 谁给 GNG015 供输入** — 预期最强是 BM_Taste
```cypher
MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron {type: 'GNG015'})
RETURN a.type, a.superclass, sum(r.weight) AS w
ORDER BY w DESC LIMIT 10
```

**B4 全库唯一的味觉感觉类型** — 预期只返回 BM_Taste
```cypher
MATCH (n:Neuron) WHERE n.type CONTAINS 'Taste'
RETURN DISTINCT n.type, n.superclass, count(*) AS instances
```

**B5 BM_Taste 的下游分布** — 看它把信息送去哪一区
```cypher
MATCH (a:Neuron {type: 'BM_Taste'})-[r:ConnectsTo]->(b:Neuron)
RETURN b.superclass, count(DISTINCT b) AS targets, sum(r.weight) AS w
ORDER BY w DESC
```

### 探索与统计

**数据规模总览** — 神经元总数与有类型的数量
```cypher
MATCH (n:Neuron)
RETURN count(n) AS 总神经元,
       count(n.type) AS 有类型,
       count(DISTINCT n.type) AS 类型数
```

**各超类的数量分布** — descending / vnc_motor 有多少
```cypher
MATCH (n:Neuron)
RETURN n.superclass, count(*) AS n
ORDER BY n DESC
```

**DNg 家族全清单** — 看下行神经元有哪些编号
```cypher
MATCH (n:Neuron) WHERE n.type STARTS WITH 'DNg'
RETURN n.type, count(*) AS instances, collect(n.bodyId)[0..4] AS sampleIds
ORDER BY n.type
```

**flywireType 覆盖率** — 跨数据集类型对照有多少
```cypher
MATCH (n:Neuron) WHERE n.flywireType IS NOT NULL
RETURN count(n) AS 有对照, count(DISTINCT n.flywireType) AS 不同类型数
```

**找权重最高的连接** — 全库最强边长什么样
```cypher
MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron)
RETURN a.type AS src, b.type AS dst, r.weight AS w
ORDER BY w DESC LIMIT 15
```

**某个神经毡内的神经元** — 示例：侧副叶 LAL
```cypher
MATCH (n:Neuron)
WHERE n.type STARTS WITH 'LAL'
RETURN n.type, n.superclass, count(*) AS n
ORDER BY n DESC LIMIT 15
```

---

## 8. 未找到清单（明确 flag，勿猜）

1. **MaleCNS 的入度/出度分布、均值/中位数/极值**（仓库把「算入度/出度/度分布」列为**尚未做的阶段 3 任务**）。
2. **hub 神经元及其最大度**（只有 DNg13 等单点实测的 `pre`/`post` 突触计数）。
3. **扇入/扇出分布**。
4. **聚类系数、互易性、rich club 的 MaleCNS 数值**（只有关于阈值稳健性的 FlyWire 定性结论）。
5. **全库最大/最小/中位数边权**（只有「高度偏斜」的定性陈述与 4.85/4.86 的均值）。
6. **`connectome-weights-…feather` 的逐字列名清单**（只有「源、目标、接触数」的语义描述）。
7. **MaleCNS 的递质构成百分比**（ACh/GABA/Glu 各占多少）；仓库只有 **FlyWire/Shiu** 的 55/24/14/7 %。
8. **视叶 → VNC 的 tract 长度**（nm/µm 数值）。
9. **`consensus_nt` 的官方定义**与递质预测不确定性百分比。
10. **`minconf-0.5` 中 0.5 的精确定义**（cleft score？pre/post 取 min？）。
11. **MaleCNS 论文 Fig. S8E/S9e 的 precision-recall 具体数值**（只有「T-bar recall 一般 >0.8、synapse recall 一般 >0.7」的定性描述，见 `berg.js` Methods "EM Volume Synapse Identification"）。
12. **`assets/papers/berg.js` 只有预印本正文**：Cell 正式版（166,700 / 11,710 / 8,069 / 138 / 289 / 71）的数字**只能通过 `malecns-factcheck-2026-09-17.md` 的联网核查记录引用**，仓库内没有正式版全文。
13. **`_official/roi-info.json` 属于哪个 ROI 图层未记录**（默认下载参数是 `fullbrain-roi-v5`，但文件本身不含图层名）。
