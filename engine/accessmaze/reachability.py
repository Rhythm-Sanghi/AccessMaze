"""Describe witnessed graph reachability without inferring exhaustive task coverage."""

from collections import deque

from accessmaze.outcomes import task_outcome


def analyze_reachability(run):
    nodes = {n["id"] for n in run.get("nodes", [])}
    steps = run.get("steps", [])
    root = next((s["state_id"] for s in steps if s.get("state_id") in nodes), None)
    adjacency = {}
    for edge in run.get("edges", []):
        if edge["status"] == "passed" and edge["source"] in nodes and edge["target"] in nodes:
            adjacency.setdefault(edge["source"], []).append(edge)
    paths = {root: []} if root else {}
    queue = deque([root] if root else [])
    while queue:
        source = queue.popleft()
        for edge in sorted(adjacency.get(source, []), key=lambda e: (e["step_id"], e["target"])):
            if edge["target"] not in paths:
                paths[edge["target"]] = [*paths[source], edge["step_id"]]
                queue.append(edge["target"])
    recorded = {s["id"]: s for s in steps}
    alternatives = {}
    pending_paths = deque([(root, [root], [])] if root else [])
    inspected_edges = 0
    while pending_paths and inspected_edges < 1000:
        source, visited, path = pending_paths.popleft()
        for edge in sorted(adjacency.get(source, []), key=lambda e: (e["step_id"], e["target"])):
            inspected_edges += 1
            target = edge["target"]
            candidate = [*path, edge["step_id"]]
            known = alternatives.setdefault(target, [])
            if target not in visited and candidate not in known and len(known) < 3:
                known.append(candidate)
                pending_paths.append((target, [*visited, target], candidate))
            if inspected_edges >= 1000:
                break
    objectives = []
    for step in run.get("journey", {}).get("steps", []):
        if step["action"].startswith("assert_") and not step.get("optional"):
            entry = recorded.get(step["id"], {})
            state = entry.get("state_id")
            witnessed = entry.get("status") == "passed" and state in paths
            objectives.append(
                {
                    "step_id": step["id"],
                    "status": "observed-success" if witnessed else "unknown",
                    "state_id": state,
                    "shortest_observed_state_path": paths.get(state) if witnessed else None,
                    "alternative_observed_state_paths": alternatives.get(state, [])
                    if witnessed
                    else [],
                }
            )
    attempts = [
        *steps,
        *[{"id": a["step_id"], **a} for a in run.get("exploration", {}).get("actions", [])],
    ]
    blockers = [
        {
            "step_id": a["id"],
            "source": a.get("source"),
            "state_id": a.get("state_id"),
            "finding_ids": [f["id"] for f in run.get("findings", []) if f["step_id"] == a["id"]],
            "chronological_prerequisites": [p["id"] for p in attempts[:index]],
        }
        for index, a in enumerate(attempts)
        if a["status"] == "failed"
    ]
    outcome = task_outcome(run)
    status = (
        "observed-success"
        if outcome["status"] == "completed"
        else "observed-failure"
        if outcome["status"] == "blocked"
        else "unknown"
    )
    frontier = run.get("exploration", {}).get("pending_branches", [])
    return {
        "schema_version": 1,
        "status": status,
        "root_state_id": root,
        "objectives": objectives,
        "blocking_attempts": blockers,
        "reachable_observed_states": len(paths),
        "observed_states": len(nodes),
        "unexplored_frontier": frontier,
        "path_search": {
            "max_alternatives_per_state": 3,
            "max_edges": 1000,
            "inspected_edges": inspected_edges,
            "exhausted": bool(pending_paths),
        },
        "limitation": "Shortest paths describe observed state edges, not a safe replay recipe: "
        "hidden values and server prerequisites may differ. Unvisited branches are unknown; "
        "bounded attempts do not prove global unreachability.",
    }
