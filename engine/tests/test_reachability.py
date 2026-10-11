from accessmaze.reachability import analyze_reachability


def test_alternative_observed_paths_are_bounded_and_do_not_clear_unknown_frontier():
    run = {
        "status": "completed_with_limitations",
        "journey": {"steps": [{"id": "done", "action": "assert_visible"}]},
        "steps": [
            {"id": "open", "state_id": "a", "status": "passed"},
            {"id": "done", "state_id": "d", "status": "passed"},
        ],
        "findings": [],
        "nodes": [{"id": s} for s in "abcd"],
        "edges": [
            {"source": "a", "target": "b", "step_id": "first", "status": "passed"},
            {"source": "a", "target": "c", "step_id": "alternative", "status": "passed"},
            {"source": "b", "target": "d", "step_id": "done", "status": "passed"},
            {"source": "c", "target": "d", "step_id": "done", "status": "passed"},
            {"source": "d", "target": "a", "step_id": "restart", "status": "passed"},
        ],
        "exploration": {"pending_branches": [{"state_id": "c", "reason": "approval-required"}]},
    }
    evidence = analyze_reachability(run)
    objective = evidence["objectives"][0]
    assert objective["status"] == "observed-success"
    assert objective["alternative_observed_state_paths"] == [
        ["alternative", "done"],
        ["first", "done"],
    ]
    assert evidence["unexplored_frontier"] == run["exploration"]["pending_branches"]
    assert evidence["path_search"]["inspected_edges"] <= 1000
    run["steps"][-1]["status"] = "interrupted"
    assert analyze_reachability(run)["status"] == "unknown"
    assert analyze_reachability(run)["objectives"][0]["status"] == "unknown"
