# Policy Impact Sandbox 项目执行计划

> 时间口径说明：原始需求写明“今天是 2026-06-29”；当前工作环境日期是 2026-07-01。本文保留完整的 2026-06-29 至 2026-07-04 赛程计划；如果团队实际从 2026-07-01 才开始执行，直接采用第 14 节的“7/1 压缩版立即行动清单”。

## 一、项目概述 + 一句话定义

**项目代号：** Policy Impact Sandbox

**一句话定义：** 一个 AI 工具，把“评估重大政策或组织决策变更会影响哪些人群、造成什么后果”这个传统上依赖顾问团队、问卷、听证会、耗时数周的低效遗留流程，压缩到几小时；全程人在回路可见、可批准、可调整，关键审计追踪可上链验证，并通过真实历史案例回测证明其可信。

**主叙事：** 这不是“政府政策预测器”，而是大组织处理高风险决策影响评估的现代化工具。政府只是最容易被公众理解、最适合 House of Lords 展示的场景；同一内核也可用于大型企业的定价变更、合规变更、供应链调整、福利政策变更等慢流程。

**架构哲学：** 一个内核 + 多个插头。

- **内核：** 面向 Conduct 的可控 AI impact assessment workflow，包含 seed document ingestion、知识图谱、archetype agents、OASIS 小规模仿真、人在回路控制层、历史回测报告、90 秒 before/after demo。
- **插头：** Kaspa 审计锚定、Fetch.ai Agentverse/ASI:One 入口、Canton 记录存证、CoralOS 观察位。插头必须强化内核，不得反向污染主线。
- **精力分配：** 90% 对准 Conduct；Kaspa 作为并列核心插头优先完成，因为它直接强化 Conduct 的“可信”和“可控”；Fetch.ai 和 Canton 在垂直链路完成后再做。

## 二、Bounty 策略与评分对齐表

| 组件/工作 | 满足的 bounty | 对应评分项/资格点 | 提交平台 | 优先级 |
|---|---|---|---|---|
| 90 秒 before/after demo 门面 | Conduct “Make Legacy Move” | Demo 20%；影响力与提速 30% | <span style="color:red">DoraHacks</span> | 必做 |
| 决策影响评估内核：输入政策、抽取利益相关者、生成 agent、运行仿真、产出报告 | Conduct | 技术实现 35%；影响力与提速 30% | <span style="color:red">DoraHacks</span> | 必做 |
| 人在回路控制层：步骤可见、批准、调整、回退、硬限制 | Conduct | 用户保持掌控 20%；技术实现 35% | <span style="color:red">DoraHacks</span> | 必做 |
| ULEZ 2023 历史回测与真实结果对照 | Conduct；House of Lords 遴选叙事 | 技术实现 35%；影响力 30%；政策制定者可理解性 | <span style="color:red">DoraHacks</span>；现场 demo | 必做 |
| Kaspa audit manifest：把批准、agent 决策、回测结果 hash 锚定到交易 payload | Kaspa；Conduct 加分 | Kaspa 集成 30%；创新 30%；Conduct 可控/可信 | <span style="color:red">DoraHacks</span> | 必做 |
| Kaspa 集成说明与 3-5 分钟视频 | Kaspa | 可工作原型；公开 GitHub；Demo 与 UX 20% | <span style="color:red">DoraHacks</span> | 必做 |
| Canton record exporter：把 simulation summary 或 audit manifest 记录到 Canton LocalNet/DevNet | Cantor8 / Learner | “Building on Canton Network” | <span style="color:red">DoraHacks</span> | 有余力 |
| Agentverse agent：通过 ACP 在 ASI:One 触发一次影响评估 | Fetch.ai | 注册 Agentverse；Agent Chat Protocol；ASI:One discoverable；工具调用；无需自定义前端 | <span style="color:red">Devpost</span> | 有余力 |
| Fetch.ai shared chat URL、Agentverse profile、3-5 分钟视频、README badge | Fetch.ai | 强制交付物 | <span style="color:red">Devpost</span> | 有余力 |
| CoralOS 多 agent 协调接入 | CoralOS & STUK | 条款未公布，需确认是否 MCP-native 协调层 | <span style="color:red">Superteam Earn</span> | 观察位 |
| Bittensor / BasedAI / GCC/ETH 适配 | 已放弃 | 与主线不匹配或细则空白 | 不提交 | 放弃 |

## 三、系统架构

### 3.1 内核 + 插头架构图

```text
                                   [Fetch.ai Plug - 有余力]
                                   Agentverse / ACP / ASI:One
                                             |
                                             v
[Seed Policy Pack] -> [Ingestion + KG] -> [HITL Control Layer] -> [OASIS Simulation Core]
   Conduct              Conduct              Conduct + Kaspa        Conduct
   ULEZ data            entities/relations   approvals/rollback     50-200 archetype agents
        |                    |                       |                       |
        |                    v                       v                       v
        |             [Archetype Generator] -> [Event Log + Audit Manifest] -> [Backtest Evaluator]
        |                    Conduct                 Conduct + Kaspa          Conduct
        |                                                |                       |
        v                                                v                       v
[Historical Truth Set] -------------------------> [Kaspa Audit Plug] ----> [Decision Impact Report]
 Conduct / House of Lords                         tx payload/hash          Conduct demo climax
                                                     |
                                                     v
                                           [Canton Plug - 有余力]
                                           simulation record / manifest
```

### 3.2 数据流

1. **输入 case pack：** ULEZ 2023 seed document、政策边界、目标、时间线、利益相关者初表、真实结果 truth set。放置到 `data/cases/ulez_2023/`。
2. **抽取：** LLM 从 seed documents 抽取 entities、groups、locations、constraints、assumptions，生成 `case_graph.json` 并写入 Neo4j 或本地 JSON fallback。
3. **人在回路检查点 1：** 用户查看并修改利益相关者、假设、数据来源；未批准不得进入 agent generation。
4. **生成 archetype agents：** 生成 50-200 个代表型 agent，不追求大规模，重点覆盖外伦敦车主、低收入家庭、vans/tradespeople、健康受益人、环保支持者、地方议员、反对组织、媒体等群体。
5. **人在回路检查点 2：** 用户批准 agent composition、初始立场、行动空间、轮次数、预算上限。
6. **仿真：** OASIS 在仿社媒环境中运行少量轮次，输出 posts/comments/reposts/following/stance changes。现场 demo 优先 replay 预跑结果，保留“Run live sample”按钮。
7. **汇总：** 生成 stakeholder impact matrix、risk timeline、predicted backlash signals、mitigations、confidence notes。
8. **历史回测：** 将系统预测与真实结果清单对照，标注方向命中、强度偏差、遗漏点，避免声称精确预测。
9. **审计：** 对每个关键 artifact 做 canonical JSON + SHA-256 hash，形成 `audit_manifest.json`；把 manifest hash、case id、stage、timestamp、artifact URI 锚定到 Kaspa transaction payload。
10. **输出：** Dashboard 展示 before/after、控制轨迹、仿真结果、回测对照、Kaspa tx hash、可下载报告。

## 四、技术栈决策

| 层 | 选择 | 理由 | 风险/待确认 |
|---|---|---|---|
| Backend | Python 3.11+ + FastAPI + uv | 与 OASIS、uAgents、数据处理生态一致，开发速度快 | 无 |
| Frontend | React + Vite + TypeScript | 快速做可点击 dashboard，适合 90 秒 demo | 若人手不足，用 Streamlit fallback |
| Simulation engine | `camel-oasis`，优先 Reddit-like environment，小规模 50-200 agents | OASIS 官方说明支持大规模 LLM social simulation、23 种动作；MVP 用小规模更稳 | OASIS 与政策影响评估不是原生一一对应，需通过 archetype + social discourse framing 解释 |
| Agent action subset | create post/comment、like/dislike、follow、refresh/trend、do nothing | 足够表现信息扩散、反对动员、支持/反对声量；避免无关动作增加噪音 | 需要在 UI 中说明这是“公众反应仿真”，不是全社会经济模型 |
| Knowledge graph | MVP：Neo4j local/Aura；fallback：`case_graph.json` + NetworkX | Neo4j 可视化和 Cypher 对 demo 友好；fallback 防止安装拖慢 | 若 6/30 前 Neo4j 未跑通，立刻用 JSON fallback |
| LLM | OpenAI-compatible API；生成/摘要用便宜模型，最终叙事可用更强模型手工触发 | 保持供应商可替换，控制成本 | 具体模型按团队 API key 与速率限制确认 |
| Persistence | SQLite for simulation/event log + JSON artifacts | OASIS 示例本身使用 DB path；SQLite 便于导出和审计 | 无 |
| Kaspa integration | MVP：Kaspa transaction payload 写入 `audit_manifest_hash`、artifact URI、stage metadata；优先用 JS Wallet API 或 Python SDK | 官方 docs 支持 transaction payload，payload 主导时实际限制约 25KB；链下推理、链上承诺符合 bounty 方向 | SilverScript/Covenants 可加分，但工具链 release/audit 状态需确认；不得把未完成 covenant 说成已完成 |
| Kaspa stretch | SilverScript covenant approval workflow：仅在工具链稳定时做“approved state can advance”示例 | 对 Kaspa 集成评分有加分潜力 | 若 7/2 中午前不能端到端发送/验证，降级为 payload hash anchoring |
| Agentverse/ASI:One | `uagents` + `chat_protocol_spec` + `mailbox=True` + `publish_agent_details=True` | 官方示例要求 agent 在线、ACP、Agentverse profile，可被 ASI:One Chat 使用 | 需要 ASI:One API key、Agentverse account、profile URL；成本高，主线后做 |
| Canton | CN Quickstart + Daml record template，LocalNet 优先 | 官方 Quickstart 提供 Dockerized LocalNet；足够证明 building on Canton 的最小路径 | DevNet/public network access 可能需要 sponsoring SV/VPN，需向 sponsor 确认 |
| Reporting | Markdown/PDF export + dashboard report cards | 评委可下载，提交材料可复用 | PDF 可选，不影响现场 |

## 五、详细任务拆解（WBS）

| ID | 模块 | 子任务 | 交付物/放置位置 | 依赖 | 预估 | 优先级 | 主得分点 |
|---|---|---|---|---|---:|---|---|
| W0 | Scope | 冻结一句话定位、bounty 取舍、demo 案例选 ULEZ | `docs/product/positioning.md` | 无 | 1h | 必做 | Conduct 影响力 |
| W1 | Repo | 建 repo 骨架、README、env template、demo script folder | `README.md`, `.env.example`, `docs/submission/` | W0 | 2h | 必做 | 所有提交 |
| W2 | Case Pack | 收集 ULEZ 官方/可靠资料、政策文本、时间线 | `data/cases/ulez_2023/sources.md` | W0 | 4h | 必做 | Conduct 技术可信 |
| W3 | Truth Set | 建真实结果对照清单：政治、公众反应、合规、空气质量 | `data/cases/ulez_2023/truth_set.json` | W2 | 3h | 必做 | 历史回测高潮 |
| W4 | Seed Doc | 写 ULEZ seed document，包含政策目标、范围、约束、未知项 | `data/cases/ulez_2023/seed_policy.md` | W2 | 2h | 必做 | Demo 输入 |
| W5 | Extraction | 定义 entity/stakeholder/assumption schema 与 prompt | `schemas/case_graph.schema.json`, `prompts/extract_case.md` | W4 | 3h | 必做 | Conduct 技术实现 |
| W6 | KG | 输出 case graph 并接 Neo4j 或 JSON fallback | `data/cases/ulez_2023/case_graph.json` | W5 | 3h | 必做 | Conduct 技术实现 |
| W7 | Archetypes | 生成 50-200 个 archetype agent profiles | `data/cases/ulez_2023/agents.json` | W6 | 4h | 必做 | Conduct 技术实现 |
| W8 | HITL UX | 设计四个批准点：抽取、agent、仿真配置、最终报告/上链 | `docs/product/control_flow.md`, dashboard screens | W5-W7 | 5h | 必做 | Conduct 用户掌控 20% |
| W9 | OASIS Wrapper | 运行小规模 simulation 或 replay 预跑结果 | `runs/ulez_2023/<run_id>/` | W7-W8 | 6h | 必做 | Conduct 技术实现 |
| W10 | Cost Guard | 限制 agent 数、rounds、LLM 调用、每阶段 max cost | config + UI guardrails | W9 | 2h | 必做 | 控制胜过自主 |
| W11 | Report | 生成 impact matrix、risk timeline、recommendation caveats | `runs/.../report.md`, dashboard report | W9 | 4h | 必做 | Conduct 影响力 |
| W12 | Backtest | 将预测与 truth set 对照，输出 directional hit table | `runs/.../backtest.md` | W3,W11 | 4h | 必做 | Conduct 技术 + demo |
| W13 | Persona Chat | 可与任一 agent 追问“为什么你反对/支持” | dashboard chat panel | W7,W9 | 3h | 必做 | Demo/可解释 |
| W14 | Dashboard | 完成 90 秒 demo 的 before/after screens | web app | W8-W13 | 8h | 必做 | Conduct Demo 20% |
| W15 | Kaspa Manifest | 设计 `audit_manifest.json`：stage、hash、actor、approval、artifact URI | `schemas/audit_manifest.schema.json` | W8,W11,W12 | 2h | 必做 | Kaspa 集成 |
| W16 | Kaspa Anchor | 发送 payload tx，展示 tx id/explorer link 或本地验证 | `docs/submission/kaspa-integration.md` | W15 | 5h | 必做 | Kaspa 30% |
| W17 | Kaspa Video | 录 3-5 分钟 Kaspa integration demo | `docs/submission/kaspa-demo.mp4` | W16 | 2h | 必做 | Kaspa 交付 |
| W18 | Canton Record | Daml template 存 `manifestHash`, `caseId`, `reportUri` | `docs/submission/canton-proof.md` | W15 | 4h | 有余力 | Cantor8 |
| W19 | Fetch Agent | 包装 backend endpoint 为 uAgent，支持 ACP chat | `agents/fetch_policy_agent/` | W11 | 6h | 有余力 | Fetch 强制资格 |
| W20 | Fetch Submit | Agentverse profile、ASI:One shared chat、README badge、视频 | Devpost assets | W19 | 4h | 有余力 | Fetch 交付 |
| W21 | Submission README | 一份评委从 README 直接跑通/理解 | `README.md`, `docs/submission/README.md` | W14-W18 | 3h | 必做 | 所有 |
| W22 | Rehearsal | 90 秒现场脚本、备用录屏、断网 fallback | `docs/demo/90s-script.md`, backup video | W14,W16 | 3h | 必做 | Conduct Demo |
| W23 | Final Submit | DoraHacks/Devpost/Superteam Earn 平台逐项提交 | submission receipts | W17-W22 | 3h | 必做 | 避免漏交 |

## 六、逐日时间线（2026-06-29 至 2026-07-04）

| 日期 | 当日目标 | 必须完成的 WBS | 里程碑/退出标准 |
|---|---|---|---|
| 6/29 | 锁定定位、案例、分工、资料源；不要写泛化平台 | W0-W4；W8 初稿 | ULEZ 被正式选为主 case；有 seed document 和 truth set 草案；每个人知道 7/2 前交什么 |
| 6/30 | 跑出“输入 -> 图谱 -> agents”的前半链路 | W5-W8；W7 初版 | 50-200 个 archetype agents 可视化；HITL 四个 checkpoint 有 wireframe |
| 7/1 | 跑出 simulation + report + backtest 初版 | W9-W13；W15 初版 | 至少一条预跑结果能生成 report/backtest；能讲清哪些是真预测、哪些是 ground truth |
| 7/2 | 晚上前完成端到端垂直链路红线 | W14-W17；W21 初版 | 从 seed -> approve -> run/replay -> report -> backtest -> Kaspa hash -> dashboard 可现场点击；若 Fetch/Canton 未完成，不影响主线 |
| 7/3 | 只做减法和打磨，不加新功能 | W12-W17 polish；W18 视情况；W22 | 90 秒 demo 连续跑 5 次不崩；所有“待确认”在 README 中诚实标注；可提交 Conduct/Kaspa |
| 7/4 | Demo Day + 提交 | W23；最终 rehearsal | DoraHacks 提交 Conduct/Kaspa/Cantor8；若 Fetch 完成则 Devpost；保留提交截图/receipt |

**7/2 红线定义：** 晚上必须有一条能从头跑到尾、能现场点的垂直链路。7/3 开始禁止新增 feature；任何无法强化 90 秒 demo 或提交资格的东西全部砍掉。

## 七、团队分工（2-4 人假设）

### 4 人配置

| 角色 | 负责人类型 | 核心责任 | 不能分散精力的点 |
|---|---|---|---|
| A：Historical Backtest Owner（最强的人） | 最懂产品/数据/叙事的人 | ULEZ case pack、truth set、agent archetype 真实性、backtest 对照、demo 高潮 | 不要被前端小修和链上插件拉走；护住可信度护城河 |
| B：Simulation/Backend Lead | Python/OASIS 强 | ingestion、KG、agent generation、OASIS wrapper、report pipeline、成本限制 | 7/2 前只服务 ULEZ 单案例 |
| C：Frontend/HITL Lead | React/UX 强 | before/after dashboard、approval checkpoints、rollback UI、persona chat、demo flow | UI 必须服务 90 秒脚本，不做通用后台 |
| D：Chain/Submission Lead | Web3/DevRel 强 | Kaspa tx payload、Canton proof、Fetch agent、README、视频、平台提交 | Kaspa 必做；Fetch/Canton 服从垂直链路红线 |

### 3 人配置

- A：Historical Backtest + Product/Demo
- B：Simulation/Backend
- C：Frontend + Kaspa + Submission

### 2 人配置

- A：Historical Backtest + Simulation + Demo narrative
- B：Frontend + HITL + Kaspa + Submission

2 人配置下直接放弃 Fetch.ai；Canton 只做 Quickstart 证明或截图级存证，不允许影响 Conduct/Kaspa。

## 八、90 秒 Demo 脚本/分镜

| 时间 | 屏幕 | 讲法 | 目的 |
|---:|---|---|---|
| 0-8s | Before screen：传统 impact assessment 流程图，weeks、consultants、hearings、spreadsheets | “Today, assessing who gets hurt by a major policy change takes weeks of consultants, surveys and hearings.” | 非工程师立刻懂痛点 |
| 8-16s | Upload/select ULEZ 2023 seed policy | “We turn that legacy process into a controlled AI workflow. Here is the 2023 London ULEZ expansion.” | 真实案例，不是玩具 |
| 16-28s | Extraction review：stakeholders、locations、assumptions 高亮 | “The agent proposes stakeholders and assumptions, but it cannot proceed until a human approves or edits them.” | 吃 Conduct 用户掌控 |
| 28-40s | Agent archetype review：outer London drivers、low-income households、van drivers、health beneficiaries、local politicians | “We simulate representative archetypes, not thousands of uncontrolled bots.” | 展示小规模、可信、可控 |
| 40-52s | Run/replay simulation：仿社媒 feed、stance shifts、risk signals | “Within minutes we see where opposition concentrates and how the narrative spreads.” | After 的速度感 |
| 52-66s | Impact report：risk matrix + mitigation options | “The output is not a black-box answer; it is a decision memo with traceable assumptions.” | 大组织决策价值 |
| 66-80s | Backtest comparison：predicted backlash vs real Uxbridge/camera vandalism/compliance rise | “Because this is a historical case, we can compare against what actually happened. It gets the direction right: outer-London backlash, political salience, but also rising compliance.” | Demo 高潮，证明可信 |
| 80-88s | Audit trail：approval history + Kaspa tx hash | “Every critical approval and result is hashed and anchored on Kaspa, so the process is verifiable after the fact.” | Kaspa + Conduct 双得分 |
| 88-90s | Closing screen：Weeks -> hours; control beats autonomy | “Weeks to hours, with the human still in control.” | 记忆点 |

**备用策略：** 现场只 live run 10 agents x 1 round；主 demo 使用预跑 100 agents x 3-5 rounds 的 replay。断网时播放本地录屏，并展示本地 `audit_manifest.json` 与已生成 tx hash。

## 九、历史回测案例方案

### 推荐：ULEZ 2023 扩区

选择 ULEZ，而不是 2017 “痴呆税”，原因：

- **本地性强：** 伦敦、Imperial、外伦敦议题，现场评委和 House of Lords 受众更容易共情。
- **影响群体清晰：** 外伦敦车主、低收入家庭、旧车/van 用户、呼吸健康受益者、环保支持者、地方政治参与者。
- **结果可对照：** 有政策扩区日期、收费规则、公众争议、camera vandalism、Uxbridge by-election、后续合规率和空气质量报告。
- **更适合 Conduct：** 它可被讲成“大组织处理高风险 stakeholder impact assessment 的慢流程”，而不是抽象政策评论。

### 必收历史背景数据

| 数据 | 用途 | 推荐来源 |
|---|---|---|
| ULEZ 扩区范围与生效日期：2023-08-29 扩至所有 London boroughs | seed policy 基础事实 | TfL ULEZ Expansion 2023 |
| 收费规则、合规标准：非合规车辆每日收费，Euro 4 petrol / Euro 6 diesel 等 | 影响判断、agent 约束 | House of Commons Library briefing；TfL |
| 外伦敦交通/车主依赖、van/tradespeople 影响 | archetype 真实性 | TfL/GLA data、ONS、公开报道 |
| 公众意见和反对叙事 | agent 初始立场、仿真 seed posts | YouGov、新闻、咨询反馈 |
| Camera vandalism / enforcement backlash | truth set | YouGov、可靠媒体、警方/官方数据如可获得 |
| Uxbridge and South Ruislip by-election 结果 | political backlash truth | UK Parliament election result |
| 6 个月后合规率、非合规车辆下降、NO2/空气质量变化 | outcome truth，避免只讲 backlash | London-wide ULEZ Six Month Report |

### 真实结果对照清单（truth set）

系统不需要预测精确数字；目标是方向命中和主要风险识别。

| 真实结果 | 期望系统在回测中捕捉到的信号 | 判定方式 |
|---|---|---|
| 外伦敦/旧车/van 用户更可能强烈反对 | “outer London car-dependent groups” risk score 高 | 方向命中 |
| ULEZ 成为 Uxbridge by-election 显著政治议题；Conservative hold，majority 495 | “political backlash/electoral salience” 被列为 top risk | 方向命中，不要求预测 495 |
| Camera vandalism/执法基础设施遭破坏成为舆论点 | “enforcement backlash / sabotage narrative” 出现 | 方向命中 |
| 车辆合规率上升，非合规车辆显著下降 | “behaviour adaptation/compliance improves over time” 出现 | 方向命中 |
| 空气质量/排放指标改善，但政策公平性争议持续 | “benefits and distributional pain both exist” 同时出现 | 平衡性命中 |

### 备选：2017 “痴呆税”

仅当 ULEZ 数据收集受阻时启用。优点是政策反噬叙事强；缺点是与伦敦本地、仿社媒数据、空气质量等多维真实指标的结合弱。

## 十、人在回路控制层设计

### 10.1 可见节点

| 阶段 | 用户必须看到什么 | 用户动作 |
|---|---|---|
| Source intake | 已使用/未使用的 source list、文件 hash、日期、来源类型 | include/exclude source；标注 source quality |
| Entity extraction | 政策目标、地理边界、人群、约束、未知项 | approve/edit/reject；添加 missing stakeholder |
| Assumption sheet | 每条假设、证据来源、confidence、影响范围 | 修改权重；冻结假设；要求补证据 |
| Agent generation | 每类 archetype 的数量、persona、初始立场、约束 | 调整群体占比；禁用不可信 persona |
| Simulation config | agent count、rounds、action space、LLM budget、random seed | 批准运行；降规模；锁 random seed |
| Simulation trace | 每轮主要事件、stance shift、top narratives | 暂停；回退到上个 checkpoint；重跑 |
| Report claims | 每条结论对应 evidence、simulation signal、truth/backtest status | approve claim；降级措辞；删除 unsupported claim |
| Audit anchoring | 将要上链的 manifest hash、artifact URI、stage metadata | approve anchor；禁止上链；查看 tx hash |

### 10.2 可调整参数

- Stakeholder weights：群体人数占比、受影响强度、政策收益/成本暴露度。
- Sentiment priors：初始支持/反对/中立概率。
- Geography：outer London vs inner London、borough grouping。
- Action space：允许 create post/comment/repost-like 行为；禁用无关动作。
- Run budget：agent 数、轮次、每轮最大 LLM 调用、总成本上限。
- Evidence filter：是否允许新闻报道、民调、官方数据、社媒数据进入 case pack。
- Report strictness：只输出 high-confidence claims，或允许 speculative warnings 但强制标注。

### 10.3 可回退机制

- 每次 approval 生成 `checkpoint_id`。
- 每个 checkpoint 保存 `case_graph`, `agents`, `simulation_config`, `run_output`, `report_claims` 的 hash。
- UI 提供 “Compare with previous checkpoint” 和 “Rollback to checkpoint”。
- rollback 后旧 checkpoint 不删除，只标记 superseded，保留 audit trail。

### 10.4 Agent 自主行为硬限制

- Agent 不得自行添加新 source；新 source 必须由用户批准。
- Agent 不得自动改变 stakeholder weights；只能提出建议。
- Agent 不得自动发送 Kaspa/Canton transaction；上链必须用户批准。
- Agent 不得输出“政策应该/必须执行”的最终建议，只能输出 impact/risk/mitigation options。
- Agent 不得处理个人身份信息；所有 persona 必须是 archetype，不是真人画像。
- 单次 run 默认最多 100 agents x 5 rounds；超过需用户确认。
- 报告必须标注 “simulation is decision support, not deterministic forecast”。
- 已锚定 audit manifest 不得被覆盖；修改后必须生成新 manifest。

这部分直接对应 Conduct 的 “Control beats autonomy”：用户看到 agent 在做什么、为什么这么做，并能逐步批准、调整、回退，同时关键自主行为有硬限制。

## 十一、提交清单（按平台）

### <span style="color:red">DoraHacks：Conduct / Kaspa / Cantor8</span>

**Conduct Track “Make Legacy Move”**

- Working tool URL 或本地运行说明。
- 公开 GitHub repo。
- README：一句话定义、before/after、如何运行、已知限制。
- 90 秒现场 demo 准备：live path + backup recording。
- ULEZ historical backtest report。
- 控制层说明：checkpoints、approval、rollback、hard limits。

**Kaspa Bounty**

- 公开 GitHub repo。
- 3-5 分钟 demo video。
- `docs/submission/kaspa-integration.md`：解释链下推理、链上承诺、payload/hash 内容、tx id/explorer link。
- `audit_manifest.json` 示例。
- Kaspa tx hash 或可验证 payload proof。
- 如果 SilverScript/Covenants 只做 stretch，必须诚实标注“prototype/待确认”，不要包装成 production covenant。

**Cantor8 / Learner**

- Canton Quickstart/Daml 记录证明。
- contract/template 代码或截图。
- `manifestHash`、`caseId`、`reportUri` 写入记录的 evidence。
- 若只在 LocalNet 跑通，明确写 “LocalNet proof；DevNet/public access 待 sponsor 确认”。

### <span style="color:red">Devpost：Fetch.ai</span>

仅在 7/2 垂直链路完成后推进。必须包含：

- ASI:One shared chat session URL。
- Agentverse Profile URL。
- 公开 GitHub repo。
- 3-5 分钟视频。
- 问题/用户/产出简述。
- README 加 innovationlab + hackathon 徽章。
- Agent 必须注册到 Agentverse、实现 ACP、可被 ASI:One discover/use、有 meaningful tool call 或 agent orchestration。
- 主流程不能依赖自定义前端；用 ASI:One chat 发起 “Run impact assessment for ULEZ case”。

### <span style="color:red">Superteam Earn：CoralOS & STUK</span>

- 条款未公布，先不做。
- 每天检查 Discord/Superteam Earn。
- 若公布要求只是“用 CoralOS 做 agent coordination/MCP-native orchestration”，评估是否能把 OASIS wrapper 的 orchestration layer 替换/包一层。
- 若需要大改主线，放弃。

## 十二、风险与应对表

| 风险 | 影响 | 早期信号 | 应对 |
|---|---|---|---|
| 可信度被质疑：“AI 怎么能预测政策？” | Conduct 技术/影响评分下降 | 评委追问模型依据 | 坚持“historical backtest + decision support”；不声称精确预测，只展示方向命中、假设可审计 |
| Demo 讲不清 | Demo 20% 丢分 | 90 秒讲不完架构 | 只讲 before/after、HITL、backtest、Kaspa hash；技术细节放 README |
| OASIS 跑不稳或太贵 | 垂直链路失败 | run 超过 5 分钟或 API 失败 | 预跑 replay 为主；live sample 10 agents；缓存所有 intermediate artifacts |
| Agent 规模诱惑导致过度工程 | 7/2 红线失守 | 有人想跑 1000 agents | 明确 50-200 archetype agents；评分看 demo 和可信链路，不看 agent 数量 |
| Kaspa 集成被认为只是“存 hash”太浅 | Kaspa 集成 30% 风险 | 评委问 programmable coordination | 说明 audit manifest 是 approval workflow 的承诺层；stretch 展示 SilverScript/covenant 设计图；若无代码则诚实标注 |
| SilverScript/Covenants 工具链不稳 | 时间浪费 | 半天不能发/验交易 | 7/2 中午前未跑通即降级 payload anchoring |
| Fetch.ai 独立提交成本高 | 拖累主线 | Agentverse account/API/profile 卡住 | 只在 Conduct/Kaspa 可提交后做；7/3 中午前没 profile URL 就放弃 |
| Canton public network access 不确定 | Cantor8 不完整 | DevNet onboarding 要 sponsor/VPN | LocalNet proof + Daml record；提交时标注 access 待确认 |
| 政府叙事与 Conduct “大组织 legacy process”不对齐 | Conduct 命题偏离 | 评委认为只是 civic tech | 开场讲“大组织高风险决策影响评估”；政府只是 demonstrator |
| 历史数据收集过深 | 时间不够 | A 角色陷入资料海 | truth set 只保留 demo 必需 5 个结果；多余资料放 appendix |
| 7/1 才开始执行 | 原 6/29 计划已滞后 | 前两天任务未完成 | 砍 Fetch/Canton；当天补完 W0-W8；7/2 只交 Conduct/Kaspa |

## 十三、待确认/未公布事项清单

| 事项 | 当前状态 | 谁负责 | 最晚确认时间 | 若未确认的处理 |
|---|---|---|---|---|
| Fetch.ai 奖金口径 | DoraHacks 1,000 USDT vs hackpack £500/£350/£150 + internship interview 不一致 | Submission Lead | 7/1 晚 | README 标注奖金口径待确认；不影响是否提交 |
| Conduct 奖金分配比例 | 8,000 £ 前三名分配比例未公布 | Product Lead | 7/2 | 不影响主线 |
| CoralOS & STUK 条款 | “dropping soon”，未公布 | Submission Lead | 每天 12:00/18:00 查 | 未公布则不做 |
| House of Lords 展示遴选标准 | 官方未公布 | Product Lead | 7/3 | 用 policymakers 友好的 public value/backtest 叙事，但不声称符合标准 |
| Kaspa SilverScript/Covenants 当前可用性、audit 状态 | 官方 docs 说明 tooling 仍年轻，需检查 release/audit 状态 | Chain Lead | 7/2 中午 | 不可用则只做 payload hash anchoring |
| Kaspa bounty 是否接受 testnet tx | 待 sponsor/Discord 确认 | Chain Lead | 7/2 | 优先可验证 transaction；不能确认则文档中说明网络选择 |
| Canton 是否必须上 DevNet/public network | 待 sponsor 确认 | Chain Lead | 7/3 | 默认 LocalNet proof，公开网络接入标注待确认 |

## 十四、今天（6/29）立即行动清单

### 6/29 原计划立即行动

1. **15 分钟 scope freeze：** 决定只打磨 ULEZ 单案例；Conduct/Kaspa 必做；Fetch/Canton 明确为有余力。
2. **建立资料夹：** 创建 `data/cases/ulez_2023/`, `docs/demo/`, `docs/submission/`, `runs/`。
3. **A 角色开始 truth set：** 收集 TfL、House of Commons Library、UK Parliament by-election、London ULEZ six-month report、YouGov/可靠媒体资料，输出 5 条真实结果。
4. **B 角色验证 OASIS：** `pip install camel-oasis`，跑通最小 Reddit example；确认 10 agents x 1 round 可运行。
5. **C 角色画 90 秒 demo wireframe：** 只画 6 屏：Before、Upload、Approve extraction、Approve agents、Simulation/report、Backtest + Kaspa。
6. **D 角色验证 Kaspa：** 读 Kaspa payload docs，确定 SDK/Wallet API 路线，写 `audit_manifest` schema 初稿。
7. **当天结束检查：** 口头跑一遍 90 秒脚本；任何不服务这条脚本的 feature 先砍。

### 7/1 压缩版立即行动（如果现在才开工）

**目标：今晚必须补齐 6/29-6/30 的产物，明天 7/2 冲端到端。**

1. **09:30-10:00：Scope freeze。** 写死 ULEZ；放弃 Fetch.ai 直到 Conduct/Kaspa 完成；Canton 只保留 LocalNet stretch。
2. **10:00-12:00：资料与 truth set。** A 角色完成 `sources.md`, `seed_policy.md`, `truth_set.json` 的可用版，只保留 5 个对照事实。
3. **10:00-12:00：技术 spike。** B 角色跑通 OASIS 最小 example；若失败，立刻用 mock simulation events 保证 dashboard 不断。
4. **12:00-14:00：case graph + archetypes。** 生成 30-50 个 agent profiles 先用于 UI；晚上再扩到 100。
5. **14:00-17:00：HITL dashboard。** C 角色做四个 approval screens，允许 fake/replay data，不等 backend 完美。
6. **14:00-18:00：Kaspa audit。** D 角色完成 `audit_manifest.json`、hash、payload tx spike；若 tx 失败，先生成可验证 manifest + integration doc，明早补 tx。
7. **18:00-21:00：首条 vertical replay。** seed -> approve -> replay -> report -> backtest -> audit hash 在 dashboard 连起来。
8. **21:00-22:00：Demo rehearsal。** 按 90 秒脚本过 3 次；列出明天只修的 top 5 blocking issues。

## 参考资料（实现边界用）

- OASIS GitHub：<https://github.com/camel-ai/oasis>
- Kaspa Docs - Programmability：<https://docs.kaspa.org/programmability>
- Kaspa Docs - Toccata Dev Guide：<https://docs.kaspa.org/toccata>
- Kaspa Docs - Transaction Payload：<https://docs.kaspa.org/integrate/transaction-payload>
- Agentverse Docs - Enable Chat Protocol：<https://docs.agentverse.ai/documentation/getting-started/enable-chat-protocol>
- ASI:One Docs - Agent Chat Protocol：<https://docs.asi1.ai/documentation/tutorials/agent-chat-protocol>
- Canton Network Developer Resources：<https://www.canton.network/developer-resources>
- Canton Network Quickstart Installation：<https://docs.digitalasset.com/build/3.5/quickstart/download/cnqs-installation.html>
- TfL ULEZ Expansion 2023：<https://tfl.gov.uk/modes/driving/ultra-low-emission-zone/ulez-expansion-2023>
- House of Commons Library - Clean Air Zones, Low Emission Zones and London ULEZ：<https://commonslibrary.parliament.uk/research-briefings/cbp-9816/>
- London-wide ULEZ Six Month Report：<https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report>
- UK Parliament - 2023 Uxbridge and South Ruislip by-election result：<https://members.parliament.uk/constituency/3817/election/412>
- YouGov - Londoners split on ULEZ expansion：<https://yougov.com/en-gb/articles/46024-londoners-split-ulez-expansion>
- Institute for Government - Uxbridge by-election and net zero：<https://www.instituteforgovernment.org.uk/comment/uxbridge-crossroads-net-zero>
