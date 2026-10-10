"""Repeatable local fixture suite; measurements come from this process and its children."""

import asyncio
import json
import platform
import statistics
import tempfile
import threading
import time
from pathlib import Path

import psutil

from accessmaze.fixtures import FixtureServer
from accessmaze.models import ProjectInput
from accessmaze.reports import export_report
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store
from accessmaze.templates import template

ROOT = Path(__file__).resolve().parents[1]


async def main():
    samples = []
    timing = []
    stop = threading.Event()
    process = psutil.Process()

    def sample():
        while not stop.wait(0.1):
            processes = [process, *process.children(recursive=True)]
            rss = 0
            for child in processes:
                try:
                    rss += child.memory_info().rss
                except psutil.NoSuchProcess:
                    pass
            samples.append(rss)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    server = FixtureServer()
    try:
        with tempfile.TemporaryDirectory(prefix="AccessMaze benchmark ") as directory:
            store = Store(Path(directory))
            for iteration in range(3):
                for kind in ["accessible", "broken", "errors", "recovery", "branch"]:
                    journey = template(kind)
                    project = store.save_project(
                        ProjectInput(name=kind, journey=journey)
                    )
                    run = await execute(
                        store,
                        project["id"],
                        journey,
                        RunControl(),
                        server,
                        ROOT / "node_modules/axe-core/axe.min.js",
                    )
                    export_start = time.perf_counter()
                    export_report(run, "html")
                    export_ms = (time.perf_counter() - export_start) * 1000
                    load_start = time.perf_counter()
                    store.projects()
                    load_ms = (time.perf_counter() - load_start) * 1000
                    timing.append(
                        {
                            "iteration": iteration + 1,
                            "fixture": kind,
                            "seconds": run["duration_seconds"],
                            "status": run["status"],
                            "findings": len(run["findings"]),
                            "export_ms": round(export_ms, 3),
                            "project_load_ms": round(load_ms, 3),
                        }
                    )
    finally:
        server.close()
        stop.set()
        thread.join()
    result = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor(),
        "logical_cpus": psutil.cpu_count(),
        "machine_ram_gib": round(psutil.virtual_memory().total / 1024**3, 2),
        "scope": "15 sequential Chromium fixture runs, 0.1s RSS sampling; no UI startup measurement",
        "rss_sum_peak_mib": round(max(samples) / 1024**2, 2),
        "rss_sum_median_mib": round(statistics.median(samples) / 1024**2, 2),
        "measurements": timing,
    }
    path = ROOT / "docs/testing/benchmark.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({k: v for k, v in result.items() if k != "measurements"}, indent=2)
    )


if __name__ == "__main__":
    asyncio.run(main())
