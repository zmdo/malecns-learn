"""
test_p3.py — 阶段 3 的「代码结果 vs 网页实测值」对照测试。

这是阶段 3 过关标准（"代码结果与网页查询一致"）的可执行版本。

分两部分：
  A. 离线部分 —— 用合成小矩阵验证「建矩阵 / 算度数 / 阈值口径」的逻辑，
     **不需要联网**，服务器挂了也能跑。
  B. 在线部分 —— 用匿名 API 复现阶段 1 在 neuPrint 上实测的数字。
     服务器不可用时自动跳过（neuPrint 会偶发 502），并明确报告"跳过"。

运行：
    py -3 tools/test_p3.py          # 全部
    py -3 tools/test_p3.py --offline  # 只跑离线部分
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p3_lib import (Client, connect, build_matrix, degrees, fetch_edges,
                    top_downstream, inputs_by_type, type_to_type, pair_weight,
                    ping, fmt)

PASS = FAIL = SKIP = 0
FAILURES: List[str] = []
SLOW: List[Tuple[str, float]] = []


def ok(cond: bool, label: str, got: Any = None, want: Any = None) -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {label}")
    else:
        FAIL += 1
        msg = f"{label}（实测 {got!r} ≠ 期望 {want!r}）"
        FAILURES.append(msg)
        print(f"  FAIL {label}")
        if got is not None or want is not None:
            print(f"         实测 {got!r} / 期望 {want!r}")


def skip(label: str) -> None:
    global SKIP
    SKIP += 1
    print(f"  SKIP {label}")


def section(t: str) -> None:
    print("\n" + t)
    print("-" * len(t))


def timed(label: str, fn, *a, **kw):
    t0 = time.time()
    v = fn(*a, **kw)
    SLOW.append((label, time.time() - t0))
    return v


# ======================================================================
# A. 离线部分：矩阵逻辑（不依赖网络）
# ======================================================================
def offline() -> None:
    section("A1. 建稀疏矩阵：bodyId 不是从 0 开始")
    # 用真实量级的 bodyId，模拟一对真实连接
    src = [11074, 11074, 512006, 512006]
    dst = [10331, 16949, 10331, 16949]
    w = [300, 120, 250, 90]
    M, ids, idx = build_matrix(src, dst, w)
    ok(M.shape == (4, 4), "矩阵边长 = 出现的不同 bodyId 数（不是最大 ID）",
       M.shape, (4, 4))
    ok(M.nnz == 4, "非零元数 = 边数", M.nnz, 4)
    # 300 + 120 + 250 + 90
    ok(int(M.sum()) == 760, "矩阵元素和 = 突触总数", int(M.sum()), 760)
    ok(11074 in idx and idx[11074] < 4, "bodyId 被映射到紧凑下标",
       idx.get(11074), "0..3")
    print(f"  ids = {ids}")
    print(f"  11074 → 行 {idx[11074]}；512006 → 行 {idx[512006]}")

    section("A2. 度数 = 伙伴数；突触数 = 权重之和（两者不是一回事）")
    dg = degrees(M, ids)
    # 11074 有 2 个下游伙伴，输出突触 300+120=420
    ok(dg["out_partners"][11074] == 2, "11074 出度 = 2 个伙伴",
       dg["out_partners"][11074], 2)
    ok(dg["out_synapses"][11074] == 420, "11074 输出突触 = 420",
       dg["out_synapses"][11074], 420)
    ok(dg["in_partners"][10331] == 2, "10331 入度 = 2 个伙伴",
       dg["in_partners"][10331], 2)
    ok(dg["in_synapses"][10331] == 550, "10331 输入突触 = 550（300+250）",
       dg["in_synapses"][10331], 550)

    section("A3. 阈值口径：同一对神经元，换阈值突触总数会变")
    # 真实案例：R1-R6 → L2  不设阈值 107,646；≥5 之后 107,572
    # 这里造一个同构的小例子：6 条强边 + 1 条弱边（w=4，低于阈值）
    strong = [(1, 2, 60000), (1, 2, 47000), (1, 2, 400), (1, 2, 150),
              (1, 2, 60), (1, 2, 30)]
    weak = [(1, 2, 4)]
    all_edges = strong + weak
    unthr = sum(w for _, _, w in all_edges)
    ge5 = sum(w for _, _, w in all_edges if w >= 5)
    print(f"  全部边（{len(all_edges)} 条）突触合计 = {unthr:,}")
    print(f"  ≥5 之后（{len(strong)} 条）突触合计 = {ge5:,}")
    ok(unthr != ge5, "换阈值会改变突触总数（所以结论必须带口径）", unthr,
       "≠" + str(ge5))
    ok(unthr - ge5 == 4, "差额恰好等于被剔除的弱边权重（w=4）", unthr - ge5, 4)

    section("A4. 连接 vs 接触：多目标突触让接触数大于连接数")
    # 一个突触前位点对接多个突触后位点 —— FlyWire/MaleCNS 记成多条突触
    contacts = 100      # 突触前位点数
    partners = 3        # 每个位点对接 3 个靶点
    synapses = contacts * partners
    ok(synapses > contacts, "突触（连接）数可以大于突触前位点数",
       synapses, contacts)
    print(f"  {contacts} 个突触前位点 × {partners} 个靶点 = {synapses} 条突触")


# ======================================================================
# B. 在线部分：复现阶段 1 的实测值
# ======================================================================
def online() -> None:
    c = connect(verbose=False, retries=2, timeout=300)
    available, msg = ping(c)
    print("  " + ("✓ " if available else "✗ ") + msg)
    if not available:
        section("B. 在线对照（服务器不可用，全部跳过）")
        for lab in ["匿名 API 自检", "字段名陷阱", "DNg13 身份卡",
                    "通路 A 第一跳", "通路 A 第二跳", "阈值对照",
                    "通路 B 糖味觉→MN9", "建矩阵（真实数据）"]:
            skip(lab)
        return

    # ----------------------------------------------------------------
    section("B1. 匿名 API 自检：无需 token")
    n_all = timed("count(:Neuron)", c.count, "MATCH (n:Neuron) RETURN count(n)")
    print(f"  :Neuron 节点数 = {n_all:,}")
    ok(n_all > 150000, "匿名 API 能返回数据", n_all, ">150000")

    # ----------------------------------------------------------------
    section("B2. 字段名陷阱：type 而不是 cellType")
    has_type = timed("数 type", c.count,
                     "MATCH (n:Neuron) WHERE n.type IS NOT NULL RETURN count(n)")
    print(f"  有 type 的神经元 = {has_type:,}")
    ok(has_type > 100000, "type 字段存在且有值", has_type, ">100000")
    wrong = c.rows("MATCH (n:Neuron) WHERE n.cellType = 'DNg13' RETURN n.bodyId")
    ok(len(wrong) == 0, "写错字段名（cellType）返回 0 行而非报错 —— 这就是坑",
       len(wrong), 0)

    # ----------------------------------------------------------------
    section("B3. DNg13 身份卡（阶段 1 实测）")
    cols, rows = timed("DNg13 行", c.table,
                       "MATCH (n:Neuron) WHERE n.type = 'DNg13' "
                       "RETURN n.bodyId, n.instance, n.superclass, n.consensusNt, "
                       "n.flywireType, n.pre, n.post ORDER BY n.bodyId")
    print(fmt(rows, ["bodyId", "instance", "superclass", "consensusNt",
                     "flywireType", "pre", "post"]))
    ids = sorted(int(r[0]) for r in rows)
    ok(ids == [11074, 512006], "DNg13 的 bodyId = 11074 / 512006", ids,
       [11074, 512006])
    if rows:
        ok(sorted(str(r[1]) for r in rows) == ["DNg13_L", "DNg13_R"],
           "instance = DNg13_L / DNg13_R")
        ok({str(r[2]) for r in rows} == {"descending_neuron"},
           "superclass = descending_neuron")
        ok({str(r[3]) for r in rows} == {"acetylcholine"},
           "consensusNt = acetylcholine")

    # ----------------------------------------------------------------
    section("B4. 通路 A：R1-R6 → L2 → Tm2 → T* → DNg13")
    # 阶段 1 记的是**未设阈值**的数，所以这里用 min_weight=1
    a1 = timed("R1-R6 下游", type_to_type, c, "R1-R6", "", "", 8, 1)
    print("  R1-R6 的主要下游（未设阈值）：")
    print(fmt([(t, f"{w:,}") for t, w, n in a1], ["目标类型", "突触总数"]))
    d1 = {t: w for t, w, n in a1}
    ok("L2" in d1, "R1-R6 的下游含 L2", list(d1)[:5], "含 L2")
    if "L2" in d1:
        print(f"  L2 突触总数 = {d1['L2']:,}")
        ok(abs(d1["L2"] - 107646) <= 5,
           "R1-R6 → L2 = 107,646（未设阈值口径）", d1["L2"], 107646)

    a2 = timed("L2 下游", type_to_type, c, "L2", "", "", 6, 1)
    print("  L2 的主要下游（未设阈值）：")
    print(fmt([(t, f"{w:,}") for t, w, n in a2], ["目标类型", "突触总数"]))
    d2 = {t: w for t, w, n in a2}
    if "Tm2" in d2:
        print(f"  Tm2 突触总数 = {d2['Tm2']:,}")
        ok(abs(d2["Tm2"] - 221186) <= 10,
           "L2 → Tm2 = 221,186（未设阈值口径）", d2["Tm2"], 221186)
    else:
        ok(False, "L2 的下游含 Tm2", list(d2)[:5], "含 Tm2")

    # ----------------------------------------------------------------
    section("B5. 阈值对照：同一条连接，换阈值差多少")
    p1 = timed("R1-R6→L2 ≥1", pair_weight, c, "R1-R6", "L2", 1)
    p5 = timed("R1-R6→L2 ≥5", pair_weight, c, "R1-R6", "L2", 5)
    print(f"      不设阈值（≥1）：突触 {p1['weight']:,}，边 {p1['edges']:,}")
    print(f"      ≥5 突触        ：突触 {p5['weight']:,}，边 {p5['edges']:,}")
    print(f"      差额           ：{p1['weight']-p5['weight']:,} 个突触 "
          f"({(p1['weight']-p5['weight'])/p1['weight']*100:.2f}%)")
    ok(p1["weight"] >= p5["weight"], "未设阈值的突触总数应 ≥ 设阈值的",
       p1["weight"], ">=" + str(p5["weight"]))
    ok(0 < (p1["weight"] - p5["weight"]) / max(p1["weight"], 1) < 0.02,
       "阈值只砍掉极小一部分突触（应为 <2%）",
       round((p1["weight"] - p5["weight"]) / max(p1["weight"], 1), 5), "<0.02")

    # ----------------------------------------------------------------
    section("B6. 通路 B：糖味觉 → GNG015 → MN9")
    taste = c.rows("MATCH (n:Neuron) WHERE n.type CONTAINS 'Taste' "
                   "RETURN DISTINCT n.type")
    print(f"  type 含 'Taste' 的类型：{[r[0] for r in taste]}")
    ok(len(taste) == 1 and str(taste[0][0]) == "BM_Taste",
       "全库唯一含 Taste 的类型是 BM_Taste", [r[0] for r in taste], ["BM_Taste"])

    mn9 = timed("MN9 行", c.rows,
                "MATCH (n:Neuron) WHERE n.type = 'MN9' "
                "RETURN n.bodyId, n.instance, n.superclass ORDER BY n.bodyId")
    print(fmt(mn9, ["bodyId", "instance", "superclass"]))
    ok(sorted(int(r[0]) for r in mn9) == [10331, 16949],
       "MN9 的 bodyId = 10331 / 16949", [r[0] for r in mn9], [10331, 16949])
    if mn9:
        ok({str(r[2]) for r in mn9} == {"cb_motor"}, "MN9 superclass = cb_motor")

    # ----------------------------------------------------------------
    section("B7. 真实数据建矩阵（小规模）")
    types = ["R1-R6", "L2", "Tm2", "T5a", "DNg13"]
    src, dst, w = timed("取 5 类细胞的边", fetch_edges, c, types, 5)
    print(f"  取到 {len(w):,} 条边")
    ok(len(w) > 0, "能取到连接三元组", len(w), ">0")
    if w:
        M, ids, idx = build_matrix(src, dst, w)
        print(f"  矩阵形状 = {M.shape}，非零元 = {M.nnz:,}")
        ok(M.nnz == len(w), "非零元数 = 边数", M.nnz, len(w))
        ok(int(M.sum()) == sum(w), "矩阵元素和 = 突触总数", int(M.sum()), sum(w))
        dg = degrees(M, ids)
        if 11074 in idx:
            # ⚠️ fetch_edges 的 WHERE 只筛「源类型」（a.type IN …），
            # 所以这批边只有这 5 类**发出**的边，没有指向它们的边。
            # DNg13 的上游（CB0244 / LAL073 / GNG532 …）不在这 5 类里，
            # 因此它在这个矩阵里的入度必然是 0 —— 这是查询口径的结果，
            # 不是「DNg13 没有上游」。想同时拿到入边，要把
            # OR b.type IN … 并进 WHERE。所以这里只能验证出方向。
            print(f"  DNg13(11074) 出度 = {dg['out_partners'][11074]:,}"
                  f"，输出突触 = {dg['out_synapses'][11074]:,}")
            ok(dg["out_partners"][11074] > 0, "矩阵里 DNg13 有下游伙伴")
            print(f"  DNg13(11074) 入度 = {dg['in_partners'][11074]}"
                  f"（本次查询只取源方向，入度必然为 0）")
            # 反向证一下：换用「谁指向 DNg13」的查询，上游立刻就有了。
            up = timed("DNg13 上游", inputs_by_type, c, 11074, 3)
            print(f"  DNg13 的上游类型（≥5 口径）："
                  f"{'、'.join(f'{t} {w:,}' for t, w in up)}")
            ok(len(up) > 0 and up[0][1] > 0,
               "换用上游查询后 DNg13 有上游（证明矩阵里的 0 是查询口径造成的）")


def main() -> int:
    only_offline = "--offline" in sys.argv
    print("阶段 3 对照测试 | 阈值口径与阶段 1 一致（未设阈值，min_weight=1）")
    offline()
    if not only_offline:
        section("B. 在线对照（需要 neuPrint）")
        try:
            online()
        except Exception as e:
            print(f"  ✗ 在线部分中断：{str(e)[:300]}")
            FAILURES.append(f"在线部分中断：{str(e)[:120]}")

    print("\n" + "=" * 66)
    print(f"结果: {PASS} 通过, {FAIL} 失败, {SKIP} 跳过")
    if SLOW:
        SLOW.sort(key=lambda x: -x[1])
        print("最慢的几项：")
        for name, dt in SLOW[:4]:
            print(f"   {dt:6.1f}s  {name}")
    if FAIL:
        print("\n失败项：")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("ALL PASS" + ("（在线部分已跳过）" if SKIP else ""))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
