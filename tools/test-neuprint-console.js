/* =====================================================================
   test-neuprint-console.js — 用「假 DOM + 假 fetch」执行 neuprint.html 里的
   内联脚本，验证查询执行台的完整链路。

   本环境浏览器不可用，这个测试台是唯一能证明
   「点执行 → 发出正确请求 → 渲染结果表 → 导出 CSV → 错误处理」
   这条链路可用、且每步的 DOM 副作用都正确的手段。

   写法：顶层 async 顺序执行 + settle() 让页面内部 promise 链结算完。
   用法: node tools/test-neuprint-console.js
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const PAGE = path.join(ROOT, 'neuprint.html');

let pass = 0, fail = 0;
const failures = [];
function ok(cond, msg) {
  if (cond) { pass++; }
  else { fail++; failures.push(msg); console.log('  FAIL  ' + msg); }
}
function section(t) { console.log('\n' + t); console.log('-'.repeat(t.length)); }
function info(t) { console.log('  ' + t); }
/** 去掉标签，便于在日志里看清表格内容 */
function strip(s) { return String(s).replace(/<[^>]+>/g, '|'); }

/* ================================================================
   假 DOM
   ================================================================ */
function makeClassList() {
  const s = new Set();
  return {
    add: c => s.add(c),
    remove: c => s.delete(c),
    contains: c => s.has(c),
    toggle: (c, on) => {
      if (on === undefined) { s.has(c) ? s.delete(c) : s.add(c); }
      else if (on) s.add(c); else s.delete(c);
    },
    _set: s
  };
}
function makeEl(tag, id) {
  const el = {
    tagName: (tag || 'div').toUpperCase(), id: id || '',
    dataset: {}, style: {}, value: '', textContent: '', innerHTML: '',
    disabled: false, children: [], _ev: {}, download: '', href: '',
    classList: makeClassList(),
    addEventListener(t, fn) { (this._ev[t] = this._ev[t] || []).push(fn); },
    removeEventListener() {},
    querySelectorAll() { return []; },
    querySelector() { return null; },
    appendChild(c) { this.children.push(c); return c; },
    removeChild(c) { return c; },
    click() {},
    focus() {}, select() {},
    closest() { return null; },
    getBoundingClientRect() { return { left: 0, top: 0, width: 1200, height: 800 }; },
    fire(type, ev) {
      (this._ev[type] || []).forEach(fn => fn(Object.assign({
        preventDefault() {}, stopPropagation() {}, target: this,
        ctrlKey: false, metaKey: false, key: ''
      }, ev || {})));
    }
  };
  // 页面里有用 element.className = '...' 设类的写法，
  // 必须与 classList 保持同步，否则 classList.contains 会读到过期状态。
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
  return el;
}

const IDS = ['cypher', 'runBtn', 'csvBtn', 'copyBtn', 'clearBtn', 'theadRow', 'tbody',
  'resTable', 'emptyMsg', 'errBox', 'connDot', 'connText', 'rowCount', 'elapsed',
  'colCount', 'limitSel', 'presetList', 'rawBox', 'rawJson', 'metaBox', 'dsMeta',
  'hintLbl', 'corsNote'];
const els = {};
IDS.forEach(id => { els[id] = makeEl(/Btn$/.test(id) ? 'button' : 'div', id); });
els.limitSel.value = '200';

const presetButtons = [];
els.presetList.querySelectorAll = function (sel) {
  return sel === '.preset' ? presetButtons : [];
};

function makeTh(i) {
  const th = makeEl('th');
  th.dataset.col = String(i);
  th.closest = (sel) => (sel === 'th' ? th : null);
  return th;
}

const document = {
  getElementById: id => els[id] || null,
  querySelector: sel => (sel === '#cypher' ? els.cypher : null),
  querySelectorAll: () => [],
  createElement: t => makeEl(t),
  body: makeEl('body'),
  addEventListener() {}
};

/* ================================================================
   假 fetch
   ================================================================ */
let fetchCalls = [];
let nextResponse = null;

function makeResponse(status, bodyText) {
  return { ok: status >= 200 && status < 300, status, text: () => Promise.resolve(bodyText) };
}

/* ================================================================
   装载
   ================================================================ */
section('0. 抽取并装载内联脚本');
const html = fs.readFileSync(PAGE, 'utf8');
const inline = [];
{
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    if (!/src\s*=/.test(m[1]) && m[2].trim()) inline.push(m[2]);
  }
}
ok(inline.length === 1, `内联脚本应为 1 个，实际 ${inline.length}`);
info(`inline script ${inline[0].length} chars`);
ok(!/<script[^>]*\bsrc=/.test(html), '执行台不应依赖外部脚本（要能单文件双击打开）');

const sandbox = {
  console, Math, JSON, Array, Object, String, Number, Boolean, Error, Set, Map, Date,
  isNaN, parseFloat, parseInt, Promise, setTimeout, clearTimeout,
  Blob: function (parts) { this.parts = parts; },
  URL: { createObjectURL: () => 'blob:fake', revokeObjectURL() {} },
  performance: { now: () => Date.now() },
  navigator: {},
  fetch: function (url, opts) {
    fetchCalls.push({ url, opts });
    return Promise.resolve(nextResponse || makeResponse(200, '{"columns":[],"data":[]}'));
  },
  document
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.window.addEventListener = function () {};

const ctx = vm.createContext(sandbox);
let bootErr = null;
try {
  vm.runInContext(inline[0], ctx, { filename: 'neuprint-inline.js' });
} catch (e) { bootErr = e; }
ok(!bootErr, '初始化抛异常: ' + (bootErr && bootErr.message));
if (bootErr) { console.log(bootErr && bootErr.stack); process.exit(1); }
info('初始化未抛异常');

const NPQ = sandbox.__npq;
ok(!!NPQ, '未暴露 __npq 测试钩子');
ok(NPQ.endpoint === 'https://neuprint.janelia.org/api/custom/custom',
  `端点不对: ${NPQ.endpoint}`);
ok(NPQ.dataset === 'male-cns:v1.0', `dataset 不对: ${NPQ.dataset}`);

/* 让页面内部排队的 promise 链结算完 */
const settle = (ms) => new Promise(r => setTimeout(r, ms === undefined ? 30 : ms));

/* ================================================================
   测试主体
   ================================================================ */
const GOOD = {
  columns: ['n.bodyId', 'n.instance', 'n.superclass', 'n.consensusNt'],
  data: [
    [11074, 'DNg13_L', 'descending_neuron', 'acetylcholine'],
    [512006, 'DNg13_R', 'descending_neuron', 'acetylcholine']
  ],
  debug: 'MATCH (n:`male-cns_Neuron`) WHERE n.type = "DNg13" RETURN ...'
};

(async function main() {
  section('1. 初始化副作用');
  ok(els.cypher.value.length > 20, '编辑器未预填首条查询');
  ok(NPQ.presetCount >= 20, `预设查询偏少: ${NPQ.presetCount}`);
  const pbtns = (els.presetList.innerHTML.match(/class="preset"/g) || []).length;
  ok(pbtns === NPQ.presetCount, `预设按钮数 ${pbtns} 与数据 ${NPQ.presetCount} 不一致`);
  info(`预设 ${NPQ.presetCount} 条，渲染 ${pbtns} 个按钮`);
  ok(/dataset male-cns:v1\.0/.test(els.dsMeta.textContent), 'dsMeta 未设置');
  ok(els.tbody.innerHTML === '', '结果表初始应为空');
  ok(els.theadRow.innerHTML === '', '表头初始应为空');
  ok(els.csvBtn.disabled === true, '无数据时导出按钮应禁用');
  ok(/尚未请求/.test(els.connText.textContent), `初始连接文案不对: ${els.connText.textContent}`);

  section('2. 执行查询 → 请求体必须是合法的 neuPrint 调用');
  nextResponse = makeResponse(200, JSON.stringify(GOOD));
  NPQ.setQuery("MATCH (n:Neuron) WHERE n.type = 'DNg13' RETURN n.bodyId");
  fetchCalls = [];
  NPQ.run();
  await settle();

  ok(fetchCalls.length === 1, `应发出 1 次请求，实际 ${fetchCalls.length}`);
  const call = fetchCalls[0];
  ok(call.url === NPQ.endpoint, `请求 URL 不对: ${call.url}`);
  ok(call.opts && call.opts.method === 'POST', '应为 POST');
  ok(call.opts.headers && /application\/json/i.test(call.opts.headers['Content-Type']),
    'Content-Type 应为 application/json');
  let body = null;
  try { body = JSON.parse(call.opts.body); } catch (e) {}
  ok(!!body, '请求体不是合法 JSON');
  ok(body && body.dataset === 'male-cns:v1.0', `请求体 dataset 不对: ${body && body.dataset}`);
  ok(body && /DNg13/.test(body.cypher || ''), '请求体未携带查询语句');
  info(`POST ${call.url}`);
  info(`body: ${JSON.stringify(body)}`);

  section('3. 结果渲染');
  const st = NPQ.state;
  ok(st.columns.length === 4, `列数应为 4，实际 ${st.columns.length}`);
  ok(st.rows.length === 2, `行数应为 2，实际 ${st.rows.length}`);
  ok(!els.resTable.classList.contains('hid'), '结果表应显示');
  ok(els.emptyMsg.classList.contains('hid'), '空态提示应隐藏');
  const thCount = (els.theadRow.innerHTML.match(/<th/g) || []).length;
  ok(thCount === 4, `表头应有 4 列，实际 ${thCount}`);
  const trCount = (els.tbody.innerHTML.match(/<tr>/g) || []).length;
  ok(trCount === 2, `表体应有 2 行，实际 ${trCount}`);
  ok(/DNg13_L/.test(els.tbody.innerHTML), '表体未包含返回数据');
  ok(/class="num"/.test(els.tbody.innerHTML), '数字列未套用 num 样式');
  info(`表头 ${thCount} 列 / 表体 ${trCount} 行`);

  section('4. 状态条与元信息');
  ok(/2/.test(els.rowCount.textContent), `行数显示不对: ${els.rowCount.textContent}`);
  ok(/4/.test(els.colCount.textContent), `列数显示不对: ${els.colCount.textContent}`);
  ok(/ms/.test(els.elapsed.textContent), `耗时显示不对: ${els.elapsed.textContent}`);
  ok(els.connDot.classList.contains('ok'), '连接状态点应为 ok');
  ok(/已连接/.test(els.connText.textContent), `连接文案不对: ${els.connText.textContent}`);
  ok(!els.rawBox.classList.contains('hid'), '原始 JSON 面板应可用');
  ok(/male-cns_Neuron/.test(els.rawJson.textContent), '原始响应未写入');
  ok(!els.metaBox.classList.contains('hid'), '改写后的 Cypher 未显示');
  ok(/male-cns_Neuron/.test(els.metaBox.textContent), 'metaBox 内容不对');
  ok(els.csvBtn.disabled === false, '有数据时导出按钮应可用');
  info(`状态条: 行 ${els.rowCount.textContent} · 列 ${els.colCount.textContent} · ${els.elapsed.textContent}`);

  section('5. CSV 导出');
  const csv = NPQ.toCSV();
  const lines = csv.split('\n');
  ok(lines.length === 3, `CSV 应有表头+2 行，实际 ${lines.length} 行`);
  ok(lines[0].indexOf('n.bodyId') === 0, `CSV 表头不对: ${lines[0]}`);
  ok(lines[1].indexOf('11074') === 0, `CSV 首行数据不对: ${lines[1]}`);
  ok(csv.indexOf('"') === -1, '本数据无需引号，CSV 不应出现');
  info('CSV: ' + lines[0]);
  info('     ' + lines[1]);

  // 含逗号/引号的值必须被正确转义
  nextResponse = makeResponse(200, JSON.stringify({
    columns: ['label', 'note'],
    data: [['a,b', 'he said "hi"'], ['ok', null]]
  }));
  NPQ.setQuery('MATCH (n:Neuron) RETURN 1');
  NPQ.run();
  await settle();
  const csv2 = NPQ.toCSV();
  ok(csv2.indexOf('"a,b"') >= 0, 'CSV 未对含逗号的值加引号');
  ok(csv2.indexOf('"he said ""hi"""') >= 0, 'CSV 未转义内部引号');
  ok(csv2.split('\n')[2].indexOf('ok,') === 0, 'CSV 空值应留空');
  info('含特殊字符的 CSV 已正确转义');

  section('6. 表头排序');
  nextResponse = makeResponse(200, JSON.stringify(GOOD));
  NPQ.setQuery("MATCH (n:Neuron) RETURN n.bodyId");
  NPQ.run();
  await settle();
  const th0 = makeTh(0);
  info('排序前表体: ' + strip(els.tbody.innerHTML).slice(0, 70));

  // 注意：bodyId 在表里带千分位显示（11,074 / 512,006），断言要用格式化后的字符串
  els.theadRow.fire('click', { target: th0 });
  const desc = els.tbody.innerHTML;
  const dFirst = desc.indexOf('512,006'), dSecond = desc.indexOf('11,074');
  info(`降序表体: ${strip(desc).slice(0, 70)}`);
  ok(dFirst >= 0 && dSecond >= 0 && dFirst < dSecond,
    `数值列首次点击应降序（512,006 应在 11,074 之前），实际 first=${dFirst} second=${dSecond}`);

  const arrow1 = (els.theadRow.innerHTML.match(/arrow">([▲▼]?)</) || [])[1];
  ok(arrow1 === '▼', `降序时表头箭头应为 ▼，实际 "${arrow1}"`);

  els.theadRow.fire('click', { target: th0 });
  const asc = els.tbody.innerHTML;
  info(`升序表体: ${strip(asc).slice(0, 70)}`);
  ok(asc.indexOf('11,074') < asc.indexOf('512,006'), '再次点击应切换为升序');

  const arrow2 = (els.theadRow.innerHTML.match(/arrow">([▲▼]?)</) || [])[1];
  ok(arrow2 === '▲', `升序时表头箭头应为 ▲，实际 "${arrow2}"`);

  // 字符串列排序（实例名）+ null 值应排到最后
  nextResponse = makeResponse(200, JSON.stringify({
    columns: ['name'], data: [['bbb'], [null], ['aaa']]
  }));
  NPQ.setQuery('MATCH (n:Neuron) RETURN n.instance AS name');
  NPQ.run();
  await settle();
  const thS = makeTh(0);
  els.theadRow.fire('click', { target: thS });   // 降序
  const sdesc = strip(els.tbody.innerHTML);
  info('字符串列降序: ' + sdesc);
  ok(sdesc.indexOf('bbb') < sdesc.indexOf('aaa'), '字符串列降序不对');
  ok(sdesc.indexOf('null') > sdesc.indexOf('aaa'), 'null 值应排在最后');

  section('7. Ctrl+Enter 触发执行');
  nextResponse = makeResponse(200, JSON.stringify(GOOD));
  fetchCalls = [];
  els.cypher.fire('keydown', { ctrlKey: true, key: 'Enter' });
  await settle();
  ok(fetchCalls.length === 1, `Ctrl+Enter 应触发 1 次请求，实际 ${fetchCalls.length}`);

  section('8. 错误处理：HTTP 400 + Cypher 报错');
  fetchCalls = [];
  nextResponse = makeResponse(400, JSON.stringify({
    error: 'Neo4jError: Variable `cellType` not defined'
  }));
  NPQ.setQuery('MATCH (n:Neuron) RETURN n.cellType LIMIT 1');
  NPQ.run();
  await settle();
  ok(els.connDot.classList.contains('bad'), '失败后状态点应为 bad');
  ok(/请求失败/.test(els.connText.textContent), `失败文案不对: ${els.connText.textContent}`);
  ok(!els.errBox.classList.contains('hid'), '错误框应显示');
  ok(/HTTP 400/.test(els.errBox.textContent), '错误信息应含 HTTP 状态');
  ok(/cellType/.test(els.errBox.textContent), '错误信息应含服务器返回的原因');
  ok(/没有联网|字段名|LIMIT/.test(els.errBox.textContent), '应给出排查建议');
  ok(!!NPQ.state.lastError, 'state.lastError 未记录');
  ok(els.csvBtn.disabled === true, '失败后导出按钮应禁用');
  info('错误提示首行: ' + els.errBox.textContent.split('\n')[0]);

  section('9. 网络异常（fetch 直接 reject）');
  const origFetch = sandbox.fetch;
  sandbox.fetch = function () { return Promise.reject(new Error('Failed to fetch')); };
  NPQ.run();
  await settle();
  ok(!els.errBox.classList.contains('hid'), '网络异常应显示错误框');
  ok(/Failed to fetch/.test(els.errBox.textContent), '应保留原始错误信息');
  ok(els.connDot.classList.contains('bad'), '网络异常后状态点应为 bad');
  sandbox.fetch = origFetch;
  info('网络异常被正确捕获');

  section('10. 空结果与清空');
  fetchCalls = [];
  nextResponse = makeResponse(200, JSON.stringify({ columns: ['t'], data: [] }));
  await NPQ.run();
  await settle();
  ok(els.resTable.classList.contains('hid'), '空结果时结果表应隐藏');
  ok(!els.emptyMsg.classList.contains('hid'), '空结果时应显示空态提示');
  ok(/没有返回任何行/.test(els.emptyMsg.textContent), '空态文案不对');
  ok(/类型名不存在|字段名写错/.test(els.emptyMsg.textContent), '空态应提示字段名陷阱');
  ok(els.csvBtn.disabled === true, '空结果时导出按钮应禁用');
  info('空态提示: ' + els.emptyMsg.textContent.slice(0, 46) + '…');
  // 回归：曾经用 !cols.length 判断空结果，导致「1 列 0 行」被渲染成只有表头的空表
  ok(els.theadRow.innerHTML === '', '0 行时不应渲染只有表头的空表');
  ok(els.connDot.classList.contains('ok'), '0 行仍是成功查询，状态应为 ok');
  info('空态提示: ' + els.emptyMsg.textContent.slice(0, 46) + '…');

  els.clearBtn.fire('click', {});
  ok(els.tbody.innerHTML === '', '清空后表体应为空');
  ok(els.theadRow.innerHTML === '', '清空后表头应为空');
  ok(els.rowCount.textContent === '—', '清空后行数应重置');
  ok(els.resTable.classList.contains('hid'), '清空后结果表应隐藏');
  ok(els.rawBox.classList.contains('hid'), '清空后原始面板应隐藏');

  section('11. 显示行数限制');
  const many = { columns: ['i'], data: [] };
  for (let i = 0; i < 500; i++) many.data.push([i]);
  nextResponse = makeResponse(200, JSON.stringify(many));
  els.limitSel.value = '50';
  NPQ.run();
  await settle();
  const rendered = (els.tbody.innerHTML.match(/<tr>/g) || []).length;
  ok(rendered === 50, `限 50 行时应渲染 50 行，实际 ${rendered}`);
  ok(/可能被截断/.test(els.rowCount.textContent), '截断时应给出提示');
  ok(NPQ.state.rows.length === 500, '原始数据不应被截断');
  ok(NPQ.toCSV().split('\n').length === 51, 'CSV 应只导出显示中的 50 行');
  info(`500 行结果 / 限 50 → 渲染 ${rendered} 行，CSV 51 行`);

  els.limitSel.value = '200';
  els.limitSel.fire('change', {});
  const rendered2 = (els.tbody.innerHTML.match(/<tr>/g) || []).length;
  ok(rendered2 === 200, `改上限后应重渲染为 200 行，实际 ${rendered2}`);
  info('改变显示上限会立即重渲染');

  section('12. 复制的查询与编辑器一致');
  NPQ.setQuery('MATCH (n:Neuron) RETURN count(n)');
  ok(NPQ.getQuery() === 'MATCH (n:Neuron) RETURN count(n)', 'getQuery 与设置不一致');
  els.copyBtn.fire('click', {});
  await settle(10);
  ok(/已复制|复制失败|已全选/.test(els.hintLbl.textContent),
    `复制按钮无反馈: ${els.hintLbl.textContent}`);
  info('复制反馈: ' + els.hintLbl.textContent);

  /* ---------------- 汇总 ---------------- */
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
