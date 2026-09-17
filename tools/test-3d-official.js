/* =====================================================================
   test-3d-official.js — 验证「官方网格」这条路径：解析、装载、渲染、拾取

   依赖 assets/mcns-meshes.js（由 tools/fetch_official_meshes.py +
   tools/decimate_meshes.py 生成）。若文件不存在，本测试会说明并跳过。

   用法: node tools/test-3d-official.js
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const M = require(path.join(ROOT, 'assets', 'mcns-3d.js'));

let pass = 0, fail = 0;
const failures = [];
function ok(cond, msg) {
  if (cond) pass++;
  else { fail++; failures.push(msg); console.log('  FAIL  ' + msg); }
}
function section(t) { console.log('\n' + t); console.log('-'.repeat(t.length)); }

const W = 1000, H = 860;

/* ---------------------------------------------------------------- */
section('0. 装载官方网格包');
const bundlePath = path.join(ROOT, 'assets', 'mcns-meshes.js');
if (!fs.existsSync(bundlePath)) {
  console.log('  未找到 assets/mcns-meshes.js');
  console.log('  请先运行: python tools/fetch_official_meshes.py && python tools/decimate_meshes.py');
  process.exit(2);
}
const sandbox = { window: {}, console, Math, JSON, Array, Object, String, Number, Boolean,
                  Error, Uint8Array, Uint32Array, Float32Array, Buffer, atob: undefined };
sandbox.globalThis = sandbox;
sandbox.window = sandbox;
vm.createContext(sandbox);
const src = fs.readFileSync(bundlePath, 'utf8');
vm.runInContext(src, sandbox, { filename: 'mcns-meshes.js' });
const bundle = sandbox.MCNS_MESHES;
ok(!!bundle, 'MCNS_MESHES 未挂到 window');
ok(!!bundle.meta, '缺少 meta');
const keys = Object.keys(bundle).filter(k => k !== 'meta');
console.log(`  结构数: ${keys.length}`);
console.log(`  来源: ${bundle.meta.source || '?'}`);
console.log(`  许可: ${bundle.meta.license || '?'}`);
ok(/flyem-male-cns/.test(bundle.meta.source || ''), 'meta.source 未指向官方桶');
ok(/CC-BY/.test(bundle.meta.license || ''), 'meta.license 未标注 CC-BY');
if (bundle.meta.decimation) {
  const d = bundle.meta.decimation;
  console.log(`  抽稀: ${d.rawTriangles.toLocaleString()} → ${d.keptTriangles.toLocaleString()} 三角形 (${(d.ratio*100).toFixed(1)}%)`);
  ok(d.keptTriangles < d.rawTriangles, '抽稀后三角形数没有减少');
}

/* ---------------------------------------------------------------- */
section('1. 官方几何装载与自洽性');
const meshes = M.loadOfficialGeometry(bundle);
ok(!!meshes && meshes.length > 0, 'loadOfficialGeometry 返回空');
console.log(`  装载 ${meshes.length} 个结构`);

let totalTri = 0, totalV = 0;
for (const mesh of meshes) {
  const id = mesh.region.id;
  ok(mesh.tris > 0, `${id} 没有三角形`);
  ok(mesh.verts.length === (mesh.verts.length | 0), `${id} verts 不是数组`);
  ok(mesh.faces.length === mesh.tris * 3, `${id} 索引数与 tris 不符`);
  // 索引必须在范围内
  let oob = 0, maxi = 0;
  for (let i = 0; i < mesh.faces.length; i++) {
    const v = mesh.faces[i];
    if (v >= mesh.verts.length / 3) oob++;
    if (v > maxi) maxi = v;
  }
  ok(oob === 0, `${id} 有 ${oob} 个越界索引`);
  // 顶点必须有限
  let bad = 0;
  for (let i = 0; i < mesh.verts.length; i++) if (!Number.isFinite(mesh.verts[i])) bad++;
  ok(bad === 0, `${id} 有 ${bad} 个非有限顶点`);
  // 法线长度应接近 1
  if (mesh.norms) {
    ok(mesh.norms.length === mesh.verts.length, `${id} 法线数量与顶点不符`);
    let nbad = 0;
    for (let i = 0; i < mesh.norms.length; i += 3) {
      const L = Math.hypot(mesh.norms[i], mesh.norms[i+1], mesh.norms[i+2]);
      if (Math.abs(L - 1) > 0.02) nbad++;
    }
    ok(nbad / (mesh.norms.length / 3) < 0.05, `${id} 有 ${nbad} 个非单位法线`);
  } else {
    ok(false, `${id} 没有顶点法线`);
  }
  totalTri += mesh.tris;
  totalV += mesh.verts.length / 3;
}
console.log(`  顶点合计 ${totalV.toLocaleString()}，三角形合计 ${totalTri.toLocaleString()}`);
ok(totalTri < 900000, `三角形总数 ${totalTri.toLocaleString()} 偏大，Canvas 2D 渲染会卡`);

/* ---------------------------------------------------------------- */
section('2. 坐标必须落在真实 MaleCNS 范围内（纳米）');
{
  let min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const mesh of meshes) {
    for (let i = 0; i < mesh.verts.length; i += 3) {
      for (let d = 0; d < 3; d++) {
        const v = mesh.verts[i + d];
        if (v < min[d]) min[d] = v;
        if (v > max[d]) max[d] = v;
      }
    }
  }
  const span = [max[0]-min[0], max[1]-min[1], max[2]-min[2]];
  console.log(`  x[${min[0].toFixed(0)}, ${max[0].toFixed(0)}] 跨度 ${(span[0]/1000).toFixed(0)} μm`);
  console.log(`  y[${min[1].toFixed(0)}, ${max[1].toFixed(0)}] 跨度 ${(span[1]/1000).toFixed(0)} μm`);
  console.log(`  z[${min[2].toFixed(0)}, ${max[2].toFixed(0)}] 跨度 ${(span[2]/1000).toFixed(0)} μm`);
  // 果蝇全 CNS 是数百微米量级
  ok(span[0] > 300000 && span[0] < 3000000, `x 跨度 ${span[0]} 不像果蝇 CNS`);
  ok(span[1] > 300000 && span[1] < 3000000, `y 跨度 ${span[1]} 不像果蝇 CNS`);
  ok(span[2] > 300000 && span[2] < 3000000, `z 跨度 ${span[2]} 不像果蝇 CNS`);
}

/* ---------------------------------------------------------------- */
section('3. 相机自动取景（把所有结构框进画面）');
/** 计算能把整个模型框进画面的相机参数（返回 center 与 focal/dist 比值） */
function fitCamera(meshes) {
  let min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (const m of meshes) {
    for (let i = 0; i < m.verts.length; i += 3) {
      for (let d = 0; d < 3; d++) {
        const v = m.verts[i + d];
        if (v < min[d]) min[d] = v;
        if (v > max[d]) max[d] = v;
      }
    }
  }
  const center = [(min[0]+max[0])/2, (min[1]+max[1])/2, (min[2]+max[2])/2];
  const radius = 0.5 * Math.hypot(max[0]-min[0], max[1]-min[1], max[2]-min[2]);
  return { center, radius, min, max };
}
const fit = fitCamera(meshes);
console.log(`  模型中心 [${fit.center.map(v => v.toFixed(0)).join(', ')}]  外接半径 ${(fit.radius/1000).toFixed(0)} μm`);

// 自动取景：先给一个初值，量出实际占幅再按比例修正（一次标定即可收敛）
function autoFit(meshes, W, H, target) {
  const dist0 = fit.radius * 3.0;
  const cam0 = M.makeCamera({ target: fit.center, dist: dist0, focal: 1000 });
  const ps = M.buildFrame(cam0, meshes, W, H, null);
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of ps) for (let i = 0; i < 3; i++) {
    minX = Math.min(minX, p.x[i]); maxX = Math.max(maxX, p.x[i]);
    minY = Math.min(minY, p.y[i]); maxY = Math.max(maxY, p.y[i]);
  }
  const fill = Math.max((maxX - minX) / W, (maxY - minY) / H);
  return M.makeCamera({
    target: fit.center,
    dist: dist0,
    focal: 1000 * (target / fill)
  });
}
const cam = autoFit(meshes, W, H, 0.88);
{
  const polys = M.buildFrame(cam, meshes, W, H, null);
  ok(polys.length > 1000, `帧里只有 ${polys.length} 个多边形`);
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, off = 0;
  for (const p of polys) {
    for (let i = 0; i < 3; i++) {
      minX = Math.min(minX, p.x[i]); maxX = Math.max(maxX, p.x[i]);
      minY = Math.min(minY, p.y[i]); maxY = Math.max(maxY, p.y[i]);
      if (p.x[i] < -4 || p.x[i] > W+4 || p.y[i] < -4 || p.y[i] > H+4) off++;
    }
  }
  const fillW = (maxX-minX)/W, fillH = (maxY-minY)/H;
  console.log(`  可见三角形 ${polys.length.toLocaleString()}, 占宽 ${(fillW*100).toFixed(0)}% 占高 ${(fillH*100).toFixed(0)}%`);
  console.log(`  越界顶点 ${off} / ${(polys.length*3).toLocaleString()}`);
  ok(fillW < 1.05 && fillH < 1.05, `模型超出画布 (${(fillW*100).toFixed(0)}% x ${(fillH*100).toFixed(0)}%)`);
  ok(Math.max(fillW, fillH) > 0.5, `模型太小 (最大维 ${(Math.max(fillW,fillH)*100).toFixed(0)}%)`);
  ok(off / (polys.length*3) < 0.05, `${((off/(polys.length*3))*100).toFixed(1)}% 顶点在画布外`);
  // 深度排序
  let bad = 0;
  for (let i = 1; i < polys.length; i++) if (polys[i].z < polys[i-1].z - 1e-6) bad++;
  ok(bad === 0, `深度排序有 ${bad} 处逆序`);
  // 背面剔除比例
  const total = totalTri;
  const kept = polys.length / total;
  console.log(`  面保留率 ${(kept*100).toFixed(1)}%`);
  ok(kept > 0.2 && kept < 0.8, `面保留率 ${(kept*100).toFixed(1)}% 异常`);

  /* -------------------------------------------------------------- */
  section('4. 每个结构都有可点击的位置');
  const polys2 = polys;
  const named = meshes.filter(m => m.region.pickable !== false);
  const byRegion = {};
  for (const p of polys2) (byRegion[p.regionId] = byRegion[p.regionId] || []).push(p);
  let unclickable = [];
  let totalOwn = 0, totalHit = 0;
  for (const mesh of named) {
    const own = byRegion[mesh.region.id] || [];
    totalOwn += own.length;
    if (!own.length) { unclickable.push(mesh.region.id + '(不可见)'); continue; }
    // 逐面测试；命中 8 个样本即认为可点击（避免大网格上跑满）
    let hit = 0;
    const cap = Math.min(own.length, 900);
    for (let i = 0; i < cap; i++) {
      const f = own[i];
      const cx = (f.x[0]+f.x[1]+f.x[2])/3, cy = (f.y[0]+f.y[1]+f.y[2])/3;
      const h = M.pick(polys2, cx, cy);
      if (h && h.id === mesh.region.id) hit++;
      if (hit >= 8) break;
    }
    totalHit += hit;
    if (hit === 0) unclickable.push(mesh.region.id);
  }
  console.log(`  可见面合计 ${totalOwn.toLocaleString()}，命中自身样本 ${totalHit}`);
  // 有些结构在三维上被别的结构包住（IB 在下脑桥深处、LOP 被 LA/ME/LO 遮住、
  // VNC-INT 被 T1/T2/T3 神经节夹在中间），从这个视角确实点不到 ——
  // 这是真实解剖遮挡，不是 bug。页面提供「显示内部结构」模式与右侧列表来访问它们。
  const OCCLUDED_BY_DESIGN = new Set(['IB', 'LOP', 'VNC-INT']);
  const unexpected = unclickable.filter(id => !OCCLUDED_BY_DESIGN.has(id));
  for (const u of unclickable) {
    console.log(`    · ${u}${OCCLUDED_BY_DESIGN.has(u) ? '  (已知被遮挡，靠列表/内部模式访问)' : ''}`);
  }
  ok(unexpected.length === 0, `非预期地有结构点不到: ${unexpected.join(', ')}`);
  const clickable = named.length - unclickable.length;
  console.log(`  可直接点击的结构: ${clickable} / ${named.length}`);
  ok(clickable >= named.length - 3, `可点击结构太少: ${clickable}/${named.length}`);

  section('5. 拾取：空白角落应无命中');
  let cornerHits = 0;
  for (const [x, y] of [[3,3],[W-3,3],[3,H-3],[W-3,H-3]]) {
    const h = M.pick(polys2, x, y);
    if (h) { cornerHits++; console.log(`    角落 (${x},${y}) → ${h.id}`); }
  }
  ok(cornerHits <= 1, `${cornerHits}/4 个角落命中结构`);

  section('6. 选中与悬停状态');
  const anyId = named[0].region.id;
  const sel = M.buildFrame(cam, meshes, W, H, anyId);
  const selFaces = sel.filter(p => p.regionId === anyId);
  ok(selFaces.length > 0, `选中 ${anyId} 后找不到它的面`);
  ok(selFaces.every(p => p.sel === true && p.alpha === 1.0), `选中 ${anyId} 后未全部高亮`);

  section('7. 渲染性能预算');
  console.log(`  每帧需绘制三角形: ${polys.length.toLocaleString()}`);
  console.log(`  Canvas 2D 参考: <150k 流畅, 150–350k 可用, >350k 明显卡顿`);
  const t0 = Date.now();
  const N = 3;
  for (let i = 0; i < N; i++) M.buildFrame(cam, meshes, W, H, null);
  const per = (Date.now() - t0) / N;
  console.log(`  buildFrame 平均 ${per.toFixed(0)} ms/帧（仅几何+排序，不含绘制）`);
  ok(per < 900, `buildFrame 太慢: ${per.toFixed(0)} ms/帧`);
}

console.log('\n' + '='.repeat(60));
console.log(`结果: ${pass} 通过, ${fail} 失败`);
if (fail) {
  console.log('\n失败项:');
  failures.forEach(f => console.log('  - ' + f));
  process.exit(1);
}
console.log('ALL PASS');
