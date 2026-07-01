from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OasisProbeDecision:
    status: str
    can_run_live: bool
    message: str


def evaluate_oasis_probe(import_ok: bool, has_api_key: bool, live_enabled: bool) -> OasisProbeDecision:
    if not import_ok:
        return OasisProbeDecision(
            status="dependency_failed",
            can_run_live=False,
            message="camel-oasis could not be imported; use mock simulation mode.",
        )
    if not has_api_key:
        return OasisProbeDecision(
            status="missing_api_key",
            can_run_live=False,
            message="camel-oasis imports, but OPENAI_API_KEY is missing; use mock simulation mode.",
        )
    if not live_enabled:
        return OasisProbeDecision(
            status="live_disabled",
            can_run_live=False,
            message="camel-oasis imports and API key exists, but live run is disabled to avoid unplanned LLM cost.",
        )
    return OasisProbeDecision(
        status="ready_for_live_probe",
        can_run_live=True,
        message="camel-oasis imports and live probe is explicitly enabled.",
    )
