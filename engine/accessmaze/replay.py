"""Rebuild historical definitions without recovering saved plaintext input values."""

from accessmaze.models import Journey
from accessmaze.retests import finding_identity


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
        raise ValueError(
            "Discovery findings need an authored journey before replay; "
            "transient approved targets are not retained in private evidence"
        )
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
    if observed:
        identity = finding_identity(finding)
        return (
            "observed-again"
            if identity is not None and any(finding_identity(f) == identity for f in observed)
            else "similar-finding-review-target"
        )
    step = next((s for s in current.get("steps", []) if s["id"] == finding["step_id"]), None)
    if step and step["status"] == "passed":
        return "not-reproduced-in-this-run"
    return "inconclusive-step-not-passed"
