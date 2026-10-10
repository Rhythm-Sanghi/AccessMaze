import asyncio
import json

import pytest

from accessmaze.inputs import RunInputs
from accessmaze.models import ProjectInput
from accessmaze.replay import prepare_replay
from accessmaze.runner import RunControl, execute
from accessmaze.templates import template


@pytest.mark.browser
def test_real_failure_replay_and_correction_preserve_history(store, fixtures, axe_path):
    async def exercise():
        journey = template("broken")
        p = store.save_project(ProjectInput(name="Replay", journey=journey))
        original = await execute(store, p["id"], journey, RunControl(), fixtures, axe_path)
        finding = original["findings"][0]
        prepared = prepare_replay(original, finding["id"])
        assert not prepared.exploration.enabled
        assert "Test Applicant" not in prepared.model_dump_json()
        values = {s.value_from: "Synthetic replay" for s in prepared.steps if s.value_from}
        provenance = {"source_id": original["id"], "finding_id": finding["id"]}
        replayed = await execute(
            store,
            p["id"],
            prepared,
            RunControl(),
            fixtures,
            axe_path,
            inputs=RunInputs(prepared, {"values": values}),
            replay=provenance.copy(),
        )
        assert replayed["replay"]["verdict"] == "observed-again"
        assert store.run(original["id"]) == original
        assert "Synthetic replay" not in json.dumps(store.run(replayed["id"]))
        # A correction changes the target's implementation, not the recorded finding.
        prepared.target = "fixture://accessible"
        corrected = await execute(
            store,
            p["id"],
            prepared,
            RunControl(),
            fixtures,
            axe_path,
            inputs=RunInputs(prepared, {"values": values}),
            replay=provenance.copy(),
        )
        assert corrected["replay"]["verdict"] == "not-reproduced-in-this-run"
        assert store.run(original["id"]) == original
        cancelled = RunControl()
        cancelled.cancel.set()
        result = await execute(
            store,
            p["id"],
            prepared,
            cancelled,
            fixtures,
            axe_path,
            replay=provenance.copy(),
            inputs=RunInputs(prepared, {"values": values}),
        )
        assert result["replay"]["verdict"] == "inconclusive-step-not-passed"

    asyncio.run(exercise())


def test_replay_and_profile_ipc_preserve_authorization_boundaries(tmp_path):
    from pathlib import Path
    from uuid import uuid4

    from accessmaze.models import ProjectInput, Request
    from accessmaze.storage import now
    from accessmaze.templates import template
    from accessmaze.worker import Worker

    worker = Worker(tmp_path, Path.cwd())

    def call(method, **params):
        return worker.dispatch(Request(version=1, id="test", method=method, params=params))

    try:
        p = worker.store.save_project(ProjectInput(name="Replay", journey=template("broken")))
        other = worker.store.save_project(ProjectInput(name="Other", journey=template()))
        original_id = str(uuid4())
        from accessmaze.evidence import public_journey

        worker.store.save_run(
            {
                "id": original_id,
                "project_id": p["id"],
                "status": "failed",
                "started_at": now(),
                "journey": public_journey(template("broken")),
                "findings": [{"id": "finding", "step_id": "date"}],
            }
        )
        prepared = call("run.replay.prepare", id=original_id, finding_id="finding")
        assert "Test Applicant" not in json.dumps(prepared)
        params = {
            "project_id": p["id"],
            "replay_source_id": original_id,
            "replay_finding_id": "finding",
        }
        with pytest.raises(ValueError, match="authorized"):
            call("run.start", **params)
        with pytest.raises(ValueError, match="original project"):
            call(
                "run.start",
                **{**params, "project_id": other["id"]},
                authorized=True,
                allow_effects=True,
            )
        bindings = {
            s["value_from"]: "Synthetic"
            for s in prepared["journey"]["steps"]
            if s.get("value_from")
        }
        with pytest.raises(ValueError, match="state-changing"):
            call("run.start", **params, authorized=True, inputs={"values": bindings})
        assert worker.thread is None
        saved = call(
            "profile.save", profile={"name": "Reusable", "profile": {"keyboard_only": False}}
        )
        assert call("profile.list") == [saved]
        call("profile.delete", id=saved["id"])
        assert call("profile.list") == []
    finally:
        worker.close()
