import json

import pytest
from test_distribution_notices import script


def test_distribution_review_refuses_to_exclude_newly_shipped_package(tmp_path):
    component = {
        "ecosystem": "npm",
        "name": "example-build-tool",
        "version": "1.0",
        "declared_license": "MIT",
        "notices": [],
    }
    baseline = tmp_path / "baseline.json"
    inventory = tmp_path / "inventory.json"
    modules = tmp_path / "modules.json"
    toc = tmp_path / "Analysis-00.toc"
    baseline.write_text(json.dumps({"unresolved": [component]}))
    inventory.write_text(json.dumps({"components": [component], "unresolved": [component]}))
    modules.write_text("[]")
    toc.write_text("[]")
    helper = script("license_gap_review")
    result = helper.review(baseline, inventory, modules, toc)
    assert result["original_gaps"] == 1
    assert result["resolutions"][0]["classification"].startswith("false positive")
    modules.write_text(json.dumps(["node_modules/example-build-tool/runtime.js"]))
    with pytest.raises(ValueError, match="Unexpected.*production UI"):
        helper.review(baseline, inventory, modules, toc)


def test_cargo_scope_is_recomputed_when_build_dependency_gains_ordinary_path(tmp_path, monkeypatch):
    component = {
        "ecosystem": "cargo",
        "name": "example-parser",
        "version": "1.0",
        "declared_license": "MIT",
        "notices": [],
    }
    baseline, inventory, modules, toc = [
        tmp_path / name
        for name in ["baseline.json", "inventory.json", "modules.json", "Analysis-00.toc"]
    ]
    baseline.write_text(json.dumps({"unresolved": [component]}))
    inventory.write_text(json.dumps({"components": [component], "unresolved": [component]}))
    modules.write_text("[]")
    toc.write_text("[]")
    helper = script("license_gap_review")
    original = helper.subprocess.check_output
    graph = ""

    def output(args, **kwargs):
        return graph if args[0] == "cargo" else original(args, **kwargs)

    monkeypatch.setattr(helper.subprocess, "check_output", output)
    build = helper.review(baseline, inventory, modules, toc)
    assert build["resolutions"][0]["classification"].startswith("build-graph-only")
    graph = "example-parser v1.0\n"
    ordinary = helper.review(baseline, inventory, modules, toc)
    assert ordinary["resolutions"][0]["ordinary_windows_dependency_path"]
    assert "linkage not proven" in ordinary["resolutions"][0]["classification"]
    assert ordinary["windows_normal_graph_sha256"] != build["windows_normal_graph_sha256"]
