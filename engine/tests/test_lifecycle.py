import asyncio

import pytest

from accessmaze.models import Journey, Step
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template


@pytest.mark.browser
def test_modal_focus_failure_is_observed(store, project, fixtures, axe_path):
    p = project("modal")
    result = asyncio.run(
        execute(store, p["id"], template("modal"), RunControl(), fixtures, axe_path)
    )
    assert result["findings"][0]["rule"] == "modal-focus-escape"
    assert any(
        c["focused"] and c["name"] == "Application help"
        for c in result["nodes"][-1]["observation"]["controls"]
    )


@pytest.mark.browser
def test_dynamic_conditional_application_submits(store, project, fixtures, axe_path):
    p = project("conditional")
    result = asyncio.run(
        execute(store, p["id"], template("conditional"), RunControl(), fixtures, axe_path)
    )
    assert result["status"] == "completed_with_limitations"
    assert not result["findings"]
    assert "Application submitted" in result["nodes"][-1]["observation"]["headings"]


@pytest.mark.browser
def test_pause_is_between_steps_and_resume_completes(store, project, fixtures, axe_path):
    async def exercise():
        p = project()
        journey = template()
        journey.steps.insert(1, Step(id="delay", action="wait", value="400"))
        control = RunControl()
        task = asyncio.create_task(execute(store, p["id"], journey, control, fixtures, axe_path))
        for _ in range(100):
            await asyncio.sleep(0.05)
            runs = store.runs(p["id"])
            if runs and any(s["id"] == "delay" for s in runs[0]["steps"]):
                control.pause.set()
                break
        else:
            pytest.fail("Delay step never started")
        for _ in range(100):
            await asyncio.sleep(0.05)
            paused = store.runs(p["id"])[0]
            if paused["status"] == "paused":
                break
        else:
            pytest.fail("Pause was not observed")
        assert paused["steps"][-1]["id"] == "delay"
        assert paused["steps"][-1]["status"] == "passed"
        control.pause.clear()
        # Completion uses the configured run budget; cancellation responsiveness has its own test.
        return await asyncio.wait_for(task, journey.max_seconds + 5)

    result = asyncio.run(exercise())
    assert result["status"] == "completed_with_limitations"


def test_schema_migration_preserves_projects(store, project):
    p = project()
    with store.connect() as db:
        db.execute("DROP TABLE retests")
        db.execute("PRAGMA user_version=1")
    from accessmaze.storage import Store

    migrated = Store(store.root)
    assert Journey.model_validate(migrated.project(p["id"])["journey"]).name == template().name
    with migrated.connect() as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM retests").fetchone()[0] == 0
