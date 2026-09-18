# MaleCNS Learn

学习 **MaleCNS v1.0**（成年雄性果蝇完整中枢神经系统连接组）的阶段性材料。

已完成两个阶段，各一份自包含 HTML，另有总览页做阶段切换：

| 页面 | 内容 |
|---|---|
| **`index.html`** | **总览 / 学习路线图** —— 六阶段一览，点按钮进入已完成阶段 |
| `phase0.html` | **阶段 0 · 打地基** —— 连接组学基本词汇与数量直觉 + **官方网格驱动的交互式 3D 脑区浏览器** |
| `phase1.html` | **阶段 1 · 在网页里逛** —— 在 neuPrint / Codex 里**亲手走通一条通路**，含逐跳可复现的查询与实测权重 |
| **`neuprint.html`** | **neuPrint 查询执行台** —— 在浏览器里**直接执行 Cypher 取回真实数据**（22 条预设、表头排序、导出 CSV） |

> 四个页面的**顶栏都有常驻的阶段切换器**（总览 / 阶段 0 / 阶段 1 / 执行台），
> 页脚也各有一个，方便来回跳。

---

## 快速开始

直接用浏览器打开 `index.html` 即可（无需服务器）：

```
index.html           ← 建议从这里开始（总览 + 阶段切换）
phase0.html          ← 阶段 0：打地基
phase1.html          ← 阶段 1：在网页里逛
neuprint.html        ← neuPrint 查询执行台（需联网）
```

> 阶段 0 的 3D 部分读取同目录的 `assets/mcns-meshes.js`（约 1 MB），
> 所以请**保持 `assets/` 与 HTML 的相对位置**，或者用本地服务器打开：
>
> ```bash
> python -m http.server 8000
> # 然后访问 http://localhost:8000/index.html
> ```

**联网要求**：
- `neuprint.html` **必须联网** —— 它直接请求 `neuprint.janelia.org`
- 阶段 1 页面里的链接需要联网，但页面本身离线可用
- 阶段 0 完全离线可用

---

## neuPrint 查询执行台

`neuprint.html` 是一个可以**真的跑出数据**的页面：

- **22 条预设查询**，覆盖阶段 1 讲到的全部通路（基础句式 / 通路 A / 通路 B / 探索统计）
- 点预设填入编辑器 → <kbd>Ctrl</kbd>+<kbd>Enter</kbd> 执行 → 结果实时返回
- 结果表**点表头可排序**，支持**导出 CSV**（自动处理逗号与引号转义）
- 显示 neuPrint **改写后的实际 Cypher**（便于学习它的查询计划）
- 失败时给出排查建议；**0 行结果会明确提示字段名陷阱**，而不是画一个空表

### 为什么不需要后端

neuPrint 的 API 开放了跨域访问：

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Allow-Methods: GET, POST, OPTIONS
```

所以页面从浏览器直接调官方端点即可，**没有中间层、没有代理**，
你看到的就是官方返回的原始结果。端点：

```
POST https://neuprint.janelia.org/api/custom/custom
     {"cypher": "...", "dataset": "male-cns:v1.0"}
```

---

## 阶段 0 页面内容

| 节 | 内容 |
|---|---|
| 00–02 | 阶段 0 过关标准、MaleCNS 数据本体、**它不是 FlyWire**（三点差异 + 相关数据集） |
| 03 | 连接组定义、EM 重建 6 阶段管线、分辨率、连接组学版图定位 |
| 04 | **接触点 ≠ 连接** 与阈值口径、权重是建模选择 |
| 05–09 | body ID / supervoxel 层级、注释字段、神经毡、hemilineage、递质预测与符号假设 |
| 10 | proofreading 与「完全校对」的代价 |
| 11–14 | MaleCNS vs FlyWire 全表、七个坑、术语表、10 题过关自测 |
| 15 | 资源、官方下载清单、**本页相对指南的修正表** |
| 07 | **交互式 3D 脑区浏览器**（官方网格） |

## 阶段 1 页面内容

| 节 | 内容 |
|---|---|
| 00–01 | 过关标准拆解、三个工具（neuPrint / Codex / Cell Type Explorer）的分工 |
| 02 | **neuPrint 实操**：Cypher 三句式、字段名陷阱、边方向判定、匿名 API |
| 03–04 | Codex 跨数据集复核、Cell Type Explorer 查类型是否存在 |
| 05 | **通路 A · 视觉 → 运动**：R1–R6 → L1/L2 → Tm1/Tm2/Tm4 → T4/T5 → LPTC → LoVP90b → DNg13 → VNC 运动神经元 |
| 06 | **通路 B · 糖味觉 → 摄食**：BM_Taste → GNG015/GNG178 → GNG654 → MN9 |
| 07–09 | 8 条动手练习、6 个工具级坑、8 题过关自测 |
| 10 | 资源与下一步 |

> 阶段 1 里所有连接权重都是 2026-09-17 通过 neuPrint **匿名只读 API 实测**的
> （dataset `male-cns:v1.0`），页面内每条查询都标了可复现的语句。
> 其中「LPTC → LoVP90b」一跳是基于强连接的**推断**（页面上用虚线标出），不是实测直连。

3D 浏览器支持：拖动旋转、滚轮缩放、点击脑区看介绍、双击复位、
正面/侧面视角、自动旋转、**显示内部结构**（切换拾取模式）。

---

## 数据来源

### 3D 网格（官方）

```
gs://flyem-male-cns/rois/fullbrain-roi-v5/mesh/<NAME>.ngmesh          84 个脑神经毡
gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0/mesh/            24 个 VNC 神经毡
```

- 格式：`neuroglancer_legacy_mesh`
  （[规范](https://neuroglancer-docs.web.app/datasource/precomputed/mesh.html)：
  `uint32 numVertices` → `float32 positions[nv*3]` → `uint32 indices[...]`，无每顶点计数表）
- 本仓库打包了其中 **26 个结构**（脑 + 视叶 + 腹神经索）
- 坐标为**原始纳米坐标**
- 许可 **CC-BY 4.0**，须引用 Berg et al. (2026) 及 FlyEM / HHMI Janelia

### 官方场景（含全部 45 个图层）

用 Neuroglancer 打开可以看到 EM、分割、神经毡 ROI、突触、跨数据集网格：

```
https://neuroglancer-demo.appspot.com/#!gs://flyem-male-cns/v1.0/male-cns-v1.0.json
```

---

## ⚠️ 网格已抽稀（必读）

官方 26 个结构的原始网格合计 **8,860,924 个三角形**，浏览器无法实时渲染。
仓库里的 `assets/mcns-meshes.js` 是经**顶点聚类（grid snapping）抽稀**的版本：

| | 原始 | 本仓库 |
|---|---|---|
| 三角形 | 8,860,924 | **31,838**（0.36%） |
| 每帧可见 | 167,298 | **14,331** |
| 文件 | 283 MB | **973 KB** |

**形状与相对位置保持不变，但表面细节已损失 —— 不可用于体积、表面积等定量测量。**
每个结构的抽稀网格边长（cell，单位 nm）都显示在页面的信息面板里。

需要原始精度请用官方 Neuroglancer 场景，或按下节重新生成。

---

## 重新生成网格数据

`_official/` 与 `assets/mcns-meshes.js` 都在 `.gitignore` 里（前者可重新下载，后者是构建产物）。
重建步骤：

```bash
# 1. 下载官方网格并转成本地格式（约 159 MB 下载，输出 mcns-meshes.js ≈ 283 MB）
python tools/fetch_official_meshes.py

# 2. 抽稀到浏览器可渲染的规模（默认 low 预设，输出 ≈ 1 MB）
python tools/decimate_meshes.py --preset low --scale 0.5
```

抽稀预设：

| 预设 | 三角形总数 | 适用 |
|---|---|---|
| `low` | ≈ 6.5 万 | Canvas 2D（页面默认） |
| `low --scale 0.5` | ≈ 3.2 万 | 更流畅（仓库内的版本） |
| `mid` | ≈ 34 万 | WebGL / 桌面 GPU |
| `high` | 不抽稀 | 仅离线分析 |

---

## 测试

```bash
python validate_pages.py           # 四个页面的结构 / 锚点 / 资源 / 内联 SVG / CSS 类名
node tools/test-neuprint-console.js  # 执行台：假 DOM + 假 fetch 跑完整链路（83 项）
node tools/test-3d.js              # 几何·投影·拾取（415 项，用示意图椭球）
node tools/test-3d-official.js     # 官方网格解析·坐标范围·取景·遮挡（204 项）
node tools/test-3d-boot.js         # 3D 页面接线：启动·事件·坐标系·面板（43 项）
```

> 三个 3D 测试需要先有 `assets/mcns-meshes.js`。
> `validate_page.py`（单数）是旧版，只校验 `phase0.html`；新页面请用 `validate_pages.py`。
>
> `test-neuprint-console.js` 用假 DOM + 假 fetch 执行页面里的内联脚本，
> 验证「执行 → 请求体正确 → 渲染表格 → 排序 → CSV → 错误处理 → 行数上限」
> 全链路，不需要浏览器、也不真的联网。

### 阶段 1 的数据可复现性

阶段 1 页面里的每一个连接权重都可以自己复现。查询走 neuPrint 的**匿名只读 API**
（不需要 token）：

```bash
curl -s -X POST 'https://neuprint.janelia.org/api/custom/custom' \
  -H 'Content-Type: application/json' \
  -d '{"cypher":"MATCH (n:Neuron) WHERE n.type = '\''DNg13'\'' RETURN n.bodyId, n.instance","dataset":"male-cns:v1.0"}'
```

页面第 05/06 节给出两条通路的**逐跳完整查询**，共 10 条，全部实测通过。

---

## 原始资料与核查

| 文件 | 说明 |
|---|---|
| `malecns-study-guide.md` | 六阶段学习路线（本页是其阶段 0 的配套材料） |
| `malecns-factcheck-2026-09-17.md` | 联网事实核查报告 |
| `MaleCNS_连接组学基础_中文报告.md` | 连接组学基础研究报告（9 大主题，逐条带 URL） |
| `malecns_scale.py` | 规模 / 密度 / 存储派生量计算 |

### 一处重要修正

指南混用了**预印本**与**正式发表**两套数字。正式 *Cell* 版（2026-09-03，
DOI `10.1016/j.cell.2026.08.015`）已更新：

| | 预印本 2025-10 | 正式 Cell 2026-09 |
|---|---|---|
| 神经元数 | 166,691 | **166,700** |
| 细胞类型总数 | 11,691 | **11,710** |
| 同构 / 异形 / 雄特 / 雌特 | 7,205 / 114 / 262 / 69 | **8,069 / 138 / 289 / 71** |

页面内所有数字均已按核查结果修正，并在「本页相对指南的修正」一节逐条列出。

---

## 引用

```
Berg et al. (2026). Whole-central nervous system connectome of the adult male
Drosophila. Cell 189(18):5504-5526.e15. DOI 10.1016/j.cell.2026.08.015
```

数据：FlyEM / HHMI Janelia、University of Cambridge、MRC LMB、Google Research。
数据许可 **CC-BY 4.0**（Cell 正文本身为订阅制）。

---

## 下一步

**阶段 1 · 在网页里逛**：打开 Codex（MCNS）或 neuPrint，
走通 `R1–R6 → … → DNg13` 或 `糖 GRN → SEZ → MN9`，并说出中间细胞类型。
