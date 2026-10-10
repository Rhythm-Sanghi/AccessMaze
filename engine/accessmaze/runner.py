import asyncio
import copy
import importlib.metadata
import platform
import threading
import time
from pathlib import Path
from uuid import uuid4

import networkx as nx
from playwright.async_api import Error as BrowserError
from playwright.async_api import async_playwright

from accessmaze.actions import CheckFailure, cancellable, perform
from accessmaze.classification import classify_failure
from accessmaze.evidence import EvidencePrivacy, fingerprint, public_journey, redact
from accessmaze.exploration import explore
from accessmaze.inputs import RunInputs
from accessmaze.network import BrowserPolicy, resolve_host
from accessmaze.outcomes import task_outcome
from accessmaze.profiles import apply_conditions
from accessmaze.reachability import analyze_reachability
from accessmaze.replay import replay_recipe, replay_verdict
from accessmaze.state_identity import annotate_states
from accessmaze.storage import now
from accessmaze.website_exploration import explore_website


class RunControl:
    def __init__(self):
        self.cancel = threading.Event()
        self.pause = threading.Event()
        self.approval_lock = threading.Lock()
        self.proposal = None
        self.decision = None

    def offer(self, proposal):
        with self.approval_lock:
            self.proposal = copy.deepcopy(proposal)
            self.decision = None

    def pending(self):
        with self.approval_lock:
            return copy.deepcopy(self.proposal)

    def approve(self, proposal_id, choice_id):
        with self.approval_lock:
            if not self.proposal or self.proposal["id"] != proposal_id or self.decision:
                raise ValueError("This approval is stale or already answered")
            if choice_id != "stop" and choice_id not in {c["id"] for c in self.proposal["choices"]}:
                raise ValueError("Unknown proposed action")
            self.decision = choice_id

    def consume(self):
        with self.approval_lock:
            if self.decision is None:
                return None
            answer = self.decision
            self.proposal = None
            self.decision = None
            return answer

    def clear_approval(self):
        with self.approval_lock:
            self.proposal = None
            self.decision = None


def check_host(url, allow_local):
    resolve_host(url, allow_local)


async def execute(
    store,
    project_id,
    journey,
    control,
    fixtures,
    axe_path: Path,
    run_id=None,
    inputs=None,
    input_key=None,
    on_ready=None,
    replay=None,
):
    journey = apply_conditions(journey)
    run_id = run_id or str(uuid4())
    inputs = inputs or RunInputs(journey, key=input_key)
    secrets = [
        s.value for s in journey.steps if s.action in {"fill", "assert_value"}
    ] + inputs.secrets
    privacy = EvidencePrivacy(journey, secrets)
    result = {
        "id": run_id,
        "project_id": project_id,
        "status": "preparing",
        "started_at": now(),
        "journey": public_journey(journey),
        "input_signature": inputs.signature,
        "steps": [],
        "findings": [],
        "nodes": [],
        "edges": [],
        "environment": {
            "engine": "0.1.0",
        },
        "limitations": [
            "Bounded fixture button discovery; unvisited branches are not covered."
            if journey.exploration.enabled and journey.target.startswith("fixture://")
            else "Website exploration requires approval for each action; "
            "unvisited branches are not covered."
            if journey.exploration.enabled
            else "Authored path only; unvisited branches are not covered.",
            "Keyboard reachability uses a finite Tab budget; failure is bounded to this attempt.",
            "DOM semantics do not establish assistive technology behavior or WCAG conformance.",
            "Motion and viewport preferences are applied; usability requires human review.",
            "Only approved origins are allowed; blocked traffic can change behavior.",
            "Screenshots are captured only for bundled synthetic fixtures.",
        ],
    }
    if replay:
        result["replay"] = replay
    graph = nx.MultiDiGraph()
    previous = None
    started = time.monotonic()
    url = (
        fixtures.url(journey.target) if journey.target.startswith("fixture://") else journey.target
    )
    blocked = set()

    def save():
        for finding in result["findings"]:
            finding["classification"] = classify_failure(
                finding["rule"], blocked=bool(blocked), verification=finding["verification"]
            )
            finding["replay_recipe"] = replay_recipe(result, finding)
        result["outcome"] = task_outcome(result)
        annotate_states(graph)
        result["nodes"] = [{"id": node, **data} for node, data in graph.nodes(data=True)]
        result["edges"] = [
            {"source": a, "target": b, **data} for a, b, data in graph.edges(data=True)
        ]
        result["reachability"] = analyze_reachability(result)
        store.save_run(redact(result, secrets))

    save()
    if on_ready:
        on_ready()
    try:
        if control.cancel.is_set():
            raise asyncio.CancelledError
        # OS inspection can be slow on a cold Windows launch. The UI must already
        # have a persisted preparing record and be able to poll/cancel this run.
        result["environment"].update(
            playwright=importlib.metadata.version("playwright"),
            python=platform.python_version(),
            os=platform.platform(),
            networkx=importlib.metadata.version("networkx"),
        )
        if control.cancel.is_set():
            raise asyncio.CancelledError
        if time.monotonic() - started >= journey.max_seconds:
            raise TimeoutError
        policy = BrowserPolicy(journey, url, blocked)
        await cancellable(policy.prepare(), control)
        async with async_playwright() as pw:
            browser = await cancellable(
                pw.chromium.launch(
                    headless=True,
                    args=policy.launch_args,
                    timeout=min(30000, journey.max_seconds * 1000),
                ),
                control,
            )
            result["environment"]["browser"] = browser.version
            try:
                context = await browser.new_context(
                    viewport={
                        "width": round(
                            journey.profile.viewport_width
                            * 100
                            / journey.profile.layout_zoom_percent
                        ),
                        "height": round(
                            journey.profile.viewport_height
                            * 100
                            / journey.profile.layout_zoom_percent
                        ),
                    },
                    device_scale_factor=journey.profile.layout_zoom_percent / 100,
                    reduced_motion="reduce" if journey.profile.reduced_motion else "no-preference",
                    service_workers="block",
                    accept_downloads=False,
                )
                if journey.profile.layout_zoom_percent != 100:
                    result["limitations"].append(
                        "Layout zoom emulation changes CSS viewport and device scale; "
                        "it does not operate browser chrome zoom or verify OS magnification."
                    )
                if journey.network.embedded_frames:
                    result["limitations"].append(
                        "Embedded frame network navigation is allowed only at "
                        "approved navigation origins. "
                        "Authored named-frame targets are supported; automatic frame discovery, "
                        "srcdoc targets and complete cross-frame focus/AX verification are not."
                    )
                result["limitations"].append(
                    "Popups, WebSockets, service workers and downloads remain unsupported. "
                    "Browser automation is not a strong isolation boundary for hostile websites."
                )
                context.set_default_timeout(journey.profile.action_timeout_ms)
                context.set_default_navigation_timeout(min(30000, journey.max_seconds * 1000))
                context._accessmaze_inputs = inputs
                if inputs.files:
                    result["limitations"].append(
                        "Programmatic upload; native file-picker accessibility is untested."
                    )

                await policy.install(context)
                page = await context.new_page()
                await policy.attach(page)
                # Every popup receives the same context restrictions; no inherited browser profile.
                result["status"] = "running"
                save()
                async with asyncio.timeout(
                    max(0, journey.max_seconds - (time.monotonic() - started))
                ):
                    for index, step in enumerate(journey.steps):
                        while control.pause.is_set() and not control.cancel.is_set():
                            result["status"] = "paused"
                            save()
                            await asyncio.sleep(0.1)
                        if control.cancel.is_set():
                            raise asyncio.CancelledError
                        result["status"] = "running"
                        entry = {
                            "id": step.id,
                            "action": step.action,
                            "status": "running",
                            "timestamp": now(),
                            "index": index,
                        }
                        result["steps"].append(entry)
                        save()
                        failure = None
                        task = asyncio.create_task(
                            perform(page, context, step, journey, url, axe_path)
                        )
                        try:
                            while not task.done():
                                if control.cancel.is_set():
                                    task.cancel()
                                    raise asyncio.CancelledError
                                await asyncio.sleep(0.05)
                            audit = await task
                            entry["status"] = "passed"
                            if audit is not None:
                                if privacy.hide_text:
                                    for violation in audit["violations"]:
                                        violation["targets"] = [
                                            privacy.token(str(t)) for t in violation["targets"]
                                        ]
                                entry["audit"] = audit
                                for violation in audit["violations"]:
                                    result["findings"].append(
                                        {
                                            "id": str(uuid4()),
                                            "step_id": step.id,
                                            "rule": violation["id"],
                                            "title": violation["description"],
                                            "severity": violation["impact"] or "moderate",
                                            "verification": "inconclusive"
                                            if blocked
                                            else "confirmed-automated",
                                            "actual": violation,
                                            "expected": "axe-core rule passes",
                                            "timestamp": now(),
                                            "reproduction": [
                                                s.id for s in journey.steps[: index + 1]
                                            ],
                                            "remediation": violation["helpUrl"],
                                        }
                                    )
                                if audit["incomplete"]:
                                    result["limitations"].append(
                                        "axe-core returned checks needing human review"
                                    )
                        except CheckFailure as exc:
                            failure = exc
                        except BrowserError:
                            failure = CheckFailure(
                                "browser-action",
                                "Browser interaction failed or timed out",
                                "Target action completes within the configured timeout",
                            )
                        finally:
                            if not task.done():
                                task.cancel()
                                await asyncio.gather(task, return_exceptions=True)
                        if failure:
                            entry["status"] = "skipped" if step.optional else "failed"
                            finding = {
                                "id": str(uuid4()),
                                "step_id": step.id,
                                "rule": failure.code,
                                "target_identity": step.target.model_dump()
                                if step.target
                                else None,
                                "title": failure.actual,
                                "severity": "moderate" if step.optional else "serious",
                                "verification": "inconclusive"
                                if blocked
                                or failure.code
                                in {
                                    "browser-action",
                                    "target-ambiguous",
                                    "audit-unavailable",
                                    "sensitive-field",
                                    "navigation-http",
                                    "target-disabled",
                                    "frame-unavailable",
                                    "native-validation-unverified",
                                    "error-discoverability-unverified",
                                }
                                else "confirmed-automated",
                                "actual": failure.actual,
                                "expected": failure.expected,
                                "timestamp": now(),
                                "reproduction": [s.id for s in journey.steps[: index + 1]],
                                "remediation": "Inspect the step and target; rerun after repair.",
                            }
                            if journey.target.startswith("fixture://"):
                                filename = f"step-{index}.png"
                                try:
                                    await page.screenshot(
                                        path=store.artifact_dir(run_id) / filename,
                                        mask=[page.locator("input,textarea,[contenteditable]")],
                                    )
                                    finding["screenshot"] = filename
                                except BrowserError:
                                    result["limitations"].append("Screenshot capture failed")
                            result["findings"].append(finding)
                        interaction = getattr(context, "_accessmaze_interaction", {})
                        if interaction:
                            entry["interaction"] = privacy.interaction(interaction)
                            if (
                                interaction.get("limitation")
                                and interaction["limitation"] not in result["limitations"]
                            ):
                                result["limitations"].append(interaction["limitation"])
                        observation = await privacy.observe(page)
                        state_id = fingerprint(observation)
                        if state_id not in graph:
                            graph.add_node(state_id, observation=observation, first_step=step.id)
                        if previous is not None:
                            graph.add_edge(
                                previous,
                                state_id,
                                step_id=step.id,
                                status=entry["status"],
                                cycle=nx.has_path(graph, state_id, previous),
                            )
                        previous = state_id
                        entry["state_id"] = state_id
                        save()
                        if failure and not step.optional:
                            result["status"] = "failed"
                            break
                    else:
                        if journey.exploration.enabled:
                            if not journey.target.startswith("fixture://"):
                                await explore_website(
                                    page,
                                    context,
                                    journey,
                                    url,
                                    axe_path,
                                    graph,
                                    previous,
                                    result,
                                    control,
                                    save,
                                    privacy,
                                )
                            else:
                                result["limitations"].append(
                                    "Discovery is limited to named buttons on resettable fixtures."
                                )
                                await explore(
                                    page,
                                    context,
                                    journey,
                                    url,
                                    axe_path,
                                    graph,
                                    previous,
                                    result,
                                    control,
                                    save,
                                )
                        result["status"] = "completed_with_limitations"
            finally:
                await browser.close()
    except asyncio.CancelledError:
        result["status"] = "cancelled"
    except TimeoutError:
        if result.get("exploration"):
            result["exploration"]["stop_reason"] = "time-budget"
        result.update(status="failed", error="Configured execution time budget exceeded")
        result["failure"] = {
            "classification": "exploration-budget-exhaustion",
            "reason": result["error"],
        }
    except (BrowserError, ValueError, OSError) as exc:
        result.update(
            status="failed",
            error=f"{type(exc).__name__}: browser preparation or observation failed",
        )
        result["failure"] = {
            "classification": "browser-environment-limitation",
            "reason": result["error"],
        }
    finally:
        if result["steps"] and result["steps"][-1]["status"] == "running":
            result["steps"][-1]["status"] = "interrupted"
        result["limitations"].extend(sorted(blocked))
        result["coverage_compromised"] = bool(blocked)
        if blocked:
            for finding in result["findings"]:
                finding["verification"] = "inconclusive"
        if replay:
            result["replay"]["verdict"] = replay_verdict(
                store.run(replay["source_id"]), result, replay["finding_id"]
            )
        result["finished_at"] = now()
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        save()
    return store.run(run_id)
