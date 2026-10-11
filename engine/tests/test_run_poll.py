import json
import time
from pathlib import Path

import pytest
from test_website_policy import website

from accessmaze.models import Journey, ProjectInput, Request
from accessmaze.worker import Worker


@pytest.mark.browser
def test_real_worker_poll_observes_approval_cancel_and_recovery(tmp_path):
    with website(
        {"/": (200, {"Content-Type": "text/html"}, "<h1>Review</h1><button>Continue</button>")}
    ) as (target, _):
        worker = Worker(tmp_path, Path.cwd())

        def call(method, **params):
            return worker.dispatch(Request(version=1, id="poll", method=method, params=params))

        try:
            journey = Journey.model_validate(
                {
                    "name": "Poll approval and cancellation",
                    "target": target,
                    "allow_local": True,
                    "steps": [
                        {"id": "start", "action": "navigate"},
                        {
                            "id": "heading",
                            "action": "assert_visible",
                            "target": {"role": "heading", "name": "Review"},
                        },
                    ],
                    "exploration": {"enabled": True, "max_actions": 2},
                }
            )
            project = worker.store.save_project(
                ProjectInput(name="Actual polling", journey=journey)
            )
            run_id = call(
                "run.start", project_id=project["id"], authorized=True, allow_effects=True
            )["id"]
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                update = call("run.poll", id=run_id, after_revision=-1)
                if update["run"]["status"] == "awaiting_approval":
                    break
                time.sleep(0.05)
            else:
                pytest.fail("Actual browser did not offer an approval")
            run = update["run"]
            assert run["approval"]["choices"][0]["name"] == "Continue"
            unchanged = call("run.poll", id=run_id, after_revision=update["revision"])
            assert unchanged == {"changed": False, "revision": update["revision"]}
            assert len(json.dumps(unchanged)) < 100
            assert len(json.dumps(run)) > 1000
            for value in [True, "1", -2, 2**53]:
                with pytest.raises(ValueError, match="revision"):
                    call("run.poll", id=run_id, after_revision=value)
            with pytest.raises(ValueError, match="Unknown"):
                call("run.poll", id=run_id, unexpected=True)
            call("run.cancel", id=run_id)
            worker.thread.join(10)
            assert not worker.thread.is_alive()
            final = call("run.poll", id=run_id, after_revision=update["revision"])
            assert final["changed"] and final["run"]["status"] == "cancelled"
            # Recovery increments the saved revision, including older interrupted runs.
            legacy = dict(final["run"])
            legacy["status"] = "running"
            legacy.pop("revision")
            worker.store.save_run(legacy)
            assert call("run.poll", id=run_id, after_revision=-1)["changed"]
            worker.store.recover()
            recovered = call("run.poll", id=run_id, after_revision=-1)
            assert recovered["run"]["status"] == "interrupted"
            assert recovered["revision"] == 1
        finally:
            worker.close()
