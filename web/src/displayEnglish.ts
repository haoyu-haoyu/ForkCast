// Display-layer English rendering for Chinese text that arrives verbatim from
// anchored run artifacts (web/src/data/* copies) and live API status enums.
//
// The canonical data is NEVER modified: runs/** is committed to on-chain
// anchors and stays byte-identical, and the web/src/data/* display copies are
// left untouched so provenance stays obvious. This map only changes what the
// dashboard renders. Lookups are keyed by the EXACT source string — if the
// underlying artifact ever changes, the lookup misses and the original text is
// shown, so a translation can never silently misrepresent changed data.
//
// Translations preserve every figure, date and named source. Where the ULEZ
// truth set already carries English source quotes (TfL, YouGov, House of
// Commons Library), the wording follows those quotes.

const DISPLAY_TRANSLATIONS: Record<string, string> = {
  // --- backtest_result.json rules[].real_outcome (R1-R6) ---
  "YouGov/ITV 2023-08-09 至 2023-08-14 调查显示：Londoners 47% 支持扩区、42% 反对；inner London 支持 62% vs 反对 26%；outer London 反对 51% vs 支持 38%。":
    "YouGov/ITV polling (2023-08-09 to 2023-08-14) found 47% of Londoners supported the expansion and 42% opposed; inner London 62% support vs 26% oppose; outer London 51% oppose vs 38% support.",

  "London-wide ULEZ 6 个月报告显示，subject vehicles 的 London-wide compliance rate 从 2023-06 的 91.6% 上升到 6 个月后的 96.2%。Cars 为 97.1%，vans 为 88.9%。":
    "The London-wide ULEZ six month report shows the London-wide compliance rate of subject vehicles rose from 91.6% in June 2023 to 96.2% after six months. Cars reached 97.1%, vans 88.9%.",

  "2023-07-20 Uxbridge and South Ruislip by-election 为 Conservative hold；Steve Tuckwell 13,965 票、45.2%；Danny Beales 13,470 票、43.6%；多数票 495；投票率 46.1%。 | 可靠分析/报道将 ULEZ 扩区与 Uxbridge 补选结果直接关联：Institute for Government 认为 ULEZ plans 是 Labour narrow loss 的 key factor；YouGov 文章称 ULEZ 被 held responsible for Labour’s failure to win the seat。":
    "The 2023-07-20 Uxbridge and South Ruislip by-election was a Conservative hold: Steve Tuckwell 13,965 votes (45.2%), Danny Beales 13,470 votes (43.6%), majority 495, turnout 46.1%. | Credible analysis/reporting linked the ULEZ expansion directly to the result: the Institute for Government called the ULEZ plans a key factor in Labour's narrow loss; a YouGov article said ULEZ was held responsible for Labour's failure to win the seat.",

  "Metropolitan Police FOI 显示 2023-08-01 至 2023-10-15 期间记录 416 起 ULEZ-related offences：59 theft、357 arson and criminal damage；property status 中 74 stolen、358 damaged。Sky/ITV 报道说明部分破坏者自称 Blade Runners。":
    "A Metropolitan Police FOI response records 416 ULEZ-related offences between 2023-08-01 and 2023-10-15: 59 theft, 357 arson and criminal damage; property status shows 74 stolen and 358 damaged. Sky/ITV reporting notes some of the vandals call themselves Blade Runners.",

  "London-wide ULEZ 6 个月报告显示，subject vehicles 的 London-wide compliance rate 从 2023-06 的 91.6% 上升到 6 个月后的 96.2%。Cars 为 97.1%，vans 为 88.9%。 | 2024-02 与 2023-06 相比，London-wide ULEZ 平均每日检测到的 non-compliant vehicles 减少 90,000，降幅 53%。":
    "The London-wide ULEZ six month report shows the London-wide compliance rate of subject vehicles rose from 91.6% in June 2023 to 96.2% after six months. Cars reached 97.1%, vans 88.9%. | Comparing February 2024 with June 2023, the average number of non-compliant vehicles detected per day London-wide fell by 90,000, a 53% reduction.",

  "6 个月报告给出 NOx emissions 和 NO2 concentrations 两类结果：outer London cars/vans NOx emissions 相对 no-ULEZ scenario 分别低 13% 和 7%；outer London roadside NO2 concentrations 在首 6 个月 up to 4.4% lower。 | 非合规且未豁免车辆在 ULEZ 内行驶需支付每日 £12.50。 | YouGov/ITV 2023-08-09 至 2023-08-14 调查显示：Londoners 47% 支持扩区、42% 反对；inner London 支持 62% vs 反对 26%；outer London 反对 51% vs 支持 38%。":
    "The six month report covers NOx emissions and NO2 concentrations: outer London car and van NOx emissions were 13% and 7% lower respectively than the no-ULEZ scenario; outer London roadside NO2 concentrations were up to 4.4% lower over the first six months. | Non-compliant, non-exempt vehicles driving within the ULEZ pay a £12.50 daily charge. | YouGov/ITV polling (2023-08-09 to 2023-08-14) found 47% of Londoners supported the expansion and 42% opposed; inner London 62% support vs 26% oppose; outer London 51% oppose vs 38% support.",

  // --- case_graph.json / live-API status enums ---
  已确认: "Confirmed",
  待核实: "Pending verification",
  未找到: "Not found",

  // --- live policy API truth_set_status.message (and the report.py
  // confidence_notes fallback variant with a trailing ideographic stop) ---
  "无历史回测数据，仅提供影响分析": "No historical backtest data — impact analysis only",
  "无历史回测数据，仅提供影响分析。": "No historical backtest data — impact analysis only.",
};

export function displayEnglish(text: string): string {
  return DISPLAY_TRANSLATIONS[text] ?? text;
}
