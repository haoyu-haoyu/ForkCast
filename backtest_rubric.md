# ULEZ 2023 回测判定规则（Backtest Rubric）

本文件定义历史回测模块的判定逻辑：系统对 ULEZ 2023 的模拟/分析输出中，出现什么信号才算"方向命中"。
所有判定基于已确认的 truth_set.json。核心原则：**只判定方向与主要风险识别，绝不声称预测精确数字。**

## 判定分级定义

- **HIT（方向命中）**：系统输出中出现了与真实结局方向一致的信号。不要求数值精确。
- **PARTIAL（部分命中）**：方向对但信号弱/不明确，或只捕捉到一半。
- **MISS（未命中）**：系统输出中没有出现该信号，或方向相反。
- **BALANCED HIT（平衡性命中）**：系统同时捕捉到相互矛盾但都真实的两面（如"收益"与"阵痛"并存），这是最高级别的命中，证明模拟捕捉到复杂社会动态。

判定方式：对每条规则，检查系统生成的 impact report / risk timeline / stakeholder impact matrix 中是否出现对应信号。判定可由人工在 demo 前确认，也可由 LLM 辅助打标（但最终以人工为准）。

## 判定规则表

| 规则 ID | 真实结局（来自 truth_set，已确认） | 系统需出现的信号 | 判定标准 | 严禁声称 |
|---|---|---|---|---|
| R1 | 外伦敦反对 51% vs 支持 38%；内伦敦支持 62% vs 反对 26% | "外伦敦/车主依赖群体"的反对强度明显高于"内伦敦群体" | 出现群体间反对强度分化，且方向为外>内 → HIT | 不得声称预测出 51%/62% 这些具体百分比 |
| R2 | 货车合规率(88.9%)显著低于轿车(97.1%)，个体工商户受冲击最重 | "货车司机/个体工商户/小生意人"被识别为受冲击最重、反对最强的经济群体之一 | 该群体被单列并标为高影响/高反对 → HIT；仅笼统提"外伦敦居民"未单列 → PARTIAL | 不得声称预测具体合规率数字 |
| R3 | Uxbridge 补选工党惜败(多数票495)，ULEZ 是关键议题 | "政治反弹/选举显著性(political salience)"被列为 top risk | 政治后果被列为主要风险 → HIT | **严禁声称预测了"工党会输"或"495票"或任何选举结果**；只能表述为 political salience/electoral risk，不得表述为 causal proof |
| R4 | 摄像头破坏 416 起，部分破坏者自称 Blade Runners | "执法抵制/破坏/蓄意破坏叙事(enforcement backlash/sabotage)"信号出现 | 出现执法抵制或破坏相关风险信号 → HIT | 不得声称预测破坏起数(416) |
| R5 | 合规率 91.6%→96.2%，非合规车辆减少53%（行为随时间适应） | "行为适应/长期合规上升(behavioural adaptation/compliance improves over time)"信号出现 | 系统预测出"短期反对，但长期行为逐渐适应/合规上升"的动态 → HIT | 不得声称预测96.2%或53%这些数字 |
| R6 | 空气质量改善(NO2浓度降至多4.4%) 与 公平性/负担争议 并存 | 系统同时输出"政策收益(空气改善/健康)"和"分配性阵痛(低收入/车主负担)"两面 | 两面同时出现 → BALANCED HIT（最高级）；只出现一面 → PARTIAL | 不得声称预测具体空气质量数字 |

## Demo 呈现方式（对应 90 秒脚本 66–80s 高潮段）

回测对照在 demo 里的呈现应是一张**"系统预测信号 vs 真实发生"的并列对照表/卡片**，逐条显示：

- 左列：系统模拟中涌现出的信号（如"外伦敦车主反对强烈""政治议题化""长期合规上升"）
- 右列：真实历史结局（配 truth_set 的来源）
- 中间：命中标记（HIT / BALANCED HIT）

**讲法要诚实且有力**（对应 demo 脚本原话）：
> "Because this is a historical case, we can compare against what actually happened. It gets the direction right: outer-London backlash, political salience — but also rising compliance over time. It does not claim to predict exact numbers; it predicts the shape of the reaction."

## 判定纪律（务必遵守，否则可信度崩塌）

1. **方向 > 数字**：所有命中判定只看方向和主要风险识别，永远不声称预测了 truth_set 里的任何精确数字。
2. **political salience 不等于 causal proof**：R3 政治后果只能表述为"选举显著性/政治风险"，不得表述为"我们预测 ULEZ 导致工党败选"。这是 truth_set 采集备注里明确的 caveat。
3. **平衡性是加分项**：能同时命中 R1（反对）和 R5/R6（长期适应+收益）的系统，比只会预测"反对"的系统强得多。这是区别于简单情绪分析工具的关键，是 demo 高潮的核心卖点。
4. **诚实标注未命中**：如果某条规则系统没命中，如实标 MISS，不要事后粉饰。评委更信任一个"5 命中 1 未命中"的诚实回测，而非"全部完美命中"的可疑结果。
5. **回测是决策支持的证据，不是准确性证书**：报告中必须保留 "simulation is decision support, not deterministic forecast" 的免责声明。

## 判定结果输出格式（供 Codex 实现）

回测模块应输出一个结构化的 `backtest_result.json`，每条规则包含：
- rule_id
- real_outcome（引用 truth_set 对应字段）
- system_signal（系统实际输出的对应信号文本）
- verdict（HIT / PARTIAL / MISS / BALANCED HIT）
- note（判定说明，尤其标注 R3 的 salience-not-causal caveat）

并生成一个人类可读的 `backtest.md` 用于 demo 展示。
