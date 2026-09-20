"""
build_phase3.py — 生成 phase3.html。

为什么用生成器而不是手写 HTML：
  页面上的代码块必须与**实际测试过的 .py 文件**逐字一致。
  手抄一遍就会走样，走样了就没人能复现。所以这里从源码里切片段嵌入。

运行：
    py -3 tools/build_phase3.py
"""
from __future__ import annotations

import html
import os
import re
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_reference as REF  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "phase3.html")


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def snippet(path: str, start: str, end: str | None = None,
            strip_doc: bool = True) -> str:
    """从源码里切一段（含 start，不含 end）。用于把真正跑过的代码嵌进页面。

    切出来的片段要 dedent —— 源文件里的缩进在 f-string 三元引号里会累积，
    导致等宽代码块横向溢出（校验器会报"最宽 835 列"）。
    """
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    i = src.find(start)
    if i < 0:
        raise SystemExit(f"在 {path} 里找不到片段起点：{start!r}")
    j = len(src) if end is None else src.find(end, i + len(start))
    if j < 0:
        raise SystemExit(f"在 {path} 里找不到片段终点：{end!r}")
    seg = src[i:j].rstrip()
    if strip_doc:
        seg = re.sub(r'^\s*"""[\s\S]*?"""\s*\n', "", seg)
    return textwrap.dedent(seg)


def style_of(path: str) -> str:
    """取某个页面 <style> 块的全部内容（不含标签）。

    为什么要整体取，而不是按标记切：
      阶段 1 的「设计系统」（.wrap / .box / .tw / .lead / .num / .en / .pill /
      .check …）和它自己的页面专属样式（.hero / .chip / .stat …）在 <style>
      里是**交错**的 —— 按 ".wrap{" 之类的标记去切一定会漏掉前者。
      历史上这里就出过一次事故：切到 ".wrap{"（在文件很靠前的位置），
      结果 10940 字符的样式只留下 1844 字符，
      阶段 3 于是掉了全部组件样式（表格、提示框、侧栏全部失效）。
      多带几条本页用不到的规则没有任何代价，掉样式才是致命的。
    """
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    m = re.search(r"<style>([\s\S]*?)</style>", src)
    if not m:
        raise SystemExit(f"在 {path} 里找不到 <style> 块")
    return m.group(1).strip("\n")


def code(src: str, lang: str = "python", title: str = "") -> str:
    head = f'<div class="codeh"><span class="cl">{esc(title or lang)}</span></div>' if title else ""
    return (f'<div class="codewrap">{head}'
            f'<pre class="cp" data-lang="{esc(lang)}">{esc(src)}</pre></div>')


# ======================================================================
# 从验证过的源码里取代码块
# ======================================================================
MIN_CLIENT = snippet("tools/p3_lib.py",
                     "class Client:",
                     "# ======================================================================\n# 2.",
                     strip_doc=False)

BLOCK_MATRIX = snippet("tools/p3_lib.py",
                       "def fetch_edges(client: Client,",
                       "def degrees(M, ids: Sequence[int])",
                       strip_doc=False)

BLOCK_DEGREES = snippet("tools/p3_lib.py",
                        "def degrees(M, ids: Sequence[int])",
                        "# ======================================================================\n# 3.",
                        strip_doc=False)

BLOCK_PATH = snippet("tools/p3_lib.py",
                     "def type_to_type(client: Client,",
                     "def inputs_by_type(",
                     strip_doc=False)

MIN_RUN = snippet("tools/test_p3.py",
                  "    section(\"B5. 阈值对照",
                  "    # ----------------------------------------------------------------\n    section(\"B6.",
                  strip_doc=False)


def ref_rows() -> str:
    """参考对照表：按组列出。"""
    out = []
    for group, items in REF.by_group().items():
        out.append(f'<tr class="grp"><td colspan="3">{esc(group)}</td></tr>')
        for it in items:
            flag = ('<span class="pill r" style="margin-left:6px">待核实</span>'
                    if it.get("status") == "待核实" else "")
            val = it["value"]
            if isinstance(val, list):
                if val and isinstance(val[0], (list, tuple)):
                    shown = "，".join(f"{a} {b:,}" for a, b in val)
                elif all(isinstance(x, int) for x in val):
                    shown = " / ".join(f"{x:,}" for x in val)
                else:
                    shown = " / ".join(str(x) for x in val)
            elif isinstance(val, dict):
                shown = "；".join(
                    f"{k} = {'/'.join(map(str, v)) if isinstance(v, list) else v}"
                    for k, v in val.items())
            else:
                shown = f"{val:,}" if isinstance(val, int) else str(val)
            # 有 ≥5 口径的项直接把两个数都列出来 —— 本页的核心结论就是
            # 「同一对连接，换阈值数字就变」，藏起来反而要读者自己去别处找。
            alt = it.get("alt_value_ge5")
            alt_html = (f'<span class="altv">≥5 口径 {alt:,}</span>' if alt else "")
            q = it.get("query", "")
            out.append(
                f"<tr><td>{esc(it['label'])}{flag}</td>"
                f"<td class=\"n\">{esc(shown)}{alt_html}</td>"
                f"<td><code class=\"q\">{esc(q)}</code></td></tr>")
    return "\n".join(out)


def ref_json() -> str:
    """给页面的交互比对器用的数据。"""
    import json
    slim = []
    for it in REF.CHECKS:
        if it["kind"] in ("pair", "count"):
            slim.append({"id": it["id"], "label": it["label"],
                         "value": it["value"],
                         "tol": it.get("tolerance", 0),
                         "src": it.get("src", ""), "dst": it.get("dst", "")})
    return json.dumps(slim, ensure_ascii=False)


def census_rows() -> str:
    return "\n".join(
        f"<tr><td>{esc(a)}</td><td><b>{esc(b)}</b></td><td class=\"n\">{esc(c)}</td>"
        f"<td>{esc(d)}</td></tr>" for a, b, c, d in REF.CENSUS)


def dng13_rows() -> str:
    total = sum(n for _, n, _ in REF.DNG13_OUTPUT)
    out = []
    for sc, n, w in REF.DNG13_OUTPUT:
        pct = w / total * 100
        out.append(f"<tr><td class=\"n\">{esc(sc)}</td><td class=\"n\">{n:,}</td>"
                   f"<td class=\"n\">{w:,}</td>"
                   f"<td><span class=\"bar\" style=\"width:{pct:.1f}%\"></span>"
                   f"<span class=\"pc\">{pct:.0f}%</span></td></tr>")
    out.append(f"<tr class=\"tot\"><td>合计</td><td class=\"n\">—</td>"
               f"<td class=\"n\">{total:,}</td><td></td></tr>")
    return "\n".join(out)


# ======================================================================
# 页面
# ======================================================================
def build() -> str:
    # 沿用阶段 1 的整套设计系统（含 .wrap / .box / .tw / .lead / .num / .en /
    # .pill / .check / nav.toc …）。整体取，见 style_of() 里的说明。
    css = style_of("phase1.html")

    toc = [
        ("env", "01 · 环境自检"),
        ("what", "02 · 这一步到底在做什么"),
        ("model", "03 · 心智模型：先分清四件事"),
        ("data", "04 · 数据从哪来"),
        ("cook", "05 · 照着敲：六段代码"),
        ("verify", "06 · 对照表：你的输出 vs 实测值"),
        ("pitfalls", "07 · 四个必踩的坑"),
        ("checkpoint", "08 · 过关自检"),
        ("refs", "09 · 参考与延伸"),
    ]
    toc_html = "\n".join(
        f'<a href="#{i}">{esc(t)}</a>' for i, t in toc)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>阶段 3 · 拿数据与第一段代码 | MaleCNS 学习指南</title>
<style>
{css}
  /* ---------- 本页新增组件 ---------- */
  nav.toc a{{display:block; padding:6px 10px; border-radius:8px; color:var(--ink3);
    font-size:14px; border-left:2px solid transparent; margin-bottom:2px}}
  nav.toc a:hover{{background:#131c33; color:var(--ink); text-decoration:none}}
  nav.toc a.on{{color:var(--green); border-left-color:var(--green); background:#0d1a12}}
  nav.toc .th{{font-size:11.5px; letter-spacing:.12em; text-transform:uppercase;
    color:var(--dim); margin:16px 0 8px; padding-left:10px}}

  .codewrap{{margin:16px 0; border:1px solid #223052; border-radius:12px;
    background:#0b1424; overflow:hidden}}
  .codeh{{display:flex; align-items:center; gap:10px; padding:7px 14px;
    background:#101a2e; border-bottom:1px solid #223052}}
  .codeh .cl{{font-family:var(--mono); font-size:11.5px; color:var(--cyan);
    letter-spacing:.04em}}
  .codeh .cp{{margin-left:auto; font-family:var(--mono); font-size:11px; color:var(--dim)}}
  pre.cp{{margin:0; border:none; border-radius:0; padding:14px 18px;
    max-height:560px; overflow:auto; font-size:12.6px; line-height:1.68}}
  .copybtn{{font:inherit; font-size:11.5px; background:#16233d; color:var(--ink3);
    border:1px solid var(--line2); border-radius:7px; padding:2px 10px; cursor:pointer}}
  .copybtn:hover{{color:var(--ink); border-color:var(--green)}}
  .copybtn.ok{{color:var(--green); border-color:#17411f; background:#0d1a12}}

  code.q{{font-size:11.4px; color:#9fb6d6; background:#0f1a2e; display:inline-block;
    padding:2px 7px; max-width:420px; overflow:hidden; text-overflow:ellipsis;
    white-space:nowrap; vertical-align:bottom}}
  tr.grp td{{background:#101a2e; color:var(--cyan); font-weight:700;
    font-size:13px; letter-spacing:.03em}}
  tr.tot td{{border-top:1px solid var(--line2); color:var(--ink); font-weight:700}}
  /* 表格里的占比条。注意必须限定在 .tw 之内 ——
     阶段 1 的顶栏是 <header class="bar">，裸 .bar 会给它加上
     margin-right / border-radius，顶栏右侧会裂开一道缝。 */
  .tw .bar{{display:inline-block; height:9px; background:linear-gradient(90deg,#22d3ee,#4ade80);
    border-radius:5px; vertical-align:middle; margin-right:8px; min-width:2px}}
  .pc{{font-family:var(--mono); font-size:11.5px; color:var(--ink3)}}
  /* 参考表里并列显示的第二个口径（未设阈值 vs ≥5） */
  .altv{{display:block; font-size:11.5px; color:var(--dim); white-space:nowrap}}

  .verifier{{background:var(--panel); border:1px solid var(--line); border-radius:13px;
    padding:16px 18px; margin:20px 0}}
  .vrow{{display:flex; flex-wrap:wrap; gap:10px; align-items:center;
    padding:9px 0; border-bottom:1px solid var(--line); font-size:14px}}
  .vrow:last-child{{border-bottom:none}}
  .vrow .lab{{flex:1 1 260px; min-width:0; color:var(--ink2)}}
  .vrow input{{width:120px; background:#0b1424; color:var(--ink); border:1px solid #223052;
    border-radius:8px; padding:5px 10px; font-family:var(--mono); font-size:13px}}
  .vrow input:focus{{outline:none; border-color:var(--green)}}
  .vrow .val{{font-family:var(--mono); font-size:12.5px; color:var(--dim); width:96px}}
  .vrow .res{{font-family:var(--mono); font-size:12.5px; width:120px}}
  .vrow.ok .res{{color:var(--green)}} .vrow.bad .res{{color:var(--red)}}
  .vrow.close .res{{color:var(--amber)}}
  .vsum{{margin-top:12px; font-size:14px; color:var(--ink2)}}
  .vsum b{{color:var(--ink)}}

  .stepgrid{{display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
    gap:12px; margin:18px 0}}
  .sc{{background:var(--panel); border:1px solid var(--line); border-radius:11px;
    padding:13px 15px}}
  .sc .n{{font-family:var(--mono); font-size:11.5px; color:var(--green)}}
  .sc h4{{margin:4px 0 6px; font-size:14.6px; color:var(--ink)}}
  .sc p{{margin:0; font-size:13.2px; color:var(--ink3); line-height:1.6}}
  .os{{display:inline-block; font-family:var(--mono); font-size:11px; padding:1px 7px;
    border-radius:5px; border:1px solid var(--line2); color:var(--ink3); margin-right:5px}}
</style>
</head>
<body>

<header class="bar">
  <nav class="phaseswitch" aria-label="阶段切换">
    <a href="index.html">总览</a>
    <a href="phase0.html">阶段 0</a>
    <a href="phase1.html">阶段 1</a>
    <a href="phase2.html">阶段 2</a>
    <span class="on">阶段 3 · 写代码</span>
    <a href="neuprint.html">执行台</a>
  </nav>
  <span class="t">拿数据与第一段代码</span>
  <span class="sp"></span>
  <span class="meta" id="barMeta">Python + neuPrint 匿名 API</span>
</header>

<div class="wrap">
  <nav class="toc">
    <div class="th">本页目录</div>
    {toc_html}
    <div class="th">过关标准</div>
    <p style="font-size:12.6px; color:var(--dim); padding:0 10px; line-height:1.6">
      代码算出来的数，<b style="color:var(--amber)">与阶段 1 在网页上查到的对得上</b>。
    </p>
  </nav>

  <main>

  <!-- ================= 01 环境 ================= -->
  <section id="env">
    <h2><span class="num">01</span>环境自检<span class="en">先确认能跑</span></h2>
    <p class="lead">
      这一页不像阶段 1/2 那样"打开就能看" —— 它需要你在本机跑 Python。
      所以第一步不是读代码，而是<b>确认环境没问题</b>。下面三条按顺序做，任何一条失败就先解决它。
    </p>

    <div class="stepgrid">
      <div class="sc"><div class="n">STEP 1</div><h4>有 Python 3.9+</h4>
        <p><code>python --version</code> 或 <code>py -3 --version</code>。
        没有就去 python.org 装，勾选 "Add to PATH"。</p></div>
      <div class="sc"><div class="n">STEP 2</div><h4>有 requests</h4>
        <p>本页代码<b>只依赖 requests</b>（不需要 neuprint-python）。
        <code>pip install requests</code> 即可。</p></div>
      <div class="sc"><div class="n">STEP 3</div><h4>能连上 neuPrint</h4>
        <p>跑一下下面的 <code>ping()</code>。返回 <code>✓ 可用</code> 就可以往下走。</p></div>
    </div>

    {code('''# 环境自检：三条全过再往下
import sys
print("Python", sys.version.split()[0])

try:
    import requests
    print("requests", requests.__version__)
except ImportError:
    print("✗ 缺 requests —— 先跑：pip install requests")

try:
    import numpy, scipy
    print("numpy", numpy.__version__, "| scipy", scipy.__version__)
except ImportError:
    print("✗ 缺 numpy/scipy（第 5 段代码要用）—— pip install numpy scipy")''', "python", "环境自检")}

    {code('''# 连通性自检：neuPrint 的匿名只读 API 不需要 token
import json, urllib.request

URL = "https://neuprint.janelia.org/api/custom/custom"
DS  = "male-cns:v1.0"

def ask(cypher, timeout=120):
    body = json.dumps({"cypher": cypher, "dataset": DS}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

print(ask("MATCH (n:Neuron) RETURN count(n)"))
# 期望形如 {"columns":["count(n)"],"data":[[176422]], ...}''', "python", "ping：确认能连上")}

    <div class="box warn">
      <div class="h">⚠️ 服务器会偶发 502 —— 这不是你的问题</div>
      <p>
        写这一页的时候，neuPrint 出现过一次<b>全线 502</b>（所有查询都失败，持续了一段时间）。
        遇到这种情况：
      </p>
      <p style="margin-bottom:0">
        ① <b>先确认是不是服务器的问题</b> —— 用浏览器打开
        <a href="https://neuprint.janelia.org/?dataset=male-cns%3Av1.0" target="_blank" rel="noopener">neuPrint 门户</a>，
        如果门户也打不开，那就是服务器侧；<br>
        ② <b>不要以为是自己的代码错了</b> 而开始乱改；<br>
        ③ 本页的<b>参考对照表是离线数据</b>，服务器挂了也能照着读。
      </p>
    </div>
  </section>

  <!-- ================= 02 这一步做什么 ================= -->
  <section id="what">
    <h2><span class="num">02</span>这一步到底在做什么<span class="en">1–2 天</span></h2>
    <p class="lead">
      一句话：<b>把阶段 1 用网页查到的数字，用代码重新算一遍，必须对得上。</b>
    </p>

    <div class="box">
      <div class="h">为什么非要"对得上"才算过关</div>
      <p style="margin-bottom:0">
        阶段 4 要跑仿真。仿真结果不对时，你必须能回答一个问题：
        <b>是建模错了，还是我连数据都读错了？</b>
        阶段 3 的作用就是把"读数"这一步先钉死 ——
        之后所有异常都可以归因到建模，而不用再怀疑数据管道。
      </p>
    </div>

    <h3>三件事，按顺序</h3>
    <div class="tw"><table>
      <thead><tr><th>#</th><th>做什么</th><th>产出</th></tr></thead>
      <tbody>
        <tr><td class="n">1</td><td>拿到连接数据</td>
            <td>一张 <code>(源, 目标, 突触数)</code> 的表，或一个稀疏矩阵</td></tr>
        <tr><td class="n">2</td><td>建稀疏矩阵、算入度/出度</td>
            <td>能对任意 bodyId 回答"它的上下游伙伴数与突触数"</td></tr>
        <tr><td class="n">3</td><td>复现阶段 1 的通路</td>
            <td>代码数字与网页实测值一致（见 <a href="#verify">§06</a>）</td></tr>
      </tbody>
    </table></div>

    <div class="box good">
      <div class="h">✅ 你可以完全不下载任何东西</div>
      <p style="margin-bottom:0">
        阶段 3 的过关标准<b>不需要</b>下载那 29 GB 的 flat-connectome。
        用匿名 API 就能把矩阵、度数、通路全部跑通。
        等你确定要做全图统计时，再下那 1.1 GB（只需 2 个文件）。
      </p>
    </div>
  </section>

  <!-- ================= 03 心智模型 ================= -->
  <section id="model">
    <h2><span class="num">03</span>心智模型：先分清四件事<span class="en">混了就会算错</span></h2>
    <p class="lead">
      这四组概念是阶段 2 读论文时反复出现的。动代码之前先确认自己能分清 ——
      否则数字对不上时你会不知道该怀疑哪一层。
    </p>

    <h3>① 度 ≠ 突触数</h3>
    <div class="tw"><table>
      <thead><tr><th>概念</th><th>含义</th><th>对应字段</th></tr></thead>
      <tbody>
        <tr><td><b>度</b>（degree）</td><td>连接的<b>伙伴个数</b></td>
            <td>矩阵一行的非零元个数</td></tr>
        <tr><td><b>突触数</b>（weight）</td><td>这条连接上有多少个突触</td>
            <td><code>r.weight</code> / 矩阵元素值</td></tr>
      </tbody>
    </table></div>
    <p>
      阶段 2 论文说"内禀神经元入度/出度中位数 ≈ <b>11 / 13</b>"，说的是<b>伙伴数</b>。
      而"DNg13 有 15,479 个下游"说的也是伙伴数，可它的 <code>pre</code> 是 2,127 个<b>突触</b>。
      <b>两个数不是一个量纲。</b>
    </p>

    <h3>② 接触 ≠ 连接</h3>
    <p>
      果蝇突触多为<b>多目标（polyadic）</b>：一个突触前位点对接多个突触后位点。
      FlyWire / MaleCNS 把它记成<b>多条突触</b>（每一条是一个"突触前–突触后位置对"）。
      所以：
    </p>
    <div class="formula">
<span class="cmt"># 直觉关系</span>
突触前位点数  ≤  突触（连接）数  =  突触前位点 × 平均对接靶点数
    </div>

    <h3>③ 阈值是<b>分析选择</b>，不是数据属性</h3>
    <p>
      同一份数据，换个阈值数字就变了。下面这张表是官方资料里的三套口径，
      <b>引用任何数字之前先确认是哪一套</b>：
    </p>
    <div class="tw"><table>
      <thead><tr><th>来源</th><th>阈值</th><th>规模</th><th>说明</th></tr></thead>
      <tbody>
        {census_rows()}
      </tbody>
    </table></div>

    <div class="box warn">
      <div class="h">⚠️ 这是本页最该记住的一条</div>
      <p style="margin-bottom:0">
        阶段 1 我记录的 <b>R1–R6 → L2 = 107,646</b> 是<b>未设阈值</b>的数。
        加上 ≥5 突触阈值之后变成 <b>107,572</b> ——
        <b>同一对连接，差 74 个突触</b>。
        数字本身没错，错的是"没写口径"。<a href="#verify">§06</a> 有在线对照可以自己验。
      </p>
    </div>

    <h3>④ 左右半球要显式拆分</h3>
    <p>
      跨中线的连接如果只记一条，就无法做"双侧一致性"检查 ——
      而双侧一致性正是判断"这个连接可不可信"的主要手段（阶段 2 的方法学核心）。
      拆分规则（来自论文方法部分）：
    </p>
    <div class="formula">
<span class="cmt"># 按源神经元的胞体侧拆分</span>
源有 somaSide        → 按 somaSide
源无侧（中线）        → 能取靶点侧就取靶点侧
源与靶都在中线        → 左右各分一半
感觉神经元           → 按其轴突进入神经系统的神经侧别（rootSide）
    </div>

    <h3>顺带把 DNg13 的输出看清楚</h3>
    <p>阶段 1 实测的 DNg13（bodyId 11074）输出分布 ——
      <b>下行神经元确实主要投向神经索</b>：</p>
    <div class="tw"><table>
      <thead><tr><th>目标超类</th><th>伙伴数</th><th>突触数</th><th>占比</th></tr></thead>
      <tbody>
        {dng13_rows()}
      </tbody>
    </table></div>
  </section>

  <!-- ================= 04 数据从哪来 ================= -->
  <section id="data">
    <h2><span class="num">04</span>数据从哪来<span class="en">三条路，按需选</span></h2>

    <div class="tw"><table>
      <thead><tr><th>路线</th><th>适合</th><th>代价</th><th>本页是否用</th></tr></thead>
      <tbody>
        <tr><td><b>匿名 API</b>（HTTP POST Cypher）</td>
            <td>先把逻辑跑通、复现通路</td>
            <td>需联网；重查询较慢</td>
            <td><span class="pill g">本页主线</span></td></tr>
        <tr><td><b>flat-connectome feather</b></td>
            <td>全图统计、要速度</td>
            <td>见下（下载量不小）</td>
            <td><span class="pill a">需要时再下</span></td></tr>
        <tr><td><b>connectome_data_prep</b></td>
            <td>直接拿现成的稀疏矩阵</td>
            <td>依赖第三方项目</td>
            <td><span class="pill b">备选</span></td></tr>
      </tbody>
    </table></div>

    <h3>想下载的话：只需要 2 个文件</h3>
    <div class="box warn">
      <div class="h">⚠️ 学习指南在这里有个数字错误（阶段 0 已修正）</div>
      <p>
        指南写"三个 feather 文件、约 1.1 GB"。
        官方 flat-connectome 目录下实际是 <b>11 个文件、合计约 29 GB</b>
        （2026-09-20 按官方 bucket 清单核对），
        <b>1.1 GB 只是其中"连接矩阵"那一个文件</b>。
      </p>
      <p style="margin-bottom:0">
        但好消息是：<b>只建连接矩阵的话，2 个文件就够</b>（约 1.1 GB）。
      </p>
    </div>

    <div class="box good">
      <div class="h">✅ 别照下面这段手写 —— 仓库里有现成的工具</div>
      <p style="margin-bottom:0">
        <code>python tools/fetch_flat_connectome.py</code>：<b>带断点续传</b>（1 GB 下到
        90% 断掉不用重来），下完自动用官方 MD5 校验，
        默认落到 <code>_data/</code>（已在 <code>.gitignore</code> 里，不会被 git 收走）。
        加 <code>--list</code> 看全部 11 个文件，<code>--verify</code> 只校验不下载。
        下面这段是它的最小内核，看懂就行。
      </p>
    </div>

    {code('''# 只需要这两个（约 1.1 GB）：
#   body-annotations     细胞注释（superclass / type / instance …）
#   connectome-weights   连接三元组（源 bodyId、目标 bodyId、突触数）
#
# 前缀：
#   https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/
#
# ⚠️ 这段是最小演示，没有续传、没有校验。
#    真要下载请用：python tools/fetch_flat_connectome.py

BASE = ("https://storage.googleapis.com/flyem-male-cns/v1.0/"
        "connectome-data/flat-connectome/")

FILES = [
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
]

# 注意文件名里的 minconf-0.5 —— 这就是阶段 2 过关标准里的
# 「min confidence 0.5」，它是内嵌在文件名里的口径。

# 落到 _data/：.gitignore 里已经排除，避免 1 GB 文件被 git 收进去。
DATA = "_data"

import os, urllib.request
os.makedirs(DATA, exist_ok=True)
for f in FILES:
    dst = os.path.join(DATA, f)
    if os.path.exists(dst):
        print("已有", f); continue
    print("下载", f, "…")
    urllib.request.urlretrieve(BASE + f, dst)
    print("  完成", round(os.path.getsize(dst)/1e6, 1), "MB")''', "python", "下载（可选）")}

    <div class="box">
      <div class="h">读 feather 只要三行</div>
      <p style="margin-bottom:0">
        <code>pyarrow</code> 或 <code>pandas</code> 都能直接读。列名可以在下载后
        <code>print(df.columns)</code> 看一下再写代码 —— <b>不要凭记忆写列名</b>，
        这是阶段 3 的坑之一。
      </p>
    </div>
  </section>

  <!-- ================= 05 代码 ================= -->
  <section id="cook">
    <h2><span class="num">05</span>照着敲：六段代码<span class="en">每段都能单独跑</span></h2>
    <p class="lead">
      下面六段是<b>本页实际测试过</b>的代码（从 <code>tools/p3_lib.py</code> 里切出来的，
      不是手抄的）。建议顺序执行，每段跑完看一眼输出。
    </p>

    <h3 id="cook1">第 1 段 · 最小可用的 API 客户端</h3>
    <p>一个类就够。<b>注意重试逻辑</b> —— 服务器会偶发 502。</p>
    {code(MIN_CLIENT, "python", "api_client.py")}

    <h3 id="cook2">第 2 段 · 取连接三元组</h3>
    <p>
      核心是把 <code>(源, 目标, 突触数)</code> 取出来。
      <b>阈值写成参数</b>，这样每次调用都提醒自己用的是哪一套。
    </p>
    {code(BLOCK_MATRIX, "python", "edges.py")}

    <h3 id="cook3">第 3 段 · 建稀疏矩阵 + 算度数</h3>
    <div class="box warn">
      <div class="h">⚠️ 最容易错的一步：bodyId 不能直接当矩阵下标</div>
      <p style="margin-bottom:0">
        bodyId 长这样：<code>11074</code>、<code>512006</code>、<code>7205759406…</code>。
        它们<b>不是从 0 开始的连续整数</b>。
        直接拿来当小标，矩阵边长会被最大 ID 撑到几十万甚至上亿，
        而实际只有十几万神经元 —— 内存白烧、还容易越界。
        <b>先建 bodyId → 0..N-1 的映射。</b>
      </p>
    </div>
    {code(BLOCK_DEGREES, "python", "matrix.py")}

    <h3 id="cook4">第 4 段 · 通路查询</h3>
    <p>把"谁连谁、连多少"写成可复用函数。这三个函数对应阶段 1 手工查的那三件事。</p>
    {code(BLOCK_PATH, "python", "pathways.py")}

    <h3 id="cook5">第 5 段 · 阈值对照（本页的核心实验）</h3>
    <p>
      同一对神经元，跑两次不同阈值，看差多少。
      <b>这个实验做完，你就不会再忘记写口径了。</b>
    </p>
    {code(MIN_RUN, "python", "threshold_check.py")}

    <h3 id="cook6">第 6 段 · 完整对照脚本</h3>
    <p>
      把上面拼起来，自动跑完 <a href="#verify">§06</a> 的全部对照项并打分。
      本仓库里已经有现成的：<code>tools/test_p3.py</code>。
    </p>
    {code('''# 在仓库根目录跑（需要联网）
py -3 tools/test_p3.py

# 只跑离线部分（不需要联网，验证矩阵逻辑）
py -3 tools/test_p3.py --offline

# 另一个可用工具：阶段 1 的执行台（浏览器里直接跑查询，不用写代码）
#   neuprint.html''', "bash", "运行对照测试")}
  </section>

  <!-- ================= 06 对照表 ================= -->
  <section id="verify">
    <h2><span class="num">06</span>对照表：你的输出 vs 实测值<span class="en">过关就看这张表</span></h2>
    <p class="lead">
      左边是阶段 1 在 neuPrint 上实测的值（<b>离线固化，服务器挂了也能读</b>），
      右边是查它用的 Cypher。你的代码算出来的数应该对得上。
    </p>

    <div class="tw"><table>
      <thead><tr><th style="min-width:250px">检查项</th>
        <th style="width:180px">实测值 / 口径</th><th>查询语句</th></tr></thead>
      <tbody>
        {ref_rows()}
      </tbody>
    </table></div>

    <div class="box good">
      <div class="h">✅ 原来标着「待核实」的三项，2026-09-20 结案了</div>
      <p>
        <code>L2 → Tm2</code> 阶段 1 记录为 <b>221,186</b>，
        后来重测得到 <b>219,357</b>，当时以为数据集变过，标成了「待核实」。
        用官方 flat-connectome（minconf-0.5）逐项复核后：<b>两个数都精确复现</b> ——
        221,186 是<b>未设阈值</b>口径，219,357 是 <b>≥5</b> 口径
        （差 1,829，正好是被砍掉的那批弱边）。
      </p>
      <p>
        <code>L2 → Tm1</code>（205,428 / ≥5 205,004）、<code>Tm2 → T5c</code>
        （61,901 / ≥5 51,892）同理。所以<b>两个数都对，错的是当时没写口径</b>。
        表里现在把两个口径并排列出。
      </p>
      <p style="margin-bottom:0">
        仍然是阶段 2 那条态度：数字对不上时，<b>先怀疑口径，再怀疑数据</b>；
        真查不出来就标出来，不要硬凑。
      </p>
    </div>

    <h3>自己填一遍（离线比对，不需要联网）</h3>
    <p>把你代码算出来的数填进去，页面会告诉你对不对。容差按各项的量级设定。</p>
    <div class="verifier" id="verifier">
      <div id="vrows"></div>
      <div class="vsum" id="vsum">还没有输入。</div>
      <div style="margin-top:12px">
        <button class="copybtn" id="vclear" type="button">清空</button>
      </div>
    </div>
  </section>

  <!-- ================= 07 坑 ================= -->
  <section id="pitfalls">
    <h2><span class="num">07</span>四个必踩的坑<span class="en">每条都配排查方法</span></h2>

    <div class="tw"><table>
      <thead><tr><th style="width:150px">坑</th><th>现象</th><th style="width:280px">排查</th></tr></thead>
      <tbody>
        <tr>
          <td><b>字段名</b></td>
          <td>类型字段是 <code>type</code>，<b>不是</b> <code>cellType</code>。
              写错<b>不报错</b>，只返回 0 行 —— 你会以为"这个类型不存在"。</td>
          <td>先跑 <code>MATCH (n:Neuron) RETURN keys(n) LIMIT 1</code> 看真实字段名。
              本页测试里专门有一条断言"写错字段返回 0 行"。</td>
        </tr>
        <tr>
          <td><b>口径混用</b></td>
          <td>同一份数据不同阈值下规模差 4 倍（2,556 万 vs 624 万）。
              两个来源的数字放在一起比，结论就废了。</td>
          <td>每个数字后面都写清阈值。看到别人的数字先问"什么口径"。</td>
        </tr>
        <tr>
          <td><b>把 bodyId 当稳定标识</b></td>
          <td>跨版本 / 跨数据集对不上。bodyId 在不同 materialization 版本里可能变。</td>
          <td>长期项目用 <code>type</code> + 形态做锚点，
              或用 <code>flywireType</code> / <code>mancType</code> 做类型级对应。</td>
        </tr>
        <tr>
          <td><b>弱边不可靠</b></td>
          <td>一个半球里 60% 的<b>单突触</b>连接，在另一个半球完全不存在。</td>
          <td>统计前先设阈值。要让一条同型边有 90% 概率在另一数据集也出现，
              它需要 <b>&gt;10 个突触</b>。</td>
        </tr>
        <tr>
          <td><b>服务器 502</b></td>
          <td>所有查询同时失败，报 502 Bad Gateway。</td>
          <td>用浏览器开 neuPrint 门户确认是服务器侧。别改代码，等一会儿重试。</td>
        </tr>
      </tbody>
    </table></div>
  </section>

  <!-- ================= 08 自检 ================= -->
  <section id="checkpoint">
    <h2><span class="num">08</span>过关自检<span class="en">做完这些就算过</span></h2>
    <div class="check" id="check">
      <div class="item"><div class="bx"></div><div>
        <div class="q">环境三件套都能过（Python / requests / 能连上 neuPrint）</div>
        <div class="a">跑 §01 的两段代码即可。服务器 502 时先确认不是你这边的问题。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">能说出"度"和"突触数"的区别，并各举一个 MaleCNS 的例子</div>
        <div class="a">度 = 伙伴个数；突触数 = 那条连接上的突触。
          DNg13 的 <code>downstream = 15,479</code> 是伙伴数，<code>pre = 2,127</code> 是突触数。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">能解释为什么 bodyId 不能直接当矩阵下标</div>
        <div class="a">bodyId 不是从 0 开始的连续整数，直接用会把矩阵撑大几个数量级。
          要先建 bodyId → 0..N-1 的映射。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">代码算出的 <code>R1–R6 → L2</code> 与实测值一致（未设阈值口径下 107,646）</div>
        <div class="a">容差按量级取。对不上时先检查是不是用了 ≥5 阈值（那会得到 107,572）。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">能出示"同一对连接换阈值"的两次输出</div>
        <div class="a">这是本页第 5 段代码。做完你就有了"口径意识"的实证。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">能复现 DNg13 身份卡：bodyId / superclass / 递质 / pre / post</div>
        <div class="a">11074 · descending_neuron · acetylcholine · 2,127 · 6,500。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">能复现通路 B 的第一跳：BM_Taste → GNG015</div>
        <div class="a">并说明为什么全库只有一个类型含 'Taste'。</div>
      </div></div>
      <div class="item"><div class="bx"></div><div>
        <div class="q">做全图统计前，能说明自己用的是哪一套口径</div>
        <div class="a">三套：neuPrint 默认 ≥5 突触 / 下载文件 minconf-0.5 / 未设阈值。</div>
      </div></div>
      <div class="hint">勾选后展开答案。这里没有提交按钮 —— 过关标准是"你自己知道对得上"。</div>
    </div>
  </section>

  <!-- ================= 09 参考 ================= -->
  <section id="refs">
    <h2><span class="num">09</span>参考与延伸<span class="en">Links</span></h2>
    <div class="tw"><table>
      <thead><tr><th style="width:230px">资源</th><th>说明</th></tr></thead>
      <tbody>
        <tr><td><a href="https://neuprint.janelia.org/?dataset=male-cns%3Av1.0" target="_blank" rel="noopener">neuPrint 官方门户</a></td>
            <td>本页所有查询的源头。<b>服务器状态也可以在这里确认</b></td></tr>
        <tr><td><a href="neuprint.html">neuPrint 执行台（本站）</a></td>
            <td>不想写代码时，在浏览器里直接跑同样的查询</td></tr>
        <tr><td><a href="phase1.html#pathA">阶段 1 · 通路 A</a></td>
            <td>本页复现的通路，那里有逐跳的查询与实测权重</td></tr>
        <tr><td><a href="phase2.html">阶段 2 · 读论文</a></td>
            <td>本页所有"口径"结论的出处（尤其 Methods 的 Connection threshold）</td></tr>
        <tr><td><a href="https://github.com/flyconnectome/2025malecns" target="_blank" rel="noopener">2025malecns</a></td>
            <td>Berg 论文配套 notebook —— 目前最接近"官方教程"的东西</td></tr>
        <tr><td><a href="https://connectome-neuprint.github.io/neuprint-python/" target="_blank" rel="noopener">neuprint-python</a></td>
            <td>官方 Python 客户端。本页刻意没用它（少一个依赖），
                但正式项目建议上</td></tr>
        <tr><td><a href="https://github.com/YijieYin/connectome_data_prep" target="_blank" rel="noopener">connectome_data_prep</a></td>
            <td>直接拿现成的稀疏矩阵（MaleCNS / BANC / FlyWire / hemibrain）</td></tr>
        <tr><td><a href="https://github.com/YijieYin/connectome_interpreter" target="_blank" rel="noopener">connectome_interpreter</a></td>
            <td>有效连接、寻路、回路操作 —— 阶段 4 会用</td></tr>
      </tbody>
    </table></div>

    <footer>
      <nav class="phaseswitch foot" aria-label="阶段切换">
        <a href="index.html">总览</a>
        <a href="phase0.html">阶段 0</a>
        <a href="phase1.html">阶段 1</a>
        <a href="phase2.html">阶段 2</a>
        <span class="on">阶段 3 · 写代码</span>
        <a href="neuprint.html">执行台</a>
      </nav>
      <p style="margin-bottom:0">
        <b>MaleCNS 学习指南 · 阶段 3 配套材料</b> ——
        本页代码在 <code>tools/p3_lib.py</code>，对照测试在 <code>tools/test_p3.py</code>，
        参考值在 <code>tools/p3_reference.py</code>。
        实测日期见 §06 表格。引用数据须注明 Berg et al. (2026)
        及 FlyEM / HHMI Janelia 等来源。
      </p>
    </footer>
  </section>

  </main>
</div>

<pre id="refdata" style="display:none">{esc(ref_json())}</pre>

<script>
(function () {{
  'use strict';

  /* ---------- 代码复制 ---------- */
  document.querySelectorAll('.codewrap').forEach(function (w) {{
    var pre = w.querySelector('pre.cp');
    if (!pre) return;
    var head = w.querySelector('.codeh');
    if (!head) {{ head = document.createElement('div'); head.className = 'codeh';
      w.insertBefore(head, pre); }}
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'copybtn'; btn.textContent = '复制';
    btn.addEventListener('click', function () {{
      var t = pre.textContent;
      var done = function () {{
        btn.textContent = '已复制'; btn.classList.add('ok');
        setTimeout(function () {{ btn.textContent = '复制'; btn.classList.remove('ok'); }}, 1400);
      }};
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(t).then(done, function () {{ pick(); }});
      }} else {{ pick(); }}
      function pick() {{
        var r = document.createRange(); r.selectNodeContents(pre);
        var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        btn.textContent = '已选中，按 Ctrl+C';
      }}
    }});
    head.appendChild(btn);
  }});

  /* ---------- 目录高亮 ---------- */
  var links = Array.prototype.slice.call(document.querySelectorAll('nav.toc a'));
  var secs = links.map(function (a) {{
    return document.getElementById((a.getAttribute('href') || '').slice(1));
  }});
  function onScroll() {{
    var active = -1;
    for (var i = 0; i < secs.length; i++) {{
      if (secs[i] && secs[i].getBoundingClientRect().top <= 120) active = i; else break;
    }}
    links.forEach(function (a, i) {{ a.classList.toggle('on', i === active); }});
  }}
  var raf = null;
  window.addEventListener('scroll', function () {{
    if (raf) return;
    raf = requestAnimationFrame(function () {{ raf = null; onScroll(); }});
  }}, {{ passive: true }});
  onScroll();

  /* ---------- 自检勾选 ---------- */
  document.querySelectorAll('#check .item').forEach(function (it) {{
    it.addEventListener('click', function () {{ it.classList.toggle('done'); }});
  }});

  /* ---------- 离线比对器 ---------- */
  var DATA = JSON.parse(document.getElementById('refdata').textContent);
  var rows = document.getElementById('vrows');
  var sum = document.getElementById('vsum');
  var inputs = [];

  function fmtNum(n) {{ return Number(n).toLocaleString(); }}

  function render() {{
    DATA.forEach(function (d) {{
      var r = document.createElement('div');
      r.className = 'vrow';
      var lab = document.createElement('div');
      lab.className = 'lab';
      lab.innerHTML = d.label +
        (d.tol ? ' <span style="color:var(--dim);font-size:12px">（容差 ±' +
                 fmtNum(d.tol) + '）</span>' : '');
      var inp = document.createElement('input');
      inp.type = 'text'; inp.inputMode = 'numeric';
      inp.placeholder = '你的结果';
      var val = document.createElement('div');
      val.className = 'val'; val.textContent = '实测 ' + fmtNum(d.value);
      var res = document.createElement('div');
      res.className = 'res';
      inp.addEventListener('input', check);
      r.appendChild(lab); r.appendChild(inp); r.appendChild(val); r.appendChild(res);
      rows.appendChild(r);
      inputs.push({{ el: inp, row: r, res: res, d: d }});
    }});
  }}

  function check() {{
    var okN = 0, badN = 0, closeN = 0, filled = 0;
    inputs.forEach(function (it) {{
      var raw = it.el.value.replace(/[,\\s_]/g, '');
      it.row.classList.remove('ok', 'bad', 'close');
      it.res.textContent = '';
      if (!raw) return;
      filled++;
      var n = Number(raw);
      if (!isFinite(n)) {{ it.res.textContent = '不是数字'; it.row.classList.add('bad'); badN++; return; }}
      var diff = Math.abs(n - it.d.value);
      if (diff === 0) {{ it.res.textContent = '✓ 完全一致'; it.row.classList.add('ok'); okN++; }}
      else if (diff <= it.d.tol) {{ it.res.textContent = '✓ 在容差内 (差 ' + fmtNum(diff) + ')';
        it.row.classList.add('ok'); okN++; }}
      else if (diff <= it.d.tol * 3 + 1) {{ it.res.textContent = '≈ 接近 (差 ' + fmtNum(diff) + ')';
        it.row.classList.add('close'); closeN++; }}
      else {{ it.res.textContent = '✗ 差 ' + fmtNum(diff); it.row.classList.add('bad'); badN++; }}
    }});
    if (!filled) {{ sum.textContent = '还没有输入。'; return; }}
    var verdict = badN === 0
      ? (closeN === 0 ? '全部通过 ✓' : '基本通过（有 ' + closeN + ' 项接近）')
      : '有 ' + badN + ' 项对不上 —— 先检查阈值口径';
    sum.innerHTML = '已填 <b>' + filled + '/' + inputs.length + '</b> 项：' +
      '一致 <b>' + okN + '</b>，接近 <b>' + closeN + '</b>，不符 <b>' + badN + '</b> —— ' +
      '<b>' + verdict + '</b>';
  }}

  render();
  document.getElementById('vclear').addEventListener('click', function () {{
    inputs.forEach(function (it) {{ it.el.value = ''; }});
    check();
  }});
}})();
</script>
</body>
</html>
"""


def main() -> None:
    html_out = build()
    with open(DST, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"已写出 {DST}  （{len(html_out)/1024:.1f} KB）")
    print(f"  参考值 {len(REF.CHECKS)} 项 / {len(REF.by_group())} 组")
    # 不要把这个表达式写进 f-string：3.11 及以下不允许表达式里出现反斜杠，
    # 会直接 SyntaxError（README 里写的是 py -3，很多机器还是 3.9/3.10）。
    n_code = len(re.findall(r'class="codewrap"', html_out))
    print(f"  嵌入代码段 {n_code} 个")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
