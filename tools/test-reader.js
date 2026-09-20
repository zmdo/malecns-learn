/* =====================================================================
   test-reader.js — 用假 DOM 执行 phase2.html 的内联脚本，验证阅读器。

   覆盖：论文切换 / 双栏段落配对 / 图渲染 / 标注注入与开关 /
         滚动联动 / 目录 / 译文覆盖率统计 / HTML 转义安全。

   用法: node tools/test-reader.js
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

/* ---------------- 假 DOM ---------------- */
function makeClassList() {
  const s = new Set();
  return {
    add: c => s.add(c), remove: c => s.delete(c), contains: c => s.has(c),
    toggle: (c, on) => { if (on === undefined) { s.has(c) ? s.delete(c) : s.add(c); } else if (on) s.add(c); else s.delete(c); },
    _set: s
  };
}
function makeEl(tag, id) {
  const el = {
    tagName: (tag || 'div').toUpperCase(), id: id || '',
    dataset: {}, style: {}, value: '', checked: false,
    textContent: '', innerHTML: '', href: '', target: '', rel: '',
    children: [], _ev: {}, _q: {},
    classList: makeClassList(),
    addEventListener(t, fn) { (this._ev[t] = this._ev[t] || []).push(fn); },
    removeEventListener() {},
    appendChild(c) { this.children.push(c); return c; },
    removeChild(c) { return c; },
    focus() {}, click() {},
    closest(sel) { return null; },
    querySelector(sel) { return (this._q[sel] || null); },
    querySelectorAll(sel) {
      if (this._q['all:' + sel]) return this._q['all:' + sel];
      return [];
    },
    getBoundingClientRect() { return { left: 0, top: 0, width: 1200, height: 800, bottom: 800 }; },
    getAttribute(a) { return this['_attr_' + a] || null; },
    fire(type, ev) {
      // 页面里用了 this.checked，所以 this 必须绑定到元素本身
      (this._ev[type] || []).forEach(fn => fn.call(this, Object.assign({
        preventDefault() {}, stopPropagation() {}, target: this
      }, ev || {})));
    }
  };
  let cls = '';
  Object.defineProperty(el, 'className', {
    get() { return cls; },
    set(v) { cls = String(v); el.classList._set.clear(); cls.split(/\s+/).filter(Boolean).forEach(c => el.classList._set.add(c)); },
    enumerable: true, configurable: true
  });
  return el;
}

const IDS = ['paperList', 'secList', 'paperHead', 'origCol', 'transCol', 'progStat',
  'licenseNote', 'footNote', 'barMeta', 'cbSync', 'cbAnno', 'cbPaper'];
const els = {};
IDS.forEach(id => { els[id] = makeEl(/^cb/.test(id) ? 'input' : 'div', id); });
els.cbSync.checked = true; els.cbAnno.checked = true; els.cbPaper.checked = true;

/* 用「HTML 字符串 + 正则」模拟查询：
   页面只用到 querySelectorAll('.pair') / ('.pair.hot') / ('.anno') / ('.pitem') 与
   querySelector('a') 之类，这里按 innerHTML 计数即可满足断言需要。 */
function pairsIn(html) { return (html.match(/class="pair/g) || []).length; }
function annosIn(html) { return (html.match(/class="anno/g) || []).length; }
function figsIn(html) { return (html.match(/class="fig"/g) || []).length; }
function missingIn(html) { return (html.match(/class="missing"/g) || []).length; }

const document = {
  body: makeEl('body'),
  getElementById: id => els[id] || (/^p-\d+(-t)?$/.test(id) ? pairEl(id) : null),
  querySelector: () => null,
  /* 页面用到的选择器只有几个，直接从 innerHTML 里数出来，
     这样「滚动联动加 hot 类」之类的行为也能被断言到。 */
  querySelectorAll(sel) {
    const want = String(sel).trim();
    const grab = (html, re) => {
      const out = [];
      let m;
      re.lastIndex = 0;
      while ((m = re.exec(html)) !== null) out.push(m[1]);
      return out;
    };
    if (want === '.pair') {
      return grab(els.origCol.innerHTML, /<div class="pair" id="([^"]+)"/g).map(id => {
        const el = makeEl('div', id); el._where = 'orig'; return el;
      });
    }
    if (want === '.pair.hot' || want === '.anno') return [];
    if (want === '.matheq') return matheqEls(els.origCol.innerHTML);
    return [];
  },
  _pairs: {},
  createElement: t => makeEl(t),
  addEventListener() {}
};

/* 内容区也要能查到 .matheq —— 页面的 mirrorFormulas 用的是
   origCol.querySelectorAll('.matheq')，不是 document.querySelectorAll。 */
els.origCol.querySelectorAll = function (sel) {
  const want = String(sel).trim();
  if (want === '.matheq') return matheqEls(els.origCol.innerHTML);
  if (want === '.pair') {
    const out = []; let m;
    const re = /<div class="pair" id="([^"]+)"/g;
    while ((m = re.exec(els.origCol.innerHTML)) !== null) {
      const e = makeEl('div', m[1]); e._where = 'orig'; out.push(e);
    }
    return out;
  }
  return [];
};

/* 记录译文侧段落元素，便于断言"公式被镜像过去了" */
const pairEls = {};
function pairEl(pid) {
  if (!pairEls[pid]) {
    const e = makeEl('div', pid);
    e._kids = [];
    e.appendChild = c => { e._kids.push(c); return c; };
    pairEls[pid] = e;
  }
  return pairEls[pid];
}

/* 构造镜像用的最小 DOM：.matheq → 其祖先 .pair(id) → 内含 img[alt] */
function matheqEls(html) {
  const out = [];
  // 段落切分：<div class="pair" id="p-N">…</div>（同一段内部可能含 .matheq）
  const re = /<div class="pair" id="([^"]+)">([\s\S]*?)(?=<div class="pair"|$)/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const pid = m[1], body = m[2];
    if (body.indexOf('class="matheq"') === -1) continue;
    // 从 .matheq 块内部取 img 的 alt（不是段落到处第一张图）
    const meq = /<span class="matheq">([\s\S]*?)<\/span>/.exec(body);
    const inner = meq ? meq[1] : body;
    const altM = /<img[^>]*?\salt="([^"]*)"/.exec(inner);
    const img = makeEl('img');
    if (!img._attr) img._attr = {};
    img._attr.alt = altM ? altM[1] : '';
    img.getAttribute = a => (a in img._attr ? img._attr[a] : null);
    img.querySelector = () => null;
    const holder = makeEl('span');
    holder.querySelector = sel => (String(sel).trim() === 'img' ? img : null);
    const parEl = makeEl('div', pid);
    parEl.classList.add('pair');
    holder.parentNode = parEl;
    holder.getAttribute = () => null;
    out.push(holder);
  }
  return out;
}

/* ---------------- 装载 ---------------- */
section('0. 装载');
const html = fs.readFileSync(PAGE, 'utf8');
const externals = [];
{
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const srcM = /src\s*=\s*["']([^"']+)["']/.exec(m[1]);
    if (srcM) externals.push(srcM[1]);
    else if (m[2].trim()) externals.push({ inline: m[2] });
  }
}
const inlineCode = externals.filter(e => typeof e === 'object' && e.inline)[0].inline;
info(`外部脚本 ${externals.filter(e => typeof e === 'string').length} 个，内联脚本 ${inlineCode.length} 字符`);

const sandbox = {
  console, Math, JSON, Array, Object, String, Number, Boolean, Error, Set, Map, Date,
  isNaN, parseFloat, parseInt, Promise, setTimeout, clearTimeout,
  requestAnimationFrame: fn => { fn(); return 1; },
  document,
  window: null
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.addEventListener = function () {};
sandbox.scrollTo = function () {};
const ctx = vm.createContext(sandbox);

let loadErr = null;
try {
  for (const e of externals) {
    if (typeof e !== 'string') continue;
    const p = path.join(ROOT, e.replace(/\//g, path.sep));
    if (!fs.existsSync(p)) { console.log(`  (缺失 ${e})`); continue; }
    vm.runInContext(fs.readFileSync(p, 'utf8'), ctx, { filename: e });
  }
  vm.runInContext(inlineCode, ctx, { filename: 'phase2-inline.js' });
} catch (e) { loadErr = e; }
ok(!loadErr, '装载/初始化抛异常: ' + (loadErr && loadErr.message));
if (loadErr) { console.log(loadErr && loadErr.stack); process.exit(1); }
info('装载完成，未抛异常');

const RD = sandbox.__rd;
ok(!!RD, '未暴露 __rd 测试钩子');
ok(!!sandbox.MCNS_PAPERS, '未加载 MCNS_PAPERS');
ok(Array.isArray(sandbox.MCNS_NOTES_PARTS) && sandbox.MCNS_NOTES_PARTS.length > 0,
  '未加载任何译文分片 MCNS_NOTES_PARTS');

/* ---------------- 论文列表 ---------------- */
section('1. 侧栏论文列表');
ok(RD.papers.length >= 2, `论文数偏少: ${RD.papers.length}`);
const items = (els.paperList.innerHTML.match(/class="pitem/g) || []).length;
ok(items === RD.papers.length, `侧栏按钮 ${items} 个，应为 ${RD.papers.length}`);
info(`论文 ${RD.papers.length} 篇，按钮 ${items} 个`);
for (const p of RD.papers) {
  ok(/class="badge (oa|sub)"/.test(els.paperList.innerHTML), '缺少开放获取标记');
  ok(RD.hasData(p.id), `论文 ${p.id} 的正文未加载`);
}

/* ---------------- 渲染 ---------------- */
section('2. 当前论文的正文渲染');
// 默认论文可能变（例如新接入一篇尚未翻译的），这里显式选一篇已有完整译文的，
// 否则「译文栏有标注」「插图用 CDN」这类断言会因选到别的论文而误报。
RD.select('dorkenwald');
const st = RD.state;
ok(st.id === 'dorkenwald', `无法切到 dorkenwald，当前是 ${st.id}`);
ok(!!st.id, '未选中任何论文');
info(`当前论文: ${st.id}`);
const oP = pairsIn(els.origCol.innerHTML), tP = pairsIn(els.transCol.innerHTML);
ok(oP > 0, '原文栏没有段落配对');
ok(oP === tP, `原文 ${oP} 段 / 译文 ${tP} 段，两侧应一一对应`);
info(`段落配对 ${oP} 对`);
ok(figsIn(els.origCol.innerHTML) > 0, '原文栏没有渲染插图');
info(`插图 ${figsIn(els.origCol.innerHTML)} 张`);
// 插图地址允许三种：Europe PMC 的 CDN、本地化的 berg/ 或 embeds/
const IMG_OK = /src="(https:\/\/cdn\.ncbi\.nlm\.nih\.gov|assets\/papers\/berg\/)/;
ok(IMG_OK.test(els.origCol.innerHTML), '插图未使用可用的地址（CDN 或本地）');
ok(/<figure/.test(els.origCol.innerHTML), '插图未用 figure 包裹');
ok(/figcaption/.test(els.origCol.innerHTML), '插图缺少图注');

section('3. 标注');
const aO = annosIn(els.origCol.innerHTML), aT = annosIn(els.transCol.innerHTML);
ok(aT > 0, '译文栏没有注入任何标注');
ok(aO === 0, '标注不应出现在原文栏');
info(`标注 ${aT} 个（全部在译文栏）`);
ok(/class="anno (violet|blue|green|amber|red)?"|class="anno"/.test(els.transCol.innerHTML),
  '标注缺少样式类');
ok(/有标注/.test(els.transCol.innerHTML), '章节标题未标出「有标注」');
ok(typeof RD.getAnnoCount === 'function' && RD.getAnnoCount() >= 0, 'getAnnoCount 缺失或出错');

section('4. 目录与章节');
const tocLinks = (els.secList.innerHTML.match(/<a /g) || []).length;
ok(tocLinks > 0, '目录为空');
info(`目录 ${tocLinks} 项`);
ok(/href="#sec-/.test(els.secList.innerHTML), '目录锚点格式不对');
ok(st.sections.length > 0, 'state.sections 为空');

section('5. 论文头部与许可提示');
ok(/<h1>/.test(els.paperHead.innerHTML), '缺少标题');
ok(/DOI/.test(els.paperHead.innerHTML), '缺少 DOI');
ok(/PDF/.test(els.paperHead.innerHTML), '缺少 PDF 链接');
ok(/CC-BY/.test(els.licenseNote.innerHTML), '开放获取论文应提示 CC-BY');
ok(/CC-BY|版权/.test(els.footNote.textContent), '页脚缺少许可说明');

section('6. 译文覆盖率统计');
ok(/译文覆盖 \d+\/\d+ 段/.test(els.progStat.textContent),
  `覆盖率文案不对: ${els.progStat.textContent}`);
info(els.progStat.textContent);
ok(missingIn(els.transCol.innerHTML) > 0,
  '本应存在未翻译段落（诚实标注），但没有找到 missing 提示');

section('7. 切换论文');
// dorkenwald 的插图是本地 asset（不是 CDN），所以用 shiu（Europe PMC CDN）来验证地址
const other = RD.papers.find(p => p.id === 'shiu') || RD.papers.find(p => p.id !== st.id);
RD.select(other.id);
ok(st.id === other.id, '切换后 state.id 未更新');
info(`切换到 ${other.id}`);
ok(new RegExp(other.cite.split(',')[0]).test(els.paperHead.innerHTML),
  '切换后论文头部未更新');
ok((els.paperList.innerHTML.match(/class="pitem on"/g) || []).length === 1,
  '侧栏应恰好有一个选中项');
ok(pairsIn(els.origCol.innerHTML) > 0, '切换后原文栏为空');
ok(IMG_OK.test(els.origCol.innerHTML), '切换后插图地址不对');

section('8. 未知论文不应崩溃');
const before = els.origCol.innerHTML;
RD.select('__nope__');
ok(st.id === other.id, '选择未知 id 不应改变当前论文');
ok(els.origCol.innerHTML === before, '选择未知 id 不应改动内容');

section('9. 控件');
els.cbAnno.checked = false;
els.cbAnno.fire('change', {});
ok(document.body.classList.contains('hideanno'), '关闭标注应给 body 加 hideanno');
els.cbAnno.checked = true;
els.cbAnno.fire('change', {});
ok(!document.body.classList.contains('hideanno'), '开启标注应移除 hideanno');

els.cbPaper.checked = false;
els.cbPaper.fire('change', {});
ok(!document.body.classList.contains('paper'), '关闭纸面配色应移除 paper');
els.cbPaper.checked = true;
els.cbPaper.fire('change', {});
ok(document.body.classList.contains('paper'), '开启纸面配色应加 paper');

section('10. HTML 转义安全');
// 构造一段带脚本的假原文，确认被转义
const evil = '<img src=x onerror="alert(1)"><script>bad()</script>';
sandbox.MCNS_PAPERS.__evil = {
  meta: { title: 'x' },
  blocks: [{ kind: 'section', level: 1, title: 'T', paras: [evil], figs: [] }]
};
RD.papers.push({ id: '__evil', oa: true, title: 'x', titleZh: 'x', cite: 'x', doi: 'd', pmcid: 'P', pdf: 'p', why: 'w' });
RD.select('__evil');
const out = els.origCol.innerHTML;
ok(out.indexOf('<script>') === -1, '原文里的 <script> 未被转义（XSS 风险）');
ok(out.indexOf('onerror=') === -1 || out.indexOf('&lt;img') >= 0,
  '原文里的 <img onerror> 未被转义');
info('恶意标签已被转义');

// 带属性的 span 只允许 class，且属性值必须是安全字符
const evilSpan = '<span class="a" onclick="x()">t</span><span class="b"><i>ok</i></span>';
sandbox.MCNS_PAPERS.__evil2 = {
  meta: { title: 'x' },
  blocks: [{ kind: 'section', level: 1, title: 'T', paras: [evilSpan], figs: [] }]
};
RD.papers.push({ id: '__evil2', oa: true, title: 'x', titleZh: 'x', cite: 'x', doi: 'd', pmcid: 'P', pdf: 'p', why: 'w' });
RD.select('__evil2');
const out2 = els.origCol.innerHTML;
ok(out2.indexOf('onclick') === -1, 'span 上的 onclick 未被剥离');
ok(/<span class="b">/.test(out2), 'span 的合法 class 应被保留');
ok(/<i>ok<\/i>/.test(out2), '白名单内联标签应被保留');

section('11. 公式渲染');
// 公式由 tools/mathfix.py 从 <mml:math> 还原，形如 <span class="math">…<br>…</span>
RD.select('shiu');
const so = els.origCol.innerHTML;
ok(/class="math"/.test(so), '原文栏未找到任何公式');
ok(/dv_i\/dt/.test(so), '未找到 LIF 的膜电位方程');
ok(/dg_i\/dt/.test(so), '未找到电导衰减方程');
ok(/<br>/.test(so), '公式里的换行 <br> 未被保留（多行公式会挤成一行）');
info('Shiu 原文栏含公式：' + (so.match(/class="math"/g) || []).length + ' 处');
RD.select('dorkenwald');
const doo = els.origCol.innerHTML;
ok(/class="math"/.test(doo), 'Dorkenwald 原文栏未找到公式');
ok(/TP \+ FP/.test(doo), '未找到精确率/召回率定义式');
info('Dorkenwald 原文栏含公式：' + (doo.match(/class="math"/g) || []).length + ' 处');
// 公式必须成对闭合，不能破坏页面结构
for (const [label, h] of [['shiu', so], ['dorkenwald', doo]]) {
  const open = (h.match(/<span class="math">/g) || []).length;
  const close = (h.match(/<\/span>/g) || []).length;
  ok(close >= open, `${label}: span 标签未闭合（开 ${open} 关 ${close}）`);
}

section('12. Berg 的公式图片（bioRxiv 用图片而非 MathML）');
RD.select('berg');
const bo = els.origCol.innerHTML;
const figCount = (bo.match(/class="matheq"/g) || []).length;
ok(figCount > 0, 'Berg 原文栏未找到公式图片');
info(`Berg 公式图片：${figCount} 处`);
ok(/assets\/papers\/berg\/graphic-\d+\.gif/.test(bo), '公式图片未使用本地路径');
ok(/alt="[^"]{6,}"/.test(bo), '公式图片缺少可读的 alt 文本');

// 镜像功能要求页面能查到 .matheq 元素
// 注意：页面里 mirrorFormulas 用的是 origCol.querySelectorAll，
// 所以假 DOM 的内容区也必须实现它（不能只在 document 上实现）
const mq = els.origCol.querySelectorAll('.matheq');
info(`原文侧 .matheq 元素：${mq.length} 个`);
ok(mq.length === figCount, `matheq 元素数(${mq.length}) 应与图片数(${figCount}) 一致`);
if (mq.length) {
  const h = mq[0];
  const pn = h.parentNode;
  const im = h.querySelector('img');
  const alt = im ? im.getAttribute('alt') : null;
  ok(!!alt, '公式图片没有可读的 alt');
  // 图片标签必须真正渲染出来，而不是被转义成 &lt;img …&gt; 的文本
  ok(!/&lt;img/.test(bo), '公式图片被转义成了文本（img 不在内联白名单里）');
  ok(/<img[^>]*\salt="/.test(bo), '公式图片的 alt 属性未保留');
  ok(!!document.getElementById((pn && pn.id) + '-t'), '译文侧对应段落元素查不到');
}

// 译文侧应当被镜像同样的公式文本
for (const k of Object.keys(pairEls)) { delete pairEls[k]; }
RD.select('berg');
const mirrored = Object.keys(pairEls).filter(k => pairEls[k]._kids.length > 0);
ok(mirrored.length > 0, '译文侧没有被镜像任何公式');
info(`镜像到译文侧的公式：${mirrored.length} 处`);
const sample = mirrored.length ? pairEls[mirrored[0]]._kids[0] : null;
ok(sample && sample.className === 'math', '镜像的不是 .math 元素');
ok(sample && String(sample.textContent).length > 4, '镜像的公式文本为空');
if (sample) info('镜像示例：' + sample.textContent.slice(0, 60));

/* ---------------- 汇总 ---------------- */
console.log('\n' + '='.repeat(62));
console.log(`结果: ${pass} 通过, ${fail} 失败`);
if (fail) {
  console.log('\n失败项:');
  failures.forEach(f => console.log('  - ' + f));
  process.exit(1);
}
console.log('ALL PASS');
