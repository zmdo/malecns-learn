/* =====================================================================
   译文与标注 02-E · Shiu et al. 2024 方法（下）—— 收尾
   覆盖：SEZ split-GAL4 鉴定 / 触角梳理建模 / 光遗传与沉默实验 /
         钙成像 / 统计分析
   人工翻译，供学习使用；引用请以原文为准。
   ===================================================================== */
window.MCNS_NOTES_PARTS = window.MCNS_NOTES_PARTS || [];
window.MCNS_NOTES_PARTS.push({
  shiu: {
    sections: {
      'Identification of SEZ split-GAL4 neurons in the Flywire volume and computational activation': [
        { h: '⭐ 跨数据集匹配神经元的完整工作流（阶段 3 可直接抄）', tone: 'violet', body: [
          '问题：<b>怎么把光镜 split-GAL4 品系标注的细胞类型，对应到电镜体积里的具体神经元？</b>' +
          '这用的是 JRC2018U 标准脑（`splitgal4.janelia.org`）。',
          '<b>方法一（骨架点云）：</b>',
          '① 用 FIJI 把单神经元多色 Flp-out 图像骨架化（调阈值去背景、保留形态，用 Skeletonize 2D/3D）；' +
          '② 存为 <code>.nrrd</code>，在 <b>natverse</b> 转成 <code>.swc</code>；' +
          '③ 上传到 <b>FlyWire gateway</b> 生成点云；' +
          '④ 用点云<b>人工</b>识别目标神经元。',
          '<b>方法二（NBLAST 自动匹配）：</b>',
          '① 从 dotprops 格式的形态数据提取点云<sup>44</sup>；' +
          '② 用 <b>Navis + FlyBrains</b> 把点云从 <b>JRC2018U 空间变换到 FAFB 空间</b>；' +
          '③ 在点云密集区周围划 1–4 个三维框，用 <b>CloudVolume</b> 查询框内的神经元碎片；' +
          '④ 算骨架，用 <b>NBLAST</b> 与目标点云比相似度；' +
          '⑤ 取 NBLAST 分数最高的候选，<b>在 FlyWire 三维视图里人工目视确认</b>。',
          '关键工程细节：<b>两种方法、两组研究者独立做，只采纳明确一致的结果</b>；' +
          '然后把某细胞类型的<b>全部</b>已识别神经元都做计算激活，记录 MN9 放电率。',
          '<b>这段是"光镜 ↔ 电镜跨模态匹配"的标准配方</b> ——' +
          '阶段 3 若要做类似对应，骨架化 + 标准脑变换 + NBLAST + 人工确认 就是完整路线。'
        ]}
      ],
      'Modelling of the antennal grooming circuit': [
        { h: '触角梳理回路的仿真参数', tone: 'blue', body: [
          '激活 <b>147 个 JON</b>（JO-C、JO-E、JO-F、JO-mz 类），生成 <b>20–220 Hz</b> 放电；' +
          '30 次 1,000 ms 模拟；取<b>放电最高的 300 个神经元</b>，' +
          '以 <b>50/100/150/200 Hz</b> 激活，判断能否激活 aDN1 或 aDN2；' +
          '再<b>逐个沉默这 300 个</b>，记录 aDN1/aDN2 活动。',
          '注意与摄食回路的差异：那里取 top <b>200</b>，这里取 top <b>300</b> —— ' +
          '说明这类阈值是<b>按回路调的</b>。'
        ]}
      ],
      'Chrimson optogenetic activation experiments': [
        { h: '光遗传激活的标准流程（含一个重要的盲法细节）', tone: 'green', body: [
          '流程要点：',
          '· 雌蝇在标准培养基上饲养；实验前 <b>48 h</b> 转移到含 <b>0.4 mM 视黄醛（retinal）</b> 的食物；' +
          '· <b>3–5 日龄</b>，CO₂ 麻醉，指甲油粘到载玻片上，<b>22 °C 湿润腔中恢复 2 h</b>；' +
          '· 光刺激：<b>153 μW·mm<sup>−2</sup> 的 635 nm 激光</b>（Laserglow）；' +
          '· 判据：<b>光照后 5 秒内是否伸出喙</b>。',
          '两个值得学的严谨细节：',
          '① <b>实验对基因型盲法</b>（blind to genotype）；' +
          '② <b>两级筛选</b>：先看"喙的任何运动"（每基因型 10 只），' +
          '<b>凡有伸出的，再用第二个独立杂交、专门针对喙基伸出（即 MN9 激活）复测一次</b>。' +
          '若测试了多个 split-GAL4 品系，图 2b 显示 MN9 最高的那个。'
        ]}
      ],
      'Silencing experiments': [
        { h: '沉默实验：注意"脱水处理"这一步', tone: 'blue', body: [
          '· 3 日龄雌蝇，标准食物 + <b>0.4 mM all-trans 视黄醛 48 h</b>；' +
          '· 麻醉、粘片后，在含约 <b>250 g CaSO₄（Drierite）</b> 的密封腔中 <b>22 °C 脱水 3 h</b>' +
          '（参考文献<sup>75</sup>）—— <b>这一步是为了制造"口渴"状态</b>；' +
          '· 用 <b>532 nm 绿激光</b>配合 <b>GtACR1</b>（阴离子通道视紫红质<sup>76</sup>）急性沉默；' +
          '· 对喙<b>呈水三次</b>，记录至少伸出一次的果蝇数。',
          'Kir2.1 与 <i>Amontillado</i> RNAi 实验同样流程，<b>但不加视黄醛、不用绿激光</b>（因为不依赖光）。'
        ]}
      ],
      'Ir94e and Gr66a optogenetic activation': [
        { h: '改用红光激活', tone: 'blue', body: [
          '与 GtACR1 实验相同，但<b>用红光而非绿光</b><sup>77</sup>。',
          '· 标准食物 + <b>0.4 mM 视黄醛饲养 4 天</b>；' +
          '· 恢复 2 h 后，用 <b>153 μW·mm<sup>−2</sup> 的 635 nm 激光</b>；' +
          '· 果蝇先<b>饮水至饱（water satiated）</b>，再对喙呈 <b>50 mM 或 1 M 蔗糖</b>三次，记录伸出比例；' +
          '· <b>同样对基因型盲法</b>。',
          '注意"先让果蝇喝饱水"这个步骤 —— <b>是为了排除口渴状态对糖反应的干扰</b>，' +
          '这也是为什么后面能用同一个 PER 读数比较糖与水的通路。'
        ]}
      ],
      'Calcium imaging setup for Fudog and Zorro imaging': [
        { h: '⭐ 一个巧妙的"人造口渴"方法', tone: 'violet', body: [
          '标本与手术：<b>交配过的雌蝇</b>，羽化后 <b>14–21 天</b>解剖；' +
          '用冰短暂麻醉，颈部固定在定制塑料支架上以隔离头部；' +
          '<b>紫外光固化胶</b>固定头部，<b>剪开食管</b>以获得通往 SEZ 的无遮挡成像通路。',
          '关键设计：',
          '· <b>Fudog</b>（测饥饿）：成像前在含湿纸巾的小瓶中<b>食物剥夺 18–24 h</b>；' +
          '解剖后浸在<b>约 250 mOsmo 的人工血淋巴样溶液（AHL）</b>中，立即成像。' +
          '· <b>Zorro</b>（测口渴）：解剖后浸在<b>高渗 AHL（约 350 mOsmo）</b>中<b>静置 1 h</b> 再成像 ——' +
          '<b>这就是所谓 "pseudodessicated（假脱水）" 果蝇的造法：不真的脱水，而是用高渗浴液制造口渴状态。</b>',
          '—— 这个"用渗透压而不是真实脱水来操纵内部状态"的技巧很值得学：' +
          '<b>它把行为状态变成了可精确控制、可重复的实验变量。</b>'
        ]}
      ],
      'Calcium imaging of Fudog and Zorro': [
        { h: '钙成像的成像参数与"呈味"技巧', tone: 'blue', body: [
          '遗传背景：UAS-CD8-tdTomato;20XUAS-IVS-GCaMP6s(attP5);20XUAS-IVS-GCaMP6s(VK00005) 雌蝇 × 各 split-GAL4 雄蝇，' +
          '取无平衡子的雌性后代成像。',
          '三种呈味物质：<b>双蒸水（"水"）、1 M 蔗糖（"糖"）、10 mM 地那铵 + 100 mM 咖啡因溶于 20% 聚乙二醇（"苦味"）</b>。',
          '呈味方式：玻璃毛细管（外径 1.0 mm、内径 0.78 mm）装约 4 µl 溶液，' +
          '用显微操纵器定位在喙尖；<b>每次成像开始时先用注射器轻微回吸，让溶液离开毛细管口</b>，' +
          '再在合适时刻<b>轻压注射器</b>把溶液递送到喙上。',
          '—— 这个"先回吸再递送"的细节是为了<b>精确控制刺激起始时刻</b>，让每个试次的时间对齐。',
          '<b>Fudog</b>（单光子）：3i 转盘共聚焦 + 压电驱动 + ×20 水镜（NA = 1.0）+ ×2.5 放大变换器；' +
          '<b>488 nm 激光，0.8 Hz</b>；8 个 z 层、间隔 1 µm，共 <b>55 帧</b>，按 4×4 合并；' +
          '<b>呈味溶液在第 20–25 帧接触唇瓣</b>。',
          '<b>Zorro</b>（双光子）：Scientifica Hyperscope 共振扫描 + 压电驱动 + ×20 水镜（NA = 1.0）+ ×4 数字变焦；' +
          '<b>920 nm 激光，0.667 Hz</b>；20 个 z 层、间隔 2 µm，共 <b>80 个 stack</b>；' +
          '<b>溶液在第 30–40 帧接触唇瓣</b>。'
        ]}
      ],
      'Functional connectivity between JON subpopulations and aBN1': [
        { h: '双表达系统：在一只果蝇里同时做激活与读out', tone: 'violet', body: [
          '这个实验需要<b>两个二元表达系统</b>（GAL4/UAS 与 LexA/LexAop），' +
          '以便在<b>同一只果蝇的不同神经元中</b>分别表达 CsChrimson 与 GCaMP6。',
          '· 用 <b>LexA 与 spGAL4 驱动系</b>（分别对 JO-CE 或 JO-F 特异）在 JON 亚群中表达 <b>CsChrimson</b>；' +
          '· 选取 <b>aBN1 特异的 ROI</b>；' +
          '· 通过物镜用 LED 给予 <b>2 ms、590 nm 光脉冲</b>激发 CsChrimson。',
          '—— <b>"用两套正交表达系统在一只动物里同时刺激和记录"是果蝇功能连接实验的经典范式</b>，' +
          '阶段 4 若要自己设计验证实验，这是模板。'
        ]}
      ],
      'Taste response calcium imaging analysis': [
        { h: '钙成像数据分析的完整管线', tone: 'blue', body: [
          '工具链：<b>Fiji + CircuitCatcher（自定义 Python 程序）+ Python + R</b>。',
          '① Fiji：各时间点的 z stack 做<b>最大强度投影</b>，' +
          '再用 <b>StackReg 插件</b>（"Rigid Body"或"Translation"）做<b>运动校正</b><sup>79</sup>；' +
          '② CircuitCatcher：圈出<b>目标细胞类型神经突起的 ROI</b> 以及一个<b>背景 ROI</b>，' +
          '取各时间点各 ROI 的平均荧光强度；' +
          '③ Python：逐时间点做<b>背景扣除</b>得 <i>F</i><sub>t</sub>；' +
          '④ <b>基线 <i>F</i><sub>initial</sub></b> = 第 9–18 帧（单光子）或第 0–19 帧（双光子与光遗传成像）的均值；' +
          '⑤ 计算 <b>Δ<i>F</i>/<i>F</i> = (<i>F</i><sub>t</sub> − <i>F</i><sub>initial</sub>) / <i>F</i><sub>initial</sub></b>；' +
          '⑥ <b>曲线下面积</b>用 Python 的 <code>NumPy.trapz</code>（梯形法）近似，' +
          '单光子成像取<b>第 20–25 帧</b>。',
          '注意第 ④ 步：<b>基线窗口的选择与成像模式绑定</b> ——' +
          '这是复现时最容易搞错的地方，因为基线取错了 ΔF/F 会整体偏移。'
        ]}
      ],
      'Statistical analysis': [
        { h: '统计方法清单', tone: 'green', body: [
          '· 行为学与计算建模分析在 <b>Prism</b> 中完成；' +
          '· 实验组与对照组 PER 比例比较：<b>Fisher 精确检验</b>；' +
          '· 计算建模预测比较：<b>双尾 Mann–Whitney <i>U</i> 检验</b>；' +
          '· 钙成像统计：R、Python（味觉成像）、Julia（JON 功能连接）；' +
          '· 味觉刺激钙成像：<b>Quade 检验 + Quade 全对检验，Holm 校正</b>多重比较；' +
          '· <b>除"检验呈味钙响应是否大于零"用 Wilcoxon 单侧检验外，全部统计检验均为双尾</b>；' +
          '· 所有展示的行为数据<b>至少独立重复成功两次</b>（行为实验中一次重复 = 一只果蝇）；' +
          '· 行为学原始数据见补充表 9。'
        ]}
      ]
    },

    trans: {
      'Identification of SEZ split-GAL4 neurons in the Flywire volume and computational activation': [
        'SEZ split-GAL4 文库的 138 个细胞类型中，共有 <b>106 个</b>在 FlyWire 体积中被识别<sup>44,71</sup>。' +
          '我们用两种<b>半独立</b>的方法来识别这些神经元。' +
          '第一种方法：从 https://splitgal4.janelia.org 下载对齐后的 JRC2018 通用注册脑，' +
          '并在可能的情况下使用单神经元多色 Flp-out 图像。' +
          '在 FIJI 中对神经元做骨架化，' +
          '阈值的选择以消除背景、同时保留神经元形态为准。' +
          '神经元用「Skeletonize 2D/3D」工具骨架化，文件存为 <code>.nrrd</code>。' +
          '这些 <code>.nrrd</code> 文件在 natverse<sup>72</sup> 中转换为 <code>.swc</code>，' +
          '并上传到 FlyWire gateway（https://flywiregateway.pniapps.org/upload）。' +
          '由此生成的点云被用来<b>人工</b>识别目标神经元。',

        '在第二种方法中，我们借助 <b>NBLAST</b><sup>73</sup> 来识别 FlyWire 中的 SEZ 中间神经元。' +
          'SEZ split-GAL4 中间神经元的形态来自单神经元多色 Flp-out 图像，' +
          '以 <b>dotprops 格式</b>提供<sup>44</sup>，我们从中提取每个神经元的点云。' +
          '点云用 Navis 与 FlyBrains 库从 JRC2018U 脑空间变换到 FAFB 空间。' +
          '为缩小 FlyWire 中点云附近的候选神经元范围，' +
          '我们在点云密集区周围划定了 1 到 4 个三维框。' +
          '框内的神经元碎片通过 FlyWire 的 CloudVolume 输入/输出接口查询。' +
          '随后计算这些神经元碎片的骨架，' +
          '并用 NBLAST 测量它们与 SEZ 中间神经元 dotprops 的相似度。' +
          'NBLAST 分数最高的候选者在 FlyWire 三维视图中与点云做目视比对，以作最终判定。',

        'SEZ split-GAL4 神经元由两种方法与两组研究者<b>独立</b>识别，' +
          '只采用两者明确一致的结果。' +
          '某细胞类型中所有已识别的神经元都被计算激活，并记录所得的 MN9 放电率。'
      ],

      'Modelling of the antennal grooming circuit': [
        '此前已识别并在电镜体积中描述了共 <b>147 个</b>属于 JO-C、JO-E、JO-F 与 JO-mz 类的 JON<sup>7</sup>。' +
          '与摄食启动回路一样，JON 被激活以产生 <b>20–220 Hz</b> 放电。' +
          '我们记录在 30 次 1,000 ms 模拟中任一次出现放电的所有神经元的放电时刻，' +
          '再把这些数据转换为每秒平均放电率。' +
          '随后把放电最高的 <b>300 个</b>神经元以 <b>50、100、150、200 Hz</b> 激活，' +
          '以确定它们能否激活 aDN1 或 aDN2。' +
          '在激活全部 147 个 JON 的同时，' +
          '通过对这 300 个放电最高的神经元逐一消除其全部输出来沉默它们，' +
          '并记录 aDN1 或 aDN2 的活动。' +
          'aBN1、aBN2、aDN1 与 aDN2 均按其此前描述的形态被识别与注释<sup>2,6,7</sup>。'
      ],

      'Chrimson optogenetic activation experiments': [
        'PER 的评分方式如此前所述<sup>4,74</sup>。' +
          '雌蝇在标准玉米粉–酵母–糖蜜培养基上饲养。' +
          '实验前 48 小时，把果蝇转移到含 <b>0.4 mM 视黄醛</b>的糖蜜食物上。' +
          '果蝇（3–5 日龄）用二氧化碳麻醉，' +
          '用指甲油粘到玻璃载玻片上，' +
          '并在 <b>22 °C</b> 的湿润腔中恢复 2 小时。' +
          '光遗传激活实验使用 <b>153 μW·mm<sup>−2</sup> 的 635 nm 激光</b>（Laserglow）。' +
          '记录果蝇是否在光照后 <b>5 秒</b>内伸出喙。' +
          '实验对基因型<b>盲法</b>进行。' +
          '筛选时，每个基因型评估 10 只果蝇喙的任何运动。' +
          '凡出现任何伸出的 split-GAL4，' +
          '再用第二个独立的杂交、专门针对<b>喙基伸出</b>（即 MN9 激活）复测一次。' +
          '若测试了多个 split-GAL4 品系，图 2b 显示 MN9 最高的那个品系。'
      ],

      'Silencing experiments': [
        '三日龄雌蝇在标准玉米粉–酵母–糖蜜培养基上饲养，' +
          '随后转移到含 <b>0.4 mM all-trans 视黄醛</b>的标准食物上 48 小时。' +
          '果蝇用二氧化碳麻醉，用指甲油粘到玻璃载玻片上，' +
          '并在一个含约 <b>250 g CaSO<sub>4</sub></b>（Drierite，货号 23001）的密封腔中、' +
          '<b>22 °C 下脱水 3 小时</b>（参考文献<sup>75</sup>）。' +
          '使用 <b>532 nm 绿激光</b>（LaserGlow LBS-532）配合 <b>GtACR1</b><sup>76</sup> 急性沉默神经元。' +
          '对喙呈水三次，记录至少伸出一次的果蝇数量。' +
          'Kir2.1 与 <i>Amontillado</i> RNAi 实验按上述流程进行，' +
          '但不使用 all-trans 视黄醛或绿激光。'
      ],

      'Ir94e and Gr66a optogenetic activation': [
        '实验按 GtACR1 实验的方式进行，' +
          '只是果蝇接受<b>红光</b>而非绿光<sup>77</sup>。' +
          '果蝇在含 0.4 mM 视黄醛的标准食物上饲养 4 天。' +
          '果蝇用二氧化碳麻醉，用指甲油粘到玻璃载玻片上，' +
          '并在 22 °C 的湿润腔中恢复 2 小时。' +
          '使用 <b>153 μW·mm<sup>−2</sup> 的 635 nm 激光</b>（Laserglow）。' +
          '果蝇先<b>饮水至饱</b>，' +
          '随后对喙呈 <b>50 mM 蔗糖或 1 M 蔗糖</b>三次，' +
          '记录至少伸出一次的果蝇数量。' +
          '实验对基因型<b>盲法</b>进行。'
      ],

      'Calcium imaging setup for Fudog and Zorro imaging': [
        '用于钙成像研究的<b>已交配雌蝇</b>在羽化后 14–21 天解剖，方法如此前所述<sup>4,29</sup>。' +
          '果蝇用冰短暂麻醉，' +
          '同时把它们以颈部放入一个定制的塑料固定器中，以把头与身体其余部分隔离。' +
          '随后用<b>紫外光固化胶</b>固定头部，并<b>剪开食管</b>，' +
          '以获得通往 SEZ 的无遮挡成像通路。' +
          '对 <b>Fudog</b>，果蝇在成像前于含湿纸巾的小瓶中<b>食物剥夺 18–24 小时</b>。' +
          '解剖后，样本浸在<b>人工血淋巴样溶液（AHL，约 250 mOsmo）</b>中并立即成像。' +
          '为生成<b>类似口渴（假脱水）</b>的 Zorro 果蝇<sup>4</sup>，' +
          '解剖后把样本浸在<b>高渗 AHL（约 350 mOsmo）</b>中并静置 1 小时，然后再成像。'
      ],

      'Calcium imaging of Fudog and Zorro': [
        '为成像对味觉溶液的响应，' +
          '把 UAS-CD8-tdTomato;20XUAS-IVS-GCaMP6s(attP5);20XUAS-IVS-GCaMP6s(VK00005) 雌蝇' +
          '与各 split-GAL4 品系的雄蝇杂交，' +
          '选取不含平衡子的雌性后代用于成像。' +
          '使用以下呈味物质：' +
          '<b>双蒸水（"水"）</b>、<b>1 M 蔗糖（"糖"）</b>、' +
          '或<b>10 mM 地那铵加 100 mM 咖啡因溶于 20% 聚乙二醇（"苦味"）</b>。' +
          '味觉溶液通过一根玻璃毛细管（外径 1.0 mm、内径 0.78 mm）递送到喙上，' +
          '毛细管内装约 4 µl 溶液，用显微操纵器定位在喙尖。' +
          '每次成像试次开始时，' +
          '先用连接着的 1 ml 注射器轻轻抽吸，把味觉溶液从毛细管口吸离，' +
          '再在成像过程中的相应时刻对注射器施加轻微压力，把溶液递送到喙上。',

        '我们用 3i 转盘共聚焦显微镜对 <b>Fudog</b> 做单光子成像，' +
          '配置压电驱动、×20 水浸物镜（数值孔径 1.0）与 ×2.5 放大变换器，方法如此前所述<sup>4</sup>。' +
          '共采集 55 帧、每帧 8 个 z 层（间隔 1 µm 或 μM），按 4 × 4 合并，' +
          '使用 488 nm 激光、以 0.8 Hz 采集。' +
          '味觉溶液在第 20 帧到第 25 帧之间与喙的唇瓣接触。',

        '我们用 Scientifica Hyperscope（共振扫描、压电驱动、' +
          '×20 水浸物镜（数值孔径 1.0）与 ×4 数字变焦）对 <b>Zorro</b> 做双光子成像，' +
          '方法如此前所述<sup>4</sup>。' +
          '共采集 80 个 stack、每个含 20 个 z 层（间隔 2 µm），' +
          '使用 920 nm 激光、以 0.667 Hz 采集。' +
          '味觉溶液在第 30 帧到第 40 帧之间与喙的唇瓣接触。'
      ],

      'Functional connectivity between JON subpopulations and aBN1': [
        'JON 功能连接实验按此前所述进行<sup>8</sup>。' +
          '该实验需要使用<b>两个二元表达系统</b>（GAL4/UAS 与 LexA/LexAop），' +
          '以便在同一只果蝇的不同神经元中分别驱动 <b>CsChrimson</b> 与 <b>GCaMP6</b> 的表达。' +
          '我们用对 JO-CE 或 JO-F 神经元特异的 LexA 与 spGAL4 驱动系，' +
          '在 JON 亚群中表达 CsChrimson。' +
          '选取 aBN1 特异的感兴趣区域（ROI），' +
          '并通过物镜用发光二极管给予 <b>2 ms、590 nm 的光脉冲</b>来激发 CsChrimson。'
      ],

      'Taste response calcium imaging analysis': [
        '对扩展数据图 1c 与 3a 的钙成像分析，' +
          '图像处理在 Fiji<sup>78</sup>、CircuitCatcher（D. Bushey 编写的定制 Python 程序）、' +
          'Python 与 R 中完成。' +
          '首先在 Fiji 中，对各时间点的 z stack 做<b>最大强度投影</b>，' +
          '再用 StackReg 插件以「刚体」或「平移」变换做<b>运动校正</b><sup>79</sup>。' +
          '接着用 CircuitCatcher 圈出包含目标细胞类型神经突起的感兴趣区域（ROI）以及一个背景 ROI，' +
          '并取出各时间点各 ROI 的平均荧光强度。' +
          '随后在 Python 中对每个时间点（<i>F</i><sub>t</sub>）做<b>背景扣除</b>。' +
          '为计算 <i>F</i><sub>initial</sub>，' +
          '初始荧光强度取第 9–18 帧（单光子成像）' +
          '或第 0–19 帧（双光子与光遗传成像）经校正后的平均荧光强度均值。' +
          '最后用下式计算：' +
          'Δ<i>F</i>/<i>F</i> = (<i>F</i><sub>t</sub> − <i>F</i><sub>initial</sub>) / <i>F</i><sub>initial</sub>。' +
          '曲线下面积在 Python 中用 NumPy.trapz 函数以梯形法近似。' +
          '曲线下面积取第 20 帧到第 25 帧（单光子成像）。'
      ],

      'Statistical analysis': [
        '行为学测定与计算建模的分析在 Prism 中完成。' +
          '实验果蝇与对照果蝇之间 PER 响应比例的比较好，用 <b>Fisher 精确检验</b>。' +
          '计算建模预测的比较使用<b>双尾 Mann–Whitney <i>U</i> 检验</b>。' +
          '钙成像的统计分析在 R、Python（味觉成像）与 Julia（JON 功能连接）中完成。' +
          '对味觉刺激钙成像实验，我们使用 Quade 检验与 Quade 全对检验，' +
          '并用 Holm 校正来调整多重比较。' +
          '所用的全部统计检验均为<b>双尾</b>，' +
          '唯一例外是用于检验呈味物质钙成像响应是否大于零的 Wilcoxon 单侧检验。' +
          '所展示的全部行为数据都至少<b>独立重复成功两次</b>；' +
          '在行为实验中，一次重复即一只果蝇。' +
          '行为数据的原始数据见补充表 9。'
      ]
    }
  }
});
