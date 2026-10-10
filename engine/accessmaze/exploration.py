"""Bounded branch discovery for resettable synthetic fixtures; never arbitrary websites."""

import asyncio
from collections import deque
from uuid import uuid4

import networkx as nx
from playwright.async_api import Error as BrowserError

from accessmaze.actions import CheckFailure, perform
from accessmaze.evidence import fingerprint, observe, redact
from accessmaze.models import Step
from accessmaze.storage import now


async def explore(page, context, journey, url, axe_path, graph, root, result, control, save):
    config = journey.exploration
    progress = {
        "actions": [],
        "discovered_states": 1,
        "pending_branches": [],
        "stop_reason": "running",
    }
    result["exploration"] = progress
    queue = deque([(root, [])])
    expanded = set()
    secrets = [s.value for s in journey.steps if s.action in {"fill", "assert_value"}]
    depth_stops = []
    unfinished = []

    async def action(step, kind):
        while control.pause.is_set() and not control.cancel.is_set():
            result["status"] = "paused"
            save()
            await asyncio.sleep(0.1)
        if control.cancel.is_set():
            raise asyncio.CancelledError
        result["status"] = "running"
        if len(progress["actions"]) >= config.max_actions:
            return False
        entry = {
            "step_id": step.id,
            "kind": kind,
            "action": step.action,
            "target": step.target.model_dump() if step.target else None,
            "timestamp": now(),
            "status": "running",
        }
        progress["actions"].append(entry)
        save()
        task = asyncio.create_task(perform(page, context, step, journey, url, axe_path))
        try:
            while not task.done():
                if control.cancel.is_set():
                    raise asyncio.CancelledError
                await asyncio.sleep(0.05)
            await task
            entry["status"] = "passed"
            return True
        except (CheckFailure, BrowserError):
            entry["status"] = "failed"
            raise
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                entry["status"] = "interrupted"
            save()

    async def restore(path):
        for step in [*journey.steps, *path]:
            if not await action(step, "replay"):
                return False
        return True

    try:
        while queue:
            source, path = queue.popleft()
            if source in expanded:
                continue
            if len(path) >= config.max_depth:
                depth_stops.append({"state_id": source, "path": [s.target.name for s in path]})
                continue
            if not await restore(path):
                queue.appendleft((source, path))
                progress["stop_reason"] = "action-budget"
                break
            candidates = await page.evaluate("""() =>
              [...document.querySelectorAll('button,[role=button]')]
              .filter(e=>e.getClientRects().length && !e.matches(':disabled'))
              .map(e=>(e.getAttribute('aria-label')||e.textContent||'').trim())
              .filter(n=>n && n.length<=200).sort().slice(0,30)""")
            expanded.add(source)
            for index, name in enumerate(sorted(set(candidates))):
                if index and not await restore(path):
                    unfinished.extend(
                        {
                            "state_id": source,
                            "path": [*[s.target.name for s in path], n],
                            "reason": "action-budget",
                        }
                        for n in candidates[index:]
                    )
                    progress["stop_reason"] = "action-budget"
                    break
                before = redact(await observe(page), secrets)
                if fingerprint(before) != source:
                    result["limitations"].append("Exploration replay diverged; branch skipped")
                    continue
                step = Step(
                    id=f"explore-{len(progress['actions']) + 1}",
                    action="activate",
                    effect=True,
                    target={"role": "button", "name": name},
                )
                failure = None
                try:
                    if not await action(step, "explore"):
                        unfinished.extend(
                            {
                                "state_id": source,
                                "path": [*[s.target.name for s in path], n],
                                "reason": "action-budget",
                            }
                            for n in candidates[index:]
                        )
                        progress["stop_reason"] = "action-budget"
                        break
                except CheckFailure as exc:
                    failure = exc
                except BrowserError:
                    failure = CheckFailure(
                        "exploration-action",
                        "Branch interaction timed out",
                        "Branch interaction completes",
                    )
                observation = redact(await observe(page), secrets)
                target = fingerprint(observation)
                if target not in graph:
                    graph.add_node(target, observation=observation, first_step=step.id)
                graph.add_edge(
                    source,
                    target,
                    step_id=step.id,
                    status="failed" if failure else "passed",
                    cycle=nx.has_path(graph, target, source),
                )
                if failure:
                    result["findings"].append(
                        {
                            "id": str(uuid4()),
                            "step_id": step.id,
                            "rule": failure.code,
                            "title": failure.actual,
                            "severity": "moderate",
                            "verification": "confirmed-automated"
                            if failure.code == "keyboard-unreachable"
                            else "inconclusive",
                            "timestamp": now(),
                            "actual": failure.actual,
                            "expected": failure.expected,
                            "reproduction": [
                                *[s.id for s in journey.steps],
                                *[f"Activate button: {s.target.name}" for s in path],
                                f"Activate button: {name}",
                            ],
                            "remediation": "Inspect the branch target and its keyboard behavior.",
                        }
                    )
                elif target not in expanded and target not in {item[0] for item in queue}:
                    queue.append((target, [*path, step]))
                progress["discovered_states"] = len(graph)
                save()
            if progress["stop_reason"] != "running":
                break
        else:
            progress["stop_reason"] = "depth-bound" if depth_stops else "frontier-exhausted"
    finally:
        progress["pending_branches"] = (
            [{"state_id": state, "path": [s.target.name for s in path]} for state, path in queue]
            + depth_stops
            + unfinished
        )
        if progress["stop_reason"] == "running":
            progress["stop_reason"] = "interrupted"
        save()
