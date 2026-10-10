"""Cancel a real packaged browser run and verify persisted partial evidence/cleanup."""

import argparse
import asyncio
import json
import re
from pathlib import Path
from uuid import uuid4

import psutil
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9224")
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    expected = args.exe.resolve()
    desktop = next(
        p
        for p in psutil.process_iter()
        if p.name().lower() == "accessmaze.exe" and Path(p.exe()).resolve() == expected
    )
    name = "Native cancellation " + uuid4().hex[:8]
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.endpoint)
        page = next(
            p for c in browser.contexts for p in c.pages if "tauri.localhost" in p.url
        )
        page.set_default_timeout(30000)
        await page.get_by_role("button", name="01 Projects").click()
        await (
            page.locator(".fixture-list")
            .get_by_role("button", name=re.compile("Long-running journey"))
            .click()
        )
        await page.get_by_label("Project name", exact=True).fill(name)
        await (
            page.locator(".run-gate")
            .get_by_label(re.compile("I am authorized"))
            .check()
        )
        await page.get_by_label(re.compile("I authorize this journey")).check()
        await page.get_by_role("button", name="Run analysis →").click()
        await (
            page.locator(".run-steps li")
            .filter(has_text="slow")
            .filter(has_text="running")
            .wait_for()
        )
        chromium = [
            p for p in desktop.children(recursive=True) if "chrome" in p.name().lower()
        ]
        assert chromium, "No actual Chromium process was running"
        await (
            page.get_by_role("region", name="Analysis workspace")
            .get_by_role("button", name="Emergency stop", exact=True)
            .click()
        )
        await (
            page.locator(".section-heading .status")
            .filter(has_text=re.compile("^cancelled$"))
            .wait_for()
        )
        for _ in range(100):
            if not any(p.is_running() for p in chromium):
                break
            await asyncio.sleep(0.1)
        assert not any(p.is_running() for p in chromium), (
            "Cancellation retained Chromium"
        )
        projects = await page.evaluate(
            "()=>window.__TAURI_INTERNALS__.invoke('worker_request',{method:'project.list',params:{}})"
        )
        project = next(p for p in projects if p["name"] == name)
        runs = await page.evaluate(
            "id=>window.__TAURI_INTERNALS__.invoke('worker_request',{method:'run.list',params:{project_id:id}})",
            project["id"],
        )
        assert len(runs) == 1
        run = runs[0]
        assert run["status"] == "cancelled" and run["outcome"]["status"] == "cancelled"
        assert run["nodes"] and any(s["status"] == "passed" for s in run["steps"])
        result = {
            "scope": "Packaged WebView2/private IPC/actual Chromium on development laptop",
            "executable": str(expected.relative_to(ROOT)),
            "emergency_stop": "passed",
            "persisted_status": run["status"],
            "task_outcome": run["outcome"]["status"],
            "retained_graph_nodes": len(run["nodes"]),
            "chromium_processes_cleaned": len(chromium),
        }
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
        result["owned_project_removed"] = True
        (ROOT / "docs/hackyard/native-cancellation-verification.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
