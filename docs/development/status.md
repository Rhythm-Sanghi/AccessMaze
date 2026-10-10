# Engineering status

Updated 2026-10-10. Verification below records actual local execution.

## Implemented

### Native covered-source delivery — byte-verified offline archives

The notice recipe now preserves the original source archives for all five resolved
MPL native crates (`cssparser`, `cssparser-macros`, `dtoa-short`, `option-ext`, `selectors`).
Each matches its Cargo.lock SHA-256; **66 published files** match the compiler registry
sources byte for byte. Notice index links make these sources available offline under
MPL-2.0. `../legal/covered-source-verification.json` records hashes/counts/provenance.
Regression rejects changed lock bytes or modified compiler source. Actual
`pytest engine/tests/test_distribution_notices.py -q`: **5 passed**; actual inventory
generation: **627 components / 782 notice files / 73 non-distributed raw flags**.

First clean `7738b1a` preview build completed with new security code/notices and omitted
standalone video encoder. The source-delivery follow-up requires a second final preview
build; actual frozen/native results and artifact identity are recorded below when complete.
The full committed engine suite passed **92 tests in 161.63 s**. Fresh npm/Python/Rust
advisory commands found zero known vulnerability entries; Rust retains the same two
informational warnings outside the Windows graph, confirmed by `cargo tree -i`.
No blanket clean all-platform or legal qualification is claimed. Browser/Microsoft
provenance, browser/axe preferred-source obligations and independent review remain open.

### Release verification pipeline and repeatable stability harness

Workflow now adds manual dispatch, read-only permissions, cancellation/time bounds,
Windows cargo-audit and a dependent Windows preview build/frozen PowerShell+complex
browser checks/ZIP CRC+SHA/artifact job. Actual actionlint 1.7.7 and Prettier passed;
official release archive checksum verified. **Remote Actions NOT RUN**. No GitHub CLI
or dispatch operation is available in this environment; the read-only connector's
original-commit query returned no PR-triggered runs only. Exact maintainer actions and
evidence requirements: `../testing/ci-verification.md`.

The package recipe omits the unused standalone FFmpeg video encoder, avoiding its
static binary redistribution; semantic journey recording does not request video.
Chromium incorporated codecs/source obligations and older packages' standalone LGPL
obligations remain open. Notice/package regressions: **4 passed**, including actual
Chromium credits. A new preview must verify real recording/browser behavior without it.

The stability harness keeps one Worker alive across cycles, runs actual browser
journeys/cancellation, verifies SQLite, exports/deletes real artifacts, then repeats
the real browser/recording/offline/persistence regression battery. Initial harness
validation completed two cycles of **32 passed each**, persistent accessible/broken
journeys, SQLite integrity and cleanup, zero surviving children. Exploratory earlier
run: **619.71 s / 18 cycles**, peak summed harness+children RSS **698.74 MiB**, idle
handles 206 initially/196 finally, zero cycle-boundary children. Code changed late in
that exploratory run; raw evidence explicitly disqualifies it as fixed-source stability.
Final committed-source run is recorded separately. No overnight claim.

Hackyard presentation now includes a three-minute real-result sequence, architecture
diagram, workflow differentiation, current/future boundaries and pre-existing versus
continuation work/AI-assistance ledger. Competition start/eligibility must be supplied
by the entrant. See `../testing/hackyard-presentation.md`; no invented eligibility claim.

### Internal security follow-up â€” reproduced failures corrected

Two regressions initially failed on existing behavior: an explicit Everyone read grant
on an existing SQLite file/screenshot survived root-only hardening, and unexpected
exception text exposed a synthetic private browser value on stderr. Storage now
reapplies private DACLs to existing descendants, fails on enumeration/ACL errors and
refuses child junctions/reparse points. Real Windows tests confirm data is preserved
and a junction's outside ACL is unchanged. Worker internal/storage/parameter failures
now use static diagnostics plus correlation UUIDs, without exception text or tracebacks.

An isolated execution of the original `275a4e1` worker also confirmed oversized-frame
suffix execution and malformed-ID data echo (4 responses, both defects true). The
fixed worker drains the whole oversized frame in bounded chunks and echoes only
validated string IDs. A real subprocess regression sees 3 responses, no synthetic
private value and subsequent healthy IPC.

`pytest engine/tests/test_permissions.py engine/tests/test_worker.py
engine/tests/test_license_gap_review.py -q`: **12 passed**. The preceding full engine
suite passed **90 tests in 138.63 s** before the final protocol and packaging additions;
final suite is rerun below. TypeScript/ESLint, 5 React tests, frontend build, contracts,
Ruff/format and 1 actual Rust Windows Job test passed. Internal engineering review only;
independent security, bootstrap diagnostics, hostile browser/OS containment and signing
remain open. See `../testing/security-review.md`.

### License gap investigation â€” original 87 rows classified

Continued from clean `275a4e1`. `docs/legal/license-gap-review.md` and JSON record
every original gap and its evidence. Actual Vite module collection excluded 71 npm
build/platform entries; actual frozen PyInstaller Analysis source matching excluded
8 Python development/platform entries. Two Python packages (`markdown-it-py`, `mdurl`)
really ship and retain their original notices. Six Windows crates now have preserved
license texts: five from exact upstream VCS revisions, selectors from the Mozilla
license explicitly named in its hashed source declaration. No SPDX expression inferred.

`license_audit.py` recognizes `mit.LICENSE`, preserves publisher license classifiers,
validates supplement revisions/hashes, records dirty provenance and writes a readable
third-party notice index. Actual commands are in the review: 627 components / 782
collected notice files / 73 raw flags (non-distributed entries remain visible), all 87
original rows classified with no open notice row. Distribution notice tests: **3 passed**,
including real Chromium hidden license extraction; Ruff passed. Initial upstream 404s
and the one-open-row intermediate review are preserved/documented.

This closes investigation of those metadata flags, **not redistribution qualification**.
FFmpeg static LGPL corresponding source/relink plan, covered native MPL source delivery,
Chromium/headless incorporated obligations, Microsoft binary provenance and independent
legal review remain release blockers. Existing packaged artifacts are unchanged; the
updated notice recipe must be used in a subsequent verified preview.

### Final readiness preview â€” verified locally, release gates open

Built `dist/AccessMaze-readiness-preview-final` from clean source **207a09a**, preserving
all previous previews. `package-manifest.json`: **1,690 hashed files**, dirty=false.
Frozen verification explicitly asserts that the new in-flight connectivity limitation
is present in saved/exportable run evidence. Actual final commands/results:

- `uv run --project engine python scripts/package_windows.py --name AccessMaze-readiness-preview-final`: native release host, frozen Python worker, freshly installed full Chromium/headless shell, dependency inventory/notices and exact browser credits built successfully.
- `powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package dist/AccessMaze-readiness-preview-final -Report docs/releases/readiness-final-powershell.json`: hashes/path containment, system-only PATH, three browser fixtures, report identity and EOF passed; worker startup **0.718 s**.
- `uv run --project engine python scripts/portable_smoke.py --package AccessMaze-readiness-preview-final --complex --report docs/releases/readiness-final-smoke.json`: three fixtures plus 19-step HTTP SPA/upload passed expected outcomes, coverage uncompromised, exact uploaded bytes/one POST and persisted connectivity limitation asserted; worker startup **1.669 s**. Concurrent checks/archive and laptop load produced fixture durations **18.657â€“26.355 s**, complex run **29.350 s**. This variability is retained, not presented as a performance-budget pass.
- Launched final executable with `launch_preview.py`; repeated `desktop_smoke.py`, `desktop_website_smoke.py`, `desktop_readiness.py` and `desktop_crash.py` at test-only port 9224. All passed: native flows, light/dark axe (contrast incomplete), one approved POST/no replay, visible recorder, Tab/Enter/heading and dialog focus, private actionable error/input retention, interruption/restart and **4 Chromium children cleaned**.
- An actual native Connection recovery fixture run exposed the expected form-state-lost finding and displayed the new offline-emulation limitation. Result: `../testing/desktop-connectivity.json`; screenshot: `screenshots/connectivity-limitation.png`.
- `uv run --project engine python scripts/archive_preview.py --package dist/AccessMaze-readiness-preview-final --archive dist/AccessMaze-readiness-preview-final.zip --report docs/releases/readiness-final-artifact.json`: **1,691 ZIP files / 391,203,383 bytes**, CRC passed; SHA-256 **da43a6e0303dcd89d4cf6e8cfcb61a8cecef15043ccba8be495d8f4e0dfeb87f**. Unsigned; hash detects corruption, not authenticated provenance.

Final engine suite: **83 passed**; **5 React tests**, **1 Rust test**, TypeScript/ESLint,
production build, Ruff, formatting and contracts passed as recorded in these milestones.
The test desktop was closed; owned children and ports 9224/9227 cleanup is recorded in
`../testing/readiness-cleanup.json`. Final post-runtime integrity-only check passed.
No source logic changed after this package's clean commit; subsequent changes record
verification. Working tree is committed clean at handoff.

**Not production-ready or release-qualified.** Actual human NVDA evaluation and an
independent clean Windows machine/image are unavailable here; their documented
procedures remain NOT RUN. Overnight stability, native large-graph scaling, independent
security/diagnostic review, the 87 dependency metadata/notice gaps, verified SBOM,
matching-source/binary distribution obligations, remote CI and signing remain open.
See the qualification matrix below. No AT or WCAG certification is claimed.

### Readiness follow-up â€” in-flight connectivity scope

The 82-test suite passed after adding archive timestamp regression. A subsequent real
in-flight API probe initially failed its expected-error assertion: offline emulation
alone allowed an already-started request to finish. Extended the owned server to hold
and actually close TCP requests; the regression now verifies visible failure, retained
draft, no automatic retry/submission after reconnection and explicit successful retry.
Reports now disclose the offline-emulation/in-flight limitation. The first integration
incorrectly returned this metadata as an axe audit; full-suite regressions exposed three
`KeyError` failures. Moved it to the existing interaction metadata channel; combined
SPA/interruption/demo regressions then **3 passed**. Full-suite rerun is recorded below.
That rerun had **82 passed / 1 failed** under substantial laptop load (77.6% CPU,
1.59 GiB available RAM): the pause/resume harness's fixed ten-second completion timer
cancelled its own run. The unchanged isolated test then passed in 5.58 s. Aligned that
completion wait with the journey's configured maximum plus shutdown allowance; pause
boundary/status assertions and separate cancellation responsiveness tests remain intact.
Final source rerun: `uv run --project engine pytest engine/tests -q`: **83 passed** in
102.15 s; Ruff/contracts/diff checks passed. Controlled 19-step corpus and Hackyard
demo were re-executed, with actual summaries in `compatibility-followup.json` and
`hackyard-demo-followup.json` under `../testing/`. Updated reports contain the connectivity
limitation. Archive regression suite: **3 passed**.
The previously verified `AccessMaze-readiness-preview` at `fcd95a8` is
preserved; the separately built and verified final preview above includes this correction.

### Readiness milestone 4 â€” frozen and native Windows revalidation

Built `dist/AccessMaze-readiness-preview` with
`uv run --project engine python scripts/package_windows.py --name AccessMaze-readiness-preview`.
Manifest records clean source `fcd95a8`, **1,690 hashed files**, 775 collected notices,
readable axe source, offline procedures and exact full Chromium credits. Earlier packages
are preserved. Native host compiled successfully; PyInstaller warned about optional
`tzdata`, which is not used by the tested UTC timestamp paths. No all-feature freeze claim.

Executed actual packaged checks:

- `powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package dist/AccessMaze-readiness-preview -Report docs/releases/readiness-portable-powershell.json`: integrity/path containment, system-only PATH, three real fixtures, exports and EOF passed; worker startup **0.662 s**.
- `uv run --project engine python scripts/portable_smoke.py --package AccessMaze-readiness-preview --complex --report docs/releases/readiness-portable-smoke.json`: three fixtures plus 19-step owned HTTP SPA passed expected outcomes, with exact actual uploaded bytes/one POST and uncompromised coverage; worker startup **0.713 s**. These independent processes ran concurrently on the same laptop, not independent machines.
- `uv run --project engine python scripts/desktop_startup.py --package AccessMaze-readiness-preview`: three native launches reached connected UI in **4.395 / 1.572 / 1.534 s**, ready summed RSS **437.70â€“447.93 MiB**, each owned process tree closed. Existing synthetic history, uncontrolled cache, CDP/poll overhead included.
- `uv run --project engine python scripts/launch_preview.py --package AccessMaze-readiness-preview`, followed by `desktop_smoke.py --endpoint http://127.0.0.1:9224`: real native three-fixture flows passed; light/dark axe zero violations, contrast **incomplete**. Screenshots visually inspected; existing design retained.
- `desktop_website_smoke.py --endpoint http://127.0.0.1:9224`: zero POSTs before approval, exactly one after, no replay, visible bundled recorder completion/stop passed.
- `desktop_readiness.py --endpoint http://127.0.0.1:9224`: actual Tab/Enter navigation and heading focus, private schema-error alert, retained invalid input, dialog initial focus/Escape/return focus passed; only its unique disposable project removed. Initial harness assumptions about navigation text and model-level error locations were corrected against the actual UI; no app defect inferred from those mismatches.
- `desktop_crash.py --endpoint http://127.0.0.1:9224 --exe dist/AccessMaze-readiness-preview/AccessMaze.exe`: interrupted state/restarted worker and **4 Chromium processes cleaned** passed.
- `cargo test --locked --manifest-path apps/desktop/src-tauri/Cargo.toml`: **1 passed**; Cargo formatting and Ruff passed.

Packaged startup applied the protected ACL to actual AppData and its pre-existing
database; `icacls` verified only current user/SYSTEM/Administrators remained. The owned
desktop was closed. An immediate port check preceded asynchronous WebView2 shutdown;
the bounded follow-up confirmed test-only ports **9224/9227 closed**. Archive CRC/hash
record is `../releases/readiness-artifact.json`. No public publication or upstream push.

Archive generation initially rejected epoch-dated upstream notice files (ZIP cannot
represent dates before 1980). The incomplete archive is preserved with an `-incomplete`
name. Added `scripts/archive_preview.py` to clamp ZIP timestamps without changing file
contents, refuse overwrite and check CRC/SHA-256; regression verifies preserved notice
bytes and overwrite refusal. The verified archive uses the ordinary preview ZIP name.

### Current qualification matrix

| Objective / gate | Actual disposition |
| --- | --- |
| Repeatable authorized compatibility corpus | Four Chromium paths completed; controlled SPA/API/forms/modal/upload/validation/conditional/offline covered. Broader site classes remain outside coverage. |
| Finding accuracy | Confirmed false positives/negatives corrected with browser regressions; full engine suite 90 passed before final protocol/package additions (final rerun recorded above). Native semantics/axe do not prove AT behavior or exhaustively clear findings. |
| Hackyard differentiation | Real failure, evidence, native-button correction, comparable retest and recorder draft replay reproduced; synthetic owned target only. |
| Windows performance | Startup/browser/RSS/handles/backend graph/reports measured locally. Overnight worker/UI soak, UI graph scaling and representative-hardware budgets NOT RUN. |
| Security | Local source/ACL/credential/retention/origin/isolation/integrity review complete; inherited/explicit child ACL and private diagnostic/frame defects fixed with regressions. Independent threat-model, bootstrap diagnostics privacy and hostile-target containment clearance OPEN. |
| Dependencies/distribution | 627-component inventory, collected notices, exact full-browser credits and advisory scans complete. all original 87 flags classified; required notices recovered. Verified binary SBOM/source obligations remain OPEN. |
| Portable runtime | Fresh frozen/native/system-PATH tests passed on this developer laptop. Independent clean Windows installation/upgrade/removal/offline qualification NOT RUN. |
| Human accessibility | Documented NVDA procedure; actual human NVDA/high contrast/manual evaluation NOT RUN. Requires a human tester. |
| CI / authenticity | Windows CI not executed remotely; package unsigned, authenticated public distribution/signing unverified. No upstream push or publication performed. |

This environment has no independent Windows machine/image or human NVDA tester.
Those external prerequisites prevent release qualification. Distribution clearance needs
the documented matching-source/rights review. These unresolved gates must remain open;
the locally verified artifact is an **unsigned development preview**, not production-ready.

### Readiness milestone 2 â€” local security, measurements and demonstration

Added repeatable 60-journey Windows benchmark with actual browser startup, resource
sampling, report timings, three-minute persistent-browser soak and separately labelled
synthetic graph scaling. Completed 60 expected fixture outcomes and 88 reloads over
181.04 seconds; peak summed RSS 421.74 MiB. See `../testing/readiness-benchmark.md` and
raw JSON for machine, timing scope and uncontrolled background activity. Overnight
stability, native large-graph UI performance and representative hardware remain gates.

Actual Windows ACL inspection found inherited access for another local group. Storage
now applies current-user/SYSTEM/Administrators-only protected inheritable permissions;
Windows regression verifies removal of seeded broad access and database inheritance.
Schema errors now identify safe fields and repair guidance without exposing input values.
Review and advisory results are in `../testing/security-review.md`; explicit child ACL
exceptions and private diagnostics remain review items. No encryption, secure erase or
hostile-site sandbox claim.

Executed `uv run --project engine python scripts/hackyard_demo.py --output
dist/Hackyard-readiness-demo`: real keyboard failure, native-button correction,
comparable passed retest, 19-step completion, one actual 25-byte multipart upload;
product recorder draft captured from scripted browser events and replayed successfully.
Reports/SQLite/diff are retained locally; summary/procedure are in
`../testing/hackyard-demo.json` and `../testing/hackyard.md`.

`uv run --project engine pytest engine/tests -q`: **79 passed** in 87.46 s after
permission/error/demo changes. Ruff/contracts/diff checks passed. The distribution
notice regressions separately passed **2 tests**. One attempted test invocation from
the Cargo directory selected global Python and failed in an unrelated pytest plugin;
the corrected repository-root invocation passed.

Manual NVDA and independent Windows procedures are in `../testing/nvda.md` and
`../releases/clean-machine.md`, all human/independent results explicitly **NOT RUN**.
No independent machine or human NVDA tester is available in this environment.

### Readiness milestone 3 â€” redistribution audit

Inventoried 627 locked/resolved components, copied 775 installed notices and recorded
87 unresolved declarations/notice sets. Extracted full Chromium's exact binary credits
offline, including 754 collapsed license sections; added a real-browser regression.
Packaging now includes inventory/notices, readable axe source and standalone credits.
`../architecture/dependencies.md` and `../testing/license-inventory.json` document scope
and unresolved binary/source obligations. Generator initially failed decoding Cargo's
UTF-8 through the Windows default codepage; explicit UTF-8 corrected it. Full notice
coverage, verified SBOM, FFmpeg source/relink plan, Microsoft DLL distribution rights
and headless-shell provenance remain release blockers.

Actual npm/Python audits found no known advisories (editable project skipped); Rust audit
found zero vulnerability entries plus two informational warnings outside the resolved
Windows graph. See security review. Existing portable artifact remains older source;
packaging, frozen workflow and native UI revalidation completed in milestone 4 above.

Final source checks for milestones 2â€“3: full engine suite **81 passed** in 93.55 s;
TypeScript/ESLint, **5 React tests**, production build, formatting, Ruff and contracts
passed. Raw advisory responses are retained in
`../testing/advisories-{npm,python,rust}.json`. No dependency lockfile was changed.

### Readiness milestone 1 â€” compatibility corpus and finding accuracy

Completed a controlled multi-step HTTP SPA with a separate CORS API, delayed rendering,
validation, conditional radio navigation, native modal/return focus, real multipart upload
and interrupted connectivity. Added opt-in, sequential Selenium and W3C educational
public cases with documented scope and exact resource permissions. All four final browser
paths completed without policy-compromised coverage. W3C before exposed seven axe rule
IDs; after still exposed two. Neither is represented as certified conformance.

Four initial browser regressions failed before fixes. The combined SPA exposed two more
cases: radio-group arrow navigation and native dialog focus moving to browser chrome.
Fixed bounded native radio activation/navigation, dynamic fill waits, disabled-target
classification, unrelated-live-region false negatives, native-validation uncertainty and
modal page-focus scope/final-move checks. Propagated interaction limitations into reports.

Commands/results: `uv run --project engine pytest engine/tests -q`: **76 passed**;
`uv run --project engine python scripts/compatibility.py --public`: **4 completed paths**,
one actual controlled upload/POST. Initial incomplete public results are preserved in
`../testing/compatibility-initial.json`; corrected results and rationale in
`../testing/compatibility.json` and `../testing/compatibility.md`.
No real NVDA, independent clean-machine or release qualification occurred.

### Continuation milestone 5 â€” portable verification

Prepared: full Chromium for the visible recorder, source/dependency and SHA-256 file
manifest, systems-only PowerShell checker, and actual native website/recorder smoke
script. `uv run --project engine pytest engine/tests/test_package_integrity.py -q`:
**1 passed**, exercising valid hashes, altered files and path-escape rejection through
the actual PowerShell script. Ruff, diff checks and Python/npm production dependency
audits passed (no known vulnerabilities; editable local project skipped by pip-audit).
Full engine suite including package integrity and cancellation: **69 passed**.
Headed recorder regressions passed (**4 recorder tests**): stopping
during a deliberately held initial HTTP response closes promptly, without waiting
for the response. Initial navigation and completion capture are now cancellable.
Built `dist/AccessMaze-web-preview` from clean commit `677a57a`, then repeated the
build as `dist/AccessMaze-web-preview-final` from clean commit `2285147` with reporting
corrections and updated guidance. Both earlier previews are preserved. Every frozen
AccessMaze Python module was compared against current-source bytecode and matched.
Actual packaged verification commands/results:

- `powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package dist/AccessMaze-web-preview-final -Report docs/releases/portable-powershell.json`: hashes/path containment, system-only PATH, three Chromium journeys, JSON identity and EOF shutdown passed; startup **0.797 s** (initial build **0.397 s**).
- `uv run --project engine python scripts/portable_smoke.py --package AccessMaze-web-preview-final`: three frozen journeys and report checks passed; startup **0.945 s** (initial build **0.556 s**, separate runs).
- `uv run --project engine python scripts/desktop_smoke.py --endpoint http://127.0.0.1:9224`: real native UI/IPC journeys passed; light/dark axe no violations, contrast incomplete.
- `uv run --project engine python scripts/desktop_website_smoke.py --endpoint http://127.0.0.1:9224`: owned HTTP app, zero POSTs before approval, one after approval, no reset/replay, bundled visible recorder completion capture/stop passed. The first attempt exposed a test-harness timing error, corrected by waiting for the original proposal to disappear.
- `uv run --project engine python scripts/desktop_crash.py --endpoint http://127.0.0.1:9224 --exe dist/AccessMaze-web-preview-final/AccessMaze.exe`: worker restart/interrupted evidence and cleanup of **4** Chromium processes passed.
- `uv run --project engine python scripts/benchmark.py`: **15** sequential real Chromium runs, **402.8 MiB** peak / **375.92 MiB** median summed RSS. Shared pages count per process; no UI startup or stress claim.

Screenshots and raw JSON contain actual local execution. The test-only WebView2
debugging port is not enabled by product code; the owned test app was closed.
These results do not establish independent clean-machine installation, signing,
manual assistive-technology behavior or release readiness.

Final review corrected fixture-only wording in website coverage and the in-progress
exploration display. The final package passed all native/portable checks again,
including assertions for the corrected labels. Targeted website regressions: **3 passed**;
TypeScript/ESLint, **5 React tests**, production build, formatting and contracts passed.
Its ZIP archive, CRC and SHA-256 record are in `../releases/preview-artifact.json`.
Archive verification passed for **902 files / 387,878,632 bytes**. The final owned
desktop process was closed and its test-only port 9224 was confirmed closed. All
source and verification records are committed locally; no upstream publication.

### Continuation milestone 4 â€” approved website exploration and computed semantics

Completed: external exploration follows one bounded path, proposing named browser
buttons/links and requiring a fresh explicit approval for every action. It never resets
or replays an external workflow. Approvals are bound to an observed state; changed
states and duplicate/stale decisions are refused. Time/depth/action bounds and
cancellation apply while waiting. Proposed names are transient in IPC; private saved
evidence uses tokens. Recovery/retention recognize runs waiting for approval.

Computed Chromium accessibility trees now expose roles/names/focus, bounded to
depth 8 and 500 semantic nodes, excluding field values. Keyboard attempts enforce
exact Tab counts and recognize open-shadow-root focus; focus assertions and bounded
forward/reverse modal checks are available. Error checks require visible associated
text and accept focused invalid fields as an alternative to populated live regions.
Live-region presence never proves a real assistive-technology announcement.

Commands: `uv run --project engine pytest engine/tests -q` **67 passed**, including actual visible Windows
recorder lifecycle, approved-action POST counters, no-replay checks, cancellation,
state-change refusal, native computed names, shadow focus and exact Tab bounds.
`npm run check`, `npm run build`, `npm run format:check` passed; **5 React tests
passed**, including keyboard activation of a specific approval and separate recorder
authorization. Ruff passed. No screen-reader or WCAG certification claim is made.

Additional real-browser regressions verify delayed approved POST redirects retain
only their existing chain permission, unrelated later writes are blocked, and HTTP
403 navigation produces an inconclusive finding. Dynamic action waits are configurable
from 1â€“30 seconds (default 10 seconds). Rust lifecycle test: **1 passed**.

A read-only public HTTPS probe navigated successfully to example.org but correctly
failed its obsolete expected heading; the current page has no matching heading.
`docs/testing/website-smoke.json` retains that negative result. Website projects now
start with an empty target and require the user's actual completion condition.
The optional smoke script requires explicit URL, heading and authorization arguments.

Limits: one approved walk is not exhaustive branch coverage. Candidate detection and
state identity are bounded, cannot prove equivalence and omit unsupported widgets.
Live dynamic changes may safely refuse approval. OS-level focus visibility, closed
shadow trees, screen-reader behavior and independent clean-machine gates remain.

### Continuation milestone 3 â€” manual browser recording

Completed: an isolated, separately authorized visible browser records supported
semantic clicks, navigation keys and field intents. Typed values, selected file names
and contents are never read by the recording script. Inputs become runtime bindings;
the user explicitly captures a completion heading and reviews the draft in the existing
editor. No recording is automatically replayed or saved. Sessions have time/100-step
bounds; worker shutdown closes them. Analysis and recording are mutually exclusive.

Verification: full suite before the headed lifecycle case **58 passed**; recorder
regressions including actual visible Windows Chromium **3 passed**. TypeScript/ESLint
and **3 React tests** passed. Actual record â†’ edit/runtime bindings â†’ fresh-browser
replay reached the captured assertion without retaining typed secrets.

The existing default-cache Chromium failed Windows activation (WinError 14001).
A freshly provisioned workspace cache launched successfully; the visible recorder
lifecycle test then passed. Development setup now documents that cache and the worker
uses it when present. No existing user browser/profile or cache was removed.

Limits: captures a supported subset; select/custom widgets, address-bar navigation,
dialogs and embedded/popup workflows require manual editing or are unsupported.
Labels/completion text can contain personal information and must be reviewed.
Manual-session scripts may issue writes on authorized origins while open.
Packaging includes full Chromium as well as its headless shell; the new package's
visible recorder passed. Independent clean-machine verification remains pending.

### Continuation milestone 2 â€” run-only account and file inputs

Completed: named runtime bindings for text/password inputs, labeled-field locators,
user-selected upload buffers (4 MiB combined), no imported filesystem paths, HTTPS
or approved private-address transport for sensitive input, and per-worker HMAC input
signatures so changed runtime data cannot verify a repair. Values/files never enter
project JSON, run records or backups. Context cookies remain ephemeral. Known input
values and filenames are redacted from evidence. Short secrets no longer damage
run IDs/status metadata. Effect actions have a documented 250 ms event-request grace.
Local axe instrumentation now works through CDP without changing target CSP.

Commands: full Python suite **56 passed**; TypeScript/ESLint passed; **3 React tests
passed**; production frontend build passed; Prettier passed; contracts regenerated.
The actual browser regression follows an approved cross-origin login redirect,
submits a password, receives an HTTP-only cookie and sends a multipart upload.
Assertions check actual received bytes and absence of sensitive values in persistence.

Limits: dedicated test accounts only; no personal-profile import, stored credentials,
SSO popup/iframe handling, browser-native file-picker verification or CAPTCHA bypass.
Run-input signatures intentionally cease to be comparable after worker restart.
Dynamic application text requires opt-in evidence capture; redaction remains best effort.

### Continuation milestone 1 â€” authorized website network policy

Completed from preserved commit `c66766d`: exact navigation/API and read-only
resource permissions; fixed DNS snapshot used by Chromium; effect-window write
permission; response-stage redirect checks; default-denied popups/embedded frames;
private website observations; blocked-traffic retest safeguards; website project entry
and permission controls using the existing design system. See ADR 002.

Commands executed: `uv run --project engine pytest engine/tests -q` **52 passed**;
`npm run check` passed; `npm test` **3 passed**; contracts regenerated. Real independent
HTTP servers verified script loading, blocked/allowed POST requests, forbidden server
redirects and popups. A real browser used a pinned synthetic DNS hostname. External
observation privacy was tested through the full persisted runner.

Known limits: only one attached page; embedded frames/popups, WebSockets and service
workers are denied. No system proxy support. Background writes outside explicit
effect actions are blocked. DNS pinning is not an OS firewall; clean-machine and
manual accessibility release gates remain open. Existing portable artifacts are the
previous commit and must not be mistaken for this milestone's source.

Working Windows desktop preview with React/TypeScript, Tauri, a private-stdio Python
worker, SQLite and real Playwright Chromium journeys. Includes saved projects,
semantic journey authoring/import/export, runtime budgets, explicit authorization,
keyboard and permitted pointer interactions, completion assertions, local axe audits,
offline/reconnect checks, observed-state graphs, evidence and JSON/HTML/CSV reports.

Eight synthetic fixtures cover accessible and broken keyboard flows, error semantics,
value loss, branching/reset loops, long-running actions, modal focus and conditional
submission. Opt-in bounded discovery replays named button branches on resettable
fixtures only, counts actions and records unexplored frontier bounds.

Runs support cancellation, pause between steps, partial evidence and interruption
recovery. Windows job objects clean browser descendants after worker termination.
Retest comparisons enforce identical redacted configuration. Consistent ZIP backup,
explicit retention cleanup and storage migrations are implemented.

## Baseline verification at c66766d (historical)

| Check | Result |
| --- | --- |
| Python suite with real Chromium fixtures | 42 passed |
| React component tests | 2 passed |
| Rust Windows lifecycle test | 1 passed |
| TypeScript, ESLint, Ruff, formatting and generated contracts | Passed |
| Production frontend and Windows release host | Built successfully |
| npm and Python dependency audits | No known vulnerabilities; local Python project excluded from PyPI lookup |
| Actual packaged WebView2 â†’ Rust â†’ frozen Python â†’ Chromium | Broken, accessible and conditional journeys passed |
| Desktop axe audit, light and dark | No reported violations; color contrast incomplete and requires manual evaluation |
| Frozen worker, system-only PATH, temporary directory with spaces | Three fixture runs and report checks passed; startup 1.634 seconds |
| Real worker crash | Development and packaged host recovery and Chromium cleanup passed |

Desktop audit injection uses test-only CDP evaluation; journey checks run with normal
application CSP. The packaged CSP correctly rejected ordinary inline script injection.
Screenshots in `screenshots/` are from the actual application.

The 15-run sequential benchmark measured 398.38 MiB peak summed RSS and 330.91 MiB
median sampled RSS for Python and child processes. Shared pages count in every
process's RSS. It excludes UI startup and long-running stress. Raw machine details
and timings at baseline are retained in Git history at `c66766d`. Current raw files
`../testing/benchmark.json` and `../releases/portable-smoke.json` contain the continuation
measurements recorded above.

## Milestone and release limits

This is an operational preview across parts of milestones 1â€“7, with milestone 8
hardening. It does not complete the master specification. Milestone 9 remains gated.

- External exploration is one approved walk; exhaustive coverage, unreachable-state proof and resume after crash remain absent.
- Recording supports a reviewed subset. Preconditions, arbitrary zoom and advanced pointer profiles remain; runtime uploads are supported.
- Real assistive-technology integration, manual NVDA/high-contrast/keyboard evaluation and full UI performance testing remain.
- Retests are narrow; human annotations and a full finding lifecycle remain.
- Broader non-HTTP containment and comprehensive security review remain; DNS is now pinned for approved hosts.
- Literal journey inputs remain plain text; credentials must use run-only bindings. Redaction is best effort.
- Corruption recovery UI, large-history pagination and virtualization remain.
- The unsigned portable build was tested on this Windows machine with developer tools removed from PATH. Clean-machine installation, upgrade/removal, signing, complete third-party license manifest and SBOM remain unverified.
- CI is configured but has not run on GitHub. No upstream push or publication occurred.

## Next engineering tasks

1. Extend recording coverage, precondition authoring and viewport zoom checks.
2. Validate broader dynamic applications and review network containment.
3. Expand stress, keyboard and assistive-technology evaluation.
4. Complete license/SBOM review and run Windows CI and clean-machine release checks.

The current environment provides one existing Windows developer machine and no
independent clean Windows installation or human assistive-technology evaluation.
Those release gates cannot be established by the automated tests above.

No full-spec completion, WCAG conformance or release-readiness claim is made.
