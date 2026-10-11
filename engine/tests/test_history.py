from uuid import uuid4

import pytest

from accessmaze.models import ProjectInput, Request
from accessmaze.storage import now
from accessmaze.templates import template


def test_aggregate_summaries_and_bounded_history_preserve_counts(store, project):
    p = project()
    empty = project("broken")
    ids = []
    for index, status in enumerate(["completed_with_limitations", "cancelled", "running"]):
        run_id = str(uuid4())
        ids.append(run_id)
        store.save_run(
            {
                "id": run_id,
                "project_id": p["id"],
                "status": status,
                "started_at": f"2026-10-10T00:00:0{index}Z",
                "journey": p["journey"],
                "findings": [
                    {"verification": "confirmed-automated"},
                    {"verification": "inconclusive"},
                ]
                if index == 0
                else [],
                "nodes": [{"synthetic": "large graph must not be included in the summary"}],
                "steps": [],
            }
        )
    projects = {item["id"]: item for item in store.projects()}
    assert projects[p["id"]]["summary"] == {
        "last_analysis": "2026-10-10T00:00:02Z",
        "confirmed_findings": 1,
        "incomplete_runs": 2,
    }
    assert projects[empty["id"]]["summary"] == {
        "last_analysis": None,
        "confirmed_findings": 0,
        "incomplete_runs": 0,
    }
    first = store.history(p["id"], 2, 0)
    assert [r["id"] for r in first["items"]] == list(reversed(ids))[:2]
    assert first["total"] == 3 and first["next_offset"] == 2
    assert all("nodes" not in r and "findings" not in r for r in first["items"])
    last = store.history(p["id"], 2, 2)
    assert last["items"][0]["finding_count"] == 2
    assert last["next_offset"] is None
    for limit, offset in [(0, 0), (101, 0), (True, 0), (1, -1), (1, "0")]:
        with pytest.raises(ValueError, match="History"):
            store.history(p["id"], limit, offset)


def test_history_ipc_rejects_unbounded_queries(tmp_path):
    from pathlib import Path

    from accessmaze.worker import Worker

    worker = Worker(tmp_path, Path.cwd())
    try:
        project = worker.store.save_project(ProjectInput(name="History bounds", journey=template()))
        worker.store.save_run(
            {
                "id": str(uuid4()),
                "project_id": project["id"],
                "status": "cancelled",
                "started_at": now(),
                "findings": [],
            }
        )

        def call(**params):
            return worker.dispatch(
                Request(
                    version=1,
                    id="history",
                    method="run.history",
                    params={"project_id": project["id"], **params},
                )
            )

        assert call()["total"] == 1
        for params in [{"limit": 1000}, {"limit": True}, {"offset": -1}, {"extra": "ignored"}]:
            with pytest.raises(ValueError):
                call(**params)
    finally:
        worker.close()
