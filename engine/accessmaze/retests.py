import json

from accessmaze.outcomes import task_outcome


def finding_identity(finding):
    """Group by stable step ID/rule and the sorted axe affected-target set."""
    actual = finding.get("actual")
    targets = actual.get("targets", []) if isinstance(actual, dict) else []
    # Private page-text tokens deliberately use different keys for different runs.
    if "[private text " in json.dumps(targets):
        return None
    return (
        finding["step_id"],
        finding["rule"],
        tuple(sorted({json.dumps(t, sort_keys=True) for t in targets})),
    )


def compare_runs(previous, current):
    """Resolve only against the same assertion and configuration in a completed rerun."""
    comparable = (
        previous["project_id"] == current["project_id"]
        and previous["journey"] == current["journey"]
        and previous["id"] != current["id"]
        and not current.get("coverage_compromised", False)
        and previous.get("input_signature") == current.get("input_signature")
        and previous.get("environment", {}) == current.get("environment", {})
    )
    records = []
    for finding in previous["findings"]:
        step = next((s for s in current["steps"] if s["id"] == finding["step_id"]), None)
        identity = finding_identity(finding)
        matching = [
            f
            for f in current["findings"]
            if identity is not None and finding_identity(f) == identity
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
            is_axe = isinstance(finding.get("actual"), dict) and "targets" in finding["actual"]
            rule_still_observed = any(
                f["step_id"] == finding["step_id"] and f["rule"] == finding["rule"]
                for f in current["findings"]
            )
            if (
                not rule_still_observed
                and (not is_axe or audit is not None)
                and (
                    audit is None
                    or finding["rule"] not in {r["id"] for r in audit.get("violations", [])}
                )
                and (audit is None or finding["rule"] not in {r["id"] for r in audit["incomplete"]})
            ):
                verdict = "passed-retest"
        records.append(
            {
                "finding_id": finding["id"],
                "rule": finding["rule"],
                "step_id": finding["step_id"],
                "verdict": verdict,
            }
        )
    before = {s["id"]: s for s in previous["steps"]}
    after = {s["id"]: s for s in current["steps"]}
    aligned = []
    for step_id in dict.fromkeys([*before, *after]):
        a, b = before.get(step_id, {}), after.get(step_id, {})
        aligned.append(
            {
                "step_id": step_id,
                "previous_status": a.get("status", "not-reached"),
                "current_status": b.get("status", "not-reached"),
                "previous_state_id": a.get("state_id"),
                "current_state_id": b.get("state_id"),
            }
        )
    changes = [
        key
        for key in sorted(set(previous["journey"]) | set(current["journey"]))
        if previous["journey"].get(key) != current["journey"].get(key)
    ]
    if previous.get("input_signature") != current.get("input_signature"):
        changes.append("runtime-input-signature")
    identities = {finding_identity(f) for f in previous["findings"]} - {None}
    added = [
        {"finding_id": f["id"], "step_id": f["step_id"], "rule": f["rule"]}
        for f in current["findings"]
        if finding_identity(f) is not None and finding_identity(f) not in identities
    ]
    warnings = []
    if not comparable:
        warnings.append(
            "Repair verification requires the same project, journey, environment and runtime "
            "inputs, distinct runs and uncompromised candidate coverage."
        )
    if any(finding_identity(f) is None for f in [*previous["findings"], *current["findings"]]):
        warnings.append(
            "Private affected-target tokens cannot be matched across runs; affected findings "
            "remain inconclusive while the rule is observed."
        )
    if current["status"] not in {"completed", "completed_with_limitations"}:
        warnings.append("Candidate execution did not complete; missing findings are not resolved.")
    return {
        "previous_id": previous["id"],
        "current_id": current["id"],
        "comparable": comparable,
        "findings": records,
        "added_findings": added,
        "steps": aligned,
        "first_divergent_step": next(
            (s for s in aligned if s["previous_status"] != s["current_status"]), None
        ),
        "previous_outcome": task_outcome(previous),
        "current_outcome": task_outcome(current),
        "changed_conditions": changes,
        "environment_changes": [
            key
            for key in sorted(
                set(previous.get("environment", {})) | set(current.get("environment", {}))
            )
            if previous.get("environment", {}).get(key) != current.get("environment", {}).get(key)
        ],
        "warnings": warnings,
        "matching_rule": (
            "Stable step ID + rule + exact affected-target set; array positions and private "
            "text tokens are never identities. Reordered definitions are descriptive only, "
            "not repair verification."
        ),
        "limitation": "A passed retest verifies only this configuration and execution.",
    }
