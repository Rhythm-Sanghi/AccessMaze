from accessmaze.outcomes import task_outcome


def record(status="completed_with_limitations"):
    return {
        "status": status,
        "journey": {
            "steps": [
                {"id": "go", "action": "activate"},
                {"id": "goal", "action": "assert_visible"},
            ]
        },
        "steps": [{"id": "go", "status": "passed"}, {"id": "goal", "status": "passed"}],
        "findings": [],
    }


def test_completion_requires_recorded_assertions_and_completed_execution():
    run = record()
    assert task_outcome(run)["status"] == "completed"
    run["steps"].pop()
    assert task_outcome(run)["status"] == "incomplete"
    assert task_outcome(run)["assertions"][0]["status"] == "not-reached"
    run = record("interrupted")
    assert task_outcome(run)["status"] == "incomplete"
    run["status"] = "cancelled"
    assert task_outcome(run)["status"] == "cancelled"


def test_failure_is_not_automatically_an_accessibility_barrier():
    run = record("failed")
    run["steps"][0]["status"] = "failed"
    assert task_outcome(run)["status"] == "inconclusive"
    run["findings"] = [{"step_id": "go", "verification": "confirmed-automated"}]
    assert task_outcome(run)["status"] == "blocked"
    assert task_outcome(run)["blocked_step_id"] == "go"
    run["coverage_compromised"] = True
    assert task_outcome(run)["status"] == "inconclusive"


def test_optional_assertions_and_audit_findings_do_not_invent_task_failure():
    run = record()
    run["journey"]["steps"].append({"id": "optional", "action": "assert_focus", "optional": True})
    run["findings"] = [{"step_id": "audit", "verification": "confirmed-automated"}]
    assert task_outcome(run)["status"] == "completed"
    run["journey"]["steps"] = []
    assert task_outcome(run)["status"] == "incomplete"
