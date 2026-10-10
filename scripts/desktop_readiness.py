"""Actual native UI regression: keyboard navigation, safe errors and dialog focus."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9224")
    args = parser.parse_args()
    name = "Readiness synthetic " + uuid4().hex[:8]
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.endpoint)
        page = next(
            p for c in browser.contexts for p in c.pages if "tauri.localhost" in p.url
        )
        page.set_default_timeout(15000)
        await page.get_by_role("button", name="01 Projects").click()
        await page.get_by_role("button", name="01 Projects").click()
        await page.keyboard.press("Tab")
        assert await page.get_by_role("button", name="02 Journey builder").evaluate(
            "e=>e===document.activeElement"
        )
        await page.keyboard.press("Enter")
        await page.get_by_role("heading", name="Journey builder", exact=True).wait_for()
        assert await page.evaluate("document.activeElement.tagName") == "H1"
        await page.get_by_role("button", name="01 Projects").click()
        await page.get_by_role(
            "button", name="+ Website investigation", exact=True
        ).click()
        await page.get_by_label("Project name", exact=True).fill(name)
        private = "synthetic-private-invalid-target"
        target = page.get_by_label("Target URL", exact=True)
        await target.fill(private)
        await page.get_by_role("button", name="Save project", exact=True).click()
        alert = page.get_by_role("alert")
        await alert.wait_for()
        message = await alert.inner_text()
        assert "Invalid request schema at journey" in message
        assert "Review required fields" in message and private not in message
        assert await target.input_value() == private
        await target.fill("https://example.invalid")
        await page.get_by_role("button", name="Save project", exact=True).click()
        await page.get_by_text("Project and journey saved", exact=True).wait_for()
        await page.get_by_role("button", name="01 Projects").click()
        row = page.get_by_role("row").filter(
            has=page.get_by_role("button", name=name, exact=True)
        )
        delete = row.get_by_role("button", name="Delete", exact=True)
        await delete.click()
        dialog = page.get_by_role("dialog", name=f"Delete {name}?")
        await dialog.wait_for()
        assert (
            await page.evaluate("document.activeElement.textContent") == "Keep project"
        )
        await page.keyboard.press("Escape")
        await dialog.wait_for(state="hidden")
        assert await delete.evaluate("e=>e===document.activeElement")
        # Remove only the uniquely named disposable project created by this script.
        await delete.click()
        await dialog.get_by_role(
            "button", name="Delete permanently", exact=True
        ).click()
        await row.wait_for(state="detached")
        result = {
            "keyboard_navigation_and_heading_focus": "passed",
            "actionable_private_schema_error": "passed",
            "invalid_input_retained": "passed",
            "native_dialog_initial_and_restored_focus": "passed",
            "owned_test_project_removed": True,
            "scope": "Actual packaged WebView2/IPC. No NVDA, contrast or exhaustive keyboard claim.",
        }
        (ROOT / "docs/testing/desktop-readiness.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
