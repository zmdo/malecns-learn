/* =====================================================================
   mcns-region-info.js — 每个官方神经毡网格的解说文字

   id 必须与 assets/mcns-meshes.js 里的 key 一致：
     MB, MB-CA, CX, CX-EB, AL, LH, SEZ, AOTU, LAL, SMP, SLP, SIP,
     CRE, WED, VES, IB, BU, LA, ME, LO, LOP,
     VNC-T1, VNC-T2, VNC-T3, VNC-AB, VNC-INT

   缩写与全称依据 Ito et al. 2014, Neuron 81(4):755-765（脑）
   与 Court et al. 2020, Neuron 107(6):1071-1079（VNC）。
   ===================================================================== */
window.MCNS_REGION_INFO = {
  MB: {
    name: '蘑菇体', abbr: 'MB', en: 'Mushroom Body',
    desc: '学习与记忆的核心结构。内在神经元叫 Kenyon 细胞（KC）：轴突在「萼」(CA) 接收嗅觉输入，' +
          '再沿垂直叶（α/α′）与水平叶（β/β′/γ）输出到蘑菇体输出神经元（MBON）。' +
          '多巴胺能神经元在这里提供奖惩信号，是果蝇联想学习回路的所在地。',
    note: '由 14 个官方网格合并：CA(L/R)、PED(L/R)、aL(R)、a\'L(L/R)、bL(R)、b\'L(L/R)、gL(L/R)'
  },
  'MB-CA': {
    name: '蘑菇体萼', abbr: 'CA', en: 'Calyx',
    desc: '蘑菇体的输入区：Kenyon 细胞的树突在这里接收来自触角叶的嗅觉投射。' +
          '「萼」的名字来自它的杯状外形。',
    note: '官方网格：CA(L)、CA(R)'
  },
  CX: {
    name: '中央复合体', abbr: 'CX', en: 'Central Complex',
    desc: '导航、朝向与运动控制的中枢，由四个互锁神经毡组成：椭球体（EB）、扇形体（FB）、' +
          '原脑桥（PB）、上/下神经毡（NO）。它维持「头朝向」的内部表征并把朝向转成转向指令 —— ' +
          '也是性别二态细胞高度富集的区域。',
    note: '官方网格：EB、FB、NO、PB'
  },
  'CX-EB': {
    name: '椭球体', abbr: 'EB', en: 'Ellipsoid Body',
    desc: '中央复合体的环形结构，是头朝向信号的主要输出枢纽。环上的活动「凸包」位置对应当前朝向 —— ' +
          '连接组里最优雅的环形拓扑例子之一。',
    note: '官方网格：EB'
  },
  AL: {
    name: '触角叶', abbr: 'AL', en: 'Antennal Lobe',
    desc: '嗅觉的第一级中枢。嗅觉受体神经元（ORN）从触角进来后在这里换元，' +
          '再投射到侧角（LH）与蘑菇体（MB）。约 50 个嗅小球（glomerulus）构成它的功能单元。',
    note: '官方网格：AL(L)、AL(R)'
  },
  LH: {
    name: '侧角', abbr: 'LH', en: 'Lateral Horn',
    desc: '嗅觉的高级整合区，主要处理先天性嗅觉行为（求偶、产卵、躲避）。' +
          '与蘑菇体不同，LH 的回路更接近「硬接线」，不依赖学习。',
    note: '官方网格：LH(L)、LH(R)'
  },
  SEZ: {
    name: '食管下区 / 颚神经毡', abbr: 'GNG', en: 'Subesophageal Zone / Gnathal Ganglion',
    desc: '味觉与摄食的中枢，也是大量下行神经元（DN）的胞体所在。味觉受体神经元（GRN）在这里换元，' +
          '再把信号送往运动神经元 —— 标准验证通路「糖 GRN → SEZ → MN9」经过此处。' +
          '在 MaleCNS 的官方 ROI 图层里，这个结构登记的缩写是 GNG（颚神经毡）。',
    note: '官方网格：GNG'
  },
  AOTU: {
    name: '前视结节', abbr: 'AOTU', en: 'Anterior Optic Tubercle',
    desc: '位于视叶与中央脑之间，与偏振光导航和头朝向系统的输入有关。' +
          '官方 Dimorphism Explorer 里的二态示例类型 AOTU012 就位于这一区域。',
    note: '官方网格：AOTU(L)、AOTU(R)'
  },
  LAL: {
    name: '侧副叶', abbr: 'LAL', en: 'Lateral Accessory Lobe',
    desc: '中央脑前下部的一对神经毡，与嗅觉、味觉的多模态整合以及求偶行为回路相关。',
    note: '官方网格：LAL(L)、LAL(R)'
  },
  SMP: {
    name: '上内侧原脑', abbr: 'SMP', en: 'Superior Medial Protocerebrum',
    desc: '前脑上部的联合区，接收来自蘑菇体与中央复合体的高级输出。' +
          '缩写与全称依据 Ito et al. 2014 的脑区命名体系。',
    note: '官方网格：SMP(L)、SMP(R)'
  },
  SLP: {
    name: '上外侧原脑', abbr: 'SLP', en: 'Superior Lateral Protocerebrum',
    desc: '前脑上部偏外侧的联合区，视觉投射神经元（VPN）的主要终止区之一。',
    note: '官方网格：SLP(L)、SLP(R)'
  },
  SIP: {
    name: '上后侧原脑', abbr: 'SIP', en: 'Superior Intermediate Protocerebrum',
    desc: '位于上外侧原脑与上内侧原脑之间的联合区。',
    note: '官方网格：SIP(L)、SIP(R)'
  },
  CRE: {
    name: '侧后脑', abbr: 'CRE', en: 'Crepine',
    desc: '前脑与视叶之间的过渡区，是视觉投射纤维进入中央脑的通道附近。',
    note: '官方网格：CRE(L)、CRE(R)'
  },
  WED: {
    name: '楔形区', abbr: 'WED', en: 'Wedge',
    desc: '中央脑前上部的一小块神经毡。',
    note: '官方网格：WED(L)、WED(R)'
  },
  VES: {
    name: '前侧沟区', abbr: 'VES', en: 'Vest',
    desc: '中央脑前部的一个小神经毡，靠近食管下区上方。',
    note: '官方网格：VES(L)、VES(R)'
  },
  IB: {
    name: '下脑桥', abbr: 'IB', en: 'Inferior Bridge',
    desc: '中央脑下部、食管孔两侧的桥状结构。' +
          '注意：它在三维上被相邻结构包住，从这个视角看不到 —— 用右侧列表选中它。',
    note: '官方网格：IB（本视角被遮挡）'
  },
  BU: {
    name: '球状体', abbr: 'BU', en: 'Bulb',
    desc: '侧角附近的球状神经毡，与嗅觉投射回路相关。',
    note: '官方网格：BU(L)、BU(R)'
  },
  LA: {
    name: '板层', abbr: 'LA', en: 'Lamina',
    desc: '视叶四层中最外层，是光感受器 R1–R6 的投射终点。' +
          '它保留了眼睛的视网膜拓扑（retinotopic），每个小眼对应一个 cartridge。',
    note: '官方网格：LA(L)、LA(R)'
  },
  ME: {
    name: '髓质', abbr: 'ME', en: 'Medulla',
    desc: '视叶中最大的一层，处理运动、颜色与偏振光。R7 / R8 直接投射到这里，' +
          '是视觉计算的主战场。',
    note: '官方网格：ME(L)、ME(R)'
  },
  LO: {
    name: '小叶', abbr: 'LO', en: 'Lobula',
    desc: '视叶第三层，处理更抽象的视觉特征（小目标、朝向）。' +
          '许多视觉投射神经元（VPN）从这里把信息送入中央脑。',
    note: '官方网格：LO(L)、LO(R)'
  },
  LOP: {
    name: '小叶板', abbr: 'LOP', en: 'Lobula Plate',
    desc: '视叶第四层，是光流与自身运动检测的中心。著名的 T4 / T5 细胞就在这里，' +
          '专门编码四个方向的运动 —— 也是 FlyWire 上研究得最透的视觉回路。' +
          '注意：它被板层、髓质、小叶挡住，用右侧列表选中它。',
    note: '官方网格：LOP(L)、LOP(R)（本视角被遮挡）'
  },
  'VNC-T1': {
    name: '前胸神经节 (T1)', abbr: 'T1', en: 'Prothoracic Neuromere',
    desc: '腹神经索的第一个胸神经节，控制前足与前翅相关运动回路。' +
          'VNC 命名法见 Court et al. 2020, Neuron 107:1071。' +
          '这一块是 FlyWire FAFB 完全没有的。',
    note: '官方网格：LegNp(T1)(L/R)、mVAC(T1)(L/R)、NTct(UTct-T1)(L/R)'
  },
  'VNC-T2': {
    name: '中胸神经节 (T2)', abbr: 'T2', en: 'Mesothoracic Neuromere',
    desc: '腹神经索的第二个胸神经节，对应中足与飞行肌（翅）的主要运动控制。',
    note: '官方网格：LegNp(T2)(L/R)、mVAC(T2)(L/R)、WTct(UTct-T2)(L/R)'
  },
  'VNC-T3': {
    name: '后胸神经节 (T3)', abbr: 'T3', en: 'Metathoracic Neuromere',
    desc: '腹神经索的第三个胸神经节，对应后足与平衡棒（haltere）回路。',
    note: '官方网格：LegNp(T3)(L/R)、mVAC(T3)(L/R)、HTct(UTct-T3)(L/R)'
  },
  'VNC-AB': {
    name: '腹部神经节区', abbr: 'AB', en: 'Abdominal Neuromere',
    desc: '神经索尾端的融合神经节，控制腹部肌肉、生殖与排泄相关回路。' +
          '这里的 ANm / CV / Ov 都是腹部神经毡。',
    note: '官方网格：ANm、CV、Ov(L)、Ov(R)'
  },
  'VNC-INT': {
    name: '节间连合区', abbr: 'INT', en: 'Intersegmental Tectulum',
    desc: '胸神经节之间的连合区域（LTct 纵行连合、IntTct 节间连合），' +
          '前胸与中胸之间的大型纤维区。',
    note: '官方网格：IntTct、LTct'
  }
};
