import asyncio

import pytest

from accessmaze.models import Step
from accessmaze.runner import RunControl, check_host, execute
from accessmaze.templates import template


def test_private_hosts_require_explicit_authorization():
    with pytest.raises(ValueError, match="authorization"):
        check_host("http://127.0.0.1:8888", False)
    check_host("http://127.0.0.1:8888", True)


@pytest.mark.browser
def test_cross_origin_redirect_is_blocked_and_result_is_inconclusive(
    store, project, fixtures, axe_path, monkeypatch
):
    from accessmaze import fixtures as module

    original = module.fixture_html

    def html(kind):
        if kind == "accessible":
            return """<!doctype html><html lang="en"><title>Redirect policy</title><main>
<a href="http://127.0.0.1:1/private">Continue</a><h1>Original page</h1></main></html>"""
        return original(kind)

    monkeypatch.setattr(module, "fixture_html", html)
    p = project()
    journey = template()
    journey.steps = [
        journey.steps[0],
        Step(
            id="leave", action="activate", effect=True, target={"role": "link", "name": "Continue"}
        ),
        Step(
            id="target",
            action="assert_visible",
            target={"role": "heading", "name": "Private service"},
        ),
    ]
    result = asyncio.run(execute(store, p["id"], journey, RunControl(), fixtures, axe_path))
    assert "Cross-origin request blocked" in result["limitations"]
    assert result["status"] == "failed"
    assert all(f["verification"] == "inconclusive" for f in result["findings"])


@pytest.mark.browser
def test_cancel_before_preparation_never_launches_browser(store, project, fixtures, axe_path):
    p = project()
    control = RunControl()
    control.cancel.set()
    result = asyncio.run(execute(store, p["id"], template(), control, fixtures, axe_path))
    assert result["status"] == "cancelled"
    assert not result["steps"]
    assert "browser" not in result["environment"]
