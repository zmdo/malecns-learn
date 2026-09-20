"""
p3_reference.py — 阶段 3 的「参考值」数据。

为什么把它单独放、而不是每次现查：
  neuPrint 会偶发 502（写这份代码时就遇到过一次全线故障），
  而学习页面不能因为服务器抖动就变成空白。所以：
    · 这里固化 2026-09-17 与本次实测的记录（含口径与查询语句）；
    · 页面与测试都从这里读，服务器可用时再"在线复现"做对照。

⚠️ 每个数字都必须带三样东西：值、口径、查询语句。
   没有口径的数字在本项目里一律视为不可用（阶段 2 的核心结论）。
"""
from __future__ import annotations

from typing import Any, Dict, List

MEASURED_ON = "2026-09-17（阶段 1 实测）"

# ======================================================================
# 对照表：阶段 1 用网页查到的值 → 阶段 3 用代码复现
# ======================================================================
# kind:
#   "pair"  一对类型之间的突触总数
#   "card"  某个类型的身份字段
#   "count" 某个集合的计数
CHECKS: List[Dict[str, Any]] = [
    # ---------------- 连通性与身份 ----------------
    {
        "id": "api-alive",
        "group": "自检",
        "label": "匿名 API 可用（无需 token）",
        "kind": "count",
        "value": 176422,
        "tolerance": 0,
        "note": ":Neuron 节点数。注意这比官方公布的 166,700 多 —— "
                "因为包含非典型/无 superclass 的节点。",
        "query": "MATCH (n:Neuron) RETURN count(n)",
    },
    {
        "id": "dn-g13-ids",
        "group": "身份卡",
        "label": "DNg13 的 bodyId 是 11074 / 512006",
        "kind": "card",
        "value": [11074, 512006],
        "note": "bodyId 不是稳定标识：跨版本可能变。长期项目请用 type + 形态做锚点。",
        "query": "MATCH (n:Neuron) WHERE n.type = 'DNg13' RETURN n.bodyId ORDER BY n.bodyId",
    },
    {
        "id": "dn-g13-fields",
        "group": "身份卡",
        "label": "DNg13 的 instance / superclass / 递质",
        "kind": "card",
        "value": {
            "instance": ["DNg13_L", "DNg13_R"],
            "superclass": "descending_neuron",
            "consensusNt": "acetylcholine",
            "flywireType": "DNg13",
        },
        "query": "MATCH (n:Neuron) WHERE n.type = 'DNg13' "
                 "RETURN n.bodyId, n.instance, n.superclass, n.consensusNt, n.flywireType",
    },
    {
        "id": "mn9",
        "group": "身份卡",
        "label": "MN9 的 bodyId 是 10331 / 16949，superclass = cb_motor",
        "kind": "card",
        "value": {"bodyId": [10331, 16949], "superclass": "cb_motor"},
        "query": "MATCH (n:Neuron) WHERE n.type = 'MN9' "
                 "RETURN n.bodyId, n.instance, n.superclass ORDER BY n.bodyId",
    },
    {
        "id": "bm-taste-unique",
        "group": "身份卡",
        "label": "全库唯一 type 含 'Taste' 的类型是 BM_Taste",
        "kind": "card",
        "value": ["BM_Taste"],
        "query": "MATCH (n:Neuron) WHERE n.type CONTAINS 'Taste' RETURN DISTINCT n.type",
    },

    # ---------------- 通路 A：视觉 → 运动 ----------------
    {
        "id": "a1-r16-l2",
        "group": "通路 A · 视觉→运动",
        "label": "R1–R6 → L2",
        "kind": "pair",
        "src": "R1-R6", "dst": "L2",
        "value": 107646,
        "alt_value_ge5": 107572,
        "tolerance": 5,
        "note": "阶段 1 记的是「未设阈值」的数。同一对连接设 ≥5 阈值后是 107,572 —— "
                "差 74 个突触（0.07%）。这就是「结论必须带口径」的实例。",
        "query": "MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron {type:'L2'}) "
                 "RETURN sum(r.weight)",
    },
    {
        "id": "a1-r16-l1",
        "group": "通路 A · 视觉→运动",
        "label": "R1–R6 → L1",
        "kind": "pair",
        "src": "R1-R6", "dst": "L1",
        "value": 103405,
        "tolerance": 5,
        "query": "MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron {type:'L1'}) "
                 "RETURN sum(r.weight)",
    },
    {
        "id": "a2-l2-tm2",
        "group": "通路 A · 视觉→运动",
        "label": "L2 → Tm2",
        "kind": "pair",
        "src": "L2", "dst": "Tm2",
        "value": 221186,
        "alt_value_ge5": 219357,
        "tolerance": 2000,
        "note": "2026-09-20 结案：用官方 flat-connectome（minconf-0.5）复核，"
                "两个数都**精确复现** —— 221,186 是未设阈值口径，219,357 是 ≥5 口径"
                "（差 1,829，正好是被砍掉的弱边）。当年「重测得到 219,357」不是数据集变了，"
                "而是重测时用了 ≥5 口径却没写出来。两个数都对，错的是没带口径。",
        "query": "MATCH (a:Neuron {type:'L2'})-[r:ConnectsTo]->(b:Neuron {type:'Tm2'}) "
                 "RETURN sum(r.weight)",
    },
    {
        "id": "a2-l2-tm1",
        "group": "通路 A · 视觉→运动",
        "label": "L2 → Tm1",
        "kind": "pair",
        "src": "L2", "dst": "Tm1",
        "value": 205428,
        "alt_value_ge5": 205004,
        "tolerance": 2000,
        "note": "与 Tm2 同批，同样已结案：未设阈值 205,428 / ≥5 口径 205,004（差 424）。",
        "query": "MATCH (a:Neuron {type:'L2'})-[r:ConnectsTo]->(b:Neuron {type:'Tm1'}) "
                 "RETURN sum(r.weight)",
    },
    {
        "id": "a3-tm2-t5",
        "group": "通路 A · 视觉→运动",
        "label": "Tm2 → T5c",
        "kind": "pair",
        "src": "Tm2", "dst": "T5c",
        "value": 61901,
        "alt_value_ge5": 51892,
        "tolerance": 3000,
        "note": "T5a–d 一批取其中较大者。未设阈值：T5a 57,808 / T5b 61,404 / "
                "T5c 61,901 / T5d 52,515（所以区间是 52,515–61,901）；"
                "≥5 口径：50,278 / 50,810 / 51,892 / 43,048。"
                "已用 flat-connectome 复核，两个口径都精确复现。",
        "query": "MATCH (a:Neuron {type:'Tm2'})-[r:ConnectsTo]->(b:Neuron {type:'T5c'}) "
                 "RETURN sum(r.weight)",
    },

    # ---------------- 通路 A 终点：DNg13 ----------------
    {
        "id": "dn-g13-degree",
        "group": "通路 A · 终点 DNg13",
        "label": "DNg13 的 pre / post / upstream / downstream",
        "kind": "card",
        "value": {"pre": 2127, "post": 6500, "upstream": 6500, "downstream": 15479},
        "note": "注意 pre/post 是**突触数**，upstream/downstream 是**伙伴数**。"
                "两者不是一回事（阶段 3 最常混的地方）。",
        "query": "MATCH (n:Neuron {bodyId: 11074}) "
                 "RETURN n.pre, n.post, n.upstream, n.downstream",
    },
    {
        "id": "dn-g13-top-input",
        "group": "通路 A · 终点 DNg13",
        "label": "DNg13 最强的上游类型（前 5）",
        "kind": "list",
        "value": [["CB0244", 167], ["LAL073", 161], ["GNG532", 156],
                  ["DNg97", 140], ["DNpe027", 127]],
        "note": "按类型聚合的突触总数。注意最强的几个突触数只有一百多 —— "
                "远小于视叶里的连接强度。",
        "query": "MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron {bodyId: 11074}) "
                 "RETURN a.type, sum(r.weight) AS w ORDER BY w DESC LIMIT 5",
    },

    # ---------------- 通路 B：糖味觉 → 摄食 ----------------
    {
        "id": "b1-bmtaste-gng015",
        "group": "通路 B · 糖味觉→摄食",
        "label": "BM_Taste → GNG015",
        "kind": "pair",
        "src": "BM_Taste", "dst": "GNG015",
        "value": 1376,
        "tolerance": 50,
        "query": "MATCH (a:Neuron {type:'BM_Taste'})-[r:ConnectsTo]->(b:Neuron {type:'GNG015'}) "
                 "RETURN sum(r.weight)",
    },
    {
        # ⚠️ 2026-09-20 修正：这一项原来写成 "GNG015 → MN9"，是错的。
        # 153 对应的是 **GNG654 → MN9** 那一跳（阶段 1 的通路表里也是这么标的）。
        # GNG015 → MN9 实测是 478，和下面 b2 的「MN9 最强上游」完全一致 ——
        # 同一个文件里自己打架，就是这次数据核对抓出来的。
        # 用下载的 feather 复核：GNG015→MN9 = 478，GNG654→MN9 = 153，两者都稳定。
        "id": "b1-gng654-mn9",
        "group": "通路 B · 糖味觉→摄食",
        "label": "GNG654 → MN9",
        "kind": "pair",
        "src": "GNG654", "dst": "MN9",
        "value": 153,
        "tolerance": 20,
        "note": "通路 B 的最后一跳。GNG015/GNG654 都直接连到 MN9："
                "GNG654→MN9 = 153，GNG015→MN9 = 478（见 b2 上游榜）。",
        "query": "MATCH (a:Neuron {type:'GNG654'})-[r:ConnectsTo]->(b:Neuron {type:'MN9'}) "
                 "RETURN sum(r.weight)",
    },
    {
        "id": "b2-mn9-top",
        "group": "通路 B · 糖味觉→摄食",
        "label": "MN9 最强的上游类型（前 5）",
        "kind": "list",
        "value": [["DNge062", 556], ["GNG015", 478], ["GNG120", 443],
                  ["GNG095", 436], ["GNG117", 413]],
        "query": "MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron {type:'MN9'}) "
                 "RETURN a.type, sum(r.weight) AS w ORDER BY w DESC LIMIT 5",
    },
]


# ======================================================================
# 同一份数据的三套口径（页面"口径"一节用）
# ======================================================================
CENSUS = [
    ("neuPrint / Codex 默认（脑区）", "≥5 突触", "约 624 万条",
     "门户上的交互查询、Pathways 工具默认口径"),
    ("flat-connectome 下载文件", "min confidence 0.5",
     "文件名里就写着 minconf-0.5", "下载的 feather 已经是筛过的数据"),
    ("未设阈值", "全部连接",
     "约 2,556 万条", "做全图统计时的原始规模"),
]

# DNg13 的输出按超类分布（阶段 1 实测）
DNG13_OUTPUT = [
    ("vnc_intrinsic", 3914, 373),
    ("ascending_neuron", 317, 35),
    ("vnc_motor", 187, 17),
    ("cb_intrinsic", 87, 67),
    ("descending_neuron", 76, 42),
]


def by_group() -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for c in CHECKS:
        out.setdefault(c["group"], []).append(c)
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    g = by_group()
    print(f"参考值共 {len(CHECKS)} 项，分 {len(g)} 组（实测日期 {MEASURED_ON}）")
    for name, items in g.items():
        print(f"\n{name}")
        for it in items:
            flag = " ⚠待核实" if it.get("status") == "待核实" else ""
            print(f"  · {it['label']} = {it['value']}{flag}")
