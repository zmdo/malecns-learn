/* =====================================================================
   mcns-3d.js — MaleCNS 阶段 0 · 脑区 3D 浏览器
   ---------------------------------------------------------------------
   自研迷你 3D 引擎（Canvas 2D + 画家算法），不依赖 WebGL / three.js。
   纯函数部分（几何构造、视图变换、投影、拾取）导出到 globalThis.MCNS3D，
   以便在 Node 里做单元测试 —— 见 tools/test-3d.js

   ⚠️ 坐标系与几何都是「示意图」：轴向与相对位置依据果蝇解剖常识设定，
      数值不是测量值，不可用于定量分析。
   ===================================================================== */
(function (root) {
  'use strict';

  /* ------------------------------------------------------------------
     0. 坐标约定  (单位: μm, 仅用于示意图比例)
        +X = 右侧 (lateral)
        +Y = 前   (anterior)
        +Z = 背   (dorsal)
     ------------------------------------------------------------------ */

  var DEG = Math.PI / 180;

  /* ------------------------------------------------------------------
     1. 脑区数据
        desc  —— 点击后在信息面板显示的介绍
        tags  —— 侧边面板里的分组标签
        bg    —— 背景结构：半透明、不参与拾取
     ------------------------------------------------------------------ */
  var REGIONS = [
    /* ---- 中央脑 ---- */
    { id:'AL', name:'触角叶', en:'Antennal Lobe', abbr:'AL',
      tags:['中央脑','嗅觉'], color:'#f472b6',
      desc:'嗅觉的第一级中枢。嗅觉受体神经元（ORN）从触角进来后在这里换元，' +
           '再投射到侧角（LH）和蘑菇体（MB）。约 50 个嗅小球（glomerulus）构成它的功能单元。',
      note:'左右各一',
      parts:[ {t:'ell', c:[ 92, 46, -36], r:[36, 38, 32]},
              {t:'ell', c:[-92, 46, -36], r:[36, 38, 32]} ] },

    { id:'MB', name:'蘑菇体', en:'Mushroom Body', abbr:'MB',
      tags:['中央脑','学习记忆'], color:'#a78bfa', prio:2,
      desc:'学习与记忆的核心结构。内在神经元叫 Kenyon 细胞（KC），轴突在「萼」(CA) 接收嗅觉输入，' +
           '再沿垂直叶／水平叶输出到蘑菇体输出神经元（MBON）。多巴胺能神经元在这里提供奖惩信号，' +
           '是果蝇联想学习回路的所在地。',
      note:'垂直叶 + 水平叶 + 萼',
      parts:[ {t:'ell', c:[ 58,  6,  30], r:[34, 36, 28]},
              {t:'ell', c:[-58,  6,  30], r:[34, 36, 28]},
              {t:'ell', c:[ 50, 34,  74], r:[19, 20, 56]},
              {t:'ell', c:[-50, 34,  74], r:[19, 20, 56]},
              {t:'ell', c:[ 20, 64, -30], r:[15, 42, 14]},
              {t:'ell', c:[-20, 64, -30], r:[15, 42, 14]} ] },

    { id:'CX', name:'中央复合体', en:'Central Complex', abbr:'CX',
      tags:['中央脑','导航'], color:'#38bdf8', prio:2,
      desc:'导航、朝向与运动控制的中枢，由四个互锁的神经毡组成：' +
           '椭球体（EB）、扇形体（FB）、原脑桥（PB）、上／下神经毡（NO）。' +
           '它维持「头朝向」的内部表征，并把朝向转换成转向指令 —— 也是性别二态细胞高度富集的区域。',
      parts:[ {t:'ell', c:[0, 14, 70], r:[31, 27, 21]},
              {t:'ell', c:[0, 58, 40], r:[34, 23, 19]} ] },

    { id:'MB-CA', name:'蘑菇体萼', en:'Calyx (CA)', abbr:'CA',
      tags:['中央脑','学习记忆','蘑菇体'], color:'#c4b5fd', prio:1,
      desc:'蘑菇体的输入区：Kenyon 细胞的树突在这里接收来自触角叶的嗅觉投射。' +
           '「萼」的名字来自它的杯状外形。',
      parts:[ {t:'ell', c:[ 58,  6,  30], r:[26, 27, 21]},
              {t:'ell', c:[-58,  6,  30], r:[26, 27, 21]} ] },

    { id:'CX-EB', name:'椭球体', en:'Ellipsoid Body', abbr:'EB',
      tags:['中央脑','导航','中央复合体'], color:'#7dd3fc', prio:1,
      desc:'中央复合体的环形结构，是头朝向信号的主要输出枢纽。' +
           '环上的活动「凸包」位置对应当前朝向 —— 是连接组里最优雅的环形拓扑例子之一。',
      parts:[ {t:'ell', c:[0, 14, 70], r:[30, 26, 20]} ] },

    { id:'LH', name:'侧角', en:'Lateral Horn', abbr:'LH',
      tags:['中央脑','嗅觉'], color:'#fbbf24',
      desc:'嗅觉的高级整合区，主要处理先天性嗅觉行为（求偶、产卵、躲避）。' +
           '与蘑菇体不同，LH 的回路更接近「硬接线」，不依赖学习。',
      parts:[ {t:'ell', c:[ 96, -10, -6], r:[31, 36, 30]},
              {t:'ell', c:[-96, -10, -6], r:[31, 36, 30]} ] },

    { id:'SEZ', name:'食管下区 / 颚神经毡', en:'Subesophageal Zone / GNG', abbr:'SEZ · GNG',
      tags:['中央脑','味觉'], color:'#4ade80',
      desc:'味觉与摄食的中枢，也是大量下行神经元（DN）的胞体所在。' +
           '味觉受体神经元（GRN）在这里换元，再把信号送往运动神经元 —— ' +
           '标准验证通路「糖 GRN → SEZ → MN9」经过此处。',
      parts:[ {t:'ell', c:[0, 22, -100], r:[56, 42, 42]} ] },

    /* ---- 视叶（右侧，四层） ---- */
    { id:'LA', name:'板层', en:'Lamina', abbr:'LA',
      tags:['视叶','视觉'], color:'#fb923c',
      desc:'视叶四层的最外层，是光感受器 R1–R6 的投射终点。' +
           '它保留了眼睛的视网膜拓扑（retinotopic），每个小眼对应一个 cartridge。',
      parts:[ {t:'ell', c:[207, 42, -74], r:[17, 100, 74]} ] },

    { id:'ME', name:'髓质', en:'Medulla', abbr:'ME',
      tags:['视叶','视觉'], color:'#fdba74',
      desc:'视叶中最大的一层，处理运动、颜色与偏振光。' +
           'R7 / R8 直接投射到这里，是视觉计算的主战场。',
      parts:[ {t:'ell', c:[173, 42, -70], r:[31, 103, 77]} ] },

    { id:'LO', name:'小叶', en:'Lobula', abbr:'LO',
      tags:['视叶','视觉'], color:'#fcd34d',
      desc:'视叶第三层，处理更抽象的视觉特征（如小目标、朝向）。' +
           '许多视觉投射神经元（VPN）从这里把信息送入中央脑。',
      parts:[ {t:'ell', c:[139, 38, -54], r:[27, 89, 63]} ] },

    { id:'LOP', name:'小叶板', en:'Lobula Plate', abbr:'LOP',
      tags:['视叶','视觉'], color:'#fde68a',
      desc:'视叶第四层，是光流与自身运动检测的中心。' +
           '著名的 T4 / T5 细胞就在这里，专门编码四个方向的运动 —— 也是 FlyWire 上研究得最透的视觉回路。',
      parts:[ {t:'ell', c:[144, 20, -118], r:[23, 70, 52]} ] },

    /* ---- 腹神经索 ---- */
    { id:'VNC', name:'腹神经索', en:'Ventral Nerve Cord', abbr:'VNC',
      tags:['腹神经索'], color:'#94a3b8',
      desc:'相当于脊髓：运动回路与局部感觉处理都在这里。' +
           '这块是 FlyWire FAFB 完全没有的，也是 MaleCNS 相对雌性脑数据集的核心增量。' +
           'MaleCNS 的 VNC 分区共 23 个神经毡。',
      parts:[ {t:'ell', c:[0, -95, -215], r:[64, 96, 46]},
              {t:'ell', c:[0, -345, -209], r:[38, 44, 24]} ] },

    { id:'NEUROMERE-T', name:'胸神经节（T1–T3）', en:'Thoracic Neuromeres', abbr:'T1 · T2 · T3',
      tags:['腹神经索'], color:'#a8b3c4',
      desc:'三个胸神经节，分别对应前、中、后胸足与翅的运动控制。' +
           '每个神经节内部又分腿神经毡（LegNp）、腹侧联合区（VAC）等 —— ' +
           'VNC 的命名法见 Court et al. 2020, Neuron 107:1071。',
      parts:[ {t:'ell', c:[0, -95, -212], r:[56, 48, 40]},
              {t:'ell', c:[0,-205, -207], r:[52, 46, 38]},
              {t:'ell', c:[0,-315, -207], r:[48, 44, 36]} ] },

    { id:'AB', name:'腹部神经节', en:'Abdominal Ganglion', abbr:'AB',
      tags:['腹神经索'], color:'#64748b', prio:1,
      desc:'神经索最尾端的融合神经节，控制腹部肌肉、生殖与排泄相关回路。',
      parts:[ {t:'ell', c:[0,-345, -207], r:[34, 40, 23]} ] },

    /* ---- 背景结构（半透明、不可点击） ---- */
    { id:'CB', name:'中央脑（整体）', en:'Central Brain', abbr:'—',
      tags:['结构'], color:'#1e3a5f', bg:true, pickable:false,
      desc:'容纳蘑菇体、中央复合体、触角叶、侧角、食管下区等。' +
           '整个中央脑属于 MaleCNS 的覆盖范围之一（另外两块是视叶与腹神经索）。',
      parts:[ {t:'ell', c:[0, 20, -26], r:[182, 128, 144]} ] },

    { id:'CONNECTIVE', name:'颈连接', en:'Neck Connective', abbr:'—',
      tags:['结构'], color:'#334155', bg:true, pickable:false,
      desc:'脑与腹神经索之间的通道，下行神经元（DN）与上行神经元（AN）从这里经过。' +
           'MaleCNS 官方强调它完整（intact neck connective）—— 这是能把「脑控身体」' +
           '整条链路放进同一个数据集的前提。',
      parts:[ {t:'ell', c:[0, -30, -172], r:[36, 44, 36]} ] },

    { id:'OL', name:'视叶（整体）', en:'Optic Lobe', abbr:'—',
      tags:['结构'], color:'#3b2f1a', bg:true, pickable:false,
      desc:'由板层（LA）、髓质（ME）、小叶（LO）、小叶板（LOP）四层组成，' +
           '负责从光感受器到运动检测的全部早期视觉计算。',
      parts:[ {t:'ell', c:[178, 40, -72], r:[80, 112, 88]} ] }
  ];

  /* ------------------------------------------------------------------
     1b. 官方网格的呈现元数据（颜色 / 中文名 / 分组 / 拾取优先级）
         几何来自 assets/mcns-meshes.js（官方 ROI 网格，见 tools/fetch_official_meshes.py）
     ------------------------------------------------------------------ */
  var STYLE = {
    MB:        { color:'#a78bfa', zh:'蘑菇体',        abbr:'MB',        tags:['中央脑'], prio:2 },
    'MB-CA':   { color:'#c4b5fd', zh:'蘑菇体萼',      abbr:'CA',        tags:['中央脑'], prio:1 },
    CX:        { color:'#38bdf8', zh:'中央复合体',    abbr:'CX',        tags:['中央脑'], prio:2 },
    'CX-EB':   { color:'#7dd3fc', zh:'椭球体',        abbr:'EB',        tags:['中央脑'], prio:1 },
    AL:        { color:'#f472b6', zh:'触角叶',        abbr:'AL',        tags:['中央脑'], prio:3 },
    LH:        { color:'#fbbf24', zh:'侧角',          abbr:'LH',        tags:['中央脑'], prio:3 },
    SEZ:       { color:'#4ade80', zh:'食管下区',      abbr:'GNG',       tags:['中央脑'], prio:3 },
    AOTU:      { color:'#22d3ee', zh:'前视结节',      abbr:'AOTU',      tags:['中央脑'], prio:3 },
    LAL:       { color:'#818cf8', zh:'侧副叶',        abbr:'LAL',       tags:['中央脑'], prio:3 },
    SMP:       { color:'#94a3b8', zh:'上内侧原脑',    abbr:'SMP',       tags:['中央脑'], prio:3 },
    SLP:       { color:'#a3b3c9', zh:'上外侧原脑',    abbr:'SLP',       tags:['中央脑'], prio:3 },
    SIP:       { color:'#b0bfd4', zh:'上后侧原脑',    abbr:'SIP',       tags:['中央脑'], prio:3 },
    CRE:       { color:'#cbd5e1', zh:'侧后脑',        abbr:'CRE',       tags:['中央脑'], prio:3 },
    WED:       { color:'#d6dee9', zh:'楔形区',        abbr:'WED',       tags:['中央脑'], prio:3 },
    VES:       { color:'#94a3b8', zh:'前侧沟区',      abbr:'VES',       tags:['中央脑'], prio:3 },
    IB:        { color:'#7c8ba1', zh:'下脑桥',        abbr:'IB',        tags:['中央脑'], prio:3 },
    BU:        { color:'#f9a8d4', zh:'球状体',        abbr:'BU',        tags:['中央脑'], prio:3 },
    LA:        { color:'#fb923c', zh:'板层',          abbr:'LA',        tags:['视叶'],   prio:3 },
    ME:        { color:'#fdba74', zh:'髓质',          abbr:'ME',        tags:['视叶'],   prio:3 },
    LO:        { color:'#fcd34d', zh:'小叶',          abbr:'LO',        tags:['视叶'],   prio:3 },
    LOP:       { color:'#fde68a', zh:'小叶板',        abbr:'LOP',       tags:['视叶'],   prio:3 },
    'VNC-T1':  { color:'#f87171', zh:'前胸神经节 T1', abbr:'T1',        tags:['腹神经索'], prio:3 },
    'VNC-T2':  { color:'#fb7185', zh:'中胸神经节 T2', abbr:'T2',        tags:['腹神经索'], prio:3 },
    'VNC-T3':  { color:'#fda4af', zh:'后胸神经节 T3', abbr:'T3',        tags:['腹神经索'], prio:3 },
    'VNC-AB':  { color:'#64748b', zh:'腹部神经节区',  abbr:'AB',        tags:['腹神经索'], prio:3 },
    'VNC-INT': { color:'#475569', zh:'节间连合区',    abbr:'INT',       tags:['腹神经索'], prio:3 }
  };

  function b64ToF32(b64) {
    var bin = (typeof atob === 'function') ? atob(b64) : Buffer.from(b64, 'base64').toString('binary');
    var n = bin.length, bytes = new Uint8Array(n);
    for (var i = 0; i < n; i++) bytes[i] = bin.charCodeAt(i);
    return new Float32Array(bytes.buffer, bytes.byteOffset, n >> 2);
  }
  function b64ToU32(b64) {
    var bin = (typeof atob === 'function') ? atob(b64) : Buffer.from(b64, 'base64').toString('binary');
    var n = bin.length, bytes = new Uint8Array(n);
    for (var i = 0; i < n; i++) bytes[i] = bin.charCodeAt(i);
    return new Uint32Array(bytes.buffer, bytes.byteOffset, n >> 2);
  }

  /** 把 window.MCNS_MESHES（官方网格包）转成内部几何结构 */
  function loadOfficialGeometry(bundle) {
    if (!bundle || typeof bundle !== 'object') return null;
    var meshes = [];
    var order = ['MB', 'MB-CA', 'CX', 'CX-EB', 'AL', 'LH', 'SEZ', 'AOTU', 'LAL',
                 'SMP', 'SLP', 'SIP', 'CRE', 'WED', 'VES', 'IB', 'BU',
                 'LA', 'ME', 'LO', 'LOP',
                 'VNC-T1', 'VNC-T2', 'VNC-T3', 'VNC-AB', 'VNC-INT'];
    var keys = order.filter(function (k) { return bundle[k]; });
    Object.keys(bundle).forEach(function (k) {
      if (k !== 'meta' && keys.indexOf(k) < 0) keys.push(k);
    });

    for (var ki = 0; ki < keys.length; ki++) {
      var key = keys[ki], raw = bundle[key];
      if (!raw || !raw.v || !raw.i) continue;
      var st = STYLE[key] || { color: '#8899aa', zh: key, abbr: key, tags: ['其他'], prio: 3 };
      var verts = b64ToF32(raw.v);
      var norms = raw.n ? b64ToF32(raw.n) : null;
      var idx = b64ToU32(raw.i);
      if (norms && norms.length !== verts.length) norms = null;

      var nv = verts.length / 3, nt = idx.length / 3;
      // 包围盒与中心
      var min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
      for (var i = 0; i < nv; i++) {
        for (var d = 0; d < 3; d++) {
          var val = verts[i * 3 + d];
          if (val < min[d]) min[d] = val;
          if (val > max[d]) max[d] = val;
        }
      }
      var region = {
        id: key, name: st.zh, en: raw.en || '', abbr: st.abbr,
        tags: st.tags, color: st.color, prio: st.prio,
        rawTris: raw.rawTris || nt, cellNm: raw.cellNm || 0,
        src: raw.src || []
      };
      meshes.push({
        region: region,
        verts: verts,
        norms: norms,
        faces: idx,
        tris: nt,
        center: [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2],
        bound: Math.max(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2,
        bbox: [min[0], min[1], min[2], max[0], max[1], max[2]]
      });
    }
    return meshes.length ? meshes : null;
  }
  function buildEllipsoid(part, segU, segV) {
    segU = segU || 16; segV = segV || 10;
    var c = part.c, r = part.r;
    var verts = [], norms = [], faces = [];
    var i, j, u, v, su, cv;

    for (j = 0; j <= segV; j++) {
      v = Math.PI * j / segV - Math.PI / 2;   // -90° → +90°（纬度）
      cv = Math.cos(v); su = Math.sin(v);
      for (i = 0; i <= segU; i++) {
        u = 2 * Math.PI * i / segU;           // 经度
        var dx = cv * Math.cos(u), dy = cv * Math.sin(u), dz = su;
        // 极点处 cos(v) ≈ 6e-17 而非 0，归一化得到精确单位法线
        var L = Math.hypot(dx, dy, dz) || 1;
        norms.push([dx / L, dy / L, dz / L]);
        verts.push([c[0] + r[0] * dx, c[1] + r[1] * dy, c[2] + r[2] * dz]);
      }
    }
    var row = segU + 1;
    for (j = 0; j < segV; j++) {
      for (i = 0; i < segU; i++) {
        var a = j * row + i, b = a + 1, d = a + row, e = d + 1;
        faces.push([a, d, b]);
        faces.push([b, d, e]);
      }
    }
    return { verts: verts, norms: norms, faces: faces,
             radius: Math.max(r[0], r[1], r[2]),
             c: c, r: r };            // 保留椭球参数，便于测试与体判定
  }

  /** 把区域定义编译成可渲染网格 */
  function buildMeshes(regions, segU, segV) {
    var out = [];
    for (var k = 0; k < regions.length; k++) {
      var reg = regions[k];
      var parts = [];
      var min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
      for (var p = 0; p < reg.parts.length; p++) {
        var m = buildEllipsoid(reg.parts[p], segU, segV);
        parts.push(m);
        for (var vi = 0; vi < m.verts.length; vi++) {
          var v = m.verts[vi];
          for (var d = 0; d < 3; d++) {
            if (v[d] < min[d]) min[d] = v[d];
            if (v[d] > max[d]) max[d] = v[d];
          }
        }
      }
      out.push({
        region: reg,
        parts: parts,
        center: [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2],
        bound: Math.max(max[0] - min[0], max[1] - min[1], max[2] - min[2]) / 2
      });
    }
    return out;
  }

  /* ------------------------------------------------------------------
     3. 相机：yaw / pitch 旋转 + 透视投影
        视图空间: 相机在原点，看向 -Z
     ------------------------------------------------------------------ */
  function makeCamera(opts) {
    opts = opts || {};
    return {
      yaw: opts.yaw === undefined ? -34 * DEG : opts.yaw,
      pitch: opts.pitch === undefined ? 16 * DEG : opts.pitch,
      dist: opts.dist || 1500,
      // focal 是「焦距像素数」：焦平面 (z=0) 处 1 世界单位 = focal/dist 像素
      // 1500 让整只 CNS（约 530 μm 高）在 900×780 画布上约占 90% 高
      focal: opts.focal || 1500,
      target: opts.target || [0, -70, -30],
      zoom: opts.zoom || 1
    };
  }

  /** 世界坐标 → 视图坐标
   *  约定：相机看向 +Z，位于 z = -dist。
   *  因此「离观察者的距离」w = z_rot + dist（>0），越近 w 越小。 */
  function worldToView(cam, p) {
    var x = p[0] - cam.target[0], y = p[1] - cam.target[1], z = p[2] - cam.target[2];
    var cy = Math.cos(cam.yaw), sy = Math.sin(cam.yaw);
    var x1 = x * cy + y * sy, y1 = -x * sy + y * cy, z1 = z;
    var cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
    var y2 = y1 * cp - z1 * sp, z2 = y1 * sp + z1 * cp;
    return [x1, y2, z2];
  }

  /**
   * 视图坐标 → 屏幕坐标
   *   w = z + dist  是到观察者的距离（>0）
   *   s = focal / w  → 越近越大；焦平面 (z=0) 处 s = focal/dist
   */
  function viewToScreen(cam, v, w, h) {
    var z = v[2];
    var depth = z + cam.dist;                 // > 0
    var s = (cam.focal * (cam.zoom || 1)) / depth;
    return [w / 2 + v[0] * s, h / 2 - v[1] * s, depth];
  }

  /** 组合：世界 → 屏幕 */
  function project(cam, p, w, h) {
    return viewToScreen(cam, worldToView(cam, p), w, h);
  }

  /* ------------------------------------------------------------------
     4. 渲染：画家算法（按面深度从远到近排序后绘制）
     ------------------------------------------------------------------ */
  var LIGHT = (function () {
    var v = [0.42, -0.62, 0.66], n = Math.hypot(v[0], v[1], v[2]);
    return [v[0] / n, v[1] / n, v[2] / n];
  })();

  function hexToRgb(hex) {
    var h = hex.replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  /** 生成一帧的绘制指令（纯数据，便于测试） */
  /**
   * 生成一帧的绘制指令（纯数据，便于测试）。
   * 支持两种几何来源：
   *   - 官方网格：mesh.verts / mesh.norms 为扁平 Float32Array，mesh.faces 为扁平索引
   *   - 示意图椭球：mesh.parts[] 里各带 verts/norms/faces
   */
  function buildFrame(cam, meshes, w, h, selectedId) {
    var polys = [];
    var cy = Math.cos(cam.yaw), sy = Math.sin(cam.yaw);
    var cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
    var tx = cam.target[0], ty = cam.target[1], tz = cam.target[2];
    var fz = cam.focal * (cam.zoom || 1);
    var dist = cam.dist, halfW = w / 2, halfH = h / 2;
    var fogLo = dist * 0.55, fogSpan = dist * 1.4;

    // 视图空间顶点用可增长的扁平原语数组暂存，避免每个三角形都新建对象
    var cap = 4096;
    var vsx = new Float64Array(cap), vsy = new Float64Array(cap), vsz = new Float64Array(cap);

    for (var mi = 0; mi < meshes.length; mi++) {
      var mesh = meshes[mi], reg = mesh.region;
      var isSel = selectedId && reg.id === selectedId;
      var alpha = (reg.bg ? 0.075 : (isSel ? 1.0 : 0.93));
      var color = reg.color;
      var pickable = reg.pickable !== false;
      var prio = reg.prio || 3;
      var groups = mesh.parts || [mesh];

      for (var pi = 0; pi < groups.length; pi++) {
        var part = groups[pi];
        var V = part.verts, F = part.faces, N = part.norms;
        var isFlat = typeof V[0] === 'number';
        var nv = isFlat ? (V.length / 3) : V.length;
        if (nv > cap) {
          cap = nv * 2;
          vsx = new Float64Array(cap); vsy = new Float64Array(cap); vsz = new Float64Array(cap);
        }

        // 顶点变换（每个顶点只做一次）
        for (var i = 0; i < nv; i++) {
          var px, py, pz;
          if (isFlat) { px = V[i*3] - tx; py = V[i*3+1] - ty; pz = V[i*3+2] - tz; }
          else { var vv = V[i]; px = vv[0] - tx; py = vv[1] - ty; pz = vv[2] - tz; }
          var x1 = px * cy + py * sy;
          var y1 = -px * sy + py * cy;
          vsx[i] = x1;
          vsy[i] = y1 * cp - pz * sp;
          vsz[i] = y1 * sp + pz * cp;
        }

        var nTri = isFlat ? (F.length / 3) : F.length;
        for (var fi = 0; fi < nTri; fi++) {
          var a, b, c;
          if (isFlat) { a = F[fi*3]; b = F[fi*3+1]; c = F[fi*3+2]; }
          else { var f = F[fi]; a = f[0]; b = f[1]; c = f[2]; }

          var vax = vsx[a], vay = vsy[a], vaz = vsz[a];
          var vbx = vsx[b], vby = vsy[b], vbz = vsz[b];
          var vcx = vsx[c], vcy = vsy[c], vcz = vsz[c];

          // 视图空间面法线 → 背面剔除
          var ux = vbx - vax, uy = vby - vay, uz = vbz - vaz;
          var wx2 = vcx - vax, wy2 = vcy - vay, wz2 = vcz - vaz;
          var nx = uy * wz2 - uz * wy2, ny = uz * wx2 - ux * wz2, nz = ux * wy2 - uy * wx2;
          if (nz <= 0) continue;                       // 背面

          var lx, ly2, lz2;
          if (N) {
            var n0x, n0y, n0z;
            if (isFlat) { n0x = N[a*3]; n0y = N[a*3+1]; n0z = N[a*3+2]; }
            else { var nn = N[a]; n0x = nn[0]; n0y = nn[1]; n0z = nn[2]; }
            lx = n0x * cy + n0y * sy;
            var lly = -n0x * sy + n0y * cy;
            ly2 = lly * cp - n0z * sp;
            lz2 = lly * sp + n0z * cp;
          } else {
            var L = Math.sqrt(nx*nx + ny*ny + nz*nz) || 1;
            lx = nx / L; ly2 = ny / L; lz2 = nz / L;
          }
          var illum = lx * LIGHT[0] + ly2 * LIGHT[1] + lz2 * LIGHT[2];
          if (illum < 0) illum = 0;
          var shade = (0.30 + 0.70 * illum);

          var d0 = vaz + dist, d1 = vbz + dist, d2 = vcz + dist;
          var depth = (d0 + d1 + d2) * 0.3333333333333333;

          var fog = (depth - fogLo) / fogSpan;
          if (fog < 0) fog = 0; else if (fog > 1) fog = 1;
          var sh = shade * (1 - 0.28 * fog);

          var s0 = fz / d0, s1 = fz / d1, s2 = fz / d2;
          polys.push({
            regionId: reg.id, pickable: pickable, prio: prio, z: depth,
            x: [halfW + vax * s0, halfW + vbx * s1, halfW + vcx * s2],
            y: [halfH - vay * s0, halfH - vby * s1, halfH - vcy * s2],
            color: color, shade: sh, alpha: alpha, sel: !!isSel
          });
        }
      }
    }
    polys.sort(function (p, q) { return p.z - q.z; });   // 远 → 近
    return polys;
  }

  /** 把一帧指令画到 2D 上下文 */
  function drawFrame(ctx, polys, w, h, bg) {
    ctx.save();
    ctx.fillStyle = bg || '#0b1020';
    ctx.fillRect(0, 0, w, h);

    var g = ctx.createRadialGradient(w * 0.5, h * 0.42, 20, w * 0.5, h * 0.42, Math.max(w, h) * 0.75);
    g.addColorStop(0, 'rgba(56,189,248,0.055)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    // 颜色字符串缓存：把 shade 量化到 1/24，26 个区域 × 24 级 ≈ 600 个字符串，
    // 全部复用。否则每帧要新建 3 万个 rgba() 字符串，GC 会吃掉大部分时间。
    var Q = 24;
    var rgbCache = {};
    var colCache = {};
    function fillFor(color, shade, alpha) {
      var q = (shade * Q) | 0;
      if (q > Q) q = Q; else if (q < 0) q = 0;
      var key = color + '|' + q + '|' + alpha;
      var c = colCache[key];
      if (c !== undefined) return c;
      var rgb = rgbCache[color];
      if (!rgb) { rgb = rgbCache[color] = hexToRgb(color); }
      var s = q / Q;
      c = 'rgba(' + Math.min(255, Math.round(rgb[0] * s)) + ',' +
                    Math.min(255, Math.round(rgb[1] * s)) + ',' +
                    Math.min(255, Math.round(rgb[2] * s)) + ',' + alpha + ')';
      colCache[key] = c;
      return c;
    }

    var lastFill = null;
    for (var i = 0; i < polys.length; i++) {
      var p = polys[i];
      var f = fillFor(p.color, p.shade, p.alpha);
      if (f !== lastFill) { ctx.fillStyle = f; lastFill = f; }
      ctx.beginPath();
      ctx.moveTo(p.x[0], p.y[0]);
      ctx.lineTo(p.x[1], p.y[1]);
      ctx.lineTo(p.x[2], p.y[2]);
      ctx.closePath();
      ctx.fill();
      if (p.sel) {
        ctx.strokeStyle = 'rgba(255,255,255,0.85)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  /* ------------------------------------------------------------------
     5. 拾取：屏幕空间三角形包含测试
     ------------------------------------------------------------------ */
  function pointInTri(px, py, x, y) {
    var d1 = (px - x[1]) * (y[0] - y[1]) - (x[0] - x[1]) * (py - y[1]);
    var d2 = (px - x[2]) * (y[1] - y[2]) - (x[1] - x[2]) * (py - y[2]);
    var d3 = (px - x[0]) * (y[2] - y[0]) - (x[2] - x[0]) * (py - y[0]);
    var neg = (d1 < 0) || (d2 < 0) || (d3 < 0);
    var pos = (d1 > 0) || (d2 > 0) || (d3 > 0);
    return !(neg && pos);
  }

  /**
   * 拾取：返回最合适的一个区域
   *   规则：优先最近的命中；但若某个更深的命中具有「更高优先级」（prio 更小），
   *   则选它 —— 这样被包在大结构里的细分区域（如 CX-EB 在 MB 内）也能点到。
   *   背景结构（pickable:false）完全跳过。
   */
  function pick(polys, px, py, opts) {
    opts = opts || {};
    var skipBg = opts.skipBackground !== false;
    var best = null;
    for (var i = 0; i < polys.length; i++) {
      var p = polys[i];
      if (skipBg && !p.pickable) continue;
      if (px < Math.min(p.x[0], p.x[1], p.x[2]) - 1) continue;
      if (px > Math.max(p.x[0], p.x[1], p.x[2]) + 1) continue;
      if (py < Math.min(p.y[0], p.y[1], p.y[2]) - 1) continue;
      if (py > Math.max(p.y[0], p.y[1], p.y[2]) + 1) continue;
      if (!pointInTri(px, py, p.x, p.y)) continue;
      var prio = p.prio === undefined ? 3 : p.prio;
      if (!best) { best = { id: p.regionId, z: p.z, prio: prio }; continue; }
      if (prio < best.prio || (prio === best.prio && p.z < best.z)) {
        best = { id: p.regionId, z: p.z, prio: prio };
      }
    }
    return best;
  }

  /* ------------------------------------------------------------------
     6. 坐标轴指示器
     ------------------------------------------------------------------ */
  var AXES = [
    { d: [1, 0, 0], label: '右 (+X)', color: '#f87171' },
    { d: [0, 1, 0], label: '前 (+Y)', color: '#4ade80' },
    { d: [0, 0, 1], label: '背 (+Z)', color: '#7dd3fc' }
  ];

  function axisScreen(cam, w, h, origin, len) {
    var out = [];
    var s0 = project(cam, origin, w, h);
    for (var i = 0; i < AXES.length; i++) {
      var a = AXES[i];
      var tip = [origin[0] + a.d[0] * len, origin[1] + a.d[1] * len, origin[2] + a.d[2] * len];
      var s1 = project(cam, tip, w, h);
      out.push({ label: a.label, color: a.color, x0: s0[0], y0: s0[1], x1: s1[0], y1: s1[1] });
    }
    return out;
  }

  /**
   * 固定屏幕位置的方向指示器（HUD）
   *   只把轴向按当前 yaw/pitch 旋转后投到屏幕平面，不随模型移动与缩放。
   *   这样它可以钉在角落，绝不会被模型挡住或跑到画面外。
   */
  function axisHud(cam, cx, cy, len) {
    var cyaw = Math.cos(cam.yaw), syaw = Math.sin(cam.yaw);
    var cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
    var out = [];
    for (var i = 0; i < AXES.length; i++) {
      var a = AXES[i], d = a.d;
      // 与 worldToView 相同的旋转，但不做平移
      var x1 = d[0] * cyaw + d[1] * syaw;
      var y1 = -d[0] * syaw + d[1] * cyaw;
      var z1 = d[2];
      var y2 = y1 * cp - z1 * sp;
      // 屏幕 y 轴向下，所以取负
      out.push({
        label: a.label, color: a.color,
        x0: cx, y0: cy,
        x1: cx + x1 * len,
        y1: cy - y2 * len,
        // 深度：越大越靠近观察者（+Z 为观察方向）
        near: y1 * sp + z1 * cp
      });
    }
    return out;
  }

  /* ------------------------------------------------------------------ */
  var API = {
    DEG: DEG,
    REGIONS: REGIONS,
    buildEllipsoid: buildEllipsoid,
    buildMeshes: buildMeshes,
    loadOfficialGeometry: loadOfficialGeometry,
    STYLE: STYLE,
    makeCamera: makeCamera,
    worldToView: worldToView,
    viewToScreen: viewToScreen,
    project: project,
    buildFrame: buildFrame,
    drawFrame: drawFrame,
    pick: pick,
    pointInTri: pointInTri,
    axisScreen: axisScreen,
    axisHud: axisHud,
    hexToRgb: hexToRgb
  };

  root.MCNS3D = API;
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
})(typeof globalThis !== 'undefined' ? globalThis : this);
