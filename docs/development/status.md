# Engineering status

Updated 2026-10-10. Verification below records actual local execution.

## Implemented

### Readiness milestone 2 — local security, measurements and demonstration

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

### Readiness milestone 3 — redistribution audit (package verification pending)

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
new packaging, frozen workflow and native UI revalidation are pending below.

Final source checks for milestones 2–3: full engine suite **81 passed** in 93.55 s;
TypeScript/ESLint, **5 React tests**, production build, formatting, Ruff and contracts
passed. Raw advisory responses are retained in
`../testing/advisories-{npm,python,rust}.json`. No dependency lockfile was changed.

### Readiness milestone 1 — compatibility corpus and finding accuracy

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

### Continuation milestone 5 — portable verification

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

### Continuation milestone 4 — approved website exploration and computed semantics

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
from 1–30 seconds (default 10 seconds). Rust lifecycle test: **1 passed**.

A read-only public HTTPS probe navigated successfully to example.org but correctly
failed its obsolete expected heading; the current page has no matching heading.
`docs/testing/website-smoke.json` retains that negative result. Website projects now
start with an empty target and require the user's actual completion condition.
The optional smoke script requires explicit URL, heading and authorization arguments.

Limits: one approved walk is not exhaustive branch coverage. Candidate detection and
state identity are bounded, cannot prove equivalence and omit unsupported widgets.
Live dynamic changes may safely refuse approval. OS-level focus visibility, closed
shadow trees, screen-reader behavior and independent clean-machine gates remain.

### Continuation milestone 3 — manual browser recording

Completed: an isolated, separately authorized visible browser records supported
semantic clicks, navigation keys and field intents. Typed values, selected file names
and contents are never read by the recording script. Inputs become runtime bindings;
the user explicitly captures a completion heading and reviews the draft in the existing
editor. No recording is automatically replayed or saved. Sessions have time/100-step
bounds; worker shutdown closes them. Analysis and recording are mutually exclusive.

Verification: full suite before the headed lifecycle case **58 passed**; recorder
regressions including actual visible Windows Chromium **3 passed**. TypeScript/ESLint
and **3 React tests** passed. Actual record → edit/runtime bindings → fresh-browser
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

### Continuation milestone 2 — run-only account and file inputs

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

### Continuation milestone 1 — authorized website network policy

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
| Actual packaged WebView2 → Rust → frozen Python → Chromium | Broken, accessible and conditional journeys passed |
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

This is an operational preview across parts of milestones 1–7, with milestone 8
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
