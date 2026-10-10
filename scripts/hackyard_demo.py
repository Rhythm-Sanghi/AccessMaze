"""Owned real-browser failure, correction and retest; all submitted data is synthetic."""

import argparse
import asyncio
import base64
import difflib
import json
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine/tests"))
from compatibility_app import CompatibilityApp  # noqa: E402
from accessmaze.fixtures import FixtureServer  # noqa: E402
from accessmaze.inputs import RunInputs  # noqa: E402
from accessmaze.models import Journey, ProjectInput  # noqa: E402
from accessmaze.network import BrowserPolicy  # noqa: E402
from accessmaze.recorder import Recording  # noqa: E402
from accessmaze.reports import export_report  # noqa: E402
from accessmaze.retests import compare_runs  # noqa: E402
from accessmaze.runner import RunControl, execute  # noqa: E402
from accessmaze.storage import Store  # noqa: E402
from accessmaze.templates import template  # noqa: E402


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


async def demonstrate(output):
    output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".accessmaze/browsers")
    )
    fixtures = FixtureServer()
    try:
        with CompatibilityApp() as app:
            journey = app.journey()
            store = Store(output / "private-workspace")
            project = store.save_project(
                ProjectInput(name="Hackyard demonstration", journey=journey)
            )
            inputs = RunInputs(
                journey,
                {
                    "files": {
                        "document": {
                            "name": "synthetic.txt",
                            "base64": base64.b64encode(
                                b"Hackyard synthetic upload"
                            ).decode(),
                        }
                    }
                },
            )

            async def run():
                return await execute(
                    store,
                    project["id"],
                    journey,
                    RunControl(),
                    fixtures,
                    ROOT / "node_modules/axe-core/axe.min.js",
                    inputs=inputs,
                )

            app.broken = True
            before_html = app.html()
            broken = await run()
            assert any(
                f["rule"] == "keyboard-unreachable" for f in broken["findings"]
            ), broken
            assert not app.posts, "Broken journey must not submit"
            app.broken = False
            (output / "correction.diff").write_text(
                "".join(
                    difflib.unified_diff(
                        before_html.splitlines(True),
                        app.html().splitlines(True),
                        fromfile="broken/application.html",
                        tofile="fixed/application.html",
                    )
                ),
                encoding="utf-8",
            )
            fixed = await run()
            comparison = compare_runs(broken, fixed)
            assert (
                fixed["status"] == "completed_with_limitations"
                and not fixed["findings"]
            ), fixed
            assert comparison["comparable"]
            assert any(f["verdict"] == "passed-retest" for f in comparison["findings"])
            assert (
                len(app.posts) == 1
                and app.posts[0]["document"] == b"Hackyard synthetic upload"
            )
            for label, result in [("broken", broken), ("fixed", fixed)]:
                for format in ["json", "html", "csv"]:
                    content, _ = export_report(result, format)
                    (output / f"{label}.{format}").write_text(content, encoding="utf-8")
            save(output / "journey.json", journey.model_dump())
            save(output / "retest.json", comparison)

            # A separate controlled form drops its draft on a real Chromium offline event.
            recovery = template("recovery")
            recovery_project = store.save_project(
                ProjectInput(name="Environmental interruption", journey=recovery)
            )
            environment = await execute(
                store,
                recovery_project["id"],
                recovery,
                RunControl(),
                fixtures,
                ROOT / "node_modules/axe-core/axe.min.js",
            )
            assert environment["outcome"]["status"] == "blocked", environment
            assert any(f["rule"] == "form-state-lost" for f in environment["findings"])
            assert any(not n["observation"]["online"] for n in environment["nodes"])
            assert environment["nodes"][-1]["observation"]["online"]
            for format in ["json", "html", "csv"]:
                content, _ = export_report(environment, format)
                (output / f"environment.{format}").write_text(content, encoding="utf-8")
            save(output / "environment-journey.json", recovery.model_dump())

            # Real input events feed the product recorder. This is scripted, not a human test.
            recording = Recording(journey)
            policy = BrowserPolicy(journey, app.origin, set())
            await policy.prepare()
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(args=policy.launch_args)
                try:
                    context = await browser.new_context(
                        service_workers="block", accept_downloads=False
                    )
                    await policy.install(context)
                    page = await context.new_page()
                    await policy.attach(page)
                    await recording.attach(context, page)
                    policy.effects = True
                    await page.goto(app.origin)
                    await page.get_by_label("Applicant name").fill(
                        "Recorded synthetic applicant"
                    )
                    await page.get_by_role("button", name="Continue").click()
                    await page.get_by_role(
                        "heading", name="Attach documents"
                    ).wait_for()
                    await recording.capture_completion(page)
                    await asyncio.sleep(0.1)
                finally:
                    await browser.close()
            draft = Journey.model_validate(
                {**journey.model_dump(), "steps": recording.snapshot()["steps"]}
            )
            assert "Recorded synthetic applicant" not in draft.model_dump_json()
            save(output / "recorded-draft.json", draft.model_dump())
            recorded_project = store.save_project(
                ProjectInput(name="Recorded draft replay", journey=draft)
            )
            replay = await execute(
                store,
                recorded_project["id"],
                draft,
                RunControl(),
                fixtures,
                ROOT / "node_modules/axe-core/axe.min.js",
                inputs=RunInputs(
                    draft,
                    {
                        "values": {
                            s.value_from: "Synthetic replay"
                            for s in draft.steps
                            if s.value_from
                        }
                    },
                ),
            )
            assert (
                replay["status"] == "completed_with_limitations"
                and not replay["findings"]
            ), replay
            save(output / "recorded-replay.json", replay)
            summary = {
                "scope": "Owned HTTP app and actual Chromium; scripted recording, no NVDA claim",
                "broken_status": broken["status"],
                "fixed_status": fixed["status"],
                "broken_outcome": broken["outcome"],
                "fixed_outcome": fixed["outcome"],
                "environment_outcome": environment["outcome"],
                "environment_scope": "Bundled synthetic form; actual Chromium offline/online events, not a physical adapter disconnect or proof about in-flight requests",
                "retest": comparison,
                "recorded_replay_status": replay["status"],
                "server_observations": app.summary(),
                "target_lifetime": "Ephemeral servers closed after demonstration; regenerate to replay",
            }
            save(output / "summary.json", summary)
            return summary
    finally:
        fixtures.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New directory, never overwritten"
    )
    print(json.dumps(asyncio.run(demonstrate(parser.parse_args().output)), indent=2))
