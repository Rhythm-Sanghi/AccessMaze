"""Verify packaged history, planned manual records and editable replay without AT claims."""

import argparse
import asyncio
import json
import time
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def verify(endpoint, output):
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    name = "Native investigation " + uuid4().hex[:8]
    owned = []
    result = {
        "scope": "Actual packaged WebView2/IPC/frozen worker/Chromium; planned NVDA preparation only, no human or AT execution",
        "result": "failed",
    }
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(endpoint)
        page = next(
            p for c in browser.contexts for p in c.pages if "tauri.localhost" in p.url
        )
        page.set_default_timeout(30000)

        async def call(method, **params):
            return await page.evaluate(
                "x=>window.__TAURI_INTERNALS__.invoke('worker_request',x)",
                {"method": method, "params": params},
            )

        try:
            health = await call("health")
            runs = []
            project = None
            for kind in ["accessible", "broken"]:
                journey = health["templates"][kind]
                journey["name"] = name
                params = {"project": {"name": name, "journey": journey}}
                if project:
                    params["id"] = project["id"]
                project = await call("project.save", **params)
                if project["id"] not in owned:
                    owned.append(project["id"])
                run_id = (
                    await call(
                        "run.start",
                        project_id=project["id"],
                        authorized=True,
                        allow_effects=True,
                    )
                )["id"]
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    run = await call("run.get", id=run_id)
                    if run["status"] not in {
                        "preparing",
                        "running",
                        "paused",
                        "awaiting_approval",
                    }:
                        break
                    await asyncio.sleep(0.1)
                else:
                    raise TimeoutError("Packaged fixture did not finish")
                assert run["outcome"]["status"] == (
                    "completed" if kind == "accessible" else "blocked"
                )
                runs.append(run)
            (output / "runs.json").write_text(
                json.dumps(runs, indent=2), encoding="utf-8"
            )
            history = await call("run.history", project_id=project["id"], limit=1)
            assert history["total"] == 2 and history["next_offset"] == 1
            assert "nodes" not in history["items"][0]
            older = await call(
                "run.history", project_id=project["id"], limit=1, offset=1
            )
            assert older["items"][0]["id"] == runs[0]["id"]
            await page.reload()
            await page.get_by_text("Worker connected", exact=True).wait_for()
            await page.get_by_role("button", name=name, exact=True).click()
            await page.get_by_role("button", name="03 Analysis", exact=True).click()
            await page.get_by_role(
                "button", name="Inspect run", exact=True
            ).first.click()
            await page.get_by_role(
                "heading", name="Task outcome: blocked", exact=True
            ).wait_for()
            panel = page.get_by_role("region", name="Human investigation", exact=True)
            await panel.get_by_text(
                "Prepare or record a manual check", exact=True
            ).click()
            await panel.get_by_role(
                "button", name="Prepare NVDA checklist", exact=True
            ).click()
            assert (
                await panel.get_by_label(
                    "Actual behavior and exact speech or focus", exact=True
                ).input_value()
                == ""
            )
            await panel.get_by_role(
                "button", name="Save human observation", exact=True
            ).click()
            await panel.get_by_text(
                "Human observation saved separately from automated findings.",
                exact=True,
            ).wait_for()
            reviews = await call("review.list", run_id=runs[1]["id"])
            assert len(reviews) == 1 and reviews[0]["status"] == "planned"
            assert not reviews[0]["performed_by_human"] and not reviews[0]["actual"]
            exported = json.loads(
                (await call("report.export", id=runs[1]["id"], format="json"))[
                    "content"
                ]
            )
            assert len(exported["human_reviews"]) == 1
            assert exported["findings"] == runs[1]["findings"]
            for index in [1, 0, 1, 0]:
                await (
                    page.get_by_role("button", name="Inspect run", exact=True)
                    .nth(index)
                    .click()
                )
                await page.get_by_role(
                    "heading",
                    name="Task outcome: " + ("completed" if index == 1 else "blocked"),
                    exact=True,
                ).wait_for()
                assert (
                    await page.get_by_role(
                        "region", name="Human investigation", exact=True
                    ).count()
                    == 1
                )
                assert await page.get_by_role(
                    "region", name="Failure reproduction", exact=True
                ).count() == (0 if index == 1 else 1)
            await page.get_by_role(
                "button", name="Review browser re-execution", exact=True
            ).click()
            await page.get_by_role(
                "button", name="Save as an editable journey", exact=True
            ).click()
            await page.get_by_text("Journey definition", exact=True).wait_for()
            projects = await call("project.list")
            editable = next(p for p in projects if p["name"] == name + " replay")
            owned.append(editable["id"])
            assert (await call("run.history", project_id=editable["id"]))["total"] == 0
            assert not editable["journey"]["exploration"]["enabled"]
            result.update(
                result="passed",
                bounded_history=True,
                planned_review_export=True,
                duplicate_panels_absent=True,
                editable_replay_does_not_execute=True,
                executed_run_ids=[r["id"] for r in runs],
                duration_seconds=round(time.monotonic() - started, 3),
            )
        finally:
            for project_id in owned:
                await call("project.delete", id=project_id)
            result["owned_records_removed"] = True
            (output / "verification.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9224")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(verify(args.endpoint, args.output))


if __name__ == "__main__":
    main()
