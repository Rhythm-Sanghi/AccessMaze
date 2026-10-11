"""Run reviewed authored journeys across at most eight profiles, one browser at a time."""

import argparse
import asyncio
import json
import os
import secrets
import time
from pathlib import Path

from accessmaze.fixtures import FixtureServer
from accessmaze.inputs import RunInputs
from accessmaze.models import Journey, ProfileInput, ProjectInput
from accessmaze.permissions import private_directory
from accessmaze.profiles import apply_conditions
from accessmaze.retests import compare_runs
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store

ROOT = Path(__file__).resolve().parents[1]


async def run_batch(
    journey,
    profiles,
    output,
    fixtures,
    axe_path,
    *,
    inputs=None,
    authorized=False,
    allow_effects=False,
    max_seconds=600,
):
    if not authorized:
        raise ValueError("Explicit target authorization is required")
    if journey.exploration.enabled:
        raise ValueError(
            "Batch execution supports authored paths only; disable discovery"
        )
    if any(step.effect for step in journey.steps) and not allow_effects:
        raise ValueError(
            "Explicit approval for every journey's state-changing actions is required"
        )
    if not 1 <= len(profiles) <= 8 or not 1 <= max_seconds <= 1800:
        raise ValueError("Batch bounds are 1–8 profiles and 1–1800 execution seconds")
    key = secrets.token_bytes(32)
    candidates = [
        Journey.model_validate(
            {**journey.model_dump(), "profile": p.profile.model_dump()}
        )
        for p in profiles
    ]
    for candidate in candidates:
        apply_conditions(candidate)
        RunInputs(candidate, inputs, key)
    output.mkdir(parents=True, exist_ok=False)
    private_directory(output)
    store = Store(output / "workspace")
    project = store.save_project(ProjectInput(name=journey.name, journey=journey))
    started = time.monotonic()
    summary = {
        "schema_version": 1,
        "concurrency": 1,
        "max_profiles": 8,
        "execution_budget_seconds": max_seconds,
        "status": "running",
        "runs": [],
        "comparisons": [],
        "limitation": "Profile comparisons describe changed conditions; they do not verify repairs. Fresh contexts do not reset external server state. No automatic retry or discovery.",
    }
    previous = None
    try:
        for profile, candidate in zip(profiles, candidates, strict=True):
            remaining = max_seconds - (time.monotonic() - started)
            if remaining < 1:
                summary["status"] = "budget-exhausted"
                break
            candidate.max_seconds = min(candidate.max_seconds, int(remaining))
            result = await execute(
                store,
                project["id"],
                candidate,
                RunControl(),
                fixtures,
                axe_path,
                inputs=RunInputs(candidate, inputs, key),
            )
            summary["runs"].append(
                {
                    "profile_name": profile.name,
                    "profile": candidate.profile.model_dump(),
                    "run_id": result["id"],
                    "status": result["status"],
                    "outcome": result["outcome"],
                    "duration_seconds": result["duration_seconds"],
                    "environment": result["environment"],
                }
            )
            if previous:
                summary["comparisons"].append(compare_runs(previous, result))
            previous = result
            (output / "batch.json").write_text(
                json.dumps(summary, indent=2) + "\n", encoding="utf-8"
            )
            if result["status"] == "cancelled" or asyncio.current_task().cancelling():
                summary["status"] = "cancelled"
                break
        else:
            summary["status"] = "completed"
    finally:
        summary["duration_seconds"] = round(time.monotonic() - started, 3)
        if summary["status"] == "running":
            summary["status"] = "interrupted"
        (output / "batch.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journey", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument(
        "--inputs", type=Path, help="Run-only values/files; never copied to output"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--allow-effects", action="store_true")
    args = parser.parse_args()
    journey = Journey.model_validate_json(args.journey.read_text(encoding="utf-8"))
    profiles = [
        ProfileInput.model_validate(p)
        for p in json.loads(args.profiles.read_text(encoding="utf-8"))
    ]
    inputs = (
        json.loads(args.inputs.read_text(encoding="utf-8")) if args.inputs else None
    )
    if (ROOT / ".accessmaze/browsers").is_dir():
        os.environ.setdefault(
            "PLAYWRIGHT_BROWSERS_PATH", str(ROOT / ".accessmaze/browsers")
        )
    fixtures = FixtureServer()
    try:
        result = asyncio.run(
            run_batch(
                journey,
                profiles,
                args.output,
                fixtures,
                ROOT / "node_modules/axe-core/axe.min.js",
                inputs=inputs,
                authorized=args.authorized,
                allow_effects=args.allow_effects,
                max_seconds=args.seconds,
            )
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "runs": len(result["runs"]),
                    "output": str(args.output),
                }
            )
        )
    finally:
        fixtures.close()


if __name__ == "__main__":
    main()
