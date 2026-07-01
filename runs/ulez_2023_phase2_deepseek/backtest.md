# Blind Prediction Backtest: ulez_2023_expansion

simulation is decision support, not deterministic forecast

Backtest mode: `blind_prediction`

| Rule | Verdict | System signal | Real outcome | Note |
|---|---|---|---|---|
| R1 | PARTIAL | Blind prediction identifies outer-London opposition but inner-London contrast is weak. | YouGov/ITV 2023-08-09 至 2023-08-14 调查显示：Londoners 47% 支持扩区、42% 反对；inner London 支持 62% vs 反对 26%；outer London 反对 51% vs 支持 38%。 | Blind prediction is checked for outer-London opposition stronger than inner-London support. |
| R2 | HIT | Blind prediction singles out van drivers, tradespeople or small businesses as high-opposition/high-impact groups. | London-wide ULEZ 6 个月报告显示，subject vehicles 的 London-wide compliance rate 从 2023-06 的 91.6% 上升到 6 个月后的 96.2%。Cars 为 97.1%，vans 为 88.9%。 | Blind prediction must single out van drivers/tradespeople/small businesses; generic vehicle cost pressure is only partial. |
| R3 | HIT | Blind prediction flags political salience/electoral risk without claiming a specific election result. | 2023-07-20 Uxbridge and South Ruislip by-election 为 Conservative hold；Steve Tuckwell 13,965 票、45.2%；Danny Beales 13,470 票、43.6%；多数票 495；投票率 46.1%。 \| 可靠分析/报道将 ULEZ 扩区与 Uxbridge 补选结果直接关联：Institute for Government 认为 ULEZ plans 是 Labour narrow loss 的 key factor；YouGov 文章称 ULEZ 被 held responsible for Labour’s failure to win the seat。 | Counts political salience/electoral risk only; not causal proof and not an election result prediction. |
| R4 | HIT | Blind prediction flags enforcement resistance, sabotage, camera backlash or vandalism risk. | Metropolitan Police FOI 显示 2023-08-01 至 2023-10-15 期间记录 416 起 ULEZ-related offences：59 theft、357 arson and criminal damage；property status 中 74 stolen、358 damaged。Sky/ITV 报道说明部分破坏者自称 Blade Runners。 | Blind prediction is checked for enforcement resistance, sabotage, or camera backlash. |
| R5 | HIT | Blind prediction flags short-term backlash with longer-term adaptation/compliance improvement. | London-wide ULEZ 6 个月报告显示，subject vehicles 的 London-wide compliance rate 从 2023-06 的 91.6% 上升到 6 个月后的 96.2%。Cars 为 97.1%，vans 为 88.9%。 \| 2024-02 与 2023-06 相比，London-wide ULEZ 平均每日检测到的 non-compliant vehicles 减少 90,000，降幅 53%。 | Blind prediction is checked for short-term opposition plus longer-term adaptation/compliance direction. |
| R6 | BALANCED HIT | Blind prediction captures both air-quality/health benefits and distributional fairness burden. | 6 个月报告给出 NOx emissions 和 NO2 concentrations 两类结果：outer London cars/vans NOx emissions 相对 no-ULEZ scenario 分别低 13% 和 7%；outer London roadside NO2 concentrations 在首 6 个月 up to 4.4% lower。 \| 非合规且未豁免车辆在 ULEZ 内行驶需支付每日 £12.50。 \| YouGov/ITV 2023-08-09 至 2023-08-14 调查显示：Londoners 47% 支持扩区、42% 反对；inner London 支持 62% vs 反对 26%；outer London 反对 51% vs 支持 38%。 | BALANCED HIT requires both air-quality/health benefit and fairness/distributional burden. |

This table compares qualitative blind-prediction signals against verified historical outcomes.
It does not claim to predict exact numbers.
