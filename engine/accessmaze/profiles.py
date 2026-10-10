"""Concrete, inspectable conditions; no disability or screen-reader simulation."""

from accessmaze.models import Step


def apply_conditions(journey):
    expanded = journey.model_copy(deep=True)
    steps = []
    reserved = {"profile-offline", "profile-online", "profile-focus", "profile-audit"}
    if any(s.id in reserved for s in journey.steps):
        raise ValueError("Step IDs beginning profile- are reserved for profile checks")
    for step in journey.steps:
        steps.append(step)
        if step.id == journey.profile.disconnect_after_step:
            steps.append(Step(id="profile-offline", action="offline"))
        if step.id == journey.profile.reconnect_after_step:
            steps.append(Step(id="profile-online", action="online"))
    if journey.profile.focus_target:
        steps.append(
            Step(id="profile-focus", action="assert_focus", target=journey.profile.focus_target)
        )
    if journey.profile.audit_semantics:
        steps.append(Step(id="profile-audit", action="audit"))
    expanded.steps = steps
    return expanded
