"""
fetch_official_meshes.py — 下载官方 MaleCNS 神经毡网格，转成本地紧凑格式。

数据来源（官方，公开可读，无需登录）：
  gs://flyem-male-cns/rois/fullbrain-roi-v5/mesh/<NAME>.ngmesh     # 脑神经毡（84 个）
  gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0/mesh/...    # VNC 神经毡

格式：neuroglancer_legacy_mesh（小端）
  uint32 numVertices
  float32 positions[numVertices * 3]        # 纳米
  uint32 numTrianglesPerVertex[numVertices] # 每个顶点属于多少个三角形（和 = 总三角形数）
  uint32 indices[totalTriangles * 3]

输出：assets/mcns-meshes.js
  window.MCNS_MESHES = {
    "_meta": {...来源与许可...},
    "MB": { v: <base64 Float32>, n: <base64 Float32>, i: <base64 Uint32>, tris: N, bbox: [...] },
    ...
  }
顶点/法线用 base64 编码的定长二进制，避免 JSON 体积膨胀。

用法:
  python tools/fetch_official_meshes.py                 # 下载并生成
  python tools/fetch_official_meshes.py --list          # 只列出可用网格
"""
import argparse
import base64
import json
import math
import os
import struct
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BUCKET = "flyem-male-cns"
GCS_OBJ = "https://storage.googleapis.com/{bucket}/{name}"
GCS_API = "https://storage.googleapis.com/storage/v1/b/{bucket}/o"
UA = {"User-Agent": "mcns-study/1.0"}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "_official", "meshes")
OUT_JS = os.path.join(ROOT, "assets", "mcns-meshes.js")

# 需要打包的解剖结构：显示名 -> 官方网格名前缀列表（左右会合并）
WANTED = {
    # ---- 中央脑 ----
    "AL":  {"src": ["AL(L)", "AL(R)"],           "zh": "触角叶",           "en": "Antennal Lobe"},
    "MB":  {"src": ["CA(L)", "CA(R)", "PED(L)", "PED(R)",
                    "aL(L)", "aL(R)", "a'L(L)", "a'L(R)",
                    "bL(L)", "bL(R)", "b'L(L)", "b'L(R)",
                    "gL(L)", "gL(R)"],           "zh": "蘑菇体",           "en": "Mushroom Body"},
    "MB-CA": {"src": ["CA(L)", "CA(R)"],         "zh": "蘑菇体萼",         "en": "Calyx"},
    "CX":  {"src": ["EB", "FB", "NO", "PB"],     "zh": "中央复合体",       "en": "Central Complex"},
    "CX-EB": {"src": ["EB"],                     "zh": "椭球体",           "en": "Ellipsoid Body"},
    "LH":  {"src": ["LH(L)", "LH(R)"],           "zh": "侧角",             "en": "Lateral Horn"},
    "SEZ": {"src": ["GNG"],                      "zh": "食管下区/颚神经毡", "en": "Subesophageal Zone / GNG"},
    "ALH": {"src": ["AL(L)", "AL(R)", "LH(L)", "LH(R)"]},   # 别名（不用）
    "AOTU": {"src": ["AOTU(L)", "AOTU(R)"],      "zh": "前视结节",         "en": "Anterior Optic Tubercle"},
    "LAL": {"src": ["LAL(L)", "LAL(R)"],         "zh": "侧副叶",           "en": "Lateral Accessory Lobe"},
    "SMP": {"src": ["SMP(L)", "SMP(R)"],         "zh": "上内侧原脑",       "en": "Superior Medial Protocerebrum"},
    "SLP": {"src": ["SLP(L)", "SLP(R)"],         "zh": "上外侧原脑",       "en": "Superior Lateral Protocerebrum"},
    "SIP": {"src": ["SIP(L)", "SIP(R)"],         "zh": "上后侧原脑",       "en": "Superior Intermediate Protocerebrum"},
    "CRE": {"src": ["CRE(L)", "CRE(R)"],         "zh": "侧后脑",           "en": "Crepine"},
    "WED": {"src": ["WED(L)", "WED(R)"],         "zh": "楔形区",           "en": "Wedge"},
    "VES": {"src": ["VES(L)", "VES(R)"],         "zh": "前侧沟区",         "en": "Vest"},
    "IB":  {"src": ["IB"],                       "zh": "下脑桥",           "en": "Inferior Bridge"},
    "BU":  {"src": ["BU(L)", "BU(R)"],           "zh": "球状体",           "en": "Bulb"},
    # ---- 视叶 ----
    "LA":  {"src": ["LA(L)", "LA(R)"],           "zh": "板层",             "en": "Lamina"},
    "ME":  {"src": ["ME(L)", "ME(R)"],           "zh": "髓质",             "en": "Medulla"},
    "LO":  {"src": ["LO(L)", "LO(R)"],           "zh": "小叶",             "en": "Lobula"},
    "LOP": {"src": ["LOP(L)", "LOP(R)"],         "zh": "小叶板",           "en": "Lobula Plate"},
}
WANTED.pop("ALH", None)

# VNC 神经毡（来自 malecns-vnc-neuropil-roi-v0，名称已在桶中核实）
VNC_SETS = {
    "VNC-T1": {"src": ["LegNp(T1)(L)", "LegNp(T1)(R)", "mVAC(T1)(L)", "mVAC(T1)(R)",
                       "NTct(UTct-T1)(L)", "NTct(UTct-T1)(R)"],
               "zh": "前胸神经节 (T1)", "en": "Prothoracic Neuromere"},
    "VNC-T2": {"src": ["LegNp(T2)(L)", "LegNp(T2)(R)", "mVAC(T2)(L)", "mVAC(T2)(R)",
                       "WTct(UTct-T2)(L)", "WTct(UTct-T2)(R)"],
               "zh": "中胸神经节 (T2)", "en": "Mesothoracic Neuromere"},
    "VNC-T3": {"src": ["LegNp(T3)(L)", "LegNp(T3)(R)", "mVAC(T3)(L)", "mVAC(T3)(R)",
                       "HTct(UTct-T3)(L)", "HTct(UTct-T3)(R)"],
               "zh": "后胸神经节 (T3)", "en": "Metathoracic Neuromere"},
    "VNC-AB": {"src": ["ANm", "CV", "Ov(L)", "Ov(R)"],
               "zh": "腹部神经节区", "en": "Abdominal Neuromere"},
    "VNC-INT": {"src": ["IntTct", "LTct"],
                "zh": "节间连合区", "en": "Intersegmental Tectulum"},
}

# VNC 神经毡单独一个 ROI 图层；名称先在运行时发现
VNC_ROI = "malecns-vnc-neuropil-roi-v0"
BRAIN_ROI = "fullbrain-roi-v5"


def http_get(url, timeout=300):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_get_cached(url, path, timeout=300):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    data = http_get(url, timeout=timeout)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return data


def list_meshes(roi):
    """列出某 ROI 图层下的所有 .ngmesh"""
    out = []
    token = None
    pref = f"rois/{roi}/mesh/"
    while True:
        q = {"prefix": pref, "maxResults": "1000", "fields": "items(name,size),nextPageToken"}
        if token:
            q["pageToken"] = token
        url = GCS_API.format(bucket=BUCKET) + "?" + urllib.parse.urlencode(q)
        d = json.loads(http_get(url).decode("utf-8"))
        for it in d.get("items", []):
            n = it["name"]
            if n.endswith(".ngmesh"):
                out.append({"name": n, "size": int(it.get("size") or 0),
                            "key": n[len(pref):-len(".ngmesh")]})
        token = d.get("nextPageToken")
        if not token:
            break
    return out


def parse_ngmesh(buf):
    """neuroglancer legacy 单分辨率 mesh 片段格式。

    规范（https://neuroglancer-docs.web.app/datasource/precomputed/mesh.html）：
      uint32  num_vertices
      float32 positions[num_vertices * 3]      # 纳米，xyz 交错
      uint32  indices[...]                     # 三角形顶点索引，3 个一组
    三角形数 = 剩余字节数 / 12；**没有**「每顶点三角形数」数组。
    """
    if len(buf) < 4:
        raise ValueError("文件太短")
    nv, = struct.unpack_from("<I", buf, 0)
    pos_end = 4 + nv * 3 * 4
    if pos_end > len(buf):
        raise ValueError(f"顶点数据越界: 需要 {pos_end} 字节，文件只有 {len(buf)}")
    verts = struct.unpack_from(f"<{nv * 3}f", buf, 4)

    rest = len(buf) - pos_end
    if rest % 12 != 0:
        raise ValueError(f"索引字节数 {rest} 不是 12 的倍数")
    nt = rest // 12
    idx = struct.unpack_from(f"<{nt * 3}I", buf, pos_end)

    # 索引必须落在顶点范围内，否则是格式判断错了
    if nt and max(idx) >= nv:
        raise ValueError(f"索引越界: max={max(idx)} >= nv={nv}")
    return verts, idx


def merge(parts):
    """把多个 (verts, idx) 合并成一份，并计算法线与包围盒。"""
    V, I = [], []
    base = 0
    for verts, idx in parts:
        nv = len(verts) // 3
        V.extend(verts)
        I.extend(i + base for i in idx)
        base += nv
    nv = len(V) // 3
    nt = len(I) // 3
    # 顶点法线 = 相邻三角形法线按面积加权平均
    nrm = [0.0] * (nv * 3)
    for t in range(nt):
        a, b, c = I[t*3], I[t*3+1], I[t*3+2]
        ax, ay, az = V[a*3], V[a*3+1], V[a*3+2]
        bx, by, bz = V[b*3], V[b*3+1], V[b*3+2]
        cx, cy, cz = V[c*3], V[c*3+1], V[c*3+2]
        ux, uy, uz = bx-ax, by-ay, bz-az
        vx, vy, vz = cx-ax, cy-ay, cz-az
        nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
        for v in (a, b, c):
            nrm[v*3] += nx; nrm[v*3+1] += ny; nrm[v*3+2] += nz
    for v in range(nv):
        x, y, z = nrm[v*3], nrm[v*3+1], nrm[v*3+2]
        L = math.sqrt(x*x + y*y + z*z)
        if L > 1e-12:
            nrm[v*3] = x/L; nrm[v*3+1] = y/L; nrm[v*3+2] = z/L
    # 包围盒
    xs, ys, zs = V[0::3], V[1::3], V[2::3]
    bbox = [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]
    return V, nrm, I, bbox


def b64_f32(vals):
    return base64.b64encode(struct.pack(f"<{len(vals)}f", *vals)).decode("ascii")


def b64_u32(vals):
    return base64.b64encode(struct.pack(f"<{len(vals)}I", *vals)).decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="只列出可用网格")
    ap.add_argument("--only", default=None, help="只处理这些 key（逗号分隔）")
    a = ap.parse_args()

    brain = {m["key"]: m for m in list_meshes(BRAIN_ROI)}
    print(f"脑神经毡网格: {len(brain)} 个, 合计 {sum(m['size'] for m in brain.values())/1e6:.1f} MB")
    vnc = {m["key"]: m for m in list_meshes(VNC_ROI)}
    print(f"VNC 神经毡网格: {len(vnc)} 个, 合计 {sum(m['size'] for m in vnc.values())/1e6:.1f} MB")
    if a.list:
        print("\n脑:", ", ".join(sorted(brain)))
        print("\nVNC:", ", ".join(sorted(vnc)))
        return

    only = set(a.only.split(",")) if a.only else None

    # 把 VNC 结构并进 WANTED
    for key, spec in VNC_SETS.items():
        WANTED[key] = spec
    # 记录每个 source 属于哪个图层
    layer_of = {}
    for m in brain.values():
        layer_of[m["key"]] = BRAIN_ROI
    for m in vnc.values():
        layer_of[m["key"]] = VNC_ROI
    all_meshes = dict(vnc)
    all_meshes.update(brain)

    bundle = {}
    used_bytes = 0
    for key, spec in WANTED.items():
        if only and key not in only:
            continue
        srcs = spec.get("src", [])
        parts = []
        got = []
        for s in srcs:
            if s not in all_meshes:
                continue
            roi = layer_of[s]
            p = os.path.join(CACHE, roi, s + ".ngmesh")
            buf = http_get_cached(GCS_OBJ.format(bucket=BUCKET, name=all_meshes[s]["name"]), p)
            used_bytes += len(buf)
            try:
                parts.append(parse_ngmesh(buf))
                got.append(s)
            except Exception as e:
                print(f"  !! {key} <- {s} 解析失败: {e}")
        if not parts:
            print(f"  -- {key}: 没有可用源 ({','.join(srcs)})")
            continue
        V, N, I, bbox = merge(parts)
        bundle[key] = {
            "zh": spec.get("zh", key), "en": spec.get("en", ""),
            "src": got,
            "tris": len(I) // 3,
            "bbox": [round(b, 1) for b in bbox],
            "v": b64_f32(V), "n": b64_f32(N), "i": b64_u32(I),
        }
        print(f"  {key:8s} {len(V)//3:>7,} v  {len(I)//3:>7,} tri  "
              f"from {len(parts)} mesh(es): {','.join(got)}")

    meta = {
        "source": f"gs://{BUCKET}/rois/{BRAIN_ROI}/mesh/  (neuroglancer_legacy_mesh)",
        "roi_layer": BRAIN_ROI,
        "license": "CC-BY 4.0 — FlyEM / HHMI Janelia",
        "citation": "Berg et al. (2026) Cell 189(18):5504-5526.e15",
        "units": "nm (原始坐标)",
        "downloaded_bytes": used_bytes,
        "structures": len(bundle),
    }
    js = ("/* 自动生成：tools/fetch_official_meshes.py —— 请勿手改。\n"
          "   数据来源：官方 MaleCNS ROI 网格（CC-BY 4.0, FlyEM/HHMI Janelia）。\n"
          "   坐标为原始纳米坐标。 */\n"
          "window.MCNS_MESHES = " + json.dumps({"meta": meta, **bundle}, ensure_ascii=False) + ";\n")
    os.makedirs(os.path.dirname(OUT_JS), exist_ok=True)
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"\n写出 {OUT_JS}  ({os.path.getsize(OUT_JS)/1e6:.2f} MB)")
    print(f"  结构数 {len(bundle)}，下载 {used_bytes/1e6:.1f} MB，"
          f"三角形合计 {sum(b['tris'] for b in bundle.values()):,}")


if __name__ == "__main__":
    main()
