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
