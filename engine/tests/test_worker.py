import json
import subprocess
import sys
from pathlib import Path

import pytest

from accessmaze.models import Request
from accessmaze.worker import Worker


def test_run_initial_record_is_available_before_slow_environment_probe(tmp_path, monkeypatch):
    import threading

    from accessmaze.models import ProjectInput
    from accessmaze.templates import template

    entered, release = threading.Event(), threading.Event()

    def slow_environment():
        entered.set()
        assert release.wait(10)
        return "Delayed synthetic environment"

    worker = Worker(tmp_path, Path.cwd())
    project = worker.store.save_project(ProjectInput(name="Slow startup", journey=template()))
    monkeypatch.setattr("accessmaze.runner.platform.platform", slow_environment)
    try:
        response = worker.dispatch(
            Request(
                version=1,
                id="start",
                method="run.start",
                params={"project_id": project["id"], "authorized": True, "allow_effects": True},
            )
        )
        assert entered.wait(2)
        saved = worker.store.run(response["id"])
        assert saved["status"] == "preparing"
        assert saved["outcome"]["status"] == "incomplete"
        worker.control.cancel.set()
    finally:
        release.set()
        worker.close()


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


def test_oversized_frame_is_discarded_and_malformed_id_is_not_echoed(tmp_path):
    secret = "private-malformed-id-412"
    spliced = '{"version":1,"id":"spliced","method":"health"}'
    malformed = json.dumps({"version": 1, "id": {"secret": secret}, "method": "health"})
    process = subprocess.run(
        [sys.executable, "-m", "accessmaze.worker", "--storage", str(tmp_path)],
        input="x" * (8 * 1024 * 1024 + 1)
        + spliced
        + "\n"
        + malformed
        + "\n"
        + '{"version":1,"id":"healthy","method":"health"}\n',
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert process.returncode == 0
    assert secret not in process.stdout + process.stderr
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(responses) == 3
    assert responses[0]["error"]["message"] == "Request exceeds 8 MiB"
    assert responses[1]["id"] is None and responses[1]["error"]
    assert responses[2]["id"] == "healthy" and responses[2]["result"]["version"] == 1


def test_stdio_schema_error_is_actionable_without_exposing_input(tmp_path):
    private = "private-password-should-not-appear"
    process = subprocess.run(
        [sys.executable, "-m", "accessmaze.worker", "--storage", str(tmp_path)],
        input=json.dumps(
            {
                "version": 1,
                "id": "invalid",
                "method": "project.save",
                "params": {"project": {"name": "Synthetic", "journey": {"target": private}}},
            }
        )
        + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert process.returncode == 0
    message = json.loads(process.stdout)["error"]["message"]
    assert "target" in message and "Review required fields" in message
    assert private not in process.stdout + process.stderr


@pytest.mark.parametrize("exception", ["RuntimeError", "OSError", "KeyError", "TypeError"])
def test_unexpected_exception_does_not_log_sensitive_browser_data(tmp_path, exception):
    private = "private-browser-response-and-password-719"
    code = """
from accessmaze import worker
original = worker.Worker.dispatch
def dispatch(self, request):
    if request.id == 'fault':
        raise RuntimeError('private-browser-response-and-password-719')
    return original(self, request)
worker.Worker.dispatch = dispatch
worker.main()
"""
    code = code.replace("raise RuntimeError(", f"raise {exception}(")
    process = subprocess.run(
        [sys.executable, "-c", code, "--storage", str(tmp_path)],
        input='{"version":1,"id":"fault","method":"health"}\n'
        '{"version":1,"id":"healthy","method":"health"}\n',
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert process.returncode == 0
    assert private not in process.stdout + process.stderr
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert "reference" in responses[0]["error"]["message"]
    assert responses[1]["result"]["version"] == 1
