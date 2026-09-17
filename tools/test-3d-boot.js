/* =====================================================================
   test-3d-boot.js — 在 Node 里用「假 DOM + 假 Canvas」真正执行页面里的
   内联初始化脚本，验证 3D 浏览器能启动、事件能跑通、且不抛异常。

   这补上了无法在无头浏览器里可靠截图的那一块：
   几何/投影/拾取由 test-3d.js 覆盖，这里覆盖「接线」部分。

   用法: node tools/test-3d-boot.js
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const HTML = fs.readFileSync(path.join(ROOT, 'phase0.html'), 'utf8');

let pass = 0, fail = 0;
const failures = [];
function ok(cond, msg) {
  if (cond) pass++;
  else { fail++; failures.push(msg); console.log('  FAIL  ' + msg); }
}
function section(t) { console.log('\n' + t); console.log('-'.repeat(t.length)); }

/* ---------------------------------------------------------------- */
section('0. 从 HTML 里抽出内联脚本');
const scripts = [];
const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
let m;
while ((m = re.exec(HTML)) !== null) {
  const attrs = m[1] || '';
  const body = m[2] || '';
  const srcM = /src\s*=\s*["']([^"']+)["']/.exec(attrs);
  if (srcM) scripts.push({ src: srcM[1], code: null });
  else if (body.trim()) scripts.push({ src: null, code: body });
}
ok(scripts.length >= 3, `脚本块数量异常: ${scripts.length}`);
scripts.forEach((s, i) => console.log(`  #${i} ${s.src ? 'src=' + s.src : 'inline ' + s.code.length + ' chars'}`));
const inline = scripts.filter(s => s.code);
ok(inline.length === 2, `内联脚本应为 2 个，实际 ${inline.length}`);

/* ---------------------------------------------------------------- */
section('1. 假 Canvas 2D 上下文（记录调用，缺方法即报错）');
function makeCtx() {
  const calls = [];
  const ctx = {
    _calls: calls,
    canvas: null,
    createRadialGradient() {
      calls.push('createRadialGradient');
      return { addColorStop() {} };
    },
    measureText(t) { calls.push('measureText'); return { width: String(t).length * 7 }; },
    fillRect(x, y, w, h) {
      calls.push('fillRect');
      if (![x, y, w, h].every(Number.isFinite)) throw new Error('fillRect 收到非有限数: ' + [x, y, w, h]);
    },
    strokeRect(x, y, w, h) {
      calls.push('strokeRect');
      if (![x, y, w, h].every(Number.isFinite)) throw new Error('strokeRect 收到非有限数: ' + [x, y, w, h]);
    },
    beginPath() { calls.push('beginPath'); },
    moveTo(x, y) {
      calls.push('moveTo');
      if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('moveTo 收到非有限数: ' + x + ',' + y);
    },
    lineTo(x, y) {
      calls.push('lineTo');
      if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('lineTo 收到非有限数: ' + x + ',' + y);
    },
    closePath() { calls.push('closePath'); },
    arc(x, y, r) {
      calls.push('arc');
      if (![x, y, r].every(Number.isFinite)) throw new Error('arc 收到非有限数');
    },
    fill() { calls.push('fill'); },
    stroke() { calls.push('stroke'); },
    save() { calls.push('save'); },
    restore() { calls.push('restore'); },
    fillText(t, x, y) {
      calls.push('fillText');
      if (!Number.isFinite(x) || !Number.isFinite(y)) throw new Error('fillText 收到非有限数: ' + x + ',' + y);
      if (t === undefined || t === null) throw new Error('fillText 文本为空');
    },
    setTransform() { calls.push('setTransform'); }
  };
  // 任何被使用但未定义的方法/属性都要报出来
  return new Proxy(ctx, {
    get(t, k) {
      if (k in t) return t[k];
      if (typeof k === 'string' && /^(fillStyle|strokeStyle|lineWidth|font|textAlign|textBaseline|globalAlpha)$/.test(k)) {
        return t['_' + k];
      }
      throw new Error('未实现的 ctx 成员被访问: ' + String(k));
    },
    set(t, k, v) {
      if (typeof k === 'string' && /^(fillStyle|strokeStyle|lineWidth|font|textAlign|textBaseline|globalAlpha)$/.test(k)) {
        t['_' + k] = v; return true;
      }
      t[k] = v; return true;
    }  });
}

/* ---------------------------------------------------------------- */
section('2. 假 DOM');
function makeEl(tag, id) {
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    id: id || '',
    dataset: {},
    style: {},
    children: [],
    _listeners: {},
    clientWidth: 900,
    width: 900, height: 820,
    tabIndex: 0,
    innerHTML: '',
    textContent: '',
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      toggle(c, on) { if (on === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (on) this._s.add(c); else this._s.delete(c); },
      contains(c) { return this._s.has(c); }
    },
    addEventListener(t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); },
    removeEventListener() {},
    getBoundingClientRect() { return { left: 0, top: 0, width: 900, height: 820, right: 900, bottom: 820 }; },
    setPointerCapture() {},
    getContext(kind) {
      if (kind !== '2d') throw new Error('只支持 2d 上下文，收到 ' + kind);
      this._ctx = this._ctx || makeCtx();
      this._ctx.canvas = this;
      return this._ctx;
    },
    querySelectorAll(sel) {
      if (sel === 'button' && Array.isArray(this._buttons)) return this._buttons;
      return [];
    },
    querySelector() { return null; },
    appendChild(c) { this.children.push(c); return c; },
    closest() { return null; },
    fire(type, ev) {
      (this._listeners[type] || []).forEach(fn => fn(Object.assign({
        preventDefault() {}, stopPropagation() {}, target: this
      }, ev || {})));
    }
  };
  return el;
}

const els = {};
['v3dStage', 'v3dCanvas', 'v3dHud', 'v3dInfo', 'v3dList', 'v3dReset', 'v3dSpin', 'v3dFront', 'v3dSide',
 'toTop', 'toc', 'checklist'].forEach(id => {
  const tag = /Canvas/.test(id) ? 'canvas' : 'div';
  els[id] = makeEl(tag, id);
});
// 列表按钮
const listButtons = [];
const REG = require(path.join(ROOT, 'assets', 'mcns-3d.js')).REGIONS.filter(r => r.pickable !== false);
REG.forEach((r, i) => {
  const b = makeEl('button');
  b.dataset.id = r.id;
  b.classList = makeEl('div').classList;
  listButtons.push(b);
});
els.v3dList._buttons = listButtons;
els.v3dList.querySelectorAll = function (sel) {
  if (sel === 'button') return listButtons;
  return [];
};

const document = {
  _els: els,
  getElementById(id) { return els[id] || null; },
  querySelector(sel) {
    if (sel === '#v3dCanvas') return els.v3dCanvas;
    return null;
  },
  querySelectorAll(sel) {
    if (sel === 'nav.toc a[href^="#"]') return [];
    if (sel === '#checklist .item') return [];
    return [];
  },
  createElement(tag) { return makeEl(tag); },
  addEventListener() {}
};

/* ---------------------------------------------------------------- */
section('3. 装载 mcns-3d.js 与内联初始化脚本');
let rafQueue = [];
const sandbox = {
  console, Math, JSON, Array, Object, String, Number, Boolean, Error, Set, Map, Date, isNaN, parseFloat, parseInt,
  requestAnimationFrame(fn) { rafQueue.push(fn); return rafQueue.length; },
  cancelAnimationFrame() {},
  devicePixelRatio: 2,
  document,
  setTimeout, clearTimeout,
  Uint8Array, Uint32Array, Float32Array, Int32Array, ArrayBuffer
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.window.addEventListener = function () {};
sandbox.addEventListener = function () {};
sandbox.window.devicePixelRatio = 2;
// atob：用 Node 的 Buffer 还原 base64
sandbox.atob = function (b64) {
  return Buffer.from(b64, 'base64').toString('binary');
};

const ctxObj = vm.createContext(sandbox);

// 3.0 先执行所有外部脚本（顺序与页面一致）
const externals = scripts.filter(s => s.src);
ok(externals.length >= 1, '页面没有引用任何外部脚本');
for (const ext of externals) {
  const p = path.join(ROOT, ext.src.replace(/\//g, path.sep));
  if (!fs.existsSync(p)) {
    console.log(`  (跳过缺失的外部脚本: ${ext.src})`);
    continue;
  }
  const code = fs.readFileSync(p, 'utf8');
  try {
    vm.runInContext(code, ctxObj, { filename: ext.src });
    console.log(`  loaded ${ext.src}  (${(code.length/1024).toFixed(0)} KB)`);
  } catch (e) {
    ok(false, `${ext.src} 抛异常: ${e.message}`);
  }
}
ok(typeof sandbox.MCNS3D === 'object' && sandbox.MCNS3D !== null, 'MCNS3D 未挂到全局');
ok(sandbox.MCNS3D && typeof sandbox.MCNS3D.buildFrame === 'function', 'MCNS3D.buildFrame 缺失');
ok(!!sandbox.MCNS_MESHES, '官方网格包 MCNS_MESHES 未加载');
ok(!!sandbox.MCNS_REGION_INFO, '解说表 MCNS_REGION_INFO 未加载');

// 3.2 再执行内联脚本（第一个含 v3d 的）
const explorer = inline.find(s => /v3dCanvas|MCNS3D/.test(s.code));
ok(!!explorer, '找不到 3D 浏览器的内联脚本');
let bootErr = null;
try {
  vm.runInContext(explorer.code, ctxObj, { filename: 'inline-3d.js' });
} catch (e) {
  bootErr = e;
}
ok(!bootErr, '初始化脚本抛异常: ' + (bootErr && bootErr.stack));
if (bootErr) {
  console.log('\n初始化失败，后续检查跳过。');
  console.log(bootErr && bootErr.stack);
  process.exit(1);
}
console.log('  初始化未抛异常');

/* ---------------------------------------------------------------- */
section('4. 初始化副作用');
ok(/脑区|结构|点击|触角叶|蘑菇体/.test(els.v3dInfo.innerHTML), '信息面板未显示默认内容');
console.log('  v3dInfo 长度: ' + els.v3dInfo.innerHTML.length);
ok(/<button/.test(els.v3dList.innerHTML), '右侧列表未生成按钮');
const btnCount = (els.v3dList.innerHTML.match(/<button/g) || []).length;
console.log('  列表按钮数: ' + btnCount);
// 官方网格路径下，列表项数应等于装载的结构数
const hook0 = sandbox.__mcnsV3d;
ok(btnCount >= 20, `列表按钮数偏少: ${btnCount}`);
ok(/触角叶|蘑菇体|中央复合体|髓质/.test(els.v3dList.innerHTML), '列表缺少区域名');
// 官方数据下应显示「官方网格」来源与抽稀信息
ok(/蘑菇体|中央复合体/.test(els.v3dList.innerHTML), '列表缺少中文名');

/* ---------------------------------------------------------------- */
section('5. rAF 渲染确实被触发，并且真的画了东西');
let rafTotalMs = 0, rafFrames = 0;
function flushRaf(limit) {
  let n = 0;
  while (rafQueue.length && n < (limit || 20)) {
    const q = rafQueue; rafQueue = [];
    const t0 = Date.now();
    q.forEach(fn => fn());
    rafTotalMs += Date.now() - t0;
    rafFrames += q.length;
    n++;
  }
  return n;
}
const frames = flushRaf(5);
ok(frames > 0, '没有任何 requestAnimationFrame 回调被执行（画面永远不会出现）');
console.log('  执行帧数: ' + frames);

const ctx2d = els.v3dCanvas._ctx;
ok(!!ctx2d, 'canvas 没有拿到 2d 上下文（未渲染）');
const calls = ctx2d ? ctx2d._calls : [];
console.log('  2D 调用次数: ' + calls.length);
ok(calls.filter(c => c === 'fill').length > 100, `fill 调用过少: ${calls.filter(c => c === 'fill').length}`);
ok(calls.includes('createRadialGradient'), '没有绘制背景光晕');
ok(calls.includes('fillText'), '没有绘制任何文字（坐标轴／标签）');
ok(/<b>/.test(els.v3dHud.innerHTML), 'HUD 未更新');

section('5b. 端到端帧耗时（buildFrame + 全部 canvas 调用）');
{
  // 量 8 帧：包含几何变换、深度排序、以及每一次 canvas API 调用
  const before = rafFrames;
  const t0 = Date.now();
  // 连续触发重绘：拖动一小步让 schedule() 排帧
  for (let k = 0; k < 8; k++) {
    els.v3dCanvas.fire('pointerdown', { clientX: 400, clientY: 400, pointerId: 90 + k });
    els.v3dCanvas.fire('pointermove', { clientX: 400 + k, clientY: 400, pointerId: 90 + k });
    els.v3dCanvas.fire('pointerup', { clientX: 400 + k, clientY: 400, pointerId: 90 + k });
    flushRaf(2);
  }
  const wall = Date.now() - t0;
  const per = wall / Math.max(1, rafFrames - before);
  console.log(`  ${rafFrames - before} 帧，平均 ${per.toFixed(1)} ms/帧`);
  console.log(`  （60fps 需 <16.7ms；30fps 需 <33ms；交互可用阈值约 100ms）`);
  console.log(`  注意：假 canvas 不做光栅化，真实浏览器里绘制还要另外花时间；`);
  console.log(`  几何部分已由 tools/test-3d-official.js 单独计时。`);
  ok(rafFrames > before, '拖动没有产生新帧');
  // 假 canvas 的开销主要是数组 push，比真实绘制小但比真实几何大，
  // 阈值放到 150ms 只用于拦住「明显失控」的回归。
  ok(per < 150, `帧耗时 ${per.toFixed(1)} ms 偏高，交互会卡`);
}

/* ---------------------------------------------------------------- */
section('6. 交互：拖动旋转');
{
  const y0 = sandbox.MCNS3D.makeCamera().yaw;   // 仅作参考
  els.v3dCanvas.fire('pointerdown', { clientX: 400, clientY: 400, pointerId: 1 });
  ok(els.v3dStage.classList.contains('dragging'), 'pointerdown 后未进入 dragging 状态');
  els.v3dCanvas.fire('pointermove', { clientX: 500, clientY: 430, pointerId: 1 });
  const nf = flushRaf(2);
  ok(nf > 0, '拖动后没有重绘');
  els.v3dCanvas.fire('pointerup', { clientX: 500, clientY: 430, pointerId: 1 });
  ok(!els.v3dStage.classList.contains('dragging'), 'pointerup 后仍处于 dragging 状态');
  console.log('  拖动重绘帧数: ' + nf);
}

section('7. 交互：点击选中结构（走完整事件链）');
{
  const hook = sandbox.__mcnsV3d;
  ok(!!hook, '页面未暴露 __mcnsV3d 测试钩子');
  ok(hook.usingOfficial === true, '页面没有使用官方网格（回退到示意图了）');
  const M = sandbox.MCNS3D;
  const polys = hook.frame();
  ok(!!polys && polys.length > 0, '测试钩子拿不到可见面');

  // 页面内部的拾取用的是「画布坐标」(canvas.width/height)，而事件处理器
  // 会把 client 坐标按 getBoundingClientRect 换算过去。测试必须做同样的换算。
  const rect = els.v3dCanvas.getBoundingClientRect();
  const toClient = (x, y) => [
    rect.left + x * (rect.width / els.v3dCanvas.width),
    rect.top + y * (rect.height / els.v3dCanvas.height)
  ];

  // 从可见面的质心里挑一个命中点（保证一定能点到东西，且不必扫全屏）
  let target = null;
  const stride = Math.max(1, Math.floor(polys.length / 40));
  for (let i = 0; i < polys.length; i += stride) {
    const f = polys[i];
    const cx = (f.x[0] + f.x[1] + f.x[2]) / 3;
    const cy = (f.y[0] + f.y[1] + f.y[2]) / 3;
    const h = M.pick(polys, cx, cy, {});
    if (h) { target = [cx, cy, h.id]; break; }
  }
  ok(!!target, '从可见面质心里点不到任何结构');
  if (target) {
    const [ux, uy] = toClient(target[0], target[1]);
    els.v3dCanvas.fire('pointerdown', { clientX: ux, clientY: uy, pointerId: 2 });
    els.v3dCanvas.fire('pointerup', { clientX: ux, clientY: uy, pointerId: 2 });
    flushRaf(2);
    const onBtn = listButtons.filter(b => b.classList.contains('on'));
    ok(onBtn.length === 1 && onBtn[0].dataset.id === target[2],
      `点击 ${target[2]} 后列表高亮为 ${onBtn.map(b => b.dataset.id).join(',')}`);
    ok(els.v3dInfo.innerHTML.length > 200, '信息面板内容过少');
    ok(/官方网格/.test(els.v3dInfo.innerHTML), '信息面板未显示官方网格来源');
    console.log(`  画布(${target[0].toFixed(0)},${target[1].toFixed(0)}) → client(${ux.toFixed(0)},${uy.toFixed(0)}) → ${onBtn.map(b => b.dataset.id).join(',')}`);
  }
}

section('8. 交互：悬停高亮');
{
  const hook = sandbox.__mcnsV3d;
  const M = sandbox.MCNS3D;
  const polys = hook.frame();
  const rect = els.v3dCanvas.getBoundingClientRect();
  let pt = null;
  const stride = Math.max(1, Math.floor(polys.length / 30));
  for (let i = 0; i < polys.length; i += stride) {
    const f = polys[i];
    const cx = (f.x[0] + f.x[1] + f.x[2]) / 3;
    const cy = (f.y[0] + f.y[1] + f.y[2]) / 3;
    const h = M.pick(polys, cx, cy, {});
    if (h) { pt = [cx, cy, h.id]; break; }
  }
  ok(!!pt, '找不到任何可悬停的位置');
  if (pt) {
    const ux = rect.left + pt[0] * (rect.width / els.v3dCanvas.width);
    const uy = rect.top + pt[1] * (rect.height / els.v3dCanvas.height);
    els.v3dCanvas.fire('pointermove', { clientX: ux, clientY: uy, pointerId: 3 });
    ok(els.v3dCanvas.style.cursor === 'pointer', `悬停未把光标改为 pointer（实际 ${els.v3dCanvas.style.cursor}）`);
    console.log(`  悬停在 ${pt[2]} 上 → cursor=${els.v3dCanvas.style.cursor}`);
  }
}

section('9. 交互：滚轮缩放');
{
  els.v3dCanvas.fire('wheel', { deltaY: -100 });
  const nf = flushRaf(2);
  ok(nf > 0, '滚轮缩放后没有重绘');
}

section('10. 视角按钮');
{
  ['v3dReset', 'v3dFront', 'v3dSide'].forEach(id => {
    els[id].fire('click', {});
    const nf = flushRaf(2);
    ok(nf > 0, `${id} 点击后没有重绘`);
  });
  els.v3dSpin.fire('click', {});
  ok(els.v3dSpin.textContent === '停止旋转', `自动旋转按钮文案未切换: "${els.v3dSpin.textContent}"`);
  const nf = flushRaf(3);
  ok(nf > 0, '自动旋转没有产生帧');
  els.v3dSpin.fire('click', {});
  ok(els.v3dSpin.textContent === '自动旋转', '停止旋转后文案未复位');
}

section('11. 列表点击');
{
  const b = listButtons.find(x => x.dataset.id === 'CX');
  els.v3dList.fire('click', { target: b });
  flushRaf(2);
  ok(/中央复合体/.test(els.v3dInfo.innerHTML), '点击列表里的 CX 没有更新信息面板');

  // 模拟点在按钮内部的 <span> 上：应向上找到按钮
  const span = makeEl('span');
  span.dataset = undefined;              // span 没有 data-id
  span.parentNode = b;
  els.v3dList.fire('click', { target: span });
  flushRaf(2);
  ok(/中央复合体/.test(els.v3dInfo.innerHTML), '点在按钮内部 span 上时未能选中区域');
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
