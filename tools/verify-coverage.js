/* =====================================================================
   verify-coverage.js — 用页面真实的合并逻辑，逐段核对译文覆盖率。

   与 tools/trans-status.js 不同：这里不解析源码，而是按 phase2.html 里
   mergeNotes 的规则在 JS 里直接算，结果就是浏览器里看到的样子。

   用法：node tools/verify-coverage.js
   ===================================================================== */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..'), PDIR = path.join(ROOT, 'assets', 'papers');

const sb = { window: null, console };
sb.window = sb; sb.globalThis = sb;
const ctx = vm.createContext(sb);
for (const fn of fs.readdirSync(PDIR).filter(f => f.endsWith('.js'))) {
  vm.runInContext(fs.readFileSync(path.join(PDIR, fn), 'utf8'), ctx, { filename: fn });
}
const PAPERS = sb.MCNS_PAPERS || {}, PARTS = sb.MCNS_NOTES_PARTS || [];

/* —— 与 phase2.html 中 mergeNotes 完全一致的实现 —— */
const NOTES = {};
const isFilled = v => v !== undefined && v !== null && String(v).trim() !== '';
for (const e of PARTS) {
  for (const pid of Object.keys(e)) {
    const add = e[pid];
    if (!add) continue;
    const cur = NOTES[pid] || (NOTES[pid] = {});
    for (const k of ['sections', 'paras', 'figs', 'trans']) {
      const src = add[k];
      if (!src) continue;
      cur[k] = cur[k] || {};
      for (const key of Object.keys(src)) {
        if (k === 'trans') {
          const dst = cur[k][key], inc = src[key] || [];
          if (!dst) { cur[k][key] = inc.slice(); continue; }
          inc.forEach((v, i) => { if (isFilled(v) && !isFilled(dst[i])) dst[i] = v; });
        } else if (cur[k][key] === undefined) {
          cur[k][key] = src[key];
        }
      }
    }
  }
}

const SKIP = new Set(['', 'Online content', 'Supplementary information', 'Author contributions',
  'Peer review', 'Data availability', 'Code availability', 'Competing interests',
  'Contributor Information', 'Extended data', 'Associated Data', 'Peer review information',
  'Supplementary Materials', 'Data Availability Statement', 'Reporting summary', 'Reporting Summary']);

let allDone = 0, allTodo = 0, gaps = 0;
for (const pid of Object.keys(PAPERS)) {
  const note = NOTES[pid] || {}, trans = note.trans || {};
  const units = [];
  for (const b of PAPERS[pid].blocks) {
    if (b.paras && b.paras.length) units.push([b.title, b.paras]);
    for (const s of (b.subs || [])) if (s.paras && s.paras.length) units.push([s.title, s.paras]);
  }
  let d = 0, t = 0;
  console.log('='.repeat(74));
  console.log(`${pid}  |  ${String(PAPERS[pid].meta.title).replace(/<[^>]+>/g, '').slice(0, 58)}`);
  console.log('='.repeat(74));
  for (const [title, paras] of units) {
    if (SKIP.has(title)) continue;
    const arr = trans[title] || [];
    let f = 0;
    const miss = [];
    for (let i = 0; i < paras.length; i++) {
      // 与页面一致：原文是空段/仅标点的排版残留，不要求翻译
      const trivial = String(paras[i]).replace(/<[^>]+>/g, '').trim().length <= 3;
      if (isFilled(arr[i]) || trivial) { f++; }
      else { miss.push(`p${i}`); gaps++; }
    }
    d += f; t += paras.length - f;
    const mark = f === paras.length ? 'OK  ' : (f ? '部分' : '待译');
    console.log(`  [${mark}] ${title.replace(/<[^>]+>/g, '').slice(0, 48).padEnd(50)} ${String(f).padStart(3)}/${String(paras.length).padEnd(3)}` +
      (miss.length && miss.length <= 6 ? '  缺 ' + miss.join(',') : ''));
  }
  console.log('  ' + '-'.repeat(60));
  console.log(`  已译 ${d} / 待译 ${t}  （${(d / (d + t) * 100).toFixed(1)}%）`);
  allDone += d; allTodo += t;
}
console.log('='.repeat(74));
const pct = (allDone / (allDone + allTodo) * 100).toFixed(1);
console.log(`总计：已译 ${allDone} 段 / 待译 ${allTodo} 段  （${pct}%）`);
// 标注统计要对**所有**已接入的论文求和 —— 之前这里写死了 dorkenwald + shiu，
// 后来接入 Berg 之后统计就少算了一篇（页面显示的图注数会偏低）。
const secN = Object.values(NOTES).reduce((n, p) => n + Object.keys(p.sections || {}).length, 0);
const parN = Object.values(NOTES).reduce((n, p) => n + Object.keys(p.paras || {}).length, 0);
const figN = Object.values(NOTES).reduce((n, p) => n + Object.keys(p.figs || {}).length, 0);
console.log(`标注：章级 ${secN} 节 · 段级 ${parN} 处 · 图注 ${figN} 条`);
process.exitCode = gaps ? 1 : 0;
