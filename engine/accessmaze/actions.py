import asyncio

from playwright.async_api import Error as BrowserError

from accessmaze.network import canonical_origin


async def cancellable(coroutine, control):
    task = asyncio.create_task(coroutine)
    try:
        while not task.done():
            if control.cancel.is_set():
                raise asyncio.CancelledError
            await asyncio.sleep(0.05)
        return await task
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


class CheckFailure(Exception):
    def __init__(self, code, actual, expected):
        self.code, self.actual, self.expected = code, actual, expected
        super().__init__(actual)


async def keyboard_reach(page, locator, budget):
    if await locator.count() != 1:
        raise CheckFailure(
            "target-ambiguous",
            "Target is absent or has multiple matches",
            "Exactly one visible semantic target",
        )
    for _ in range(budget + 1):
        if await locator.evaluate("e => e === document.activeElement"):
            return
        await page.keyboard.press("Tab")
    raise CheckFailure(
        "keyboard-unreachable",
        f"Target not reached within {budget} Tab presses",
        "Target reachable through sequential keyboard navigation",
    )


async def perform(page, context, step, journey, url, axe_path):
    policy = getattr(context, "_accessmaze_policy", None)
    if policy:
        policy.effects = step.effect
    try:
        result = await _perform(page, context, step, journey, url, axe_path)
        if policy and step.effect:
            # Allow requests scheduled by the DOM event to reach interception before
            # closing this action's permission window. This grace is bounded.
            await asyncio.sleep(0.25)
        return result
    finally:
        if policy:
            policy.effects = False


async def _perform(page, context, step, journey, url, axe_path):
    inputs = getattr(context, "_accessmaze_inputs", None)
    value = inputs.value(step) if inputs and step.action in {"fill", "assert_value"} else step.value
    policy = getattr(context, "_accessmaze_policy", None)
    secure_input = (
        page.url.startswith("https://")
        or (policy and canonical_origin(page.url) in policy.local_origins)
        if page.url != "about:blank"
        else False
    )
    locator = (
        (
            page.get_by_label(step.target.name, exact=True)
            if step.target.by == "label"
            else page.get_by_role(step.target.role, name=step.target.name, exact=True)
        )
        if step.target
        else None
    )
    match step.action:
        case "navigate":
            await page.goto(url, wait_until="domcontentloaded")
        case "fill":
            if step.value_from and not secure_input:
                raise CheckFailure(
                    "sensitive-field",
                    "Runtime text requires HTTPS",
                    "HTTPS or explicitly authorized local test server",
                )
            if await locator.count() != 1:
                raise CheckFailure(
                    "target-ambiguous",
                    "Text field is absent or ambiguous",
                    "One matching text field",
                )
            if await locator.get_attribute("type") == "password" and (
                not step.value_from or not inputs
            ):
                raise CheckFailure(
                    "sensitive-field",
                    "Password interaction blocked",
                    "Synthetic non-secret input only",
                )
            if journey.profile.keyboard_only:
                await keyboard_reach(page, locator, journey.tab_budget)
                await page.keyboard.press("ControlOrMeta+A")
                await page.keyboard.insert_text(value)
            else:
                await locator.fill(value)
        case "upload":
            if not secure_input:
                raise CheckFailure(
                    "upload-input",
                    "Uploads require HTTPS",
                    "HTTPS or explicitly authorized local test server",
                )
            if not inputs:
                raise CheckFailure(
                    "upload-input", "Runtime file input missing", "Choose a file for this run"
                )
            field = page.get_by_label(step.file_label, exact=True)
            if await field.count() != 1 or await field.get_attribute("type") != "file":
                raise CheckFailure(
                    "upload-input", "File input absent or ambiguous", "One labeled file input"
                )
            await field.set_input_files(inputs.files[step.value_from])
        case "activate":
            if journey.profile.keyboard_only:
                await keyboard_reach(page, locator, journey.tab_budget)
                await page.keyboard.press("Space" if step.target.role == "checkbox" else "Enter")
            else:
                await locator.click()
        case "press":
            await page.keyboard.press(step.value)
        case "assert_visible":
            try:
                await locator.wait_for(state="visible")
            except BrowserError as exc:
                raise CheckFailure(
                    "completion-assertion",
                    "Expected state was not visible in time",
                    f"Visible {step.target.role}: {step.target.name}",
                ) from exc
            if await locator.count() != 1 or not await locator.is_visible():
                raise CheckFailure(
                    "completion-assertion",
                    "Expected state is absent or ambiguous",
                    f"Visible {step.target.role}: {step.target.name}",
                )
        case "assert_modal":
            await locator.wait_for(state="visible")
            for _ in range(8):
                if not await locator.evaluate("e => e.contains(document.activeElement)"):
                    raise CheckFailure(
                        "modal-focus-escape",
                        "Keyboard focus is outside the open modal",
                        "Focus enters and remains in the modal while it is open",
                    )
                await page.keyboard.press("Tab")
        case "assert_value":
            if await locator.count() != 1 or await locator.input_value() != value:
                raise CheckFailure(
                    "form-state-lost",
                    "Field does not retain the expected value",
                    "Entered synthetic value survives the transition",
                )
        case "assert_errors":
            result = await page.evaluate("""() => {
              const fields=[...document.querySelectorAll('[aria-invalid=true]')];
              return {count:fields.length,associated:fields.every(e=>
                (e.getAttribute('aria-describedby')||e.getAttribute('aria-errormessage')||'')
                  .split(/\\s+/).some(id=>document.getElementById(id)?.textContent.trim())),
                live:[...document.querySelectorAll('[role=alert],[aria-live=assertive],[aria-live=polite]')]
                  .some(e=>e.getClientRects().length && e.textContent.trim())};
            }""")
            if not result["count"] or not result["associated"] or not result["live"]:
                raise CheckFailure(
                    "error-semantics",
                    f"Validation semantics: {result}",
                    "Invalid fields associated with text errors and a populated live region",
                )
        case "offline" | "online":
            offline = step.action == "offline"
            await context.set_offline(offline)
            await page.wait_for_function(
                "expected => navigator.onLine === expected", arg=not offline
            )
        case "wait":
            await asyncio.sleep(int(step.value) / 1000)
        case "audit":
            if not axe_path.is_file():
                raise CheckFailure(
                    "audit-unavailable",
                    "Bundled axe-core script is missing",
                    "Install npm dependencies before running an audit",
                )
            # Instrument the isolated target through CDP without changing its CSP.
            session = await context.new_cdp_session(page)
            try:
                injected = await session.send(
                    "Runtime.evaluate",
                    {
                        "expression": axe_path.read_text(encoding="utf-8"),
                        "allowUnsafeEvalBlockedByCSP": True,
                    },
                )
                if "exceptionDetails" in injected:
                    raise CheckFailure(
                        "audit-unavailable",
                        "axe injection failed",
                        "Audit instrumentation available",
                    )
            finally:
                await session.detach()
            return await page.evaluate("""async () => {
              const r=await axe.run(document, {resultTypes:['violations','incomplete']});
              return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,
                description:v.description,helpUrl:v.helpUrl,
                targets:v.nodes.slice(0,20).map(n=>n.target)})),
                incomplete:r.incomplete.map(v=>({id:v.id,description:v.description}))};
            }""")
    return None
