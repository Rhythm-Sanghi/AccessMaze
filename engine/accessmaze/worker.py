"""Versioned newline-delimited JSON on private stdin/stdout; no analysis HTTP API."""

import argparse
import asyncio
import base64
import json
import os
import sys
import threading
import traceback
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import ValidationError

from accessmaze.fixtures import FixtureServer
from accessmaze.inputs import RunInputs
from accessmaze.maintenance import backup, prune
from accessmaze.models import Journey, ProjectInput, Request
from accessmaze.reports import export_report
from accessmaze.retests import compare_runs
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store
from accessmaze.templates import template


class Worker:
    def __init__(self, root: Path, resources: Path):
        self.store = Store(root)
        self.store.recover()
        self.fixtures = FixtureServer()
        self.axe = resources / "node_modules" / "axe-core" / "axe.min.js"
        if not self.axe.exists():
            self.axe = resources / "axe.min.js"
        self.active = None
        self.control = None
        self.thread = None
        self.input_key = os.urandom(32)

    def dispatch(self, request):
        params = request.params
        method = request.method
        if method == "health":
            return {
                "version": 1,
                "engine": "0.1.0",
                "templates": {
                    kind: template(kind).model_dump()
                    for kind in [
                        "accessible",
                        "broken",
                        "errors",
                        "recovery",
                        "branch",
                        "slow",
                        "modal",
                        "conditional",
                    ]
                },
            }
        if method == "project.list":
            return self.store.projects()
        if method in {"storage.backup", "storage.prune"}:
            if self.active:
                raise ValueError("Stop the active run before storage maintenance")
            if method == "storage.backup":
                if params.get("acknowledge_plaintext") is not True:
                    raise ValueError("Acknowledge that backups include plain-text journey inputs")
                return backup(self.store)
            return prune(self.store, params["days"])
        if method == "project.save":
            project_id = params.get("id")
            if project_id:
                UUID(project_id)
            return self.store.save_project(
                ProjectInput.model_validate(params["project"]), project_id
            )
        if method in {"project.delete", "project.archive"}:
            project_id = params["id"]
            UUID(project_id)
            if self.active and self.store.run(self.active)["project_id"] == project_id:
                raise ValueError("Stop the active run before changing this project")
            if method == "project.delete":
                self.store.delete_project(project_id)
            else:
                self.store.archive(project_id, params.get("archived", True))
            return {"ok": True}
        if method == "run.list":
            return self.store.runs(params["project_id"])
        if method == "run.get":
            return self.store.run(params["id"])
        if method == "run.compare":
            comparison = compare_runs(
                self.store.run(params["previous_id"]), self.store.run(params["current_id"])
            )
            self.store.save_retest(comparison)
            return comparison
        if method == "run.start":
            if self.thread and self.thread.is_alive():
                raise ValueError("One analysis may run at a time")
            if params.get("authorized") is not True:
                raise ValueError("Confirm that you are authorized to test this target")
            project = self.store.project(params["project_id"])
            journey = Journey.model_validate(project["journey"])
            inputs = RunInputs(journey, params.get("inputs"), self.input_key)
            if (
                any(step.effect for step in journey.steps) or journey.exploration.enabled
            ) and params.get("allow_effects") is not True:
                raise ValueError(
                    "Explicit authorization is required for state-changing interactions"
                )
            self.active = run_id = str(uuid4())
            self.control = RunControl()
            ready = threading.Event()

            def run():
                async def start():
                    # Allow start response only after the first persisted run record exists.
                    task = asyncio.create_task(
                        execute(
                            self.store,
                            project["id"],
                            journey,
                            self.control,
                            self.fixtures,
                            self.axe,
                            run_id,
                            inputs,
                        )
                    )
                    await asyncio.sleep(0)
                    ready.set()
                    return await task

                try:
                    asyncio.run(start())
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    try:
                        result = self.store.run(run_id)
                        result.update(
                            status="failed", error="Unexpected worker error; see diagnostic log"
                        )
                        self.store.save_run(result)
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                finally:
                    ready.set()
                    self.active = None

            self.thread = threading.Thread(target=run, daemon=True)
            self.thread.start()
            if not ready.wait(timeout=5):
                self.control.cancel.set()
                raise ValueError("Run initialization timed out")
            return {"id": run_id}
        if method in {"run.cancel", "run.pause", "run.resume"}:
            if params["id"] != self.active or not self.control:
                raise ValueError("This run is no longer active")
            if method == "run.cancel":
                self.control.cancel.set()
            elif method == "run.pause":
                self.control.pause.set()
            else:
                self.control.pause.clear()
            return {"ok": True}
        if method == "report.export":
            run = self.store.run(params["id"])
            screenshots = {}
            if params["format"] == "html":
                for finding in run["findings"][:10]:
                    name = finding.get("screenshot")
                    if name and Path(name).name == name and name.endswith(".png"):
                        path = self.store.artifact_dir(run["id"]) / name
                        if path.is_file():
                            screenshots[name] = "data:image/png;base64," + base64.b64encode(
                                path.read_bytes()
                            ).decode("ascii")
            content, mime = export_report(run, params["format"], screenshots)
            return {"content": content, "mime": mime}
        if method == "evidence.read":
            run = self.store.run(params["id"])
            name = params["name"]
            if name not in {f.get("screenshot") for f in run["findings"]}:
                raise ValueError("Artifact is not referenced by this run")
            if Path(name).name != name or not name.endswith(".png"):
                raise ValueError("Invalid artifact name")
            data = (self.store.artifact_dir(run["id"]) / name).read_bytes()
            return {"url": "data:image/png;base64," + base64.b64encode(data).decode("ascii")}
        raise ValueError("Unknown method")

    def close(self):
        if self.control:
            self.control.cancel.set()
        if self.thread:
            self.thread.join(timeout=10)
        self.fixtures.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", type=Path, required=True)
    parser.add_argument("--resources", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if (args.resources / "browsers").is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(args.resources / "browsers")
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    worker = Worker(args.storage, args.resources)
    try:
        while line := sys.stdin.buffer.readline(8 * 1024 * 1024 + 1):
            request_id = None
            try:
                if len(line) > 8 * 1024 * 1024:
                    raise ValueError("Request exceeds 8 MiB")
                raw = json.loads(line)
                request_id = raw.get("id") if isinstance(raw, dict) else None
                request = Request.model_validate(raw)
                data = worker.dispatch(request)
                response = {"version": 1, "id": request.id, "result": data}
            except (ValidationError, ValueError, KeyError, TypeError, OSError) as exc:
                message = "Invalid request schema" if isinstance(exc, ValidationError) else str(exc)
                response = {"version": 1, "id": request_id, "error": {"message": message}}
            except Exception:
                traceback.print_exc(file=sys.stderr)
                response = {
                    "version": 1,
                    "id": request_id,
                    "error": {"message": "Internal worker error; see diagnostic log"},
                }
            print(json.dumps(response, ensure_ascii=False), flush=True)
    finally:
        worker.close()


if __name__ == "__main__":
    main()
