"""
regions.py — 「可点击的神经元组」→ 图索引 的映射层。

数据来源是 fly-arena `prepare` 编译好的图（`_ref/arena-data/graph/`）：
  ids.npy            图索引 → bodyId（按 bodyId 排序）
  neurons.feather    同一顺序的注释（type / superclass / somaSide …）
所以「图索引 i」与「注释行 i」是同一只神经元 —— 本模块启动时会断言这一点，
不用「大概对齐」这种假设。

分组规则全部是**数据驱动**的：要么按 superclass 精确匹配，要么按 type 前缀匹配，
要么按具名类型匹配。没有任何写死的神经元列表。每个组的神经元数都从数据里数出来，
所以「点下去到底刺激了多少个细胞」是可核查的。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pyarrow.feather as feather

# ----------------------------------------------------------------------
# 分组定义
# ----------------------------------------------------------------------
# kind: named（具名类型，行为最明确）/ superclass（超类）/ prefix（脑区，按 type 前缀）
# mesh: 关联的 MaleCNS 神经毡网格名（点右侧 3D 脑时用；None 表示只能从列表点）
GROUPS: List[dict] = [
    # ---- 具名行为神经元：刺激后行为最可预测，放最前面 ----
    {"id": "DNp09", "kind": "named", "match": "DNp09", "mesh": "VNC-T2",
     "zh": "DNp09 · 前进指令", "note": "下行神经元，放电率过阈值就开走"},
    {"id": "DNa02", "kind": "named", "match": "DNa02", "mesh": "VNC-T1",
     "zh": "DNa02 · 转向指令", "note": "左右不对称刺激 → 偏航"},
    {"id": "MDN", "kind": "named", "match": "MDN", "mesh": "VNC-T1",
     "zh": "MDN · 倒退（月球漫步）", "note": "爆发 → 向后走"},
    {"id": "DNp01", "kind": "named", "match": "DNp01", "mesh": "VNC-T1",
     "zh": "DNp01 · 巨纤维（逃跑）", "note": "逃跑命令神经元 → 起飞"},
    {"id": "DNg11", "kind": "named", "match": "DNg11", "mesh": "SEZ",
     "zh": "DNg11 · 梳理", "note": "放电 → 前足梳理"},
    {"id": "DNp02", "kind": "named", "match": "DNp02", "mesh": "VNC-T2",
     "zh": "DNp02 · 振翅/威胁抬翅", "note": "飞行肌相关下行神经元"},
    {"id": "DNg13", "kind": "named", "match": "DNg13", "mesh": "VNC-AB",
     "zh": "DNg13 · 下行（阶段 1 主角）", "note": "阶段 1 走通的那条通路的终点"},
    {"id": "MeVP24", "kind": "named", "match": "MeVP24", "mesh": "LO",
     "zh": "MeVP24 · 视觉下行", "note": "小叶板视觉投射"},
    {"id": "LC4_LPLC2", "kind": "named", "match": r"^(LC4|LPLC2)$", "mesh": "LO",
     "zh": "LC4 + LPLC2 · 逼近检测", "note": " loom 检测 → 逃跑/紧张乱窜"},
    {"id": "MN9", "kind": "named", "match": "MN9", "mesh": "SEZ",
     "zh": "MN9 · 取食运动神经元", "note": "喙肌；阶段 1 通路 B 的终点"},
    {"id": "BM_Taste", "kind": "named", "match": "BM_Taste", "mesh": "SEZ",
     "zh": "BM_Taste · 糖味觉感觉", "note": "全库唯一的味觉感觉类型"},

    # ---- 超类：覆盖全脑，量级大，效果偏「整体状态」 ----
    {"id": "sc:descending_neuron", "kind": "superclass", "match": "descending_neuron",
     "mesh": None, "zh": "下行神经元（全部）", "note": "脑 → 神经索的出口"},
    {"id": "sc:ascending_neuron", "kind": "superclass", "match": "ascending_neuron",
     "mesh": None, "zh": "上行神经元（全部）", "note": "神经索 → 脑的反馈"},
    {"id": "sc:vnc_motor", "kind": "superclass", "match": "vnc_motor",
     "mesh": "VNC-AB", "zh": "VNC 运动神经元", "note": "直接驱动腿/翅"},
    {"id": "sc:cb_motor", "kind": "superclass", "match": "cb_motor",
     "mesh": "SEZ", "zh": "中央脑运动神经元", "note": "喙/颈等"},
    {"id": "sc:vnc_intrinsic", "kind": "superclass", "match": "vnc_intrinsic",
     "mesh": "VNC-T1", "zh": "VNC 局部中间神经元", "note": "神经索内部回路"},
    {"id": "sc:cb_intrinsic", "kind": "superclass", "match": "cb_intrinsic",
     "mesh": "SMP", "zh": "中央脑局部中间神经元", "note": "中央脑内部回路"},
    {"id": "sc:ol_intrinsic", "kind": "superclass", "match": "ol_intrinsic",
     "mesh": "ME", "zh": "视叶局部中间神经元", "note": "最大的一群（约 8.9 万）"},
    {"id": "sc:visual_projection", "kind": "superclass", "match": "visual_projection",
     "mesh": "LO", "zh": "视觉投射神经元", "note": "视叶 → 中央脑"},
    {"id": "sc:cb_sensory", "kind": "superclass", "match": "cb_sensory",
     "mesh": "AL", "zh": "中央脑感觉神经元", "note": "嗅觉等"},
    {"id": "sc:ol_sensory", "kind": "superclass", "match": "ol_sensory",
     "mesh": "ME", "zh": "视叶感觉神经元", "note": "光感受器"},
    {"id": "sc:vnc_sensory", "kind": "superclass", "match": "vnc_sensory",
     "mesh": "VNC-AB", "zh": "VNC 感觉神经元", "note": "本体/机械感觉"},

    # ---- 解剖脑区：按 type 前缀 ----
    {"id": "pf:KC", "kind": "prefix", "match": r"^KC", "mesh": "MB",
     "zh": "蘑菇体 · Kenyon 细胞", "note": "学习与记忆"},
    {"id": "pf:MBON", "kind": "prefix", "match": r"^MBON", "mesh": "MB",
     "zh": "蘑菇体 · 输出神经元 MBON", "note": "蘑菇体输出"},
    {"id": "pf:CX", "kind": "prefix", "match": r"^(EPG|PB|FC|FR|PFN|PFL|ER|EL|EXR|IB|NO)",
     "mesh": "CX", "zh": "中央复合体（环状/桥状）", "note": "导航与朝向"},
    {"id": "pf:ORN", "kind": "prefix", "match": r"^ORN", "mesh": "AL",
     "zh": "触角叶 · 嗅觉受体 ORN", "note": "气味输入"},
    {"id": "pf:LN", "kind": "prefix", "match": r"^LN", "mesh": "AL",
     "zh": "触角叶 · 局部中间神经元 LN", "note": "嗅觉侧抑制"},
    {"id": "pf:LH", "kind": "prefix", "match": r"^LH", "mesh": "LH",
     "zh": "侧角 LH", "note": "先天气味反应"},
    {"id": "pf:optic", "kind": "prefix", "match": r"^(T\d|Tm|Mi|L\d|Lawf|C\d)",
     "mesh": "ME", "zh": "视叶 T / Tm / Mi / L 系", "note": "运动与亮度通路"},
    {"id": "pf:GNG", "kind": "prefix", "match": r"^GNG", "mesh": "SEZ",
     "zh": "颚神经毡 GNG（= Shiu 的 SEZ）", "note": "摄食中枢"},
]


def _matches(types: np.ndarray, superclasses: np.ndarray, rule: dict) -> np.ndarray:
    if rule["kind"] == "superclass":
        return superclasses == rule["match"]
    if rule["kind"] == "named":
        rx = re.compile(rf"^{rule['match']}$")
    else:
        rx = re.compile(rule["match"])
    return np.array([bool(rx.match(str(t))) for t in types], dtype=bool)


def load(graph_dir: Path) -> dict:
    """读图与注释，返回 {组 id: {…, "indices": np.ndarray}}（附一个 catalog 摘要）。"""
    graph_dir = Path(graph_dir)
    ids = np.load(graph_dir / "ids.npy")
    table = feather.read_table(graph_dir / "neurons.feather",
                               columns=["bodyId", "type", "superclass"]).to_pydict()
    body_ids = np.asarray(table["bodyId"], dtype=np.int64)
    if not np.array_equal(ids, body_ids):
        raise SystemExit("ids.npy 与 neurons.feather 不是同一顺序 —— 拒绝在未对齐的数据上映射")
    types = np.asarray([str(t) for t in table["type"]], dtype=object)
    superclasses = np.asarray([str(t) for t in table["superclass"]], dtype=object)

    out: Dict[str, dict] = {}
    for rule in GROUPS:
        idx = np.flatnonzero(_matches(types, superclasses, rule)).astype(np.int32)
        out[rule["id"]] = {
            "id": rule["id"], "zh": rule["zh"], "note": rule["note"],
            "kind": rule["kind"], "mesh": rule["mesh"],
            "indices": idx, "count": int(idx.size),
        }
    return {"groups": out, "neurons": int(ids.size)}


if __name__ == "__main__":
    import sys
    g = load(Path(sys.argv[1]))
    print(f"神经元总数 {g['neurons']:,}\n")
    print(f"{'组':26} {'神经元数':>9}  说明")
    print("-" * 78)
    for r in g["groups"].values():
        print(f"{r['id']:26} {r['count']:>9,}  {r['zh']}")
