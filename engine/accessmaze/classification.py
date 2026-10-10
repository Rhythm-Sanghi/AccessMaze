"""Conservative categories describe evidence; they do not certify accessibility."""


def classify_failure(rule, *, blocked=False, verification="inconclusive"):
    if blocked:
        return "network-policy-restriction"
    if rule == "completion-assertion":
        return "completion-assertion-failure"
    if rule in {"target-ambiguous", "upload-input"}:
        return "test-definition-error"
    if rule in {"target-disabled", "frame-unavailable", "navigation-http"}:
        return "application-state-unavailable"
    if rule == "sensitive-field":
        return "missing-authorization"
    if rule in {"audit-unavailable", "native-validation-unverified"}:
        return "browser-environment-limitation"
    if rule == "browser-action":
        return "transient-execution-failure"
    if rule == "execution-budget":
        return "exploration-budget-exhaustion"
    return (
        "observed-accessibility-failure"
        if verification == "confirmed-automated"
        else "inconclusive-investigation"
    )
