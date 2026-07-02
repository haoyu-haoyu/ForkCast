Generate a structured policy impact report for a decision-support system.

Return one JSON object and no prose. Do not invent source-backed historical outcomes, exact percentages, election results, prices, offence counts, or air-quality measurements.
If the supplied policy context does not contain historical evidence, mark confidence conservatively and explain that no truth_set was supplied.

Required keys:
- stakeholder_impact_matrix
- risk_timeline
- mitigation_options
- confidence_notes
- claims_audit_table

Stakeholder impact rows require:
- stakeholder_id
- name
- impact_level
- opposition_intensity
- qualitative_signal

Risk timeline rows require:
- stage
- signal
- risk_level

Mitigation rows require:
- option
- rationale

Claims audit rows require:
- id
- claim
- provenance_class: one of DOCUMENT-CITED, INFERRED-FROM-DOCUMENT, MODEL-PRIOR
- evidence_pointer
- evidence_fact_ids
- source_artifact
- confidence

Safety rules:
- This is decision support, not deterministic forecast.
- Personas are archetypes only.
- Do not suggest automatic on-chain action.
- Do not change stakeholder weights automatically.
