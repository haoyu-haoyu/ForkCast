# Impact Report: london_congestion_charge_2003

simulation is decision support, not deterministic forecast

Mode: `mock_demo_visualization`

This impact report is generated from mock interaction events for dashboard demonstration. Historical backtest credibility is based on blind_prediction.json, not these mock events.

## System Signals
- R5: short-term opposition coexists with longer-term behavioural adaptation and improving compliance

## Risk Timeline
- short_term: outer-London and van-dependent groups show strong backlash (medium)
- implementation_period: political salience and enforcement backlash require active management (medium)
- longer_term: behavioural adaptation and compliance improvement emerge over time (medium)

## Mitigation Options
- targeted support for van-dependent small businesses: reduces the highest-impact economic pressure without changing stakeholder weights automatically
- low-income household transition assistance: addresses distributional burden while preserving air-quality objectives
- visible enforcement legitimacy and camera-protection plan: responds to enforcement backlash without escalating automated actions

## Claims Audit
| Claim | Provenance | Evidence pointer |
|---|---|---|
| short-term opposition coexists with longer-term behavioural adaptation and improving compliance | INFERRED-FROM-DOCUMENT | simulation_events.signals.behavioural_adaptation |
| outer-London and van-dependent groups show strong backlash | INFERRED-FROM-DOCUMENT | simulation_events.signals; risk_timeline.short_term |
| political salience and enforcement backlash require active management | INFERRED-FROM-DOCUMENT | simulation_events.signals; risk_timeline.implementation_period |
| behavioural adaptation and compliance improvement emerge over time | INFERRED-FROM-DOCUMENT | simulation_events.signals; risk_timeline.longer_term |
| reduces the highest-impact economic pressure without changing stakeholder weights automatically | MODEL-PRIOR | impact_report.mitigation_options[0] |
| addresses distributional burden while preserving air-quality objectives | MODEL-PRIOR | impact_report.mitigation_options[1] |
| responds to enforcement backlash without escalating automated actions | MODEL-PRIOR | impact_report.mitigation_options[2] |
