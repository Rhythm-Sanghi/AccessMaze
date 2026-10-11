import asyncio
import importlib.util
from pathlib import Path

import pytest

from accessmaze.models import ProfileInput
from accessmaze.templates import template


@pytest.mark.browser
def test_batch_applies_profiles_serially_without_claiming_repairs(tmp_path, fixtures, axe_path):
    path = Path(__file__).resolve().parents[2] / "scripts/profile_batch.py"
    spec = importlib.util.spec_from_file_location("profile_batch", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profiles = [
        ProfileInput(name="Keyboard", profile={}),
        ProfileInput(name="Pointer", profile={"keyboard_only": False}),
    ]
    output = tmp_path / "batch"
    with pytest.raises(ValueError, match="authorization"):
        asyncio.run(module.run_batch(template("broken"), profiles, output, fixtures, axe_path))
    assert not output.exists()
    with pytest.raises(ValueError, match="state-changing"):
        asyncio.run(
            module.run_batch(
                template("broken"), profiles, output, fixtures, axe_path, authorized=True
            )
        )
    assert not output.exists()
    result = asyncio.run(
        module.run_batch(
            template("broken"),
            profiles,
            output,
            fixtures,
            axe_path,
            authorized=True,
            allow_effects=True,
            max_seconds=30,
        )
    )
    assert result["concurrency"] == 1
    assert [r["outcome"]["status"] for r in result["runs"]] == ["blocked", "completed"]
    assert all(r["profile"]["schema_version"] == 1 for r in result["runs"])
    assert result["comparisons"][0]["verdict"] == "inconclusive-different-conditions"
    with pytest.raises(FileExistsError):
        asyncio.run(
            module.run_batch(
                template("broken"),
                profiles,
                output,
                fixtures,
                axe_path,
                authorized=True,
                allow_effects=True,
            )
        )
