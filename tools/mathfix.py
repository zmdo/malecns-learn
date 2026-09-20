"""
mathfix.py — 把 <mml:math> 公式恢复成可读的 Unicode 数学文本。

背景：
  extract_papers.py / extract_berg.py 抽取正文时会剥掉全部标签，
  连带把 <mml:math> 公式也剥成了连在一起的符号串（例如 "dvi/dt=(gi−…)/Tmbr"），
  或者干脆丢掉。而页面渲染时又没有公式排版库，於是你看到的就是一串乱码般的字符。

本模块提供一个两用的工具：
  1) mml_math_to_text()：把一段 MathML 转成人类可读的 Unicode 数学；
  2) 在抽取流程里被调用，把公式接回段落文本末尾，并加一个标记 class，
     页面据此用 <span class="math"> 排版。

用法（在抽取脚本里）：
    from mathfix import restore_math
    paras = restore_math(paras, xml_math_list)
"""
import html
import re

# ----------------------------------------------------------------------
# MathML → Unicode 文本
# ----------------------------------------------------------------------
_SUB_MROW = re.compile(
    r"<mml:msub>\s*<mml:mrow>(.*?)</mml:mrow>\s*<mml:mrow>(.*?)</mml:mrow>\s*</mml:msub>", re.S)
_SUB_MI = re.compile(
    r"<mml:msub>\s*<mml:mi>(.*?)</mml:mi>\s*<(?:mml:mi|mml:mrow)>(.*?)</(?:mml:mi|mml:mrow)>\s*</mml:msub>", re.S)
_SUP_MROW = re.compile(
    r"<mml:msup>\s*<mml:mrow>(.*?)</mml:mrow>\s*<mml:mrow>(.*?)</mml:mrow>\s*</mml:msup>", re.S)
_SUP_MI = re.compile(
    r"<mml:msup>\s*<mml:mi>(.*?)</mml:mi>\s*<mml:mi>(.*?)</mml:mi>\s*</mml:msup>", re.S)
_FRAC_MROW = re.compile(
    r"<mml:mfrac>\s*<mml:mrow>(.*?)</mml:mrow>\s*<mml:mrow>(.*?)</mml:mrow>\s*</mml:mfrac>", re.S)
_FRAC_MI = re.compile(
    r"<mml:mfrac>\s*<mml:mi>(.*?)</mml:mi>\s*<mml:mi>(.*?)</mml:mi>\s*</mml:mfrac>", re.S)


def _unwrap(s):
    """把内部的 mml 标签全部去掉，只留文本。"""
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def mml_math_to_text(mathml):
    """把一段 <mml:math>…</mml:math> 转成可读的 Unicode 数学文本。

    不做十全十美的 LaTeX 转换，只求**人能读懂**：
    下标用 _、上标用 ^、分式用 (a)/(b)。
    """
    s = re.sub(r"<\?[^?]*\?>", "", mathml)

    # 先把嵌套结构替换成标记形式
    prev = None
    while prev != s:
        prev = s
        s = _SUB_MROW.sub(lambda m: _unwrap(m.group(1)) + "_" + _unwrap(m.group(2)), s)
        s = _SUB_MI.sub(lambda m: _unwrap(m.group(1)) + "_" + _unwrap(m.group(2)), s)
        s = _SUP_MROW.sub(lambda m: _unwrap(m.group(1)) + "^" + _unwrap(m.group(2)), s)
        s = _SUP_MI.sub(lambda m: _unwrap(m.group(1)) + "^" + _unwrap(m.group(2)), s)
        s = _FRAC_MROW.sub(lambda m: "(" + _unwrap(m.group(1)) + ")/(" + _unwrap(m.group(2)) + ")", s)
        s = _FRAC_MI.sub(lambda m: _unwrap(m.group(1)) + "/" + _unwrap(m.group(2)), s)

    # 剩下的纯文本
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", "", s)
    # 常见符号归一
    s = s.replace("−", "−").replace("鈭?", "−")
    return s


# ----------------------------------------------------------------------
# 公式列表 & 接回段落
# ----------------------------------------------------------------------
def extract_math(xml):
    """按出现顺序取出全部 <mml:math>，返回 Unicode 文本列表（去重保序）。"""
    out, seen = [], set()
    for m in re.finditer(r"<mml:math[\s\S]*?</mml:math>", xml):
        t = mml_math_to_text(m.group(0))
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


# 公式在正文里应当接在哪一段的末尾：用"该段必须包含的片段"来定位。
# ⚠️ 锚点必须用**英文原文**里的片段 —— 抽取发生在翻译之前。
# 公式里的 `\n` 会渲染成换行（多条公式共用一段时用）。
ATTACH = {
    "dorkenwald": [
        # Methods → Quality assurance：F1 的定义式
        ("Quality assurance", "harmonic mean of recall", None),
    ],
    "shiu": [
        # Methods → Computational model：LIF 的三个方程
        ("Computational model", "using the following three differential equations", None),
        ("Computational model", "the membrane potential dynamics are defined by",
         "dv_i/dt = (g_i − (v_i − V_resting)) / T_mbr"),
        ("Computational model", "exponentially decays with the timescale", None),
    ],
}

# 每篇论文的公式文本（由 extract_math 从 XML 取出后按序对应）
FORMULAS = {
    "dorkenwald": {
        "harmonic mean of recall":
            "P = TP / (TP + FP)\n"
            "R = TP / (TP + FN)\n"
            "F₁ = (2 × P × R) / (P + R)",
    },
    "shiu": {
        "using the following three differential equations":
            "dv_i/dt = (g_i − (v_i − V_resting)) / T_mbr\n"
            "dg_i/dt = −g_i / τ\n"
            "g_i ← g_i + w_(j,i)   （当神经元 j 放电时）",
        "the membrane potential dynamics are defined by":
            "dv_i/dt = (g_i − (v_i − V_resting)) / T_mbr",
        "exponentially decays with the timescale":
            "dg_i/dt = −g_i / τ",
    },
}


def restore_math(name, blocks, xml):
    """把公式接到对应段落的末尾（原文侧），并标记 class。

    做法：把公式作为 `<span class="math">…</span>` 追加到目标段落文本后面。
    页面会把 .math 渲染成等宽、居中的公式块；公式里的 `\\n` 变成 <br>。
    """
    table = FORMULAS.get(name, {})
    if not table:
        return blocks
    done = set()

    def patch(paras, title):
        for i, p in enumerate(paras):
            for sec, needle, _ in ATTACH.get(name, []):
                if sec != title or needle in done:
                    continue
                if needle in p:
                    body = html.escape(table[needle]).replace("\n", "<br>")
                    paras[i] = p + ' <span class="math">' + body + "</span>"
                    done.add(needle)

    for b in blocks:
        patch(b.get("paras", []), b.get("title", ""))
        for s in b.get("subs", []):
            patch(s.get("paras", []), s.get("title", ""))
    return blocks


if __name__ == "__main__":
    import sys
    import os
    import json

    sys.stdout.reconfigure(encoding="utf-8")
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("dorkenwald", "shiu"):
        p = os.path.join(ROOT, "_papers", name + ".xml")
        if not os.path.isfile(p):
            continue
        xml = open(p, encoding="utf-8").read()
        print("=" * 70)
        print(name, "公式：")
        for t in extract_math(xml):
            print("   ", t)
