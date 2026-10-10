import asyncio
import json

import pytest
from test_website_policy import website

from accessmaze.models import Journey, ProjectInput, Step
from accessmaze.runner import RunControl, execute

pytestmark = pytest.mark.browser


def journey_for(target):
    return Journey(
        name="Approved website walk",
        target=target,
        allow_local=True,
        exploration={"enabled": True, "max_depth": 2, "max_actions": 2},
        steps=[
            Step(id="open", action="navigate"),
            Step(id="base", action="assert_visible", target={"role": "heading", "name": "Base"}),
        ],
    )


async def wait_for_proposal(control):
    for _ in range(200):
        if pending := control.pending():
            return pending
        await asyncio.sleep(0.05)
    pytest.fail("Website exploration never offered an approval")


def test_website_walk_waits_for_each_approval_and_never_replays(store, fixtures, axe_path):
    async def exercise():
        with website(
            {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    """<h1>Base</h1>
<button onclick="fetch('/write',{method:'POST'})
.then(()=>document.querySelector('h1').textContent='Next')">Advance privately</button>
<button onclick="fetch('/danger',{method:'POST'})">Dangerous alternative</button>""",
                ),
                "/write": (200, {}, "ok"),
                "/danger": (200, {}, "bad"),
            }
        ) as (target, hits):
            journey = journey_for(target)
            p = store.save_project(ProjectInput(name="Website walk", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, p["id"], journey, control, fixtures, axe_path)
            )
            first = await wait_for_proposal(control)
            await asyncio.sleep(0.15)
            assert not any(method == "POST" for method, _ in hits)
            saved = store.runs(p["id"])[0]
            assert saved["status"] == "awaiting_approval"
            assert "Dangerous alternative" not in json.dumps(saved)
            choice = next(c for c in first["choices"] if c["name"] == "Advance privately")
            control.approve(first["id"], choice["id"])
            with pytest.raises(ValueError, match="stale"):
                control.approve(first["id"], choice["id"])
            for _ in range(200):
                second = control.pending()
                if second and second["id"] != first["id"]:
                    break
                await asyncio.sleep(0.05)
            else:
                pytest.fail("Second action was not separately gated")
            assert hits.count(("POST", "/write")) == 1
            assert ("POST", "/danger") not in hits
            control.approve(second["id"], "stop")
            result = await asyncio.wait_for(task, 5)
            assert result["exploration"]["stop_reason"] == "user-stopped"
            assert len(result["exploration"]["actions"]) == 1
            assert hits.count(("GET", "/")) == 1, "External workflow was reset or replayed"
            assert "Advance privately" not in json.dumps(result)
            assert "approval" not in result
            assert not any("fixture button discovery" in s for s in result["limitations"])
            assert any("requires approval for each action" in s for s in result["limitations"])

    asyncio.run(exercise())


def test_cancel_waiting_for_approval_keeps_partial_results(store, fixtures, axe_path):
    async def exercise():
        with website(
            {"/": (200, {"Content-Type": "text/html"}, "<h1>Base</h1><button>Continue</button>")}
        ) as (target, hits):
            journey = journey_for(target)
            p = store.save_project(ProjectInput(name="Cancel approval", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, p["id"], journey, control, fixtures, axe_path)
            )
            await wait_for_proposal(control)
            control.cancel.set()
            result = await asyncio.wait_for(task, 5)
            assert result["status"] == "cancelled"
            assert not result["exploration"]["actions"]
            assert result["nodes"]
            assert control.pending() is None

    asyncio.run(exercise())


def test_changed_state_refuses_previously_approved_action(store, fixtures, axe_path):
    async def exercise():
        with website(
            {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    """<h1>Base</h1>
<button onclick="fetch('/write',{method:'POST'})">Continue</button>
<script>setTimeout(()=>document.title='Changed after proposal',1000)</script>""",
                ),
                "/write": (200, {}, "bad"),
            }
        ) as (target, hits):
            journey = journey_for(target)
            p = store.save_project(ProjectInput(name="Stale state", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, p["id"], journey, control, fixtures, axe_path)
            )
            proposal = await wait_for_proposal(control)
            await asyncio.sleep(1.2)
            control.approve(proposal["id"], proposal["choices"][0]["id"])
            result = await asyncio.wait_for(task, 5)
            assert result["exploration"]["stop_reason"] == "state-changed-before-action"
            assert ("POST", "/write") not in hits

    asyncio.run(exercise())
