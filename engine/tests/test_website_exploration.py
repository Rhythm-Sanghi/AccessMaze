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
    import threading

    changed = threading.Event()

    def release_change(handler):
        assert changed.wait(30), "Test never released the title change"
        return 200, {"Content-Type": "text/plain"}, "change"

    async def exercise():
        try:
            with website(
                {
                    "/": (
                        200,
                        {"Content-Type": "text/html"},
                        """<h1>Base</h1>
<button onclick="fetch('/write',{method:'POST'})">Continue</button>
<script>fetch('/change').then(r=>r.text()).then(()=>{
 document.title='Changed after proposal';fetch('/changed');});</script>""",
                    ),
                    "/change": (200, {}, release_change),
                    "/changed": (200, {}, "observed"),
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
                # Trigger only after the proposal, and wait for the page's acknowledgement.
                # A timer from document load can fire before slow CI finishes preparing it.
                changed.set()
                for _ in range(200):
                    if ("GET", "/changed") in hits:
                        break
                    await asyncio.sleep(0.05)
                else:
                    pytest.fail("Browser did not acknowledge the controlled state change")
                control.approve(proposal["id"], proposal["choices"][0]["id"])
                result = await asyncio.wait_for(task, 10)
                assert result["exploration"]["stop_reason"] == "state-changed-before-action"
                assert ("POST", "/write") not in hits
        finally:
            changed.set()

    asyncio.run(exercise())


@pytest.mark.parametrize("spa", [False, True], ids=["multi-page", "history-spa"])
def test_authorized_branch_recovery_is_separately_approved(store, fixtures, axe_path, spa):
    async def exercise():
        branch = (
            "<h1>Branch</h1>"
            "<button onclick=\"fetch('/danger',{method:'POST'})\">Delete records</button>"
        )
        if spa:
            body = """<h1>Base</h1><span id='name'>Alpha</span>
<button aria-labelledby='name' onclick="history.pushState({},'', '/alpha');
document.body.innerHTML='<h1>Alpha branch</h1>'">hidden</button>
<button onclick="history.pushState({},'', '/beta');
document.body.innerHTML='<h1>Beta branch</h1>'">Beta</button>"""
        else:
            body = "<h1>Base</h1><a href='/beta'>Beta</a><a href='/alpha'>Alpha</a>"
        with website(
            {
                "/": (200, {"Content-Type": "text/html"}, body),
                "/alpha": (200, {"Content-Type": "text/html"}, branch),
                "/beta": (200, {"Content-Type": "text/html"}, branch),
                "/danger": (200, {}, "bad"),
            }
        ) as (target, hits):
            journey = journey_for(target)
            journey.exploration.recover_navigation = True
            journey.exploration.max_actions = 3
            journey.exploration.max_depth = 1
            p = store.save_project(ProjectInput(name="Branches", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, p["id"], journey, control, fixtures, axe_path)
            )
            first = await wait_for_proposal(control)
            assert [c["name"] for c in first["choices"]] == ["Alpha", "Beta"]
            control.approve(first["id"], first["choices"][0]["id"])

            async def next_proposal(previous):
                for _ in range(200):
                    pending = control.pending()
                    if pending and pending["id"] != previous["id"]:
                        return pending
                    await asyncio.sleep(0.05)
                pytest.fail("Next approved branch was unavailable")

            recovery = await next_proposal(first)
            assert [c["role"] for c in recovery["choices"]] == ["navigation"]
            assert hits.count(("GET", "/")) == 1
            partial = store.runs(p["id"])[0]
            assert partial["exploration"]["pending_branches"]  # root sibling retained
            control.approve(recovery["id"], recovery["choices"][0]["id"])
            second = await next_proposal(recovery)
            assert [c["name"] for c in second["choices"]] == ["Beta"]
            control.approve(second["id"], second["choices"][0]["id"])
            result = await asyncio.wait_for(task, 8)
            assert result["exploration"]["stop_reason"] == "action-budget"
            assert len(result["exploration"]["actions"]) == 3
            assert len(result["nodes"]) >= 3
            assert result["exploration"]["actions"][0]["reachability"] == "reached"
            assert result["exploration"]["actions"][1]["kind"] == "approved-recovery"
            assert not result["findings"]
            assert not any(method == "POST" for method, _ in hits)
            assert hits.count(("GET", "/")) == 2
            assert store.run(result["id"])["exploration"] == result["exploration"]

    asyncio.run(exercise())


def test_checkbox_state_is_not_lost_by_focus_normalization(store, fixtures, axe_path):
    from accessmaze.website_exploration import state_key

    async def exercise():
        with website(
            {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    "<h1>Base</h1><label>Terms<input type=checkbox></label>"
                    "<label>Plan<input type=radio></label>",
                )
            }
        ) as (target, hits):
            journey = journey_for(target)
            journey.exploration.max_actions = 1
            p = store.save_project(ProjectInput(name="Checkbox discovery", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, p["id"], journey, control, fixtures, axe_path)
            )
            proposal = await wait_for_proposal(control)
            assert [c["role"] for c in proposal["choices"]] == ["checkbox", "radio"]
            choice = proposal["choices"][0]
            assert choice["classification"] == "potentially-consequential"
            assert not store.runs(p["id"])[0]["exploration"]["actions"]
            control.approve(proposal["id"], choice["id"])
            result = await asyncio.wait_for(task, 8)
            action = result["exploration"]["actions"][0]
            source = next(n["observation"] for n in result["nodes"] if n["id"] == action["source"])
            destination = next(
                n["observation"] for n in result["nodes"] if n["id"] == action["state_id"]
            )
            assert state_key(source) != state_key(destination), (
                "Checked state was incorrectly aliased after focus normalization"
            )
            assert action["reachability"] == "reached"
            assert not result["findings"]
            assert not any(method == "POST" for method, _ in hits)

    asyncio.run(exercise())


def test_observation_does_not_mix_documents_during_navigation(monkeypatch):
    from pathlib import Path

    from playwright.async_api import async_playwright

    import accessmaze.evidence as evidence

    browsers = Path.cwd() / ".accessmaze/browsers"
    if browsers.is_dir():
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browsers))

    async def exercise():
        with website(
            {
                "/": (200, {"Content-Type": "text/html"}, "<title>Old</title><h1>Old</h1>"),
                "/next": (200, {"Content-Type": "text/html"}, "<title>New</title><h1>New</h1>"),
            }
        ) as (url, hits):
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                try:
                    page = await browser.new_page()
                    await page.goto(url)
                    real_tree = evidence.accessibility_tree
                    navigated = False

                    async def tree_during_navigation(page):
                        nonlocal navigated
                        if not navigated:
                            navigated = True
                            await page.goto(url + "/next")
                        return await real_tree(page)

                    monkeypatch.setattr(evidence, "accessibility_tree", tree_during_navigation)
                    observation = await evidence.observe(page)
                    assert observation["title"] == "New"
                    assert observation["headings"] == ["New"]
                    assert observation["url"] == url + "/next"
                    assert "_document_epoch" not in observation
                    assert hits.count(("GET", "/next")) == 1
                finally:
                    await browser.close()

    asyncio.run(exercise())
