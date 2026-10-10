"""Verify the frozen worker with a stripped PATH and portable browser resources."""

import json
import argparse
import os
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", default="AccessMaze-portable")
    args = parser.parse_args()
    package = ROOT / "dist" / args.package
    environment = {
        key: os.environ[key]
        for key in [
            "SystemRoot",
            "WINDIR",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "LOCALAPPDATA",
            "APPDATA",
        ]
        if key in os.environ
    }
    environment["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
    with tempfile.TemporaryDirectory(prefix="AccessMaze portable smoke ") as directory:
        started = time.perf_counter()
        process = subprocess.Popen(
            [
                str(package / "accessmaze-worker.exe"),
                "--resources",
                str(package / "resources"),
                "--storage",
                directory,
            ],
            cwd=directory,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        sequence = 0

        def request(method, params=None):
            nonlocal sequence
            sequence += 1
            process.stdin.write(
                json.dumps(
                    {
                        "version": 1,
                        "id": str(sequence),
                        "method": method,
                        "params": params or {},
                    }
                )
                + "\n"
            )
            process.stdin.flush()
            line = process.stdout.readline()
            if not line:
                raise RuntimeError(process.stderr.read())
            result = json.loads(line)
            if "error" in result:
                raise RuntimeError(result["error"])
            return result["result"]

        runs = []
        try:
            health = request("health")
            startup = round(time.perf_counter() - started, 3)
            for kind in ["accessible", "broken", "conditional"]:
                project = request(
                    "project.save",
                    {"project": {"name": kind, "journey": health["templates"][kind]}},
                )
                run_id = request(
                    "run.start",
                    {
                        "project_id": project["id"],
                        "authorized": True,
                        "allow_effects": True,
                    },
                )["id"]
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    result = request("run.get", {"id": run_id})
                    if result["status"] not in {"preparing", "running", "paused"}:
                        break
                    time.sleep(0.1)
                expected = (
                    "failed" if kind == "broken" else "completed_with_limitations"
                )
                assert result["status"] == expected, result
                report = request("report.export", {"id": run_id, "format": "json"})
                assert json.loads(report["content"])["findings"] == result["findings"]
                html = request("report.export", {"id": run_id, "format": "html"})[
                    "content"
                ]
                assert "Observed states, transitions and incomplete exploration" in html
                if kind == "broken":
                    assert "data:image/png;base64," in html
                runs.append(
                    {
                        "fixture": kind,
                        "status": result["status"],
                        "findings": len(result["findings"]),
                        "seconds": result["duration_seconds"],
                    }
                )
        finally:
            process.stdin.close()
            process.wait(timeout=15)
            assert process.returncode == 0, process.stderr.read()
        evidence = {
            "frozen_worker": "passed",
            "system_path_only": True,
            "working_directory": "temporary path with spaces",
            "browser_resources": "portable bundled revision",
            "worker_startup_seconds": startup,
            "runs": runs,
            "limitation": "Same Windows machine; not a clean-machine installation test.",
        }
        (ROOT / "docs/releases/portable-smoke.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
