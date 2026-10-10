"""Real native comparison UI/IPC/browser regression on a uniquely named owned target."""

import argparse
import asyncio
import json
import re
import sys
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
    name = "Native comparison " + uuid4().hex[:8]
    with CompatibilityApp() as app:

        def document():
            tag = "div role=button" if app.broken else "button"
            closing = "div" if app.broken else "button"
            return (
                '<!doctype html><html lang="en"><title>Owned comparison</title>'
                "<main><h1>Application</h1>"
                f"<{tag} onclick=\"document.querySelector('h1').textContent='Done'\">"
                f"Continue</{closing}></main></html>"
            )

        app.html = document
        journey = Journey(
            name="Native keyboard correction",
            target=app.origin,
            allow_local=True,
            tab_budget=8,
            privacy={"capture_page_text": True},
            steps=[
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
        definition = ROOT / "dist" / (name.replace(" ", "-") + ".json")
        definition.write_text(journey.model_dump_json(indent=2), encoding="utf-8")
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(args.endpoint)
            page = next(
                p
                for c in browser.contexts
                for p in c.pages
                if "tauri.localhost" in p.url
            )
            page.set_default_timeout(30000)
            await page.get_by_role("button", name="01 Projects").click()
            await page.get_by_role("button", name="+ Website investigation").click()
            await page.get_by_label("Project name", exact=True).fill(name)
            await page.locator("input[type=file]").first.set_input_files(definition)
            await page.get_by_text(
                "Imported and validated journey as a new project", exact=True
            ).wait_for()

            async def start():
                await (
                    page.locator(".run-gate")
                    .get_by_label(re.compile("I am authorized"))
                    .check()
                )
                await page.get_by_label(re.compile("I authorize this journey")).check()
                await page.get_by_role("button", name="Run analysis →").click()

            app.broken = True
            await start()
            await page.get_by_role(
                "heading", name="Task outcome: blocked", exact=True
            ).wait_for()
            await page.get_by_text(
                "keyboard-unreachable / continue", exact=True
            ).wait_for()
            await page.get_by_role("button", name="Inspect run").first.wait_for()
            app.broken = False
            await page.get_by_role(
                "button", name="02 Journey builder", exact=True
            ).click()
            await start()
            await page.get_by_role(
                "heading", name="Task outcome: completed", exact=True
            ).wait_for()
            await page.get_by_role(
                "heading", name="Journey comparison", exact=True
            ).wait_for()
            previous = page.get_by_label("Previous run", exact=True)
            options = await previous.locator("option").evaluate_all(
                "es=>es.filter(e=>e.value).map(e=>({value:e.value,text:e.textContent}))"
            )
            baseline = next(o["value"] for o in options if o["text"].endswith("failed"))
            await previous.select_option(baseline)
            await page.get_by_role(
                "button", name="Compare findings", exact=True
            ).focus()
            await page.keyboard.press("Enter")
            await page.get_by_text("passed-retest", exact=True).wait_for()
            await page.get_by_text(
                "Baseline: blocked · Candidate: completed", exact=True
            ).wait_for()
            await page.get_by_text(
                "First divergent execution step: continue", exact=True
            ).wait_for()
            await page.get_by_text("Configurations match", exact=True).wait_for()
            await page.screenshot(
                path=ROOT / "docs/development/screenshots/journey-comparison.png",
                full_page=True,
            )
            cdp = await page.context.new_cdp_session(page)
            injection = await cdp.send(
                "Runtime.evaluate",
                {
                    "expression": (ROOT / "node_modules/axe-core/axe.min.js").read_text(
                        encoding="utf-8"
                    ),
                    "allowUnsafeEvalBlockedByCSP": True,
                },
            )
            assert "exceptionDetails" not in injection
            audit = await page.evaluate(
                "async()=>{const r=await axe.run(document);return {violations:r.violations.map(v=>v.id),incomplete:r.incomplete.map(v=>v.id)}}"
            )
            assert not audit["violations"], audit
            await page.get_by_role(
                "button", name="Inspect baseline run", exact=True
            ).click()
            await page.get_by_role(
                "heading", name="Task outcome: blocked", exact=True
            ).wait_for()
            assert await page.get_by_text("passed-retest", exact=True).count() == 0
            # Remove only the uniquely named project created above through normal UI approval.
            await page.get_by_role("button", name="01 Projects").click()
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
                "scope": "Actual packaged native WebView2, private IPC and owned Chromium target; same development laptop",
                "broken_outcome": "blocked",
                "candidate_outcome": "completed",
                "keyboard_comparison": "passed-retest",
                "first_divergent_step": "continue",
                "stale_comparison_hidden": True,
                "synthetic_project_removed": True,
                "axe": audit,
            }
            (ROOT / "docs/hackyard/native-comparison-verification.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
