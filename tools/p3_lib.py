"""
p3_lib.py — 阶段 3「拿数据 + 第一段代码」的可执行库。

设计原则（三条，都是踩出来的）：
  1) 只用 requests 直调 neuPrint 的匿名只读 API —— 不需要 token，
     也不需要 neuprint-python（少装一个包就少一个坑）。
  2) 每个查询都显式写清「阈值口径」—— 阈值是分析选择，不是数据属性。
  3) 网络不稳时要有明确的重试与错误信息（neuPrint 会偶发 502）。

用法：
    from p3_lib import connect, q, fetch_edges, build_matrix, degrees
    c = connect()
    print(c.count("MATCH (n:Neuron) RETURN count(n)"))
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

ENDPOINT = "https://neuprint.janelia.org/api/custom/custom"
DATASET = "male-cns:v1.0"

# 论文/门户的默认阈值口径（阶段 2 的结论）
DEFAULT_MIN_WEIGHT = 5


# ======================================================================
# 1. 最小可用的 API 客户端
# ======================================================================
class NeuprintError(RuntimeError):
    pass


class Client:
    """neuPrint 匿名客户端：POST 一段 Cypher，拿回 columns/data。"""

    def __init__(self, endpoint: str = ENDPOINT, dataset: str = DATASET,
                 timeout: int = 300, retries: int = 3, verbose: bool = False):
        self.endpoint = endpoint
        self.dataset = dataset
        self.timeout = timeout
        self.retries = retries
        self.verbose = verbose
        self.calls = 0
        self.seconds = 0.0

    def raw(self, cypher: str) -> Dict[str, Any]:
        if requests is None:
            raise NeuprintError("需要 requests：pip install requests")
        body = {"cypher": cypher, "dataset": self.dataset}
        last: Optional[str] = None
        for attempt in range(self.retries):
            t0 = time.time()
            try:
                r = requests.post(self.endpoint, json=body, timeout=self.timeout)
                self.calls += 1
                self.seconds += time.time() - t0
                if self.verbose:
                    print(f"    [{self.calls}] {time.time()-t0:5.1f}s "
                          f"HTTP {r.status_code}  {cypher[:60]}…")
                if r.status_code == 200:
                    return r.json()
                # 502/503/504 是网关侧的临时故障，值得重试
                last = f"HTTP {r.status_code}: {r.text[:200]}"
                if r.status_code not in (429, 502, 503, 504):
                    break
            except Exception as e:
                self.seconds += time.time() - t0
                last = f"{type(e).__name__}: {e}"
            time.sleep(3 * (attempt + 1))
        raise NeuprintError(
            f"neuPrint 请求失败（{self.retries} 次重试后）：{last}\n"
            f"  查询：{cypher.strip()[:200]}\n"
            f"  排查：① 网络能否访问 neuprint.janelia.org；"
            f"② 服务器是否在维护（502/503 是网关故障，与本机无关）；"
            f"③ 查询是否过重（加 WHERE 或 LIMIT）。")

    def rows(self, cypher: str) -> List[List[Any]]:
        return self.raw(cypher).get("data") or []

    def table(self, cypher: str) -> Tuple[List[str], List[List[Any]]]:
        j = self.raw(cypher)
        return j.get("columns") or [], j.get("data") or []

    def one(self, cypher: str) -> Any:
        rows = self.rows(cypher)
        return rows[0][0] if rows and rows[0] else None

    def count(self, cypher: str) -> int:
        v = self.one(cypher)
        return int(v) if v is not None else 0


def connect(dataset: str = DATASET, **kw) -> Client:
    return Client(dataset=dataset, **kw)


def q(client: Client, cypher: str) -> List[List[Any]]:
    return client.rows(cypher)


def ping(client: Optional[Client] = None) -> Tuple[bool, str]:
    """连通性自检 —— 阶段 3 的第一步就该跑这个。"""
    c = client or connect(retries=1)
    try:
        n = c.count("MATCH (n:Neuron) RETURN count(n)")
        return True, f"neuPrint 可用，:Neuron 节点数 = {n:,}"
    except Exception as e:
        return False, f"neuPrint 不可用：{str(e)[:200]}"


# ======================================================================
# 2. 从"连接表"建稀疏矩阵
# ======================================================================
def fetch_edges(client: Client,
                types: Optional[Sequence[str]] = None,
                min_weight: int = DEFAULT_MIN_WEIGHT,
                limit: Optional[int] = None,
                ) -> Tuple[List[int], List[int], List[int]]:
    """取 (src_bodyId, dst_bodyId, weight) 三元组。

    两个必须显式记住的口径（阶段 2 的结论）：
      · 阈值：neuPrint/Codex 默认「≥5 个突触才算一条连接」。
        但**同一对神经元换阈值，突触总数也会变**：
        例如 R1-R6→L2 不设阈值是 107,646，≥5 之后是 107,572。
        所以永远把这个数写成参数、写进结论。
      · 连接 vs 接触：`r.weight` 是突触数；一个突触前位点可对接多个
        突触后位点（多目标突触），所以"接触点数"会大于"连接数"。
    """
    where = []
    if types:
        where.append("a.type IN %s" % json.dumps(list(types)))
    if min_weight:
        where.append("r.weight >= %d" % int(min_weight))
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    lim = ("LIMIT %d" % int(limit)) if limit else ""
    cypher = (f"MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron) {clause} "
              f"RETURN a.bodyId, b.bodyId, r.weight {lim}").strip()

    src, dst, w = [], [], []
    for row in client.rows(cypher):
        src.append(int(row[0]))
        dst.append(int(row[1]))
        w.append(int(row[2]))
    return src, dst, w


def build_matrix(src: Sequence[int], dst: Sequence[int], w: Sequence[int]):
    """把三元组变成 scipy 稀疏矩阵 + 索引映射。

    关键点：**bodyId 不是从 0 开始的连续整数**（例如 11074、512006）。
    直接拿它当矩阵下标会浪费（矩阵边长由最大 ID 决定，约 90 万，
    而实际只有十几万神经元）。所以先建 bodyId → 0..N-1 的映射。
    """
    if np is None:
        raise RuntimeError("需要 numpy/scipy")
    from scipy.sparse import csr_matrix

    ids = sorted(set(src) | set(dst))
    idx = {b: i for i, b in enumerate(ids)}
    rows = [idx[s] for s in src]
    cols = [idx[d] for d in dst]
    M = csr_matrix((np.asarray(w, dtype=np.int64), (rows, cols)),
                   shape=(len(ids), len(ids)))
    return M, ids, idx


def degrees(M, ids: Sequence[int]) -> Dict[str, Dict[int, int]]:
    """算出度/入度。

    定义（与论文一致，别混）：
      · **度 = 伙伴数**（不是突触数）—— 出度 = 下游伙伴数
      · **突触数** = 权重之和
    阶段 2 论文里"内禀神经元入/出度中位数 ≈ 11 / 13"说的是**伙伴数**。
    """
    if np is None:
        raise RuntimeError("需要 numpy/scipy")
    nz = (M != 0)
    out_d = np.asarray(nz.sum(axis=1)).ravel()
    in_d = np.asarray(nz.sum(axis=0)).ravel()
    out_w = np.asarray(M.sum(axis=1)).ravel()
    in_w = np.asarray(M.sum(axis=0)).ravel()
    return {
        "out_partners": {ids[i]: int(out_d[i]) for i in range(len(ids))},
        "in_partners": {ids[i]: int(in_d[i]) for i in range(len(ids))},
        "out_synapses": {ids[i]: int(out_w[i]) for i in range(len(ids))},
        "in_synapses": {ids[i]: int(in_w[i]) for i in range(len(ids))},
    }


# ======================================================================
# 3. 通路查询（阶段 1 走的那两条）
# ======================================================================
def top_downstream(client: Client, body_id: int, limit: int = 10,
                   min_weight: int = DEFAULT_MIN_WEIGHT
                   ) -> List[Tuple[str, int, int, int]]:
    """某神经元最主要的下游类型（按类型聚合）。

    返回 [(type, 目标个数, 突触总数, 单条最大突触数), …]
    """
    cypher = (f"MATCH (a:Neuron {{bodyId: {int(body_id)}}})-[r:ConnectsTo]->(b:Neuron) "
              f"WHERE r.weight >= {int(min_weight)} "
              f"RETURN b.type, count(*) AS n, sum(r.weight) AS w, max(r.weight) AS wmax "
              f"ORDER BY w DESC LIMIT {int(limit)}")
    return [(r[0], int(r[1]), int(r[2]), int(r[3])) for r in client.rows(cypher)]


def type_to_type(client: Client, src_type: str, dst_prefix: str = "",
                 dst_type: str = "", limit: int = 12,
                 min_weight: int = DEFAULT_MIN_WEIGHT
                 ) -> List[Tuple[str, int, int]]:
    """类型 → 类型：聚合突触数与边数。

    `dst_type` 用来精确锁定一对类型（做"同一条连接换阈值"的对照）。
    """
    extra = ""
    if dst_type:
        extra += f" AND b.type = '{dst_type}'"
    if dst_prefix:
        extra += f" AND b.type STARTS WITH '{dst_prefix}'"
    cypher = (f"MATCH (a:Neuron {{type: '{src_type}'}})-[r:ConnectsTo]->(b:Neuron) "
              f"WHERE r.weight >= {int(min_weight)} {extra} "
              f"RETURN b.type, sum(r.weight) AS w, count(*) AS n "
              f"ORDER BY w DESC LIMIT {int(limit)}")
    return [(r[0], int(r[1]), int(r[2])) for r in client.rows(cypher)]


def pair_weight(client: Client, src_type: str, dst_type: str,
                min_weight: int = 1) -> Dict[str, int]:
    """一对类型之间的突触总数与边数（换阈值做对照时用）。"""
    cypher = (f"MATCH (a:Neuron {{type: '{src_type}'}})-[r:ConnectsTo]->"
              f"(b:Neuron {{type: '{dst_type}'}}) "
              f"WHERE r.weight >= {int(min_weight)} "
              f"RETURN sum(r.weight) AS w, count(r) AS n")
    rows = client.rows(cypher)
    if not rows:
        return {"weight": 0, "edges": 0, "min_weight": min_weight}
    return {"weight": int(rows[0][0] or 0), "edges": int(rows[0][1] or 0),
            "min_weight": min_weight}


def inputs_by_type(client: Client, body_id: int, limit: int = 10,
                   min_weight: int = DEFAULT_MIN_WEIGHT) -> List[Tuple[str, int]]:
    """谁在驱动这个神经元（按类型聚合突触数）。"""
    cypher = (f"MATCH (a:Neuron)-[r:ConnectsTo]->(b:Neuron {{bodyId: {int(body_id)}}}) "
              f"WHERE r.weight >= {int(min_weight)} "
              f"RETURN a.type, sum(r.weight) AS w "
              f"ORDER BY w DESC LIMIT {int(limit)}")
    return [(r[0], int(r[1])) for r in client.rows(cypher)]


# ======================================================================
# 4. 口径自查
# ======================================================================
def census(client: Client) -> Dict[str, int]:
    """拿到"同一份数据的不同口径"数字，用来提醒自己用的是哪一套。

    注意：这里只做轻量查询。全图边数在 neuPrint 上很慢，
    要精确统计请用下载的 feather 文件（见页面"数据获取"一节）。
    """
    out = {}
    out["neurons"] = client.count("MATCH (n:Neuron) RETURN count(n)")
    out["neurons_typed"] = client.count(
        "MATCH (n:Neuron) WHERE n.type IS NOT NULL RETURN count(n)")
    out["types"] = client.count(
        "MATCH (n:Neuron) WHERE n.type IS NOT NULL RETURN count(DISTINCT n.type)")
    return out


# ======================================================================
# 5. 小工具
# ======================================================================
def save_matrix(M, ids: Sequence[int], path: str) -> str:
    import scipy.sparse as sp
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    sp.save_npz(path, M)
    with open(path + ".ids.json", "w", encoding="utf-8") as f:
        json.dump(list(map(int, ids)), f)
    return path


def load_matrix(path: str):
    import scipy.sparse as sp
    M = sp.load_npz(path)
    ids = json.load(open(path + ".ids.json", encoding="utf-8"))
    return M, ids, {b: i for i, b in enumerate(ids)}


def fmt(rows, headers: Optional[Sequence[str]] = None, width: int = 26) -> str:
    """把查询结果排成等宽表格（阶段 3 的"对照输出"用）。"""
    out = []
    if headers:
        out.append("  ".join(str(h)[:width].ljust(width) for h in headers))
        out.append("  ".join("-" * min(width, len(str(h))) for h in headers))
    for r in rows:
        out.append("  ".join(str(c)[:width].ljust(width) for c in r))
    return "\n".join(out)


if __name__ == "__main__":
    ok, msg = ping()
    print(("✓ " if ok else "✗ ") + msg)
