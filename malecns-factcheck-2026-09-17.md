# MaleCNS 学习页事实核查报告

- **核查日期（实际当天）**：2026-09-17（Asia/Shanghai，`Get-Date` = 2026-09-17 13:58 +08:00）
- **核查方法**：web_search + web_fetch 实时联网，以官方站点、PubMed/Europe PMC、Codex FAQ、官方 GitHub 仓库与新闻稿为准
- **2026-09-20 复核更新**：下载官方 v1.0 flat-connectome（`_data/`，MD5 与官方 bucket 清单一致）后，A 节的两项「待核实」整数 **已坐实** —— 见 A 节与汇总表。复核脚本：`python tools/verify_feather.py`。
  ⚠️ **但类型总数未能复现**：官方公布的 **11,710** 在 v1.0 注释文件里得不到 —— 对 166,700 个神经元按 `type` 去重是 **11,751**（多 41）。两者口径差异未查明，故 **11,710 / 11,691 这一组数字维持原状、不做改动**，引用时仍按官方口径。
- **核心结论一句话**：**指南整体方向正确，但混用了「预印本数字」与「正式发表数字」，并且把 166,700 误标为「社区过滤值」。** v1.0 官方/发表口径为 **166,700 神经元 / 11,710 类型**；166,691 / 11,691 是 2025-10 预印本口径。

---

## 0. 今天日期 与 Cell 论文状态

| 项目 | 结论 |
|---|---|
| 今天日期 | **2026-09-17**（确认） |
| Cell 论文是否已正式发表 | **已正式发表，不是仅有预印本**（确认） |
| DOI | **10.1016/j.cell.2026.08.015** |
| 卷期页 | Cell **189**(18): **5504–5526.e15**，print publication date **2026-09-01**，issue date **2026-09-03** |
| PMID / 索引 | PMID **42691995**；Europe PMC `firstPublicationDate` 2026-09-01，`dateOfCompletion` 2026-09-03，状态 `ppublish`（正式出版） |
| cell.com 链接是否可解析 | 链接真实存在，但本机抓取返回 **HTTP 403（Cloudflare 人机校验）**；此为反爬拦截，不代表链接失效。用 PubMed/Europe PMC 已独立确认该文存在且正式发表 |

⚠️ **重要**：official 站点新闻写 "2026-09-03 - MaleCNS paper published"，Cell 目录 issue 日期也是 2026-09-03，但 PubMed/期刊记录 `printPublicationDate` = 2026-09-01。指南写 "Cell 2026-09-03" 属于**可接受的表述**（= 期次日期）。

- https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6
- https://doi.org/10.1016/j.cell.2026.08.015
- https://pubmed.ncbi.nlm.nih.gov/42691995/
- https://www.sciencedirect.com/journal/cell/vol/189/issue/18

**论文包数量有分歧（附带提示）**：Science 新闻称 "a package of **four papers in Cell**"；Smithsonian 称 "**three** studies in Cell **and another in Current Biology**"。建议学习页写「Cell 同一期多篇（含味觉连接组 Cell 2026 与一篇 Current Biology）」而不要写死数字。

---

## A. MaleCNS 范围与规模 — **修正**

| 项目 | 指南值 | 核查值 | 结论 |
|---|---|---|---|
| 神经元数（官方） | ~166,691 | **166,700**（正式发表摘要 + Codex MCNS v1.0 + 官方 gallery） | **修正** |
| 神经元数（"社区 flat-connectome 过滤"）| 166,700 | 社区过滤（annotation status = `Traced`）实为 **165,122 神经元 / 25,563,197 边** | **修正（原标注张冠李戴）** |
| 有向连接数 | 25,582,938 | **已坐实（2026-09-20 复核）**。下载官方 v1.0 flat-connectome（MD5 与官方 bucket 清单一致）后，按「两端都是有 `superclass` 的神经元」过滤，实测正好 **25,582,938** 条边 / **124,177,617** 个突触 / **166,700** 个神经元。同一子图加 ≥5 突触阈值后为 **6,242,118** 条边，与 Codex MCNS v1.0 界面一致。官方作者计数 notebook 的 **v0.9** 口径（未阈值 25,563,426 / ≥5 6,237,402）是旧快照，与 v1.0 的差值不是记录错误 | **已坐实** |
| 突触接触数 | 124,177,617 | **已坐实（2026-09-20 复核）**：同一 v1.0 神经元子图实测正好 **124,177,617**，与 Science 新闻 "**124.2 million synapses**"、UKRI 新闻 "**124 million synaptic connections**" 一致 | **已坐实** |
| 覆盖范围 | 中央脑 + 视叶 + VNC，颈部连接完整 | **确认**。官方原文："encompassing the central brain, optic lobes … and the ventral nerve cord … a fully proofread and annotated brain and nerve cord connectome with an **intact neck connective**"（"完整颈部连接" 对应 "intact neck connective"） | 确认 |

**要点**：166,691 与 166,700 **不是「官方 vs 社区」的关系**，而是**「预印本 vs 正式发表 + Codex/官方 v1.0」**的关系。2025-10 预印本摘要写 166,691；2026-09 正式 Cell 摘要写 **166,700**，官方 media 页也写 "contains **166,700** neurons in total"。

- https://www.janelia.org/project-team/flyem/male-cns-connectome
- https://male-cns.janelia.org/media/
- https://api.biorxiv.org/details/biorxiv/10.1101/2025.10.09.680999 （预印本 166,691 / 11,691 类型）
- https://pubmed.ncbi.nlm.nih.gov/42691995/ （正式 166,700 / 11,710 类型）
- https://raw.githubusercontent.com/flyconnectome/2025malecns/main/supplemental_data/quantify-neuron-connections.ipynb （官方计数 notebook）
- https://codex.flywire.ai/api/download?dataset=fafb （Codex 数据集卡片：MCNS v1.0 = 166,700 神经元 / 6,242,118 connections）
- https://github.com/Ibtisam-Mohammad/Fly.exe （社区 Traced 子图：165,122 / 25,563,197）
- https://www.science.org/content/article/new-connectome-shows-all-124-million-contact-points-fruit-fly-s-nervous-system
- https://www.ukri.org/news/world-first-map-of-a-male-fly-brain-a-win-for-neuroscience/

---

## B. 数据版本 — **确认（含一处官方自相矛盾）**

| 项目 | 结论 |
|---|---|
| v0.9 = 2025-10-05 | **官方 Release Notes 页写 "v0.9 (October 5, 2025)"**；但同站首页与 Janelia 页的新闻条目写 **2025-10-03**。官方内部不一致，**建议标注为 2025-10-03/05（官方两处口径不同）** |
| v1.0 = 2026-06-08 | **确认** |
| v1.0 变更内容 | **确认，官方原文仅两条**：「Minor proofreading changes」「Refinement of neuron annotations」 |
| 其他里程碑 | 2025-10-30 预印本 v2；2025-11-07 NeuronBridge 支持 MaleCNS |

- https://male-cns.janelia.org/release/
- https://male-cns.janelia.org/

---

## C. 阈值约定 — **确认**

| 项目 | 结论 | 依据 |
|---|---|---|
| flat-connectome 使用 min confidence 0.5 | **确认** | 官方下载页全部三个 flat 文件名内嵌 `minconf-0.5` 后缀 |
| neuPrint/Codex MCNS 默认 ≥5 突触 | **确认（Codex 明文）** | Codex FAQ："Default minimum thresholds are dataset-specific: FAFB 5+ / BANC 3+ / MANC 1+ / MAOL 1+ / **MCNS 5+**"；官方 notebook 亦按 `weight >= 5` 阈值统计 |

- https://male-cns.janelia.org/download/
- https://codex.flywire.ai/faq
- https://raw.githubusercontent.com/flyconnectome/2025malecns/main/supplemental_data/quantify-neuron-connections.ipynb

---

## D. FlyWire FAFB 对比 — **修正（突触数口径）**

| 项目 | 指南值 | 核查值 | 结论 |
|---|---|---|---|
| 神经元数 | 139,255 | **139,255** | 确认 |
| 突触数 | ~54.5 million | **论文原文为 "5 × 10^7 chemical synapses"＝约 5,000 万**；54.5M 属后续/新闻报道口径（Smithsonian: "more than 54.5 million"; 中文报道："超过 5000 万个"） | **修正：论文口径 50M，54.5M 非论文数字** |
| 仅脑（brain-only）| 是 | **确认**（whole **brain**；不含 VNC。含 VNC 的是 BANC） | 确认 |
| 性别 = 雌性 | 是 | **确认**（"reconstructed from an adult **female** Drosophila melanogaster"） | 确认 |
| 文献 | Dorkenwald et al. 2024, Nature 634:124 | **确认**：Nature **634**(8032): **124–138**，DOI **10.1038/s41586-024-07558-y** | 确认 |
| Codex 快照 | v783, 2023-10 | **确认**：Codex FAQ "FlyWire FAFB … default snapshot 783; available in Codex: v783 – Oct 2023 [latest release]"；Codex 卡片 139,255 神经元 / 3,732,460 connections | 确认 |
| flywire.ai 站点 | — | 站点存在，但核查当日抓取失败（`fetch failed`），未能直接引其文案 | 部分确认 |
| 校对/注释状态 | — | **确认**：Codex「Completeness and accuracy of the connectome annotations are still improving, and are updated in Codex ~weekly」；v783 为当前 latest release；突触检测方法于 2025-07 更换（Yu et al. 取代 Buhmann et al.） | 确认 |
| 雌雄问题 | — | **确认且必须写清**：FAFB = 雌，MaleCNS = 雄。二者对比**本体就是跨性别对比**（这正是该论文的核心），但任何「非性别相关」的跨数据集比较都受性别混杂 | 确认 |

- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-024-07558-y%22&resultType=core&format=json
- https://codex.flywire.ai/faq
- https://codex.flywire.ai/api/download?dataset=fafb
- https://codex.flywire.ai/about_flywire

---

## E. ID 不可互换 / Codex 跨库搜索与托管数据集 — **部分确认 + 修正**

| 项目 | 结论 |
|---|---|
| MaleCNS 与 FlyWire body ID 不可互换 | **结构上确定，但未找到「官方明文声明」→ 部分确认**。依据：FlyWire root ID 为 ~18–19 位大整数（如 720575940625682725），MaleCNS bodyId 为小整数（如 12781、194965、42685）；Codex FAQ 明文「Root IDs are tied to a specific source segmentation and data snapshot」，跨库映射工具只对 FlyWire 系（CAVE）有效 |
| 「不存在跨数据集 ID 映射」 | **需修正措辞**：**ID 级映射确实不存在**，但**类型级交叉对照是存在的**——官方补充数据 `mcns_fw_edge_comp_mappings.json` 提供 MaleCNS↔FlyWire 的「标签/类型」对应；`natverse/malecns` 元数据含 `flywireType`/`mancType` 列；AOTU012 页面也列 "FlyWire Type(s): AOTU012"。**应写「无 ID 映射，但有官方类型级 crosswalk」** |
| Codex 支持 `@` 前缀跨库搜索 | **确认**。Codex FAQ："Can I search all datasets at once? Yes. In the main Search app, prepend the query with **@**… `@ T4a` searches for T4a across all datasets" |
| Codex 托管的数据集 | **确认，共 5 个**：FAFB、**BANC**、**MANC**、**MAOL**、**MCNS**（指南所列 5 个全部正确） |

- https://codex.flywire.ai/faq
- https://raw.githubusercontent.com/flyconnectome/2025malecns/main/README.md
- https://natverse.org/malecns/index.html
- https://male-cns.janelia.org/build/summary_types/AOTU012/

---

## F. 相关数据集（性别/范围/快照）— **确认 + 两处补充**

| 数据集 | 指南 | 核查 | 结论 |
|---|---|---|---|
| BANC | 雌性 brain+cord，v888 快照 2026-05-20 | **确认**：Codex FAQ "FlyWire BANC — Female Adult Fly Brain and Nerve Cord; default snapshot 888; available in Codex: v888 – May 20, 2026, v626 – Jul 20, 2025"；VFB 记录：Adult female, 5–6 日龄；Bates et al. 2026, Nature, DOI 10.1038/s41586-026-10735-w；Codex 卡片 158,262 神经元 / 3,037,361 connections | 确认 |
| MANC | 雄性 VNC | **确认**：Codex "MANC (VNC) — Male Adult Fly Nerve Cord, v1.2.1"，23,665 神经元 / 5,305,638 connections；VFB: Adult **male**, 5 日龄；Takemura et al. 2024, eLife 13:RP97769 | 确认 |
| MAOL | 雄性 optic lobe | **部分修正**：Codex 原文是 "Male Adult Fly **Right** Optic Lobe"（**仅右侧视叶**），v1.1，52,445 神经元 / 6,484,936 connections；来源 Nern et al. 2025, Nature 641:1225–1237 | **修正：应写明 "右视叶"** |
| hemibrain | 2020 | **确认年份，但需补性别**：**雌性**（VFB: Adult female, 5 日龄, Scheffer et al. 2020, eLife 9:e57443, DOI 10.7554/eLife.57443）；范围 = 中央脑的**一部分**（非全脑、无视叶全貌、无 VNC），约 25,000 神经元、>4,000 类型；发布 v1.0 2020-01-22 / v1.1 2020-06 / v1.2 2020-12-23 | 确认（补：雌性 + 局部中央脑） |
| MaleCNS | 雄性 CNS | **确认**：Adult male, 5 日龄, Canton-S G1 × w1118, 标本编号 Z0720-07m | 确认 |

⚠️ **高价值补充（建议写入学习页）**：MAOL 与 MaleCNS **来自同一只果蝇**（标本 `Z0720-07m`，视叶论文称其为「同一标本的早期研究」）。跨两者统计神经元会**重复计数同一批细胞**。

📌 同一来源还给出全表：FAFB / hemibrain / BANC = 雌；MANC / optic lobe / male-CNS = 雄；L1 larval CNS = 雌性一龄幼虫。

- http://v2-preview.virtualflybrain.org/about/whichfly/
- https://codex.flywire.ai/faq
- https://codex.flywire.ai/api/download?dataset=fafb
- https://www.janelia.org/project-team/flyem/hemibrain

---

## G. 三项关键科学发现 — **修正（数字已被正式版更新）**

### 🚨 这是全篇最重要的一处修正

| 项目 | 指南/预印本口径 | **正式 Cell 2026-09-03 口径** |
|---|---|---|
| 神经元 | 166,691 | **166,700** |
| 类型总数 | 11,691 | **11,710** |
| 同构类型 | 7,205 | **8,069** |
| 两性异形（dimorphic） | **114** | **138** |
| 雄性特有 | **262** | **289** |
| 雌性特有 | 69 | **71** |

- **指南的「262 + 114」是 2025-10 预印本数字**（bioRxiv v1/v2 摘要），也仍留在 **Janelia 项目页的旧文案**里；**正式发表版已改为 289 + 138（+71 雌性特有）**。
- 「**4.8% of the central brain**」只出现在 **Janelia 项目页的预印本文案**中（"262 sex-specific and 114 sexually dimorphic cell types, comprising 4.8% of the central brain"）。**该百分比的分母（是类型占比还是神经元占比）无法核实 → 待核实**。注意：262+114=376，376/11,691=3.2%，不等于 4.8%，故 4.8% 大概率是**神经元占比**而非类型占比，但**官方未明说**。
- UKRI 新闻的口径是 "around **95%** of the cells in the brain are shared between sexes… the remaining **5%** differ" — 与 4.8% 同量级。
- 定性结论 **三项全部确认**：① 性别差异集中于**高级脑中枢**，感觉/运动外周**基本同构**；② 性别特异/异形神经元集中于 higher brain centres；③ 异形性通过**异形连接（dimorphic connectivity）在神经系统中传播**。
- **DOI：10.1016/j.cell.2026.08.015**

- https://pubmed.ncbi.nlm.nih.gov/42691995/ （正式摘要：8,069 / 138 / 289 / 71）
- https://api.biorxiv.org/details/biorxiv/10.1101/2025.10.09.680999 （预印本：7,205 / 114 / 262 / 69）
- https://www.janelia.org/project-team/flyem/male-cns-connectome （仍为预印本文案 + 4.8%）
- https://male-cns.janelia.org/media/ （已更新为 11,710 类型 / 166,700 神经元）

---

## H. 命名示例细胞与通路 — **确认（含一处时效性提醒）**

| 项目 | 结论 | 依据 |
|---|---|---|
| AOTU012 是 MaleCNS 的性别异形细胞类型 | **确认**。官方 Dimorphism Explorer 把它列在「Sexually dimorphic cell types」下；其详情页标题即 **"Dimorphic Cell Type 'AOTU012'"**；标注 Male 1\|1 / Female 1\|1 计数，Matching Notes = "male-specific ventral axon projection" | 
| 官方示例通路为 R1-R6 光感受器 → … → DNg13 运动神经元 | **确认**。Janelia 项目页与官方 Media 页原文：「This video shows an example of such a pathway, **from R1-R6 visual neurons to the DNg13 motor neuron**」（视觉-运动示例通路） | 
| 糖 GRN → SEZ → MN9 通路来自 Shiu et al. 2024 | **确认（但需限定数据集）**。Shiu et al. 2024, Nature **634**(8032): **210–219**, DOI **10.1038/s41586-024-07763-9**。全文实测：图 1 标题为 "The computational model accurately predicts neurons that respond to sugar stimulation and neurons required for proboscis extension to sugar"；正文明确 "unilateral sugar presentation"、"Predicted **MN9** firing rate… in response to unilateral left hemisphere **sugar GRN** activation"、"activation of sugar GRNs at 100 Hz resulted in roughly 80% of maximal MN9 firing"；SEZ 被定义为 "the primary taste centre of the insect brain – the **suboesophageal zone (SEZ)**"，并称 SEZ 为 "the primary feeding region of the brain"。MN9 = 喙肌 9 运动神经元（FBbt_00111298） | 

⚠️ **两点必须在学习页写清**：
1. **Shiu et al. 2024 用的是 FlyWire FAFB（雌性脑），不是 MaleCNS**。它是 LIF 计算模型论文，不是 MaleCNS 数据论文。
2. 2026-09-03 另有**新的味觉连接组 Cell 论文**（DOI **10.1016/j.cell.2026.08.016**，PII S0092-8674(26)00943-8），在 **MaleCNS + MANC + FAFB** 上重算 GRN–MN 有效连接。**若学习页讲「糖→SEZ→MN9 的最新证据」，应同时引这篇**，否则读者会以为是 2024 年成果独占。

- https://male-cns.janelia.org/build/dimorphism_overview/
- https://male-cns.janelia.org/build/summary_types/AOTU012/
- https://male-cns.janelia.org/media/
- https://www.janelia.org/project-team/flyem/male-cns-connectome
- https://doi.org/10.1038/s41586-024-07763-9
- https://doi.org/10.1016/j.cell.2026.08.016

---

## I. 许可与署名 — **确认（一处补充）**

| 项目 | 结论 |
|---|---|
| MaleCNS 数据 CC-BY 4.0 | **确认**。官方各页均写 "The Male CNS dataset is licensed under CC-BY."，链接到 https://creativecommons.org/licenses/by/4.0/ |
| 必署名实体 | **确认**：**FlyEM (HHMI Janelia)**、**University of Cambridge (Dept. of Zoology)**、**MRC Laboratory of Molecular Biology**、**Google Research** —— 官方页脚原文完全一致 |
| 补充 | 官方致谢还含 **Wellcome Trust**（资助）、**Champalimaud Foundation**（UKRI 列为共同主导方之一）。若学习页要求「完整署名」，建议加上 Wellcome Trust 与 Champalimaud |
| 注意 | CC-BY 4.0 适用于**数据**；Cell 论文正文本身是 **订阅制**（Europe PMC 记录 `isOpenAccess = N`，`license = cc by` 指预印本） |

- https://male-cns.janelia.org/release/
- https://male-cns.janelia.org/download/
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2026.08.015%22&resultType=core&format=json

---

## J. 官方 Web 工具与精确 URL — **基本确认 + 一处需注意**

| 工具 | 官方 URL | 结论 |
|---|---|---|
| 项目总览 | https://www.janelia.org/project-team/flyem/male-cns-connectome | 确认 |
| 项目站首页 | https://male-cns.janelia.org/ | 确认 |
| **Codex** | https://codex.flywire.ai/ （MCNS 直达：https://codex.flywire.ai/?dataset=mcns） | 确认 |
| **neuPrint** | https://neuprint.janelia.org/?dataset=male-cns%3Av1.0&qt=findneurons （dataset 字符串 **`male-cns:v1.0`**） | 确认 |
| **Cell Type Explorer** | https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/ | 确认 |
| **Neuroglancer 独立 JSON** | `gs://flyem-male-cns/v1.0/male-cns-v1.0.json`，入口 https://neuroglancer-demo.appspot.com/#!gs://flyem-male-cns/v1.0/male-cns-v1.0.json | 确认 |
| **Dimorphism Explorer** | https://male-cns.janelia.org/build/dimorphism_overview/ （镜像 https://janelia-flyem.github.io/male-cns/build/dimorphism_overview/） | 确认 |
| **Clio** | 官方站给出的链接为 https://clio.janelia.org/ws/annotate?dataset=male-cns:v1.0**-v1.0**&tab=bodies —— **dataset 参数疑似重复拼接（`v1.0-v1.0`），疑为官方页面 bug**。https://clio.janelia.org/ 本身可访问（返回 JS 应用壳） | **需注意：URL 疑有官方笔误** |
| **NeuronBridge** | https://neuronbridge.janelia.org/ ，官方新闻 "**2025-11-07** – NeuronBridge now provides matches for the MaleCNS!" | 确认 |
| 官方 Gallery（媒体） | https://male-cns.janelia.org/media/ | 确认 |
| 官方下载页 | https://male-cns.janelia.org/download/ | 确认 |
| 官方 Release Notes | https://male-cns.janelia.org/release/ | 确认 |

---

## K. flat-connectome feather 文件 — **修正（数量与总大小都错）**

指南写「**三个** feather 文件、总计 **~1.1 GB**」。

**实测：`gs://flyem-male-cns/v1.0/connectome-data/flat-connectome/` 下官方下载页共列出 7 个 feather 文件，合计约 24.2 GB。**

| # | 文件名 | 大小 |
|---|---|---|
| 1 | `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 13 MB |
| 2 | `body-neurotransmitters-male-cns-v1.0.feather` | 42 MB |
| 3 | `body-stats-male-cns-v1.0-minconf-0.5.feather` | 780 MB |
| 4 | `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | **1.1 GB** ← 「1.1 GB」出处 |
| 5 | `syn-points-male-cns-v1.0-minconf-0.5.feather` | 12.7 GB |
| 6 | `syn-partners-male-cns-v1.0-minconf-0.5.feather` | 6.8 GB |
| 7 | `tbar-neurotransmitters-male-cns-v1.0.feather` | 2.7 GB |

**修正建议**：改为「flat-connectome 目录下共 **7** 个 feather 文件，总计约 **24 GB**；其中**连接矩阵** `connectome-weights-…feather` 单文件约 **1.1 GB**」。第三方项目 Fly.exe 也独立记录为 "**seven** checksum-locked flat-connectome tables"。

URL 前缀：`https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/`

- https://male-cns.janelia.org/download/
- https://github.com/Ibtisam-Mohammad/Fly.exe

---

## L. 编程接口 — **确认（cocoa 有一处版本滞后）**

| 接口 | 结论 |
|---|---|
| `neuprint-python` | **确认**：https://github.com/connectome-neuprint/neuprint-python ，官方推荐，`Client("https://neuprint.janelia.org", dataset='male-cns:v1.0', token=token)` |
| R 包 `natverse/malecns` | **确认**：https://github.com/natverse/malecns ；默认数据集 `male-cns:v1.0`；元数据含 `flywireType` / `mancType` / `itoleeHl` 列 |
| `YijieYin/connectome_data_prep` | **确认**：https://github.com/YijieYin/connectome_data_prep （含 maleCNS 预处理稀疏矩阵 + axon-dendrite 拆分） |
| `YijieYin/connectome_interpreter` | **确认**：https://github.com/YijieYin/connectome_interpreter （PyPI `connectome-interpreter`；notebook 支持 maleCNS/BANC/hemibrain/MANC 切换） |
| `flyconnectome/cocoa` | **确认存在**，已实现 FlyWire / hemibrain / MANC / **male CNS**。⚠️ **README 仍写 male CNS 为 `male-cns:v0.9`（未更新到 v1.0）**，引用时宜注明 |
| `navis` | **确认**：https://github.com/navis-org/navis ，官方下载页推荐；配 `navis-flybrains` 做跨模板空间变换 |
| `flyconnectome/2025malecns` notebooks | **确认**：https://github.com/flyconnectome/2025malecns ，Berg et al. 补充数据，含 `quantify-neuron-connections.ipynb`（⚠️ 该 notebook 内 `VERSION = 'v0.9'`，输出的是预印本口径计数） |

- https://male-cns.janelia.org/download/
- https://raw.githubusercontent.com/flyconnectome/cocoa/master/README.md
- https://raw.githubusercontent.com/flyconnectome/2025malecns/main/README.md
- https://raw.githubusercontent.com/YijieYin/connectome_interpreter/main/README.md
- https://raw.githubusercontent.com/natverse/malecns/master/README.md

---

## 汇总表：结论一览

| 声明 | 结论 | 关键修正 |
|---|---|---|
| A 规模 | **修正** | 166,700 是**正式发表+Codex**数字，非「社区过滤」；25,582,938 与 124,177,617 **已于 2026-09-20 用官方 v1.0 flat-connectome 坐实**（≥5 突触为 6,242,118；notebook 的 25,563,426 / 6,237,402 属 v0.9 口径） |
| B 版本 | **确认** | v0.9 官方两处写 10-05 与 10-03，不一致 |
| C 阈值 | **确认** | minconf 0.5；Codex MCNS 默认 5+ |
| D FlyWire | **修正** | 论文写 **50M** 突触（非 54.5M）；brain-only、雌性确认 |
| E ID/Codex | **部分确认 + 修正** | ID 不可互换✓；但**存在类型级 crosswalk**；`@` 跨库✓；托管 5 库✓ |
| F 相关数据集 | **确认 + 修正** | MAOL 是**右**视叶；hemibrain 是**雌性**；MAOL 与 MaleCNS 同一只果蝇 |
| G 三项发现 | **修正（最重要）** | 正式版 **8,069 / 138 / 289 / 71**（非 7,205 / 114 / 262 / 69）；4.8% 分母待核实 |
| H 示例细胞 | **确认** | AOTU012✓；R1-R6→DNg13✓；Shiu 2024 糖→SEZ→MN9✓（但为 FAFB 雌性脑；新 2026 Cell 味觉论文应并引） |
| I 许可 | **确认** | CC-BY 4.0 + 4 个署名实体✓；可补 Wellcome Trust / Champalimaud |
| J 工具 URL | **确认** | Clio 的 dataset 参数疑为官方笔误 `v1.0-v1.0` |
| K feather 文件 | **修正** | **7 个**文件约 24 GB；1.1 GB 是 connectome-weights 单文件 |
| L 编程接口 | **确认** | cocoa README 仍写 v0.9（滞后） |

---

## 主要 SOURCE 清单

**官方一手**
- https://male-cns.janelia.org/ ｜ https://male-cns.janelia.org/release/ ｜ https://male-cns.janelia.org/download/ ｜ https://male-cns.janelia.org/explore/ ｜ https://male-cns.janelia.org/media/ ｜ https://male-cns.janelia.org/build/dimorphism_overview/ ｜ https://male-cns.janelia.org/build/summary_types/AOTU012/
- https://www.janelia.org/project-team/flyem/male-cns-connectome ｜ https://www.janelia.org/project-team/flyem/hemibrain
- https://codex.flywire.ai/faq ｜ https://codex.flywire.ai/about_flywire ｜ https://codex.flywire.ai/api/download?dataset=fafb
- https://raw.githubusercontent.com/flyconnectome/2025malecns/main/README.md ｜ https://raw.githubusercontent.com/flyconnectome/2025malecns/main/supplemental_data/quantify-neuron-connections.ipynb

**文献数据库**
- Europe PMC（Cell 论文）：https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.cell.2026.08.015%22&resultType=core&format=json
- Europe PMC（预印本）：https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1101/2025.10.09.680999%22&resultType=core&format=json
- PubMed：https://pubmed.ncbi.nlm.nih.gov/42691995/
- Dorkenwald 2024：https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1038/s41586-024-07558-y%22&resultType=core&format=json
- Shiu 2024 全文：https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=11446845&rettype=xml

**权威第三方**
- Virtual Fly Brain「Which fly is this?」：http://v2-preview.virtualflybrain.org/about/whichfly/
- Science 新闻（124.2M）：https://www.science.org/content/article/new-connectome-shows-all-124-million-contact-points-fruit-fly-s-nervous-system
- UKRI 新闻（166,700 / 124M / 95%）：https://www.ukri.org/news/world-first-map-of-a-male-fly-brain-a-win-for-neuroscience/
- Smithsonian：https://www.smithsonianmag.com/smart-news/this-new-brain-map-shows-every-nerve-cell-in-an-adult-male-fruit-flys-central-nervous-system-heres-why-that-matters-180989490/
- 中文（预印本口径 166,691 / 11,691）：https://www.ithome.com/1/000/273.htm ｜ https://www.huxiu.com/article/4891644.html

**工具仓库**
- https://github.com/connectome-neuprint/neuprint-python ｜ https://github.com/natverse/malecns ｜ https://github.com/YijieYin/connectome_data_prep ｜ https://github.com/YijieYin/connectome_interpreter ｜ https://github.com/flyconnectome/cocoa ｜ https://github.com/navis-org/navis ｜ https://github.com/flyconnectome/2025malecns
