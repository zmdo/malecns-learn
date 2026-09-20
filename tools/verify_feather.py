"""
verify_feather.py — 用下载的 flat-connectome 复现阶段 1/3 的参考值。

这就是阶段 3 的过关标准「代码结果与网页查询一致」的可执行版本 ——
只不过走的是**下载的 feather** 这条路，而不是匿名 API：
不需要联网、不需要 neuPrint 活着，全图统计也快得多。

口径必须先说清楚（否则数字对不上会白查半天）：
  · 本文件是 minconf-0.5 版本，**没有**做「≥5 突触」的边级过滤，
    所以它对应参考值的「未设阈值」口径（r.weight >= 1）。
  · 参考值里带 alt_value_ge5 的项，是 neuPrint 默认 ≥5 口径下的数，
    和这里算出来的不是一回事。脚本会把两个都列出来。

用法：
    python tools/verify_feather.py            # 全部 pair 检查
    python tools/verify_feather.py --all      # 连 alt（≥5）口径一起算
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.feather as feather
except ImportError:
    print("需要 pandas + pyarrow：pip install pandas pyarrow")
    sys.exit(2)

import p3_reference as REF  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "_data")
ANN = os.path.join(DATA, "body-annotations-male-cns-v1.0-minconf-0.5.feather")
WGT = os.path.join(DATA, "connectome-weights-male-cns-v1.0-minconf-0.5.feather")


def main() -> int:
    show_all = "--all" in sys.argv

    for p in (ANN, WGT):
        if not os.path.isfile(p):
            print(f"找不到 {p}\n先跑：python tools/fetch_flat_connectome.py")
            return 2

    ann = pd.read_feather(ANN, columns=["bodyId", "type", "superclass"])
    tb = feather.read_table(WGT)
    pre, post, wt = (tb.column("body_pre"), tb.column("body_post"),
                     tb.column("weight"))

    print(f"注释 {len(ann):,} 行 · 连接 {tb.num_rows:,} 行 · "
          f"突触合计 {pc.sum(wt).as_py():,}")
    neurons = int(ann["superclass"].notna().sum())
    print(f"其中神经元（有 superclass）{neurons:,} 个\n")

    def ids(t: str):
        return pa.array(ann.loc[ann["type"] == t, "bodyId"].to_numpy())

    def pair(src: str, dst: str, thresh: int = 1):
        m = pc.and_(pc.is_in(pre, value_set=ids(src)),
                    pc.is_in(post, value_set=ids(dst)))
        if thresh > 1:
            m = pc.and_(m, pc.greater_equal(wt, thresh))
        sub = tb.filter(m)
        return sub.num_rows, pc.sum(sub.column("weight")).as_py()

    checks = [c for c in REF.CHECKS if c["kind"] == "pair"]
    bad = 0
    print("=" * 78)
    print(f"{'检查项':<26}{'参考值':>12}{'feather 实测':>14}{'差':>8}  判定")
    print("=" * 78)
    t0 = time.time()
    for c in checks:
        n, total = pair(c["src"], c["dst"])
        tol = c.get("tolerance", 0)
        diff = total - c["value"]
        if diff == 0:
            verdict = "✓ 完全一致"
        elif abs(diff) <= tol:
            verdict = f"✓ 在容差 ±{tol} 内"
        else:
            verdict = f"✗ 超出容差 ±{tol}"
            bad += 1
        flag = c.get("status", "")
        print(f"{c['label']:<26}{c['value']:>12,}{total:>14,}{diff:>+8,}  {verdict}"
              + (f"  [{flag}]" if flag else ""))
        if show_all and c.get("alt_value_ge5"):
            n5, t5 = pair(c["src"], c["dst"], 5)
            print(f"{'  └ ≥5 突触口径':<26}{c['alt_value_ge5']:>12,}{t5:>14,}"
                  f"{t5 - c['alt_value_ge5']:>+8,}  （边 {n5:,}）")

    print("=" * 78)
    print(f"耗时 {time.time() - t0:.1f}s · {len(checks) - bad}/{len(checks)} 项与参考值一致\n")

    # 顺手核一下「全图口径」：只保留两端都是神经元的边。
    neu = pa.array(ann.loc[ann["superclass"].notna(), "bodyId"].to_numpy())
    sub = tb.filter(pc.and_(pc.is_in(pre, value_set=neu),
                            pc.is_in(post, value_set=neu)))
    print("全图口径（两端都是神经元）：")
    print(f"  有向连接 {sub.num_rows:,} 条 · 突触 {pc.sum(sub.column('weight')).as_py():,}")
    print("  学习指南记的是 25,582,938 条 / 124,177,617 个突触 —— 对得上就说明"
          "指南那两个数是**神经元口径**，不是原始文件的口径。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
