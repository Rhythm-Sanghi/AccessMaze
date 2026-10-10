"""Real independent HTTP origins; no request mocking or third-party side effects."""

import asyncio
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from playwright.async_api import async_playwright
from pydantic import ValidationError

from accessmaze.models import NetworkPolicy
from accessmaze.network import BrowserPolicy, canonical_origin
from accessmaze.templates import template


@contextmanager
def website(routes):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            received.append((self.command, self.path))
            status, headers, body = routes.get(self.path, (404, {}, "missing"))
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body.encode())

        def do_POST(self):
            self.do_GET()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", received
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize(
    "origin",
    [
        "https://*.example.org",
        "file:///x",
        "https://a/b",
        "https://a?secret=x",
        "http://u:p@a",
        "http://a:0",
    ],
)
def test_origin_permissions_reject_unsafe_patterns(origin):
    with pytest.raises((ValueError, ValidationError)):
        NetworkPolicy(navigation_origins=[origin])


def test_dns_snapshot_rejects_mixed_private_answers(monkeypatch):
    from accessmaze.network import resolve_host

    monkeypatch.setattr(
        "accessmaze.network.socket.getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("8.8.8.8", 443)), (2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(ValueError, match="authorization"):
        resolve_host("https://example.org", False)
    assert len(resolve_host("https://example.org", True)) == 2
    assert canonical_origin("https://EXAMPLE.org:443/") == "https://example.org"


@pytest.mark.browser
def test_resources_navigation_writes_and_server_redirects_are_separate():
    async def exercise():
        with (
            website(
                {
                    "/asset.js": (
                        200,
                        {"Content-Type": "text/javascript"},
                        "document.querySelector('h1').textContent='Loaded'",
                    )
                }
            ) as (cdn, cdn_hits),
            website({"/private": (200, {}, "private")}) as (private, private_hits),
        ):
            # Change routes in place after ephemeral ports have been allocated.
            routes = {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    f'<h1>Loading</h1><script src="{cdn}/asset.js"></script>',
                ),
                "/redirect": (302, {"Location": private + "/private"}, ""),
                "/write": (200, {}, "saved"),
            }
            # The app handler holds the dictionary supplied above.
            # A separate server below uses these fully resolved URLs.
            with website(routes) as (target, target_hits):
                journey = template()
                journey.target = target
                journey.allow_local = True
                journey.network = NetworkPolicy(resource_origins=[cdn])
                blocked = set()
                policy = BrowserPolicy(journey, target, blocked)
                await policy.prepare()
                async with async_playwright() as pw:
                    browser = await pw.chromium.launch(args=policy.launch_args)
                    context = await browser.new_context(service_workers="block")
                    await policy.install(context)
                    page = await context.new_page()
                    await policy.attach(page)
                    await page.goto(target)
                    await page.get_by_role("heading", name="Loaded").wait_for()
                    assert ("GET", "/asset.js") in cdn_hits
                    await page.evaluate("u=>window.open(u)", private + "/private")
                    await asyncio.sleep(0.15)
                    assert not private_hits, "Popup escaped the context default-deny rule"
                    await page.evaluate("fetch('/write',{method:'POST'}).catch(()=>{})")
                    assert ("POST", "/write") not in target_hits
                    policy.effects = True
                    await page.evaluate("fetch('/write',{method:'POST'})")
                    assert ("POST", "/write") in target_hits
                    await page.evaluate(
                        "u=>fetch(u,{method:'POST'}).catch(()=>{})", cdn + "/asset.js"
                    )
                    assert not any(method == "POST" for method, _ in cdn_hits)
                    try:
                        await page.goto(target + "/redirect", timeout=3000)
                    except Exception:
                        pass
                    assert not private_hits, "Server redirect bypassed origin policy"
                    try:
                        await page.goto(cdn + "/asset.js", timeout=3000)
                    except Exception:
                        pass
                    assert len(cdn_hits) == 1, "Resource permission permitted navigation"
                    await browser.close()

    asyncio.run(exercise())


@pytest.mark.browser
def test_external_evidence_withholds_unrelated_personal_text(store, fixtures, axe_path):
    import json

    from accessmaze.models import ProjectInput, Step
    from accessmaze.runner import RunControl, execute

    with website(
        {
            "/": (
                200,
                {"Content-Type": "text/html"},
                "<title>Private Alice</title><h1>Private Alice</h1><button>Private Alice</button>",
            )
        }
    ) as (target, _):
        journey = template()
        journey.target = target
        journey.allow_local = True
        journey.steps = [
            Step(id="open", action="navigate"),
            Step(
                id="done",
                action="assert_visible",
                target={"role": "heading", "name": "Private Alice"},
            ),
        ]
        p = store.save_project(ProjectInput(name="Website privacy", journey=journey))
        result = asyncio.run(execute(store, p["id"], journey, RunControl(), fixtures, axe_path))
        assert result["status"] == "completed_with_limitations"
        assert "Private Alice" not in json.dumps(result["nodes"])
        assert all(n["observation"]["text_withheld"] for n in result["nodes"])
        assert result["nodes"][0]["id"] == result["nodes"][-1]["id"]


@pytest.mark.browser
def test_dns_snapshot_is_used_by_the_real_browser(monkeypatch):
    import ipaddress

    async def exercise():
        with website({"/": (200, {"Content-Type": "text/html"}, "<h1>Pinned host</h1>")}) as (
            target,
            hits,
        ):
            journey = template()
            journey.target = target.replace("127.0.0.1", "pin.accessmaze.invalid")
            journey.allow_local = True
            monkeypatch.setattr(
                "accessmaze.network.resolve_host", lambda *args: [ipaddress.ip_address("127.0.0.1")]
            )
            policy = BrowserPolicy(journey, journey.target, set())
            await policy.prepare()
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(args=policy.launch_args)
                context = await browser.new_context(service_workers="block")
                await policy.install(context)
                page = await context.new_page()
                await policy.attach(page)
                await page.goto(journey.target)
                assert await page.get_by_role("heading", name="Pinned host").is_visible()
                assert hits
                await browser.close()

    asyncio.run(exercise())
