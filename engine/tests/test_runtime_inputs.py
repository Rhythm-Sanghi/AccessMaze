import asyncio
import base64
import json

import pytest
from test_website_policy import website

from accessmaze.inputs import RunInputs
from accessmaze.models import Journey, ProjectInput, Step
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template


def runtime_journey():
    journey = template()
    journey.steps[1] = Step(
        id="name",
        action="fill",
        value_from="applicant",
        target={"role": "textbox", "name": "Applicant name"},
    )
    return journey


def test_runtime_inputs_require_exact_keys_and_preserve_only_a_private_signature():
    journey = runtime_journey()
    with pytest.raises(ValueError, match="exactly"):
        RunInputs(journey)
    with pytest.raises(ValueError, match="exactly"):
        RunInputs(journey, {"values": {"applicant": "secret", "extra": "unexpected"}})
    first = RunInputs(journey, {"values": {"applicant": "private value"}}, b"worker key")
    same = RunInputs(journey, {"values": {"applicant": "private value"}}, b"worker key")
    changed = RunInputs(journey, {"values": {"applicant": "changed"}}, b"worker key")
    assert first.signature == same.signature
    assert first.signature != changed.signature
    assert "private value" not in first.signature


def test_imported_uploads_cannot_read_filesystem_paths():
    with pytest.raises(ValueError):
        Step(
            id="upload", action="upload", file_label="Document", value="C:/private.txt", effect=True
        )
    journey = template()
    journey.steps.insert(
        1,
        Step(
            id="upload", action="upload", file_label="Document", value_from="document", effect=True
        ),
    )
    with pytest.raises(ValueError):
        RunInputs(journey, {"files": {"document": {"name": "../../private.txt", "base64": ""}}})
    with pytest.raises(ValueError, match="buffer"):
        RunInputs(journey, {"files": {"document": {"name": "test.txt", "base64": "!invalid"}}})


@pytest.mark.browser
def test_password_login_approved_redirect_and_actual_upload_are_private(store, fixtures, axe_path):
    received = []
    secret = "synthetic-password-381"
    file_content = b"synthetic-upload-private-725"

    def login(handler):
        received.append(handler.rfile.read(int(handler.headers["Content-Length"])))
        return 200, {"Set-Cookie": "test_session=approved; HttpOnly; SameSite=Lax"}, "ok"

    def upload(handler):
        assert "test_session=approved" in handler.headers.get("Cookie", "")
        received.append(handler.rfile.read(int(handler.headers["Content-Length"])))
        return 200, {"Access-Control-Allow-Origin": "*"}, "ok"

    auth_routes = {"/session": (200, {}, login)}
    with website(auth_routes) as (auth, _):
        routes = {
            "/": (200, {"Content-Type": "text/html"}, f'<a href="{auth}/">Sign in</a>'),
            "/upload": (200, {}, upload),
        }
        with website(routes) as (app, _):
            login_html = f"""<label>Password<input type="password" id="password"></label>
<button onclick="fetch('{auth}/session',{{method:'POST',body:password.value,credentials:'include'}})
.then(()=>location.href='{app}/account')">Sign in</button>"""
            auth_routes["/"] = (200, {"Content-Type": "text/html"}, login_html)
            routes["/"] = (302, {"Location": auth + "/"}, "")
            routes["/account"] = (
                200,
                {"Content-Type": "text/html"},
                """<h1>Account ready</h1>
<label>Document<input type="file" id="doc"></label>
<script>doc.onchange=async()=>{const data=new FormData();data.append('file',doc.files[0]);
await fetch('/upload',{method:'POST',body:data});
document.querySelector('h1').textContent='Upload complete'}</script>""",
            )
            journey = Journey(
                name="Authorized account upload",
                target=app,
                allow_local=True,
                network={"navigation_origins": [auth]},
                steps=[
                    Step(id="open", action="navigate"),
                    Step(
                        id="password",
                        action="fill",
                        value_from="password",
                        target={"by": "label", "role": "textbox", "name": "Password"},
                    ),
                    Step(
                        id="login",
                        action="activate",
                        effect=True,
                        target={"role": "button", "name": "Sign in"},
                    ),
                    Step(
                        id="account",
                        action="assert_visible",
                        target={"role": "heading", "name": "Account ready"},
                    ),
                    Step(
                        id="upload",
                        action="upload",
                        effect=True,
                        file_label="Document",
                        value_from="document",
                    ),
                    Step(
                        id="done",
                        action="assert_visible",
                        target={"role": "heading", "name": "Upload complete"},
                    ),
                ],
            )
            p = store.save_project(ProjectInput(name="Account upload", journey=journey))
            inputs = RunInputs(
                journey,
                {
                    "values": {"password": secret},
                    "files": {
                        "document": {
                            "name": "private-file.txt",
                            "base64": base64.b64encode(file_content).decode(),
                        }
                    },
                },
            )
            result = asyncio.run(
                execute(store, p["id"], journey, RunControl(), fixtures, axe_path, inputs=inputs)
            )
            assert result["status"] == "completed_with_limitations", json.dumps(result["findings"])
            assert not result["findings"], result
            assert secret.encode() in received[0]
            assert file_content in received[1]
            assert b"private-file.txt" in received[1]
            persisted = json.dumps(result) + json.dumps(store.project(p["id"]))
            for sensitive in (secret, file_content.decode(), "private-file.txt"):
                assert sensitive not in persisted
            assert any("file-picker" in limit for limit in result["limitations"])


@pytest.mark.browser
def test_short_runtime_values_do_not_corrupt_run_metadata(store, project, fixtures, axe_path):
    journey = runtime_journey()
    p = project()
    inputs = RunInputs(journey, {"values": {"applicant": "a"}})
    result = asyncio.run(
        execute(store, p["id"], journey, RunControl(), fixtures, axe_path, inputs=inputs)
    )
    assert result["status"] == "completed_with_limitations"
    assert result["project_id"] == p["id"]
    assert all(step["status"] == "passed" for step in result["steps"])
