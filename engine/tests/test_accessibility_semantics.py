import asyncio
import json

import pytest
from playwright.async_api import async_playwright

from accessmaze.actions import CheckFailure, keyboard_reach, perform
from accessmaze.evidence import observe
from accessmaze.models import Step
from accessmaze.templates import template

pytestmark = pytest.mark.browser


def test_tab_budget_is_exact_and_shadow_focus_is_recognized(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await page.set_content("<button>A</button><button>B</button>")
            await page.evaluate(
                "document.addEventListener('keydown',e=>{if(e.key==='Tab')window.tabs=(window.tabs||0)+1})"
            )
            with pytest.raises(CheckFailure, match="1 Tab"):
                await keyboard_reach(page, page.get_by_role("button", name="B", exact=True), 1)
            assert await page.evaluate("window.tabs") == 1
            assert context._accessmaze_interaction["tab_presses"] == 1
            await page.set_content('<div id="host"></div>')
            await page.evaluate(
                "host.attachShadow({mode:'open'}).innerHTML='<button>Inside shadow</button>'"
            )
            await keyboard_reach(page, page.get_by_role("button", name="Inside shadow"), 2)
            await perform(
                page,
                context,
                Step(
                    id="focus",
                    action="assert_focus",
                    target={"role": "button", "name": "Inside shadow"},
                ),
                template(),
                "fixture://accessible",
                axe_path,
            )
            await browser.close()

    asyncio.run(exercise())


def test_computed_accessible_names_and_values_are_separate():
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content("""<span id="name">Computed name</span>
<button aria-label="Fallback name" aria-labelledby="name">Content</button>
<label>Private field<input value="never-persist-field-value"></label>""")
            data = await observe(page)
            assert any(
                n["role"] == "button" and n["name"] == "Computed name"
                for n in data["ax_tree"]["nodes"]
            )
            assert "never-persist-field-value" not in json.dumps(data)
            await browser.close()

    asyncio.run(exercise())


def test_focused_visible_error_association_does_not_require_live_region(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await page.set_content("""<label>Email
<input id="email" aria-invalid="true" aria-describedby="error"></label>
<p id="error">Enter a valid test email</p>""")
            await page.get_by_label("Email", exact=True).focus()
            await perform(
                page,
                context,
                Step(id="errors", action="assert_errors"),
                template(),
                "fixture://accessible",
                axe_path,
            )
            assert context._accessmaze_interaction["error_semantics"]["focus"]
            await page.locator("#error").evaluate("e=>e.hidden=true")
            with pytest.raises(CheckFailure, match="Validation semantics"):
                await perform(
                    page,
                    context,
                    Step(id="errors", action="assert_errors"),
                    template(),
                    "fixture://accessible",
                    axe_path,
                )
            await browser.close()

    asyncio.run(exercise())
