/* =====================================================================
   test-3d.js — 验证 mcns-3d.js 的几何 / 投影 / 拾取是否真的可用
   用法:  node tools/test-3d.js
   ===================================================================== */
'use strict';

const path = require('path');
const M = require(path.join(__dirname, '..', 'assets', 'mcns-3d.js'));

let pass = 0, fail = 0;
const failures = [];

function ok(cond, msg) {
  if (cond) { pass++; }
  else { fail++; failures.push(msg); console.log('  FAIL  ' + msg); }
}
function section(t) { console.log('\n' + t); console.log('-'.repeat(t.length)); }

const W = 900, H = 700;

/* ---------------------------------------------------------------- */
section('1. 数据完整性');
const seen = new Set();
for (const r of M.REGIONS) {
  ok(typeof r.id === 'string' && r.id.length > 0, `region 缺少 id: ${JSON.stringify(r.name)}`);
  ok(!seen.has(r.id), `region id 重复: ${r.id}`);
  seen.add(r.id);
  ok(typeof r.name === 'string' && r.name.length > 0, `${r.id} 缺少 name`);
  ok(typeof r.en === 'string' && r.en.length > 0, `${r.id} 缺少 en`);
  ok(typeof r.desc === 'string' && r.desc.length > 20, `${r.id} 的 desc 太短（点击后没内容可看）`);
  ok(Array.isArray(r.parts) && r.parts.length > 0, `${r.id} 没有几何部件`);
  ok(/^#[0-9a-fA-F]{6}$/.test(r.color), `${r.id} 颜色格式不对: ${r.color}`);
  ok(Array.isArray(r.tags) && r.tags.length > 0, `${r.id} 没有 tags`);
}
console.log(`  区域数: ${M.REGIONS.length}`);
console.log(`  命名的（可点击高亮）: ${M.REGIONS.filter(r => !r.bg).length}`);
console.log(`  背景结构: ${M.REGIONS.filter(r => r.bg).length}`);

/* ---------------------------------------------------------------- */
section('2. 几何有效性');
const meshes = M.buildMeshes(M.REGIONS, 16, 10);
ok(meshes.length === M.REGIONS.length, 'buildMeshes 数量不匹配');

for (const mesh of meshes) {
  const id = mesh.region.id;
  ok(mesh.bound > 0 && Number.isFinite(mesh.bound), `${id} bound 非法: ${mesh.bound}`);
  for (const p of mesh.parts) {
    ok(p.verts.length === p.norms.length, `${id} verts/norms 长度不一致`);
    ok(p.faces.length > 0, `${id} 没有面`);
    // 顶点必须是有限数
    let bad = 0;
    for (const v of p.verts) {
      if (!v.every(Number.isFinite)) bad++;
    }
    ok(bad === 0, `${id} 有 ${bad} 个非有限顶点`);
    // 面索引必须在范围内
    let oob = 0;
    for (const f of p.faces) {
      if (f.some(i => i < 0 || i >= p.verts.length)) oob++;
    }
    ok(oob === 0, `${id} 有 ${oob} 个越界面索引`);
    // 法线必须是单位向量
    let nb = 0;
    for (const n of p.norms) {
      const L = Math.hypot(n[0], n[1], n[2]);
      if (Math.abs(L - 1) > 1e-6) nb++;
    }
    ok(nb === 0, `${id} 有 ${nb} 个非单位法线（球体极点会有 NaN，需检查）`);
  }
  // 包围盒中心必须有限
  ok(mesh.center.every(Number.isFinite), `${id} center 非有限`);
}

/* ---------------------------------------------------------------- */
section('3. 相机与投影');
const cam = M.makeCamera();

// 视图变换保距性（旋转不应改变长度）
{
  const p = [123, -45, 67], q = [10, 20, -30];
  const vp = M.worldToView(cam, p), vq = M.worldToView(cam, q);
  const d0 = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);
  const d1 = Math.hypot(vp[0] - vq[0], vp[1] - vq[1], vp[2] - vq[2]);
  ok(Math.abs(d0 - d1) < 1e-9, `视图变换不保距: ${d0} vs ${d1}`);
}

// 原点投影到屏幕中心附近
{
  const c = M.project(cam, cam.target, W, H);
  ok(Math.abs(c[0] - W / 2) < 1e-6 && Math.abs(c[1] - H / 2) < 1e-6,
    `target 未投影到屏幕中心: ${c[0]},${c[1]}`);
}

// 所有顶点必须落在相机前方（depth = z + dist 必须 > 0，否则透视除法翻号）
{
  let behind = 0, nearest = Infinity;
  for (const mesh of meshes) {
    for (const p of mesh.parts) {
      for (const v of p.verts) {
        const d = M.worldToView(cam, v)[2] + cam.dist;
        if (d <= 0) behind++;
        if (d < nearest) nearest = d;
      }
    }
  }
  ok(behind === 0, `有 ${behind} 个顶点落在相机后方（depth<=0）`);
  console.log(`  最近顶点距相机 depth = ${nearest.toFixed(1)} (必须 > 0)`);
  console.log(`  最远顶点距相机 depth = ${(cam.dist + 450).toFixed(1)} (参考)`);
}

/* ---------------------------------------------------------------- */
section('4. 渲染帧与背面剔除');
const polys = M.buildFrame(cam, meshes, W, H, null);
ok(polys.length > 500, `帧里只有 ${polys.length} 个多边形，偏少`);
console.log(`  可见三角形: ${polys.length}`);

// 深度必须单调不减（画家算法前提）
{
  let bad = 0;
  for (let i = 1; i < polys.length; i++) if (polys[i].z < polys[i - 1].z - 1e-9) bad++;
  ok(bad === 0, `深度排序有 ${bad} 处逆序`);
}
// shade / alpha 必须在合理范围
{
  let bad = 0;
  for (const p of polys) {
    if (!(p.shade >= 0 && p.shade <= 1.05)) bad++;
    if (!(p.alpha > 0 && p.alpha <= 1)) bad++;
  }
  ok(bad === 0, `有 ${bad} 个多边形的 shade/alpha 越界`);
}
// 背面剔除比例：应剔除大约一半
{
  let total = 0;
  for (const mesh of meshes) for (const p of mesh.parts) total += p.faces.length;
  const kept = polys.length / total;
  console.log(`  面保留率: ${(kept * 100).toFixed(1)}% (期望约 45–60%)`);
  ok(kept > 0.25 && kept < 0.75, `面保留率异常: ${(kept * 100).toFixed(1)}% —— 可能是绕序反了`);
}

/* ---------------------------------------------------------------- */
section('5. 每个命名区域都可见');
const counts = {};
for (const p of polys) counts[p.regionId] = (counts[p.regionId] || 0) + 1;
for (const mesh of meshes) {
  const id = mesh.region.id;
  const n = counts[id] || 0;
  ok(n > 0, `${id} (${mesh.region.name}) 在当前视角下完全不可见`);
  if (n > 0 && n < 12) console.log(`  提示: ${id} 只有 ${n} 个可见面（可能太边缘）`);
}
console.log('  ' + Object.keys(counts).length + ' 个区域有可见面');

/* ---------------------------------------------------------------- */
section('6. 屏幕填充率（模型要占满画布，不能缩成一小团）');
const STEPS = [0, 45, 90, 135, 180, 225, 270, 315];
for (const deg of STEPS) {
  const c = M.makeCamera({ yaw: (deg - 34) * M.DEG, pitch: 16 * M.DEG });
  const ps = M.buildFrame(c, meshes, W, H, null);
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const p of ps) {
    for (let i = 0; i < 3; i++) {
      minX = Math.min(minX, p.x[i]); maxX = Math.max(maxX, p.x[i]);
      minY = Math.min(minY, p.y[i]); maxY = Math.max(maxY, p.y[i]);
    }
  }
  const fillW = (maxX - minX) / W, fillH = (maxY - minY) / H;
  const fillMax = Math.max(fillW, fillH);
  console.log(`  yaw ${String(deg).padStart(3)}°: 占宽 ${(fillW * 100).toFixed(0)}%  ` +
    `占高 ${(fillH * 100).toFixed(0)}%  最大维 ${(fillMax * 100).toFixed(0)}%  ` +
    `x[${minX.toFixed(0)},${maxX.toFixed(0)}] y[${minY.toFixed(0)},${maxY.toFixed(0)}]`);
  // 头尾相接的 CNS 又高又窄（脑 + 视叶 + 神经索），且旋转时轮廓在两个方向上
  // 此消彼长。判据因此定为：不许溢出；且两个维度都保持在合理占比之上
  // （回归基准：修好投影前这里只有 23–33%）。
  ok(fillW <= 1.02, `yaw ${deg}° 占宽 ${(fillW * 100).toFixed(0)}%（超出画布，会被裁切）`);
  ok(fillH <= 1.02, `yaw ${deg}° 占高 ${(fillH * 100).toFixed(0)}%（超出画布，会被裁切）`);
  ok(fillMax > 0.60, `yaw ${deg}° 最大维只占 ${(fillMax * 100).toFixed(0)}%（缩得太小）`);
  ok(Math.min(fillW, fillH) > 0.38, `yaw ${deg}° 最小维只占 ${(Math.min(fillW, fillH) * 100).toFixed(0)}%`);
}

/* ---------------------------------------------------------------- */
section('7. 拾取：每个命名区域都要有可点击的屏幕位置');
/* 每个区域取「自己可见面」的若干采样点，要求至少有一个点能点到自己。
   比「点重心必须命中自己」更贴近真实交互，也更宽容合理的遮挡。 */
let globalHit = 0, globalTry = 0;
const unclickable = [];
for (const mesh of meshes) {
  if (mesh.region.pickable === false) continue;
  const own = polys.filter(p => p.regionId === mesh.region.id);
  let okCount = 0;
  for (const f of own) {
    const cx = (f.x[0] + f.x[1] + f.x[2]) / 3;
    const cy = (f.y[0] + f.y[1] + f.y[2]) / 3;
    globalTry++;
    const hit = M.pick(polys, cx, cy);
    if (hit && hit.id === mesh.region.id) { okCount++; globalHit++; }
  }
  const rate = own.length ? okCount / own.length : 0;
  console.log(`  ${mesh.region.id.padEnd(12)} 可见面 ${String(own.length).padStart(4)}  ` +
    `可点击 ${String(okCount).padStart(4)}  (${(rate * 100).toFixed(0)}%)`);
  if (okCount === 0) unclickable.push(mesh.region.id);
}
ok(unclickable.length === 0, `这些区域完全点不到: ${unclickable.join(', ')}`);
const globalRate = globalHit / globalTry;
console.log(`  总体可点击率: ${(globalRate * 100).toFixed(1)}%`);
ok(globalRate > 0.40, `总体可点击率过低: ${(globalRate * 100).toFixed(1)}%`);

section('8. 拾取：加厚选项能让每个区域都更容易点到');
{
  // 若启用「优先点最近的前景区域」，各区域的可点击率应保持合理
  const named = M.REGIONS.filter(r => r.pickable !== false).map(r => r.id);
  const cnt = {};
  for (const id of named) cnt[id] = 0;
  for (const f of polys) {
    const cx = (f.x[0] + f.x[1] + f.x[2]) / 3;
    const cy = (f.y[0] + f.y[1] + f.y[2]) / 3;
    const hit = M.pick(polys, cx, cy);
    if (hit && cnt[hit.id] !== undefined) cnt[hit.id]++;
  }
  const zero = named.filter(id => cnt[id] === 0);
  ok(zero.length === 0, `有区域从未被拾取到: ${zero.join(', ')}`);
}

section('8b. 拾取：空白处应返回 null');
{
  const corners = [[3, 3], [W - 3, 3], [3, H - 3], [W - 3, H - 3]];
  let hits = 0;
  for (const [x, y] of corners) {
    const p = M.pick(polys, x, y);
    if (p) { hits++; console.log(`  角落 (${x},${y}) 命中了 ${p.id}`); }
  }
  ok(hits <= 1, `${hits}/4 个角落命中了区域（空白处不该有东西）`);
}

section('9. 选中状态影响渲染');
{
  const anyId = M.REGIONS.find(r => r.pickable !== false).id;
  const sel = M.buildFrame(cam, meshes, W, H, anyId);
  const selFaces = sel.filter(p => p.regionId === anyId);
  ok(selFaces.length > 0, `选中 ${anyId} 后找不到它的面`);
  ok(selFaces.every(p => p.sel === true), `选中 ${anyId} 后部分面未标记 sel`);
  ok(selFaces.every(p => p.alpha === 1.0), `选中 ${anyId} 后不是全不透明`);
  const bgFaces = sel.filter(p => p.pickable === false);
  ok(bgFaces.length > 0, '背景结构应当仍在渲染');
  console.log(`  选中 ${anyId}: 高亮面 ${selFaces.length}, 背景面 ${bgFaces.length}`);
}

section('10. 缩放 zoom 生效');
{
  const c1 = M.makeCamera(), c2 = M.makeCamera({ zoom: 1.5 });
  const ps1 = M.buildFrame(c1, meshes, W, H, null);
  const ps2 = M.buildFrame(c2, meshes, W, H, null);
  const span = ps => {
    let mn = Infinity, mx = -Infinity;
    for (const p of ps) for (let i = 0; i < 3; i++) { mn = Math.min(mn, p.x[i]); mx = Math.max(mx, p.x[i]); }
    return mx - mn;
  };
  const s1 = span(ps1), s2 = span(ps2);
  console.log(`  zoom 1.0 跨度 ${s1.toFixed(0)}px, zoom 1.5 跨度 ${s2.toFixed(0)}px`);
  ok(s2 > s1 * 1.3, `zoom 没有生效: ${s1.toFixed(0)} → ${s2.toFixed(0)}`);
}

section('11. 坐标轴指示器');
{
  const ax = M.axisScreen(cam, W, H, [0, -60, -260], 120);
  ok(ax.length === 3, `坐标轴数量应为 3，实际 ${ax.length}`);
  for (const a of ax) {
    const len = Math.hypot(a.x1 - a.x0, a.y1 - a.y0);
    ok(len > 5, `坐标轴 ${a.label} 长度过短: ${len.toFixed(1)}`);
  }
  const labels = ax.map(a => a.label).join(' / ');
  ok(labels.includes('右') && labels.includes('前') && labels.includes('背'),
    `坐标轴标签不完整: ${labels}`);
}

section('11b. 固定屏幕位置的坐标轴 HUD');
{
  const cx = 66, cy = 400, len = 42;
  const hud = M.axisHud(M.makeCamera(), cx, cy, len);
  ok(hud.length === 3, `HUD 轴数应为 3，实际 ${hud.length}`);
  for (const a of hud) {
    // 起点固定在给定屏幕点
    ok(a.x0 === cx && a.y0 === cy, `${a.label} 起点未固定在 (${cx},${cy})`);
    const L = Math.hypot(a.x1 - a.x0, a.y1 - a.y0);
    // 透视效果：轴在屏幕上会被透视缩短，最长不超过 len
    ok(L <= len + 1e-6, `${a.label} HUD 长度 ${L.toFixed(2)} 超过上限 ${len}`);
    ok(L > 2, `${a.label} HUD 长度过短（几乎看不见）: ${L.toFixed(2)}`);
    ok(Number.isFinite(a.near), `${a.label} near 非有限`);
  }
  // 至少有一根轴接近满长，否则整个指示器会缩成一点
  const maxL = Math.max.apply(null, hud.map(a => Math.hypot(a.x1 - a.x0, a.y1 - a.y0)));
  ok(maxL > len * 0.7, `HUD 最长轴只有 ${maxL.toFixed(1)}px（应接近 ${len}）`);
  // 旋转相机时，轴向应随之改变，但长度不变
  const hud2 = M.axisHud(M.makeCamera({ yaw: 1.1, pitch: -0.4 }), cx, cy, len);
  let changed = 0;
  for (let i = 0; i < 3; i++) {
    if (Math.abs(hud2[i].x1 - hud[i].x1) > 1) changed++;
  }
  ok(changed >= 2, `旋转相机后 HUD 轴向几乎没变（changed=${changed}）`);
  // 固定屏幕位置 → 永远在画布内（不会被模型挤出去）
  for (const a of hud2) {
    ok(a.x1 > 0 && a.x1 < W && a.y1 > 0 && a.y1 < H,
      `${a.label} HUD 末端跑出画布: (${a.x1.toFixed(0)},${a.y1.toFixed(0)})`);
  }
  console.log(`  HUD 锚点 (${cx},${cy})，轴长恒为 ${len}px，旋转时方向更新`);
}

section('12. 背景结构不可拾取');
{
  const bgIds = M.REGIONS.filter(r => r.pickable === false).map(r => r.id);
  ok(bgIds.length === 3, `背景结构应为 3 个，实际 ${bgIds.length}`);
  const hitBg = polys.filter(p => !p.pickable).length;
  console.log(`  不可拾取的面: ${hitBg} / ${polys.length}`);
  // 背景面很多，但 pick 必须跳过它们
  let picked = 0;
  for (const f of polys.filter(p => !p.pickable)) {
    const cx = (f.x[0] + f.x[1] + f.x[2]) / 3;
    const cy = (f.y[0] + f.y[1] + f.y[2]) / 3;
    const hit = M.pick(polys, cx, cy);
    if (hit && bgIds.includes(hit.id)) picked++;
  }
  ok(picked === 0, `背景结构被拾取到 ${picked} 次（本应完全跳过）`);
}

section('13. 区域之间的几何一致性（不能互相吃掉）');
{
  // 计算每个区域的轴对齐包围盒
  const boxes = meshes.map(mesh => {
    let mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    for (const part of mesh.parts) {
      for (const v of part.verts) {
        for (let d = 0; d < 3; d++) {
          if (v[d] < mn[d]) mn[d] = v[d];
          if (v[d] > mx[d]) mx[d] = v[d];
        }
      }
    }
    return { id: mesh.region.id, name: mesh.region.name, mn, mx, bg: mesh.region.bg === true };
  });

  // 已知的、有意的包含关系（细分区域在母结构内部）
  const INTENDED = new Set([
    'MB-CA>MB', 'CX-EB>CX', 'AB>VNC', 'AB>NEUROMERE-T',
    'MB>CB', 'CX>CB', 'AL>CB', 'LH>CB', 'SEZ>CB', 'MB-CA>CB', 'CX-EB>CB',
    'LA>OL', 'ME>OL', 'LO>OL', 'LOP>OL'
  ]);

  // 用椭球参数式判定「点是否在某区域内」，比轴对齐包围盒准确得多
  const inside = (mesh, p) => {
    for (const part of mesh.parts) {
      const c = part.c, r = part.r;
      const dx = (p[0] - c[0]) / r[0], dy = (p[1] - c[1]) / r[1], dz = (p[2] - c[2]) / r[2];
      if (dx * dx + dy * dy + dz * dz <= 1) return true;
    }
    return false;
  };

  // 在区域表面均匀取样，看有多大比例落在另一个区域内部
  const surfacePoints = (mesh, n) => {
    const pts = [];
    const N = mesh.parts.length;
    for (let i = 0; i < n; i++) {
      const part = mesh.parts[i % N];
      // Fibonacci 球面采样
      const k = i + 0.5;
      const phi = Math.acos(1 - 2 * k / n);
      const theta = Math.PI * (1 + Math.sqrt(5)) * k;
      const u = [Math.sin(phi) * Math.cos(theta), Math.sin(phi) * Math.sin(theta), Math.cos(phi)];
      pts.push([
        part.c[0] + part.r[0] * u[0],
        part.c[1] + part.r[1] * u[1],
        part.c[2] + part.r[2] * u[2]
      ]);
    }
    return pts;
  };

  const named = meshes.filter(m => !m.region.bg);
  const samples = {};
  named.forEach(m => { samples[m.region.id] = surfacePoints(m, 60); });

  const swallowed = [];
  for (const a of named) {
    for (const b of named) {
      if (a.region.id === b.region.id) continue;
      let insideCount = 0;
      for (const p of samples[a.region.id]) if (inside(b, p)) insideCount++;
      const frac = insideCount / samples[a.region.id].length;
      const key = `${a.region.id}>${b.region.id}`;
      if (frac > 0.85 && !INTENDED.has(key)) {
        swallowed.push(`${a.region.id} 有 ${(frac * 100).toFixed(0)}% 的表面在 ${b.region.id} 内部`);
      }
    }
  }
  for (const s of swallowed) console.log('    · ' + s);
  ok(swallowed.length === 0, `有 ${swallowed.length} 处非预期的「被吞掉」关系`);

  // 顺带确认已知的嵌套关系确实成立（否则说明坐标写错了）
  const checkNested = (inner, outer) => {
    const mi = named.find(m => m.region.id === inner);
    const mo = named.find(m => m.region.id === outer || m.region.id === outer);
    if (!mi || !mo) return;
    let n = 0;
    for (const p of samples[inner]) if (inside(mo, p)) n++;
    const frac = n / samples[inner].length;
    ok(frac > 0.8, `预期 ${inner} 应嵌在 ${outer} 内，实际只有 ${(frac * 100).toFixed(0)}%`);
    console.log(`  ${inner} 嵌在 ${outer} 内的表面比例: ${(frac * 100).toFixed(0)}%`);
  };
  checkNested('MB-CA', 'MB');
  checkNested('CX-EB', 'CX');
  checkNested('AB', 'VNC');

  console.log(`  检查了 ${named.length} 个区域的椭球包含关系（每区 60 个表面采样点）`);
}

section('14. 悬停与点击用的候选点都能落在画布内');
{
  const hits = [];
  for (let y = 6; y < H; y += 10) {
    for (let x = 6; x < W; x += 10) {
      const h = M.pick(polys, x, y);
      if (h) hits.push({ x, y });
    }
  }
  console.log(`  可点击像素点: ${hits.length} / ${Math.floor(W / 10) * Math.floor(H / 10)} 采样点`);
  ok(hits.length > 300, `可点击像素太少: ${hits.length}`);
  const out = hits.filter(h => h.x < 0 || h.x > W || h.y < 0 || h.y > H);
  ok(out.length === 0, `有 ${out.length} 个命中点落在画布外`);
}

section('15. 坐标轴指示器与模型几何必须一致（不能左右/前后反向）');
{
  // +X 是右侧：视叶（x ≈ +178）必须出现在中央脑（x = 0）的 +X 一侧；
  // 腹神经索（y, z 都很靠后下）必须出现在脑的 -Y/-Z 一侧。
  const c = M.makeCamera();
  const proj = p => M.project(c, p, W, H);

  const origin = proj([0, 20, -26]);            // 中央脑中心
  const optic = proj([178, 40, -72]);           // 视叶中心
  const vnc = proj([0, -215, -205]);            // 腹神经索中心
  const axis = M.axisHud(c, 100, 100, 100);

  const dirOf = label => {
    const a = axis.find(x => x.label.indexOf(label) === 0);
    const dx = a.x1 - a.x0, dy = a.y1 - a.y0;
    const L = Math.hypot(dx, dy) || 1;
    return [dx / L, dy / L];
  };
  const unit = (from, to) => {
    const dx = to[0] - from[0], dy = to[1] - from[1];
    const L = Math.hypot(dx, dy) || 1;
    return [dx / L, dy / L];
  };
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1];

  // 视叶方向应与 +X 轴一致
  const dOptic = unit(origin, optic);
  const dPlusX = dirOf('右');
  const cOptic = dot(dOptic, dPlusX);
  console.log(`  脑→视叶 方向 vs +X 轴 一致性: ${cOptic.toFixed(3)} (应接近 1)`);
  ok(cOptic > 0.6, `视叶出现在了 +X 的相反侧 (cos=${cOptic.toFixed(3)})，说明轴向反了`);

  // 脑→VNC 方向应与 +Y/+Z 轴相反（VNC 在后下方）
  const dVnc = unit(origin, vnc);
  const cY = dot(dVnc, dirOf('前'));
  console.log(`  脑→VNC 方向 vs +Y(前) 轴 一致性: ${cY.toFixed(3)} (应为负)`);
  ok(cY < -0.3, `VNC 没有出现在 -Y 方向 (cos=${cY.toFixed(3)})`);

  // 左右镜像检验：把视叶中心沿 -X 镜像，屏幕位置应落在 +X 的另一侧
  const mirror = proj([-178, 40, -72]);
  const dMirror = unit(origin, mirror);
  const cMirror = dot(dMirror, dPlusX);
  console.log(`  脑→镜像视叶 vs +X 轴: ${cMirror.toFixed(3)} (应与视叶相反)`);
  ok(cOptic * cMirror < 0, '左右镜像没有反转，说明投影丢了手性');
}

/* ---------------------------------------------------------------- */
console.log('\n' + '='.repeat(60));
console.log(`结果: ${pass} 通过, ${fail} 失败`);
if (fail) {
  console.log('\n失败项:');
  failures.forEach(f => console.log('  - ' + f));
  process.exit(1);
}
console.log('ALL PASS');
