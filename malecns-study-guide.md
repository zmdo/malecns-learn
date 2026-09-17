# MaleCNS v1.0 学习指南

> 面向：有基础神经科学 / 机器学习背景，但没接触过连接组（connectome）的人。
> 资料截止：**2026-09-17**。MaleCNS v1.0 发布仅约 3 个月，专门教程极少，本文档把散落在官网、论文、社区仓库里的信息整理成一条可执行的路线。

---

## 0. 一分钟速览

- **MaleCNS** = 成年**雄性**果蝇的**完整中枢神经系统**连接组：中央脑 + 视叶 + 腹神经索（VNC），颈连接完整。
- 规模：**约 16.67 万神经元**，社区过滤口径为 **25,582,938 条有向连接 / 124,177,617 个突触接触点**。
- 官方门户：<https://male-cns.janelia.org/>；查询入口：neuPrint（`male-cns:v1.0`）。
- 主论文：Berg et al., *Cell*（2026-09-03），预印本 <https://www.biorxiv.org/content/10.1101/2025.10.09.680999v2>。
- 许可：**CC-BY 4.0**，发表必须引用。
- **它不是 FlyWire 的新版本**：FlyWire 是雌性**仅脑**、入口在 Codex；两者的 body ID 体系不通用。

---

## 1. 这是什么：数据集本体

### 1.1 规模与构成

| 项目 | 数值 | 说明 |
|---|---|---|
| 神经元 | **约 166,691**（官方报道口径） | 社区 flat-connectome 过滤后为 **166,700**，差值是过滤/注释口径造成的 |
| 有向连接（去重后） | **25,582,938** | 即"神经元 A → 神经元 B"的对数 |
| 突触接触点 | **124,177,617** | 接触点 ≠ 连接：一对神经元之间可以有多个突触 |
| 覆盖区域 | 中央脑 + 视叶 + 腹神经索 | VNC 相当于脊髓，是 FlyWire FAFB 完全没有的部分 |
| 数据版本 | v0.9（2025-10-05）、**v1.0（2026-06-08）** | v1.0 = 少量校对修改 + 注释细化 |
| 过滤阈值 | flat-connectome 用 **min confidence 0.5**；neuPrint/Codex 的 MCNS 默认 **≥5 突触** | 两套数字对不上是正常的 |

### 1.2 与 FlyWire 的对照（务必先分清）

| | **MaleCNS** | **FlyWire FAFB v783** |
|---|---|---|
| 性别 | 雄性 | 雌性 |
| 范围 | 全 CNS（脑 + 视叶 + VNC） | **仅脑** |
| 神经元 | ~166,691 | 139,255（已校对） |
| 突触 | ~1.24 亿接触点 | ~5,450 万 |
| 快照/发布 | v1.0，2026-06-08 | v783，2023-10 |
| 论文 | Berg et al., *Cell* 2026 | Dorkenwald et al., *Nature* 634:124 (2024)；Schlegel et al., *Nature* 634:139 (2024) |
| 官方门户 | [male-cns.janelia.org](https://male-cns.janelia.org/) / neuPrint | [flywire.ai](https://flywire.ai/) / [Codex](https://codex.flywire.ai/) |
| 编程接口 | `neuprint-python`、R 包 `natverse::malecns` | CAVEclient、`fafbseg-py` + `navis` |
| 生态成熟度 | 新，多为社区 demo | 成熟，有完整工具链和教程 |
| **ID 互通** | **不通用，绝不可混用** | 同上 |

相关但不同的数据集：**BANC**（雌性脑 + 神经索，v888 快照 2026-05-20）、**MANC**（雄神经索）、**MAOL**（雄视叶）、**Hemibrain**（2020 年早期部分数据）。Codex 把 FAFB / BANC / MANC / MAOL / MCNS 都收在一个界面里，可以跨数据集搜索（查询前加 `@`）。

### 1.3 科学结论（读论文时抓这几条）

- 鉴定出 **262 个性别特异细胞类型 + 114 个二态（dimorphic）类型**，合计占中央脑的 **4.8%**。
- 性别差异**集中在高级脑中心**；感觉与运动外周基本同构（isomorphic）。
- 虽然二态细胞占比很小，但二态性会通过**二态连接**向外传播——支持"少量接线改动即可造成全脑影响"这一连接组学基本命题。
- 官方示例通路：**R1–R6 光感受器 → … → DNg13 运动神经元**（视觉-运动）；性二态示例细胞类型：**AOTU012**。

---

## 2. 数据怎么拿

### 2.1 网页工具（无需安装任何东西）

| 工具 | 地址 | 用途 | 备注 |
|---|---|---|---|
| **Codex** | <https://codex.flywire.ai/>（数据集切到 MCNS v1.0） | 搜索、Stats、3D(Neuroglancer)、Connectivity、Pathways、Motifs、Cell Type Counts | 交互页需 Google 登录；静态页免登录。对 MCNS 只做交互浏览，不做权威下载 |
| **neuPrint**（官方） | <https://neuprint.janelia.org/?dataset=male-cns%3Av1.0&qt=findneurons> | 细胞/连接查询、骨架、NBLAST、3D | 官方查询门户 |
| **Cell Type Explorer** | <https://reiserlab.github.io/celltype-explorer-drosophila-male-cns/> | 细胞类型总目录 + **类型→类型连接矩阵** + eyemap | 想快速了解"有哪些类型"最好用 |
| **Neuroglancer 独立 3D** | `https://neuroglancer-demo.appspot.com/#!gs://flyem-male-cns/v1.0/male-cns-v1.0.json` | 全图层：EM、分割、突触、神经毡、骨架 | 叠加了两只雌蝇的配准网格，**可肉眼直接比雄/雌** |
| **Dimorphism Explorer** | <https://male-cns.janelia.org/build/dimorphism_overview/> | 262 特异 + 114 二态类型的对比 | 官方站内 |
| **Clio** | <https://clio.janelia.org/ws/annotate?dataset=male-cns:v1.0-v1.0&tab=bodies> | 按 hemilineage / 类型过滤的注释视角 | |
| **NeuronBridge** | <https://neuronbridge.janelia.org/> | EM 神经元 ↔ FlyLight 光镜品系匹配 | 把连接组接到遗传工具时用（2025-11-07 起支持 MaleCNS） |
| **官方 Gallery / Explore** | <https://male-cns.janelia.org/> | 渲染图、视频、发布说明 | |

### 2.2 下载原始数据

权威下载页：<https://male-cns.janelia.org/download/>。社区常用的三个 flat-connectome 文件（约 **1.1 GB**，min confidence 0.5）：

```
https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/
  ├─ body-annotations-male-cns-v1.0-minconf-0.5.feather   # 细胞注释（superclass 等）
  ├─ connectome-weights-male-cns-v1.0-minconf-0.5.feather # 连接权重（源、目标、接触数）
  └─ body-neurotransmitters-male-cns-v1.0.feather         # 预测递质
```

### 2.3 编程接口与现成工具

| 工具 | 语言 | 用途 |
|---|---|---|
| [neuprint-python](https://connectome-neuprint.github.io/neuprint-python/) | Python | 官方查询客户端 |
| [natverse/malecns](https://github.com/natverse/malecns) | R | MaleCNS 数据访问 |
| [connectome_data_prep](https://github.com/YijieYin/connectome_data_prep) | Python | **直接拿准备好的稀疏矩阵**（MaleCNS / BANC / FlyWire / hemibrain） |
| [connectome_interpreter](https://github.com/YijieYin/connectome_interpreter) | Python | 有效连接、寻路、回路操作、全脑规模可微模型 |
| [cocoa](https://github.com/flyconnectome/cocoa) | Python | 跨数据集共聚类 / 细胞分型匹配 |
| [navis](https://github.com/navis-org/navis) / [natverse](https://natverse.org/) | Py/R | 形态学分析与可视化 |
| [2025malecns](https://github.com/flyconnectome/2025malecns) | 笔记本 | **Berg 论文配套数据与分析 notebook——目前最接近"官方教程"的东西** |

---

## 3. 学习路线（6 阶段，每阶段有"过关标准"）

| 阶段 | 做什么 | 过关标准 |
|---|---|---|
| **0 · 打地基**（30 min） | 词表：连接组、body ID、细胞类型、神经毡 neuropil、hemilineage、递质、proofreading | 能说出 MaleCNS 与 FlyWire 的三点差异 |
| **1 · 网页里逛**（半天，最重要） | Codex(MCNS) + neuPrint + Cell Type Explorer；用 Pathways 工具手工走通一条已知通路 | 能走通 **R1–R6 → … → DNg13** 或 **糖 GRN → SEZ → MN9**，并说出中间细胞类型 |
| **2 · 读论文**（1 天） | 主论文 Berg et al. 2026 *Cell*；背景三件套 Dorkenwald 2024 / Schlegel 2024 / Shiu 2024 | 能解释"≥5 突触阈值"和"min confidence 0.5"如何改变连接数 |
| **3 · 拿数据 + 第一段代码**（1–2 天） | 下载三个 feather 或用 `neuprint-python`；建稀疏矩阵、算入度/出度、复现阶段 1 的通路 | 代码结果与网页查询一致 |
| **4 · 跑仿真**（2–3 天） | [mps-malecns-model](https://github.com/seohyunjun/mps-malecns-model)（Mac 最省事）→ 参考 [Doomfly](https://github.com/nftechie/doomfly) 的 C++ 内核 → 自己写 LIF | 刺激已知神经元→下游按预期激活，且**静默对照不激活** |
| **5 · 接身体**（1 周+） | [FlyGym / NeuroMechFly v2](https://github.com/NeLy-EPFL/flygym)，把下行神经元（DN）放电率解码为前进/转向 | 刺激左侧 DN → 只向左侧转；能分清哪部分是测量、哪部分是工程假设 |

**按阶段读论文的顺序建议**

1. Berg et al. 2026（主论文，先看摘要 + 前 3 张图）
2. Dorkenwald et al. 2024 *Nature*——FlyWire 接线图（建立"连接组长什么样"的直觉）
3. Schlegel et al. 2024 *Nature*——注释与细胞分型体系（看懂 `cell_type` / `super_class` 从哪来）
4. Shiu et al. 2024 *Nature*——全脑 LIF 模型（要做仿真必读）
5. 选读：Nern et al. 2025（视觉系统细胞库存）、Stürner et al. 2025（上下行神经元跨性别比较）

---

## 4. 数据模型与建模约定（做仿真必读）

连接组本身**只是接线图**，没有任何动力学。下面这些数字是社区项目（Doomfly / mps-malecns-model / Fly Dino）实际使用的约定，**是建模选择，不是测量值**：

```text
# 权重：按突触后神经元的总输入接触数归一化，再乘递质符号
W[j,i] = c[j,i] * s[j] / Σ_k ( c[k,i] * |s[k]| )

# 递质符号（假设，非事实）
s = +1  if 乙酰胆碱 (ACh)
    -1  if GABA 或 谷氨酸 (Glu)
     0  if 未知 / 仅调质 / 冲突      # MaleCNS 中约 3,718 个细胞符号不明

# LIF 动力学（Doomfly 参数）
v_next = exp(-dt/tau_m) * v + W·(上一步脉冲) + drive
spike  = (v_next >= threshold) ; 发放后 v_next = 0
dt = 0.1 ms,  tau_m = 20 ms,  不应期 = 2.2 ms,  传导延迟 = 1.8 ms
```

未建模的部分（写论文/汇报时必须声明）：受体层面的兴奋/抑制差异、神经调质、电突触、可塑性、学习、神经分支的形态学细节、真实放电率标定。

**阈值口径提醒**：neuPrint/Codex 的 MCNS 默认 **≥5 突触**才算一条连接；下载的 flat connectome 用 **min confidence 0.5**。做规模统计前先明确用的是哪一套。

---

## 5. 仿真性能参考（1 秒真实蝇时间需要多久）

> 没有 MaleCNS 的官方基准。下表把实测值与外推值分开标注。**dt = 0.1 ms 时，1 秒真实时间 = 10,000 步。**

### 5.1 同源参考：FlyWire 全脑 LIF（138,639 神经元 / 15.1M 连接，dt=0.1 ms）

数据来自 [eonsystemspbc/fly-brain](https://github.com/eonsystemspbc/fly-brain) 仓库中提交的 `data/benchmark-results.csv`（RTX 4070 机器）：

| 后端 | 单 trial（1 s 仿真） | 相对实时 | 批 8（80 s 仿真） |
|---|---|---|---|
| GeNN（GPU） | 0.52 s | **1.94×** | 12.6 s → **6.34×** |
| NEST GPU | 1.18 s | 0.85× | 85.2 s → 0.94× |
| Brian2GeNN（GPU） | 1.87 s | 0.53× | 152 s → 0.53× |
| Brian2（**CPU**，C++ standalone） | 2.66 s | 0.38× | 81.8 s → 0.98× |
| PyTorch（CUDA） | 9.82 s | 0.10× | 498 s → 0.16× |
| Brian2CUDA（GPU） | 11.94 s | **0.084×** | 339 s → 0.24× |

独立复现（[DGX Spark GB10，20 核 Grace + CUDA 13](https://grizzlypeaksoftware.com/articles/p/i-ran-a-fruit-flys-entire-brain-on-my-dgx-spark-then-gave-it-a-body-nxqdy1xn)）：Brian2 CPU **1.8 s**、Brian2CUDA **7.9 s**、PyTorch **12.0 s**；脑 + 身体（NeuroMechFly）跑 5 秒蝇时间需 **64 秒**计算。

**读这张表的关键**：模型活跃度只有约 0.3%（每步几百个神经元放电）。GeNN/NEST 是 **event-driven**（只处理放电神经元的输出突触）；PyTorch 每步做一次全图稀疏矩阵乘（1500 万条边），所以慢。**"GPU 反而输给 CPU"不是 GPU 不行，是单 trial 下问题太小、太稀疏。**

### 5.2 MaleCNS v1.0 的实测与外推

| 实现 | 硬件 | 1 秒真实时间需要 | 性质 |
|---|---|---|---|
| [mps-malecns-model](https://github.com/seohyunjun/mps-malecns-model)（全图，dt=1 ms） | Apple Silicon GPU (MPS) | **22.4 s**（实测 44.56 步/s） | 实测；换算到 dt=0.1 ms 约 224 s |
| [Fly64](https://github.com/ornata/fly)（全图 LIF） | M2 MacBook / 16 GB | ~50 步/s | 实测步率 |
| [Doomfly](https://github.com/nftechie/doomfly)（C++ 事件驱动内核） | 未公开 | 慢于实时（README 未给数） | 实测定性 |
| 优化 C++ 多核（Brian2 standalone 类） | 桌面 CPU | **~3–5 s** | 外推 |
| 同上 | 笔记本 CPU | **~10–20 s** | 外推 |
| 优化 event-driven CUDA 内核（GeNN 类） | 单张消费级 GPU | **~1–3 s（接近实时）** | 外推 |
| 每步扫全边表的 cuSPARSE 级矩阵乘 | 离散 GPU | **~15 s** | 外推（按 1.45 ms/步） |
| 每步扫全边表的 PyTorch/MPS 写法 | Apple GPU | **~200 s** | 实测外推 |

外推依据：FlyWire 上 Brian2 CPU 每 1 s 仿真约 1.8–2.7 s，折算神经元更新吞吐约 5×10⁸ 次/秒；MaleCNS = 166,700 神经元 × 10,000 步 ≈ 1.7×10⁹ 次更新/秒生物时间 → 约 3.3 s，再乘 1.2–1.7 的规模系数。

### 5.3 CPU 与 GPU 的取舍

| 维度 | 结论 |
|---|---|
| **CPU 单核 vs 多核** | 单核决定**下限**，多核决定**上限**，**8 核之后收益递减**。仿真是步同步的（每 0.1 ms 一个全局屏障），只能在步内并行；低活跃度下每步活儿很小，核一多同步开销就吃掉收益。选 **高主频 8 核 > 低频 16 核**，大 L3 有帮助（16.7 万神经元状态数组约 8 MB） |
| **GPU 显存** | 很小。CSR 形式约 **0.2 GB**；COO + 多份权重约 **0.5 GB**（社区实测值）；加神经元状态、突触状态、延时数组共 **1–2 GB**。**4 GB 能跑，8 GB 舒适**（批处理几乎不额外吃显存，每条 trial 状态只多 4 MB） |
| **绝对禁止** | 用 N×N 稠密矩阵（166,700² × 4 B = **111 GB**）；用 numpy/PyTorch 每步扫全边表的写法（比事件驱动慢 40–50 倍） |

---

## 6. 生态项目清单

![MaleCNS / FlyWire 生态图谱](fly-connectome-ecosystem.png)

### 6.1 MaleCNS 系（2026-06 之后的新浪潮）

| 项目 | 定位 |
|---|---|
| [Doomfly](https://github.com/nftechie/doomfly) | **最有名**：166,700 神经元 / 25,582,938 边接入 ViZDoom，原生 C++ LIF 内核，4,184 条 KC→MBON11 连接上跑多巴胺门控可塑性；公开承认训练失败（negative results） |
| [Fly64](https://github.com/ornata/fly) | 全图接 Super Mario 64，M2 MacBook，50 步/s；文档对"哪部分是测量/哪部分是假设"写得最诚实 |
| [Fly Dino](https://github.com/cobanov/flyjump) | 80 神经元子回路 + 243 参数 CEM 训练读出，held-out 99/100；**含回路静默因果对照**，方法学最规范 |
| [mps-malecns-model](https://github.com/seohyunjun/mps-malecns-model) | Apple MPS 实验性 LIF，自带 3D 活动 `report.html` |
| [malecns-reservoir-computing](https://github.com/JangYeongSil69420/malecns-reservoir-computing) | 全图当储备池（Tesla T4），Mackey-Glass 预测 |
| [Cell Type Explorer](https://github.com/reiserlab/celltype-explorer-drosophila-male-cns) / [Dimorphism Explorer](https://male-cns.janelia.org/build/dimorphism_overview/) | 类型浏览 / 雄雌对比 |
| 其他 demo | flm、DesktopFly/gnat、NeuroTerrarium、flyverse、FlyBoard、Minecraft/Half-Life mod、FLYT3、FlyPong 等 |

### 6.2 FlyWire 系（成熟、研究级）

| 项目 | 定位 |
|---|---|
| [Shiu et al. LIF 全脑模型](https://github.com/philshiu/Drosophila_brain_model)（*Nature* 634:210, 2024） | 整个仿真生态的源头，预测准确率约 91%；糖→MN9 是标准验证实验 |
| [Eon Systems fly-brain](https://github.com/eonsystemspbc/fly-brain) | 6 个后端 + 官方 benchmark + 数值对齐脚本；2026-03 与 FlyGym 结合做具身演示 |
| [flyvis](https://github.com/TuragaLab/flyvis) | 连接组约束的视觉系统深度模型（*Nature* 2024） |
| [flybody](https://github.com/TuragaLab/flybody) | MuJoCo 解剖级蝇体 + 强化学习运动（*Nature* 2025） |
| [FlyGym / NeuroMechFly v2](https://github.com/NeLy-EPFL/flygym) | 生物力学蝇体 + 感觉接口，具身实验标准框架 |
| [FlyBrainLab](https://github.com/FlyBrainLab/FlyBrainLab) | 可执行回路交互平台 |
| [FastFly](https://github.com/eonfathom/FastFly) | CUDA 推式 LIF，目标单卡实时 |

> **读这批项目的一条通用警告**（[awesome-fly](https://github.com/cobanov/awesome-fly) 自己也这么写）：它们几乎全是"**连接组当固定基底 + 只训练一个小读出层**"。生物学真实性来自接线，动力学、感受器映射、动作解码全是自定假设。"蝇子会玩 Doom" ≠ 学到行为。

---

## 7. 四个必踩的坑

1. **ID 会变**：v0.9 → v1.0 有校对改动，跨版本必须重映射；MaleCNS 与 FlyWire 的 ID **绝不能混用**。
2. **阈值口径不同**：neuPrint/Codex 的 MCNS 默认 **≥5 突触**；flat connectome 用 **min confidence 0.5**。两套数字对不上是正常的。
3. **符号是假设不是事实**：ACh→+1 / GABA、Glu→−1 / 未知→0 是建模选择。MaleCNS 中有 **3,718 个细胞递质符号不明**；受体层面的 E/I 差异、神经调质都未建模。
4. **授权**：CC-BY 4.0，发表必须引用 Berg et al. 及数据来源（FlyEM/HHMI Janelia、剑桥大学、MRC LMB、Google Research）。

---

## 8. 一周最小可行计划

| 天 | 任务 |
|---|---|
| D1 | Codex / neuPrint 里走通一条已知通路；读 Berg 摘要 + 前 3 张图 |
| D2 | 下载三个 feather（或直接用 `connectome_data_prep` 的现成矩阵），搞清字段含义 |
| D3–4 | 建稀疏矩阵，复现 D1 的通路，算入度/出度/类型统计 |
| D5 | 跑 `mps-malecns-model`，或自己写最小 LIF（dt=0.1 ms、τ=20 ms、权重=归一化接触数×符号），做**刺激 + 静默对照** |
| D6–7 | 把下行神经元读出接 FlyGym；接不上就先只做静态解码，**别硬上全脑闭环** |

---

## 9. 术语表

| 术语 | 含义 |
|---|---|
| 连接组 connectome | 神经元之间全部连接关系的图谱 |
| body ID / root ID | 神经元在某个数据版本中的唯一编号；随校对会变 |
| 细胞类型 cell_type / resolved_type | 综合多个来源后的主类型标签 |
| 神经毡 neuropil | 神经纤维网区域，相当于"脑区"的精细划分 |
| hemilineage | 发育谱系，常用于归类细胞 |
| 递质 nt_type / consensus_nt | 预测的神经递质类型（ACh / GABA / Glu / 等） |
| proofreading | 人工校对分割与突触，决定数据质量 |
| min confidence | 突触/连接的最低置信度阈值 |
| 下行神经元 DN / 上行神经元 AN | 脑 ↔ 神经索之间的指令通道，是"脑控身体"的关键接口 |
| GRN | 味觉受体神经元（gustatory receptor neuron） |
| SEZ | 食管下区（subesophageal zone） |
| KC / MBON | 蘑菇体 Kenyon 细胞 / 蘑菇体输出神经元 |
| NBLAST | 神经元形态相似度打分工具 |

---

## 10. 资源链接汇总

**官方**
- 项目主页 / 下载 / 发布说明：<https://male-cns.janelia.org/>
- Janelia 项目页（科学结论摘要）：<https://www.janelia.org/project-team/flyem/male-cns-connectome>
- neuPrint：<https://neuprint.janelia.org/?dataset=male-cns%3Av1.0>
- 官网源码 + Dimorphism Explorer：<https://github.com/janelia-flyem/male-cns>

**论文**
- Berg et al. 2026 *Cell*：<https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6>
- Cell 专辑页：<https://www.cell.com/consortium/male-fly-connectome>
- 预印本 v2：<https://www.biorxiv.org/content/10.1101/2025.10.09.680999v2>
- 论文配套数据与 notebook：<https://github.com/flyconnectome/2025malecns>

**工具与教程**
- Codex：<https://codex.flywire.ai/>
- FlyWire Academy（方法论通用）：<https://codex.flywire.ai/academy_home>
- 连接组数据教程：<https://github.com/sjcabs/fly_connectome_data_tutorial>
- 现成矩阵 / 可微模型：<https://github.com/YijieYin/connectome_data_prep>、<https://github.com/YijieYin/connectome_interpreter>
- R 接口：<https://github.com/natverse/malecns>
- 生态清单（含项目局限标注）：<https://github.com/cobanov/awesome-fly>

---

## 11. 不确定 / 待核实项（诚实标注）

- **166,691 与 166,700 的差异**来自不同过滤口径，官方论文的具体计数需以论文正文为准。
- **1.24 亿突触接触点**来自社区 flat-connectome（minconf 0.5）解析结果，可能不等于论文报告的突触总数。
- **MaleCNS 的 CPU/GPU 仿真速度全部为外推**（除 MPS 的 44.56 步/s 和 Fly64 的 50 步/s 两个实测点），目前不存在官方或第三方权威基准。
- **Eon Systems 是否已为 MaleCNS 提供后端支持**未确认；其 `fly-brain` 目前基于 FlyWire。
- Codex 中 MCNS 的下载能力有限，权威数据请走官方下载页。
