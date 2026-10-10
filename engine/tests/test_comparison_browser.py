"""Two real axe executions with the same rule on different controls."""

import asyncio

import pytest
from compatibility_app import CompatibilityApp

from accessmaze.models import Journey
from accessmaze.retests import compare_runs
from accessmaze.runner import RunControl, execute


@pytest.mark.browser
def test_rule_on_different_control_is_not_a_persistent_identity(store, fixtures, axe_path):
    async def exercise():
        with CompatibilityApp() as app:
            journey = Journey(
                name="Affected controls",
                target=app.origin,
                allow_local=True,
                privacy={"capture_page_text": True},
                steps=[
                    {"id": "open", "action": "navigate"},
                    {"id": "audit", "action": "audit"},
                    {
                        "id": "goal",
                        "action": "assert_visible",
                        "target": {"role": "heading", "name": "Ready"},
                    },
                ],
            )
            # Use a real persisted project for SQLite foreign-key integrity.
            from accessmaze.models import ProjectInput

            project = store.save_project(ProjectInput(name="Controls", journey=journey))

            async def persisted_run(target):
                app.html = lambda: (
                    '<!doctype html><html lang="en"><title>Control test</title>'
                    f'<main><h1>Ready</h1><button id="{target}"></button></main></html>'
                )
                return await execute(
                    store, project["id"], journey, RunControl(), fixtures, axe_path
                )

            previous = await persisted_run("first")
            current = await persisted_run("second")
            comparison = compare_runs(previous, current)
            old = next(f for f in previous["findings"] if f["rule"] == "button-name")
            new = next(f for f in current["findings"] if f["rule"] == "button-name")
            assert old["actual"]["targets"] != new["actual"]["targets"]
            assert comparison["comparable"]
            assert (
                next(f for f in comparison["findings"] if f["finding_id"] == old["id"])["verdict"]
                == "inconclusive"
            )
            assert new["id"] in {f["finding_id"] for f in comparison["added_findings"]}
            assert current["outcome"]["status"] == "completed"

    asyncio.run(exercise())
