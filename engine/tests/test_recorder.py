import asyncio
import json
from pathlib import Path

import pytest
from playwright.async_api import async_playwright
from test_website_policy import website

from accessmaze.inputs import RunInputs
from accessmaze.models import Journey, ProjectInput, Request
from accessmaze.network import BrowserPolicy
from accessmaze.recorder import Recording
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template
from accessmaze.worker import Worker


@pytest.mark.browser
def test_real_recording_discards_values_and_replays_the_edited_draft(store, fixtures, axe_path):
    async def exercise():
        with website(
            {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    """<h1>Start</h1>
<label>Applicant<input id="applicant"></label>
<label>Password<input type="password" id="password"></label>
<button onclick="document.querySelector('h1').textContent='Task complete'">Finish</button>""",
                )
            }
        ) as (target, _):
            journey = template()
            journey.target = target
            journey.allow_local = True
            recording = Recording(journey)
            policy = BrowserPolicy(journey, target, set())
            await policy.prepare()
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(args=policy.launch_args)
                context = await browser.new_context(service_workers="block")
                await policy.install(context)
                page = await context.new_page()
                await policy.attach(page)
                await recording.attach(context, page)
                await page.goto(target)
                await page.get_by_label("Applicant", exact=True).fill("private-applicant-318")
                await page.keyboard.press("Tab")
                await page.get_by_label("Password", exact=True).fill("private-password-752")
                await page.get_by_role("button", name="Finish").click()
                await recording.capture_completion(page)
                await asyncio.sleep(0.1)
                snapshot = recording.snapshot()
                text = json.dumps(snapshot)
                assert "private-applicant-318" not in text
                assert "private-password-752" not in text
                fills = [s for s in snapshot["steps"] if s["action"] == "fill"]
                assert len(fills) == 2, snapshot
                assert all(s["value_from"] and not s["value"] for s in fills)
                assert snapshot["steps"][1]["action"] == "fill", (
                    "Tab must follow the flushed field intent"
                )
                await browser.close()
            draft = Journey.model_validate({**journey.model_dump(), "steps": snapshot["steps"]})
            p = store.save_project(ProjectInput(name="Recorded draft", journey=draft))
            inputs = RunInputs(
                draft, {"values": {s["value_from"]: "synthetic replay" for s in fills}}
            )
            result = await execute(
                store, p["id"], draft, RunControl(), fixtures, axe_path, inputs=inputs
            )
            assert result["status"] == "completed_with_limitations", result["findings"]
            assert not result["findings"]

    asyncio.run(exercise())


def test_recording_requires_separate_manual_effect_authorization(tmp_path):
    worker = Worker(tmp_path, Path.cwd())
    try:
        p = worker.store.save_project(ProjectInput(name="recording", journey=template()))
        with pytest.raises(ValueError, match="Authorize"):
            worker.dispatch(
                Request(
                    version=1,
                    id="1",
                    method="recorder.start",
                    params={"project_id": p["id"], "authorized": True},
                )
            )
        assert worker.recorder is None
    finally:
        worker.close()


@pytest.mark.browser
def test_headed_recorder_worker_lifecycle_on_windows(tmp_path):
    import sys
    import time

    import psutil

    if sys.platform != "win32":
        pytest.skip("Actual headed Windows browser test; Linux CI has no desktop session")
    worker = Worker(tmp_path, Path.cwd())
    try:
        p = worker.store.save_project(ProjectInput(name="Manual recording", journey=template()))
        started = worker.dispatch(
            Request(
                version=1,
                id="1",
                method="recorder.start",
                params={"project_id": p["id"], "authorized": True, "allow_effects": True},
            )
        )
        for _ in range(100):
            current = worker.dispatch(
                Request(version=1, id="2", method="recorder.get", params={"id": started["id"]})
            )
            if current["status"] != "preparing":
                break
            time.sleep(0.05)
        assert current["status"] == "recording", current
        children = [
            p for p in psutil.Process().children(recursive=True) if "chrome" in p.name().lower()
        ]
        assert children
        with pytest.raises(ValueError, match="recording"):
            worker.dispatch(
                Request(
                    version=1,
                    id="3",
                    method="run.start",
                    params={"project_id": p["id"], "authorized": True, "allow_effects": True},
                )
            )
        worker.dispatch(
            Request(version=1, id="4", method="recorder.stop", params={"id": started["id"]})
        )
        worker.recorder.thread.join(timeout=8)
        assert not worker.recorder.thread.is_alive()
        assert worker.recorder.recording.status == "stopped"
        assert not any(p.is_running() for p in children)
    finally:
        worker.close()
