"""Rebuild historical definitions without recovering saved plaintext input values."""

from accessmaze.models import Journey
from accessmaze.retests import finding_identity


def replay_recipe(run, finding):
    """A chronological witness, not an automatic reset or a promise of server state."""
    actions = run.get("exploration", {}).get("actions", [])
    authored = {s["id"] for s in run["journey"]["steps"]}
    relevant = []
    if finding["step_id"] not in authored:
        if run["journey"]["target"].startswith("fixture://") and finding.get("replay_steps"):
            relevant = [
                {"step_id": step["id"], "replay_step": step} for step in finding["replay_steps"]
            ]
        else:
            for action in actions:
                relevant.append(action)
                if action["step_id"] == finding["step_id"]:
                    break
        if not relevant or relevant[-1]["step_id"] != finding["step_id"]:
            return {
                "schema_version": 1,
                "available": False,
                "reason": "No supported chronological discovery witness",
            }
        if any(not a.get("replay_step") for a in relevant):
            return {
                "schema_version": 1,
                "available": False,
                "reason": "Discovery target text was withheld. Author a new journey or explicitly "
                "enable page-text retention before recording a new path.",
            }
    available = len(run["journey"]["steps"]) + len(relevant) <= 100
    return {
        "schema_version": 1,
        "available": available,
        "reason": "Review prerequisites and authorize every effect; server state is not restored"
        if available
        else "Recipe exceeds the 100-step import bound",
        "discovered_steps": [a["replay_step"] for a in relevant] if available else [],
        "observation_ids": [a.get("source") for a in relevant]
        + [a.get("state_id") for a in relevant],
        "requirements": {
            "network": run["journey"].get("network", {}),
            "profile": run["journey"].get("profile", {}),
            "fresh_runtime_inputs": True,
            "explicit_effect_approval": True,
        },
        "preconditions": "Fresh browser context; application/server prerequisites "
        "must be supplied by the tester",
    }


def prepare_replay(run, finding_id):
    finding = next((f for f in run.get("findings", []) if f["id"] == finding_id), None)
    if finding is None:
        raise ValueError("Recorded finding not found")
    data = run["journey"]
    # A schema round-trip copies the original. Redacted literals need new run-only bindings.
    import copy
    import hashlib

    data = copy.deepcopy(data)
    recorded_step_ids = {step["id"] for step in data["steps"]}
    data["steps"] = [
        s
        for s in data["steps"]
        if s["id"] not in {"profile-offline", "profile-online", "profile-focus", "profile-audit"}
    ]
    data["exploration"] = {**data.get("exploration", {}), "enabled": False}
    for step in data["steps"]:
        if step["action"] in {"fill", "assert_value"}:
            if not step.get("value_from"):
                step["value_from"] = (
                    "replay_" + hashlib.sha256(step["id"].encode()).hexdigest()[:16]
                )
            step["value"] = ""
    if finding["step_id"] not in recorded_step_ids:
        recipe = finding.get("replay_recipe") or replay_recipe(run, finding)
        if not recipe["available"]:
            raise ValueError(recipe["reason"])
        data["steps"].extend(recipe["discovered_steps"])
    return Journey.model_validate(data)


def replay_verdict(original, current, finding_id):
    finding = next(f for f in original["findings"] if f["id"] == finding_id)
    observed = [
        f
        for f in current.get("findings", [])
        if f["step_id"] == finding["step_id"] and f["rule"] == finding["rule"]
    ]
    if current.get("coverage_compromised"):
        return "inconclusive-blocked-traffic"
    if current.get("environment", {}).get("browser") and original.get(
        "environment", {}
    ) != current.get("environment", {}):
        return "environment-changed"
    if observed:
        identity = finding_identity(finding)
        return (
            "observed-again"
            if identity is not None and any(finding_identity(f) == identity for f in observed)
            else "similar-finding-review-target"
        )
    step = next((s for s in current.get("steps", []) if s["id"] == finding["step_id"]), None)
    if step and step["status"] == "passed":
        if original["journey"]["target"] != current["journey"]["target"]:
            return "environment-changed"
        if original.get("input_signature") != current.get("input_signature"):
            return "inconclusive-different-inputs"
        return "not-reproduced-in-this-run"
    return "inconclusive-step-not-passed"
