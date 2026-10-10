import asyncio
import json

import pytest
from playwright.async_api import async_playwright
from test_website_exploration import journey_for, wait_for_proposal
from test_website_policy import website

from accessmaze.actions import CheckFailure, perform
from accessmaze.evidence import fingerprint, observe
from accessmaze.inputs import RunInputs
from accessmaze.models import ProjectInput, Step
from accessmaze.replay import prepare_replay
from accessmaze.retests import compare_runs
from accessmaze.runner import RunControl, execute
from accessmaze.state_identity import navigation_state_id
from accessmaze.templates import template
from accessmaze.website_exploration import candidates


@pytest.mark.browser
def test_scoped_targets_roving_tabs_and_focus_identity(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            try:
                page = await browser.new_page()
                await page.set_content("""<div role="tablist" aria-label="Delivery">
<button role="tab" aria-selected="true" tabindex="0">Standard</button>
<button role="tab" aria-selected="false" tabindex="-1" id="express">Express</button></div>
<h1>Choose delivery</h1><script>
document.querySelector('[role=tablist]').onkeydown=e=>{
 if(e.key==='ArrowRight') {e.preventDefault(); document.querySelector('#express').focus()}
}; document.querySelector('#express').onclick=e=>{
 e.target.setAttribute('aria-selected','true');
 document.querySelector('h1').textContent='Express selected'
};</script>""")
                before = await observe(page)
                await page.get_by_role("tab", name="Standard").focus()
                focused = await observe(page)
                assert navigation_state_id(before) == navigation_state_id(focused)
                assert fingerprint(before) != fingerprint(focused)
                offered = await candidates(page)
                target = next(c["target"] for c in offered if c["name"] == "Express")
                assert target["scope"] == {"role": "tablist", "name": "Delivery"}
                await perform(
                    page,
                    page.context,
                    Step(id="express", action="activate", effect=True, target=target),
                    template(),
                    "",
                    axe_path,
                )
                assert await page.get_by_role("heading").inner_text() == "Express selected"
                trace = page.context._accessmaze_interaction
                assert trace["arrow_presses"] == 1
                assert trace["locator_provenance"]["scoped"]
                assert navigation_state_id(focused) != navigation_state_id(await observe(page))
                await page.set_content("""
<div role="group" aria-label="Billing"><button>Save</button></div>
<div role="group" aria-label="Shipping">
<button onclick="this.textContent='Saved'">Save</button></div>""")
                offered = await candidates(page)
                assert len(offered) == 2
                target = next(
                    c["target"] for c in offered if c["target"]["scope"]["name"] == "Shipping"
                )
                await perform(
                    page,
                    page.context,
                    Step(id="save", action="activate", effect=True, target=target),
                    template(),
                    "",
                    axe_path,
                )
                assert await page.get_by_role("button", name="Save", exact=True).count() == 1
                await page.set_content("<button>Duplicate</button><button>Duplicate</button>")
                diagnostics = []
                assert not await candidates(page, diagnostics)
                assert {d["reason"] for d in diagnostics} == {"ambiguous-target"}
                with pytest.raises(CheckFailure) as failure:
                    await perform(
                        page,
                        page.context,
                        Step(
                            id="duplicate",
                            action="assert_visible",
                            target={"role": "button", "name": "Duplicate"},
                        ),
                        template(),
                        "",
                        axe_path,
                    )
                assert failure.value.code == "target-ambiguous"
            finally:
                await browser.close()

    asyncio.run(exercise())


@pytest.mark.browser
@pytest.mark.parametrize("retain_text", [True, False])
def test_discovered_failure_recipe_replays_only_retained_targets(
    store, fixtures, axe_path, retain_text
):
    async def exercise():
        routes = {
            "/": (
                200,
                {"Content-Type": "text/html"},
                '<h1>Base</h1><button id="blocked" tabindex="-1">Continue task</button>',
            )
        }
        with website(routes) as (target, hits):
            journey = journey_for(target)
            journey.privacy.capture_page_text = retain_text
            journey.tab_budget = 3
            project = store.save_project(ProjectInput(name="Discovery replay", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, project["id"], journey, control, fixtures, axe_path)
            )
            proposal = await wait_for_proposal(control)
            control.approve(proposal["id"], proposal["choices"][0]["id"])
            original = await asyncio.wait_for(task, 8)
            finding = original["findings"][0]
            assert finding["rule"] == "keyboard-unreachable"
            assert original["reachability"]["blocking_attempts"][0]["step_id"] == "explore-1"
            assert all(
                n["navigation_state_id"] and n["interaction_state_id"] == n["id"]
                for n in original["nodes"]
            )
            if not retain_text:
                assert "Continue task" not in json.dumps(original)
                with pytest.raises(ValueError, match="withheld"):
                    prepare_replay(original, finding["id"])
                return
            draft = prepare_replay(original, finding["id"])
            assert draft.steps[-1].target.element_id == "blocked"
            replay = {"source_id": original["id"], "finding_id": finding["id"]}
            reproduced = await execute(
                store, project["id"], draft, RunControl(), fixtures, axe_path, replay=replay.copy()
            )
            assert reproduced["replay"]["verdict"] == "observed-again"
            assert reproduced["reachability"]["status"] == "observed-failure"
            routes["/"] = (
                200,
                {"Content-Type": "text/html"},
                '<h1>Base</h1><button id="blocked">Continue task</button>',
            )
            fixed = await execute(
                store, project["id"], draft, RunControl(), fixtures, axe_path, replay=replay.copy()
            )
            assert fixed["replay"]["verdict"] == "not-reproduced-in-this-run"
            assert fixed["reachability"]["status"] == "observed-success"
            assert store.run(original["id"]) == original
            assert not any(method == "POST" for method, _ in hits)

    asyncio.run(exercise())


@pytest.mark.browser
def test_redacted_literals_cannot_make_different_inputs_comparable(store, fixtures, axe_path):
    async def exercise():
        journey = template()
        project = store.save_project(
            ProjectInput(name="Comparable input boundary", journey=journey)
        )
        key = b"test-only-key"
        before = await execute(
            store,
            project["id"],
            journey,
            RunControl(),
            fixtures,
            axe_path,
            inputs=RunInputs(journey, key=key),
        )
        journey.steps[1].value = "Different synthetic input"
        after = await execute(
            store,
            project["id"],
            journey,
            RunControl(),
            fixtures,
            axe_path,
            inputs=RunInputs(journey, key=key),
        )
        assert before["journey"] == after["journey"]
        comparison = compare_runs(before, after)
        assert not comparison["comparable"]
        assert comparison["verdict"] == "inconclusive-different-conditions"
        assert "Different synthetic input" not in json.dumps(after)
        assert "runtime-input-signature" in comparison["changed_conditions"]

    asyncio.run(exercise())


@pytest.mark.browser
def test_aria_owned_option_and_description_constraints(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            try:
                page = await browser.new_page()
                await page.set_content("""<div role="listbox" aria-label="Routes" tabindex="0"
aria-activedescendant="local" onkeydown="if(event.key==='Enter') this.dataset.chosen='yes'">
<div role="option" id="local" aria-selected="true">Local</div></div>
<button aria-describedby="billing" aria-description="Wrong fallback"
onclick="this.dataset.used='yes'">Save</button><p id="billing">Billing details</p>
<button aria-description="Shipping details">Save</button>""")
                diagnostics = []
                choices = await candidates(page, diagnostics)
                assert any(c["role"] == "option" for c in choices)
                assert any(d["reason"] == "unsupported-container-action" for d in diagnostics)
                await perform(
                    page,
                    page.context,
                    Step(
                        id="local",
                        action="activate",
                        effect=True,
                        target={"role": "option", "name": "Local", "element_id": "local"},
                    ),
                    template(),
                    "",
                    axe_path,
                )
                assert page.context._accessmaze_interaction["logical_focus"]
                assert await page.get_by_role("listbox").get_attribute("data-chosen") == "yes"
                await perform(
                    page,
                    page.context,
                    Step(
                        id="save",
                        action="activate",
                        effect=True,
                        target={"role": "button", "name": "Save", "description": "Billing details"},
                    ),
                    template(),
                    "",
                    axe_path,
                )
                assert await page.locator('[data-used="yes"]').count() == 1
                with pytest.raises(CheckFailure, match="description"):
                    await perform(
                        page,
                        page.context,
                        Step(
                            id="wrong",
                            action="activate",
                            effect=True,
                            target={
                                "role": "button",
                                "name": "Save",
                                "description": "Wrong fallback",
                            },
                        ),
                        template(),
                        "",
                        axe_path,
                    )
            finally:
                await browser.close()

    asyncio.run(exercise())


@pytest.mark.browser
def test_discovery_state_bound_preserves_unknown_frontier(store, fixtures, axe_path):
    async def exercise():
        with website(
            {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    '<h1>Base</h1><button onclick="'
                    "document.querySelector('h1').textContent='Next'\">Advance</button>",
                )
            }
        ) as (target, _):
            journey = journey_for(target)
            journey.exploration.max_states = 2
            project = store.save_project(ProjectInput(name="State bound", journey=journey))
            control = RunControl()
            task = asyncio.create_task(
                execute(store, project["id"], journey, control, fixtures, axe_path)
            )
            proposal = await wait_for_proposal(control)
            control.approve(proposal["id"], proposal["choices"][0]["id"])
            result = await asyncio.wait_for(task, 8)
            assert result["exploration"]["stop_reason"] == "state-budget"
            assert len(result["nodes"]) == 2
            assert result["reachability"]["unexplored_frontier"][0]["reason"] == "state-budget"
            assert not result["findings"]

    asyncio.run(exercise())


@pytest.mark.browser
def test_controlled_fixture_failure_replay_uses_observed_prerequisite_path(
    store, fixtures, axe_path
):
    async def exercise():
        journey = template("broken")
        journey.steps = [
            journey.steps[0],
            Step(
                id="explore-3",
                action="assert_visible",
                target={"role": "heading", "name": "Scholarship application"},
            ),
        ]
        journey.exploration.enabled = True
        journey.exploration.max_depth = 1
        journey.exploration.max_actions = 10
        journey.tab_budget = 3
        project = store.save_project(ProjectInput(name="Fixture witness", journey=journey))
        original = await execute(store, project["id"], journey, RunControl(), fixtures, axe_path)
        finding = next(f for f in original["findings"] if f["rule"] == "keyboard-unreachable")
        draft = prepare_replay(original, finding["id"])
        assert len(draft.steps) == 3
        replayed = await execute(
            store,
            project["id"],
            draft,
            RunControl(),
            fixtures,
            axe_path,
            replay={"source_id": original["id"], "finding_id": finding["id"]},
        )
        assert replayed["replay"]["verdict"] == "observed-again"

    asyncio.run(exercise())
