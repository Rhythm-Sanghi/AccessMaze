"""Repeatable browser corpus. Public targets are opt-in, allowlisted educational pages."""

import argparse
import asyncio
import base64
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine/tests"))
from compatibility_app import CompatibilityApp  # noqa: E402
from accessmaze.fixtures import FixtureServer  # noqa: E402
from accessmaze.inputs import RunInputs  # noqa: E402
from accessmaze.models import Journey, ProjectInput, Step  # noqa: E402
from accessmaze.runner import RunControl, execute  # noqa: E402
from accessmaze.storage import Store  # noqa: E402


def public_journeys():
    return [
        Journey(
            name="Selenium official web form",
            target="https://www.selenium.dev/selenium/web/web-form.html",
            network={
                "resource_origins": [
                    "https://cdn.jsdelivr.net",
                    "https://code.jquery.com",
                    "https://unpkg.com",
                ]
            },
            steps=[
                Step(id="open", action="navigate"),
                Step(
                    id="text",
                    action="fill",
                    target={"role": "textbox", "name": "Text input"},
                    value="Synthetic compatibility",
                ),
                Step(
                    id="submit",
                    action="activate",
                    effect=True,
                    target={"role": "button", "name": "Submit"},
                ),
                Step(
                    id="received",
                    action="assert_visible",
                    target={"role": "heading", "name": "Form submitted"},
                ),
                Step(id="audit", action="audit"),
            ],
        ),
        *[
            Journey(
                name="W3C educational " + variant,
                target=f"https://www.w3.org/WAI/demos/bad/{variant}/home.html",
                steps=[
                    Step(id="open", action="navigate"),
                    Step(
                        id="page",
                        action="assert_visible",
                        target={"role": "heading", "name": heading},
                    ),
                    Step(id="audit", action="audit"),
                ],
            )
            for variant, heading in [
                ("before", "Inaccessible Home Page - Before and After Demonstration"),
                ("after", "Accessible Home Page - Before and After Demonstration"),
            ]
        ],
    ]


async def run_case(store, fixtures, journey, inputs=None):
    project = store.save_project(ProjectInput(name=journey.name, journey=journey))
    run = await execute(
        store,
        project["id"],
        journey,
        RunControl(),
        fixtures,
        ROOT / "node_modules/axe-core/axe.min.js",
        inputs=inputs,
    )
    return {
        "case": journey.name,
        "status": run["status"],
        "coverage_compromised": run["coverage_compromised"],
        "seconds": run["duration_seconds"],
        "browser": run["environment"].get("browser"),
        "steps": [{k: s[k] for k in ["id", "status"]} for s in run["steps"]],
        "rules": sorted({f["rule"] for f in run["findings"]}),
        "limitations": run["limitations"],
        "error": run.get("error"),
    }


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public",
        action="store_true",
        help="Authorize only the three documented public demo cases",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/testing/compatibility.json"
    )
    args = parser.parse_args()
    cases = []
    fixtures = FixtureServer()
    try:
        with tempfile.TemporaryDirectory(prefix="AccessMaze compatibility ") as folder:
            store = Store(Path(folder))
            with CompatibilityApp() as app:
                journey = app.journey()
                inputs = RunInputs(
                    journey,
                    {
                        "files": {
                            "document": {
                                "name": "synthetic.txt",
                                "base64": base64.b64encode(
                                    b"Compatibility corpus only"
                                ).decode(),
                            }
                        }
                    },
                )
                cases.append(await run_case(store, fixtures, journey, inputs))
                cases[-1]["server_observations"] = app.summary()
            if args.public:
                for journey in public_journeys():
                    cases.append(await run_case(store, fixtures, journey))
    finally:
        fixtures.close()
    result = {
        "scope": "Real Chromium, isolated contexts; no NVDA or WCAG certification",
        "public_authorized": args.public,
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if any(
        case["status"] != "completed_with_limitations" or case["coverage_compromised"]
        for case in cases
    ):
        raise SystemExit(
            "Compatibility incomplete; inspect recorded results and permissions"
        )


if __name__ == "__main__":
    asyncio.run(main())
