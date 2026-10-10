import asyncio

import pytest
from pydantic import ValidationError
from test_website_policy import website

from accessmaze.models import Journey, NetworkPolicy, ProjectInput
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template


def test_frame_permission_is_explicit_and_target_requires_permission():
    with pytest.raises(ValidationError, match="authorized-application"):
        NetworkPolicy(embedded_frames=True)
    data = template().model_dump()
    data["steps"][-1]["target"]["frame_name"] = "checkout"
    with pytest.raises(ValidationError, match="frame permission"):
        Journey.model_validate(data)


@pytest.mark.browser
def test_authorized_frame_journey_keeps_write_and_origin_guards(store, fixtures, axe_path):
    async def exercise():
        with website(
            {
                "/": (
                    200,
                    {"Content-Type": "text/html"},
                    '<h1>Embedded task</h1><button onclick="'
                    "document.querySelector('h1').textContent='Done'; "
                    "fetch('/write',{method:'POST'})\">Continue</button>",
                ),
                "/write": (200, {}, "written"),
            }
        ) as (child, hits):
            with website(
                {
                    "/": (
                        200,
                        {"Content-Type": "text/html"},
                        '<h1>Host</h1><iframe name="checkout" title="Checkout" '
                        f'src="{child}"></iframe>',
                    )
                }
            ) as (host, _):
                data = template().model_dump()
                data.update(target=host, allow_local=True, max_seconds=15)
                data["profile"]["action_timeout_ms"] = 1000
                data["steps"] = [
                    data["steps"][0],
                    {
                        "id": "continue",
                        "action": "activate",
                        "effect": True,
                        "target": {"role": "button", "name": "Continue", "frame_name": "checkout"},
                    },
                    {
                        "id": "done",
                        "action": "assert_visible",
                        "target": {"role": "heading", "name": "Done", "frame_name": "checkout"},
                    },
                ]
                data["network"] = {
                    "mode": "authorized-application",
                    "embedded_frames": True,
                    "navigation_origins": [child],
                }
                journey = Journey.model_validate(data)
                project = store.save_project(ProjectInput(name="Frame task", journey=journey))
                result = await execute(
                    store, project["id"], journey, RunControl(), fixtures, axe_path
                )
                assert result["outcome"]["status"] == "completed", result
                assert hits.count(("POST", "/write")) == 1
                assert not result["coverage_compromised"]
                # Read-only resource approval never grants frame navigation.
                hits.clear()
                data["network"].update(navigation_origins=[], resource_origins=[child])
                journey = Journey.model_validate(data)
                result = await execute(
                    store, project["id"], journey, RunControl(), fixtures, axe_path
                )
                assert not hits
                assert result["coverage_compromised"]
                assert result["outcome"]["status"] == "inconclusive"
                assert all(
                    f["classification"] == "network-policy-restriction" for f in result["findings"]
                )

    asyncio.run(exercise())


@pytest.mark.browser
def test_restricted_frame_and_ambiguous_frames_are_not_accessibility_failures(
    store, fixtures, axe_path
):
    async def exercise():
        routes = {}
        with website(routes) as (host, hits):
            routes["/"] = (
                200,
                {"Content-Type": "text/html"},
                '<h1>Host</h1><iframe name="checkout" src="/child"></iframe>'
                '<iframe name="checkout" src="/child"></iframe>',
            )
            routes["/child"] = (200, {}, "<h1>Child</h1>")
            data = template().model_dump()
            data.update(target=host, allow_local=True)
            data["steps"] = [
                data["steps"][0],
                {
                    "id": "host",
                    "action": "assert_visible",
                    "target": {"role": "heading", "name": "Host"},
                },
            ]
            journey = Journey.model_validate(data)
            project = store.save_project(ProjectInput(name="Restricted frame", journey=journey))
            result = await execute(store, project["id"], journey, RunControl(), fixtures, axe_path)
            assert ("GET", "/child") not in hits
            assert result["coverage_compromised"]
            data["network"] = {"mode": "authorized-application", "embedded_frames": True}
            data["steps"][-1]["target"].update(name="Child", frame_name="checkout")
            result = await execute(
                store, project["id"], Journey.model_validate(data), RunControl(), fixtures, axe_path
            )
            assert result["findings"][0]["classification"] == "test-definition-error"
            assert result["findings"][0]["verification"] == "inconclusive"

    asyncio.run(exercise())
