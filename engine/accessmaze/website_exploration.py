"""A bounded, approved walk through a website. Never reset/replay external effects."""

import asyncio
from uuid import uuid4

import networkx as nx
from playwright.async_api import Error as BrowserError

from accessmaze.actions import CheckFailure, perform
from accessmaze.evidence import accessibility_tree, fingerprint
from accessmaze.models import Step
from accessmaze.storage import now


async def explore_website(
    page, context, journey, url, axe_path, graph, source, result, control, save, privacy
):
    progress = {
        "actions": [],
        "discovered_states": len(graph),
        "pending_branches": [],
        "stop_reason": "running",
        "mode": "approved-walk",
    }
    result["exploration"] = progress
    result["limitations"].append(
        "Website exploration follows one approved path; no resets or automatic effect replay."
    )
    visited = {source}
    try:
        for depth in range(min(journey.exploration.max_depth, journey.exploration.max_actions)):
            if control.cancel.is_set():
                raise asyncio.CancelledError
            choices = []
            seen = set()
            for node in (await accessibility_tree(page))["nodes"]:
                role, name = node["role"], node["name"]
                if role not in {"button", "link"} or not name or (role, name) in seen:
                    continue
                seen.add((role, name))
                locator = page.get_by_role(role, name=name, exact=True)
                if (
                    await locator.count() != 1
                    or not await locator.is_visible()
                    or not await locator.is_enabled()
                ):
                    continue
                choices.append({"id": str(uuid4()), "role": role, "name": name})
                if len(choices) >= 30:
                    break
            if not choices:
                progress["stop_reason"] = "no-supported-actions"
                break
            # Observation and permission are tied to this exact bounded state.
            observation = await privacy.observe(page)
            current = fingerprint(observation)
            if current != source:
                source = current
                graph.add_node(source, observation=observation, first_step="exploration-observed")
            proposal = {"id": str(uuid4()), "state_id": source, "choices": choices}
            control.offer(proposal)
            result["approval"] = {
                **proposal,
                "choices": [
                    {
                        **choice,
                        "name": privacy.token(choice["name"])
                        if privacy.hide_text
                        else choice["name"],
                    }
                    for choice in choices
                ],
            }
            progress["pending_branches"] = [
                {"state_id": source, "path": [choice["name"]], "reason": "approval-required"}
                for choice in result["approval"]["choices"]
            ]
            result["status"] = "awaiting_approval"
            save()
            answer = None
            while answer is None:
                if control.cancel.is_set():
                    raise asyncio.CancelledError
                if not control.pause.is_set():
                    answer = control.consume()
                await asyncio.sleep(0.05)
            if answer == "stop":
                progress["stop_reason"] = "user-stopped"
                break
            if fingerprint(await privacy.observe(page)) != source:
                progress["stop_reason"] = "state-changed-before-action"
                result["limitations"].append("State changed after approval; action refused")
                break
            selected = next(c for c in choices if c["id"] == answer)
            step = Step(
                id=f"explore-{depth + 1}",
                action="activate",
                effect=True,
                target={"role": selected["role"], "name": selected["name"]},
            )
            result["status"] = "running"
            entry = {
                "step_id": step.id,
                "kind": "approved-explore",
                "action": "activate",
                "target": {
                    **step.target.model_dump(),
                    "name": privacy.token(selected["name"])
                    if privacy.hide_text
                    else selected["name"],
                },
                "timestamp": now(),
                "status": "running",
                "approval_id": proposal["id"],
            }
            progress["actions"].append(entry)
            save()
            failure = None
            try:
                from accessmaze.actions import cancellable

                await cancellable(perform(page, context, step, journey, url, axe_path), control)
                entry["status"] = "passed"
            except (CheckFailure, BrowserError) as error:
                failure = (
                    error
                    if isinstance(error, CheckFailure)
                    else CheckFailure(
                        "browser-action",
                        "Approved interaction failed or timed out",
                        "Action completes",
                    )
                )
                entry["status"] = "failed"
            observation = await privacy.observe(page)
            target = fingerprint(observation)
            if target not in graph:
                graph.add_node(target, observation=observation, first_step=step.id)
            graph.add_edge(
                source,
                target,
                step_id=step.id,
                status=entry["status"],
                cycle=nx.has_path(graph, target, source),
            )
            progress["discovered_states"] = len(graph)
            progress["pending_branches"] = [
                {"state_id": source, "path": [choice["name"]], "reason": "unvisited-alternative"}
                for choice in result["approval"]["choices"]
                if choice["id"] != answer
            ]
            save()
            if failure:
                result["findings"].append(
                    {
                        "id": str(uuid4()),
                        "step_id": step.id,
                        "rule": failure.code,
                        "title": failure.actual,
                        "actual": failure.actual,
                        "expected": failure.expected,
                        "severity": "moderate",
                        "verification": "confirmed-automated"
                        if failure.code == "keyboard-unreachable"
                        else "inconclusive",
                        "timestamp": now(),
                        "reproduction": [
                            *[s.id for s in journey.steps],
                            *[a["target"]["name"] for a in progress["actions"]],
                        ],
                        "remediation": "Inspect the approved target and its keyboard behavior.",
                    }
                )
                progress["stop_reason"] = "action-failed"
                result["limitations"].append(
                    "Approved exploration action failed; no subsequent path was tested"
                )
                break
            if target in visited:
                progress["stop_reason"] = "observed-cycle"
                break
            visited.add(target)
            source = target
        else:
            progress["stop_reason"] = (
                "depth-bound"
                if journey.exploration.max_depth <= journey.exploration.max_actions
                else "action-budget"
            )
    finally:
        control.clear_approval()
        result.pop("approval", None)
        if progress["stop_reason"] == "running":
            progress["stop_reason"] = "interrupted"
        if progress["actions"] and progress["actions"][-1]["status"] == "running":
            progress["actions"][-1]["status"] = "interrupted"
        save()
