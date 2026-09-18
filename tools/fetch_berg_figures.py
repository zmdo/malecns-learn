"""
fetch_berg_figures.py — 下载 Berg 预印本的 9 张图到本地。

为什么不外链：bioRxiv 对图片有速率限制，且跨站引用可能被拦，
页面会时常显示不出图。本地化之后阅读器离线也能看。

输出: assets/papers/berg/F1.large.jpg … F9.large.jpg
      并把 _papers/berg.sections.json 里的 url 改成本地相对路径。
"""
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, "_papers")
OUT = os.path.join(ROOT, "assets", "papers", "berg")
BASE = ("https://www.biorxiv.org/content/biorxiv/early/2025/10/30/"
        "2025.10.09.680999/")
UA = {"User-Agent": "Mozilla/5.0 (mcns-study; +https://github.com/zmdo/malecns-learn)",
      "Referer": "https://www.biorxiv.org/"}


def main():
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(PAPERS, "berg.sections.json")
    data = json.load(open(src, encoding="utf-8"))

    # 收集所有图
    figs = []

    def walk(blocks):
        for b in blocks:
            for f in b.get("figs", []):
                figs.append(f)
            walk(b.get("subs", []))
    walk(data["blocks"])

    got = 0
    for f in figs:
        url = f.get("url") or ""
        m = re.search(r"/F(\d+)\.", url)
        if not m:
            continue
        n = m.group(1)
        name = "F%s.large.jpg" % n
        dst = os.path.join(OUT, name)
        if os.path.isfile(dst) and os.path.getsize(dst) > 4000:
            f["url"] = "assets/papers/berg/" + name
            got += 1
            continue
        ok = False
        for attempt in range(4):
            try:
                req = urllib.request.Request(BASE + name, headers=UA)
                with urllib.request.urlopen(req, timeout=120) as r:
                    blob = r.read()
                if len(blob) < 4000:
                    raise ValueError("文件过小")
                open(dst, "wb").write(blob)
                f["url"] = "assets/papers/berg/" + name
                print(f"  {name:20} {len(blob)/1024:8.0f} KB")
                got += 1
                ok = True
                break
            except Exception as e:
                time.sleep(6 * (attempt + 1))
                if attempt == 3:
                    print(f"  {name:20} 失败: {str(e)[:60]}")
        if not ok:
            f["url"] = None

    json.dump(data, open(src, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n共 {len(figs)} 张图，成功 {got} 张 -> {OUT}")
    print("berg.sections.json 里的 url 已改为本地相对路径")


if __name__ == "__main__":
    main()
