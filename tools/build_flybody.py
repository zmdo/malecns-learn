"""
build_flybody.py — 生成 flybody.html（官方蝇体模型 + MaleCNS 具身演示页）。

为什么要生成而不是手写：
  页面得沿用阶段 1 的整套设计系统（.wrap / .box / .tw / .pill …）。
  手抄一份 CSS 迟早会和 phase1.html 走样 —— 阶段 3 就出过一次
  「按标记切 CSS 切早了、整个页面掉样式」的事故。
  这里直接把 phase1.html 的 <style> 整块搬过来。

用法：
    python tools/build_flybody.py
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "flybody.html")


def style_of(path: str) -> str:
    """取某页 <style> 块的全部内容（理由见上）。"""
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    m = re.search(r"<style>([\s\S]*?)</style>", src)
    if not m:
        raise SystemExit(f"在 {path} 里找不到 <style> 块")
    return m.group(1).strip("\n")


PAGE_CSS = """
  /* ---------- 本页新增组件 ---------- */
  .grid2{display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:16px; margin:20px 0}
  .card{background:var(--panel); border:1px solid var(--line); border-radius:13px; padding:16px 18px}
  .card h4{margin:0 0 8px; font-size:15.5px; color:var(--ink)}
  .card p{font-size:13.6px; color:var(--ink3); margin:0 0 8px; line-height:1.65}
  .card p:last-child{margin-bottom:0}
  .card .src{font-family:var(--mono); font-size:11.5px; color:var(--dim); word-break:break-all}
  .vid{background:#0b1424; border:1px solid #223052; border-radius:13px; padding:10px; margin:18px 0}
  .vid video{width:100%; display:block; border-radius:9px; background:#000}
  .vid .cap{font-size:13px; color:var(--ink3); padding:10px 6px 4px; line-height:1.6}
  .vid .cap b{color:var(--ink)}
  .vid .cap .tagline{font-family:var(--mono); font-size:11.5px; color:var(--amber)}
  .cred{font-size:12.6px; color:var(--dim); border-top:1px solid var(--line); margin-top:14px; padding-top:12px}
  .kbdline{font-family:var(--mono); font-size:12.4px; color:var(--ink3)}
"""


def build() -> str:
    css = style_of("phase1.html")
    html = TEMPLATE.replace("/*__CSS__*/", css + PAGE_CSS)
    return html


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>蝇体 + 大脑演示 | MaleCNS 学习指南</title>
<style>
/*__CSS__*/
  nav.toc a{display:block; padding:6px 10px; border-radius:8px; color:var(--ink3);
    font-size:14px; border-left:2px solid transparent; margin-bottom:2px}
  nav.toc a:hover{background:#131c33; color:var(--ink); text-decoration:none}
  nav.toc a.on{color:var(--green); border-left-color:var(--green); background:#0d1a12}
  nav.toc .th{font-size:11.5px; letter-spacing:.12em; text-transform:uppercase;
    color:var(--dim); margin:16px 0 8px; padding-left:10px}
</style>
</head>
<body>

<header class="bar">
  <nav class="phaseswitch" aria-label="阶段切换">
    <a href="index.html">总览</a>
    <a href="phase0.html">阶段 0</a>
    <a href="phase1.html">阶段 1</a>
    <a href="phase2.html">阶段 2</a>
    <a href="phase3.html">阶段 3</a>
    <a href="neuprint.html">执行台</a>
  </nav>
  <span class="t">蝇体 + 大脑演示</span>
  <span class="sp"></span>
  <span class="meta">flybody + MaleCNS · MuJoCo</span>
</header>

<div class="wrap">
  <nav class="toc">
    <div class="th">本页目录</div>
    <a href="#what">01 · 这是什么</a>
    <a href="#assets">02 · 两块官方拼图</a>
    <a href="#inside">03 · 脑在身体里的位置</a>
    <a href="#demo">04 · 演示视频</a>
    <a href="#numbers">05 · 实测数字</a>
    <a href="#repro">06 · 怎么复现</a>
    <a href="#honest">07 · 哪些是测量、哪些是假设</a>
    <a href="#related">08 · 相关项目</a>
  </nav>

  <main>

  <!-- ================= 01 ================= -->
  <section id="what">
    <h2><span class="num">01</span>这是什么<span class="en">官方蝇体 + 官方大脑，跑起来</span></h2>
    <p class="lead">
      前面几个阶段你一直在<strong>看数据</strong>。这一页把它<strong>接上身体</strong>：
      用官方的解剖级蝇体模型当身体，用 MaleCNS 的
      <strong>166,700 个神经元 / 25,582,938 条连接</strong>当脑，
      在 MuJoCo 里真的跑起来 —— 脑发脉冲，身体走路。
    </p>

    <div class="box good">
      <div class="h">✅ 两个部件都是官方的，而且出自同一家研究所</div>
      <p style="margin-bottom:0">
        <b>身体</b>：<code>flybody</code>，由 <strong>Google DeepMind 与 HHMI Janelia</strong> 合作开发，
        收录在 DeepMind 官方的 MuJoCo Menagerie 里（Apache-2.0）。<br>
        <b>脑</b>：<strong>MaleCNS v1.0</strong>，HHMI Janelia FlyEM 发布（CC-BY 4.0）。<br>
        所以这套组合不需要你自己拼凑：躯壳和脑来自同一个实验室体系，许可也都允许再发布。
      </p>
    </div>

    <p>
      两点必须说在前面：<b>身体模型与脑不是同一只果蝇</b>（一个是建模资产，一个是另一个体的重建），
      而且<b>把脑装进身体这件事本身是工程实现，不是数据</b>。
      第 <a href="#honest">07 节</a>会把这条界线画清楚。
    </p>
  </section>

  <!-- ================= 02 ================= -->
  <section id="assets">
    <h2><span class="num">02</span>两块官方拼图<span class="en">The two official parts</span></h2>

    <div class="grid2">
      <div class="card">
        <h4>🪰 身体 · flybody</h4>
        <p>解剖级果蝇全身模型：头、胸、腹、两对翅、平衡棒、三对足（含跗节与爪）、
           喙与触角，共 <b>68 个刚体 / 85 个网格</b>，总质量约 <b>0.98 mg</b>（模型尺度）。</p>
        <p>开发：<b>Google DeepMind × HHMI Janelia</b>；经授权收录进 MuJoCo Menagerie，
           与 Turaga Lab 官方仓库同一 commit。</p>
        <p class="src">许可 Apache-2.0 · Menagerie/flybody</p>
      </div>
      <div class="card">
        <h4>🧠 大脑 · MaleCNS v1.0</h4>
        <p>成年雄性果蝇完整中枢神经系统：中央脑 + 视叶 + 腹神经索。
           本页用的是你已经在第 3 阶段下载并校验过的同一份文件。</p>
        <p>发育：<b>HHMI Janelia FlyEM</b> 等；<b>166,700 个神经元</b>、
           <b>25,582,938 条有向连接</b>（两端都是神经元、未设阈值口径）。</p>
        <p class="src">许可 CC-BY 4.0 · Berg et al. (2026) Cell 189(18):5504-5526.e15</p>
      </div>
    </div>

    <div class="box">
      <div class="h">两个数字对得上，说明拼装没出错</div>
      <p style="margin-bottom:0">
        第三方项目 <code>fly-arena</code> 自己重新解了一遍那两个 feather 文件
        （用 <strong>SHA-256</strong>，和我们当初用官方 MD5 的校验相互独立），
        建出的图是 <b>166,700 个神经元 / 25,582,938 条边</b> ——
        与我们在阶段 3 用官方文件数出来的完全一致。
      </p>
    </div>
  </section>

  <!-- ================= 03 ================= -->
  <section id="inside">
    <h2><span class="num">03</span>脑在身体里的位置<span class="en">Where the CNS sits</span></h2>
    <p class="lead">
      把 MaleCNS 的神经毡网格按解剖比例缩放进官方蝇体，身体调成半透明 ——
      这样能直接看到中枢神经系统在体内的位置。
    </p>

    <figure>
      <img src="assets/demo/cns-in-body.png" alt="MaleCNS 中枢神经系统置于官方蝇体模型内部">
      <figcaption>
        <b>彩色为中枢神经系统</b>：<span style="color:#4de3ff">青</span>=中央脑、
        <span style="color:#8cf27a">绿</span>=视叶、
        <span style="color:#ffd84d">黄</span>=食管下区（SEZ）、
        <span style="color:#ff7abf">粉</span>=腹神经索（VNC）。
        脑在头内、VNC 向后延伸入胸 —— 与真实解剖结构一致。
      </figcaption>
    </figure>

    <div class="box warn">
      <div class="h">⚠️ 这是示意图，不是解剖配准</div>
      <p style="margin-bottom:0">
        两部分来自<b>不同个体、不同坐标系</b>（MaleCNS 是纳米级 EM 重建坐标，
        flybody 是设计坐标系），所以这里是按「体长比例」摆放的，<b>不是</b>把两个坐标系配准。
        可以据此讲清拓扑关系（脑在头、VNC 入胸），<b>不能</b>用来量任何距离。
      </p>
    </div>
  </section>

  <!-- ================= 04 ================= -->
  <section id="demo">
    <h2><span class="num">04</span>演示视频<span class="en">Two runs, one control</span></h2>
    <p class="lead">
      同一个身体跑两遍：一遍<strong>不接脑</strong>（脚本控制，作为对照），
      一遍<strong>接上 MaleCNS</strong>。对比着看，才知道画面里的动作到底是谁产生的。
    </p>

    <div class="vid">
      <video controls loop muted playsinline preload="metadata" poster="assets/demo/poster-body.png">
        <source src="assets/demo/fly-body-demo.mp4" type="video/mp4">
        你的浏览器不支持内嵌视频。
      </video>
      <div class="cap">
        <span class="tagline">对照 · 无连接组</span><br>
        <b>脚本控制</b>：预先编好的步态程序直接驱动六条腿，脑<strong>没有参与</strong>。
        左上为竞技场俯视，右上为蝇体近景，右下为左右复眼的模拟视野，
        叠加层显示时间、脉冲数（这里恒为 0）与步态指令。
      </div>
    </div>

    <div class="vid">
      <video controls loop muted playsinline preload="metadata" poster="assets/demo/poster-connectome.png">
        <source src="assets/demo/fly-connectome.mp4" type="video/mp4">
        你的浏览器不支持内嵌视频。
      </video>
      <div class="cap">
        <span class="tagline">接上 MaleCNS</span><br>
        <b>166,700 个神经元在跑</b>：复眼的模拟输入送进视叶，全脑 LIF 以 0.1 ms 步长积分，
        下行神经元（DNp09 / DNa02）的放电率解码成前进与转向指令，交给身体执行。
        叠加层里的 <b>spikes / 10 ms</b> 是这一步的脉冲总数。
      </div>
    </div>

    <div class="box">
      <div class="h">🔍 该看什么</div>
      <p style="margin-bottom:0">
        两段视频里蝇子的<strong>步态是同一位「工程师」写的</strong>（六足协调的 CPG 程序），
        脑改变的是<strong>速度与转向</strong>。所以要看的不是「腿抬得像不像」——
        那是身体模型与步态程序的功劳；要看的是<b>转向是否由神经活动驱动</b>。
        这也正是第 07 节要划清的界线。
      </p>
    </div>
  </section>

  <!-- ================= 05 ================= -->
  <section id="numbers">
    <h2><span class="num">05</span>实测数字<span class="en">What actually ran</span></h2>
    <p class="lead">下面每个数都是本机跑出来的，不是估计值。</p>

    <div class="stats">
      <div class="stat"><div class="v">166,700</div><div class="l">参与仿真的神经元</div></div>
      <div class="stat"><div class="v">25.58M</div><div class="l">有向连接（边）</div></div>
      <div class="stat g"><div class="v">4,943,604</div><div class="l">6 秒仿真里的脉冲总数</div></div>
      <div class="stat a"><div class="v">4.06 mm/s</div><div class="l">接脑后的平均前进速度</div></div>
    </div>

    <div class="tw"><table>
      <thead><tr><th>运行</th><th>仿真时长</th><th>墙钟耗时</th><th>脉冲</th><th>位移</th><th>视频帧</th></tr></thead>
      <tbody>
        <tr><td>脚本控制（对照）</td><td class="n">4.0 s</td><td class="n">11.4 s</td>
            <td class="n">0</td><td class="n">13.6 mm</td><td class="n">121</td></tr>
        <tr><td><b>接 MaleCNS</b></td><td class="n">6.0 s</td><td class="n">19.0 s</td>
            <td class="n">4,943,604</td><td class="n">24.4 mm</td><td class="n">181</td></tr>
      </tbody>
    </table></div>

    <div class="formula">
<span class="cmt"># 仿真速度（本机，单进程 CPU）</span>
接脑： 6.0 s 生物时间 / 19.0 s 墙钟  = <span class="hl">0.32 × 实时</span>
对照： 4.0 s 生物时间 / 11.4 s 墙钟  = <span class="hl">0.35 × 实时</span>
<span class="cmt"># 也就是说：这个规模的全脑 + 身体，目前比实时慢约 3 倍</span>
    </div>

    <p>
      <b>怎么理解这个速度</b>：全脑 LIF 每 0.1 ms 积一次，166,700 个神经元、
      2,558 万条边，全部在 CPU 上。参考<a href="malecns-study-guide.md">学习指南</a>里的
      独立复现：脑 + 身体跑 5 秒蝇时间约需 64 秒 —— 与这里的量级一致。
    </p>
  </section>

  <!-- ================= 06 ================= -->
  <section id="repro">
    <h2><span class="num">06</span>怎么复现<span class="en">Reproduce it</span></h2>
    <p class="lead">
      身体模型与仿真框架来自两个第三方项目，本页只负责把 MaleCNS 接上去。
      下面是完整链路。
    </p>

    <h3>① 拿身体模型（官方）</h3>
    <pre><span class="c"># DeepMind MuJoCo Menagerie：只取 flybody，约 134 MB</span>
git clone --depth 1 --filter=blob:none --sparse \\
  https://github.com/google-deepmind/mujoco_menagerie.git
cd mujoco_menagerie &amp;&amp; git sparse-checkout set flybody</pre>

    <h3>② 拿脑（就是第 3 阶段那两个文件）</h3>
    <pre><span class="c"># 复用已下载并校验过的 feather，另加一个 43 MB 的递质文件</span>
python tools/fetch_flat_connectome.py</pre>

    <h3>③ 用 fly-arena 把两者接起来</h3>
    <pre><span class="c"># MIT 许可的实验性项目：NeuroMechFly 身体 + MaleCNS + 行为控制器</span>
pip install -e fly-arena

<span class="c"># --raw 指向你已有的 feather 目录，避免重复下载 1.1 GB（它会用 SHA-256 重新校验）</span>
python -m fly_arena prepare --data arena-data --raw _data

<span class="c"># 对照：只有身体，没有脑</span>
python -m fly_arena run --mode body-demo --headless \\
  --video body-demo.mp4 --seconds 4

<span class="c"># 接上 MaleCNS：166,700 个神经元真的在跑</span>
python -m fly_arena run --mode connectome --headless --data arena-data \\
  --video connectome.mp4 --seconds 6</pre>

    <div class="box">
      <div class="h">环境要求</div>
      <p style="margin-bottom:0">
        Python <b>3.12</b>、MuJoCo、Numba。渲染用离屏模式即可（macOS 用 <code>MUJOCO_GL=cgl</code>，
        Linux 无显示器用 <code>egl</code>）——<b>不需要图形界面</b>，所以服务器上也能出视频。
        本机为 Apple Silicon，两个 venv 加起来约 700 MB。
      </p>
    </div>
  </section>

  <!-- ================= 07 ================= -->
  <section id="honest">
    <h2><span class="num">07</span>哪些是测量、哪些是假设<span class="en">Measured vs engineered</span></h2>
    <p class="lead">
      这是整个学习指南反复强调的纪律。看这段演示时，请把下面两栏分清楚。
    </p>

    <div class="grid2">
      <div class="card">
        <h4>✅ 来自真实数据的</h4>
        <p>• 神经元数量、连接、突触数：直接读官方 v1.0 文件，<b>已用 SHA-256/MD5 双重校验</b></p>
        <p>• 突触符号：由预测递质映射（GABA / 谷氨酸 / 组胺 → 抑制性，其余 → 兴奋性代理）</p>
        <p>• 复眼输入的空间映射：按视叶的解剖连接近似</p>
        <p>• 身体形态与质量分布：来自解剖测量</p>
      </div>
      <div class="card">
        <h4>⚠️ 工程假设（不是数据）</h4>
        <p>• <b>LIF 参数</b>：膜时间常数、阈值、突触增益均为选定值</p>
        <p>• <b>递质符号</b>：受体层面的兴奋/抑制差异、神经调质<strong>完全没建模</strong>；
           MaleCNS 里有数千个细胞递质未知，这里一律当兴奋性</p>
        <p>• <b>步态</b>：六足协调的 CPG 是<strong>写好的程序</strong>，不是从连接组学出来的</p>
        <p>• <b>下行解码</b>：把 DNp09 / DNa02 的放电率映射成前进/转向是线性读出</p>
        <p>• 没有学习、没有身体感觉反馈闭环（除了视觉）</p>
      </div>
    </div>

    <div class="box danger">
      <div class="h">🚫 一句话：这不是「果蝇数字孪生」</div>
      <p style="margin-bottom:0">
        接线来自真实重建，这是它的价值；但<b>动力学、感受器映射、动作解码都是工程选择</b>。
        所以只能说「用真实连接组驱动的具身仿真」，不能说「重现了果蝇行为」。
        fly-arena 自己在元数据里也是这么写：<i>"No learned natural behavior."</i>
      </p>
    </div>
  </section>

  <!-- ================= 08 ================= -->
  <section id="related">
    <h2><span class="num">08</span>相关项目与许可<span class="en">Related projects</span></h2>

    <div class="tw"><table>
      <thead><tr><th>项目</th><th>做什么</th><th>许可</th></tr></thead>
      <tbody>
        <tr><td><b>flybody</b>（MuJoCo Menagerie）</td>
            <td>官方解剖级蝇体 MJCF，DeepMind × Janelia</td>
            <td><span class="pill g">Apache-2.0</span></td></tr>
        <tr><td><b>FlyGym / NeuroMechFly v2</b></td>
            <td>生物力学蝇体 + 感觉接口，具身实验标准框架（EPFL）</td>
            <td><span class="pill g">Apache-2.0</span></td></tr>
        <tr><td><b>fly-arena</b></td>
            <td><b>本页演示所用</b>：MaleCNS + NeuroMechFly + 行为控制器</td>
            <td><span class="pill g">MIT</span></td></tr>
        <tr><td><b>flybody</b>（Turaga Lab）</td>
            <td>蝇体模型与强化学习运动控制的官方仓库</td>
            <td><span class="pill g">Apache-2.0</span></td></tr>
        <tr><td>MaleCNS v1.0</td>
            <td>脑与腹神经索连接组（本页的「脑」）</td>
            <td><span class="pill b">CC-BY 4.0</span></td></tr>
      </tbody>
    </table></div>

    <h3>引用</h3>
    <pre><span class="c"># 身体模型</span>
Vaxenburg et al. (2024). Whole-body simulation of realistic fruit fly
locomotion with deep reinforcement learning. bioRxiv.
doi:10.1101/2024.03.11.584515

<span class="c"># 大脑数据</span>
Berg et al. (2026). Whole-central nervous system connectome of the adult
male Drosophila. Cell 189(18):5504-5526.e15. doi:10.1016/j.cell.2026.08.015
<span class="c"># 数据来源：FlyEM / HHMI Janelia、University of Cambridge、MRC LMB、Google Research</span></pre>

    <div class="cred">
      本页视频与图片为本机实跑/实渲染产出，所用模型与数据版权归上述各方所有，
      按各自许可（Apache-2.0 / CC-BY 4.0 / MIT）使用并注明出处。
    </div>
  </section>

    <footer>
      <nav class="phaseswitch foot" aria-label="阶段切换">
        <a href="index.html">总览</a>
        <a href="phase0.html">阶段 0</a>
        <a href="phase1.html">阶段 1</a>
        <a href="phase2.html">阶段 2</a>
        <a href="phase3.html">阶段 3</a>
        <a href="neuprint.html">执行台</a>
      </nav>
      <p style="margin-bottom:0">
        <b>MaleCNS 学习指南 · 具身演示</b> ——
        身体模型来自 Google DeepMind × HHMI Janelia 的 <code>flybody</code>（Apache-2.0），
        脑数据来自 HHMI Janelia FlyEM 的 <b>MaleCNS v1.0</b>（CC-BY 4.0），
        仿真与行为控制器来自 <code>fly-arena</code>（MIT）。
        引用数据须注明 Berg et al. (2026)；引用身体模型须注明 Vaxenburg et al. (2024)。
      </p>
    </footer>

  </main>
</div>

</body>
</html>
"""


def main() -> None:
    html = build()
    with open(DST, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已写出 {DST}  （{len(html)/1024:.1f} KB）")
    print(f"  引用资源 {len(re.findall(r'src=', html))} 处")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()