"""Synthetic storage read load; these records are not executed accessibility tests."""

import argparse
import ast
import json
import platform
import re
import statistics
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import psutil

from accessmaze.evidence import public_journey
from accessmaze.models import ProjectInput
from accessmaze.permissions import private_directory
from accessmaze.storage import Store
from accessmaze.templates import template

ROOT = Path(__file__).resolve().parents[1]


def historical_projects(ref):
    if not re.fullmatch(r"[0-9a-f]{7,40}", ref):
        raise ValueError("Baseline must be an explicit commit hash")
    source = subprocess.check_output(
        ["git", "show", f"{ref}:engine/accessmaze/storage.py"], cwd=ROOT, text=True
    )
    store = next(
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.ClassDef) and n.name == "Store"
    )
    function = next(
        n for n in store.body if isinstance(n, ast.FunctionDef) and n.name == "projects"
    )
    namespace = {"json": json}
    exec(
        compile(
            ast.Module(body=[function], type_ignores=[]),
            "historical storage.projects",
            "exec",
        ),
        namespace,
    )
    return namespace["projects"]


def measure(function, repetitions=5):
    samples = []
    value = None
    for _ in range(repetitions):
        start = time.perf_counter()
        value = function()
        samples.append((time.perf_counter() - start) * 1000)
    return {
        "median_ms": round(statistics.median(samples), 3),
        "samples_ms": [round(s, 3) for s in samples],
    }, value


def benchmark(
    output,
    *,
    baseline="109d90e",
    project_count=24,
    runs_per_project=12,
    large_history=500,
):
    if (
        not 1 <= project_count <= 100
        or not 1 <= runs_per_project <= 100
        or not 1 <= large_history <= 2000
    ):
        raise ValueError("Synthetic workload exceeds documented bounds")
    output.mkdir(parents=True, exist_ok=False)
    private_directory(output)
    store = Store(output / "workspace")
    definition = template()
    projects = [
        store.save_project(
            ProjectInput(name=f"SYNTHETIC read load {i}", journey=definition)
        )
        for i in range(project_count)
    ]
    observation = {
        "title": "Synthetic storage load; never executed",
        "url": "fixture://accessible",
        "headings": [],
        "online": True,
        "reduced_motion": False,
        "controls": [
            {
                "tag": "button",
                "role": "button",
                "name": f"Synthetic control {i}",
                "disabled": False,
                "visible": True,
                "invalid": None,
                "populated": False,
                "focused": False,
            }
            for i in range(20)
        ],
    }
    nodes = [
        {
            "id": f"synthetic-state-{i}",
            "first_step": "synthetic-load",
            "observation": observation,
        }
        for i in range(20)
    ]
    started = time.perf_counter()
    stamp = datetime.now(UTC)
    count = 0
    for index, project in enumerate(projects):
        for _ in range(large_history if index == 0 else runs_per_project):
            store.save_run(
                {
                    "id": str(uuid4()),
                    "project_id": project["id"],
                    "status": "synthetic-load",
                    "started_at": (stamp + timedelta(milliseconds=count)).isoformat(),
                    "synthetic_benchmark": True,
                    "journey": public_journey(definition),
                    "steps": [],
                    "findings": [],
                    "nodes": nodes,
                    "edges": [],
                    "limitations": ["Storage load only; no browser executed"],
                    "environment": {},
                }
            )
            count += 1
    old = historical_projects(baseline)
    old_time, old_value = measure(lambda: old(store))
    new_time, new_value = measure(store.projects)
    if old_value != new_value:
        raise AssertionError("Project summary behavior changed")
    full_time, full = measure(lambda: store.runs(projects[0]["id"]), 3)
    full_bytes = len(json.dumps(full).encode())
    rss_full = psutil.Process().memory_info().rss
    del full
    paged_time, paged_bytes = None, None
    if hasattr(store, "history"):
        paged_time, page = measure(lambda: store.history(projects[0]["id"], 50, 0), 3)
        paged_bytes = len(json.dumps(page).encode())
    connections = {}
    connect = store.connect
    for label, function in [
        ("baseline", lambda: old(store)),
        ("current", store.projects),
    ]:
        connections[label] = 0

        def counted():
            connections[label] += 1
            return connect()

        store.connect = counted
        try:
            function()
        finally:
            store.connect = connect
    result = {
        "schema_version": 1,
        "synthetic_storage_load": True,
        "baseline_commit": baseline,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
        "host": platform.platform(),
        "cpu": platform.processor(),
        "ram_bytes": psutil.virtual_memory().total,
        "projects": project_count,
        "runs": count,
        "largest_history": large_history,
        "baseline_projects": old_time,
        "current_projects": new_time,
        "summary_connections": connections,
        "full_history": full_time,
        "full_history_bytes": full_bytes,
        "history_page": paged_time,
        "history_page_bytes": paged_bytes,
        "rss_after_full_history_bytes": rss_full,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "limitation": "Warm repeated reads of synthetic SQLite data; not native rendering, browser results, peak process memory or a release performance budget.",
    }
    (output / "results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", default="109d90e")
    args = parser.parse_args()
    result = benchmark(args.output, baseline=args.baseline)
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "projects",
                    "runs",
                    "baseline_projects",
                    "current_projects",
                    "summary_connections",
                    "full_history_bytes",
                    "history_page_bytes",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
