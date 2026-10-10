"""Browser-reproduced false positives/negatives, not mocked accessibility outcomes."""

import asyncio

import pytest
from playwright.async_api import async_playwright

from accessmaze.actions import CheckFailure, perform
from accessmaze.models import Step
from accessmaze.templates import template

pytestmark = pytest.mark.browser


def test_native_radio_activation_uses_selection_key(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content('<label><input type="radio" name="route">International</label>')
            await perform(
                page,
                page.context,
                Step(
                    id="choose",
                    action="activate",
                    effect=True,
                    target={"role": "radio", "name": "International"},
                ),
                template(),
                "",
                axe_path,
            )
            assert await page.get_by_role("radio").is_checked()
            await browser.close()

    asyncio.run(exercise())


def test_fill_waits_for_spa_field_mount(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                "<main></main><script>setTimeout(()=>document.querySelector('main').innerHTML='<label>Account<input></label>',250)</script>"
            )
            await perform(
                page,
                page.context,
                Step(
                    id="account",
                    action="fill",
                    value="Synthetic",
                    target={"role": "textbox", "name": "Account"},
                ),
                template(),
                "",
                axe_path,
            )
            assert await page.get_by_label("Account").input_value() == "Synthetic"
            await browser.close()

    asyncio.run(exercise())


def test_unrelated_live_region_does_not_prove_error_discoverability(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                '<label>Name<input aria-invalid="true" aria-describedby="err"></label>'
                '<p id="err">Name required</p><p role="status" aria-live="polite">Online</p>'
                "<button>Submit</button>"
            )
            await page.get_by_role("button").focus()
            with pytest.raises(CheckFailure):
                await perform(
                    page,
                    page.context,
                    Step(id="errors", action="assert_errors"),
                    template(),
                    "",
                    axe_path,
                )
            await browser.close()

    asyncio.run(exercise())


def test_disabled_control_is_not_a_keyboard_blocker(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content("<button disabled>Wait for approval</button>")
            with pytest.raises(CheckFailure) as error:
                await perform(
                    page,
                    page.context,
                    Step(
                        id="disabled",
                        action="activate",
                        effect=True,
                        target={"role": "button", "name": "Wait for approval"},
                    ),
                    template(),
                    "",
                    axe_path,
                )
            assert error.value.code == "target-disabled"
            await browser.close()

    asyncio.run(exercise())


def test_axe_detects_missing_button_name_and_clears_after_real_correction(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                '<html lang="en"><title>Rule ground truth</title><main><h1>Save draft</h1>'
                '<button><span aria-hidden="true">+</span></button></main></html>'
            )
            step = Step(id="audit", action="audit")
            before = await perform(page, page.context, step, template(), "", axe_path)
            assert "button-name" in {v["id"] for v in before["violations"]}
            await page.get_by_role("button").evaluate(
                "e=>e.setAttribute('aria-label','Save draft')"
            )
            after = await perform(page, page.context, step, template(), "", axe_path)
            assert "button-name" not in {v["id"] for v in after["violations"]}
            await browser.close()

    asyncio.run(exercise())


def test_native_validation_is_unverified_rather_than_missing_aria_failure(axe_path):
    async def exercise():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.set_content(
                '<form><label>Email<input type="email" required></label>'
                "<button>Submit</button></form>"
            )
            await page.get_by_role("button").click()
            with pytest.raises(CheckFailure) as error:
                await perform(
                    page,
                    page.context,
                    Step(id="errors", action="assert_errors"),
                    template(),
                    "",
                    axe_path,
                )
            assert error.value.code == "native-validation-unverified"
            await browser.close()

    asyncio.run(exercise())
