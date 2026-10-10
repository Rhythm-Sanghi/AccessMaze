import asyncio
import importlib.util
import os
from pathlib import Path

import pytest


@pytest.mark.browser
def test_paired_corpus_records_actual_task_and_initial_scanner_results(tmp_path):
    path = Path(__file__).resolve().parents[2] / "scripts/comparative_benchmark.py"
    spec = importlib.util.spec_from_file_location("comparative_benchmark", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # CI explicitly installs the optional locked scanner; ordinary pytest runs do
    # not download tools. Each recorded result states which probes actually ran.
    pa11y = os.environ.get("ACCESSMAZE_CORPUS_PA11Y") == "1"
    output = Path(os.environ.get("ACCESSMAZE_CORPUS_OUTPUT", str(tmp_path / "corpus")))
    result = asyncio.run(module.benchmark(output, pa11y=pa11y))
    assert len(result["results"]) == 16
    for case in result["results"]:
        assert case["task_assessment"] == "correct", case
        assert not case["unexpected_confirmed_findings"], case
        if pa11y:
            assert case["initial_pa11y"]["status"] == "completed"
        else:
            assert case["initial_pa11y"] is None
        assert case["initial_axe"]["engine"]["name"] == "axe-core"
        assert case["initial_axe"]["engine"]["version"]
        assert len(case["environment"]["axe_sha256"]) == 64
        if case["expected_rule"]:
            assert case["expected_rule_observed"], case
        if case["case"] == "static-calibration-broken":
            assert any(v["id"] == "button-name" for v in case["initial_axe"]["violations"])
        elif case["case"].endswith("-working"):
            assert case["initial_axe"]["violations"] == []
        if "comparison" in case:
            assert case["comparison"]["comparable"]
            assert case["comparison"]["verdict"] == "verified-improvement"
