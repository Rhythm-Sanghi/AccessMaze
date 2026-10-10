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

Manual release checks: complete a project/journey/run/report flow using only a keyboard;
inspect focus after navigation/dialog closure; test 200% text and narrow windows; verify
both themes in high contrast; evaluate announcements with NVDA; inspect graph alternatives;
cancel during browser preparation and active actions; kill/restart worker; run offline with
all external connectivity blocked. Do not mark an unevaluated check as passed.
