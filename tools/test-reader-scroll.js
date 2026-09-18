/* =====================================================================
   test-reader-scroll.js — 验证阶段 2 阅读器的「左右独立滚动 + 按段落配对同步」。

   为什么要单独测：中英文同一段的渲染高度差别很大（中文更短、英文更长），
   若按「滚动比例」同步，误差会随文章长度累积，读到后面就对不上了。
   页面因此改成按「段落配对」对齐 —— 这个测试用虚拟布局验证它确实对齐。

   虚拟布局：段落高度按纯文本「字符数/每行字符数」估算，
   中英文给不同的每行字符数，从而复现真实的高度差。

   用法：node tools/test-reader-scroll.js
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const PAGE = path.join(ROOT, 'phase2.html');

let pass = 0, fail = 0;
const failures = [];
function ok(cond, msg) {
  if (cond) { pass++; } else { fail++; failures.push(msg); console.log('  FAIL  ' + msg); }
}
function section(t) { console.log('\n' + t); console.log('-'.repeat(t.length)); }
function info(t) { console.log('  ' + t); }

/* ================================================================
   虚拟布局参数
   ================================================================ */
const LINE = { orig: 26.5, trans: 29 };      // 行高（px）
const PERLINE = { orig: 78, trans: 44 };     // 每行可容纳的「显式宽度」单位
const SECH = 46;                             // 章节标题高度

/* 显式宽度：CJK 记 2，其余记 1 */
function width(str) {
  const s = String(str).replace(/<[^>]+>/g, '').replace(/&[a-z]+;/g, 'x');
  let w = 0;
  for (const ch of s) w += (ch.charCodeAt(0) > 0x2e80) ? 2 : 1;
  return w;
}
/** 含内联标签的富文本 → 估算高度 */
function textHeight(html, side) {
  const t = String(html).replace(/<sup>[\s\S]*?<\/sup>/g, '^')
    .replace(/<[^>]+>/g, ' ');
  const lines = Math.max(1, Math.ceil(width(t) / PERLINE[side]));
  return lines * LINE[side];
}

/* ================================================================
   假 DOM
   ================================================================ */
function makeClassList() {
  const s = new Set();
  return {
    _set: s,
    add: c => s.add(c), remove: c => s.delete(c), contains: c => s.has(c),
    toggle: (c, on) => {
      if (on === undefined) { s.has(c) ? s.delete(c) : s.add(c); }
      else if (on) s.add(c); else s.delete(c);
    }
  };
}

/** 排版块：一对 paragraph 占位 */
let UID = 0;
function makeBlock(id, side) {
  return { id, side, top: 0, h: 0, uid: ++UID };
}

const els = {};
function makeEl(tag, id) {
  const el = {
    tagName: (tag || 'div').toUpperCase(), id: id || '',
    dataset: {}, style: {}, value: '', checked: false,
    textContent: '', innerHTML: '', href: '', target: '', rel: '',
    children: [], _ev: {}, _attr: {},
    classList: makeClassList(),
    scrollTop: 0,
    get scrollHeight() { return el._scrollHeight || 500; },
    set scrollHeight(v) { el._scrollHeight = v; },
    get clientHeight() { return el._clientHeight || 500; },
    set clientHeight(v) { el._clientHeight = v; },
    _scrollHeight: 500, _clientHeight: 500,
    addEventListener(t, fn) { (el._ev[t] = el._ev[t] || []).push(fn); },
    removeEventListener() {},
    appendChild(c) { el.children.push(c); return c; },
    removeChild(c) { return c; },
    focus() {}, click() {},
    closest() { return null; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    getAttribute(a) { return el._attr[a] !== undefined ? el._attr[a] : null; },
    fire(type, ev) {
      const e = Object.assign({
        preventDefault() {}, stopPropagation() {}, target: el, ctrlKey: false, key: ''
      }, ev || {});
      (el._ev[type] || []).forEach(fn => fn.call(el, e));
    }
  };
  // 关键：scrollTop 被赋值时触发 scroll 事件（真实浏览器的行为）
  let st = 0;
  Object.defineProperty(el, 'scrollTop', {
    get() { return st; },
    set(v) {
      const nv = Math.max(0, Math.min(Number(v) || 0, Math.max(0, el.scrollHeight - el.clientHeight)));
      if (nv === st) return;
      st = nv;
      // 异步派发，模拟浏览器
      setTimeout(() => el.fire('scroll', {}), 0);
    },
    enumerable: true, configurable: true
  });
  let cls = '';
  Object.defineProperty(el, 'className', {
    get() { return cls; },
    set(v) {
      cls = String(v);
      el.classList._set.clear();
      cls.split(/\s+/).filter(Boolean).forEach(c => el.classList._set.add(c));
    },
    enumerable: true, configurable: true
  });
  // innerHTML 赋值时重建虚拟布局
  let html = '';
  Object.defineProperty(el, 'innerHTML', {
    get() { return html; },
    set(v) { html = String(v); if (el._onHtml) el._onHtml(html); },
    enumerable: true, configurable: true
  });
  return el;
}

/* ---------- 两个滚动容器 + 各自内容区 ---------- */
const IDS = ['paperList', 'secList', 'paperHead', 'origCol', 'transCol', 'progStat',
  'licenseNote', 'footNote', 'barMeta', 'cbSync', 'cbAnno', 'cbPaper',
  'origScroll', 'transScroll', 'scrOrig', 'scrTrans', 'backToHead'];
IDS.forEach(i => { els[i] = makeEl(/^cb/.test(i) ? 'input' : 'div', i); });
els.cbSync.checked = true; els.cbAnno.checked = true; els.cbPaper.checked = true;
els.origScroll.id = 'origScroll'; els.transScroll.id = 'transScroll';
els.origScroll.clientHeight = 640; els.transScroll.clientHeight = 640;

/* 每个 pane 的虚拟块列表 */
const blocks = { orig: [], trans: [] };   // side -> [block]
const byId = {};                           // 'p-3' / 'p-3-t' -> block
const secPos = { orig: {}, trans: {} };    // anchor -> top
/** 段落 id 归一化：'p-3' 与 'p-3-t' 都归到 'p-3' */
function baseId(id) { return String(id).replace(/-t$/, ''); }

function buildLayout(side) {
  const html = (side === 'orig' ? els.origCol.innerHTML : els.transCol.innerHTML);
  secPos[side] = {};
  // 按出现顺序切出 secblock（章节标题 + 段落 + 图）
  const list = [];
  const re = /<div class="secblock"[^>]*id="([^"]*)"[^>]*>([\s\S]*?)(?=<div class="secblock"|$)/g;
  let m;
  while ((m = re.exec(html)) !== null) list.push({ anchor: m[1], chunk: m[2] });
  const out = [];
  let top = 0;
  for (const { anchor, chunk } of list) {
    secPos[side][anchor] = top;
    // 章节标题
    if (/<(h2|h3)[^>]*>/.test(chunk)) top += SECH;
    // 段落对
    const pairRe = /<div class="pair" id="([^"]+)">([\s\S]*?)<\/div>\s*(?=<div class="pair"|<figure|<\/div>|$)/g;
    let p;
    while ((p = pairRe.exec(chunk)) !== null) {
      const pid = p[1];
      const body = p[2];
      let extra = 0;
      const annos = body.match(/<div class="anno[\s\S]*?<\/div>\s*<\/div>/g) || [];
      annos.forEach(a => { extra += textHeight(a, side) + 46; });
      const bh = textHeight(body, side) + 22 + extra;
      const b = makeBlock(pid, side);
      b.top = top; b.h = bh;
      top += bh;
      out.push(b);
    }
    // 图
    const figs = (chunk.match(/<figure class="fig"/g) || []).length;
    top += figs * 260;
  }
  blocks[side] = out;
  for (const b of out) byId[b.id] = b;
  const pane = side === 'orig' ? els.origScroll : els.transScroll;
  pane.scrollHeight = Math.max(top + 40, pane.clientHeight + 1);
  return out;
}
els.origCol._onHtml = () => buildLayout('orig');
els.transCol._onHtml = () => buildLayout('trans');

/* 元素的 getBoundingClientRect 依据虚拟布局 */
function rectFor(el) {
  // 从 id 找到块；'p-N' 在 orig，'p-N-t' 在 trans
  const isTrans = /-t$/.test(el.id);
  const pid = isTrans ? el.id.slice(0, -2) : el.id;
  const b = byId[isTrans ? el.id : pid];
  const side = isTrans ? 'trans' : 'orig';
  const pane = side === 'trans' ? els.transScroll : els.origScroll;
  if (!b || b.side !== side) {
    return { left: 0, top: 0, width: 600, height: 20, bottom: 20 };
  }
  const top = b.top - pane.scrollTop;
  return { left: 0, top, width: 600, height: b.h, bottom: top + b.h };
}

const document = {
  body: makeEl('body'),
  getElementById(id) {
    if (els[id]) return els[id];
    if (byId[id]) return byId[id]._el || (byId[id]._el = mkPairEl(id));
    // 章节锚点（只用于滚动定位）
    for (const side of ['orig', 'trans']) {
      if (secPos[side] && secPos[side][id] !== undefined) {
        const e = mkSecEl(id, side, secPos[side][id]);
        return e;
      }
    }
    return null;
  },
  querySelector: () => null,
  querySelectorAll(sel) {
    const want = String(sel).trim();
    if (want === '.pair') {
      return blocks.orig.map(b => b._el || (b._el = mkPairEl(b.id)));
    }
    if (want === '.pair.hot') {
      return blocks.orig.map(b => b._el || (b._el = mkPairEl(b.id)))
        .filter(e => e.classList.contains('hot'));
    }
    if (want === '.anno') return [];
    return [];
  },
  createElement: t => makeEl(t),
  addEventListener() {}
};

function mkPairEl(id) {
  const e = makeEl('div', id);
  e.getBoundingClientRect = () => rectFor(e);
  return e;
}

/** 章节标题元素：只有位置，没有内容 */
function mkSecEl(anchor, side, top) {
  const e = makeEl('div', anchor);
  const pane = side === 'orig' ? els.origScroll : els.transScroll;
  e.getBoundingClientRect = () => {
    const t = top - pane.scrollTop;
    return { left: 0, top: t, width: 600, height: SECH, bottom: t + SECH };
  };
  return e;
}

/* 内容区也要能查到自己的段落 —— 页面用 origCol.querySelectorAll('.pair') 建映射。
   注意这里只返回原文侧的块（页面就是这么用的）。 */
els.origCol.querySelectorAll = function (sel) {
  if (String(sel).trim() === '.pair') {
    return blocks.orig.map(b => b._el || (b._el = mkPairEl(b.id)));
  }
  return [];
};
els.transCol.querySelectorAll = function () { return []; };

/* 目录锚点也要能查到 */
els.secList.querySelectorAll = function (sel) {
  if (String(sel).trim() !== 'a') return [];
  return (RD && RD.state ? RD.state.sections : []).map(s => {
    const a = makeEl('a');
    a._attr.href = '#' + s.anchor;
    return a;
  });
};
// 内容区与容器本身也需要 rect
els.origCol.getBoundingClientRect = () => ({
  left: 0, top: -els.origScroll.scrollTop, width: 600,
  height: els.origScroll.scrollHeight, bottom: 0
});
els.transCol.getBoundingClientRect = () => ({
  left: 0, top: -els.transScroll.scrollTop, width: 600,
  height: els.transScroll.scrollHeight, bottom: 0
});
els.origScroll.getBoundingClientRect = () => ({ left: 0, top: 0, width: 600, height: 640, bottom: 640 });
els.transScroll.getBoundingClientRect = () => ({ left: 0, top: 0, width: 600, height: 640, bottom: 640 });

/* ================================================================
   装载页面
   ================================================================ */
section('0. 装载');
const html = fs.readFileSync(PAGE, 'utf8');
const externals = [];
let inlineCode = null;
{
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const s = /src\s*=\s*["']([^"']+)["']/.exec(m[1]);
    if (s) externals.push(s[1]); else if (m[2].trim()) inlineCode = m[2];
  }
}
info(`外部脚本 ${externals.length} 个`);

const sandbox = {
  console, Math, JSON, Array, Object, String, Number, Boolean, Error, Set, Map, Date,
  isNaN, parseFloat, parseInt, Promise, setTimeout, clearTimeout,
  requestAnimationFrame: fn => { fn(); return 1; },
  document, window: null
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.addEventListener = function () {};
sandbox.scrollTo = function () {};
const ctx = vm.createContext(sandbox);

let loadErr = null;
try {
  for (const e of externals) {
    const p = path.join(ROOT, e.replace(/\//g, path.sep));
    if (fs.existsSync(p)) vm.runInContext(fs.readFileSync(p, 'utf8'), ctx, { filename: e });
  }
  vm.runInContext(inlineCode, ctx, { filename: 'phase2-inline.js' });
} catch (e) { loadErr = e; }
ok(!loadErr, '装载/初始化抛异常: ' + (loadErr && loadErr.message));
if (loadErr) { console.log(loadErr && loadErr.stack); process.exit(1); }

const RD = sandbox.__rd;
ok(!!RD, '未暴露 __rd');
ok(typeof RD.scrollToAnchor === 'function', '缺少 scrollToAnchor 钩子');
ok(typeof RD.pairCount === 'function', '缺少 pairCount 钩子');

const wait = (ms) => new Promise(r => setTimeout(r, ms === undefined ? 25 : ms));

(async function main() {
  section('1. 两栏各自拥有独立滚动区');
  ok(!!els.origScroll && !!els.transScroll, '缺少左右滚动容器');
  buildLayout('orig'); buildLayout('trans');
  RD.buildMap();
  info(`原文段落块 ${blocks.orig.length} 个，高度 ${els.origScroll.scrollHeight}`);
  info(`译文段落块 ${blocks.trans.length} 个，高度 ${els.transScroll.scrollHeight}`);
  ok(blocks.orig.length > 100, `原文块数偏少: ${blocks.orig.length}`);
  ok(blocks.trans.length === blocks.orig.length,
    `两侧块数应相同: ${blocks.orig.length} vs ${blocks.trans.length}`);
  ok(RD.pairCount() === blocks.orig.length, `配对映射数 ${RD.pairCount()} 与块数不符`);
  const ho = els.origScroll.scrollHeight, ht = els.transScroll.scrollHeight;
  ok(ho !== ht, '两侧总高度应不同（这正是需要对段落配对同步的原因）');
  info(`高度比 原文/译文 = ${(ho / ht).toFixed(2)}`);

  section('2. 中文侧滚动 → 英文侧跟随到同一段');
  // 把中文滚到大约 1/3 处
  const t1 = Math.round(els.transScroll.scrollHeight * 0.33);
  els.transScroll.scrollTop = t1;
  await wait();
  info(`译文 scrollTop=${els.transScroll.scrollTop}`);
  info(`原文 scrollTop=${els.origScroll.scrollTop}`);
  ok(els.origScroll.scrollTop > 0, '原文侧未跟随滚动');
  // 校验：两侧顶部的段落 id 应相同（或相差极小）
  const idT = RD.hot();
  ok(!!idT, '未记录当前配对段落');
  // 顶部所在段落在两侧的偏移应接近
  function topPair(pane, side) {
    const list = blocks[side];
    let cur = null;
    for (const b of list) { if (b.top - pane.scrollTop <= 90) cur = b; else break; }
    return cur;
  }
  const bT = topPair(els.transScroll, 'trans');
  const bO = topPair(els.origScroll, 'orig');
  info(`译文顶部段=${bT && bT.id}  原文顶部段=${bO && bO.id}`);
  ok(bT && bO && baseId(bT.id) === baseId(bO.id),
    `两侧顶部段落不一致: ${bT && bT.id} vs ${bO && bO.id}`);
  RD.buildMap();

  section('3. 英文侧滚动 → 中文侧跟随到同一段');
  els.origScroll.scrollTop = 0; els.transScroll.scrollTop = 0;
  await wait();
  const o2 = Math.round(els.origScroll.scrollHeight * 0.72);
  els.origScroll.scrollTop = o2;
  await wait();
  info(`原文 scrollTop=${els.origScroll.scrollTop}`);
  info(`译文 scrollTop=${els.transScroll.scrollTop}`);
  ok(els.transScroll.scrollTop > 0, '译文侧未跟随滚动');
  const bO2 = topPair(els.origScroll, 'orig');
  const bT2 = topPair(els.transScroll, 'trans');
  info(`原文顶部段=${bO2 && bO2.id}  译文顶部段=${bT2 && bT2.id}`);
  ok(bO2 && bT2 && baseId(bO2.id) === baseId(bT2.id),
    `反向同步未按段落对齐: ${bO2 && bO2.id} vs ${bT2 && bT2.id}`);

  section('4. 比例同步会漂移 —— 段落配对不会（对照实验）');
  // 若按比例同步，原文 72% 处对应的译文位置：
  const ratioTarget = Math.round(els.transScroll.scrollHeight * (o2 / els.origScroll.scrollHeight));
  const actual = els.transScroll.scrollTop;
  const drift = Math.abs(actual - ratioTarget);
  info(`按比例应滚到 ${ratioTarget}，实际按段落对齐滚到 ${actual}，相差 ${drift}px`);
  // 说明：两者不相等正说明页面没有按比例同步
  ok(true, '');   // 仅记录
  const driftLimit = 5;   // px
  info(drift > driftLimit
    ? `→ 比例同步在此处会偏差 ${drift}px，段落配对把它纠回 0`
    : '→ 本例两者接近');
  // 真正的断言：段落对齐 —— 顶部段落一致
  ok(baseId(bO2.id) === baseId(bT2.id), '段落对齐失败');

  section('5. 关掉同步后两栏独立');
  els.cbSync.checked = false;
  els.cbSync.fire('change', {});
  els.origScroll.scrollTop = 0; els.transScroll.scrollTop = 0;
  await wait();
  els.transScroll.scrollTop = 500;
  await wait();
  info(`关闭同步后：译文=${els.transScroll.scrollTop} 原文=${els.origScroll.scrollTop}`);
  ok(els.origScroll.scrollTop === 0, '关闭同步后原文侧不应跟随');
  els.cbSync.checked = true;
  els.cbSync.fire('change', {});
  await wait();

  section('6. 目录点击：两栏一起跳到该章节');
  const sec0 = RD.state.sections[3] || RD.state.sections[0];
  RD.scrollToAnchor(sec0.anchor, 'orig');
  await wait();
  const secEl = document.getElementById(sec0.anchor);
  info(`跳转到章节「${sec0.title}」`);
  info(`原文 scrollTop=${els.origScroll.scrollTop} 译文=${els.transScroll.scrollTop}`);
  ok(els.origScroll.scrollTop > 0, '原文未跳到章节位置');
  ok(els.transScroll.scrollTop > 0, '译文未跟随跳转');
  if (secEl) {
    const rel = secEl.getBoundingClientRect().top
      - els.origScroll.getBoundingClientRect().top + els.origScroll.scrollTop;
    ok(rel > 0, '目标章节位置异常');
  }

  section('7. 切换论文后滚动位置归零且映射重建');
  const other = RD.papers.find(p => p.id !== RD.state.id);
  RD.select(other.id);
  await wait();
  ok(els.origScroll.scrollTop === 0, '切换论文后原文未回到开头');
  ok(els.transScroll.scrollTop === 0, '切换论文后译文未回到开头');
  buildLayout('orig'); buildLayout('trans');
  RD.buildMap();
  ok(RD.pairCount() > 0, '切换论文后配对映射为空');
  info(`切换后配对 ${RD.pairCount()} 段`);

  section('8. 无抖动：同步不应互相触发形成回环');
  els.origScroll.scrollTop = 0; els.transScroll.scrollTop = 0;
  await wait();
  els.transScroll.scrollTop = Math.round(els.transScroll.scrollHeight * 0.5);
  await wait(60);
  const a1 = els.origScroll.scrollTop, b1 = els.transScroll.scrollTop;
  await wait(60);
  const a2 = els.origScroll.scrollTop, b2 = els.transScroll.scrollTop;
  info(`稳定前 原文=${a1} 译文=${b1} → 稳定后 原文=${a2} 译文=${b2}`);
  ok(a1 === a2 && b1 === b2, '滚动位置在反复变动（存在回环抖动）');

  section('9. 两栏都有独立的滚动条与百分比显示');
  ok(els.scrOrig && els.scrTrans, '缺少滚动百分比显示元素');
  els.transScroll.scrollTop = els.transScroll.scrollHeight;
  await wait();
  info(`滚到底：原文 ${els.scrOrig.textContent} / 译文 ${els.scrTrans.textContent}`);
  ok(/%$/.test(els.scrOrig.textContent), '原文百分比未更新');
  ok(/%$/.test(els.scrTrans.textContent), '译文百分比未更新');
  // 同步生效时两栏都在底部，百分比应一致
  // （曾经因为被同步那侧的 scroll 事件被锁跳过，导致百分比不一致）
  ok(els.scrOrig.textContent === els.scrTrans.textContent,
    `两侧百分比应一致，实际 原文 ${els.scrOrig.textContent} / 译文 ${els.scrTrans.textContent}`);
  els.origScroll.scrollTop = 0;
  await wait();
  info(`回到开头：原文 ${els.scrOrig.textContent} / 译文 ${els.scrTrans.textContent}`);
  ok(els.scrOrig.textContent === '0%' && els.scrTrans.textContent === '0%',
    `回到开头两侧都应为 0%，实际 原文 ${els.scrOrig.textContent} / 译文 ${els.scrTrans.textContent}`);

  console.log('\n' + '='.repeat(62));
  console.log(`结果: ${pass} 通过, ${fail} 失败`);
  if (fail) {
    console.log('\n失败项:');
    failures.forEach(f => console.log('  - ' + f));
    process.exit(1);
  }
  console.log('ALL PASS');
})().catch(e => {
  console.log('\n测试台自身出错: ' + (e && e.stack || e));
  process.exit(1);
});
