from copy import deepcopy

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


def axe_finding(target, finding_id="f"):
    return {
        "id": finding_id,
        "step_id": "date",
        "rule": "button-name",
        "verification": "confirmed-automated",
        "actual": {"targets": [[target]]},
    }


def test_affected_controls_are_not_conflated_and_absent_audit_cannot_verify_repair():
    old = run("old", findings=[axe_finding("#first")])
    new = run("new", findings=[axe_finding("#second", "new-f")])
    comparison = compare_runs(old, new)
    assert comparison["findings"][0]["verdict"] == "inconclusive"
    assert comparison["added_findings"][0]["finding_id"] == "new-f"
    new["findings"] = []
    assert compare_runs(old, new)["findings"][0]["verdict"] == "inconclusive"
    new["steps"][0]["audit"] = {"incomplete": [], "violations": []}
    assert compare_runs(old, new)["findings"][0]["verdict"] == "passed-retest"


def test_private_tokens_are_never_matched_as_target_identities():
    old = run("old", findings=[axe_finding("[private text aaa]")])
    new = run("new", findings=[axe_finding("[private text bbb]")])
    comparison = compare_runs(old, new)
    assert comparison["findings"][0]["verdict"] == "inconclusive"
    assert comparison["warnings"]
    assert not comparison["added_findings"]


def test_reordering_aligns_by_step_id_without_claiming_repair():
    old = run("old", findings=[axe_finding("#first")])
    old["journey"]["steps"] = [{"id": "open"}, {"id": "date"}]
    old["steps"].insert(0, {"id": "open", "status": "passed"})
    new = deepcopy(old)
    new["id"] = "new"
    new["journey"]["steps"].reverse()
    new["steps"].reverse()
    new["steps"][0]["status"] = "failed"
    # Definitions are intentionally minimal legacy records for descriptive comparison.
    old["journey"]["steps"][0]["action"] = "navigate"
    old["journey"]["steps"][1]["action"] = "audit"
    new["journey"]["steps"][0]["action"] = "audit"
    new["journey"]["steps"][1]["action"] = "navigate"
    comparison = compare_runs(old, new)
    assert not comparison["comparable"]
    assert comparison["changed_conditions"] == ["steps"]
    assert comparison["first_divergent_step"]["step_id"] == "date"
    assert comparison["findings"][0]["verdict"] == "inconclusive"
