"""
fetch_roi_volume.py — 从官方 MaleCNS GCS 桶下载 ROI 分割体并解码。

数据来源（官方，无需登录）：
  gs://flyem-male-cns/rois/fullbrain-roi-v5/          # 脑神经毡 ROI（84 个）
  gs://flyem-male-cns/rois/malecns-vnc-neuropil-roi-v0/  # VNC 神经毡（23 个）

格式为 Neuroglancer "precomputed" 分割体：
  <scale_key>/<x0-x1>_<y0-y1>_<z0-z1>   每个 chunk 用 compressed_segmentation 编码

本脚本：
  1. 读 /info 取尺度与尺寸
  2. 列出某尺度下所有 chunk 并从 GCS 下载（带磁盘缓存）
  3. 解码 compressed_segmentation（8x8x8 块，16 位或 32 位 raw 索引）
  4. 输出 numpy 体数据 .npy 供 build_roi_meshes.py 做 marching cubes

用法:
  python tools/fetch_roi_volume.py --roi fullbrain-roi-v5 --scale 1024_1024_1024
"""
import argparse
import json
import os
import struct
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BUCKET = "flyem-male-cns"
GCS_API = "https://storage.googleapis.com/storage/v1/b/{bucket}/o"
GCS_OBJ = "https://storage.googleapis.com/{bucket}/{name}"
UA = {"User-Agent": "mcns-study/1.0"}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "_official", "chunks")
OUT = os.path.join(ROOT, "_official")


def http_get(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_get_cached(url, path, timeout=180):
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as f:
            return f.read()
    data = http_get(url, timeout=timeout)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return data


def list_objects(prefix):
    """列出 bucket 中某前缀下的所有对象（分页）。"""
    out = []
    token = None
    while True:
        q = {"prefix": prefix, "maxResults": "1000", "fields": "items(name,size),nextPageToken"}
        if token:
            q["pageToken"] = token
        url = GCS_API.format(bucket=BUCKET) + "?" + urllib.parse.urlencode(q)
        d = json.loads(http_get(url).decode("utf-8"))
        out.extend(d.get("items", []))
        token = d.get("nextPageToken")
        if not token:
            break
    return out


def read_info(roi):
    url = GCS_OBJ.format(bucket=BUCKET, name=f"rois/{roi}/info")
    return json.loads(http_get(url).decode("utf-8"))


# ----------------------------------------------------------------------
# compressed_segmentation 解码
# ----------------------------------------------------------------------
def decode_chunk(buf, data_type, block_size):
    """返回 (values_voxels, shape) 的扁平列表 + 各维块数。

    布局: uint32 num_encoded_values
          (uint32 * num_encoded_values if uint32 else uint16 * n)  每个 8x8x8 块一个调色板
          (uint32 or uint16) * 512 * num_encoded_values            块内索引
    """
    pos = 0
    n_enc, = struct.unpack_from("<I", buf, pos)
    pos += 4
    idx_dtype = "<I" if data_type == "uint32" else "<H"
    idx_size = 4 if data_type == "uint32" else 2

    palette = list(struct.unpack_from(f"<{n_enc}{idx_dtype[1]}", buf, pos))
    pos += n_enc * idx_size

    per_block = block_size[0] * block_size[1] * block_size[2]
    n_blocks = len(buf[pos:]) // (per_block * idx_size)
    blocks = []
    for b in range(n_blocks):
        vals = struct.unpack_from(f"<{per_block}{idx_dtype[1]}", buf, pos + b * per_block * idx_size)
        blocks.append(vals)
    return palette, blocks


def assemble(roi, scale_key, verbose=True):
    info = read_info(roi)
    scale = None
    for s in info["scales"]:
        if s["key"] == scale_key:
            scale = s
            break
    if scale is None:
        raise SystemExit(f"尺度 {scale_key} 不存在；可用: {[s['key'] for s in info['scales']]}")

    res = scale["resolution"]
    size = scale["size"]
    chunk = scale["chunk_sizes"][0]
    block = scale.get("compressed_segmentation_block_size", [8, 8, 8])
    data_type = info["data_type"]
    if verbose:
        print(f"ROI={roi} scale={scale_key} data_type={data_type}")
        print(f"  resolution={res} size={size} chunk={chunk} block={block}")
        print(f"  体素总数 = {size[0]*size[1]*size[2]:,}")

    objs = list_objects(f"rois/{roi}/{scale_key}/")
    if verbose:
        total = sum(int(o.get("size") or 0) for o in objs)
        print(f"  chunk 数 = {len(objs)}, 合计 {total/1e6:.2f} MB")
    if not objs:
        raise SystemExit("没有找到任何 chunk")

    try:
        import numpy as np
    except ImportError:
        raise SystemExit("需要 numpy: pip install numpy")

    vol = np.zeros((size[2], size[1], size[0]), dtype=np.uint64)
    nz_chunks = 0
    for k, o in enumerate(objs):
        name = o["name"]
        coords = name.rsplit("/", 1)[-1]
        try:
            xs, ys, zs = coords.split("_")
            x0, x1 = (int(v) for v in xs.split("-"))
            y0, y1 = (int(v) for v in ys.split("-"))
            z0, z1 = (int(v) for v in zs.split("-"))
        except Exception:
            continue
        local = name[len(f"rois/{roi}/{scale_key}/"):]
        path = os.path.join(CACHE, roi, scale_key, local.replace("/", "__"))
        buf = http_get_cached(GCS_OBJ.format(bucket=BUCKET, name=name), path)
        palette, blocks = decode_chunk(buf, data_type, block)
        if not palette or not any(palette):
            continue
        nz_chunks += 1
        # 每块 8x8x8，按 z,y,x 展开到体数据
        nx = (x1 - x0) // block[0]
        ny = (y1 - y0) // block[1]
        bi = 0
        for bz in range(nz := (z1 - z0) // block[2]):
            for by in range(ny):
                for bx in range(nx):
                    if bi >= len(blocks):
                        break
                    vals = blocks[bi]
                    bi += 1
                    arr = np.array(vals, dtype=np.uint64).reshape(block[2], block[1], block[0])
                    arr = np.where(arr < len(palette), np.array(palette, dtype=np.uint64)[arr], 0)
                    zz = z0 + bz * block[2]
                    yy = y0 + by * block[1]
                    xx = x0 + bx * block[0]
                    vol[zz:zz + block[2], yy:yy + block[1], xx:xx + block[0]] = arr
        if verbose and (k + 1) % 40 == 0:
            print(f"    已处理 {k+1}/{len(objs)} chunk")

    if verbose:
        print(f"  非空 chunk = {nz_chunks}")
        ids, counts = np.unique(vol, return_counts=True)
        print(f"  出现的标签数 = {len(ids)}")
        order = np.argsort(-counts)
        print("  体素最多的 15 个标签:")
        for i in order[:15]:
            print(f"    id={ids[i]:<6} voxels={counts[i]:,}")

    out = os.path.join(OUT, f"vol-{roi}-{scale_key}.npy")
    np.save(out, vol)
    print(f"  写出 {out}  ({os.path.getsize(out)/1e6:.2f} MB)")

    # 同时保存 label -> 名称 映射
    props_url = GCS_OBJ.format(bucket=BUCKET, name=f"rois/{roi}/segment_properties/info")
    props = json.loads(http_get(props_url).decode("utf-8"))
    ids_list = props["inline"]["ids"]
    label_prop = None
    for p in props["inline"].get("properties", []):
        if p.get("type") == "label":
            label_prop = p
            break
    if label_prop:
        mapping = {int(i): v for i, v in zip(ids_list, label_prop["values"])}
        mp = os.path.join(OUT, f"labels-{roi}.json")
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=1)
        print(f"  写出 {mp}  ({len(mapping)} 个标签)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roi", default="fullbrain-roi-v5")
    ap.add_argument("--scale", default="1024_1024_1024")
    a = ap.parse_args()
    assemble(a.roi, a.scale)


if __name__ == "__main__":
    main()
