"""Focus belongs to interaction evidence; coverage identity ignores only focus flags."""

import copy

from accessmaze.evidence import fingerprint


def navigation_state_id(observation):
    stable = copy.deepcopy(observation)
    for control in stable.get("controls", []):
        control.pop("focused", None)
    for node in stable.get("ax_tree", {}).get("nodes", []):
        node.pop("focused", None)
    return fingerprint(stable)


def annotate_states(graph):
    for state_id, data in graph.nodes(data=True):
        if "navigation_state_id" not in data:
            data["navigation_state_id"] = navigation_state_id(data["observation"])
            data["interaction_state_id"] = state_id
