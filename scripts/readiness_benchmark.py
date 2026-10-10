"""Bounded Windows readiness measurements; synthetic scaling is labelled separately."""

import argparse
import asyncio
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import networkx as nx
import psutil
from playwright.async_api import async_playwright

from accessmaze.fixtures import FixtureServer
from accessmaze.models import ProjectInput
from accessmaze.reports import export_report
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store
from accessmaze.templates import template

ROOT = Path(__file__).resolve().parents[1]


def startup(folder):
    samples = []
    for index in range(3):
        started = time.perf_counter()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "accessmaze.worker",
                "--resources",
                str(ROOT),
                "--storage",
                str(folder / str(index)),
            ],
            input=json.dumps(
                {"version": 1, "id": "1", "method": "health", "params": {}}
            )
            + "\n",
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        response = json.loads(result.stdout)
        assert response["result"]["engine"] == "0.1.0"
        samples.append(round(time.perf_counter() - started, 4))
    return samples


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=60)
    parser.add_argument("--soak-seconds", type=int, default=180)
    args = parser.parse_args()
    if not 5 <= args.runs <= 500 or not 10 <= args.soak_seconds <= 3600:
        parser.error("runs: 5..500; soak-seconds: 10..3600")
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".accessmaze/browsers")
    )
    samples = []
    stop = threading.Event()
    parent = psutil.Process()

    def sample():
        while not stop.wait(0.2):
            rss = handles = 0
            for process in [parent, *parent.children(recursive=True)]:
                try:
                    rss += process.memory_info().rss
                    handles += (
                        process.num_handles() if os.name == "nt" else process.num_fds()
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            samples.append(
                {
                    "elapsed": round(time.perf_counter() - started, 2),
                    "rss_mib": round(rss / 1024**2, 2),
                    "handles": handles,
                }
            )

    started = time.perf_counter()
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    server = FixtureServer()
    runs = []
    browser_timings = []
    graph = []
    try:
        with tempfile.TemporaryDirectory(prefix="AccessMaze readiness ") as folder:
            worker_startup = startup(Path(folder) / "startup")
            store = Store(Path(folder) / "runs")
            for index in range(args.runs):
                kind = ["accessible", "broken", "errors", "recovery", "branch"][
                    index % 5
                ]
                journey = template(kind)
                project = store.save_project(ProjectInput(name=kind, journey=journey))
                run = await execute(
                    store,
                    project["id"],
                    journey,
                    RunControl(),
                    server,
                    ROOT / "node_modules/axe-core/axe.min.js",
                )
                expected_status = (
                    "failed"
                    if kind in {"broken", "errors", "recovery"}
                    else "completed_with_limitations"
                )
                if run["status"] != expected_status or run["coverage_compromised"]:
                    raise RuntimeError(
                        f"Unexpected benchmark outcome for {kind}: {run['status']}"
                    )
                exports = {}
                for format in ["json", "html", "csv"]:
                    begin = time.perf_counter()
                    content, _ = export_report(run, format)
                    exports[format] = {
                        "ms": round((time.perf_counter() - begin) * 1000, 3),
                        "bytes": len(content.encode()),
                    }
                begin = time.perf_counter()
                store.projects()
                runs.append(
                    {
                        "index": index,
                        "fixture": kind,
                        "status": run["status"],
                        "seconds": run["duration_seconds"],
                        "exports": exports,
                        "history_load_ms": round(
                            (time.perf_counter() - begin) * 1000, 3
                        ),
                    }
                )
            async with async_playwright() as pw:
                for _ in range(3):
                    begin = time.perf_counter()
                    browser = await pw.chromium.launch()
                    launched = time.perf_counter()
                    page = await browser.new_page()
                    await page.goto(server.url("fixture://accessible"))
                    browser_timings.append(
                        {
                            "launch_ms": round((launched - begin) * 1000, 2),
                            "context_navigation_ms": round(
                                (time.perf_counter() - launched) * 1000, 2
                            ),
                        }
                    )
                    await browser.close()
                browser = await pw.chromium.launch()
                page = await browser.new_page()
                soak_start = time.perf_counter()
                reloads = 0
                while time.perf_counter() - soak_start < args.soak_seconds:
                    await page.goto(server.url("fixture://accessible"))
                    await page.get_by_role("textbox").first.fill("Synthetic soak")
                    reloads += 1
                    await asyncio.sleep(2)
                soak_actual = time.perf_counter() - soak_start
                await browser.close()
            for size in [1000, 10000, 50000]:
                begin = time.perf_counter()
                network = nx.path_graph(size, create_using=nx.DiGraph)
                assert nx.has_path(network, 0, size - 1)
                encoded = json.dumps(nx.node_link_data(network, edges="edges"))
                graph.append(
                    {
                        "synthetic_nodes": size,
                        "edges": size - 1,
                        "build_path_serialize_ms": round(
                            (time.perf_counter() - begin) * 1000, 3
                        ),
                        "serialized_bytes": len(encoded),
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
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scope": "Development worker startup including EOF shutdown; sequential real Chromium fixtures; persistent browser soak; synthetic backend graphs. No desktop startup, UI graph rendering, independent hardware or 24-hour stability claim. RSS sums count shared pages per process; background laptop activity uncontrolled.",
        "worker_startup_shutdown_seconds": worker_startup,
        "browser_timings": browser_timings,
        "soak_seconds": round(soak_actual, 2),
        "soak_reloads": reloads,
        "wall_seconds": round(time.perf_counter() - started, 2),
        "peak_rss_mib": max(s["rss_mib"] for s in samples),
        "median_rss_mib": statistics.median(s["rss_mib"] for s in samples),
        "runs": runs,
        "synthetic_graph": graph,
        "resource_samples": samples,
    }
    output = ROOT / "docs/testing/readiness-benchmark.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in {"runs", "resource_samples"}},
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
