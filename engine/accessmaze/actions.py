import asyncio

from playwright.async_api import Error as BrowserError

from accessmaze.network import canonical_origin

DEEP_FOCUS = """e => {
  let active=document.activeElement;
  while(active?.shadowRoot?.activeElement) active=active.shadowRoot.activeElement;
  return e === active;
}"""


async def focus_description(page):
    return await page.evaluate("""() => {
      let e=document.activeElement;
      while(e?.shadowRoot?.activeElement) e=e.shadowRoot.activeElement;
      return {tag:e?.tagName.toLowerCase()||'',role:e?.getAttribute('role')||'',
        name:(e?.getAttribute('aria-label')||e?.labels?.[0]?.textContent||
          (['BUTTON','A'].includes(e?.tagName) ? e.textContent:'')||'').trim().slice(0,160)};
    }""")


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
    await locator.wait_for(state="visible")
    if await locator.count() != 1:
        raise CheckFailure(
            "target-ambiguous",
            "Target is absent or has multiple matches",
            "Exactly one visible semantic target",
        )
    trace = {"tab_presses": 0, "focus_history": []}
    browser_page = page if hasattr(page, "keyboard") else page.page
    browser_page.context._accessmaze_interaction = trace
    if not await locator.is_enabled():
        raise CheckFailure(
            "target-disabled",
            "Target is currently disabled",
            "Enable the target or test the prerequisite state before activation",
        )
    for index in range(budget + 1):
        if len(trace["focus_history"]) < 40:
            trace["focus_history"].append(await focus_description(page))
        if await locator.evaluate(DEEP_FOCUS):
            return
        if index == budget:
            break
        same_radio_group = await locator.evaluate("""target => {
          let active=document.activeElement;
          while(active?.shadowRoot?.activeElement) active=active.shadowRoot.activeElement;
          return target.matches('input[type=radio]') && target.name &&
            active?.matches('input[type=radio]') && active.name===target.name &&
            active.form===target.form && active.getRootNode()===target.getRootNode();
        }""")
        if same_radio_group:
            await browser_page.keyboard.press("ArrowRight")
            trace["arrow_presses"] = trace.get("arrow_presses", 0) + 1
        else:
            await browser_page.keyboard.press("Tab")
            trace["tab_presses"] += 1
    raise CheckFailure(
        "keyboard-unreachable",
        f"Target not reached within {budget} Tab presses"
        if not trace.get("arrow_presses")
        else f"Target not reached within {budget} keyboard moves (Tab/ArrowRight)",
        "Target reachable through sequential keyboard navigation",
    )


async def perform(page, context, step, journey, url, axe_path):
    context._accessmaze_interaction = {}
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
    surface = page
    if step.target and step.target.frame_name:
        matches = [frame for frame in page.frames if frame.name == step.target.frame_name]
        if len(matches) != 1 or matches[0] == page.main_frame:
            raise CheckFailure(
                "target-ambiguous", "Named frame absent or ambiguous", "One named embedded frame"
            )
        surface = matches[0]
        policy = getattr(context, "_accessmaze_policy", None)
        if surface.url == "about:blank":
            await surface.wait_for_url(lambda value: value != "about:blank")
        try:
            origin = canonical_origin(surface.url)
        except ValueError:
            origin = None
        if not journey.network.embedded_frames or not policy or origin not in policy.navigation:
            raise CheckFailure(
                "frame-unavailable",
                "Frame is outside the authorized navigation origins",
                "Explicit frame permission and an approved HTTP(S) document",
            )
    inputs = getattr(context, "_accessmaze_inputs", None)
    value = inputs.value(step) if inputs and step.action in {"fill", "assert_value"} else step.value
    policy = getattr(context, "_accessmaze_policy", None)
    secure_input = (
        surface.url.startswith("https://")
        or (policy and canonical_origin(surface.url) in policy.local_origins)
        if surface.url != "about:blank"
        else False
    )
    locator = (
        (
            surface.get_by_label(step.target.name, exact=True)
            if step.target.by == "label"
            else surface.get_by_role(step.target.role, name=step.target.name, exact=True)
        )
        if step.target
        else None
    )
    match step.action:
        case "navigate":
            response = await page.goto(url, wait_until="domcontentloaded")
            if response:
                context._accessmaze_interaction = {"http_status": response.status}
                if response.status >= 400:
                    raise CheckFailure(
                        "navigation-http",
                        f"Navigation returned HTTP {response.status}",
                        "Target is available before accessibility checks",
                    )
        case "fill":
            if step.value_from and not secure_input:
                raise CheckFailure(
                    "sensitive-field",
                    "Runtime text requires HTTPS",
                    "HTTPS or explicitly authorized local test server",
                )
            await locator.wait_for(state="visible")
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
                await keyboard_reach(surface, locator, journey.tab_budget)
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
                await keyboard_reach(surface, locator, journey.tab_budget)
                await page.keyboard.press(
                    "Space" if step.target.role in {"checkbox", "radio"} else "Enter"
                )
            else:
                await locator.click()
        case "press":
            await page.keyboard.press(step.value)
        case "assert_visible":
            try:
                await locator.wait_for(state="visible")
            except BrowserError as exc:
                raise CheckFailure(
                    "target-ambiguous" if await locator.count() > 1 else "completion-assertion",
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
            keys = ["Tab"] * 8 + ["Shift+Tab"] * 8
            chrome_hops = 0
            for index in range(len(keys) + 1):
                focus = await locator.evaluate("""e => ({
                  inside:e.contains(document.activeElement),pageFocused:document.hasFocus()})""")
                if not focus["pageFocused"]:
                    chrome_hops += 1
                elif not focus["inside"]:
                    raise CheckFailure(
                        "modal-focus-escape",
                        "Keyboard focus is outside the open modal",
                        "Focus enters and remains in the modal while it is open",
                    )
                if index < len(keys):
                    await page.keyboard.press(keys[index])
            context._accessmaze_interaction = {
                "modal_keyboard_moves": len(keys),
                "outside_document_focus_observations": chrome_hops,
                "limitation": "Modal check covers page focus only; "
                "browser chrome/OS focus requires manual review",
            }
        case "assert_focus":
            if await locator.count() != 1 or not await locator.evaluate(DEEP_FOCUS):
                raise CheckFailure(
                    "focus-mismatch",
                    "Focus is not on the expected target",
                    "Expected semantic target owns keyboard focus",
                )
        case "assert_value":
            if await locator.count() != 1 or await locator.input_value() != value:
                raise CheckFailure(
                    "form-state-lost",
                    "Field does not retain the expected value",
                    "Entered synthetic value survives the transition",
                )
        case "assert_errors":
            result = await page.evaluate("""() => {
              const visible=e=>!!e && e.checkVisibility({
                checkOpacity:true,checkVisibilityCSS:true});
              const fields=[...document.querySelectorAll('[aria-invalid=true]')]
                .filter(visible);
              const errors=fields.map(e=>[
                e.getAttribute('aria-describedby')||'',e.getAttribute('aria-errormessage')||'']
                .join(' ').split(/\\s+/).map(id=>document.getElementById(id))
                .filter(e=>visible(e)&&e.textContent.trim()));
              const live=[...document.querySelectorAll(
                '[role=alert],[aria-live=assertive],[aria-live=polite]')]
                .filter(e=>visible(e)&&e.textContent.trim());
              return {count:fields.length,associated:errors.every(list=>list.length>0),
                focus:fields.includes(document.activeElement),
                native_invalid:!!document.querySelector('input:invalid,select:invalid,textarea:invalid'),
                live:errors.length>0 && errors.every(list=>list.some(error=>live.some(region=>
                  region.contains(error)||region.textContent.includes(error.textContent.trim()))))};
            }""")
            context._accessmaze_interaction = {
                "error_semantics": result,
                "limitation": "Live-region presence does not prove an announcement",
            }
            if (
                not result["count"]
                or not result["associated"]
                or not (result["live"] or result["focus"])
            ):
                raise CheckFailure(
                    "native-validation-unverified"
                    if not result["count"] and result["native_invalid"]
                    else "error-discoverability-unverified"
                    if result["count"] and result["associated"]
                    else "error-semantics",
                    f"Validation semantics: {result}",
                    "Visible associated errors with a populated live region "
                    "or focus on an invalid field",
                )
        case "offline" | "online":
            offline = step.action == "offline"
            await context.set_offline(offline)
            await page.wait_for_function(
                "expected => navigator.onLine === expected", arg=not offline
            )
            context._accessmaze_interaction = {
                "limitation": "Connectivity uses Chromium offline emulation; in-flight requests "
                "may finish. Physical connection interruption requires a controlled-server "
                "or manual network test."
            }
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
