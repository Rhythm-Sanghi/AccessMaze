"""An isolated manual browser recorder. Captures intent and labels, never typed values."""

import asyncio
import copy
import threading
from uuid import uuid4

from playwright.async_api import async_playwright
from pydantic import ValidationError

from accessmaze.actions import cancellable
from accessmaze.models import Step
from accessmaze.network import BrowserPolicy, canonical_origin

SCRIPT = r"""(() => {
  if (window !== window.top || window.__accessmazeRecording) return;
  window.__accessmazeRecording = true;
  const label = e => (e.getAttribute('aria-label') ||
    (e.getAttribute('aria-labelledby') || '').split(/\s+/)
      .map(id=>document.getElementById(id)?.textContent||'').join(' ').trim() ||
    (e.labels ? [...e.labels].map(l=>l.textContent).join(' ').trim() : '') ||
    (['BUTTON','A'].includes(e.tagName) ? e.textContent : '') || '').trim().slice(0,200);
  const role = e => e.getAttribute('role') || ({BUTTON:'button', A:'link', TEXTAREA:'textbox',
    INPUT: ['submit','button','reset'].includes(e.type) ? 'button' : e.type==='checkbox'
      ? 'checkbox' : e.type==='radio' ? 'radio' : 'textbox'})[e.tagName];
  const target = e => ({role:role(e),name:label(e),
    by:e.matches('input,textarea') ? 'label':'role'});
  const emit = value => window.__accessmazeRecord(value).catch(()=>{});
  const dirty = new WeakSet();
  document.addEventListener('input', event => {
    if (event.isTrusted && event.target.matches('input,textarea')) dirty.add(event.target);
  },true);
  const flush = e => {
    if (!dirty.has(e)) return;
    dirty.delete(e); emit({action:'fill',target:target(e)});
  };
  document.addEventListener('change', event => {
    const e=event.target; if (!event.isTrusted || !e.matches('input,textarea')) return;
    if (['checkbox','radio','button','submit','reset','hidden'].includes(e.type)) return;
    // Intentionally never access value, files, filenames, clipboard or key characters.
    if(e.type==='file') emit({action:'upload',file_label:label(e)}); else flush(e);
  },true);
  document.addEventListener('click', event => {
    if (!event.isTrusted || event.detail===0) return;
    const e=event.target.closest('button,a[href],[role=button],'+
      'input[type=checkbox],input[type=radio],input[type=submit]');
    if (e) emit({action:'activate',target:target(e)});
  },true);
  document.addEventListener('keydown', event => {
    if (!event.isTrusted) return;
    const keys=['Tab','Enter',' ','Escape','ArrowDown','ArrowUp',
      'ArrowLeft','ArrowRight','Home','End'];
    if (!keys.includes(event.key) || event.ctrlKey || event.metaKey || event.altKey) return;
    // Text editing arrows/Home/End are not useful journey actions and can reveal typing behavior.
    if (event.target.matches('input,textarea') &&
      !['Tab','Enter','Escape'].includes(event.key)) return;
    if (event.target.matches('input,textarea')) flush(event.target);
    emit({action:'press',value:event.key===' ' ? 'Space' :
      event.key==='Tab' && event.shiftKey ? 'Shift+Tab':event.key});
  },true);
})();"""


class Recording:
    def __init__(self, journey):
        self.id = str(uuid4())
        self.journey = journey.model_copy(deep=True)
        self.steps = [Step(id="open", action="navigate")]
        self.warnings = set()
        self.status = "preparing"
        self.origin = ""
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.cancel = self.stop
        self.capture = threading.Event()
        self.binding_index = 0

    def snapshot(self):
        with self.lock:
            return {
                "id": self.id,
                "status": self.status,
                "origin": self.origin,
                "steps": [s.model_dump() for s in self.steps],
                "warnings": sorted(self.warnings),
            }

    def append(self, step):
        with self.lock:
            if len(self.steps) >= 100:
                self.warnings.add("Recording reached the 100-step bound")
                self.stop.set()
                return
            # Change events on the same field collapse into one input intent; values are never read.
            if (
                step.action == "fill"
                and self.steps[-1].action == "fill"
                and self.steps[-1].target == step.target
            ):
                return
            self.steps.append(step)

    async def attach(self, context, page):
        async def event(source, payload):
            if source["page"] != page or source["frame"] != page.main_frame or self.stop.is_set():
                return
            try:
                if not isinstance(payload, dict) or payload.get("action") not in {
                    "fill",
                    "activate",
                    "press",
                    "upload",
                }:
                    raise ValueError("Unsupported event")
                data = copy.deepcopy(payload)
                data["id"] = f"recorded-{len(self.steps)}"
                data["effect"] = data["action"] in {"activate", "upload"} or data.get("value") in {
                    "Enter",
                    "Space",
                }
                if data["action"] in {"fill", "upload"}:
                    self.binding_index += 1
                    data["value_from"] = f"input_{self.binding_index}"
                step = Step.model_validate(data)
                if (
                    step.target
                    and not step.target.name
                    or step.action == "upload"
                    and not step.file_label
                ):
                    raise ValueError("Missing label")
                self.append(step)
            except (ValidationError, ValueError, TypeError):
                self.warnings.add(
                    "An unsupported or unnamed interaction was omitted; edit the journey manually"
                )

        await context.expose_binding("__accessmazeRecord", event)
        await context.add_init_script(SCRIPT)
        page.on("dialog", lambda dialog: dialog.dismiss())

    async def capture_completion(self, page):
        headings = page.get_by_role("heading", level=1)
        if await headings.count() != 1 or not await headings.is_visible():
            self.warnings.add(
                "Completion needs one visible level-one heading; add an assertion manually"
            )
            return
        name = await headings.get_attribute("aria-label") or await headings.inner_text()
        if (
            not 1 <= len(name.strip()) <= 200
            or await page.get_by_role("heading", name=name.strip(), exact=True).count() != 1
        ):
            self.warnings.add("Completion heading is ambiguous; add an assertion manually")
            return
        self.append(
            Step(
                id=f"completion-{len(self.steps)}",
                action="assert_visible",
                target={"role": "heading", "name": name.strip()},
            )
        )


class Recorder:
    def __init__(self, journey, target):
        self.recording = Recording(journey)
        self.target = target
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self.recording.snapshot()

    def _run(self):
        async def run():
            recording = self.recording
            policy = BrowserPolicy(recording.journey, self.target, recording.warnings)
            browser = None
            try:
                async with asyncio.timeout(recording.journey.max_seconds):
                    await cancellable(policy.prepare(), recording)
                    if any(
                        not origin.startswith("https://") and origin not in policy.local_origins
                        for origin in policy.navigation
                    ):
                        recording.warnings.add(
                            "Recording requires HTTPS or an authorized private test origin"
                        )
                        return
                    async with async_playwright() as pw:
                        browser = await cancellable(
                            pw.chromium.launch(headless=False, args=policy.launch_args), recording
                        )
                        context = await browser.new_context(
                            service_workers="block", accept_downloads=False
                        )
                        await policy.install(context)
                        page = await context.new_page()
                        await policy.attach(page)
                        await recording.attach(context, page)
                        # Manual session effects are separately authorized before launching.
                        policy.effects = True
                        await page.goto(self.target, wait_until="domcontentloaded")
                        recording.status = "recording"
                        while (
                            not recording.stop.is_set()
                            and browser.is_connected()
                            and not page.is_closed()
                        ):
                            try:
                                recording.origin = canonical_origin(page.url)
                            except ValueError:
                                recording.warnings.add("Unsupported navigation; recording stopped")
                                break
                            if recording.capture.is_set():
                                recording.capture.clear()
                                await recording.capture_completion(page)
                            await asyncio.sleep(0.1)
            except TimeoutError:
                recording.warnings.add("Recording reached its time bound")
            except asyncio.CancelledError:
                pass
            except Exception:
                # Never log browser exception details, which can contain credentials or page text.
                recording.warnings.add(
                    "Recording browser stopped or could not start; check browser installation"
                )
            finally:
                if browser and browser.is_connected():
                    await browser.close()
                recording.status = "stopped"

        asyncio.run(run())

    def close(self):
        self.recording.stop.set()
        self.thread.join(timeout=10)
