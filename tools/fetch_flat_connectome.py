"""
fetch_flat_connectome.py — 下载阶段 3 需要的 MaleCNS flat-connectome 文件。

为什么值得单独写一个脚本，而不是页面里那几行 urlretrieve：
  1) 大文件必须能续传。连接矩阵有 1 GB，下到 90% 断掉重来是常事，
     HTTP Range 续传是基本要求。
  2) 必须校验完整性。下载被截断、或官方静默更新了文件，
     都会表现为「代码算出来的数和网页对不上」——
     而你会先去怀疑自己的代码。用官方 MD5 一验就知道是谁的问题。
  3) 目录要和 .gitignore 对齐（_data/），否则 1 GB 文件会被 git 收进去。

官方文件清单（11 个文件，合计约 28 GB）：
  阶段 3 只需要其中 2 个 —— 细胞注释 + 连接权重，合计约 1.1 GB。
  全量清单用 --list 看。

用法：
    python tools/fetch_flat_connectome.py            # 下载 + 校验（默认 2 个文件）
    python tools/fetch_flat_connectome.py --verify   # 只校验已有的文件
    python tools/fetch_flat_connectome.py --list     # 打印官方目录清单
    python tools/fetch_flat_connectome.py --all      # 下载全部（约 28 GB，慎用）
"""
from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "_data")

PREFIX = "v1.0/connectome-data/flat-connectome/"
LIST_URL = ("https://storage.googleapis.com/flyem-male-cns"
            "?prefix=" + PREFIX + "&maxResults=1000")
BASE = "https://storage.googleapis.com/flyem-male-cns/" + PREFIX

# 阶段 3 真正需要的两个（约 1.1 GB）。
# 连接矩阵是 7 个候选文件里最"全"的一个：另外两个 *-traced-only /
# *-significant-only 是它的子集，syn-* 那两个则是突触级明细（6.8 GB / 13 GB）。
NEEDED = [
    "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
]


def human(n: int) -> str:
    return f"{n / 1048576:.1f} MB" if n < 1 << 30 else f"{n / (1 << 30):.2f} GB"


def list_objects() -> "dict[str, dict]":
    """读官方 bucket 清单，返回 {文件名: {size, md5}}。

    用清单里的 Hash 当 MD5 —— 单段上传的对象，ETag/Hash 就是内容的 MD5，
    这是不信任本地副本、也不需要下载两次就能校验的唯一办法。
    """
    with urllib.request.urlopen(LIST_URL, timeout=60) as r:
        xml = r.read()
    root = ET.fromstring(xml)
    out = {}
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag != "Contents":
            continue
        info = {}
        for child in node:
            ctag = child.tag.rsplit("}", 1)[-1]
            if ctag in ("Key", "Size", "Hash", "ETag"):
                info[ctag] = (child.text or "").strip().strip('"')
        name = info.get("Key", "").rsplit("/", 1)[-1]
        if name:
            out[name] = {"size": int(info.get("Size", 0)),
                         "md5": (info.get("Hash") or info.get("ETag", "")).lower()}
    return out


def md5_of(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(name: str, meta: dict) -> bool:
    """核对本地文件的大小与 MD5。"""
    path = os.path.join(OUTDIR, name)
    if not os.path.isfile(path):
        print(f"  ✗ 缺失  {name}")
        return False
    size = os.path.getsize(path)
    if meta["size"] and size != meta["size"]:
        print(f"  ✗ 大小不对  {name}：{size:,} ≠ 官方 {meta['size']:,}")
        return False
    got = md5_of(path)
    if meta["md5"] and got != meta["md5"]:
        print(f"  ✗ MD5 不匹配  {name}\n      本地 {got}\n      官方 {meta['md5']}")
        return False
    print(f"  ✓ {name}  {human(size)}  MD5 {got}")
    return True


def download(name: str, meta: dict) -> None:
    """带续传的下载；下完就地校验。"""
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, name)
    done = os.path.getsize(path) if os.path.exists(path) else 0

    if done and meta["size"] and done == meta["size"]:
        print(f"  已存在且大小一致，直接校验：{name}")
        return
    if done and meta["size"] and done > meta["size"]:
        print(f"  本地文件比官方还大，多半是坏的，重新下载：{name}")
        os.remove(path)
        done = 0

    req = urllib.request.Request(BASE + name)
    mode = "wb"
    if done:
        req.add_header("Range", f"bytes={done}-")
        mode = "ab"
        print(f"  续传 {name}（从 {human(done)} 开始）")
    else:
        print(f"  下载 {name}（{human(meta['size'])}）")

    with urllib.request.urlopen(req, timeout=120) as r, open(path, mode) as f:
        got = done
        step = 1 << 22
        while True:
            chunk = r.read(step)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if meta["size"]:
                pct = got / meta["size"] * 100
                sys.stdout.write(f"\r    {pct:5.1f}%  {human(got)} / {human(meta['size'])}")
                sys.stdout.flush()
    sys.stdout.write("\r" + " " * 60 + "\r")


def main() -> int:
    args = set(sys.argv[1:])
    print("读取官方 bucket 清单…")
    try:
        objects = list_objects()
    except Exception as e:                                    # noqa: BLE001
        print(f"  ✗ 拿不到清单：{e}")
        return 2
    print(f"  官方 {PREFIX} 下共 {len(objects)} 个文件，"
          f"合计 {human(sum(v['size'] for v in objects.values()))}\n")

    if "--list" in args:
        for name in sorted(objects, key=lambda n: -objects[n]["size"]):
            mark = "  ← 阶段 3 需要" if name in NEEDED else ""
            print(f"  {human(objects[name]['size']):>10}  {name}{mark}")
        return 0

    wanted = sorted(objects) if "--all" in args else NEEDED
    missing = [n for n in wanted if n not in objects]
    if missing:
        print("  ✗ 官方清单里找不到：" + "、".join(missing))
        return 2

    if "--verify" not in args:
        total = sum(objects[n]["size"] for n in wanted
                    if not os.path.exists(os.path.join(OUTDIR, n)))
        print(f"待下载 {human(total)}\n" if total else "文件都在本地，跳过下载\n")
        for name in wanted:
            download(name, objects[name])
            print()

    print("校验：")
    return 0 if all(verify(n, objects[n]) for n in wanted) else 1


if __name__ == "__main__":
    sys.exit(main())
