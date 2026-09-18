"""validate_pages.py — 结构校验：支持多页面 + 内联 SVG 的 XML 合法性。

用法:
  python validate_pages.py                # 校验仓库里所有 phase*.html
  python validate_pages.py phase1.html    # 只校验指定文件
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))

# 顶层可导航页面（校验时一并检查其互链）
TOP_PAGES = {"index.html", "phase0.html", "phase1.html", "phase2.html", "neuprint.html"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class P(HTMLParser):
    """宽松的 HTML 嵌套检查器：记录未闭合/多余闭合标签、id、资源引用。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = {}
        self.images = []
        self.hrefs = []
        self.tagcount = {}
        self.in_style = self.in_script = False
        self.tables = self.sections = self.figures = 0
        self.textlen = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tagcount[tag] = self.tagcount.get(tag, 0) + 1
        if tag == "style":
            self.in_style = True
        if tag == "script":
            self.in_script = True
        if tag == "table":
            self.tables += 1
        if tag == "section":
            self.sections += 1
        if tag == "figure":
            self.figures += 1
        if "id" in a:
            i = a["id"]
            if i in self.ids:
                self.errors.append(f"重复 id '{i}' (行 {self.getpos()[0]})")
            self.ids[i] = self.getpos()[0]
        if tag == "img":
            self.images.append((a.get("src"), self.getpos()[0]))
        if tag == "a" and a.get("href"):
            self.hrefs.append((a["href"], self.getpos()[0]))
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "script":
            self.in_script = False
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"多余的 </{tag}> (行 {self.getpos()[0]})")
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        names = [t for t, _ in self.stack]
        if tag in names:
            idx = len(names) - 1 - names[::-1].index(tag)
            for t, ln in self.stack[idx + 1:]:
                self.errors.append(f"未闭合 <{t}> 开于行 {ln}，被 </{tag}> (行 {self.getpos()[0]}) 关闭")
            del self.stack[idx:]
        else:
            self.errors.append(f"不匹配的 </{tag}> (行 {self.getpos()[0]})")

    def handle_data(self, d):
        if not self.in_style and not self.in_script:
            self.textlen += len(d.strip())


def check_svg(path, html):
    """把每个内联 <svg> 单独做一次 XML 解析，确保是合法 XML。"""
    problems = []
    blocks = re.findall(r"<svg\b[\s\S]*?</svg>", html)
    for n, b in enumerate(blocks, 1):
        try:
            ET.fromstring(b)
        except ET.ParseError as e:
            problems.append(f"内联 SVG #{n} 不是合法 XML: {e}")
    return blocks, problems


# 只在「代码块/公式块」里使用的语义着色类，必须真正有 CSS 定义。
# 这类错误很隐蔽：类名写错不会报错，只是那个 span 悄悄变成纯文本。
COLOR_CLASSES = ["c", "cmt", "s", "k", "n", "bl", "hl", "hl2"]


def _display_width(s):
    """等宽排版下的显示宽度：CJK 全角算 2 列，其余算 1 列。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def check_css_usage(path, html):
    """校验 CSS 类名的引用与定义，以及等宽块的宽度。"""
    problems = []
    notes = []
    m = re.search(r"<style>([\s\S]*?)</style>", html)
    if not m:
        return notes, ["找不到 <style> 块"]
    css = m.group(1)

    # 1) 语义着色类：在 pre / .formula 里用到就必须有对应定义
    for blk_name, pat in [("pre", r"<pre[^>]*>([\s\S]*?)</pre>"),
                          (".formula", r'<div class="formula">([\s\S]*?)</div>')]:
        used = set()
        for b in re.findall(pat, html):
            for cm in re.finditer(r'class="([^"]+)"', b):
                used.update(cm.group(1).split())
        for c in sorted(used):
            if c not in COLOR_CLASSES:
                continue
            # 必须是精确的「pre .c」或「.formula .c」规则，不能靠前缀匹配
            hit = re.search(rf"(^|[\n,])\s*(pre|\.formula)\s+\.{re.escape(c)}\s*[,{{]", css)
            if hit:
                notes.append(f"{blk_name} 里的 .{c} 有定义")
            else:
                problems.append(f"{blk_name} 里用了 .{c}，但 CSS 没有 pre/.formula 作用域下的定义"
                                f"（会渲染成无色纯文本）")

    # 2) 等宽块不能过宽（否则要横向滚动，读者会漏掉右半边）
    LIMIT = 92
    for kind, pat in [(".formula", r'<div class="formula">([\s\S]*?)</div>'),
                      ("pre", r"<pre[^>]*>([\s\S]*?)</pre>")]:
        for i, b in enumerate(re.findall(pat, html), 1):
            worst = 0
            for ln in b.split("\n"):
                vis = re.sub(r"<[^>]+>", "", ln)
                vis = (vis.replace("&gt;", ">").replace("&lt;", "<")
                          .replace("&amp;", "&").replace("&nbsp;", " "))
                worst = max(worst, _display_width(vis))
            if worst > LIMIT:
                problems.append(f"{kind} 块 #{i} 最宽 {worst} 列，超过 {LIMIT}（等宽排版会横向溢出）")

    # 3) 导航类组件：用到就必须有定义（同样属于「静默失效」那一类问题）
    NAV_CLASSES = ["phaseswitch", "on", "p0", "p1", "foot", "now"]
    nav_used = set()
    for b in re.findall(r'class="([^"]*phaseswitch[^"]*)"', html):
        nav_used.update(b.split())
    for c in sorted(nav_used):
        if c not in NAV_CLASSES:
            continue
        if re.search(rf"\.{re.escape(c)}\b", css):
            notes.append(f"导航类 .{c} 有定义")
        else:
            problems.append(f"阶段切换器用了 .{c}，但 CSS 里没有定义（会掉样式）")

    # 4) 内联语义标签：用了就应该有样式，否则退化成浏览器默认外观
    INLINE_TAGS = ["kbd", "mark", "abbr", "samp", "var"]
    for tag in INLINE_TAGS:
        used = len(re.findall(rf"<{tag}[\s>]", html))
        if not used:
            continue
        if re.search(rf"(^|[\n,}}])\s*{tag}\s*[,{{]", css):
            notes.append(f"内联标签 <{tag}> ×{used} 有样式")
        else:
            problems.append(f"用了 {used} 处 <{tag}>，但 CSS 没有该标签的样式"
                            f"（会退化成浏览器默认外观）")

    return notes, problems


def collect_ids(path):
    """收集某个页面里的所有 id。"""
    html = open(path, encoding="utf-8").read()
    return set(re.findall(r'\bid="([^"]+)"', html))


def check_file(path, id_map=None):
    name = os.path.basename(path)
    html = open(path, encoding="utf-8").read()
    p = P()
    p.feed(html)

    print("=" * 72)
    print(f"{name}   ({len(html):,} bytes, 可见文字 {p.textlen:,} 字)")
    print("=" * 72)
    print(f"  section {p.sections} · table {p.tables} · figure {p.figures} · "
          f"img {len(p.images)} · a {len(p.hrefs)}")

    ok = True

    if p.stack:
        ok = False
        print("  !! 文末仍未闭合:")
        for t, ln in p.stack:
            print(f"     <{t}> 行 {ln}")
    if p.errors:
        ok = False
        print(f"  !! {len(p.errors)} 处嵌套问题:")
        for e in p.errors[:30]:
            print("     " + e)
    if not p.errors and not p.stack:
        print("  OK: 标签嵌套正确，无未闭合元素")

    # 资源
    missing = 0
    for src, ln in p.images:
        if not src or re.match(r"^https?://", src):
            continue
        fp = os.path.join(ROOT, src.replace("/", os.sep))
        if os.path.isfile(fp):
            print(f"  OK   img 行 {ln:>5}  {src}  ({os.path.getsize(fp)/1024:.1f} KB)")
        else:
            ok = False
            missing += 1
            print(f"  MISS img 行 {ln:>5}  {src}")

    # 锚点
    broken = sorted({h for h, _ in p.hrefs if h.startswith("#") and h[1:] not in p.ids})
    if broken:
        ok = False
        print("  !! 断掉的内链: " + ", ".join(broken))
    else:
        print("  OK: 所有 #锚点都能解析")

    # 本地页面互链
    for h, ln in p.hrefs:
        if h.endswith(".html") and not re.match(r"^https?://", h):
            fp = os.path.join(ROOT, h)
            if not os.path.isfile(fp):
                ok = False
                print(f"  !! 行 {ln} 指向不存在的页面: {h}")
            else:
                print(f"  OK   行 {ln:>5}  → {h}")

    # 跨页锚点：phase0.html#xxx 里的 xxx 必须在目标页真实存在
    if id_map:
        checked = 0
        for h, ln in p.hrefs:
            if "#" not in h or re.match(r"^https?://", h):
                continue
            page, _, frag = h.partition("#")
            if not page or not frag:
                continue
            target = id_map.get(page)
            if target is None:
                continue
            checked += 1
            if frag not in target:
                ok = False
                print(f"  !! 行 {ln} 跨页锚点失效: {h}（{page} 里没有 id=\"{frag}\"）")
        if checked and ok:
            print(f"  OK: {checked} 个跨页锚点都能解析")

    # 内联 SVG
    svgs, problems = check_svg(path, html)
    if svgs:
        print(f"  内联 SVG: {len(svgs)} 个")
        for pr in problems:
            ok = False
            print("  !! " + pr)
        if not problems:
            print("  OK: 每个内联 SVG 都是合法 XML")

    # CSS 类名引用 vs 定义、等宽块宽度
    notes, cssprobs = check_css_usage(path, html)
    if cssprobs:
        ok = False
        print(f"  !! {len(cssprobs)} 处 CSS 使用问题:")
        for e in cssprobs:
            print("     " + e)
    else:
        print(f"  OK: CSS 类名与等宽宽度检查通过（{len(notes)} 项）")

    print(f"  → {'PASS' if ok else 'FAIL'}\n")
    return ok


def main():
    if len(sys.argv) > 1:
        files = [os.path.join(ROOT, a) for a in sys.argv[1:]]
    else:
        # 顶层页面：index.html + phase*.html
        files = sorted(os.path.join(ROOT, f) for f in os.listdir(ROOT)
                       if f in TOP_PAGES or re.match(r"^phase\d+\.html$", f))
    if not files:
        print("没有找到可校验的页面")
        return 1

    # 顶层页面集合，用于校验互链
    top = sorted(os.path.join(ROOT, f) for f in os.listdir(ROOT)
                 if f in TOP_PAGES or re.match(r"^phase\d+\.html$", f))
    id_map = {os.path.basename(f): collect_ids(f) for f in top}

    results = [check_file(f, id_map) for f in files]
    print("=" * 72)
    print(f"总计 {len(results)} 个页面，{sum(results)} 个通过，{len(results)-sum(results)} 个失败")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
