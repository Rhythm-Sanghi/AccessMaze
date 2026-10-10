import asyncio
import threading

import pytest
from compatibility_app import CompatibilityApp
from playwright.async_api import async_playwright

from accessmaze.actions import perform
from accessmaze.models import Step
from accessmaze.network import BrowserPolicy


@pytest.mark.browser
def test_interrupted_inflight_api_preserves_draft_and_requires_explicit_retry(axe_path):
    async def exercise():
        with CompatibilityApp() as app:
            app.options_gate = threading.Event()
            app.options_disconnect = True
            journey = app.journey()
            policy = BrowserPolicy(journey, app.origin, set())
            await policy.prepare()
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(args=policy.launch_args)
                try:
                    context = await browser.new_context(service_workers="block")
                    await policy.install(context)
                    page = await context.new_page()
                    await policy.attach(page)
                    await page.goto(app.origin)
                    await page.get_by_label("Applicant name").fill("Synthetic interrupted draft")
                    policy.effects = True
                    await page.get_by_role("button", name="Continue").click()
                    assert await asyncio.to_thread(app.options_started.wait, 3)
                    await perform(
                        page,
                        context,
                        Step(id="disconnect", action="offline"),
                        journey,
                        app.origin,
                        axe_path,
                    )
                    assert "in-flight requests" in context._accessmaze_interaction["limitation"]
                    app.options_gate.set()
                    await (
                        page.get_by_role("alert")
                        .filter(has_text="Connection interrupted")
                        .wait_for(timeout=5000)
                    )
                    assert (
                        await page.get_by_label("Applicant name").input_value()
                        == "Synthetic interrupted draft"
                    )
                    interrupted_requests = app.summary()["api_options_requests"]
                    await perform(
                        page,
                        context,
                        Step(id="reconnect", action="online"),
                        journey,
                        app.origin,
                        axe_path,
                    )
                    await asyncio.sleep(0.4)
                    assert app.summary()["api_options_requests"] == interrupted_requests
                    assert await page.get_by_role(
                        "heading", name="Hackyard application", exact=True
                    ).is_visible()
                    app.options_disconnect = False
                    await page.get_by_role("button", name="Continue").click()
                    await page.get_by_role("heading", name="Attach documents").wait_for()
                    assert app.summary()["api_options_requests"] > interrupted_requests
                    assert not app.posts
                finally:
                    app.options_gate.set()
                    await browser.close()

    asyncio.run(exercise())
