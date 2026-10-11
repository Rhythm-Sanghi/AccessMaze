"""Measure an explicitly selected packaged desktop; exercise only owned fixtures."""

import argparse
import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import psutil
from playwright.async_api import async_playwright

ACTIVE = {"preparing", "running", "paused", "awaiting_approval"}


def measure(host, known):
    processes = [host, *host.children(recursive=True)]
    known.update({(p.pid, p.create_time()): p for p in processes[1:]})
    rss = handles = 0
    for process in processes:
        try:
            rss += process.memory_info().rss
            handles += process.num_handles()
        except psutil.NoSuchProcess:
            pass
    return {
        "rss_mib": round(rss / 1024**2, 2),
        "handles": handles,
        "children": len(processes) - 1,
    }


async def verify(args):
    host = psutil.Process(args.pid)
    package = args.exe.resolve().parent
    if Path(host.exe()).resolve() != args.exe.resolve():
        raise ValueError("Selected PID does not match the explicit executable")
    manifest = json.loads(
        (package / "package-manifest.json").read_text(encoding="utf-8")
    )
    args.output.mkdir(parents=True, exist_ok=False)
    known = {}
    project = None
    run_id = None
    started = time.monotonic()
    result = {
        "source_commit": manifest["source_commit"],
        "source_dirty": manifest["source_dirty"],
        "requested_seconds": args.seconds,
        "scope": "Long-lived packaged desktop, WebView2, private IPC and frozen worker on development laptop. Owned fixtures, UI history/graph inspection, cancellation and cleanup. CDP instrumentation enabled. Summed RSS double-counts shared pages; background activity uncontrolled. No overnight, independent-machine or leak-clearance claim.",
        "cycles": [],
        "samples": [],
        "result": "failed",
    }
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.endpoint)
        page = next(
            p for c in browser.contexts for p in c.pages if "tauri.localhost" in p.url
        )
        page.set_default_timeout(30000)

        async def call(method, **params):
            return await page.evaluate(
                "x=>window.__TAURI_INTERNALS__.invoke('worker_request',x)",
                {"method": method, "params": params},
            )

        async def finish():
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                run = await call("run.get", id=run_id)
                result["samples"].append(
                    {
                        "elapsed": round(time.monotonic() - started, 2),
                        **measure(host, known),
                    }
                )
                if run["status"] not in ACTIVE:
                    return run
                await asyncio.sleep(0.2)
            raise TimeoutError("Owned fixture exceeded completion bound")

        try:
            health = await call("health")
            name = "Native sustained " + uuid4().hex[:8]
            while time.monotonic() - started < args.seconds:
                index = len(result["cycles"])
                kind = ["accessible", "broken", "recovery", "conditional", "slow"][
                    index % 5
                ]
                journey = health["templates"][kind]
                journey["name"] = name
                params = {"project": {"name": name, "journey": journey}}
                if project:
                    params["id"] = project["id"]
                project = await call("project.save", **params)
                run_id = (
                    await call(
                        "run.start",
                        project_id=project["id"],
                        authorized=True,
                        allow_effects=True,
                    )
                )["id"]
                if kind == "slow":
                    await asyncio.sleep(0.5)
                    await call("run.cancel", id=run_id)
                run = await finish()
                expected = (
                    "cancelled"
                    if kind == "slow"
                    else "failed"
                    if kind in {"broken", "recovery"}
                    else "completed_with_limitations"
                )
                if run["status"] != expected:
                    raise AssertionError((kind, run["status"], expected))
                history = await call("run.history", project_id=project["id"], limit=5)
                assert history["total"] == index + 1
                await page.reload()
                await page.get_by_text("Worker connected", exact=True).wait_for()
                await page.get_by_role("button", name=name, exact=True).click()
                await page.get_by_role("button", name="03 Analysis", exact=True).click()
                await page.get_by_role(
                    "button", name="Inspect run", exact=True
                ).first.click()
                await page.get_by_role(
                    "region", name="Human investigation", exact=True
                ).wait_for()
                assert (
                    await page.get_by_role(
                        "region", name="Human investigation", exact=True
                    ).count()
                    == 1
                )
                export_started = time.monotonic()
                report = await call("report.export", id=run_id, format="html")
                assert report["content"]
                export_seconds = round(time.monotonic() - export_started, 3)
                await asyncio.sleep(0.5)
                children = host.children(recursive=True)
                surviving_chromium = [
                    p.pid
                    for p in children
                    if p.name().lower()
                    in {"chrome.exe", "chrome-headless-shell.exe", "headless_shell.exe"}
                ]
                cycle = {
                    "index": index,
                    "fixture": kind,
                    "status": run["status"],
                    "history_count": history["total"],
                    "export_seconds": export_seconds,
                    "idle": measure(host, known),
                    "surviving_chromium": surviving_chromium,
                }
                result["cycles"].append(cycle)
                print(json.dumps(cycle), flush=True)
                if surviving_chromium:
                    raise AssertionError("Run retained Chromium descendants")
                (args.output / "progress.json").write_text(
                    json.dumps(result, indent=2), encoding="utf-8"
                )
                await asyncio.sleep(1)
            result["result"] = "passed"
        finally:
            if run_id:
                if (await call("run.get", id=run_id))["status"] in ACTIVE:
                    await call("run.cancel", id=run_id)
                    await finish()
            if project:
                await call("project.delete", id=project["id"])
                assert project["id"] not in {
                    p["id"] for p in await call("project.list")
                }
                result["owned_history_removed"] = True
            measure(host, known)
            subprocess.run(
                [
                    str(
                        Path(os.environ["SystemRoot"])
                        / "System32/WindowsPowerShell/v1.0/powershell.exe"
                    ),
                    "-NoProfile",
                    "-Command",
                    f"(Get-Process -Id {host.pid}).CloseMainWindow()",
                ],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
                timeout=10,
            )
            await asyncio.to_thread(host.wait, timeout=15)
            # Windows can reuse browser PIDs during a long run. wait_procs may wait
            # on the replacement PID before checking identity; is_running checks
            # the original creation time and never treats that replacement as ours.
            for _ in range(100):
                alive = [p for p in known.values() if p.is_running()]
                if not alive:
                    break
                await asyncio.sleep(0.1)
            result["observed_child_identities"] = [
                {"pid": pid, "created": created} for pid, created in known
            ]
            result["reused_pids_excluded"] = sorted(
                {
                    p.pid
                    for p in known.values()
                    if not p.is_running() and psutil.pid_exists(p.pid)
                }
            )
            result["surviving_children_after_close"] = [p.pid for p in alive]
            result["elapsed_seconds"] = round(time.monotonic() - started, 3)
            if alive:
                result["result"] = "failed"
            (args.output / "measurements.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            assert not alive, "Owned desktop left children after close"
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"samples", "cycles", "observed_child_identities"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:9224")
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 60 <= args.seconds <= 86400:
        parser.error("seconds must be 60..86400")
    asyncio.run(verify(args))
