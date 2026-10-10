def compare_runs(previous, current):
    """Resolve only against the same assertion and configuration in a completed rerun."""
    comparable = (
        previous["project_id"] == current["project_id"]
        and previous["journey"] == current["journey"]
        and previous["id"] != current["id"]
        and not current.get("coverage_compromised", False)
        and previous.get("input_signature") == current.get("input_signature")
    )
    records = []
    for finding in previous["findings"]:
        step = next((s for s in current["steps"] if s["id"] == finding["step_id"]), None)
        matching = [
            f
            for f in current["findings"]
            if f["step_id"] == finding["step_id"] and f["rule"] == finding["rule"]
        ]
        verdict = "inconclusive"
        if comparable and matching:
            verdict = "still-observed"
        elif (
            comparable
            and step
            and step["status"] == "passed"
            and current["status"] in {"completed", "completed_with_limitations"}
            and finding["verification"] == "confirmed-automated"
        ):
            audit = step.get("audit")
            # axe rules can disappear into an incomplete/manual-review result.
            if audit is None or finding["rule"] not in {r["id"] for r in audit["incomplete"]}:
                verdict = "passed-retest"
        records.append(
            {
                "finding_id": finding["id"],
                "rule": finding["rule"],
                "step_id": finding["step_id"],
                "verdict": verdict,
            }
        )
    return {
        "previous_id": previous["id"],
        "current_id": current["id"],
        "comparable": comparable,
        "findings": records,
        "limitation": "A passed retest verifies only this configuration and execution.",
    }
