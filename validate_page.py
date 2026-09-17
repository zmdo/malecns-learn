"""Structural validation + link/asset audit for the Phase 0 study page."""
import os, re, sys
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"E:\code-design\dianzinao-research\malecns\phase0.html"
ROOT = os.path.dirname(SRC)

VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = {}
        self.tagcount = {}
        self.images = []
        self.hrefs = []
        self.text_len = 0
        self.in_style = False
        self.in_script = False
        self.headings = []
        self._cur = None
        self.tables = 0
        self.sections = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tagcount[tag] = self.tagcount.get(tag, 0) + 1
        if tag == "style": self.in_style = True
        if tag == "script": self.in_script = True
        if "id" in a:
            i = a["id"]
            if i in self.ids:
                self.errors.append(f"DUPLICATE id '{i}' at line {self.getpos()[0]}")
            self.ids[i] = self.getpos()[0]
        if tag == "img":
            self.images.append((a.get("src"), a.get("alt", ""), self.getpos()[0]))
        if tag == "a" and a.get("href"):
            self.hrefs.append((a["href"], self.getpos()[0]))
        if tag == "table": self.tables += 1
        if tag == "section": self.sections += 1
        if tag in ("h1","h2","h3"): self._cur = (tag, self.getpos()[0], [])
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == "style": self.in_style = False
        if tag == "script": self.in_script = False
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}> at line {self.getpos()[0]}")
            return
        top, ln = self.stack[-1]
        if top == tag:
            self.stack.pop()
        else:
            # search for match (indicates unclosed tags)
            names = [t for t, _ in self.stack]
            if tag in names:
                idx = len(names) - 1 - names[::-1].index(tag)
                for t, l in self.stack[idx+1:]:
                    self.errors.append(f"UNCLOSED <{t}> opened line {l}, closed by </{tag}> line {self.getpos()[0]}")
                del self.stack[idx:]
            else:
                self.errors.append(f"UNMATCHED </{tag}> at line {self.getpos()[0]} (open: {top} line {ln})")

    def handle_data(self, d):
        if not self.in_style and not self.in_script:
            self.text_len += len(d.strip())
            if self._cur:
                self._cur[2].append(d)

p = P()
html = open(SRC, encoding="utf-8").read()
p.feed(html)

print("=" * 72)
print("STRUCTURE")
print("=" * 72)
print(f"file size        : {len(html):,} bytes")
print(f"visible text     : {p.text_len:,} chars")
print(f"sections         : {p.sections}")
print(f"tables           : {p.tables}")
print(f"images           : {len(p.images)}")
print(f"<a href>         : {len(p.hrefs)}")
if p.stack:
    print("\n!! UNCLOSED AT EOF:")
    for t, l in p.stack:
        print(f"   <{t}> line {l}")
if p.errors:
    print(f"\n!! {len(p.errors)} NESTING ERRORS:")
    for e in p.errors[:40]:
        print("   " + e)
else:
    print("\nOK: all tags properly nested, no unclosed elements.")

print()
print("=" * 72)
print("ASSETS")
print("=" * 72)
for src, alt, ln in p.images:
    if src and not re.match(r"^https?://", src):
        path = os.path.join(ROOT, src.replace("/", os.sep))
        ok = os.path.isfile(path)
        size = f"{os.path.getsize(path):,} B" if ok else "MISSING"
        print(f"[{'OK ' if ok else 'FAIL'}] line {ln:>4}  {src}  ({size})")
        if not ok:
            p.errors.append(f"missing asset {src}")
    else:
        print(f"[EXT] line {ln:>4}  {src}")

print()
print("=" * 72)
print("ANCHORS")
print("=" * 72)
bad = [h for h, ln in p.hrefs if h.startswith("#") and h[1:] not in p.ids]
for h in sorted(set(bad)):
    print(f"  BROKEN internal anchor: {h}")
print("  OK: every internal #anchor resolves." if not bad else f"  {len(set(bad))} broken")

print()
print("=" * 72)
print("EXTERNAL LINKS")
print("=" * 72)
ext = sorted(set(h for h, _ in p.hrefs if h.startswith("http")))
for u in ext:
    print("  " + u)
print(f"  total {len(ext)} unique external URLs")

print()
print("=" * 72)
print("HEADING OUTLINE")
print("=" * 72)
for m in re.finditer(r"<(h[123])[^>]*>(.*?)</\1>", html, re.S):
    lvl = int(m.group(1)[1])
    txt = re.sub(r"<[^>]+>", "", m.group(2))
    txt = re.sub(r"\s+", " ", txt).strip()
    print("  " * (lvl - 1) + f"h{lvl} {txt}")

if p.errors:
    print("\nRESULT: FAIL")
    sys.exit(1)
print("\nRESULT: PASS")
