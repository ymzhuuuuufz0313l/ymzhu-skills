---
name: power-eco
description: DC 后网表（pre-APR）功耗 ECO 工作流——从 PowerPro 报告对比定位高功耗模块，结合网表（裸挂 flop 底表 + EN 回溯）与 RTL（DC 不敢优化的写法、冗余 FF）找 ECO 点，网表先行改（叶子级 ICG / 删冗余寄存器，CTS 树不动），RTL 同步跟上，Yosys miter + LEC + case 三道证据闭环。与 netlist-metal-eco（金属层）互补；树级时钟改动、架构重构、PTPX 不在范围。触发词：功耗 ECO、power eco、网表加 ICG、DC 后网表改门控、哪里 DC 不敢优化、裸挂 flop、跨域寄存器、冗余 FF、删寄存器、网表先行、ECO 候选清单、DC 抢跑、PIX_CLK_EN。
---

# power-eco — DC 后网表功耗 ECO：找点 → 网表先行 → RTL 跟上 → 三道证据

## 何时用

- **DC 综合后、APR 前**的网表功耗 ECO：有 `rep_dir/<top>.gv`、对应 RTL、PowerPro csv，想在不重跑综合的前提下让功耗降一点。
- **用户指定模块**（"我想做 LONG_ENCODING_OUTPUT"）或**只有单份功耗报告**时，按本 skill 找点。
- **DC 已经自动做了大部分**（HK1V11 实测：148 个自动 ICG、76% flop 已门控）——剩下的都是 DC **不敢做**的，本 skill 的核心就是找出"为什么不敢"并在网表上补刀。

**不适用**（走别的路）：
- base 层冻结只改走线 → `netlist-metal-eco`
- 要改时钟树结构（CLKGEN 根部加分叉、改 MUX、重分叉）→ 本 skill **明确剔除**，ECO 阶段动 tree 代价太大
- 架构重构（串行化、资源共享、协议改动）→ 走 RTL 改完重新 DC
- 门级功耗定数 → 用户跑 PTPX，本 skill 不碰

---

## 零、先定死的三条边界（每次 ECO 开工前过一遍）

| 边界 | 规则 | 为什么 |
|---|---|---|
| **只动叶子** | ECO 点位必须在 **flop 的 CK 脚**或**已有 ICG 的 E 脚**；禁止改任何时钟生成/分叉/MUX/CTS buffer | ECO 已是后期，动 tree 要重跑 CTS + 全树重签 |
| **网表改动必须 RTL 可表达** | 新加的 cell 只能是网表里已有的 wrapper（如 `CG_CELLX4_N`，内部是库 latch），**不用裸 latch**；命名 `u_gate_ICG_ECO_*` 蹭现有 dont_touch 规则 | 流程是"网表先行、RTL 跟上"，RTL 表达不了 = LEC 永远过不了 |
| **删 FF 只删模块内部负载** | 被删寄存器的负载若跨模块边界 → 标"需 RTL 先行"走反向流程（RTL 先改、重 DC、网表验证） | 跨层级摘 cell 一处漏接就是悬空 |

---

## 一、找点（三步，产出 ECO 候选清单）

### ① 报告定位——先定模块，再进网表

**对比型报告**（long/short 两份 csv、mode A/B）：逐模块对比

| 模块 | 模式 A | 模式 B | Δ | register 占比 | 判断 |
|---|---:|---:|---:|---|---|
| LONG_ALIGN | 6136 | SHORT 2917 | +3219 | 74.7% | register 主导，看 ICG 空白 |
| LONG_DECODE | 4668 | SHORT 1688 | +2980 | — | 同上 |

差值大的模块直接锁定（HK1V11 用这法子定出了 OUTPUT/ALIGN/DECODE 三块）。

**单份报告**：按 total 排 top-N（默认 5），每行带 register/comb/clk 三分账 + **可动性初判**，**列给用户、由用户指定**：

| 可动性初判 | 含义 | 对应 ECO 类型 |
|---|---|---|
| register 主导 + 网表有裸挂 | DC 没做，有空子 | (a) 叶子级 ICG |
| register 主导 + 网表已门控 | DC 做过了 | 低优先，看 EN 锥贵不贵 |
| comb 主导 | 组合翻转 | 删 FF / 组合（占位） |
| total 小（<500 µW） | 池子小 | 跳过 |

### ② 网表底表——候选模块的裸挂 flop 与 EN 回溯

对候选模块段（网表里 `module <top>_<MOD>_0 (` 到 `endmodule`）：

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

### ③ RTL 扫描——"写得烂导致 FF 多"的四形态

| 形态 | RTL 特征 | 删法 | 级别 | 第一版 |
|---|---|---|---|---|
| **死寄存器** | Q 无负载 / 只喂死锥（输出网无人用） | 摘 | L2 | ✅ |
| **重复状态** | 两寄存器同 D、同 CK、同复位 → 永远同值 | 合并保留一个 | L2 | ✅ |
| 冗余流水级 | 直通寄存器（D 直连上游 Q，无逻辑） | 删、输出前移一拍 | **L3 重定时** | 占位 |
| 宽寄存器存窄数据 | 26bit shifter 实际只用 21bit | 截位宽 | 需审 | 占位 |

死锥判法见 `netlist-metal-eco` §一（有负载 ≠ 活络，要追到锥尾）。

### 产出：`ECO_CANDIDATES.md`

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
| 产物目录 | `power_saving/<date>/ECO_<name>/`：`<top>_eco.gv` + `eco.diff` + `ECO_RECORD.md` + `miter/` + LEC 日志 + case 结果。**不进 SYNTHESIS/**（overlay 校验管着的服务器同步目录） |
| `ECO_RECORD.md` | 每个 ECO 一段：目标组 / 网表改动（实例名/行号/前后）/ EN 信号与域 / 时钟域 L1 结论 / DFT 行（固定："新增 ICG N 个，TE=1'b0，DFT 插 scan 需确认 TE 可控"）/ 三道证据路径 / 对应 RTL 改动（文件:行） |
| 闸门 | RTL 改动按 **L2** 走（`rtl-code-review` + preflight）；网表证据（miter + LEC + case）作 L2 评审附件 |
| 变更记录 | `修改记录/CHANGES.md` 登记（AGENTS.md §3.1 强制） |
| 文件尾签名 | 按 AGENTS.md §8 规则 |

---

## 五、HK1V11 实证（2026-11-20~23）

- 全设计裸挂 flop 底表：DCLK 554 / DCLK_DATA 74 / DCLK_CONFIG 68 / OSC_CLK 59 / DCLK_INV 56 / SD_CLK_INV 26 —— 约 845 个，DC 自动 ICG 覆盖 148 个（76%）
- **DC 抢跑只有两形态**：写使能→CG、常量等式压缩。纯组合 operand isolation 从不被抢，被吃的是收益分母——µW 推算先取 csv comb 分项
- **RTL 级 PowerPro 对 DC 的 148 个 ICG 全盲**：RTL 级数字只判 switching 方向，不作收益定数（HK1V11 实测：C3 RTL 级 +7 µW，L47 switching −28.65 是真信号，internal +27.67 是反馈 mux 罚分）
- 叶子级 ICG 的 CTS 副作用：新 ICG 让目标 flop 多一级 cell delay（100~200 ps），CTS 做 skew 平衡时可能给同域其他 flop 补 delay——工具自动行为，不是改 tree
- 时钟域 L1 实例：`PIX_CLK_EN`（DCLK 域）门控 `PIX_DATA`（DCLK_DATA 域）——SDC 查得 DCLK = I_CLKIN 直通、DCLK_DATA = I_CLKIN→ICG→MUX，**同源同步**，PT gating check 覆盖，不需同步器

### 首个样板 ECO_A1_pix_clk_en 跑出的三条规则（2026-11-23）

样板目录：`HK1V11/power_saving/20261119/ECO_A1_pix_clk_en/`（ECO_CANDIDATES / apply_eco.py / eco.diff / ECO_RECORD / miter）。

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

## 六、相关 skill

- `netlist-metal-eco`：金属层 ECO（base 冻结只改走线）；本 skill 的死锥判法来自它
- `digital-backend-pitfalls`：ICG 复位两大坑、cell 引用稳定性
- `hk1v11-delivery-gate`：RTL 侧 L2 闸门
- `rtl-code-review` / `rtl-signal-trace`：RTL 跟上后的评审
- `local-simulation`：Yosys miter 的本机环境

<!-- ymzhu 2026-11-23 14:40 -->
