# CC 2003 Truth-Set Human Verification Checklist

Case: `london_congestion_charge_2003` - London Congestion Charge 2003
Current verification policy: `DRAFT — PENDING HUMAN VERIFICATION`
Current headline_excluded: `True`

Instructions for the human reviewer:

- Use only the linked source URL and quoted text for each item.
- Mark exactly one decision per fact: CONFIRM, REJECT, or EDIT.
- Do not promote any `待核实` fact to `已确认` unless the reviewer explicitly marks CONFIRM.
- If any scored fact remains unconfirmed, keep `headline_excluded=true` and exclude this case from headline metrics.

Decision key: `[ ] CONFIRM   [ ] REJECT   [ ] EDIT: <write corrected fact/status>`

## 1. CC_A1_start_date_and_aim

- Category: A. Policy baseline
- Requested item: Introduction date and stated aim
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL describes the central London congestion charging scheme as introduced on 17 February 2003, with a primary aim of reducing traffic congestion in and around the charging zone.
- Value JSON: `{"introduced_on": "2003-02-17"}`
- Notes: Needs human page-level verification before use as final ground truth.

Sources:
- Source 1 name: TfL Second Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/impacts-monitoring-report-2.pdf
  - Quote: The central London congestion charging scheme was introduced on 17 February 2003. The primary aim of the scheme is to reduce traffic congestion in and around the charging zone.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 2. CC_A2_charge_and_hours

- Category: A. Policy baseline
- Requested item: Initial daily charge and operating hours
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL describes the initial congestion charge as a £5 daily charge between 0700 and 1830, Monday to Friday, excluding weekends and public holidays.
- Value JSON: `{"daily_charge_gbp": 5, "days": "Monday-Friday", "hours": "0700-1830"}`
- Notes: Draft baseline fact for scaffold only.

Sources:
- Source 1 name: TfL Second Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/impacts-monitoring-report-2.pdf
  - Quote: The congestion charge is a £5 daily charge for driving or parking a vehicle on public roads within the congestion charging zone between 0700 and 1830, Monday to Friday, excluding weekends and public holidays.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 3. CC_A3_zone_scope

- Category: A. Policy baseline
- Requested item: Charging zone scope
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL describes the central London congestion charging zone as covering 22 square kilometres in the heart of London.
- Value JSON: `{"area_square_km": 22}`
- Notes: Draft baseline fact for scaffold only.

Sources:
- Source 1 name: TfL Second Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/impacts-monitoring-report-2.pdf
  - Quote: It covers 22 square kilometres in the heart of London, including centres of government, law, business, finance and entertainment.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 4. CC_D1_congestion_reduction

- Category: D. Policy outcome
- Requested item: Congestion reduction direction
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL's third annual monitoring report says reductions to delays inside the charging zone remained around 30 percent compared with 2002 pre-charging conditions.
- Value JSON: `{"direction": "down", "reported_reduction_percent": 30}`
- Notes: Draft outcome fact, not yet manually verified.

Sources:
- Source 1 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: Taking an average of all available post-charging congestion surveys, reductions to delays inside the charging zone during charging hours remain at around 30 percent compared to pre-charging conditions in 2002.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 5. CC_D2_traffic_entering_reduction

- Category: D. Policy outcome
- Requested item: Traffic entering zone direction
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL's third annual monitoring report says 2004 traffic entering the charging zone during charging hours remained 18 percent below 2002 pre-charging levels.
- Value JSON: `{"direction": "down", "reported_reduction_percent": 18}`
- Notes: Draft outcome fact, not yet manually verified.

Sources:
- Source 1 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: The total volume of traffic entering the charging zone during charging hours in 2004 was identical to 2003, continuing to represent a reduction of 18 percent against pre-charging levels in 2002.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 6. CC_D3_public_transport_adaptation

- Category: D. Policy outcome
- Requested item: Bus and public transport adaptation
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL reports bus reliability and journey-time benefits, and says public transport accommodated displaced car users.
- Value JSON: `{"direction": "improved_or_adapted"}`
- Notes: Draft outcome fact, not yet manually verified.

Sources:
- Source 1 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: Bus services continue to benefit from significant improvements in reliability and journey time, particularly within the zone, but also outside it.
- Source 2 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: Public transport continues to successfully accommodate displaced car users alongside ongoing improvements to bus services throughout London.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 7. CC_D4_business_impact_neutral

- Category: D. Policy outcome
- Requested item: Business and economic impact direction
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL reports a broadly neutral overall business impact, while noting sectoral evidence was inconclusive.
- Value JSON: `{"direction": "broadly_neutral"}`
- Notes: Draft outcome fact, not yet manually verified.

Sources:
- Source 1 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: Results from an extensive research programme suggest that congestion charging has had a broadly neutral impact on overall business performance in the charging zone.
- Source 2 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: Sectoral evidence from the business performance research programme is inconclusive.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:


## 8. CC_D5_revenue_bus_services

- Category: D. Policy outcome
- Requested item: Revenue use
- Current status: `待核实`
- Headline excluded: `True`
- Fact: Draft: TfL reports over £90 million in provisional net revenues for 2004/5, spent largely on improved bus services within London.
- Value JSON: `{"direction": "revenue_for_transport", "reported_net_revenue_gbp_million": 90}`
- Notes: Draft outcome fact, not yet manually verified.

Sources:
- Source 1 name: TfL Third Annual Monitoring Report
  - Type: official TfL PDF
  - URL: https://content.tfl.gov.uk/central-london-congestion-charging-impacts-monitoring-third-annual-report.pdf
  - Quote: The scheme provisionally generated net revenues of over £90 million in 2004/5, which have been spent largely on improved bus services within London.

Human decision: [ ] CONFIRM   [ ] REJECT   [ ] EDIT: ________________________________

Reviewer notes:
