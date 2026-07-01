from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_NAMES = [
    "truth_set.schema.json",
    "case_graph.schema.json",
    "agents.schema.json",
    "simulation_config.schema.json",
    "audit_manifest.schema.json",
    "report_claims.schema.json",
    "blind_prediction.schema.json",
]


def test_phase1_core_schemas_exist_and_are_valid_json_schema() -> None:
    for schema_name in SCHEMA_NAMES:
        schema = json.loads(Path("schemas", schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_existing_ulez_truth_set_validates_against_schema() -> None:
    schema = json.loads(Path("schemas/truth_set.schema.json").read_text(encoding="utf-8"))
    truth_set = json.loads(Path("data/cases/ulez_2023/truth_set.json").read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(truth_set)
