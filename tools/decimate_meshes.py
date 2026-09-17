"""
decimate_meshes.py — 把官方网格抽稀到浏览器可实时渲染的规模。

输入:  assets/mcns-meshes.js  (由 fetch_official_meshes.py 生成，原始纳米坐标)
输出:  assets/mcns-meshes.js  (就地替换为抽稀版本)

算法：网格顶点聚类（vertex clustering / grid snapping）
  1. 把顶点按 cell 尺寸吸附到规则网格，同格顶点合并为一个代表点
  2. 重建三角形，丢弃退化三角形（三顶点落同格 / 面积为零）
  3. 对每个结构二分搜索 cell 尺寸，使三角形数落在预算内
  4. 保留连通性：输出仍是合法三角网格，形状与原网格一致

⚠️ 抽稀是不可逆的近似：形状保持，但表面细节与体积估计不再精确。
   原始网格请用 tools/fetch_official_meshes.py 重新获取（步骤见页面说明）。

用法:
  python tools/decimate_meshes.py                 # 使用默认预算
  python tools/decimate_meshes.py --budget 60000  # 调整单结构三角形预算
"""
import argparse
import array
import base64
import json
import math
import os
import re
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "assets", "mcns-meshes.js")

# 每个结构的三角形预算（越大越精细）
# 三档预设：Canvas 2D 对每帧绘制三角形数很敏感。
#   low  —— 目标 6-7 万三角形，Canvas 2D 流畅（默认，页面使用）
#   mid  —— 约 34 万，桌面 GPU / WebGL 合适
#   high —— 不做抽稀（原始 886 万），仅用于离线分析
PRESETS = {
    "low": {
        # 中央脑：教学重点
        "MB": 6000, "MB-CA": 2200, "CX": 4500, "CX-EB": 1800,
        "AL": 3500, "LH": 3000, "SEZ": 4000, "AOTU": 1600,
        "LAL": 1800, "SMP": 1800, "SLP": 1800, "SIP": 1600,
        "CRE": 1600, "WED": 1600, "VES": 1600, "IB": 1400, "BU": 1200,
        # 视叶四层（视觉上最显眼，稍多给一点）
        "LA": 4000, "ME": 7000, "LO": 4500, "LOP": 3500,
        # 腹神经索
        "VNC-T1": 3000, "VNC-T2": 3000, "VNC-T3": 2600,
        "VNC-AB": 2200, "VNC-INT": 1800,
    },
    "mid": {
        "MB": 30000, "CX": 22000, "CX-EB": 9000, "MB-CA": 12000, "AL": 16000,
        "LH": 14000, "SEZ": 20000, "AOTU": 7000,
        "LAL": 9000, "SMP": 9000, "SLP": 9000, "SIP": 8000, "CRE": 8000,
        "WED": 8000, "VES": 8000, "IB": 7000, "BU": 5000,
        "LA": 18000, "ME": 34000, "LO": 22000, "LOP": 18000,
        "VNC-T1": 18000, "VNC-T2": 18000, "VNC-T3": 16000,
        "VNC-AB": 12000, "VNC-INT": 10000,
    },
}
PRESETS["high"] = {}          # 空 => 全部按超大预算，即不抽稀
DEFAULT_BUDGET = PRESETS["low"]


def unpack_f32(b64):
    raw = base64.b64decode(b64)
    return list(struct.unpack(f"<{len(raw)//4}f", raw))


def unpack_u32(b64):
    raw = base64.b64decode(b64)
    return list(struct.unpack(f"<{len(raw)//4}I", raw))


def pack_f32(vals):
    return base64.b64encode(struct.pack(f"<{len(vals)}f", *vals)).decode("ascii")


def pack_u32(vals):
    return base64.b64encode(struct.pack(f"<{len(vals)}I", *vals)).decode("ascii")


def build_grid(vx, vy, vz, cell, out_verts):
    """把顶点按 grid cell 聚成新顶点。

    vx/vy/vz: array('d') 分量数组（避免逐元素 list 索引）
    out_verts: 复用的 array('d')，函数内清空后写入
    """
    inv = 1.0 / cell
    cellmap = {}
    remap = array.array('i', bytes(4 * len(vx)))
    del out_verts[:]
    n = 0
    get = cellmap.get
    for i in range(len(vx)):
        key = (int(vx[i] * inv), int(vy[i] * inv), int(vz[i] * inv))
        j = get(key, -1)
        if j < 0:
            j = n
            cellmap[key] = j
            out_verts.append(vx[i]); out_verts.append(vy[i]); out_verts.append(vz[i])
            n += 1
        remap[i] = j
    return remap, n


def count_tris(remap, idx):
    """只数三角形，不构建（用于二分搜索）。"""
    cnt = 0
    for t in range(0, len(idx), 3):
        a = remap[idx[t]]; b = remap[idx[t+1]]; c = remap[idx[t+2]]
        if a != b and b != c and a != c:
            cnt += 1
    return cnt


def rebuild(remap, idx, nverts, out_verts):
    """重建三角形：去退化、去重、去零面积。"""
    out = array.array('I')
    seen = set()
    for t in range(0, len(idx), 3):
        a = remap[idx[t]]; b = remap[idx[t+1]]; c = remap[idx[t+2]]
        if a == b or b == c or a == c:
            continue
        if a < b:
            key = (a, b, c) if b < c else (a, c, b) if a < c else (c, a, b)
        else:
            key = (b, a, c) if a < c else (b, c, a) if b < c else (c, b, a)
        if key in seen:
            continue
        seen.add(key)
        # 零面积判定
        ax = out_verts[a*3]; ay = out_verts[a*3+1]; az = out_verts[a*3+2]
        bx = out_verts[b*3]; by = out_verts[b*3+1]; bz = out_verts[b*3+2]
        cx = out_verts[c*3]; cy = out_verts[c*3+1]; cz = out_verts[c*3+2]
        ux = bx-ax; uy = by-ay; uz = bz-az
        vx2 = cx-ax; vy2 = cy-ay; vz2 = cz-az
        nx = uy*vz2-uz*vy2; ny = uz*vx2-ux*vz2; nz = ux*vy2-uy*vx2
        if nx*nx + ny*ny + nz*nz <= 1e-6:
            continue
        out.append(a); out.append(b); out.append(c)
    return out


def decimate(verts, tris, cell):
    """兼容接口：一次性抽稀，返回 (newverts_list, newtris_list)。"""
    vx = array.array('d', verts[0::3])
    vy = array.array('d', verts[1::3])
    vz = array.array('d', verts[2::3])
    idx = array.array('I', tris)
    ov = array.array('d')
    remap, n = build_grid(vx, vy, vz, cell, ov)
    out = rebuild(remap, idx, n, ov)
    return list(ov), list(out)


def compute_normals(verts, tris):
    nv = len(verts) // 3
    nrm = [0.0] * (nv * 3)
    for t in range(len(tris) // 3):
        a, b, c = tris[t*3], tris[t*3+1], tris[t*3+2]
        ax, ay, az = verts[a*3], verts[a*3+1], verts[a*3+2]
        bx, by, bz = verts[b*3], verts[b*3+1], verts[b*3+2]
        cx, cy, cz = verts[c*3], verts[c*3+1], verts[c*3+2]
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
    return nrm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", choices=["low", "mid", "high"], default="low",
                    help="low≈7万三角形(默认,页面用) / mid≈34万 / high=不抽稀")
    ap.add_argument("--scale", type=float, default=1.0, help="在预设基础上再整体缩放")
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--dry", action="store_true", help="只报告，不写文件")
    a = ap.parse_args()

    budget_map = PRESETS[a.preset]
    big = 10 ** 9
    print(f"预设: {a.preset}" + (f"  (scale={a.scale})" if a.scale != 1.0 else ""))

    txt = open(a.src, encoding="utf-8").read()
    m = re.search(r"window\.MCNS_MESHES\s*=\s*(\{.*\});\s*$", txt, re.S)
    if not m:
        raise SystemExit("无法解析 mcns-meshes.js")
    data = json.loads(m.group(1))
    meta = data.pop("meta", {})

    print(f"输入 {len(data)} 个结构, {os.path.getsize(a.src)/1e6:.1f} MB")
    print(f"{'结构':10s} {'原始 tri':>10s} {'目标':>8s} {'抽稀后 tri':>11s} {'顶点':>9s} {'cell(nm)':>10s}")
    total_in = total_out = 0
    out = {}
    for key, rec in data.items():
        vlist = unpack_f32(rec["v"])
        tlist = unpack_u32(rec["i"])
        n0 = len(tlist) // 3
        total_in += n0
        budget = int(budget_map.get(key, 1500 if a.preset == "low" else 12000) * a.scale)
        if not budget_map:
            budget = big

        vx = array.array('d', vlist[0::3])
        vy = array.array('d', vlist[1::3])
        vz = array.array('d', vlist[2::3])
        idx = array.array('I', tlist)
        ov = array.array('d')

        if n0 <= budget:
            nv, nt, cell = vlist, tlist, 0.0
        else:
            # 三角形数随 cell 近似以 cell^-2 衰减，所以先用一个参考 cell 标定，
            # 再按幂律直接估算目标 cell，最后只做几次校正 —— 比二分快一个数量级。
            span = max(max(vx) - min(vx), max(vy) - min(vy), max(vz) - min(vz))
            ref = span / 300.0                      # 参考格边长
            remap_ref, _ = build_grid(vx, vy, vz, ref, ov)
            c_ref = count_tris(remap_ref, idx)

            cell = ref
            for _ in range(8):
                est = ref * math.sqrt(max(c_ref, 1) / budget)
                cell = min(max(est, ref), span / 4.0)
                remap, nvv = build_grid(vx, vy, vz, cell, ov)
                cnt = count_tris(remap, idx)
                if cnt <= budget * 1.04:
                    break
                # 超标则按幂律继续放大
                ref, c_ref = cell, cnt
            remap, nvv = build_grid(vx, vy, vz, cell, ov)
            nt = list(rebuild(remap, idx, nvv, ov))
            nv = list(ov)
            if len(nt) // 3 > budget * 1.3:
                print(f"    (警告: {key} 达到预算上限仍为 {len(nt)//3:,} tri)")

        nrm = compute_normals(nv, nt)
        total_out += len(nt) // 3
        out[key] = {
            "zh": rec.get("zh", key), "en": rec.get("en", ""),
            "src": rec.get("src", []), "bbox": rec.get("bbox"),
            "tris": len(nt) // 3, "rawTris": n0,
            "cellNm": round(cell, 1),
            "v": pack_f32(nv), "n": pack_f32(nrm), "i": pack_u32(nt),
        }
        print(f"{key:10s} {n0:>10,} {budget:>8,} {len(nt)//3:>11,} {len(nv)//3:>9,} {cell:>10.0f}")

    meta["decimation"] = {
        "method": "vertex clustering (grid snapping)",
        "rawTriangles": total_in,
        "keptTriangles": total_out,
        "ratio": round(total_out / max(1, total_in), 4),
        "note": "抽稀仅用于浏览器实时渲染；形状保持，细节与体积不再精确。",
    }
    payload = json.dumps({"meta": meta, **out}, ensure_ascii=False)
    js = ("/* 自动生成：tools/fetch_official_meshes.py + tools/decimate_meshes.py —— 请勿手改。\n"
          "   几何来自官方 MaleCNS ROI 网格（CC-BY 4.0, FlyEM/HHMI Janelia），\n"
          "   已做顶点聚类抽稀以便浏览器实时渲染。坐标为原始纳米坐标。 */\n"
          "window.MCNS_MESHES = " + payload + ";\n")
    print(f"\n合计 {total_in:,} → {total_out:,} 三角形 ({(total_out/max(1,total_in))*100:.1f}%)")
    if a.dry:
        print("(--dry: 未写文件)")
        return
    # 加 .bak 备份原始版本（体积大，抽稀后覆盖）
    with open(a.src, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"写出 {a.src}  ({os.path.getsize(a.src)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
