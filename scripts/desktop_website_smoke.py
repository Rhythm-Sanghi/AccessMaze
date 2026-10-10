"""Verify actual packaged WebView2 approval and recording using an owned HTTP app."""

import argparse
import asyncio
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:9224")
    args = parser.parse_args()
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append((self.command, self.path))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""<html lang=en><title>Owned approval application</title>
              <main><h1>Base</h1><button onclick="fetch('/write',{method:'POST'}).then(()=>{
              document.querySelector('h1').textContent='Next';this.remove()})">Advance</button>
              <button>Remain</button></main></html>""")

        def do_POST(self):
            hits.append((self.command, self.path))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
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
            await page.get_by_label("Project name", exact=True).fill(
                "Native approved website smoke"
            )
            await page.get_by_label("Target URL", exact=True).fill(
                f"http://127.0.0.1:{server.server_port}"
            )
            await page.get_by_label("Step 2 name", exact=True).fill("Base")
            await page.get_by_label(
                "Authorize private and loopback network target access"
            ).check()
            await page.get_by_label(re.compile("Propose website buttons")).check()
            await page.get_by_label("Time budget (seconds)").fill("120")
            gate = page.locator(".run-gate")
            await gate.get_by_label(re.compile("I am authorized")).check()
            await gate.get_by_label(re.compile("I authorize this journey")).check()
            await page.get_by_role("button", name="Run analysis →").click()
            approve = page.get_by_role(
                "button", name="Approve button: Advance", exact=True
            )
            await approve.wait_for()
            assert not any(method == "POST" for method, _ in hits), hits
            await page.screenshot(
                path=ROOT / "docs/development/screenshots/website-approval.png",
                full_page=True,
            )
            await approve.click()
            await approve.wait_for(state="hidden")
            await page.get_by_role(
                "button", name="Approve button: Remain", exact=True
            ).wait_for()
            assert hits.count(("POST", "/write")) == 1, hits
            assert hits.count(("GET", "/")) == 1, "Website was reset or replayed"
            await page.get_by_role(
                "button", name="Finish without further actions"
            ).click()
            await (
                page.locator(".section-heading .status")
                .filter(has_text="completed with limitations")
                .wait_for()
            )
            await page.get_by_role("button", name="02 Journey").click()
            recorder = page.get_by_role("region", name="Record a browser journey")
            await recorder.get_by_label(re.compile("I am authorized to record")).check()
            await recorder.get_by_label(re.compile("I authorize interactions")).check()
            await recorder.get_by_role("button", name="Open recording browser").click()
            capture = recorder.get_by_role(
                "button", name="Capture current H1 as completion"
            )
            await capture.wait_for(state="visible")
            await page.wait_for_function(
                "()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='Capture current H1 as completion'&&!b.disabled)"
            )
            await capture.click()
            await (
                recorder.get_by_role("listitem")
                .filter(has_text="assert_visible")
                .wait_for()
            )
            await recorder.get_by_role("button", name="Stop recording").click()
            await recorder.get_by_role(
                "button", name="Review these steps in the editor"
            ).wait_for()
            result = {
                "packaged_website_approval": "passed",
                "posts": 1,
                "external_replay": False,
                "packaged_headed_recorder": "passed",
                "completion_capture": "Base",
                "scope": "Owned HTTP server, actual native UI/IPC/browser",
            }
            (ROOT / "docs/testing/desktop-website.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print(json.dumps(result, indent=2))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    asyncio.run(main())
