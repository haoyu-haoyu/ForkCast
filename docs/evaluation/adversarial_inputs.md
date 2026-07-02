# Adversarial Input Extraction Suite

This is an observed-behavior report. It records what the current extraction stage does; it does not claim production robustness.

## Summary

- Fixture count: `5`
- Mock crashes: `0`
- Mock schema-valid outputs: `5`
- Real LLM mode statuses: `{"schema_valid": 5}`

## Results

| Fixture | Chars | Source | Mock status | Mock schema | Mock notes | Real LLM status | Real notes |
|---|---:|---|---|---|---|---|---|
| long_public_consultation.txt | 57945 | https://www.gov.uk/government/consultations/creating-a-smokefree-generation-and-tackling-youth-vaping/creating-a-smokefree-generation-and-tackling-youth-vaping-your-views | schema_valid | True | long_document_extraction_truncated:low_confidence_long_input | schema_valid | smokefree_generation_youth_vaping_consultation |
| contradictory_policy.txt | 815 |  | schema_valid | True | access_rule_contradiction:contradiction_flag; funding_rule_contradiction:contradiction_flag | schema_valid | contradictory_parking_clean_air_pilot |
| off_topic_junk.txt | 342 |  | schema_valid | True | input_not_policy:low_confidence_non_policy | schema_valid | fixture_empty_policy_001 |
| near_empty.txt | 8 |  | schema_valid | True | insufficient_policy_detail:low_confidence_insufficient_input | schema_valid | policy_case_001 |
| non_policy_technical.txt | 684 |  | schema_valid | True | not_public_policy:low_confidence_non_policy | schema_valid | tls_handshake_implementation_notes |

## Observed Behavior

- The mock extraction path did not crash on any adversarial fixture and produced schema-valid outputs for all five.
- Mock off-topic, near-empty and non-policy technical inputs produce schema-valid fallback case graphs with low-confidence/non-policy assumption statuses, rather than a hard rejection.
- In the recorded real-LLM run, DeepSeek also returned schema-valid outputs for all five fixtures; it did not surface confidence flags for the off-topic, near-empty or non-policy technical cases under the current schema.
- Current extraction therefore behaves permissively: adversarial or underspecified inputs become case graphs instead of cleanly stopping for human clarification.
- The long GOV.UK consultation fixture is over 50k characters and is useful for prompt/context stress testing; production ingestion still needs chunking and page-level provenance.
- Any real-LLM status above is the actual run result from the current environment. A skipped real-LLM status means no key was available or the run was intentionally skipped by flag.
