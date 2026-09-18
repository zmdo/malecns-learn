"""
extract_papers.py — 从 EuropePMC 的 JATS XML 抽取结构化正文，生成页面用的数据。

输入:  _papers/<name>.xml   （EuropePMC fullTextXML）
输出:  _papers/<name>.sections.json
       { meta:{...}, blocks:[ {id, kind, level, title, paras:[...], figs:[...]} ] }

设计原则：
  · 只抽取「阅读顺序」上的正文段落，跳过参考文献、作者贡献等
  · 段落保留少量内联标记（<b>/<i>），去掉其余标签
  · 图形给出可直接引用的 CDN URL（不下载图片，避免仓库膨胀）
"""
import html
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "_papers")

# PMC id 用于拼接图片 CDN 地址
PAPER_META = {
    "dorkenwald": {
        "pmcid": "PMC11446842",
        "cite": "Dorkenwald et al. 2024, Nature 634:124–138",
        "doi": "10.1038/s41586-024-07558-y",
        "license": "CC-BY 4.0",
    },
    "shiu": {
        "pmcid": "PMC11446845",
        "cite": "Shiu et al. 2024, Nature 634:210–219",
        "doi": "10.1038/s41586-024-07763-9",
        "license": "CC-BY 4.0",
    },
}

# 跳过这些 sec-type（不是正文阅读材料）
SKIP_SEC_TYPES = {"kwd-group", "supplementary-material", "author-notes", "fn-group",
                  "ack", "abbrev", "glossary", "ref-list", "app", "app-group"}


def strip_tags(s, keep=("b", "i", "sub", "sup", "em", "strong", "sc")):
    """只保留少量内联标记，其余标签剥掉。"""
    s = re.sub(r"<\?[^?]*\?>", "", s)                      # 处理指令
    s = re.sub(r"<!--[\s\S]*?-->", "", s)
    # 归一化要保留的标签
    s = re.sub(r"<(italic|em)\b[^>]*>", "<i>", s)
    s = re.sub(r"</(italic|em)>", "</i>", s)
    s = re.sub(r"<(bold|strong)\b[^>]*>", "<b>", s)
    s = re.sub(r"</(bold|strong)>", "</b>", s)
    # 去掉不保留的标签
    def repl(m):
        tag = m.group(1)
        return "" if tag.lower() not in keep else m.group(0)
    s = re.sub(r"</?([A-Za-z][\w:-]*)[^>]*>", lambda m: "" if m.group(1).lower() not in keep else m.group(0), s)
    s = html.unescape(s)
    # xref 引用（图/表/文献）已经剥掉标签，这里整理多余空格
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+([,.;:)])", r"\1", s)
    return s.strip()


def find_sections(xml):
    """按出现顺序切出 <sec>…</sec> 顶层块（含嵌套标题）。"""
    out = []
    # 逐个捕获 sec（含嵌套），用深度扫描
    for m in re.finditer(r"<sec\b([^>]*)>", xml):
        attrs = m.group(1)
        sec_type = (re.search(r'sec-type="([^"]*)"', attrs) or [None, ""])[1]
        if sec_type in SKIP_SEC_TYPES:
            continue
        # 找到匹配的 </sec>
        start = m.end()
        depth = 1
        i = start
        while depth and i < len(xml):
            nxt = re.search(r"</?sec\b", xml[i:])
            if not nxt:
                break
            j = i + nxt.start()
            if xml[j:j + 5] == "</sec":
                depth -= 1
            else:
                depth += 1
            i = j + 4
        body = xml[start:i]
        tm = re.search(r"<title>([\s\S]*?)</title>", body)
        title = strip_tags(tm.group(1)) if tm else ""
        if not title:
            continue
        # 只取本层直接段落（排除更深层 sec 里的，避免重复）
        out.append({"title": title, "body": body, "attrs": attrs})
    return out


def top_level_sections(xml):
    """取出互不嵌套的顶层 sec。"""
    secs = []
    pos = 0
    while True:
        m = re.search(r"<sec\b([^>]*)>", xml[pos:])
        if not m:
            break
        attrs = m.group(1)
        start = pos + m.end()
        # 匹配结束
        depth = 1
        i = start
        while depth and i < len(xml):
            nxt = re.search(r"</?sec\b", xml[i:])
            if not nxt:
                i = len(xml)
                break
            j = i + nxt.start()
            if xml[j:j + 5] == "</sec":
                depth -= 1
            else:
                depth += 1
            i = j + 4
        body = xml[start:i]
        sec_type = (re.search(r'sec-type="([^"]*)"', attrs) or [None, ""])[1]
        tm = re.search(r"<title>([\s\S]*?)</title>", body)
        title = strip_tags(tm.group(1)) if tm else ""
        secs.append({"title": title, "body": body, "type": sec_type})
        pos = i
    return [s for s in secs if s["type"] not in SKIP_SEC_TYPES]


def paras_of(body):
    """取某层直接段落（不进入子 sec）。"""
    # 先砍掉所有子 sec，避免把子章节段落算进来
    cut = body
    depth = 0
    out = []
    i = 0
    while i < len(cut):
        m = re.search(r"</?sec\b", cut[i:])
        if not m:
            out.append(cut[i:])
            break
        j = i + m.start()
        if cut[j:j + 5] == "</sec":
            if depth == 0:
                out.append(cut[i:j])
                i = j + 4
                continue
            depth -= 1
        else:
            if depth == 0:
                out.append(cut[i:j])
            depth += 1
        i = j + 4
    text = "".join(out)
    ps = re.findall(r"<p\b[^>]*>([\s\S]*?)</p>", text)
    return [strip_tags(p) for p in ps if strip_tags(p)]


def figs_of(body, pmcid):
    """抽取 <fig>，给出 CDN 图片地址。"""
    out = []
    for m in re.finditer(r"<fig\b([^>]*)>([\s\S]*?)</fig>", body):
        attrs, inner = m.group(1), m.group(2)
        lab = re.search(r"<label>([\s\S]*?)</label>", inner)
        cap = re.search(r"<caption>([\s\S]*?)</caption>", inner)
        title = re.search(r"<title>([\s\S]*?)</title>", inner)
        # 取非缩略图的那张
        href, blob = None, None
        for g in re.finditer(r'<graphic\b([^>]*?)/?>', inner):
            a = g.group(1)
            ct = (re.search(r'content-type="([^"]*)"', a) or [None, ""])[1]
            h = (re.search(r'xlink:href="([^"]*)"', a) or [None, None])[1]
            if ct == "thumb" or h is None:
                continue
            href = h
            pm = re.search(r"<\?cloudpmc-path ([^?]+)\?>", inner)
            blob = pm.group(1).strip() if pm else None
            break
        url = None
        if blob:
            url = "https://cdn.ncbi.nlm.nih.gov/pmc/" + blob.lstrip("/")
        elif href:
            url = f"https://cdn.ncbi.nlm.nih.gov/pmc/blobs/{pmcid}/{href}"
        out.append({
            "label": strip_tags(lab.group(1)) if lab else "",
            "title": strip_tags(title.group(1)) if title else "",
            "caption": strip_tags(cap.group(1)) if cap else "",
            "url": url,
        })
    return out


def build(name):
    path = os.path.join(PAPERS, name + ".xml")
    xml = open(path, encoding="utf-8").read()
    meta = dict(PAPER_META.get(name, {}))
    tm = re.search(r"<article-title>([\s\S]*?)</article-title>", xml)
    meta["title"] = strip_tags(tm.group(1)) if tm else ""
    ab = re.search(r"<abstract\b[^>]*>([\s\S]*?)</abstract>", xml)
    blocks = []
    if ab:
        blocks.append({
            "kind": "abstract", "level": 1, "title": "Abstract",
            "paras": paras_of(ab.group(1)), "figs": [],
        })
    for s in top_level_sections(xml):
        paras = paras_of(s["body"])
        figs = figs_of(s["body"], meta.get("pmcid", ""))
        # 子章节单独成块（避免丢内容）
        subs = []
        for sub in re.finditer(r"<sec\b[^>]*>([\s\S]*?)</sec>", s["body"]):
            st = re.search(r"<title>([\s\S]*?)</title>", sub.group(1))
            if not st:
                continue
            stitle = strip_tags(st.group(1))
            if stitle and stitle != s["title"]:
                sp = paras_of(sub.group(1))
                sf = figs_of(sub.group(1), meta.get("pmcid", ""))
                if sp or sf:
                    subs.append({"kind": "section", "level": 2, "title": stitle,
                                 "paras": sp, "figs": sf})
        if paras or figs or subs:
            blocks.append({"kind": "section", "level": 1, "title": s["title"],
                           "paras": paras, "figs": figs, "subs": subs})
    meta["blocks"] = len(blocks)
    meta["paras"] = sum(len(b["paras"]) + sum(len(x["paras"]) for x in b.get("subs", [])) for b in blocks)
    meta["figs"] = sum(len(b["figs"]) + sum(len(x["figs"]) for x in b.get("subs", [])) for b in blocks)
    meta["chars"] = sum(len(p) for b in blocks
                        for p in (b["paras"] + [q for x in b.get("subs", []) for q in x["paras"]]))
    out = {"meta": meta, "blocks": blocks}
    dst = os.path.join(PAPERS, name + ".sections.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{name}: blocks={meta['blocks']} paras={meta['paras']} figs={meta['figs']} "
          f"chars={meta['chars']:,}  -> {dst}")
    return out


if __name__ == "__main__":
    for n in (sys.argv[1:] or ["dorkenwald", "shiu"]):
        try:
            build(n)
        except Exception as e:
            print(f"{n}: ERR {e}")
