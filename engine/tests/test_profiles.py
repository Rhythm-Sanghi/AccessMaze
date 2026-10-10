import asyncio
import json

import pytest
from test_website_policy import website

from accessmaze.models import Journey, ProfileInput, ProjectInput
from accessmaze.retests import compare_runs
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store


def test_profiles_persist_independently_of_journey_snapshots(store, project):
    p = project()
    saved = store.save_profile(ProfileInput(name="Keyboard", profile={"layout_zoom_percent": 200}))
    restarted = Store(store.root)
    assert restarted.profiles() == [saved]
    restarted.save_profile(
        ProfileInput(name="Pointer", profile={"keyboard_only": False}), saved["id"]
    )
    assert restarted.profiles()[0]["profile"]["keyboard_only"] is False
    assert restarted.project(p["id"]) == p
    restarted.delete_profile(saved["id"])
    assert restarted.profiles() == []


@pytest.mark.browser
def test_profiles_change_real_browser_conditions_and_outcomes(store, fixtures, axe_path):
    async def exercise():
        html = """<html lang=en><title>Profile test</title><main><h1>Base</h1>
<label>Name<input></label>
<div role=button onclick="document.querySelector('h1').textContent='Done'">Proceed</div>
<script>window.addEventListener('offline',()=>document.body.dataset.offline='yes');
window.addEventListener('online',()=>document.body.dataset.recovered='yes');</script></main>"""
        with website({"/": (200, {"Content-Type": "text/html"}, html)}) as (url, hits):
            journey = Journey(
                name="Profiles",
                target=url,
                allow_local=True,
                tab_budget=4,
                steps=[
                    {"id": "open", "action": "navigate"},
                    {
                        "id": "name",
                        "action": "fill",
                        "target": {"role": "textbox", "name": "Name"},
                        "value": "Synthetic name",
                    },
                    {
                        "id": "retained",
                        "action": "assert_value",
                        "target": {"role": "textbox", "name": "Name"},
                        "value": "Synthetic name",
                    },
                    {
                        "id": "base",
                        "action": "assert_visible",
                        "target": {"role": "heading", "name": "Base"},
                    },
                    {
                        "id": "proceed",
                        "action": "activate",
                        "effect": True,
                        "target": {"role": "button", "name": "Proceed"},
                    },
                    {
                        "id": "done",
                        "action": "assert_visible",
                        "target": {"role": "heading", "name": "Done"},
                    },
                ],
                profile={
                    "layout_zoom_percent": 200,
                    "reduced_motion": True,
                    "network_latency_ms": 100,
                    "disconnect_after_step": "name",
                    "reconnect_after_step": "base",
                    "audit_semantics": True,
                },
            )
            project = store.save_project(ProjectInput(name="Conditions", journey=journey))
            keyboard = await execute(
                store, project["id"], journey, RunControl(), fixtures, axe_path
            )
            assert keyboard["outcome"]["status"] == "blocked"
            assert [s["action"] for s in keyboard["steps"]][2:6] == [
                "offline",
                "assert_value",
                "assert_visible",
                "online",
            ]
            assert any(not n["observation"]["online"] for n in keyboard["nodes"])
            assert all(n["observation"]["reduced_motion"] for n in keyboard["nodes"])
            assert keyboard["nodes"][0]["observation"]["viewport"]["width"] == 640
            assert keyboard["nodes"][0]["observation"]["viewport"]["device_pixel_ratio"] == 2
            journey.profile.keyboard_only = False
            journey.profile.layout_zoom_percent = 100
            pointer = await execute(store, project["id"], journey, RunControl(), fixtures, axe_path)
            assert pointer["outcome"]["status"] == "completed"
            assert pointer["steps"][-1]["id"] == "profile-audit"
            assert "audit" in pointer["steps"][-1]
            comparison = compare_runs(keyboard, pointer)
            assert not comparison["comparable"]
            assert "profile" in comparison["changed_conditions"]
            assert comparison["previous_outcome"]["status"] == "blocked"
            assert comparison["current_outcome"]["status"] == "completed"
            assert "Synthetic name" not in json.dumps(pointer)
            assert len(hits) >= 2

    asyncio.run(exercise())


@pytest.mark.browser
def test_profile_focus_check_is_an_actual_assertion(store, fixtures, axe_path):
    from accessmaze.models import Step
    from accessmaze.templates import template

    async def exercise():
        journey = template()
        journey.steps = [
            journey.steps[0],
            journey.steps[1],
            Step(
                id="base",
                action="assert_visible",
                target={"role": "textbox", "name": "Applicant name"},
            ),
        ]
        journey.profile.focus_target = journey.steps[1].target
        p = store.save_project(ProjectInput(name="Focus condition", journey=journey))
        result = await execute(store, p["id"], journey, RunControl(), fixtures, axe_path)
        assert result["steps"][-1]["id"] == "profile-focus"
        assert result["steps"][-1]["status"] == "passed"
        assert result["outcome"]["status"] == "completed"

    asyncio.run(exercise())


def test_version_two_migration_keeps_runs_and_partial_discovery(store, project):
    from uuid import uuid4

    from accessmaze.storage import now

    p = project()
    run_id = str(uuid4())
    store.save_run(
        {
            "id": run_id,
            "project_id": p["id"],
            "journey": p["journey"],
            "status": "awaiting_approval",
            "started_at": now(),
            "steps": [],
            "findings": [],
            "approval": {"id": "old"},
            "exploration": {
                "stop_reason": "running",
                "actions": [{"status": "running"}],
                "pending_branches": [{"state_id": "observed", "path": ["unvisited"]}],
            },
        }
    )
    with store.connect() as db:
        db.execute("DROP TABLE profiles")
        db.execute("PRAGMA user_version=2")
    migrated = Store(store.root)
    migrated.recover()
    partial = migrated.run(run_id)
    assert partial["status"] == "interrupted"
    assert "approval" not in partial
    assert partial["exploration"]["actions"][0]["status"] == "interrupted"
    assert partial["exploration"]["pending_branches"][0]["state_id"] == "observed"
    assert partial["outcome"]["status"] == "incomplete"
    assert migrated.profiles() == []
    assert migrated.project(p["id"])["journey"] == p["journey"]
