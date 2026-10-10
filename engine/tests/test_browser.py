import asyncio
import json

import pytest

from accessmaze.models import Journey
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template

pytestmark = pytest.mark.browser


def run_case(store, project, fixtures, axe_path, kind):
    p = project(kind)
    return asyncio.run(
        execute(
            store, p["id"], Journey.model_validate(p["journey"]), RunControl(), fixtures, axe_path
        )
    )


def test_keyboard_blocker_has_observations_screenshot_and_reproduction(
    store, project, fixtures, axe_path
):
    result = run_case(store, project, fixtures, axe_path, "broken")
    assert result["status"] == "failed"
    finding = result["findings"][0]
    assert finding["rule"] == "keyboard-unreachable"
    assert finding["reproduction"] == ["open", "name", "date"]
    assert (store.artifact_dir(result["id"]) / finding["screenshot"]).is_file()
    assert len(result["nodes"]) >= 2
    assert "Test Applicant" not in json.dumps(result)


def test_accessible_journey_completes_without_invented_findings(store, project, fixtures, axe_path):
    result = run_case(store, project, fixtures, axe_path, "accessible")
    assert result["status"] == "completed_with_limitations"
    assert not result["findings"]
    assert all(s["status"] == "passed" for s in result["steps"])


def test_missing_error_association_is_observed(store, project, fixtures, axe_path):
    result = run_case(store, project, fixtures, axe_path, "errors")
    assert result["findings"][0]["rule"] == "error-semantics"
    assert "False" in result["findings"][0]["actual"]


def test_real_network_reconnect_detects_lost_form_value(store, project, fixtures, axe_path):
    result = run_case(store, project, fixtures, axe_path, "recovery")
    assert result["findings"][0]["rule"] == "form-state-lost"
    assert any(not n["observation"]["online"] for n in result["nodes"])
    assert result["nodes"][-1]["observation"]["online"]


def test_both_conditional_paths_and_cycle_are_recorded(store, project, fixtures, axe_path):
    result = run_case(store, project, fixtures, axe_path, "branch")
    assert result["status"] == "completed_with_limitations"
    assert any(e["cycle"] for e in result["edges"])
    assert {s["id"] for s in result["steps"]} >= {"ready", "validation", "restart"}


def test_cancellation_preserves_partial_results_and_closes_browser(
    store, project, fixtures, axe_path
):
    import psutil

    async def cancel_run():
        p = project("slow")
        control = RunControl()
        task = asyncio.create_task(
            execute(store, p["id"], template("slow"), control, fixtures, axe_path)
        )
        for _ in range(100):
            await asyncio.sleep(0.1)
            runs = store.runs(p["id"])
            if runs and any(s["id"] == "slow" for s in runs[0]["steps"]):
                break
        else:
            pytest.fail("Slow step never started")
        control.cancel.set()
        return await asyncio.wait_for(task, 8)

    before = {p.pid for p in psutil.Process().children(recursive=True)}
    result = asyncio.run(cancel_run())
    assert result["status"] == "cancelled"
    assert result["steps"][0]["status"] == "passed"
    assert result["steps"][-1]["status"] == "interrupted"
    after = [p for p in psutil.Process().children(recursive=True) if p.pid not in before]
    assert not [p for p in after if "chrome" in p.name().lower()]


def test_axe_runs_locally_and_reports_genuine_rule_results(store, project, fixtures, axe_path):
    p = project("broken")
    journey = template("broken")
    # Audit the broken date control, then verify that the application heading is present.
    from accessmaze.models import Step

    journey.steps = [
        journey.steps[0],
        Step(id="audit", action="audit"),
        Step(
            id="heading",
            action="assert_visible",
            target={"role": "heading", "name": "Scholarship application"},
        ),
    ]
    result = asyncio.run(execute(store, p["id"], journey, RunControl(), fixtures, axe_path))
    assert "audit" in {s["id"] for s in result["steps"] if "audit" in s}
    assert "button-name" in {v["id"] for v in result["steps"][1]["audit"]["violations"]}
    assert any(f["rule"] == "button-name" for f in result["findings"])
