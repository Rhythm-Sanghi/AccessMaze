"""Generate the authoritative import schema; --check verifies committed schema freshness."""

import json
import re
import sys
from pathlib import Path
from typing import get_args

from accessmaze.models import Journey, Request, Step, Target

root = Path(__file__).resolve().parents[1] / "packages" / "contracts"
typescript = (root / "index.ts").read_text(encoding="utf-8")
for name, annotation in [
    ("Action", Step.model_fields["action"].annotation),
    ("Role", Target.model_fields["role"].annotation),
    ("Method", Request.model_fields["method"].annotation),
]:
    match = re.search(rf"export type {name}\s*=([^;]+);", typescript)
    actual = set(re.findall(r'"([^"]+)"', match.group(1))) if match else set()
    if actual != set(get_args(annotation)):
        raise SystemExit(f"TypeScript {name} does not match the worker contract")
for name, model in [("journey", Journey), ("request", Request)]:
    content = json.dumps(model.model_json_schema(), indent=2) + "\n"
    path = root / f"{name}.schema.json"
    if "--check" in sys.argv:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"Stale contract: {path.name}")
    else:
        path.write_text(content, encoding="utf-8")
