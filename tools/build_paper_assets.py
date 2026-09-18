"""
build_paper_assets.py — 把 _papers/*.sections.json 转成页面直接引用的 JS。

输出:
  assets/papers/<name>.js   ->  window.MCNS_PAPERS['<name>'] = {...};

译文与标注是人工撰写的，放在 assets/papers/notes.js（本脚本不覆盖它）。
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_papers")
DST = os.path.join(ROOT, "assets", "papers")


def main():
    os.makedirs(DST, exist_ok=True)
    names = sys.argv[1:] or ["dorkenwald", "shiu", "berg"]
    for name in names:
        p = os.path.join(SRC, name + ".sections.json")
        if not os.path.isfile(p):
            print(f"{name}: 缺少 {p}，先跑 tools/extract_papers.py")
            continue
        data = json.load(open(p, encoding="utf-8"))
        js = (
            "/* 自动生成：tools/build_paper_assets.py —— 请勿手改。\n"
            "   来源 Europe PMC JATS 全文（CC-BY 4.0）："
            + data["meta"].get("pmcid", "") + " */\n"
            "window.MCNS_PAPERS = window.MCNS_PAPERS || {};\n"
            "window.MCNS_PAPERS[" + json.dumps(name) + "] = "
            + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
        )
        out = os.path.join(DST, name + ".js")
        with open(out, "w", encoding="utf-8") as f:
            f.write(js)
        meta = data["meta"]
        print(f"{name}: 段{meta['paras']} 图{meta['figs']} "
              f"字符{meta['chars']:,} -> {os.path.relpath(out, ROOT)} "
              f"({os.path.getsize(out)/1024:.0f} KB)")

    # 记录来源与许可，便于核对
    manifest = {
        "note": "原文来自 Europe PMC 开放获取全文（JATS XML），按 CC-BY 4.0 转载。",
        "papers": {}
    }
    for name in names:
        p = os.path.join(SRC, name + ".sections.json")
        if os.path.isfile(p):
            m = json.load(open(p, encoding="utf-8"))["meta"]
            manifest["papers"][name] = {
                k: m.get(k) for k in ("title", "cite", "doi", "pmcid", "license",
                                      "blocks", "paras", "figs", "chars")
            }
    with open(os.path.join(DST, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print("manifest.json 已写出")


if __name__ == "__main__":
    main()
