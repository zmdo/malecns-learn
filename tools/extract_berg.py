"""
extract_berglab.py — 从 bioRxiv 全文 HTML 抽取 Berg et al. 的 MaleCNS 论文结构。

为什么用 bioRxiv 而不是 Europe PMC：
  · 正式版（Cell 2026）是订阅制，不可转载
  · bioRxiv 预印本（10.1101/2025.10.09.680999）明确为 CC BY 4.0，可合法转载
  · Europe PMC 虽收录该预印本（PPR1098763），但 fullTextXML 端点不提供全文

输入:  https://www.biorxiv.org/content/10.1101/2025.10.09.680999v2.full
输出:  _papers/berg.sections.json   （结构与 extract_papers.py 一致，便于页面复用）
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "_papers")
URL = "https://www.biorxiv.org/content/10.1101/2025.10.09.680999v2.full"
UA = {"User-Agent": "Mozilla/5.0 (mcns-study; +https://github.com/zmdo/malecns-learn)"}

# 这些 section 不是阅读材料
SKIP = {
    "Declaration of Interests", "Author Contributions", "Acknowledgements",
    "Funder Information Declared", "Footnotes", "References",
    "Citation Manager Formats", "Subject Area", "Supplementary Figures",
    "Supplementary Information", "Data availability", "Code availability",
}

KEEP_INLINE = ("b", "i", "sub", "sup", "em", "strong")


def strip_tags(s):
    s = re.sub(r"<script[\s\S]*?</script>", "", s)
    s = re.sub(r"<style[\s\S]*?</style>", "", s)
    s = re.sub(r"<(italic|em)\b[^>]*>", "<i>", s)
    s = re.sub(r"</(italic|em)>", "</i>", s)
    s = re.sub(r"<(bold|strong)\b[^>]*>", "<b>", s)
    s = re.sub(r"</(bold|strong)>", "</b>", s)
    s = re.sub(r"</?([A-Za-z][\w:-]*)[^>]*>",
               lambda m: "" if m.group(1).lower() not in KEEP_INLINE else m.group(0), s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    return s.strip()


CACHE = os.path.join(PAPERS, "berg.biorxiv.html")


def fetch():
    """下载 bioRxiv 全文 HTML，带本地缓存（避免反复请求被限流）。"""
    if os.path.isfile(CACHE) and os.path.getsize(CACHE) > 500_000:
        print(f"  使用缓存 {CACHE}")
        return open(CACHE, encoding="utf-8").read()
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                doc = r.read().decode("utf-8", "replace")
            os.makedirs(PAPERS, exist_ok=True)
            open(CACHE, "w", encoding="utf-8").write(doc)
            return doc
        except Exception as e:
            last = e
            wait = 8 * (attempt + 1)
            print(f"  第 {attempt + 1} 次失败（{str(e)[:50]}），{wait}s 后重试 …")
            time.sleep(wait)
    raise last


def find_sections(doc):
    """把正文按 h2 切成节；每节取 h3 作为子节。"""
    body = doc
    # 去掉脚本/样式，避免标题被误抓
    body = re.sub(r"<script[\s\S]*?</script>", "", body)
    body = re.sub(r"<style[\s\S]*?</style>", "", body)

    # 找所有 h2，记录位置
    marks = [(m.start(), m.end(), strip_tags(m.group(1)))
             for m in re.finditer(r"<h2[^>]*>([\s\S]*?)</h2>", body)]
    out = []
    for i, (s, e, title) in enumerate(marks):
        if not title:
            continue
        nxt = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        chunk = body[e:nxt]
        out.append({"title": title, "body": chunk})
    return out


def _paras_in(chunk):
    """chunk 里所有段落（不再往下切）。"""
    out = []
    for p in re.findall(r"<p\b[^>]*>([\s\S]*?)</p>", chunk):
        t = strip_tags(p)
        if len(t) < 25:
            continue
        # 丢掉参考文献条目
        if re.match(r"^\d+\.\s", t) and len(t) < 200:
            continue
        out.append(t)
    return out


def paras_of(chunk):
    """取本层段落：第一个 <h3> 之前的部分（其后的属于子节）。"""
    first_h3 = chunk.find("<h3")
    return _paras_in(chunk if first_h3 < 0 else chunk[:first_h3])


def sub_paras(chunk):
    """子节段落：从子节起点到下一个 <h3> 或 <h2>。"""
    m = re.search(r"<h[23]", chunk)
    return _paras_in(chunk[m.start():] if m else chunk)


def subs_of(chunk):
    """h3 子节。"""
    marks = [(m.start(), m.end(), strip_tags(m.group(1)))
             for m in re.finditer(r"<h3[^>]*>([\s\S]*?)</h3>", chunk)]
    out = []
    for i, (s, e, title) in enumerate(marks):
        if not title:
            continue
        nxt = marks[i + 1][0] if i + 1 < len(marks) else len(chunk)
        sub = chunk[e:nxt]
        ps = sub_paras(sub)
        if ps:
            out.append({"kind": "section", "level": 2, "title": title,
                        "paras": ps, "figs": figs_of(sub)})
    return out


def figs_of(chunk):
    """bioRxiv 的图。

    · 图在 <div class="highwire-figure"> 里，图片是 <img class="fig-inline-img" data-src="…/F1.large.jpg">
    · 图注放在 data-figure-caption 属性里
    · 真实图片地址形如 .../2025.10.09.680999/F1.large.jpg
    """
    out = []
    FURL = ("https://www.biorxiv.org/content/biorxiv/early/2025/10/30/"
            "2025.10.09.680999/")
    for m in re.finditer(r'<div[^>]*class="[^"]*highwire-figure[^"]*"[^>]*>', chunk):
        nxt = re.search(r'<div[^>]*class="[^"]*highwire-figure[^"]*"', chunk[m.end():])
        end = m.end() + nxt.start() if nxt else min(len(chunk), m.end() + 12000)
        inner = chunk[m.start():end]

        cap = ""
        cm = re.search(r'data-figure-caption="([^"]*)"', inner)
        if cm:
            cap = strip_tags(html.unescape(cm.group(1)))
        else:
            cm2 = re.search(r"<figcaption[^>]*>([\s\S]*?)</figcaption>", inner)
            if cm2:
                cap = strip_tags(cm2.group(1))

        url = None
        for tag in re.finditer(r"<img\b[^>]*>", inner):
            t = tag.group(0)
            for a in ("data-src", "src"):
                sm = re.search(r'%s="([^"]+)"' % a, t)
                if sm and not sm.group(1).startswith("data:") and "loading" not in sm.group(1):
                    url = sm.group(1)
                    break
            if url:
                break
        if url and url.startswith("/"):
            url = "https://www.biorxiv.org" + url
        # 统一用高分辨率 jpg（页面里的 data-src 有时是 .medium.gif）
        if url:
            url = re.sub(r"\.(?:medium|small)\.(?:gif|jpg)$", ".large.jpg", url)
        if not url:
            fm = re.search(r"\bF(\d+)\.(?:large|full)", inner)
            if fm:
                url = FURL + "F%s.large.jpg" % fm.group(1)

        label = ""
        lm = re.match(r"^(Figure\s*\d+|Fig\.?\s*\d+)\b[.:]?\s*", cap)
        if lm:
            label = lm.group(1)
            cap = cap[lm.end():]
        if not label and url:
            fm = re.search(r"/F(\d+)\.", url)
            if fm:
                label = "Figure " + fm.group(1)

        if cap or url:
            out.append({"label": label or "Figure", "title": "",
                        "caption": cap, "url": url})
    return out


def meta(doc, name):
    m = re.search(r'<meta[^>]*name="%s"[^>]*content="([^"]*)"' % re.escape(name), doc)
    return html.unescape(m.group(1)) if m else None


def main():
    print("下载 bioRxiv 全文 …")
    doc = fetch()
    print(f"  {len(doc):,} chars")
    secs = find_sections(doc)

    blocks = []
    # 摘要取自 citation_abstract（比从正文里找可靠）
    ab = meta(doc, "citation_abstract")
    if ab:
        ap = _paras_in(ab)
        if ap:
            blocks.append({"kind": "abstract", "level": 1, "title": "Abstract",
                           "paras": ap, "figs": []})

    for s in secs:
        t = s["title"].strip()
        if t in SKIP or t.lower() in ("abstract",):
            continue
        if t == "References":
            break
        ps = paras_of(s["body"])
        fs = figs_of(s["body"])
        subs = subs_of(s["body"])
        if ps or fs or subs:
            blocks.append({"kind": "section", "level": 1, "title": t,
                           "paras": ps, "figs": fs, "subs": subs})

    # 同一张图可能既落在父节的范围内、也落在子节里，去重（保留首次出现）
    seen = set()

    def dedupe(figs):
        out = []
        for f in figs:
            key = f.get("label") or f.get("url")
            if key in seen:
                continue
            seen.add(key)
            out.append(f)
        return out

    for b in blocks:
        b["figs"] = dedupe(b.get("figs", []))
        for x in b.get("subs", []):
            x["figs"] = dedupe(x.get("figs", []))

    meta_out = {
        "pmcid": "biorxiv:2025.10.09.680999",
        "cite": "Berg et al. — bioRxiv 预印本 v2 (2025-10-30)；正式版 Cell 189(18):5504–5526.e15 (2026)",
        "doi": "10.1101/2025.10.09.680999",
        "license": "CC-BY 4.0（预印本）",
        "title": meta(doc, "citation_title") or "Sexual dimorphism in the complete connectome of the Drosophila male central nervous system",
        "pdf": meta(doc, "citation_pdf_url"),
        "preprint": True,
        "preprint_note": "本页正文来自 bioRxiv 预印本（CC-BY 4.0），不是 Cell 正式版。"
                         "两者数字有差异（预印本 166,691 神经元 / 11,691 类型；"
                         "正式版 166,700 / 11,710），引用请以正式版为准。",
    }
    meta_out["paras"] = sum(len(b["paras"]) + sum(len(x["paras"]) for x in b.get("subs", []))
                            for b in blocks)
    meta_out["figs"] = sum(len(b["figs"]) + sum(len(x["figs"]) for x in b.get("subs", []))
                           for b in blocks)
    meta_out["chars"] = sum(len(p) for b in blocks
                            for p in (b["paras"] + [q for x in b.get("subs", []) for q in x["paras"]]))
    meta_out["blocks"] = len(blocks)

    os.makedirs(PAPERS, exist_ok=True)
    dst = os.path.join(PAPERS, "berg.sections.json")
    json.dump({"meta": meta_out, "blocks": blocks}, open(dst, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nberg: blocks={meta_out['blocks']} paras={meta_out['paras']} "
          f"figs={meta_out['figs']} chars={meta_out['chars']:,} -> {dst}")
    print("\n章节：")
    for i, b in enumerate(blocks):
        n = len(b["paras"]) + sum(len(x["paras"]) for x in b.get("subs", []))
        f = len(b["figs"]) + sum(len(x["figs"]) for x in b.get("subs", []))
        print(f"  [{i:>2}] {b['title'][:56]:<58} 段{n:<4} 图{f}")
        for x in b.get("subs", []):
            print(f"        └ {x['title'][:52]:<54} 段{len(x['paras'])} 图{len(x['figs'])}")


if __name__ == "__main__":
    main()
