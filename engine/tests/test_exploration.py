import asyncio

import pytest

from accessmaze.models import Exploration
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template

pytestmark = pytest.mark.browser


def test_discovery_records_real_branch_actions_and_bounded_frontier(
    store, project, fixtures, axe_path
):
    p = project("accessible")
    journey = template("accessible")
    journey.exploration = Exploration(enabled=True, max_depth=2, max_actions=65)
    result = asyncio.run(execute(store, p["id"], journey, RunControl(), fixtures, axe_path))
    assert result["status"] == "completed_with_limitations"
    progress = result["exploration"]
    assert len(progress["actions"]) <= 65
    assert progress["stop_reason"] in {"depth-bound", "action-budget", "frontier-exhausted"}
    assert {a["target"]["name"] for a in progress["actions"] if a["kind"] == "explore"} >= {
        "Choose date",
        "Review application",
        "Start again",
    }
    assert any(e["step_id"].startswith("explore-") for e in result["edges"])
    assert any(e["cycle"] for e in result["edges"])
    assert progress["pending_branches"]


def test_budget_counts_replay_and_keeps_unexplored_frontier(store, project, fixtures, axe_path):
    p = project()
    journey = template()
    journey.exploration = Exploration(enabled=True, max_actions=2)
    result = asyncio.run(execute(store, p["id"], journey, RunControl(), fixtures, axe_path))
    assert len(result["exploration"]["actions"]) == 2
    assert result["exploration"]["stop_reason"] == "action-budget"
    assert result["exploration"]["pending_branches"]
