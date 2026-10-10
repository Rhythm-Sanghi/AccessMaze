# Verification scope

`engine/tests/test_browser.py` launches real Chromium against a random-port loopback
fixture server. It covers the broken/corrected keyboard workflow, missing error semantics,
actual browser offline/online events, value loss, authored conditional paths, graph cycle
detection, local axe-core execution and cancellation with process cleanup checks.

Storage tests cover schema version refusal, restart interruption, foreign-key deletion and
artifact path rejection. Protocol tests use real stdin/stdout and verify malformed version
recovery and effect authorization. Unit tests cover strict imports, fingerprints, redaction
and report escaping. React tests verify authoring through accessible controls.

These scopes are separate: React tests do not validate the Python runner, and Python tests
do not prove desktop IPC, installer behavior, keyboard accessibility of Windows chrome or
screen-reader compatibility. Desktop-host and clean-machine checks are recorded separately.

`scripts/desktop_smoke.py` exercised the actual packaged WebView2, Rust IPC, frozen
worker and bundled browser with three journeys and light/dark axe audits. Audit
instrumentation uses CDP evaluation because the normal packaged CSP blocks inline
injection. No violations were reported; color contrast remained incomplete.
`scripts/desktop_crash.py` kills only the selected application's worker and verifies
interruption recovery and descendant Chromium cleanup. The frozen-worker test
uses a stripped system-only PATH and a temporary directory containing spaces.
These tests ran on the build machine; clean-machine installation remains unverified.

Website regressions use independent real HTTP origins and Chromium. They cover DNS
pinning, resource/navigation/write separation, redirects, private evidence, run-only
password login with cookies, buffer uploads, dynamic waits, shadow focus and computed
accessibility names. No request interception mocks substitute for those browser runs.
The approved-walk tests count actual requests, require fresh decisions and check that
external state is never reset/replayed. Recorder tests replay a captured draft and use
actual visible Windows Chromium for stop/lifecycle checks, including slow navigation.
Visible tests are explicitly skipped on Linux without a desktop session.

`scripts/desktop_website_smoke.py` uses an owned HTTP app through packaged native UI:
zero POSTs before approval, exactly one afterward, no reset/replay, and visible recorder
completion capture/stop. `Test-AccessMazePortable.ps1` needs only Windows PowerShell/.NET
and the package; it validates hashes, frozen browser journeys, JSON identity and shutdown
with system-only PATH. Hashes detect corruption and are not a signature/authenticity check.

Optional `scripts/website_smoke.py --url URL --heading NAME --authorized` uses a real
read-only public target and defaults its private result to ignored `dist/`. The recorded
example.org probe correctly failed a stale expected heading after successful navigation;
it is not represented as a successful completion or a dependable third-party fixture.

Manual release checks: complete a project/journey/run/report flow using only a keyboard;
inspect focus after navigation/dialog closure; test 200% text and narrow windows; verify
both themes in high contrast; evaluate announcements with NVDA; inspect graph alternatives;
cancel during browser preparation and active actions; kill/restart worker; run offline with
all external connectivity blocked. Do not mark an unevaluated check as passed.

Readiness extensions: the [compatibility corpus](compatibility.md) adds real owned
multi-step/CORS/upload behavior and opt-in public educational targets. A separate
controlled TCP-drop test distinguishes in-flight interruption from Chromium's offline
emulation. The [Hackyard demo](hackyard.md) preserves failure, correction and retest.
The [benchmark](readiness-benchmark.md) separates real browser timings from synthetic
backend graph scaling. Native readiness checks cover keyboard navigation, safe error
alerts, retained input and dialog focus through WebView2/IPC. The
[NVDA procedure](nvda.md) and [independent Windows procedure](../releases/clean-machine.md)
remain unexecuted human/independent gates. Engineering status is authoritative.

Generated test reports and machine diagnostics are local outputs, ignored by Git.
Publish measured results and limitations in engineering status; keep source fixtures,
tests and legally required audit records in the repository.
