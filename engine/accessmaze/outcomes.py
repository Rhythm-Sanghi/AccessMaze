"""Task outcomes are derived from recorded assertions, never from a finding count."""


def task_outcome(run):
    definitions = run.get("journey", {}).get("steps", [])
    recorded = {s["id"]: s for s in run.get("steps", [])}
    assertions = [
        {"step_id": s["id"], "status": recorded.get(s["id"], {}).get("status", "not-reached")}
        for s in definitions
        if s["action"].startswith("assert_") and not s.get("optional", False)
    ]
    failed = next(
        (
            s
            for s in definitions
            if not s.get("optional", False) and recorded.get(s["id"], {}).get("status") == "failed"
        ),
        None,
    )
    status = "incomplete"
    reason = "Required assertions have not all been verified in a completed execution."
    if run["status"] == "cancelled":
        status, reason = "cancelled", "Execution was cancelled; partial evidence is retained."
    elif run.get("coverage_compromised"):
        status, reason = "inconclusive", "Blocked traffic may have changed the tested application."
    elif failed:
        confirmed = any(
            f["step_id"] == failed["id"] and f["verification"] == "confirmed-automated"
            for f in run.get("findings", [])
        )
        status = "blocked" if confirmed else "inconclusive"
        reason = (
            "A required interaction or assertion failed in this bounded attempt."
            if confirmed
            else "A required step failed without a confirmed accessibility barrier."
        )
    elif (
        assertions
        and all(a["status"] == "passed" for a in assertions)
        and run["status"] in {"completed", "completed_with_limitations"}
    ):
        status, reason = "completed", "All mandatory assertions passed in this execution."
    return {
        "status": status,
        "reason": reason,
        "assertions": assertions,
        "blocked_step_id": failed["id"] if failed else None,
        "limitation": (
            "Task completion does not establish accessibility conformance or untested coverage."
        ),
    }
