"""Exercise actual packaged profile, branch approval and live failure replay UI."""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine/tests"))
from compatibility_app import CompatibilityApp  # noqa: E402
from accessmaze.models import Journey  # noqa: E402


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9224")
    args = parser.parse_args()
    token = uuid4().hex[:8]
    names = [f"Native features branches {token}", f"Native features replay {token}"]
    profile_name = f"Native reusable {token}"
    started = time.monotonic()
    with CompatibilityApp() as app:
        mode = "branches"

        def document():
            if mode == "branches":
                return """<!doctype html><html lang=en><title>Owned branches</title><main>
<h1>Base</h1><button onclick="document.querySelector('h1').textContent='Alpha branch';
this.remove()">Alpha</button><button onclick="document.querySelector('h1').textContent='Beta branch';
this.remove()">Beta</button></main></html>"""
            tag, closing = (
                ("div role=button", "div") if app.broken else ("button", "button")
            )
            return (
                "<!doctype html><html lang=en><title>Owned replay</title><main><h1>Base</h1>"
                f"<{tag} onclick=\"document.querySelector('h1').textContent='Done'\">"
                f"Continue</{closing}></main></html>"
            )

        app.html = document
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(args.endpoint)
            page = next(
                p
                for c in browser.contexts
                for p in c.pages
                if "tauri.localhost" in p.url
            )
            page.set_default_timeout(30000)

            async def import_journey(name, steps, exploration=None):
                journey = Journey(
                    name=name,
                    target=app.origin,
                    allow_local=True,
                    tab_budget=8,
                    privacy={"capture_page_text": True},
                    steps=steps,
                    exploration=exploration or {},
                )
                definition = ROOT / "dist" / f"{name.replace(' ', '-')}.json"
                definition.write_text(
                    journey.model_dump_json(indent=2), encoding="utf-8"
                )
                await page.get_by_role("button", name="01 Projects").click()
                await page.get_by_role("button", name="+ Website investigation").click()
                await page.get_by_label("Project name", exact=True).fill(name)
                await page.locator("input[type=file]").first.set_input_files(definition)
                await page.get_by_text(
                    "Imported and validated journey as a new project", exact=True
                ).wait_for()

            async def run():
                await (
                    page.locator(".run-gate")
                    .get_by_label(re.compile("I am authorized"))
                    .check()
                )
                await page.get_by_label(re.compile("I authorize this journey")).check()
                await page.get_by_role("button", name="Run analysis →").click()

            await import_journey(
                names[0],
                [
                    {"id": "open", "action": "navigate"},
                    {
                        "id": "base",
                        "action": "assert_visible",
                        "target": {"role": "heading", "name": "Base"},
                    },
                ],
                {
                    "enabled": True,
                    "recover_navigation": True,
                    "max_depth": 1,
                    "max_actions": 3,
                },
            )
            await page.get_by_label("Profile name", exact=True).fill(profile_name)
            await page.get_by_label("Layout zoom emulation (%)", exact=True).fill("125")
            await page.get_by_role(
                "button", name="Save as new profile", exact=True
            ).click()
            await page.get_by_text(
                "Profile saved. Existing journeys retain their own condition snapshots.",
                exact=True,
            ).wait_for()
            await run()
            await page.get_by_role(
                "button", name="Approve button: Alpha", exact=True
            ).click()
            await page.get_by_role(
                "button",
                name="Approve navigation: Return to configured start",
                exact=True,
            ).click()
            await page.get_by_role(
                "button", name="Approve button: Beta", exact=True
            ).click()
            await page.get_by_role(
                "heading", name="Task outcome: completed", exact=True
            ).wait_for()
            await page.get_by_text("Stopped: action-budget", exact=True).wait_for()
            await page.get_by_text(
                "Executed discovery actions and reachability", exact=True
            ).click()
            await page.evaluate("window.scrollTo(0,0)")
            await page.screenshot(
                path=ROOT / "docs/development/screenshots/approved-branches.png",
                full_page=True,
            )

            mode = "failure"
            app.broken = True
            await import_journey(
                names[1],
                [
                    {"id": "open", "action": "navigate"},
                    {
                        "id": "continue",
                        "action": "activate",
                        "effect": True,
                        "target": {"role": "button", "name": "Continue"},
                    },
                    {
                        "id": "done",
                        "action": "assert_visible",
                        "target": {"role": "heading", "name": "Done"},
                    },
                ],
            )
            await page.get_by_label(
                re.compile("^Saved capability profile")
            ).select_option(label=profile_name)
            assert (
                await page.get_by_label(
                    "Layout zoom emulation (%)", exact=True
                ).input_value()
                == "125"
            )
            await run()
            await page.get_by_role(
                "heading", name="Task outcome: blocked", exact=True
            ).wait_for()

            async def replay(verdict):
                await page.get_by_role(
                    "button", name="Review browser re-execution", exact=True
                ).click()
                await page.get_by_label(re.compile("I authorize this target")).check()
                await page.get_by_role(
                    "button", name="Run approved replay", exact=True
                ).click()
                await page.get_by_text(
                    re.compile("Live re-execution:.*" + verdict)
                ).wait_for()

            await replay("observed-again")
            app.broken = False
            await replay("not-reproduced-in-this-run")
            await page.get_by_role(
                "heading", name="Task outcome: completed", exact=True
            ).wait_for()
            await page.get_by_text(
                "Compare historical and live step evidence", exact=True
            ).click()
            await page.evaluate("window.scrollTo(0,0)")
            await page.screenshot(
                path=ROOT / "docs/development/screenshots/failure-replay.png",
                full_page=True,
            )
            cdp = await page.context.new_cdp_session(page)
            await cdp.send(
                "Runtime.evaluate",
                {
                    "expression": (ROOT / "node_modules/axe-core/axe.min.js").read_text(
                        encoding="utf-8"
                    ),
                    "allowUnsafeEvalBlockedByCSP": True,
                },
            )
            audit = await page.evaluate(
                "async()=>{const r=await axe.run(document);return {violations:r.violations.map(v=>v.id),incomplete:r.incomplete.map(v=>v.id)}}"
            )
            assert not audit["violations"], audit
            projects = await page.evaluate(
                "async names => (await window.__TAURI_INTERNALS__.invoke('worker_request',{method:'project.list',params:{}})).filter(p=>names.includes(p.name))",
                names,
            )
            actual_runs = []
            for project in projects:
                actual_runs.extend(
                    await page.evaluate(
                        "id=>window.__TAURI_INTERNALS__.invoke('worker_request',{method:'run.list',params:{project_id:id}})",
                        project["id"],
                    )
                )
            assert len(actual_runs) == 4
            (ROOT / "docs/hackyard/native-features-runs.json").write_text(
                json.dumps(actual_runs, indent=2) + "\n", encoding="utf-8"
            )
            # Normal UI removal is limited to these unique, owned records.
            await page.get_by_role(
                "button", name="02 Journey builder", exact=True
            ).click()
            await page.get_by_label(
                re.compile("^Saved capability profile")
            ).select_option(label=profile_name)
            await page.get_by_role(
                "button", name="Remove from library", exact=True
            ).click()
            await page.get_by_role("button", name="01 Projects").click()
            for name in names:
                row = page.get_by_role("row").filter(
                    has=page.get_by_role("button", name=name, exact=True)
                )
                await row.get_by_role("button", name="Delete", exact=True).click()
                await (
                    page.get_by_role("dialog", name=f"Delete {name}?")
                    .get_by_role("button", name="Delete permanently", exact=True)
                    .click()
                )
                await row.wait_for(state="detached")
            result = {
                "scope": "Packaged native WebView2/private IPC/owned Chromium HTTP target on development laptop",
                "approved_branch_actions": 3,
                "replay_before_correction": "observed-again",
                "replay_after_correction": "not-reproduced-in-this-run",
                "profile_reused_across_projects": True,
                "layout_zoom_percent": 125,
                "owned_records_removed": True,
                "duration_seconds": round(time.monotonic() - started, 3),
                "run_durations_seconds": [
                    r.get("duration_seconds") for r in actual_runs
                ],
                "observed_graph_nodes": [len(r["nodes"]) for r in actual_runs],
                "axe": audit,
            }
            (ROOT / "docs/hackyard/native-features-verification.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
