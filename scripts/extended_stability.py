"""Repeat real browser regressions for a measured interval; never implies overnight coverage."""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

from accessmaze.models import Request
from accessmaze.worker import Worker

ROOT = Path(__file__).resolve().parents[1]
TESTS = [
    "test_browser.py",
    "test_lifecycle.py",
    "test_recorder.py",
    "test_connectivity_interruption.py",
    "test_maintenance.py",
    "test_worker.py",
    "test_storage_reports.py",
    "test_compatibility_app.py",
]


def measure(process):
    rss = handles = 0
    children = process.children(recursive=True)
    for child in [process, *children]:
        try:
            rss += child.memory_info().rss
            handles += child.num_handles() if os.name == "nt" else child.num_fds()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return {
        "rss_mib": round(rss / 1024**2, 2),
        "handles": handles,
        "children": len(children),
    }


def persistent_cycle(worker, index, samples, start, parent):
    def request(method, params=None):
        return worker.dispatch(
            Request(version=1, id="stability", method=method, params=params or {})
        )

    kind = ["accessible", "broken", "recovery", "conditional", "slow"][index % 5]
    health = request("health")
    project = request(
        "project.save",
        {"project": {"name": "Persistent soak", "journey": health["templates"][kind]}},
    )
    run_id = request(
        "run.start",
        {"project_id": project["id"], "authorized": True, "allow_effects": True},
    )["id"]
    deadline = time.monotonic() + 90
    cancelled = False
    while worker.thread.is_alive():
        if kind == "slow" and not cancelled:
            request("run.cancel", {"id": run_id})
            cancelled = True
        if time.monotonic() > deadline:
            raise RuntimeError("Persistent worker exceeded 90-second completion bound")
        samples.append(
            {"elapsed": round(time.monotonic() - start, 2), **measure(parent)}
        )
        time.sleep(0.2)
    worker.thread.join()
    result = request("run.get", {"id": run_id})
    expected = (
        "cancelled"
        if kind == "slow"
        else "failed"
        if kind in {"broken", "recovery"}
        else "completed_with_limitations"
    )
    if result["status"] != expected:
        raise RuntimeError(
            f"Unexpected persistent worker result: {kind} {result['status']}"
        )
    request("report.export", {"id": run_id, "format": "html"})
    with worker.store.connect() as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLite integrity failure")
    request("project.delete", {"id": project["id"]})
    if (worker.store.root / "artifacts" / run_id).exists() or request(
        "run.list", {"project_id": project["id"]}
    ):
        raise RuntimeError("Run/artifact cleanup failed")
    return {
        "fixture": kind,
        "status": result["status"],
        "sqlite_integrity": "ok",
        "report_and_cleanup": "passed",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 60 <= args.seconds <= 86400:
        parser.error("seconds must be 60..86400")
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".accessmaze/browsers")
    )
    parent = psutil.Process()
    start = time.monotonic()
    report = {
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True)
        ),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "scope": "Persistent in-process Worker across cycles plus repeated real Chromium regression processes, including headed recording, cancellation, offline socket failure, SQLite backup/retention and invalid IPC recovery. Each pytest cycle is a new process. Native Job-object crash tests, physical network interruption and overnight qualification require separate evidence. Summed RSS double-counts shared pages. Background laptop load uncontrolled.",
        "requested_seconds": args.seconds,
        "cycles": [],
        "samples": [],
    }
    source_paths = sorted((ROOT / "engine/accessmaze").glob("*.py"))
    source_hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths
    }
    report["engine_sources_sha256"] = source_hashes
    temporary = tempfile.TemporaryDirectory(prefix="AccessMaze sustained worker ")
    worker = Worker(Path(temporary.name), ROOT)
    try:
        while time.monotonic() - start < args.seconds:
            index = len(report["cycles"])
            persistent = persistent_cycle(
                worker, index, report["samples"], start, parent
            )
            with (args.output / f"cycle-{index:03d}.txt").open(
                "w", encoding="utf-8"
            ) as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        *[str(ROOT / "engine/tests" / t) for t in TESTS],
                        "-q",
                    ],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                while process.poll() is None:
                    report["samples"].append(
                        {
                            "elapsed": round(time.monotonic() - start, 2),
                            **measure(parent),
                        }
                    )
                    if time.monotonic() - start > args.seconds + 300:
                        process.kill()
                        process.wait()
                        raise RuntimeError(
                            "Cycle exceeded overall duration plus 300-second shutdown allowance"
                        )
                    time.sleep(1)
            time.sleep(1)
            survivors = parent.children(recursive=True)
            cycle = {
                "index": index,
                "persistent_worker": persistent,
                "exit_code": process.returncode,
                "idle": measure(parent),
                "surviving_children": [p.pid for p in survivors],
            }
            report["cycles"].append(cycle)
            print(json.dumps(cycle), flush=True)
            if process.returncode or survivors:
                raise RuntimeError(
                    "Regression failed or owned descendants survived; inspect cycle log"
                )
        if source_hashes != {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths
        }:
            raise RuntimeError(
                "Engine changed during measurement; cannot qualify this run"
            )
        report["result"] = "passed"
    except Exception as error:
        report["result"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        worker.close()
        temporary.cleanup()
        report["actual_seconds"] = round(time.monotonic() - start, 2)
        (args.output / "measurements.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
