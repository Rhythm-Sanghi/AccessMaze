"""Read-only public HTTPS smoke: navigation, heading assertion and private observations."""

import asyncio
import argparse
import json
import tempfile
from pathlib import Path

from accessmaze.fixtures import FixtureServer
from accessmaze.models import Journey, ProjectInput, Step
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store

ROOT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--heading", required=True)
    parser.add_argument("--authorized", action="store_true", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/website-smoke.json")
    args = parser.parse_args()
    journey = Journey(
        name="Public HTTPS smoke",
        target=args.url,
        max_seconds=30,
        steps=[
            Step(id="open", action="navigate"),
            Step(
                id="heading",
                action="assert_visible",
                target={"role": "heading", "name": args.heading},
            ),
        ],
    )
    fixtures = FixtureServer()
    try:
        with tempfile.TemporaryDirectory(
            prefix="AccessMaze website smoke "
        ) as directory:
            store = Store(Path(directory))
            project = store.save_project(
                ProjectInput(name="Public HTTPS smoke", journey=journey)
            )
            result = await execute(
                store,
                project["id"],
                journey,
                RunControl(),
                fixtures,
                ROOT / "node_modules/axe-core/axe.min.js",
            )
            evidence = {
                "target": journey.target,
                "scope": "Actual public HTTPS navigation and heading assertion; no effect actions",
                "status": result["status"],
                "coverage_compromised": result.get("coverage_compromised"),
                "seconds": result["duration_seconds"],
                "browser": result["environment"].get("browser"),
                "private_observations": all(
                    n["observation"].get("text_withheld") for n in result["nodes"]
                ),
                "error": result.get("error"),
                "steps": [
                    {"id": s["id"], "status": s["status"]} for s in result["steps"]
                ],
                "finding_rules": [f["rule"] for f in result["findings"]],
                "limitations": result["limitations"],
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(evidence, indent=2))
            assert result["status"] == "completed_with_limitations"
            assert not result["coverage_compromised"]
    finally:
        fixtures.close()


if __name__ == "__main__":
    asyncio.run(main())
