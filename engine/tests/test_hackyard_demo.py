import asyncio
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.mark.browser
def test_demo_records_real_failure_fix_and_replay(tmp_path, monkeypatch):
    # The standalone demo may choose the local browser cache. Never change the
    # cache used by subsequent tests in this process.
    import os

    if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
        monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", os.environ["PLAYWRIGHT_BROWSERS_PATH"])
    else:
        monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    path = Path(__file__).resolve().parents[2] / "scripts/hackyard_demo.py"
    spec = importlib.util.spec_from_file_location("hackyard_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "demo"
    result = asyncio.run(module.demonstrate(output))
    assert result["server_observations"]["api_posts"] == 1
    assert result["isolated_page_findings"] == 0
    isolated = json.loads((output / "isolated-check.json").read_text(encoding="utf-8"))
    assert isolated["steps"][1]["action"] == "audit"
    assert isolated["steps"][1]["audit"]["violations"] == []
    assert result["broken_outcome"]["status"] == "blocked"
    assert result["fixed_outcome"]["status"] == "completed"
    assert result["environment_outcome"]["status"] == "blocked"
    environment = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    assert any(f["rule"] == "form-state-lost" for f in environment["findings"])
    assert "Task outcome: blocked" in (output / "environment.html").read_text(encoding="utf-8")
    assert "passed-retest" in (output / "retest.json").read_text()
    draft = json.loads((output / "recorded-draft.json").read_text())
    assert any(s["value_from"] for s in draft["steps"])
    assert (output / "correction.diff").read_text().count("+<") > 0
    with pytest.raises(FileExistsError):
        asyncio.run(module.demonstrate(output))
