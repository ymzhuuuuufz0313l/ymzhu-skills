---
name: power-clinic
description: DC 后网表（pre-APR）功耗体检与 ECO。主入口是第一步体检——网表时钟网谱系 × RTL 定性 × PowerPro 四场景功耗三方交叉，找"哪里代码 DC 没做好"，只 D/E/G 类进候选，每条写成一张 GitHub issue（现状→因果→改法→为什么对→好处→风险；范例 HK1V11 issue 2/3/4）。拍板后才网表先行改（叶子级 ICG、删冗余 FF，CTS 不动）、RTL 跟上、miter+LEC+case。树级时钟改动、PTPX 不在范围。触发词：功耗 ECO、功耗会诊、DC 优化体检、哪里 DC 没做好、哪里 DC 没门控、power clinic、四场景功耗、网表加 ICG、DC 后网表改门控、哪里 DC 不敢优化、裸挂 flop、跨域寄存器、冗余 FF、删寄存器、网表先行、ECO 候选清单、DC 抢跑、PIX_CLK_EN。
---

# power-clinic — DC 后网表功耗会诊与 ECO：体检 → 找点 → 网表先行 → RTL 跟上 → 三道证据

> **名字**：2026-11-24 由 power-eco 改名。重心在"会诊"——网表时钟网谱系、RTL 定性、PowerPro 四场景功耗三方交叉出诊断和 issue；网表 ECO 是拍板之后的执行段。旧文档里写的 power-eco 就是本 skill。

## 何时用

- **DC 综合后、APR 前**的网表功耗 ECO：有 `rep_dir/<top>.gv`、对应 RTL、PowerPro csv，想在不重跑综合的前提下让功耗降一点。
- **用户指定模块**（"我想做 LONG_ENCODING_OUTPUT"）或**只有单份功耗报告**时，按本 skill 找点。
- **DC 已经自动做了大部分**（HK1V11 实测：148 个 DC 自动 ICG、53% 的 flop 已门控）——裸挂的 flop 里只有一小部分是 DC **没做好**的，其余是设计上不该门控、或时钟源头已经门控。本 skill 的核心就是用三方交叉把那一小部分挑出来，并说清"为什么没做"。

**不适用**（走别的路）：
- base 层冻结只改走线 → `netlist-metal-eco`
- 要改时钟树结构（CLKGEN 根部加分叉、改 MUX、重分叉）→ 本 skill **明确剔除**，ECO 阶段动 tree 代价太大
- 架构重构（串行化、资源共享、协议改动）→ 走 RTL 改完重新 DC
- 门级功耗定数 → 用户跑 PTPX，本 skill 不碰

## 本 skill 的重心（2026-11-24 ymzhu 确认）

**第一步体检是本 skill 最有价值的部分**：拿网表、RTL、PowerPro 报告三方交叉，回答"哪些代码 DC 没做好、为什么、值多少钱"。体检的产出直接写成 GitHub issue 交给人拍板（§六；模板是 HK1V11 的 issue 2、3、4）。后面的网表改动和三道证据，只在人点了某张票之后才做。

用户说"先做第一步""体检""找 DC 没做好的地方"时：范围先和用户确认（哪几个模块、用哪版网表和 RTL），全程只读，做到 issue 发出、候选表摆出来就停，等确认再动手。体检不派子代理也可以在主对话做完——用脚本出底表，人只读归组后的结果和 RTL 的 always 块。

---

## 零、先定死的三条边界（每次 ECO 开工前过一遍）

| 边界 | 规则 | 为什么 |
|---|---|---|
| **只动叶子** | ECO 点位必须在 **flop 的 CK 脚**或**已有 ICG 的 E 脚**；禁止改任何时钟生成/分叉/MUX/CTS buffer | ECO 已是后期，动 tree 要重跑 CTS + 全树重签 |
| **网表改动必须 RTL 可表达** | 新加的 cell 只能是网表里已有的 wrapper（如 `CG_CELLX4_N`，内部是库 latch），**不用裸 latch**；命名 `u_gate_ICG_ECO_*` 蹭现有 dont_touch 规则 | 流程是"网表先行、RTL 跟上"，RTL 表达不了 = LEC 永远过不了 |
| **删 FF 只删模块内部负载** | 被删寄存器的负载若跨模块边界 → 标"需 RTL 先行"走反向流程（RTL 先改、重 DC、网表验证） | 跨层级摘 cell 一处漏接就是悬空 |

---

## 一、找点（四步：体检三方交叉 → 排序 → 网表底表 → RTL 扫描）

### ① DC 优化体检——三方交叉判定"DC 哪里没做好"（必做，先于一切）

**判据定义**：一个 flop 组算"DC 优化没做好"，必须**三条同时成立**——缺一条就不是 ECO 点：

| 维度 | 问什么 | 数据源 | 缺了会怎样 |
|---|---|---|---|
| **网表** | 这组 flop 的 CK 是不是裸挂，**且该时钟网源头没有被同 EN 门控** | 网表 grep + 时钟网溯源 | 只看叶子 → F 类误判（A1/A2 样板即此坑） |
| **报告** | 这个模块的 register 分量值多少钱（≥ 几百 µW 才值得） | PowerPro csv `;register;` 行 | 看不见 DC 做没做（RTL 级对 ICG 全盲，已证） |
| **RTL** | **为什么没门控**——DC 不敢（跨域/复位特殊/写法问题），还是语义上不该门控（同步器/每拍必刷的限定词） | RTL 源码 + 网表 D 端回溯 | **把"不该门控"误判成空白** |

**反例二（HK1V11 A1/A2 样板，2026-11-24 eco-output 发现）**：OUTPUT 的 PIX_DATA 组 25 flop、CONFIG 组 26 flop 叶子看是裸挂 `DCLK_DATA`/`DCLK_CONFIG`——但追到 CLKGEN（网表 621-628）：`DCLK_DATA = MUX(PIX_CLK_LONG, …)`，`PIX_CLK_LONG = CG_CELLX4_8(ENA=PIX_CLK_EN_LONG)`。**时钟网本身就是同一个 EN 门控后的输出**，叶子再串同 EN 的 ICG = 冗余，增量功耗 0，只多面积和一级延迟。miter 证"无条件等价"就是铁证——叶子 ICG 真改了行为不可能无条件等价。**规则：叶子裸挂 flop 的时钟网必须追到源头（CLKGEN / 上级 ICG 输出），若源头已有同 EN 的 ICG，判 F 类（冗余），跳过。**整网级排查：`DCLK_CONFIG`(69 裸挂)、`PIX_CLK`(258 裸挂) 这类以时钟网为单位的裸挂，先查该网的生成链再谈叶子。

**反例一（HK1V11 BUFFER_I）**：网表体检 84/84 裸挂（100%、零 ICG）——像是大空白；RTL 一看是 `INDATA_SYNC_D1/D2/D3` 20bit × 3 级**输入同步器链**，每拍必须采样，**门控即 bug**。只看网表会把它排进主战场。

#### ①-0 输入核对（先证明"网表对"）

- 取 DC 下**最新**的 `rep_dir`。目录 mtime 会被同步工具刷新，不作数；看网表头部的 `// Date`，确认 `.gv` 与 `.gv_org` 逐字节相同，md5 记进报告。
- 从 `dc.log` 摘出门控设置（`compile_ultra -gate_clock`、`set_clock_gating_style -minimum_bitwidth N -max_fanout M`、`set_clock_gating_check -setup/-hold`）。后面解释"DC 为什么没做"时要引用它们。
- RTL 与网表对代：比网表新的 RTL 标出差异范围；差异影响到寄存器结构的模块，用网表同代的 RTL（HK1V11 的 DECODE 就是这样）。

#### ①-a 全设计底表（脚本，1 秒）

```bash
python ~/.dsh/skills/power-clinic/scripts/build_tables.py <netlist.gv> --out <ECO_HEALTH 目录> \
       --powercsv <hier_pwr_detail.csv> --mods <模块关键字>
python ~/.dsh/skills/power-clinic/scripts/q.py flops.csv --where module=XXX --cols inst,ck,ck_cls,q_loads --head 40   # 查表
```

产出 `data/*.csv`：`flops.csv`（每个 flop 的 CK、时钟来源类别、D 锥叶子、Q 负载、死锥判定）、`icgs.csv`（每个 ICG 的 EN 源与 EN 锥门数）、`clk_genealogy.csv`（时钟网谱系）、`bare_groups.csv`（裸挂按寄存器名归组）、`redundant_candidates.csv`（死 / 重复 / 直通 / 常量 D）、`power_by_module.csv`（PowerPro 自身功耗）。

**先看 `clk_genealogy.csv`，再看模块表。** 叶子裸挂不等于没门控，时钟来源分五类：

| 时钟来源类别 | 含义 | 怎么对待 |
|---|---|---|
| GATED_LOCAL / GATED_UP | CK 已是 ICG 输出（本模块 / 父模块的 DC ICG） | DC 已做 |
| BARE_SRC_GATED | 叶子裸挂，但时钟每条路径都经过一个**模式级** ICG（如 DCLK_LE） | 该模式下时钟常开；细粒度 EN **不冗余**，按 D/E 类正常定性 |
| BARE_SRC_MIXED | 时钟经 MUX，只有部分支路有 ICG（如 DCLK_DATA） | 同 EN 的叶子 ICG 多半是 F 类，先查 EN |
| BARE_SRC_FREE | 时钟从顶层端口直通或取反，源头没有 ICG | **主战场** |

旧入口 `netlist_health.py` 只数叶子裸挂，会把"挂在父模块 ICG 输出上的 flop"和"挂在 DC 自动 ICG 输出 `n###` 上的 flop"两头漏计（HK1V11 报 1370，实为 1350）。新流程一律用 `build_tables.py`。

自己写 grep 时要避开的坑（脚本已处理）：实例会跨行，要按 `;` 切语句；`module` 关键字可能缩进；层级实例的输出脚要按子模块端口方向登记；单实例包装模块（库 wrapper、`CG_CELLX4_N`、`SNPS_CG_MOD_*`）先拍平，含 flop 的单实例模块保界；死寄存器判定要忽略回到自身的保持环，输出端口要追到父模块的负载；PowerPro csv 是"块头行 + 数据行"格式，模块自身功耗 = 父行减去直接子行。

#### ①-b 报告定价——四个场景一起看

对每个候选模块，从 PowerPro 取**四个场景**（两个速率 × 长码/短码，HK1V11 是 4G/3G × 420b/非 420b）的自身功耗：register（内部 / 翻转）、combinational、clock_network、total、占顶层比例。长码短码按哪一侧编码模块的寄存器在翻来判定。三个读数直接写进报告：

| 读数 | 含义 |
|---|---|
| 长码 ↔ 短码几乎不变 | 这部分功耗与模式无关，是常驻的 |
| 两个速率之比 ≈ 时钟频率比 | 功耗只随时钟频率变 → 是时钟脚功耗 |
| 翻转分量只占寄存器功耗的 1% 左右 | 99% 是时钟脚内部功耗：**flop 内容不翻也照样耗电**（HK1V11 的 ANCTL 78 个 flop 翻转 1 µW，却烧 850 µW） |

规则：register < 300 µW 的模块跳过；单 flop 代价用同频模块折算，并给出上下界（HK1V11：常开时钟的 85 个 flop =（模块寄存器功耗 − 已门控部分）/ 85，对照同频模块实测的 µW/flop）。还有一种要单独看的形态：**模块寄存器翻转≈0（时钟已关），组合功耗却随速率缩放**——这是时钟关着、组合锥被活输入带着空转，属于 G 类。

这一步产出的是"现状"表和定价推导，不是收益；收益定数靠 gate 级 PTPX。

#### ①-c RTL 定性（判"DC 为什么没做"——真正的判据）

对进入 ①-c 的模块，先看 `clk_genealogy.csv` 里它每条时钟网的生成链（是否经过 ICG、ENA 是谁、属于哪一类来源；要展开看用 `build_tables.py --debug MOD:NET`）——这张"时钟网谱系"是后面所有定性的前提。然后把裸挂 flop 按**寄存器名**归组（`bare_groups.csv` 已按 `_reg[N]_` 去掉位号聚类），每组回 RTL 找对应的 always 块，归入七类：

| RTL 定性 | 特征 | 判定 | 处置 |
|---|---|---|---|
| **A. 同步器/重同步链** | `_SYNC`/`_D1/_D2/_D3` 后缀，D 直连上一级 Q，无使能 | **不该门控**（门控即丢数据） | 跳过 |
| **B. 每拍必刷的协议限定词** | `dvld`/`last`/`start`/`valid` 类 1bit，无条件赋值 | **不该门控** | 跳过 |
| **C. 单 bit 控制位** | 状态机标志、配置位 | DC 不划算 | 跳过（<5 µW） |
| **D. DC 不敢——跨域采样** | 跨域重同步的**末级**，D 直连源域信号，有同源/同步 EN 可用 | **DC 没做好** | (a) 叶子级 ICG |
| **E. DC 不敢——写法问题** | RTL 无条件写 `q <= d`，但数据实际有静止窗；EN 在 RTL 里现成 → 加 ICG；EN 要新综合 → **需 RTL 先行** | **DC 没做好** | (a) / RTL 先行 |
| **F. 时钟网源头已门控** | 叶子 CK 裸挂 `DCLK_x`，但 `DCLK_x` 在 CLKGEN 已是**同 EN** 的 ICG 输出（追 `.CG_CLK`/`.O` 驱动链） | **叶子 ICG 冗余** | 跳过；若要省，换**更紧的 EN**（源寄存器更新窗口），且注意独立 beat 的信号要分组 |
| **G. 时钟已关、组合空转** | 模块寄存器翻转≈0（时钟被模式位关掉），组合功耗却随速率缩放；网表里从活输入端口出发能碰到大部分组合门（`build_tables.py --live MOD:端口,端口`） | **DC 没做好**（纯组合 operand isolation 从不被 DC 自动插） | 组合隔离（RTL 先行）：用决定"结果采不采"的那个信号把活输入钳 0，条件与消费条件是同一个信号才安全 |

**产出**：`ECO_HEALTH.md`——每个候选模块一段：四场景功耗 / 网表数字 / 定价推导 / 裸挂 flop 按名归组表 / 每组 RTL 定性（A~G）/ 行号 / **结论（跳过 / 进入 ECO_CANDIDATES）**。

**只有 D/E/G 三类进 ECO 候选清单。A/B/C/F 四类必须显式列出并标跳过理由**——证明看过、不是漏了。

**同时体检 DC 自门控的代价**（判据④的输入）：对已有 ICG 回溯 EN 锥门数（`grep "\.O(EN_NET)"` 追驱动链），>50 门的标记为"改接 EN 候选"。

### ② 报告定位——多候选间排先后

①-b 已用报告定了价，这一步只对**对比型报告**补 long/short 差值确认（结构性溢价 vs 空转残留），给 ①-c 产出的多个 D/E 候选排优先级。**单份报告时此步可省。**

### ③ 网表底表——候选模块的裸挂 flop 与 EN 回溯

对候选模块段（网表里 `module <top>_<MOD>_0 (` 到 `endmodule`）。底表已经由 `build_tables.py` 给出（`flops.csv` / `bare_groups.csv` / `icgs.csv`，用 `q.py` 查），下面的 grep 只在要手工复核某一行时用：

```bash
# 裸挂 flop 按 CK 分组（CK 直连时钟网而非 ENCLK = 没被门控）
sed -n "${S},${E}p" $N | grep -E "DFF[A-Z0-9]*\s+\S+\s*\(" | grep -oE "\.CK\([^)]+\)" | sort | uniq -c
# 列出裸挂 flop 名
sed -n "${S},${E}p" $N | grep "\.CK(DCLK_DATA)" | grep -oE "\s\S+_reg\S*\s*\(" | sort
# 已有 ICG 的 EN 回溯（EN 网由谁驱动，多少门）
grep -n "\.O(EN_NET)\|\.Y(EN_NET)" $N
```

**DC 不敢做的四类判据**（自带做/不做初筛）：

| 类型 | 网表特征 | RTL 根源 | 处置 |
|---|---|---|---|
| ① 跨域采样 | `_ASYNC` 对：源域 flop → 目标域 flop，D 直连，CK 裸挂目标时钟 | 跨时钟域重同步，DC 不提取使能（不敢假设源有效） | **加 ICG + 同源 EN**（主战场） |
| ② 单 bit 控制位 | 1bit，CK 裸挂，DCLK 域 | 状态机标志位 | **跳过**（DC 不插 ICG 不划算，<5 µW） |
| ③ 特殊复位 | `DFFSBQ`（set 型）/ `DFFRBQBX`（反相） | 复位值非 0 | 可加，**复位行为要审**（复位期间 EN 是几） |
| ④ 使能锥太贵 | 有 ICG，但 EN 锥几十~几百门 | DC 自门控的自检测逻辑 | 改接 EN（占位） |

**时钟域检查（每个 ECO 必做）**：
- **L1 域关系**：EN 信号在哪个时钟域？被门控 flop 在哪个域？查 SDC 的 `create_generated_clock` 链——同源（如 DCLK 和 DCLK_DATA 都是 RX_CLK 分支）= 同步，PT gating check 覆盖；真异步（OSC_CLK/I2C_CLK → DCLK）= 需同步器，否则 runt
- **L2 marker**：`_ASYNC` 后缀、跨域寄存器对——这是"DC 不敢碰"的路标，也是 ECO 富矿

### ④ RTL 扫描——"写得烂导致 FF 多"的四形态

| 形态 | RTL 特征 | 删法 | 级别 | 第一版 |
|---|---|---|---|---|
| **死寄存器** | Q 无负载 / 只喂死锥（输出网无人用） | 摘 | L2 | ✅ |
| **重复状态** | 两寄存器同 D、同 CK、同复位 → 永远同值 | 合并保留一个 | L2 | ✅ |
| 冗余流水级 | 直通寄存器（D 直连上游 Q，无逻辑） | 删、输出前移一拍 | **L3 重定时** | 占位 |
| 宽寄存器存窄数据 | 26bit shifter 实际只用 21bit | 截位宽 | 需审 | 占位 |

死锥判法见 `netlist-metal-eco` §一（有负载 ≠ 活络，要追到锥尾）。

### 产出：`ECO_HEALTH.md`（①-c，三方交叉体检）+ `ECO_CANDIDATES.md`（③④ 后，只含 D/E 类）

```markdown
| # | 目标组 | 网表行号/实例 | CK 来源 | 候选 EN（名/域/复位值） | DC 为何没做 | 类型 | 预估收益 | 风险 | 时钟域 L1 | 做? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PIX_DATA[23:0]+START_DLY | OUTPUT段 :443-458, 25 flop | DCLK_DATA 裸挂 | PIX_CLK_EN / DCLK / set复位=1 | 跨域采样① | (a) | 40~105 | EN跨域, PT gating check | 同源同步 | ✅ 用户采纳 |
| 2 | CONFIG_DATA 等 25 flop | 同段 :461-470 | DCLK_CONFIG 裸挂 | CONFIG_CLK_EN / DCLK / set复位=1 | 跨域采样① | (a) | 含上 | 行为变更: EN=0 期间保持 | 同源同步 | 待用户确认 |
| 3 | 13 个控制位 | OUTPUT段 | DCLK 裸挂 | — | 单bit② | 跳过 | <5 | — | — | ❌ |
```

**用户在此表上拍板**：做哪几行、删 FF 的删不删。agent 只摆候选和证据，不替用户定设计决策。

---

## 二、改网表（类型 a：叶子级 ICG）

### 改法（照抄网表现有 wrapper）

```
改前：DCLK_DATA ──CTS──┬─→ PIX_DATA_reg_0_.CK   （25 个 flop 裸挂）
                      └─→ ...

改后：DCLK_DATA ──CTS──┴─→ u_gate_ICG_ECO_PIX_DATA.CLKIN
                              .ENA(PIX_CLK_EN)  ← 现成信号
                              .SCAN_EN(1'b0)
                              .CG_CLK ─→ 25 个 flop 的 .CK（局部短线）
```

步骤：
1. **另存** `rep_dir/<top>_eco.gv`，**绝不覆盖** `rep_dir/<top>.gv`（它是 LEC 的 `-rev` 基准和下次综合输入）
2. 在目标模块段加 wrapper 实例，**格式照抄网表里已有的** `HK1V11_digital_top_CG_CELLX4_N`（N 取未用编号）：
   ```verilog
   HK1V11_digital_top_CG_CELLX4_<N> u_gate_ICG_ECO_<GRP> ( .CLKIN(DCLK_DATA),
         .ENA(PIX_CLK_EN), .SCAN_EN(1'b0), .CG_CLK(ECG_<GRP>) );
   ```
3. 把该组所有 flop 的 `.CK(DCLK_DATA)` 改成 `.CK(ECG_<GRP>)`——**只改 CK 引脚，D/RB/Q 一根不动**
4. 一个 flop 组一个 ICG（skew 一致、面积省）；不同时钟域/不同 EN 的组各自一个
5. `TE`/`SCAN_EN` 接 `1'b0` 跟网表现有 148 个一致

**自检**（改完立刻跑）：
- `grep -c "\.CK(ECG_<GRP>)"` = flop 数；原时钟网上这些 flop 数归零
- `iverilog -tnull` 网表能编译（无悬空/重复驱动）
- 新 ICG 的 ENA 网在网表里有驱动（`grep "\.O(PIX_CLK_EN)\|PIX_CLK_EN_reg"`）

### 删冗余寄存器（类型 e，第一版只做死寄存器/重复状态）

1. 死寄存器：确认 Q 负载为 0 或全喂死锥 → 摘 `DFF..._reg_ (` 整行 → 若有 `assign` 引用其 Q 也摘
2. 重复状态：A/B 同 D 同 CK 同复位 → 保留 A，把 B 的所有负载 `.D(B_Q)` 改接 `.D(A_Q)` → 摘 B
3. **只删模块内部负载**；负载跨 `module` 边界 → 停手，标"需 RTL 先行"
4. 自检：`iverilog -tnull` + 重复状态类的 miter（下节）

---

## 三、三道证据（缺一不可交付）

### 证据 1：Yosys miter（RTL 跟之前，本机可做）

改前网表 vs 改后网表，**限定等价**：
- EN=1 时：输出逐拍等价（门控透明）
- EN=0 时：改后 flop 保持、改前 flop 跟随——**这是设计意图，不是 bug**，miter 要 qualify（把 EN=0 拍的比较屏蔽，或证"EN=0 期间源数据不变"）

```bash
# 网表级 miter 骨架（库 cell 要有 behavioral stub，或只对目标模块段做）
yosys -p "read_verilog -lib cells_stub.v; read_verilog before.v; rename MOD gold; \
  read_verilog after.v; rename MOD dut; proc; async2sync; memory_map; \
  miter -equiv -flatten -make_assert gold dut m; hierarchy -top m; \
  sat -verify -prove-asserts -set-init-zero -seq 20"
```

### 证据 2：LEC（RTL 跟上后）

- 用户改 RTL：目标组 always 块加 `if (EN) q <= d;`（**不手插 ICG**，让 DC 推断；或显式例化 `CG_CELLX4` 与网表一一对应——两种方式 LEC 都能对上，但必须和网表改法同一种）
- 新建 `lec_power_eco/` 变体（照 `lec_upf/` 结构）：golden = RTL（`.sv.f`/`.f`），revised = `<top>_eco.gv`
- **服务器上建**，本地写好 `.do` 待同步；不要动主流程的 `.gv_org`

### 证据 3：case

- 跑改动模块相关的 case（HK1V11：420b 长码主 case + 改动模块单测）
- 通过标准：功能 pass，波形比对零差（EN=0 期间的保持值不计入比对）
- **功耗数字不是通过门槛**（用户跑 PTPX 作记录）

### 通过 = LEC + case；miter 是 RTL 跟之前的预证据。

---

## 四、落位、记录、闸门

| 项 | 规则 |
|---|---|
| 产物目录 | `内部分享/power_saving/<date>/ECO_<name>/`：`<top>_eco.gv` + `eco.diff` + `ECO_RECORD.md` + `miter/` + LEC 日志 + case 结果。**不进 SYNTHESIS/**（overlay 校验管着的服务器同步目录） |
| `ECO_RECORD.md` | 每个 ECO 一段：目标组 / 网表改动（实例名/行号/前后）/ EN 信号与域 / 时钟域 L1 结论 / DFT 行（固定："新增 ICG N 个，TE=1'b0，DFT 插 scan 需确认 TE 可控"）/ 三道证据路径 / 对应 RTL 改动（文件:行） |
| 闸门 | RTL 改动按 **L2** 走（`rtl-code-review` + preflight）；网表证据（miter + LEC + case）作 L2 评审附件 |
| 变更记录 | `修改记录/CHANGES.md` 登记（AGENTS.md §3.1 强制） |
| 文件尾签名 | 按 AGENTS.md §8 规则 |

---

## 五、HK1V11 实证（2026-11-20~24）

- **全设计 DC 体检（2026-11-24，`scripts/build_tables.py`）**：2921 flop，**已门控 1571（54%）/ 裸挂 1350**（源头有模式级 ICG 804 / 混合 166 / 完全自由 280）；ICG 163 = DC 自动 148 + 手写 15。逐模块裸挂：**LONG_ALIGN 172/212（81%）** > DPLC_DATA_GEN 160/256（62%）> SHORT_OUTPUT 146/226 > SHORT_ALIGN 126/146（86%）> DTCTL 115/172 > CHPI_SD_CTRL 85 > **BUFFER_I 84/84（100%，零 ICG）** > SHORT_DECODE 75 > LONG_DECODE 71 > LONG_OUTPUT 65/276（24%）> LC_CPUWR 4/518（1%）。裸挂按时钟网：DCLK 566 / **PIX_CLK 258**（DPLC_DATA_GEN 主时钟）/ CLKIN_I 80 / DCLK_DATA 77 / DCLK_INV 76 / DCLK_CONFIG 69。网表入口显示 ALIGN 最大，**但裸挂多 ≠ DC 没做好**：BUFFER_I 84/84 裸挂经 RTL 定性是输入同步器链（A 类，门控即 bug），必须跳过——这就是体检要三方交叉、不能只看网表的理由。round2 盯 ALIGN 组合逻辑半月未数 flop 覆盖率，则说明只看报告同样不够。
- **六个模块体检完的结果（2026-11-24，issue 2）**：裸挂最多的 ALIGN 172 个里 120 个是 G13 为修 setup 加的自由流水打拍、OUTPUT 51 个是跨域采样（F 类）、BUFFER_I 84 个是输入同步器/抽头（A 类）——真正 DC 没做好的只有五条：S-1 CHPI_SD_CTRL 四条 16 拍延迟线自使能门控（64 flop 挂在永不关的 `DCLK_INV` 上，≈1.0～1.25 mW@4G，位精确等价，issue 3）、P-1 DPLC 标定乘加锥组合隔离（时钟关着组合仍烧 1172 µW，G 类，issue 4）、D-1 DECODE `rx_shifter[9:4]` 的 CK 改接 DC 已生成的门控时钟 `n654`（6 flop，零新综合）、T-1 DTCTL 输出通路半速率门控（72 flop，需时序复核）、A-1 ALIGN `LONG_DEC_CNT` 用现成 `LONG_DEC_ACTIVE`（5 flop）。另有 30 个可删的冗余 flop（DPLC 24、DTCTL 2、SD_CTRL 3、DECODE 1）
- **时钟网谱系的更正**：长编码三模块的 `DCLK` 是 CLKGEN `u_gate_ICG_DCLK_LE` 的输出（EN=`~SP`，模式级），不是 `I_CLKIN` 直通——直通的是 CHPI_SD_CTRL 的 `DCLK`，取反直通的是 `DCLK_INV`。CHPI_SD_CTRL 的 `TP_WIDTH_CNT0` 9 个 flop 由父模块 LINK_LOGIC 的 DC ICG 门控（GATED_UP）
- **"行内其余时间全是 0、没有翻转"也要门控**：功耗在时钟脚不在数据（同一报告里 ANCTL 78 个 flop 翻转 1 µW 却烧 850 µW）。加的组合逻辑只是生成使能，是成本；真正省的是 ICG 停掉的 64 个寄存器时钟脚。D 端做隔离对它无效，时钟源头门控属树级改动不做（issue 3 的问答）
- **DC 抢跑只有两形态**：写使能→CG、常量等式压缩。纯组合 operand isolation 从不被抢，被吃的是收益分母——µW 推算先取 csv comb 分项
- **RTL 级 PowerPro 对 DC 的 148 个 ICG 全盲**：RTL 级数字只判 switching 方向，不作收益定数（HK1V11 实测：C3 RTL 级 +7 µW，L47 switching −28.65 是真信号，internal +27.67 是反馈 mux 罚分）
- 叶子级 ICG 的 CTS 副作用：新 ICG 让目标 flop 多一级 cell delay（100~200 ps），CTS 做 skew 平衡时可能给同域其他 flop 补 delay——工具自动行为，不是改 tree
- 时钟域 L1 实例：`PIX_CLK_EN`（DCLK 域）门控 `PIX_DATA`（DCLK_DATA 域）——网表谱系：DCLK = I_CLKIN→ICG（DCLK_LE），DCLK_DATA = I_CLKIN→ICG(PIX_CLK_EN_LONG)→MUX，两者同出 `I_CLKIN`，**同源同步**，PT gating check 覆盖，不需同步器。（旧写法"DCLK = I_CLKIN 直通"只对 CHPI_SD_CTRL 的 DCLK 成立。）

### 首个样板 ECO_A1_pix_clk_en 跑出的四条规则（2026-11-23）——注意：A1 本身已被 F 类判定为 0 收益，这四条是流程规则，不是收益背书

样板目录：`HK1V11/内部分享/power_saving/20261119/ECO_A1_pix_clk_en/`（ECO_CANDIDATES / apply_eco.py / eco.diff / ECO_RECORD / miter）。

1. **网表改写必须二进制读写**：DC 网表是 `\n` 行尾；Python `read_text`/`write_text` 在 Windows 会转成 `\r\n`，diff 从 +11 行膨胀到 53207 行（每行都"变"）。用 `read_bytes().decode()` / `write_bytes()`。另存后必查 `diff | grep -c "^[<>]"` 与预期行数一致。
2. **用带断言的脚本改，不手改**：`apply_eco.py` 每步计数断言（目标 flop 数=25、CK 改写数=25、ICG 实例数=1）。首跑就拦住一个 bug（`m in targets` 用 Match 对象做成员判断恒 False → 改写数 0 ≠ 25 → `die`）。
3. **带 ICG 的 flop 组，复位期间 EN 的值决定复位能否落地**：Verilog 异步复位只在 RSTN **下降沿**触发；TB 若 RSTN 初始即 0，复位分支不执行、经 ICG 的 flop（EN=0 时无时钟沿）复位后为 X。真实芯片上电复位有下降沿不受影响，但它是判据③（特殊复位）的具体形态：**EN 复位值必须为 1，或复位必须独立于门控时钟**。ECO_A1 的 `PIX_CLK_EN` 是 set 型（复位值=1），安全。TB 要建模真实复位序列（1→0→1）。
4. **miter 的正确抽象层是 ECO 语义，不是整个模块**：OUTPUT 段用 ~75 种库 cell，逐个写 stub 不现实且引入误差；ECO 只改 CK 来源，所以 miter 只建模「ICG latch + 被门控 flop」，证 **限定等价**（EN 稳定时逐 bit 相等），整模块等价交给 LEC。SAT 用 `sat -prove bad_q 1'b0 -tempinduct`，`bad_q` 要提升为 output 端口（flatten 后内部 wire 名会变）。qualify 要屏蔽 EN 0→1 后第一拍（gold 在 EN=0 期间跟随 D、dut 保持，对齐要一拍）。

### miter 骨架（ECO_A1 可直接复用）

```verilog
// 库 ICG 行为模型（latch-based，低电平锁存 EN）
module GCKHBQX4AL9 (CK, E, TE, Q); input CK,E,TE; output Q; reg latch;
  always @(*) if (!CK) latch <= TE | E;  assign Q = CK & latch;  endmodule
// bad = EN & (q_gold != q_dut) & en_d（en_d = EN 上一拍；屏蔽 EN 0→1 第一拍）
// yosys: read; hierarchy -top bad_top; flatten; proc; async2sync; sat -prove bad_q 1'b0 -tempinduct -seq 12 -set-init-zero
```

## 六、报告怎么写、issue 怎么发（模板 = HK1V11 的 issue 2、3、4）

ymzhu 2026-11-24 定的规矩：**体检的产出直接写成 GitHub issue**，一条大候选一张票。模板在 HK1V11 仓库的 issue 里（全部票：https://github.com/ymzhuuuuufz0313l/HK1V11/issues ）：

| 模板 | 地址 | 学什么 |
|---|---|---|
| 体检总表 | https://github.com/ymzhuuuuufz0313l/HK1V11/issues/2 | 结论一屏怎么排；哪些模块要明确写"不是 DC 没做好"；口径更正、待拍板、范围外观察怎么列 |
| 单条候选 · 门控类 | https://github.com/ymzhuuuuufz0313l/HK1V11/issues/3 | 八节结构；"行里其余时间全是 0 为什么要门控"的问答；用现有 cell 演示改前改后 |
| 单条候选 · 组合隔离类 | https://github.com/ymzhuuuuufz0313l/HK1V11/issues/4 | 时钟已关但组合空转怎么定价；隔离条件为什么必须等于消费条件 |

发新票之前先把这三张读一遍（`gh issue view 3 -R ymzhuuuuufz0313l/HK1V11 --json body -q .body`），照着它们的节次和口吻写。这三张会随问答继续演进，以线上版为准；下面的八节表只是摘要。发票用 deck 工具：先 `deck_context`，再 `deck_issue_create`；用户提问用 `deck_issue_patch` 记原话和回答。

### 总表票（模板：issue 2）

输入核对（网表 md5、DC 设置、RTL 对代）/ 结论一屏（排序表：候选、模块、类型、预估、把握）/ 明确不是 DC 没做好的模块及理由 / 口径更正 / 待拍板问题 / 范围外观察 / 产物路径。

### 单条候选票（模板：issue 3、issue 4）——八节，顺序固定

| 节 | 写什么 | 要点 |
|---|---|---|
| 1 现状：四个场景各烧多少 | 四场景功耗表、三个读数、这一块怎么定价、**现在的代码（改前）** | 改前代码由脚本按行号从 RTL 取，不手抄；读的人要能和第 3 节左右对照 |
| 2 什么导致了什么 | 三列表：事实 → 出处 → 导致 | 每条事实带网表行号或 RTL 行号 |
| 3 怎么改 | 网表先行 / RTL 先行；给落地方式 A、B | 用现有网表里已有的 cell 演示改前改后，说明动的是哪一层（叶子 ICG 不动时钟树） |
| 4 为什么正确 | 归纳证明 + 机器证据表 | 写明是位精确等价还是限定等价，限定条件是什么 |
| 5 好处 | 四场景净省表、占顶层比例、代价 | 估算和实测分开写，估算要给出假设 |
| 6 风险 | 编号表：风险 / 说明 / 处置 | 输出时序、EN 自参考、LEC 形态、DFT、待鉴别的数字都要过一遍 |
| 7 验证与定数计划 | 五道关：模型级证明、DC 后查结构、LEC、case 对拍、PT | 每关给通过标准 |
| 8 关联 | 上游票、相关 skill | |

第 1 节回答"值不值得做"，第 2～4 节回答"为什么是这样、为什么改了是对的"，第 5～6 节回答"能得到什么、要担什么"。每节第一句就是结论。

### 问答也进票

用户对某张票提问时：问题原话一字不改记进"维护者原话"（`deck_issue_patch originalWords`），回答写成票下的评论；问答改变了票里的结论，就同步把正文改掉。回答先给结论（"对，这是该条件下唯一的写法"），再把预期落差说在前面（比如"综合后网表变了，CTS 流程照常要重跑"）。

### issue 排版（ymzhu 的阅读体验要求，硬规则）

- 行内代码体（反引号）不用；特殊名称用斜体。
- 范围不写半角波浪号：GitHub 把成对的半角波浪号当删除线，整段会被划掉。范围写全角"～"或"约"。
- 代码段放引用块（GitHub 的引用文字是淡灰色正常字体），缩进用 `&nbsp;` 保留。
- 发出前用 `python scripts/issue_plain.py check <票号>` 让 GitHub 的渲染接口核对，删除线、代码体、代码块都是 0 才算过（脚本里的 REPO 常量按项目改）。
- 表格优先，长解释少写。

### 模型级证明的现成骨架

- 自使能移位线（issue 3）：HK1V11 `内部分享/power_saving/20261119/ECO_HEALTH/s1_proof/`——Yosys `sat -prove bad_q 1'b0 -tempinduct -seq 12 -set-init-zero`；非空洞对照（去掉"链内非零"项）应当 FAIL；iverilog 用真 latch 型 ICG、真时钟沿、复位 1→0→1 做动态对拍。
- 只改 CK 来源的叶子 ICG（C2、D-1 这类）：`…/ECO_C2_decode_out_hold/miter/`。

## 七、相关 skill

- `netlist-metal-eco`：金属层 ECO（base 冻结只改走线）；本 skill 的死锥判法来自它
- `digital-backend-pitfalls`：ICG 复位两大坑、cell 引用稳定性
- `hk1v11-delivery-gate`：RTL 侧 L2 闸门
- `rtl-code-review` / `rtl-signal-trace`：RTL 跟上后的评审
- `local-simulation`：Yosys miter 的本机环境
<!-- ymzhu 2026-11-24 17:05 -->
