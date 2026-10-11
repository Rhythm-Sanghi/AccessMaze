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


@pytest.fixture
def recorder_cleanup(monkeypatch):
    import time

    # Browser-process logs only for these owned synthetic recorder tests.
    monkeypatch.setenv("DEBUG", "pw:browser")
    browsers = []
    connected_at_driver_exit = []
    contexts_at_browser_close = []
    cleanup_events = []

    def event(stage):
        cleanup_events.append((stage, round(time.monotonic(), 3)))

    class ObservedPlaywright:
        def __init__(self):
            self.manager = async_playwright()

        async def __aenter__(self):
            playwright = await self.manager.__aenter__()
            browser_type = playwright.chromium
            original_launch = browser_type.launch

            async def launch(**options):
                browser = await original_launch(**options)
                browsers.append(browser)
                original_close = browser.close
                original_new_context = browser.new_context

                async def new_context(**options):
                    context = await original_new_context(**options)
                    original_context_close = context.close

                    async def close_context(**kwargs):
                        event("context.close started")
                        try:
                            return await original_context_close(**kwargs)
                        finally:
                            event("context.close finished")

                    monkeypatch.setattr(context, "close", close_context)
                    return context

                async def close(**kwargs):
                    contexts_at_browser_close.append(len(browser.contexts))
                    event("browser.close started")
                    try:
                        return await original_close(**kwargs)
                    finally:
                        event("browser.close finished")

                monkeypatch.setattr(browser, "close", close)
                monkeypatch.setattr(browser, "new_context", new_context)
                return browser

            monkeypatch.setattr(browser_type, "launch", launch)
            return playwright

        async def __aexit__(self, *args):
            # Observe actual Chromium ownership before stopping the real driver.
            connected_at_driver_exit.extend(b.is_connected() for b in browsers)
            event("driver exit started")
            try:
                await self.manager.__aexit__(*args)
            finally:
                event("driver exit finished")

    monkeypatch.setattr("accessmaze.recorder.async_playwright", ObservedPlaywright)
    return cleanup_events, contexts_at_browser_close, connected_at_driver_exit, event


@pytest.mark.browser
def test_headed_recorder_worker_lifecycle_on_windows(tmp_path, recorder_cleanup):
    import sys
    import time

    import psutil

    if sys.platform != "win32":
        pytest.skip("Actual headed Windows browser test; Linux CI has no desktop session")
    cleanup_events, contexts_at_browser_close, connected_at_driver_exit, event = recorder_cleanup
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
        event("stop requested")
        worker.dispatch(
            Request(version=1, id="4", method="recorder.stop", params={"id": started["id"]})
        )
        worker.recorder.thread.join(timeout=8)
        event("join returned")
        assert not worker.recorder.thread.is_alive(), cleanup_events
        assert worker.recorder.recording.status == "stopped"
        assert contexts_at_browser_close == [0], cleanup_events
        assert connected_at_driver_exit == [False], cleanup_events
        assert not any(p.is_running() for p in children)
    finally:
        worker.close()


@pytest.mark.browser
def test_recorder_stop_cancels_slow_initial_navigation(recorder_cleanup):
    import sys
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from accessmaze.recorder import Recorder

    if sys.platform != "win32":
        pytest.skip("Actual visible Windows recorder")
    cleanup_events, contexts_at_browser_close, connected_at_driver_exit, event = recorder_cleanup
    requested = threading.Event()
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requested.set()
            release.wait(10)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h1>Slow</h1>")
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    journey = template()
    journey.target = f"http://127.0.0.1:{server.server_port}"
    journey.allow_local = True
    recorder = Recorder(journey, journey.target)
    try:
        recorder.start()
        assert requested.wait(8), recorder.recording.snapshot()
        started = time.monotonic()
        event("stop requested")
        recorder.close()
        event("join returned")
        assert not recorder.thread.is_alive(), cleanup_events
        assert recorder.recording.status == "stopped"
        assert connected_at_driver_exit == [False], "Browser outlived its driver scope"
        assert contexts_at_browser_close == [0], "Recorder context was not closed first"
        assert time.monotonic() - started < 3, cleanup_events
    finally:
        release.set()
        recorder.close()
        server.shutdown()
        server.server_close()
        thread.join()
