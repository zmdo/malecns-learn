"""轻量诊断：R1-R6→L2 的数字为何与阶段 1 不同（只用带索引的查询）。"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p3_lib import connect

sys.stdout.reconfigure(encoding="utf-8")
c = connect()

print("=== 不同阈值下的 R1-R6 → L2 ===")
for mw in (1, 3, 5):
    t0 = time.time()
    v = c.one("MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron {type:'L2'}) "
              f"WHERE r.weight >= {mw} RETURN sum(r.weight)")
    n = c.one("MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron {type:'L2'}) "
              f"WHERE r.weight >= {mw} RETURN count(r)")
    print(f"  ≥{mw:<3} sum = {v:>9,}  边数 = {n:>7,}   ({time.time()-t0:.1f}s)")

print()
print("=== 不按类型聚合，而是先取 L2 的 bodyId 再按 bodyId 查 ===")
l2 = [int(r[0]) for r in c.rows("MATCH (n:Neuron {type:'L2'}) RETURN n.bodyId")]
print(f"  L2 神经元个数 = {len(l2)}")
r16 = [int(r[0]) for r in c.rows("MATCH (n:Neuron {type:'R1-R6'}) RETURN n.bodyId")]
print(f"  R1-R6 神经元个数 = {len(r16)}")

# 逐个 L2 查其来自 R1-R6 的输入总和，再相加
tot = 0
t0 = time.time()
for b in l2[:400]:
    v = c.one("MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron {bodyId:%d}) "
              "WHERE r.weight >= 5 RETURN sum(r.weight)" % b)
    tot += int(v or 0)
print(f"  前 400 个 L2 的 R1-R6 输入合计 = {tot:,}  ({time.time()-t0:.1f}s)")

print()
print("=== r 上到底有哪些字段 ===")
cols, rows = c.table("MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron {type:'L2'}) "
                     "RETURN keys(r) LIMIT 1")
print("  ", rows)

print()
print("=== type 为 None 的边（说明有神经元没类型）===")
none_n = c.one("MATCH (a:Neuron {type:'R1-R6'})-[r:ConnectsTo]->(b:Neuron) "
               "WHERE b.type IS NULL AND r.weight >= 5 RETURN sum(r.weight)")
print(f"  R1-R6 → 无类型靶点的突触总数 = {none_n:,}")
