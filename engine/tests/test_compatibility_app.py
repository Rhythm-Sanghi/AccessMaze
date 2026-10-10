import asyncio
import base64

import pytest
from compatibility_app import CompatibilityApp

from accessmaze.inputs import RunInputs
from accessmaze.models import ProjectInput
from accessmaze.runner import RunControl, execute

pytestmark = pytest.mark.browser


def test_multistep_spa_modal_upload_conditional_and_connectivity(store, fixtures, axe_path):
    with CompatibilityApp() as app:
        journey = app.journey()
        project = store.save_project(ProjectInput(name="Owned compatibility app", journey=journey))
        inputs = RunInputs(
            journey,
            {
                "files": {
                    "document": {
                        "name": "synthetic.txt",
                        "base64": base64.b64encode(b"No personal data").decode(),
                    }
                }
            },
        )
        result = asyncio.run(
            execute(store, project["id"], journey, RunControl(), fixtures, axe_path, inputs=inputs)
        )
        assert result["status"] == "completed_with_limitations", (
            result["findings"],
            result.get("error"),
        )
        assert not result["coverage_compromised"]
        assert not result["findings"]
        assert app.posts[0]["document"] == b"No personal data"
        assert app.posts[0]["route"] == b"international"
        assert app.posts[0]["reference"] == b"TEST-ONLY"
        assert app.summary()["api_options_requests"] == 1
