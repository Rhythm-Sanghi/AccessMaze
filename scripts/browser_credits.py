"""Extract notices from the exact full Chromium binary, with networking offline."""

import argparse
import asyncio
import hashlib
import html
import json
from pathlib import Path

from playwright.async_api import async_playwright


async def capture(browser_root, output):
    (executable,) = browser_root.glob("chromium-*/chrome-win64/chrome.exe")
    output.mkdir(parents=True, exist_ok=False)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=str(executable))
        try:
            context = await browser.new_context(offline=True)
            page = await context.new_page()
            await page.goto("chrome://credits")
            # inner_text excludes the collapsed license bodies on chrome://credits.
            text = await page.locator("body").text_content()
            count = await page.locator(".license").count()
            if len(text) < 1000000 or count < 100 or "Chromium" not in text:
                raise RuntimeError("Chromium credits unexpectedly incomplete")
            (output / "chromium-credits.html").write_text(
                '<!doctype html><html lang="en"><meta charset="utf-8">'
                '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
                "style-src 'unsafe-inline'\"><title>Chromium credits</title>"
                "<style>pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>"
                "<h1>Exact bundled Chromium credits</h1><pre>"
                + html.escape(text)
                + "</pre>",
                encoding="utf-8",
            )
            (output / "chromium-credits.txt").write_text(text, encoding="utf-8")
            result = {
                "browser": browser.version,
                "license_sections": count,
                "executable_sha256": hashlib.sha256(
                    executable.read_bytes()
                ).hexdigest(),
                "credits_text_characters": len(text),
                "scope": "Exact full Chromium chrome://credits offline; headless-shell and separately shipped binaries still require verification",
            }
            (output / "provenance.json").write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            return result
        finally:
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(asyncio.run(capture(args.browsers.resolve(), args.output)), indent=2)
    )
