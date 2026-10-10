"""Bounded semantic discovery. Every activation and root recovery needs fresh approval."""

import asyncio
import copy
from uuid import uuid4

import networkx as nx
from playwright.async_api import Error as BrowserError

from accessmaze.actions import CheckFailure, cancellable, perform
from accessmaze.evidence import accessibility_tree, fingerprint
from accessmaze.models import Step
from accessmaze.storage import now


def state_key(observation):
    """Ignore transient focus for coverage deduplication, but retain it in evidence."""
    stable = copy.deepcopy(observation)
    for control in stable.get("controls", []):
        control.pop("focused", None)
    for node in stable.get("ax_tree", {}).get("nodes", []):
        node.pop("focused", None)
    return fingerprint(stable)


async def candidates(page):
    # Computed accessible names handle aria-labelledby and native labelled controls.
    names = sorted(
        {
            (node["role"], node["name"])
            for node in (await accessibility_tree(page))["nodes"]
            if node["role"] in {"button", "link", "checkbox", "radio"} and node["name"]
        }
    )
    choices = []
    for role, name in names[:100]:
        locator = page.get_by_role(role, name=name, exact=True)
        if await locator.count() == 1 and await locator.is_visible() and await locator.is_enabled():
            choices.append(
                {
                    "id": str(uuid4()),
                    "role": role,
                    "name": name,
                    "classification": "potentially-consequential",
                }
            )
        if len(choices) == 30:
            break
    return choices


async def explore_website(
    page, context, journey, url, axe_path, graph, source, result, control, save, privacy
):
    progress = {
        "actions": [],
        "discovered_states": len(graph),
        "pending_branches": [],
        "stop_reason": "running",
        "mode": "approved-branches",
        "reachability": [],
    }
    result["exploration"] = progress
    result["limitations"].append(
        "Semantic discovery is capped at 500 AX nodes / depth 8 "
        "and 30 unique enabled actions per state. "
        "Every activation and optional root navigation requires approval. Root recovery does not "
        "undo server effects, restore application data, or replay form inputs. "
        "Unattempted actions and exhausted budgets do not establish inaccessibility."
    )
    attempted = set()
    frontier = {}
    root = None
    depth = 0
    try:
        while len(progress["actions"]) < journey.exploration.max_actions:
            if control.cancel.is_set():
                raise asyncio.CancelledError
            observation = await privacy.observe(page)
            source = fingerprint(observation)
            normalized = state_key(observation)
            root = root or normalized
            if source not in graph:
                graph.add_node(source, observation=observation, first_step="exploration-observed")
            all_choices = await candidates(page)
            choices = []
            for choice in all_choices:
                key = (normalized, choice["role"], choice["name"])
                if key in attempted:
                    continue
                private_name = (
                    privacy.token(choice["name"]) if privacy.hide_text else choice["name"]
                )
                frontier[key] = {
                    "state_id": source,
                    "normalized_state_id": normalized,
                    "path": [private_name],
                    "reason": "approval-required"
                    if depth < journey.exploration.max_depth
                    else "depth-bound",
                }
                if depth < journey.exploration.max_depth:
                    choices.append(choice)
            # Recovery navigates only to the original configured URL, with no automatic replay.
            # It is separately approved even though GET is normally considered read-only.
            if journey.exploration.recover_navigation and normalized != root:
                choices.append(
                    {
                        "id": str(uuid4()),
                        "role": "navigation",
                        "name": "Return to configured start",
                        "classification": "navigation-may-change-state",
                    }
                )
            progress["pending_branches"] = list(frontier.values())
            progress["discovered_states"] = len(graph)
            if not choices:
                progress["stop_reason"] = (
                    "depth-bound"
                    if depth >= journey.exploration.max_depth
                    else "no-unattempted-actions"
                )
                break
            proposal = {"id": str(uuid4()), "state_id": source, "choices": choices}
            control.offer(proposal)
            result["approval"] = {
                **proposal,
                "choices": [
                    {**c, "name": privacy.token(c["name"]) if privacy.hide_text else c["name"]}
                    for c in choices
                ],
            }
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
            recovery = selected["role"] == "navigation"
            key = (normalized, selected["role"], selected["name"])
            if not recovery:
                attempted.add(key)
                frontier.pop(key, None)
            step = Step(
                id=f"explore-{len(progress['actions']) + 1}",
                action="navigate" if recovery else "activate",
                effect=True,
                target=None if recovery else {"role": selected["role"], "name": selected["name"]},
            )
            entry = {
                "step_id": step.id,
                "kind": "approved-recovery" if recovery else "approved-explore",
                "action": step.action,
                "target": None
                if recovery
                else {
                    **step.target.model_dump(),
                    "name": privacy.token(selected["name"])
                    if privacy.hide_text
                    else selected["name"],
                },
                "source": source,
                "timestamp": now(),
                "status": "running",
                "approval_id": proposal["id"],
            }
            progress["actions"].append(entry)
            progress["pending_branches"] = list(frontier.values())
            result["status"] = "running"
            save()
            failure = None
            try:
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
            interaction = privacy.interaction(getattr(context, "_accessmaze_interaction", {}))
            entry["interaction"] = interaction
            entry["reachability"] = (
                "not-tested-pointer"
                if not journey.profile.keyboard_only
                else (
                    "bounded-failure"
                    if failure and failure.code == "keyboard-unreachable"
                    else "reached"
                    if not recovery and not failure
                    else "inconclusive"
                )
            )
            observation = await privacy.observe(page)
            target = fingerprint(observation)
            entry["state_id"] = target
            if target not in graph:
                graph.add_node(target, observation=observation, first_step=step.id)
            graph.add_edge(
                source,
                target,
                step_id=step.id,
                status=entry["status"],
                cycle=nx.has_path(graph, target, source),
            )
            progress["reachability"].append(
                {
                    "step_id": step.id,
                    "source": source,
                    "target": target,
                    "status": entry["reachability"],
                }
            )
            progress["discovered_states"] = len(graph)
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
                            *[a["step_id"] for a in progress["actions"]],
                        ],
                        "remediation": "Inspect the approved target and its keyboard behavior.",
                    }
                )
                # The failed branch remains explicitly observed; never automatically retry it.
                progress["stop_reason"] = "action-failed"
                save()
                break
            depth = 0 if recovery else depth + 1
            save()
        else:
            progress["stop_reason"] = "action-budget"
            # Capture the final state's untested candidates even when no further action is allowed.
            observation = await privacy.observe(page)
            for choice in await candidates(page):
                key = (state_key(observation), choice["role"], choice["name"])
                if key not in attempted:
                    frontier[key] = {
                        "state_id": fingerprint(observation),
                        "path": [
                            privacy.token(choice["name"]) if privacy.hide_text else choice["name"]
                        ],
                        "reason": "action-budget",
                    }
            progress["pending_branches"] = list(frontier.values())
    finally:
        control.clear_approval()
        result.pop("approval", None)
        if progress["stop_reason"] == "running":
            progress["stop_reason"] = "interrupted"
        if progress["actions"] and progress["actions"][-1]["status"] == "running":
            progress["actions"][-1]["status"] = "interrupted"
        save()
