/* =====================================================================
   app.js — 左：蝇体实时画面（MJPEG）· 右：MaleCNS 脑区（可点刺激）

   右侧 3D 脑复用站点里的 assets/mcns-3d.js（纯函数：几何/投影/拾取/绘制），
   网格数据是 assets/mcns-meshes.js（官方 MaleCNS 神经毡，26 个结构）。
   点击一个脑区 → POST /stimulate → 后端往该组神经元注入电流 → 蝇体运动改变。
   ===================================================================== */
'use strict';

const $ = (s) => document.querySelector(s);
const M = window.MCNS3D;

const state = {
  groups: [],            // /groups 的目录
  byId: {},              // id → 目录项
  hz: {},                // id → 当前放电率
  meshGroups: {},        // 神经毡名 → [组 id]
  active: new Set(),     // 正在被刺激的组
  mv: 8, ms: 400,
  cam: null, meshes: null, polys: [],
  canvas: null, ctx: null, W: 0, H: 0,
  drag: null, spin: true, lastFrame: 0,
};

/* ---------------- 强度 / 时长 ---------------- */
$('#mv').addEventListener('input', (e) => { state.mv = +e.target.value; $('#mv-v').textContent = e.target.value; });
$('#ms').addEventListener('input', (e) => { state.ms = +e.target.value; $('#ms-v').textContent = e.target.value; });
$('#clear').addEventListener('click', () => {
  fetch('/stimulate', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'clear' }) });
  flash('已停止全部刺激');
});
$('#recenter').addEventListener('click', () => {
  fetch('/stimulate', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'recenter' }) });
  flash('蝇子已回到场地中心');
});

function flash(text) {
  $('#msg').textContent = text;
  clearTimeout(flash._t);
  flash._t = setTimeout(() => { $('#msg').textContent = ''; }, 2600);
}

/* ---------------- 左侧实时画面：canvas 拉帧 ----------------
   为什么不用 <img src="/stream">（multipart/x-mixed-replace）：
   Safari 对 <img> 里的 MJPEG 支持并不稳定，会出现「什么都不显示」。
   canvas 轮询 /frame 在任何浏览器里都一样，代价只是每帧一个请求。      */
function watchStream() {
  const canvas = $('#fly');
  const ctx = canvas.getContext('2d');
  const badge = $('#b-stream');
  let frames = 0, lastT = Date.now(), fails = 0, since = -1;

  async function pump() {
    try {
      const r = await fetch('/frame?since=' + since, { cache: 'no-store' });
      if (!r.ok) throw new Error(r.status);
      since = +(r.headers.get('X-Frame-Seq') || -1);
      const bmp = await createImageBitmap(await r.blob());
      if (canvas.width !== bmp.width || canvas.height !== bmp.height) {
        canvas.width = bmp.width; canvas.height = bmp.height;
      }
      ctx.drawImage(bmp, 0, 0);
      bmp.close();
      frames++; fails = 0;
    } catch (e) {
      fails++;
      if (fails > 20) {
        badge.textContent = '画面连不上后端，重试中…';
        badge.className = 'badge warn';
      }
      await new Promise((r) => setTimeout(r, 300));      // 出错时降速重试
    }
    // 每 20 帧报一次实际帧率
    const now = Date.now();
    if (frames && frames % 20 === 0) {
      const fps = 20000 / Math.max(now - lastT, 1);
      lastT = now;
      if (fails === 0) {
        badge.textContent = `画面 ${canvas.width}×${canvas.height} · ${fps.toFixed(0)} fps`;
        badge.className = 'badge ok';
      }
    }
    setTimeout(pump, 0);                                  // 服务端长轮询自带节流
  }
  pump();
}

/* ---------------- 3D 脑 ---------------- */
function initBrain() {
  const canvas = $('#brain');
  const ctx = canvas.getContext('2d');
  if (!ctx || !M || !window.MCNS_MESHES) {
    $('.stage', $('#right')).insertAdjacentHTML('beforeend',
      '<p style="padding:20px;color:#f87171">canvas 或 MCNS3D/MCNS_MESHES 未加载</p>');
    return;
  }
  state.canvas = canvas; state.ctx = ctx;

  const official = M.loadOfficialGeometry(window.MCNS_MESHES);
  state.meshes = official || M.buildMeshes(M.REGIONS, 18, 12);

  // 按包围盒自动取景，与 phase0 的 3D 浏览器同一套做法
  let bmin = [Infinity, Infinity, Infinity], bmax = [-Infinity, -Infinity, -Infinity];
  for (const mm of state.meshes) {
    const b = mm.bbox || [mm.center[0] - mm.bound, mm.center[1] - mm.bound, mm.center[2] - mm.bound,
                          mm.center[0] + mm.bound, mm.center[1] + mm.bound, mm.center[2] + mm.bound];
    for (let d = 0; d < 3; d++) { bmin[d] = Math.min(bmin[d], b[d]); bmax[d] = Math.max(bmax[d], b[d + 3]); }
  }
  const center = [0, 1, 2].map((d) => (bmin[d] + bmax[d]) / 2);
  const radius = 0.5 * Math.hypot(bmax[0] - bmin[0], bmax[1] - bmin[1], bmax[2] - bmin[2]);
  state.cam = M.makeCamera({ target: center, dist: radius * 3.0, focal: 1000 });

  resize();
  window.addEventListener('resize', resize);

  canvas.addEventListener('pointerdown', (e) => {
    state.drag = { x: e.clientX, y: e.clientY, yaw: state.cam.yaw, pitch: state.cam.pitch, moved: 0 };
    canvas.classList.add('drag'); canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!state.drag) return;
    const dx = e.clientX - state.drag.x, dy = e.clientY - state.drag.y;
    state.drag.moved += Math.abs(dx) + Math.abs(dy);
    state.cam.yaw = state.drag.yaw + dx * 0.008;
    state.cam.pitch = Math.max(-1.3, Math.min(1.3, state.drag.pitch + dy * 0.008));
    state.spin = false;
  });
  canvas.addEventListener('pointerup', (e) => {
    const wasDrag = state.drag && state.drag.moved > 6;
    state.drag = null; canvas.classList.remove('drag');
    if (!wasDrag) clickAt(e);
  });
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    state.cam.dist = Math.max(radius * 1.2, Math.min(radius * 9, state.cam.dist * (1 + Math.sign(e.deltaY) * 0.09)));
  }, { passive: false });

  requestAnimationFrame(drawBrain);
}

function resize() {
  const c = state.canvas; if (!c) return;
  const stage = c.parentElement;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  state.W = Math.max(320, Math.floor(stage.clientWidth));
  state.H = Math.max(260, Math.floor(stage.clientHeight));
  c.width = state.W * dpr; c.height = state.H * dpr;
  c.style.width = state.W + 'px'; c.style.height = state.H + 'px';
  state.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

/** 该神经毡当前的活动强度：取映射到它的组的最大放电率 */
function meshRate(meshId) {
  const gs = state.meshGroups[meshId]; if (!gs) return 0;
  let v = 0;
  for (const g of gs) v = Math.max(v, state.hz[g] || 0);
  return v;
}

function drawBrain(ts) {
  const { ctx, canvas, meshes, cam } = state;
  if (!ctx) return;
  if (state.spin && !state.drag) cam.yaw += 0.0035;
  const W = state.W, H = state.H;

  // 被刺激的组 → 高亮对应的神经毡
  const hotMeshes = new Set();
  for (const gid of state.active) {
    const g = state.byId[gid]; if (g && g.mesh) hotMeshes.add(g.mesh);
  }
  state.polys = M.buildFrame(cam, meshes, W, H, null);
  M.drawFrame(ctx, state.polys, W, H, '#05080f');

  // ---- 活动热区：在每个神经毡中心投影处画一个发光点 ----
  const maxHz = Math.max(1, ...Object.values(state.hz));
  ctx.save();
  for (const mm of meshes) {
    const id = mm.region.id;
    const hz = meshRate(id);
    if (hz <= 0.05) continue;
    const p = M.project(cam, mm.center, W, H);
    if (!p || !isFinite(p[0])) continue;
    const f = Math.min(1, Math.log1p(hz) / Math.log1p(maxHz));
    const r = 5 + 22 * f;
    const grd = ctx.createRadialGradient(p[0], p[1], 1, p[0], p[1], r);
    const hot = hotMeshes.has(id);
    grd.addColorStop(0, hot ? 'rgba(74,222,128,.85)' : 'rgba(34,211,238,.55)');
    grd.addColorStop(1, 'rgba(34,211,238,0)');
    ctx.fillStyle = grd;
    ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, Math.PI * 2); ctx.fill();

    ctx.font = '10px ui-monospace,Menlo,monospace';
    ctx.fillStyle = hot ? 'rgba(74,222,128,.95)' : 'rgba(150,190,215,.8)';
    ctx.textAlign = 'center';
    ctx.fillText(hz >= 10 ? hz.toFixed(0) : hz.toFixed(1), p[0], p[1] - r - 3);
  }
  ctx.restore();
  requestAnimationFrame(drawBrain);
}

/* ---------------- 点击 → 刺激 ---------------- */
function clickAt(e) {
  const rect = state.canvas.getBoundingClientRect();
  const hit = M.pick(state.polys, e.clientX - rect.left, e.clientY - rect.top, {});
  if (!hit) { flash('这一处没有可刺激的脑区'); return; }
  const gs = state.meshGroups[hit.id];
  if (!gs || !gs.length) { flash(`${hit.id} 还没有映射到神经元组`); return; }
  // 一个神经毡可能对应多个组：优先具名行为神经元（kind = named）
  const named = gs.find((g) => state.byId[g] && state.byId[g].kind === 'named');
  stimulate(named || gs[0], hit.id);
}

function stimulate(gid, meshName) {
  const g = state.byId[gid];
  flash(`刺激 ${g ? g.zh : gid}（${g ? g.count.toLocaleString() : '?'} 个神经元，${state.mv} mV / ${state.ms} ms）`);
  fetch('/stimulate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ group: gid, mv: state.mv, ms: state.ms }),
  }).then((r) => r.json()).then((d) => {
    if (d.error) flash('失败：' + d.error);
  }).catch((err) => flash('请求失败：' + err));
}

/* ---------------- 组列表 ---------------- */
function buildList() {
  const box = $('#groups');
  box.innerHTML = '';
  // 具名行为神经元排前面，其余按神经元数降序
  const items = state.groups.slice().sort((a, b) => {
    const an = a.kind === 'named' ? 0 : 1, bn = b.kind === 'named' ? 0 : 1;
    return an - bn || b.count - a.count;
  });
  for (const g of items) {
    const row = document.createElement('div');
    row.className = 'grp';
    row.dataset.id = g.id;
    row.innerHTML = `<span class="nm">${g.zh}</span>
      <span class="ct">${g.count.toLocaleString()}</span>
      <span class="bar"><i></i></span>
      <span class="hz">0.0 Hz</span>`;
    row.title = g.note ? `${g.id} · ${g.note}` : g.id;
    row.addEventListener('click', () => stimulate(g.id));
    box.appendChild(row);
  }
}

/* ---------------- 状态轮询 ---------------- */
async function poll() {
  try {
    const d = await (await fetch('/state')).json();
    if (d.starting) return;
    $('#h-sim').textContent = d.sim_s.toFixed(2);
    $('#h-spk').textContent = d.spikes_per_10ms.toLocaleString();
    $('#h-gait').textContent = `${d.gait[0].toFixed(2)} / ${d.gait[1].toFixed(2)}`;
    $('#h-pos').textContent = `${d.position_mm[0].toFixed(1)}, ${d.position_mm[1].toFixed(1)}`;
    $('#h-fired').textContent = d.ever_fired.toLocaleString();
    $('#h-loop').textContent = d.loop_ms.toFixed(1);
    if (d.recenters) $('#foot-note').textContent = `卡住自动回中心 ×${d.recenters}（演示便利，非蝇的行为）`;
    $('#b-rt').textContent = `${d.realtime.toFixed(3)}× 实时`;
    $('#b-rt').className = 'badge ' + (d.realtime > 0.2 ? 'ok' : 'warn');
    $('#b-neurons').textContent = `${d.neurons.toLocaleString()} 神经元`;
    state.active = new Set(d.active || []);

    const hz = {};
    for (const g of d.group_hz) hz[g.id] = g.hz;
    state.hz = hz;

    const maxHz = Math.max(1, ...Object.values(hz));
    for (const row of document.querySelectorAll('.grp')) {
      const id = row.dataset.id, v = hz[id] || 0;
      row.querySelector('.hz').textContent = v >= 10 ? v.toFixed(0) + ' Hz' : v.toFixed(1) + ' Hz';
      row.querySelector('.bar i').style.width = Math.min(100, (Math.log1p(v) / Math.log1p(maxHz)) * 100) + '%';
      row.classList.toggle('on', state.active.has(id));
      row.classList.toggle('hot', v >= 0.3 * maxHz && v > 1);
    }
  } catch (e) { /* 服务端短暂忙时忽略 */ }
}

/* ---------------- 启动 ---------------- */
(async function boot() {
  initBrain();
  watchStream();
  try {
    const d = await (await fetch('/groups')).json();
    state.groups = d.groups;
    for (const g of d.groups) state.byId[g.id] = g;
    for (const g of d.groups) {
      if (!g.mesh) continue;
      (state.meshGroups[g.mesh] = state.meshGroups[g.mesh] || []).push(g.id);
    }
    buildList();
    $('#b-neurons').textContent = `${d.neurons.toLocaleString()} 神经元`;
    $('#foot-note').textContent = `${d.groups.length} 个可刺激组 · 全部来自注释，无写死列表`;
  } catch (e) {
    flash('拿不到 /groups');
  }
  setInterval(poll, 300);
  poll();
})();
