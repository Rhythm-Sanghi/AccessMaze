import json
import subprocess
import sys
from pathlib import Path

import pytest

from accessmaze.models import Request
from accessmaze.worker import Worker


def test_effect_authorization_precedes_browser_launch(tmp_path):
    worker = Worker(tmp_path, Path.cwd())
    try:
        health = worker.dispatch(Request(version=1, id="1", method="health"))
        p = worker.dispatch(
            Request(
                version=1,
                id="2",
                method="project.save",
                params={
                    "project": {"name": "Synthetic", "journey": health["templates"]["accessible"]}
                },
            )
        )
        with pytest.raises(ValueError, match="authorized"):
            worker.dispatch(
                Request(version=1, id="3", method="run.start", params={"project_id": p["id"]})
            )
        with pytest.raises(ValueError, match="state-changing"):
            worker.dispatch(
                Request(
                    version=1,
                    id="4",
                    method="run.start",
                    params={"project_id": p["id"], "authorized": True},
                )
            )
        assert worker.thread is None
    finally:
        worker.close()


def test_stdio_invalid_message_does_not_kill_worker(tmp_path):
    messages = [
        '{"version":2,"id":"bad","method":"health"}',
        '{"version":1,"id":"good","method":"health"}',
    ]
    process = subprocess.run(
        [sys.executable, "-m", "accessmaze.worker", "--storage", str(tmp_path)],
        input="\n".join(messages) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert process.returncode == 0, process.stderr
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert responses[0]["error"]
    assert responses[1]["id"] == "good"
    assert responses[1]["result"]["version"] == 1
