"""Kill only this development app's worker and verify actual host recovery and child cleanup."""

import asyncio
import argparse
import json
import re
from pathlib import Path

import psutil
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:9223")
    parser.add_argument(
        "--exe",
        type=Path,
        default=ROOT / "apps/desktop/src-tauri/target/debug/accessmaze.exe",
    )
    args = parser.parse_args()
    expected = args.exe.resolve()
    desktop = next(
        p
        for p in psutil.process_iter()
        if p.name().lower() == "accessmaze.exe" and Path(p.exe()).resolve() == expected
    )
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.endpoint)
        page = next(
            p
            for c in browser.contexts
            for p in c.pages
            if "1420" in p.url or "tauri.localhost" in p.url
        )
        page.set_default_timeout(30000)
        await page.get_by_role("button", name="01 Projects").click()
        await (
            page.locator(".fixture-list")
            .get_by_role("button", name=re.compile("Long-running journey"))
            .click()
        )
        await page.get_by_label("Project name", exact=True).fill(
            "Desktop crash recovery / synthetic"
        )
        await page.get_by_label(re.compile("I am authorized")).check()
        await page.get_by_label(re.compile("I authorize this journey")).check()
        await page.get_by_role("button", name="Run analysis →").click()
        await (
            page.locator(".run-steps li")
            .filter(has_text="slow")
            .filter(has_text="running")
            .wait_for()
        )
        worker = next(
            p
            for p in desktop.children(recursive=True)
            if p.name().lower() == "accessmaze-worker.exe"
            or "accessmaze.worker" in " ".join(p.cmdline())
        )
        chromium = [
            p for p in worker.children(recursive=True) if "chrome" in p.name().lower()
        ]
        assert chromium, "Real Chromium was not running"
        worker.kill()
        worker.wait(timeout=5)
        await (
            page.locator(".section-heading .status")
            .filter(has_text=re.compile("^interrupted$"))
            .wait_for()
        )
        await (
            page.locator(".run-steps li")
            .filter(has_text="slow")
            .filter(has_text="interrupted")
            .wait_for()
        )
        for _ in range(100):
            if not any(p.is_running() for p in chromium):
                break
            await asyncio.sleep(0.1)
        assert not any(p.is_running() for p in chromium), (
            "Worker crash left Chromium running"
        )
        evidence = {
            "host_restarted_worker": True,
            "run_marked_interrupted": True,
            "chromium_processes_cleaned": len(chromium),
            "scope": "Real Windows desktop and Windows job object",
            "executable": str(expected.relative_to(ROOT)),
        }
        (ROOT / "docs/testing/desktop-crash.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
