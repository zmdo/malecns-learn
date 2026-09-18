/* =====================================================================
   trans-status.js — 真实执行 notes-*.js 与论文数据，统计译文进度。

   比 tools/trans_status.py 的正则解析可靠：这里直接跑 JS，拿到合并后的
   NOTES，再与原文逐段比对。

   用法：node tools/trans-status.js [--todo]
   ===================================================================== */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, '..');
const PDIR = path.join(ROOT, 'assets', 'papers');

/* 投稿元数据：对学习无价值，不计入进度 */
const SKIP = new Set([
  '', 'Online content', 'Supplementary information', 'Author contributions',
  'Peer review', 'Data availability', 'Code availability', 'Competing interests',
  'Contributor Information', 'Extended data', 'Associated Data',
  'Peer review information', 'Supplementary Materials',
  'Data Availability Statement', 'Reporting summary', 'Reporting Summary'
]);

const sandbox = { window: null, console };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
const ctx = vm.createContext(sandbox);

for (const fn of fs.readdirSync(PDIR).filter(f => f.endsWith('.js'))) {
  vm.runInContext(fs.readFileSync(path.join(PDIR, fn), 'utf8'), ctx, { filename: fn });
}
const PAPERS = sandbox.MCNS_PAPERS || {};
const PARTS = sandbox.MCNS_NOTES_PARTS || [];

/* 复刻页面的合并逻辑 */
const NOTES = {};
function merge(pid, add) {
  if (!add) return;
  const cur = NOTES[pid] || (NOTES[pid] = {});
  for (const k of ['sections', 'paras', 'figs', 'trans']) {
    const src = add[k];
    if (!src) continue;
    cur[k] = cur[k] || {};
    for (const key of Object.keys(src)) {
      if (k === 'trans' && cur[k][key] && cur[k][key].length) {
        const dst = cur[k][key];
        src[key].forEach((v, i) => { if (v && !dst[i]) dst[i] = v; });
      } else if (cur[k][key] === undefined) {
        cur[k][key] = src[key];
      }
    }
  }
}
for (const e of PARTS) for (const pid of Object.keys(e)) merge(pid, e[pid]);

/* 展平成与页面相同的渲染顺序 */
function units(data) {
  const out = [];
  for (const b of data.blocks) {
    if (b.paras && b.paras.length) out.push([b.title, b.paras]);
    for (const s of (b.subs || [])) if (s.paras && s.paras.length) out.push([s.title, s.paras]);
  }
  return out;
}

const showTodo = process.argv.includes('--todo');
let gDone = 0, gTodo = 0;

for (const pid of Object.keys(PAPERS)) {
  const data = PAPERS[pid];
  const note = NOTES[pid] || {};
  const trans = note.trans || {};
  console.log('='.repeat(78));
  console.log(`${pid}  |  ${String(data.meta.title).replace(/<[^>]+>/g, '').slice(0, 62)}`);
  console.log('='.repeat(78));
  let d = 0, t = 0;
  for (const [title, paras] of units(data)) {
    if (SKIP.has(title)) continue;
    const arr = trans[title] || [];
    const filled = paras.reduce((a, _, i) => a + (arr[i] && String(arr[i]).trim() ? 1 : 0), 0);
    d += filled; t += paras.length - filled;
    const mark = filled === paras.length ? 'OK ' : (filled ? '部分' : '待译');
    console.log(`  [${mark}] ${title.slice(0, 50).padEnd(52)} ${String(filled).padStart(3)}/${String(paras.length).padEnd(3)}`);
    if (showTodo && filled < paras.length) {
      for (let i = 0; i < paras.length; i++) {
        if (!(arr[i] && String(arr[i]).trim())) {
          console.log(`         - p${i} (${paras[i].length} chars)`);
        }
      }
    }
  }
  const pct = t + d ? (d / (d + t) * 100).toFixed(1) : '100.0';
  console.log('  ' + '-'.repeat(62));
  console.log(`  已译 ${d} / 待译 ${t}   （本章 ${pct}%）`);
  console.log();
  gDone += d; gTodo += t;
}
console.log('='.repeat(78));
console.log(`总计：已译 ${gDone} 段 / 待译 ${gTodo} 段  （${(gDone / Math.max(1, gDone + gTodo) * 100).toFixed(1)}%）`);
console.log(`标注：章级 ${Object.keys(NOTES.dorkenwald?.sections || {}).length + Object.keys(NOTES.shiu?.sections || {}).length} 个节` +
            ` · 段级 ${Object.keys(NOTES.dorkenwald?.paras || {}).length + Object.keys(NOTES.shiu?.paras || {}).length} 处` +
            ` · 图注 ${Object.keys(NOTES.dorkenwald?.figs || {}).length + Object.keys(NOTES.shiu?.figs || {}).length} 条`);
