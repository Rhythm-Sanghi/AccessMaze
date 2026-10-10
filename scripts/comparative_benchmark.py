"""Paired owned browser tasks with same-initial-state axe/optional Pa11y probes."""

import argparse
import asyncio
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil
from playwright.async_api import async_playwright

from accessmaze.fixtures import FixtureServer
from accessmaze.inputs import RunInputs
from accessmaze.models import Journey, ProjectInput, Step
from accessmaze.permissions import private_directory
from accessmaze.retests import compare_runs
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine/tests"))
from test_website_policy import website  # noqa: E402


def activation(id, name, role="button"):
    return {
        "id": id,
        "action": "activate",
        "effect": True,
        "target": {"role": role, "name": name},
    }


def assertion(id, name, role="heading", action="assert_visible"):
    return {"id": id, "action": action, "target": {"role": role, "name": name}}


def corpus():
    """Truth labels concern these deliberately authored conditions, not compliance."""
    cases = []
    for broken in (True, False):
        tab = ' tabindex="-1"' if broken else ""
        cases.append(
            {
                "name": "date-picker",
                "broken": broken,
                "rule": "keyboard-unreachable",
                "body": f'<label>Name<input id="name"></label><div role="button"{tab} id="date" '
                "onclick=\"this.dataset.selected='yes'\">Choose date</div>"
                if broken
                else '<label>Name<input id="name"></label><button id="date" onclick="this.dataset.selected=\'yes\'">Choose date</button>',
                "script": "",
                "steps": [activation("date", "Choose date")],
                "finish": True,
            }
        )
        cases.append(
            {
                "name": "intermediate-step",
                "broken": broken,
                "rule": "keyboard-unreachable",
                "body": '<button id="start">Start form</button>',
                "script": f"start.onclick=()=>{{stage.innerHTML='<h2>Details</h2><button{tab} onclick=\"done()\">Continue</button>'}};",
                "steps": [
                    activation("start", "Start form"),
                    assertion("details", "Details"),
                    activation("continue", "Continue"),
                ],
                "finish": False,
            }
        )
        destination = "other" if broken else "name"
        cases.append(
            {
                "name": "validation-focus",
                "broken": broken,
                "rule": "focus-mismatch",
                "body": '<label>Name<input id="name" aria-describedby="error"></label><p id="error" role="alert"></p>'
                '<button id="validate">Validate</button><button id="other">Help</button>',
                "script": f"validate.onclick=()=>{{nameField.setAttribute('aria-invalid','true');error.textContent='Enter a name';document.getElementById('{destination}').focus()}};",
                "steps": [
                    activation("validate", "Validate"),
                    assertion("error-focus", "Name", "textbox", "assert_focus"),
                ],
                "finish": True,
            }
        )
        recovery = "stage.textContent='Recovery unavailable'" if broken else "done()"
        cases.append(
            {
                "name": "error-recovery",
                "broken": broken,
                "rule": "completion-assertion",
                "body": '<button id="errorButton">Trigger error</button><button id="recover">Retry task</button>',
                "script": f"errorButton.onclick=()=>stage.textContent='Retry allowed';recover.onclick=()=>{{{recovery}}};",
                "steps": [
                    activation("error", "Trigger error"),
                    activation("recover", "Retry task"),
                ],
                "finish": False,
            }
        )
        cases.append(
            {
                "name": "offline-draft",
                "broken": broken,
                "rule": "form-state-lost",
                "body": '<label>Name<input id="name"></label>',
                "script": "addEventListener('offline',()=>{nameField.value=''})"
                if broken
                else "",
                "steps": [
                    {
                        "id": "name",
                        "action": "fill",
                        "target": {"role": "textbox", "name": "Name"},
                        "value": "Synthetic draft",
                    },
                    {"id": "offline", "action": "offline"},
                    {"id": "online", "action": "online"},
                    {
                        "id": "retained",
                        "action": "assert_value",
                        "target": {"role": "textbox", "name": "Name"},
                        "value": "Synthetic draft",
                    },
                ],
                "finish": True,
            }
        )
        cases.append(
            {
                "name": "spa-navigation",
                "broken": broken,
                "rule": "keyboard-unreachable",
                "body": '<button id="start">Open details</button>',
                "script": f"start.onclick=()=>{{history.pushState({{}},'', '/details');stage.innerHTML='<h2>Details</h2><button{tab} onclick=\"done()\">Confirm</button>'}};",
                "steps": [
                    activation("details", "Open details"),
                    assertion("route", "Details"),
                    activation("confirm", "Confirm"),
                ],
                "finish": False,
            }
        )
        cases.append(
            {
                "name": "conditional-route",
                "broken": broken,
                "rule": "keyboard-unreachable",
                "body": '<label><input id="regional" type="checkbox">Regional route</label>',
                "script": f"regional.onchange=()=>{{stage.innerHTML=regional.checked?'<button{tab} onclick=\"done()\">Continue regional</button>':'<button onclick=\"done()\">Continue standard</button>'}};regional.onchange();",
                "steps": [
                    activation("regional", "Regional route", "checkbox"),
                    activation("continue", "Continue regional"),
                ],
                "finish": False,
            }
        )
        cases.append(
            {
                "name": "static-calibration",
                "broken": broken,
                "rule": "button-name",
                "body": "<button></button>" if broken else "<button>Help</button>",
                "script": "",
                "steps": [],
                "finish": True,
                "static_defect": broken,
            }
        )
    return sorted(cases, key=lambda c: (c["name"], not c["broken"]))


def html(case):
    handler = (
        "if(document.getElementById('date').dataset.selected==='yes')done()"
        if case["name"] == "date-picker"
        else "done()"
    )
    finish = (
        f'<button onclick="{handler}">Finish task</button>' if case["finish"] else ""
    )
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Controlled task</title>
<main><h1>Task ready</h1>{case["body"]}<section id="stage"></section>{finish}</main>
<script>const stage=document.getElementById('stage'); const nameField=document.getElementById('name');
function done(){{stage.innerHTML='<h2>Done</h2>'}}
{case["script"]}</script></html>"""


def journey(case, target):
    return Journey(
        name=case["name"],
        target=target,
        allow_local=True,
        privacy={"capture_page_text": True},
        profile={"action_timeout_ms": 2000},
        tab_budget=6,
        steps=[
            Step(id="open", action="navigate"),
            Step(id="initial-audit", action="audit"),
            Step.model_validate(assertion("ready", "Task ready")),
            *[Step.model_validate(s) for s in case["steps"]],
            *(
                [Step.model_validate(activation("finish", "Finish task"))]
                if case["finish"]
                else []
            ),
            Step.model_validate(assertion("done", "Done")),
        ],
    )


def pa11y_command(*args):
    cli = ROOT / "benchmarks/pa11y/node_modules/pa11y/bin/pa11y.js"
    node = shutil.which("node")
    if not node or not cli.is_file():
        raise ValueError(
            "Install the optional locked benchmark tool with npm ci --prefix benchmarks/pa11y (PUPPETEER_SKIP_DOWNLOAD=true)"
        )
    return [node, str(cli), *args]


def run_tool(command, environment, timeout):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        env=environment,
        creationflags=0x08000000 if sys.platform == "win32" else 0,
    )
    owner = psutil.Process(process.pid)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        # Only descendants of the tool this invocation launched; never a global browser kill.
        try:
            children = owner.children(recursive=True)
        except psutil.NoSuchProcess:
            children = []
        for child in reversed(children):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(children, timeout=5)
        process.kill()
        process.communicate(timeout=5)
        raise


async def benchmark(output, *, pa11y=False, only=None):
    output.mkdir(parents=True, exist_ok=False)
    private_directory(output)
    store = Store(output / "workspace")
    axe = ROOT / "node_modules/axe-core/axe.min.js"
    results = []
    projects, previous = {}, {}
    key = os.urandom(32)
    tool_environment = {**os.environ, "PUPPETEER_SKIP_DOWNLOAD": "true"}
    config = output / "pa11y.json"
    pa11y_version = None
    full_chromium_version = None
    started_at = datetime.now(UTC).isoformat()
    if pa11y:
        shutil.copy2(
            ROOT / "benchmarks/pa11y/package-lock.json",
            output / "pa11y-package-lock.json",
        )
        async with async_playwright() as pw:
            executable = pw.chromium.executable_path
            full = await pw.chromium.launch(headless=True, executable_path=executable)
            try:
                full_chromium_version = full.version
            finally:
                await full.close()
        config.write_text(
            json.dumps(
                {
                    "chromeLaunchConfig": {
                        "executablePath": executable,
                        "args": ["--no-proxy-server"],
                    },
                    "viewport": {"width": 1280, "height": 800},
                    "standard": "WCAG2AA",
                    "runners": ["htmlcs"],
                    "timeout": 30000,
                    "wait": 0,
                }
            ),
            encoding="utf-8",
        )
        version = run_tool(pa11y_command("--version"), tool_environment, 120)
        if version.returncode != 0:
            raise RuntimeError(
                "Pa11y setup failed; inspect the tool installation separately"
            )
        pa11y_version = version.stdout.strip()
    started = time.monotonic()
    fixtures = FixtureServer()
    try:
        routes = {}
        with website(routes) as (target, _):
            for case in corpus():
                if only and case["name"] not in only:
                    continue
                routes["/"] = (200, {"Content-Type": "text/html"}, html(case))
                routes["/details"] = routes["/"]
                stem = case["name"] + ("-broken" if case["broken"] else "-working")
                (output / (stem + ".html")).write_text(html(case), encoding="utf-8")
                definition = journey(case, target)
                if case["name"] not in projects:
                    projects[case["name"]] = store.save_project(
                        ProjectInput(name=case["name"], journey=definition)
                    )
                pa11y_result = None
                if pa11y:
                    begin = time.perf_counter()
                    probe = run_tool(
                        pa11y_command(
                            target,
                            "--config",
                            str(config.resolve()),
                            "--reporter",
                            "json",
                        ),
                        tool_environment,
                        60,
                    )
                    (output / (stem + "-pa11y.stdout")).write_text(
                        probe.stdout, encoding="utf-8"
                    )
                    (output / (stem + "-pa11y.stderr")).write_text(
                        probe.stderr, encoding="utf-8"
                    )
                    try:
                        issues = json.loads(probe.stdout)
                    except json.JSONDecodeError:
                        issues = None
                    pa11y_result = {
                        "version": pa11y_version,
                        "status": "completed"
                        if probe.returncode in {0, 2} and isinstance(issues, list)
                        else "inconclusive",
                        "exit_code": probe.returncode,
                        "issues": issues,
                        "duration_seconds": round(time.perf_counter() - begin, 6),
                    }
                run = await execute(
                    store,
                    projects[case["name"]]["id"],
                    definition,
                    RunControl(),
                    fixtures,
                    axe,
                    inputs=RunInputs(definition, key=key),
                )
                (output / (stem + "-accessmaze.json")).write_text(
                    json.dumps(run, indent=2) + "\n", encoding="utf-8"
                )
                audit = next((s["audit"] for s in run["steps"] if s.get("audit")), None)
                expected_failure = case["broken"] and not case.get("static_defect")
                relevant = [
                    f
                    for f in run["findings"]
                    if f["rule"] == case["rule"]
                    and f["verification"] == "confirmed-automated"
                ]
                actual_task = run["outcome"]["status"]
                inconclusive = run.get("coverage_compromised") or actual_task not in {
                    "blocked",
                    "completed",
                }
                correct_task = actual_task == (
                    "blocked" if expected_failure else "completed"
                )
                record = {
                    "case": stem,
                    "fixture_sha256": hashlib.sha256(html(case).encode()).hexdigest(),
                    "expected_task": "blocked" if expected_failure else "completed",
                    "expected_rule": case["rule"] if case["broken"] else None,
                    "actual_task": actual_task,
                    "accessmaze_rules": [f["rule"] for f in run["findings"]],
                    "task_assessment": "inconclusive"
                    if inconclusive
                    else "correct"
                    if correct_task
                    else "false-negative"
                    if expected_failure
                    else "false-positive",
                    "expected_rule_observed": bool(relevant)
                    if case["broken"]
                    else None,
                    "unexpected_confirmed_findings": [
                        f["rule"]
                        for f in run["findings"]
                        if not (case["broken"] and f["rule"] == case["rule"])
                        and f["verification"] == "confirmed-automated"
                    ],
                    "environment": run["environment"],
                    "accessmaze_duration_seconds": run["duration_seconds"],
                    "initial_axe": audit,
                    "initial_pa11y": pa11y_result,
                }
                if case["name"] in previous:
                    record["comparison"] = compare_runs(previous[case["name"]], run)
                previous[case["name"]] = run
                results.append(record)
                (output / "results.partial.json").write_text(
                    json.dumps(results, indent=2) + "\n", encoding="utf-8"
                )
    finally:
        fixtures.close()
    summary = {
        "schema_version": 1,
        "host": platform.platform(),
        "cpu": platform.processor(),
        "ram_bytes": psutil.virtual_memory().total,
        "started_at": started_at,
        "finished_at": datetime.now(UTC).isoformat(),
        "full_chromium_version": full_chromium_version,
        "python": platform.python_version(),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
        "duration_seconds": round(time.monotonic() - started, 3),
        "pa11y_lock_sha256": hashlib.sha256(
            (ROOT / "benchmarks/pa11y/package-lock.json").read_bytes()
        ).hexdigest()
        if pa11y
        else None,
        "node_version": subprocess.check_output(
            [shutil.which("node"), "--version"], text=True
        ).strip()
        if pa11y
        else None,
        "results": results,
        "methodology": "Owned paired fixtures. AccessMaze executes the authored keyboard task; axe and Pa11y/HTMLCS probe only the same initial page in fresh contexts. Static absence is not a task false negative. Pa11y supports configured actions, which this baseline does not exercise. Timing workloads differ and do not establish tool speed rankings. Manual announcement and Accessibility Insights checks are not run.",
    }
    (output / "results.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--pa11y",
        action="store_true",
        help="Run pinned Pa11y 10 with the existing full Chromium",
    )
    parser.add_argument(
        "--only", nargs="+", choices=sorted({c["name"] for c in corpus()})
    )
    args = parser.parse_args()
    if (ROOT / ".accessmaze/browsers").is_dir():
        os.environ.setdefault(
            "PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".accessmaze/browsers")
        )
    result = asyncio.run(benchmark(args.output, pa11y=args.pa11y, only=args.only))
    print(
        json.dumps(
            {
                "cases": len(result["results"]),
                "seconds": result["duration_seconds"],
                "output": str(args.output),
            }
        )
    )
    if any(
        r["task_assessment"] != "correct"
        or r["unexpected_confirmed_findings"]
        or (r["expected_rule"] and not r["expected_rule_observed"])
        or (args.pa11y and r["initial_pa11y"]["status"] != "completed")
        for r in result["results"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
