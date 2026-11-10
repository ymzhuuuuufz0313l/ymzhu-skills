---
name: subagent-dispatch
description: 派发/拆分 subagent 前的模型选择与确认协议。触发词："分发 subagent"、"拆分 subagent"、"派子代理"、"启动子代理"、"并行子代理"、"delegate subagent"、"spawn subagent"。凡准备用 subagent/subagent_fork/agent_teams 成员分派任务前都应先载入本 skill。
disable-model-invocation: false
---

# Subagent 派发协议（模型分工 + 确认）

派发子代理前，按下面的分工选模型，并在需要时先让用户确认，再派。
本策略针对**本桌面已授权的子代理模型**（见 DSH 设置「Subagent」页）。

## 模型分工（本桌面已授权）

| 模型 | 定位（2026-09-30 用户策略） |
|---|---|
| GLM-5.3 / GLM-5.3-flash / GLM-5.3-flashx | **默认主力**：已开 GLM 高级别套餐，一切派发优先 GLM 系（高强度用 GLM-5.3；快/大规模用 flash；不确定就直派继承当前路由） |
| DeepSeek（xxw/DeepSeek） | **xxw 首选**：xxw provider 下的 DeepSeek 模型（baseURL 172.16.185.4:3000/v1）。**多 subagent 时，xxw 提供的模型（Qwen / DeepSeek）里 DeepSeek 接通就优先用 xxw/DeepSeek**；仅 xxw/DeepSeek 不可用（API 报错/超时/不接通）才 fallback 到 xxw/Qwen。⚠️ 需 subagent `allowedModels` 显式含 `xxw/DeepSeek`（2026-11-06 已加进 `profiles/desktop/cordis.patch.yml`；显式 `provider+model` 可绕过 catalog 热加载，不重启即用）。 |
| Qwen（xxw/Qwen） | **xxw fallback**：⚠️ 仅 256K 上下文的小模型，xxw/DeepSeek 不可用时的兜底。派发输入必须精简：prompt 紧凑自包含（目标 + 必要文件路径），让 Qwen 自己去读文件，绝不内联大段文件内容、长背景或长输出 |

**实测事实（2026-09-29/30）**：`subagent` 支持 `provider`/`model` 跨模型覆盖（Qwen / GLM-5.3 均实测通过）。同模型同任务对比：subagent 与 agent-teams 成员产出质量相当，subagent 更快、机制更轻。**默认用 subagent，不建 agent-teams 队**（除非用户明确要求团队模式）。agent-teams 插件自桌面 0.2.0-rc.2 起全功能正常（2026-10-04 实测：建队/调度/任务板/成员执行/完成报告全链路通过），用户点名团队模式时直接用。

**Qwen 接入坑（2026-10-28 实测排障）**：ZCode 对所有 anthropic-messages 格式的自定义供应商，内置推理映射是 GLM 专有格式——`thinking: {"type":"adaptive"}` + `output_config: {"effort":...}`。**Qwen 走 new-api 网关时这两个字段各答自触发 400 invalid_request**，症状是子代理请求被随机拒（N 路并发挂 1~2 路、换子代理也复发、重试无效）。修复：在 provider_config.json 的 Qwen 模型条目 optionSpecs 里写入兼容映射（已固化）：`reasoningLevel == "disabled" ? {"thinking":{"type":"disabled"}} : {"thinking":{"type":"enabled","budget_tokens":8192}}`。⚠️ 若在 UI 里重开「智能配置」或重存模型配置，此覆盖会被内置映射覆盖回去，需重写。排障方法：ZCode 配置热重载（改 provider_config.json 立即生效），可指向本地日志代理抓真实请求字节，再用原始字节重放 + 逐字段二分定位。

## 派发协议

1. **选模型**：默认 GLM 系（高强度任务 GLM-5.3；快/大规模 GLM-5.3-flash；不确定就直派继承当前路由）。**多 subagent 时，对 xxw 提供的模型（Qwen / DeepSeek）：xxw/DeepSeek 接通就优先选 xxw/DeepSeek**（显式 `provider=xxw, model=DeepSeek`），仅 xxw/DeepSeek 不可用（API 报错/超时/不接通）才 fallback 到 xxw/Qwen。"xxw/DeepSeek 接通"判断：显式路由能正常调用（无 API 报错/超时）即接通。
2. **交叉验证与脏活派发（由模型判断，非机械）**：派发实质工作任务时，**由你思考判断**是否需要额外派发交叉验证——不要求每个任务都同步双派。交叉验证模型按第 1 步规则选（xxw 场景：DeepSeek 接通优先 xxw/DeepSeek，否则 xxw/Qwen）。

   **值得派发的场景（鼓励多派，不必吝啬 token）：**
   - 任务结论会作为后续决策的**唯一依据**（比如"这个 bug 的根因是什么"→ 错了全盘错）
   - 任务涉及**多文件/多模块**，单个模型容易遗漏上下文
   - 任务输出是**交付物**（文档、代码、报告）而非中间推导
   - 任务有**明确的可验证答案**（是/否、数值、具体行号），便于比对仲裁
   - 你**自己不太确定**答案，需要第二视角
   - 用户特别强调"仔细"、"重要"、"不能错"

   **不值得派发的场景（省着点）：**
   - 琐碎确认（连通性测试、一句话回答、ls 目录）
   - 纯格式转换（markdown → docx、代码格式美化）
   - 你已经非常确定答案，第二份只是走流程
   - 任务结果只是中间变量，后续步骤会自然校验

   **给 Qwen 的 prompt 规则**：256K 上下文上限，只给目标 + 文件路径，让 Qwen 自读文件，不内联大段内容。
   **比对规则**：两份结果一致则采信；不一致则比对分歧点，你仲裁或呈报用户。
3. **需要确认时**（多子代理 / 严谨模式 / 要覆盖默认模型）：把「任务 → 模型」列给用户确认后再派。
4. **单个简单子代理**：按档直派，不逐次打断。
5. **收尾**：一次性子代理拿回结果即弃；要留给其他会话 / agent 的结论，**显式存进 dsh-mnemon**（Document / 记忆），别指望子代理记得。

## 多路 subagent 审计的汇总纪律（2026-11-10 PORSD 事故沉淀，强制）

> 事故：三路 DeepSeek 盲审中 ds2 已报出"PORSD 置 RSTN、未列 Note-1 例外 [LOW/待确认]"，但 captain 汇总时把该双信号条目捆绑进 SCREN 条目降格丢失，用户裁定材料中 PORSD 不可见 → RTL 实际违反表规则（PORSD 应做 unlock reset）漏改。**发现者的信号在"发现→裁定"之间被汇总环节砍掉带宽，是整条链上最隐蔽的失效点。**

1. **每条 finding 独立成条、原文照抄**：汇总者（captain/主 agent）不得合并、删减或预先取舍 subagent 的 findings。一条 finding 里含多个信号（如"PORSD 与 SCREN 均……"）时必须**拆开各立一条**，逐条进入呈报材料。
2. **不得降格、不替用户筛**：severity 与定性由发现者给出，汇总者只搬运不下调；`[待确认]` 类发现必须**先附规则原文**（如 Note-1 全文、表单元格）对照后再呈报，判定权完整交用户。
3. **确认偏差防线**：刚修完/刚验证过的信号 ≠ 无问题；**不同维度的 ✓ 不能互相传染**（某信号"写门控 ✓"不代表"复位域 ✓"）。凡该信号在其他 finding 中出现，一律按新 finding 处理。
4. **反向全集枚举**：规则形如"除 X 例外清单外全部都要 Y"时，审计任务书必须同时要求两个方向——正方向（例外是否都在豁免域）+ **反方向（Y 域之外的每一个对象必须出示例外身份，出示不了即 HIGH）**。只核例外清单正方向是框架性盲区。
5. **审计任务书的基准链**：规格（表/spec 原文）→ 实现，逐层穿透；不得默认"表=spec 的忠实镜像"，也不得以"表对实现一致"替代"spec 对实现一致"。

<!-- ymzhu 2026-11-10 14:30 -->
