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


def check_file(path):
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

    # 内联 SVG
    svgs, problems = check_svg(path, html)
    if svgs:
        print(f"  内联 SVG: {len(svgs)} 个")
        for pr in problems:
            ok = False
            print("  !! " + pr)
        if not problems:
            print("  OK: 每个内联 SVG 都是合法 XML")

    print(f"  → {'PASS' if ok else 'FAIL'}\n")
    return ok


def main():
    if len(sys.argv) > 1:
        files = [os.path.join(ROOT, a) for a in sys.argv[1:]]
    else:
        files = sorted(os.path.join(ROOT, f) for f in os.listdir(ROOT)
                       if re.match(r"^phase\d+\.html$", f))
    if not files:
        print("没有找到 phase*.html")
        return 1
    results = [check_file(f) for f in files]
    print("=" * 72)
    print(f"总计 {len(results)} 个页面，{sum(results)} 个通过，{len(results)-sum(results)} 个失败")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
