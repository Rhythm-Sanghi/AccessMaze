from accessmaze.retests import compare_runs


def run(run_id, status="completed_with_limitations", findings=None):
    return {
        "id": run_id,
        "project_id": "project",
        "journey": {"target": "same"},
        "status": status,
        "steps": [{"id": "date", "status": "passed"}],
        "findings": findings or [],
    }


def test_retest_pass_requires_completed_same_configuration():
    finding = {
        "id": "f",
        "step_id": "date",
        "rule": "keyboard-unreachable",
        "verification": "confirmed-automated",
    }
    old = run("old", "failed", [finding])
    new = run("new")
    assert compare_runs(old, new)["findings"][0]["verdict"] == "passed-retest"
    new["coverage_compromised"] = True
    assert compare_runs(old, new)["findings"][0]["verdict"] == "inconclusive"
    new["coverage_compromised"] = False
    new["status"] = "cancelled"
    assert compare_runs(old, new)["findings"][0]["verdict"] == "inconclusive"
    new["status"] = "completed_with_limitations"
    new["journey"] = {"target": "changed"}
    assert compare_runs(old, new)["findings"][0]["verdict"] == "inconclusive"


def test_axe_incomplete_does_not_resolve_finding():
    old = run(
        "old",
        "failed",
        [{"id": "f", "step_id": "date", "rule": "contrast", "verification": "confirmed-automated"}],
    )
    new = run("new")
    new["steps"][0]["audit"] = {"incomplete": [{"id": "contrast"}]}
    assert compare_runs(old, new)["findings"][0]["verdict"] == "inconclusive"
