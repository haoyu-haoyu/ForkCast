# ULEZ Human Adjudication Sheet

Case: `ulez_2023_expansion`
Purpose: human grading of the cached blind prediction against source-backed truth-set evidence.

Instructions:

- Read the cached blind prediction excerpt and the linked truth-set evidence for each rule.
- Mark exactly one decision per rule: HIT, PARTIAL, or MISS.
- Do not use the automated scorer verdicts while completing this sheet.
- The excerpts below are copied from `blind_prediction.json`; no post-hoc prediction text is added here.

Decision key: `[ ] HIT   [ ] PARTIAL   [ ] MISS`

## R1

Question: Did the blind prediction identify stronger outer-London opposition than inner-London support?

Cached blind prediction excerpt:

```json
{
  "group_reactions": [
    {
      "group_id": "stakeholder_outer_london_residents",
      "direction": "oppose",
      "intensity": "high",
      "rationale": "Direct daily charge for non-compliant vehicles, perceived as unfair tax on car-dependent suburbs with limited public transport alternatives."
    },
    {
      "group_id": "stakeholder_inner_london_residents",
      "direction": "support",
      "intensity": "moderate",
      "rationale": "Already experienced benefits of existing ULEZ, support expansion for cleaner air and reduced traffic, but less personally affected by new charge."
    },
    {
      "group_id": "stakeholder_conservative_party",
      "direction": "oppose",
      "intensity": "high",
      "rationale": "Sees electoral opportunity in mobilizing outer London and business discontent; can frame as 'war on motorists' and Labour overreach."
    },
    {
      "group_id": "stakeholder_labour_party",
      "direction": "support",
      "intensity": "moderate",
      "rationale": "Supports environmental goals but faces electoral risk in outer London constituencies; must manage backlash from affected voters."
    }
  ]
}
```

Relevant truth-set facts and evidence:

### C1_public_opinion_distribution

- Fact: YouGov/ITV 2023-08-09 至 2023-08-14 调查显示：Londoners 47% 支持扩区、42% 反对；inner London 支持 62% vs 反对 26%；outer London 反对 51% vs 支持 38%。
- Current confidence status: `已确认`

Sources:
- Source 1: YouGov - Londoners split on ULEZ expansion
  - URL: https://yougov.com/en-gb/articles/46024-londoners-split-ulez-expansion
  - Quote: 47% supporting ... while 42% are opposed
- Source 2: YouGov - Londoners split on ULEZ expansion
  - URL: https://yougov.com/en-gb/articles/46024-londoners-split-ulez-expansion
  - Quote: outer London ... 51% to 38%

Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS

Reviewer notes:


## R2

Question: Did the blind prediction single out van drivers, tradespeople, or small businesses as highly affected?

Cached blind prediction excerpt:

```json
{
  "group_reactions": [
    {
      "group_id": "stakeholder_van_drivers_tradespeople",
      "direction": "oppose",
      "intensity": "very high",
      "rationale": "Daily charge directly impacts operating costs and livelihoods; vehicle replacement is expensive and disruptive for small businesses."
    }
  ],
  "ranked_opposition_groups": [
    {
      "group_id": "stakeholder_van_drivers_tradespeople",
      "rank": 1,
      "rationale": "Highest direct economic impact per actor; daily charge is a recurring cost that threatens livelihoods, leading to sustained and vocal opposition."
    },
    {
      "group_id": "stakeholder_ulez_opponents_radical",
      "rank": 2,
      "rationale": "Motivated to disrupt enforcement and gain media attention; can amplify opposition beyond their numbers through protests and civil disobedience."
    },
    {
      "group_id": "stakeholder_low_income_households",
      "rank": 3,
      "rationale": "High burden relative to income, but less organized than business groups; may be mobilized by political opponents."
    },
    {
      "group_id": "stakeholder_outer_london_residents",
      "rank": 4,
      "rationale": "Large group with diffuse costs; opposition is broad but less intense per individual than tradespeople or activists."
    },
    {
      "group_id": "stakeholder_conservative_party",
      "rank": 5,
      "rationale": "Political opponent leveraging existing discontent; opposition is strategic and electoral, not directly affected by the charge."
    }
  ]
}
```

Relevant truth-set facts and evidence:

### D1_six_month_compliance_rate_change

- Fact: London-wide ULEZ 6 个月报告显示，subject vehicles 的 London-wide compliance rate 从 2023-06 的 91.6% 上升到 6 个月后的 96.2%。Cars 为 97.1%，vans 为 88.9%。
- Current confidence status: `已确认`

Sources:
- Source 1: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 96.2 per cent, up from 91.6 per cent
- Source 2: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 97.1 per cent of cars and 88.9 per cent of vans

Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS

Reviewer notes:


## R3

Question: Did the blind prediction identify political salience/electoral risk without claiming to predict the election result?

Cached blind prediction excerpt:

```json
{
  "political_consequences": [
    {
      "electoral_risk_for_advocates": "high",
      "rationale": "The policy creates a clear wedge issue in outer London constituencies where Labour holds marginal seats. The concentrated burden on small businesses and car-dependent voters can be exploited by the Conservative Party and local opponents, increasing electoral risk for the Mayor and Labour Party in the next London mayoral and local elections.",
      "salience_level": "high",
      "key_swing_groups": [
        "stakeholder_outer_london_residents",
        "stakeholder_van_drivers_tradespeople",
        "stakeholder_low_income_households"
      ]
    }
  ]
}
```

Relevant truth-set facts and evidence:

### B1_uxbridge_by_election_result

- Fact: 2023-07-20 Uxbridge and South Ruislip by-election 为 Conservative hold；Steve Tuckwell 13,965 票、45.2%；Danny Beales 13,470 票、43.6%；多数票 495；投票率 46.1%。
- Current confidence status: `已确认`

Sources:
- Source 1: UK Parliament - Uxbridge and South Ruislip election result
  - URL: https://members.parliament.uk/constituency/3817/election/412
  - Quote: Conservative Hold
- Source 2: UK Parliament - Uxbridge and South Ruislip election result
  - URL: https://members.parliament.uk/constituency/3817/election/412
  - Quote: Majority 495

### B2_ulez_as_key_by_election_issue

- Fact: 可靠分析/报道将 ULEZ 扩区与 Uxbridge 补选结果直接关联：Institute for Government 认为 ULEZ plans 是 Labour narrow loss 的 key factor；YouGov 文章称 ULEZ 被 held responsible for Labour’s failure to win the seat。
- Current confidence status: `已确认`

Sources:
- Source 1: Institute for Government - Will the Uxbridge by-election prove a crossroads for net zero?
  - URL: https://www.instituteforgovernment.org.uk/comment/uxbridge-crossroads-net-zero
  - Quote: key factor in Labour's narrow loss
- Source 2: YouGov - Londoners split on ULEZ expansion
  - URL: https://yougov.com/en-gb/articles/46024-londoners-split-ulez-expansion
  - Quote: held responsible for Labour’s failure

Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS

Reviewer notes:


## R4

Question: Did the blind prediction identify enforcement resistance, camera backlash, sabotage, or vandalism risk?

Cached blind prediction excerpt:

```json
{
  "secondary_reactions": [
    {
      "group_id": "stakeholder_labour_party",
      "reaction": "internal tension",
      "rationale": "Balancing environmental credibility with electoral survival in outer London; may push for mitigation measures like scrappage scheme expansion."
    },
    {
      "group_id": "stakeholder_transport_for_london",
      "reaction": "operational strain",
      "rationale": "Enforcement requires camera installation and data processing; protests may target cameras, increasing maintenance costs."
    },
    {
      "group_id": "stakeholder_london_mayor",
      "reaction": "reputational risk",
      "rationale": "Policy success or failure directly tied to mayoral legacy; may need to offer concessions or additional support to affected groups to reduce backlash."
    }
  ]
}
```

Relevant truth-set facts and evidence:

### C2_camera_vandalism_and_enforcement_resistance

- Fact: Metropolitan Police FOI 显示 2023-08-01 至 2023-10-15 期间记录 416 起 ULEZ-related offences：59 theft、357 arson and criminal damage；property status 中 74 stolen、358 damaged。Sky/ITV 报道说明部分破坏者自称 Blade Runners。
- Current confidence status: `已确认`

Sources:
- Source 1: Metropolitan Police FOI - Crimes relating to ULEZ cameras from August to October 2023
  - URL: https://www.met.police.uk/foi-ai/metropolitan-police/disclosure-2023/november-2023/crimes-ulez-cameras-august-october2023/
  - Quote: Grand Total 416
- Source 2: Metropolitan Police FOI downloadable XLSX
  - URL: https://www.met.police.uk/SysSiteAssets/foi-media/metropolitan-police/disclosure_2023/november_2023/crimes-ulez-cameras-august-october2023.xlsx
  - Quote: Stolen 74; Damaged 358
- Source 3: Sky News - anti-ULEZ suspect / blade runners
  - URL: https://news.sky.com/story/police-release-image-of-anti-ulez-suspect-as-hundreds-of-cameras-damaged-or-stolen-12942206
  - Quote: describe themselves as "blade runners"

Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS

Reviewer notes:


## R5

Question: Did the blind prediction identify short-term backlash plus longer-term adaptation or compliance improvement?

Cached blind prediction excerpt:

```json
{
  "time_dynamics": [
    {
      "short_term_1_to_6_months": "High protest activity and media coverage; enforcement challenges from radical opponents; initial compliance costs dominate public discourse.",
      "medium_term_6_to_18_months": "Gradual compliance as some replace vehicles; opposition may persist among those unable to afford replacement; political campaigns use ULEZ as key issue.",
      "long_term_18_months_plus": "If air quality improvements become measurable, support may grow among inner London residents; but resentment in outer London may remain entrenched, especially if economic benefits are not visible."
    }
  ]
}
```

Relevant truth-set facts and evidence:

### D1_six_month_compliance_rate_change

- Fact: London-wide ULEZ 6 个月报告显示，subject vehicles 的 London-wide compliance rate 从 2023-06 的 91.6% 上升到 6 个月后的 96.2%。Cars 为 97.1%，vans 为 88.9%。
- Current confidence status: `已确认`

Sources:
- Source 1: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 96.2 per cent, up from 91.6 per cent
- Source 2: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 97.1 per cent of cars and 88.9 per cent of vans

### D2_non_compliant_vehicle_count_change

- Fact: 2024-02 与 2023-06 相比，London-wide ULEZ 平均每日检测到的 non-compliant vehicles 减少 90,000，降幅 53%。
- Current confidence status: `已确认`

Sources:
- Source 1: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 90,000 fewer non-compliant vehicles
- Source 2: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 53 per cent reduction

Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS

Reviewer notes:


## R6

Question: Did the blind prediction capture both air-quality/health benefits and distributional burden?

Cached blind prediction excerpt:

```json
{
  "benefit_burden_balance": [
    {
      "beneficiaries": [
        "stakeholder_inner_london_residents"
      ],
      "burdened": [
        "stakeholder_outer_london_residents",
        "stakeholder_van_drivers_tradespeople",
        "stakeholder_low_income_households"
      ],
      "imbalance_severity": "high",
      "rationale": "Benefits (cleaner air, health) are diffuse and long-term, accruing mainly to inner London. Burdens (daily charge, vehicle replacement cost) are immediate, concentrated, and fall on outer London residents, small businesses, and low-income households, creating a classic concentrated-costs/diffuse-benefits political dynamic that fuels opposition."
    }
  ]
}
```

Relevant truth-set facts and evidence:

### D3_air_quality_and_emissions_changes

- Fact: 6 个月报告给出 NOx emissions 和 NO2 concentrations 两类结果：outer London cars/vans NOx emissions 相对 no-ULEZ scenario 分别低 13% 和 7%；outer London roadside NO2 concentrations 在首 6 个月 up to 4.4% lower。
- Current confidence status: `已确认`

Sources:
- Source 1: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 13 per cent and 7 per cent lower
- Source 2: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: up to 4.4 per cent lower
- Source 3: London City Hall - London-wide ULEZ Six Month Report
  - URL: https://www.london.gov.uk/programmes-strategies/environment-and-climate-change/environment-and-climate-change-publications/london-wide-ulez-six-month-report
  - Quote: 21 per cent lower in outer London

### A2_daily_charge

- Fact: 非合规且未豁免车辆在 ULEZ 内行驶需支付每日 £12.50。
- Current confidence status: `已确认`

Sources:
- Source 1: Transport for London - Ultra Low Emission Zone
  - URL: https://tfl.gov.uk/modes/driving/ultra-low-emission-zone
  - Quote: pay a £12.50 daily charge

### C1_public_opinion_distribution

- Fact: YouGov/ITV 2023-08-09 至 2023-08-14 调查显示：Londoners 47% 支持扩区、42% 反对；inner London 支持 62% vs 反对 26%；outer London 反对 51% vs 支持 38%。
- Current confidence status: `已确认`

Sources:
- Source 1: YouGov - Londoners split on ULEZ expansion
  - URL: https://yougov.com/en-gb/articles/46024-londoners-split-ulez-expansion
  - Quote: 47% supporting ... while 42% are opposed
- Source 2: YouGov - Londoners split on ULEZ expansion
  - URL: https://yougov.com/en-gb/articles/46024-londoners-split-ulez-expansion
  - Quote: outer London ... 51% to 38%

Human decision: [ ] HIT   [ ] PARTIAL   [ ] MISS

Reviewer notes:
