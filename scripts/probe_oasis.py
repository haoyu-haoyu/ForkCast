from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

from policy_impact_sandbox.simulation.oasis_probe import evaluate_oasis_probe


REDDIT_PROFILE_URL = "https://raw.githubusercontent.com/camel-ai/oasis/main/data/reddit/user_data_36.json"


def main() -> int:
    import_error: Exception | None = None
    try:
        import oasis  # noqa: F401
        from oasis import ActionType, LLMAction, ManualAction, generate_reddit_agent_graph  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on optional dependency state
        import_error = exc

    decision = evaluate_oasis_probe(
        import_ok=import_error is None,
        has_api_key=bool(os.getenv("OPENAI_API_KEY")),
        live_enabled=os.getenv("OASIS_RUN_LIVE") == "1",
    )

    print(f"OASIS probe status: {decision.status}")
    print(decision.message)
    if import_error is not None:
        print(f"Import error: {type(import_error).__name__}: {import_error}")
        return 1

    print("Imported official OASIS symbols: oasis, ActionType, LLMAction, ManualAction, generate_reddit_agent_graph")
    if not decision.can_run_live:
        return 2

    try:
        asyncio.run(_run_live_reddit_probe())
    except Exception as exc:  # pragma: no cover - requires live API credentials
        print(f"Live OASIS probe failed: {type(exc).__name__}: {exc}")
        return 3

    print("Live OASIS Reddit-like probe completed.")
    return 0


async def _run_live_reddit_probe() -> None:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType, ModelType
    import oasis
    from oasis import ActionType, LLMAction, ManualAction, generate_reddit_agent_graph

    profile_path = _ensure_reddit_profile()
    openai_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    available_actions = [
        ActionType.LIKE_POST,
        ActionType.DISLIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.LIKE_COMMENT,
        ActionType.DISLIKE_COMMENT,
        ActionType.SEARCH_POSTS,
        ActionType.SEARCH_USER,
        ActionType.TREND,
        ActionType.REFRESH,
        ActionType.DO_NOTHING,
        ActionType.FOLLOW,
        ActionType.MUTE,
    ]
    agent_graph = await generate_reddit_agent_graph(
        profile_path=str(profile_path),
        model=openai_model,
        available_actions=available_actions,
    )

    db_path = Path("runs/phase0_oasis/reddit_probe.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=str(db_path),
    )
    try:
        await env.reset()
        actions_1 = {}
        actions_1[env.agent_graph.get_agent(0)] = [
            ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": "Phase 0 OASIS probe post."},
            ),
            ManualAction(
                action_type=ActionType.CREATE_COMMENT,
                action_args={"post_id": "1", "content": "Phase 0 OASIS probe comment."},
            ),
        ]
        actions_1[env.agent_graph.get_agent(1)] = ManualAction(
            action_type=ActionType.CREATE_COMMENT,
            action_args={"post_id": "1", "content": "Acknowledged."},
        )
        await env.step(actions_1)
        actions_2 = {
            agent: LLMAction()
            for _, agent in env.agent_graph.get_agents([1, 2, 3, 4, 5, 6, 7, 8, 9])
        }
        await env.step(actions_2)
    finally:
        await env.close()


def _ensure_reddit_profile() -> Path:
    profile_dir = Path("data/oasis/reddit")
    profile_dir.mkdir(parents=True, exist_ok=True)
    full_profile_path = profile_dir / "user_data_36.json"
    ten_profile_path = profile_dir / "user_data_10.json"

    if not full_profile_path.exists():
        with urlopen(REDDIT_PROFILE_URL, timeout=30) as response:
            full_profile_path.write_bytes(response.read())

    if not ten_profile_path.exists():
        profiles = json.loads(full_profile_path.read_text(encoding="utf-8"))
        ten_profile_path.write_text(json.dumps(profiles[:10], indent=2), encoding="utf-8")

    return ten_profile_path


if __name__ == "__main__":
    sys.exit(main())
