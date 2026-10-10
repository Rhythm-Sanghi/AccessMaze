"""Exercise a running development desktop through its actual WebView2 and IPC.

Start with WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9223.
The debugging port is test-only; it is not enabled by application code.
"""

import asyncio
import argparse
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:9223")
    args = parser.parse_args()
    output = ROOT / "docs" / "development" / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.endpoint)
        page = next(
            p
            for c in browser.contexts
            for p in c.pages
            if "1420" in p.url or "tauri.localhost" in p.url
        )
        page.set_default_timeout(30000)
        await page.get_by_text("Worker connected", exact=True).wait_for()
        await page.get_by_role("button", name="01 Projects").click()
        await page.screenshot(path=output / "projects.png", full_page=True)
        for kind, expected in [
            ("Keyboard blocker", "keyboard-unreachable / date"),
            ("Accessible application", "completed with limitations"),
            ("Conditional application", "completed with limitations"),
        ]:
            await page.get_by_role("button", name="01 Projects").click()
            await (
                page.locator(".fixture-list")
                .get_by_role("button", name=re.compile(kind))
                .click()
            )
            await page.get_by_label("Project name", exact=True).fill(
                f"Desktop smoke / {kind}"
            )
            await page.get_by_label(re.compile("I am authorized")).check()
            await page.get_by_label(re.compile("I authorize this journey")).check()
            await page.get_by_role("button", name="Run analysis →").click()
            await page.get_by_text(expected, exact=True).first.wait_for()
            status = (
                "failed" if kind == "Keyboard blocker" else "completed with limitations"
            )
            await (
                page.locator(".section-heading .status")
                .filter(has_text=re.compile(f"^{status}$"))
                .wait_for()
            )
            await page.get_by_role("button", name="Inspect run").first.wait_for()
            await page.screenshot(
                path=output
                / (
                    "keyboard-blocker.png"
                    if kind == "Keyboard blocker"
                    else "conditional-run.png"
                    if kind == "Conditional application"
                    else "accessible-run.png"
                ),
                full_page=True,
            )
        # Test instrumentation only: packaged CSP correctly blocks inline injection.
        # Journey/IPC checks above run with the normal application policy.
        cdp = await page.context.new_cdp_session(page)
        injection = await cdp.send(
            "Runtime.evaluate",
            {
                "expression": (ROOT / "node_modules/axe-core/axe.min.js").read_text(),
                "allowUnsafeEvalBlockedByCSP": True,
            },
        )
        assert "exceptionDetails" not in injection, injection
        audit = await page.evaluate("""async () => {
          const r=await axe.run(document);
          return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,
            targets:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>v.id)};
        }""")
        (output.parent / "desktop-audit.json").write_text(
            json.dumps(audit, indent=2) + "\n", encoding="utf-8"
        )
        await page.get_by_role("button", name="05 Settings").click()
        await page.get_by_label("Appearance").select_option("dark")
        await page.get_by_role("button", name="03 Analysis").click()
        dark = await page.evaluate("""async () => {
          const r=await axe.run(document);
          return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,
            targets:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>v.id)};
        }""")
        await page.screenshot(path=output / "dark-analysis.png", full_page=True)
        await page.get_by_role("button", name="05 Settings").click()
        await page.get_by_label("Appearance").select_option("light")
        await page.get_by_role("button", name="03 Analysis").click()
        (output.parent / "desktop-audit.json").write_text(
            json.dumps({"light": audit, "dark": dark}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {"desktop_flow": "passed", "light": audit, "dark": dark}, indent=2
            )
        )
        assert not audit["violations"], audit
        assert not dark["violations"], dark
        # Closing the CDP connection leaves the desktop application open for inspection.


if __name__ == "__main__":
    asyncio.run(main())
