# Engineering status

Updated 2026-10-10. Verification below records actual local execution.
The first acceptance section is current. Older milestone entries preserve their
point-in-time pending checks; later completed verification supersedes those entries.

## Implemented

### Final remaining-feature acceptance — clean application source 746eaca

The approved branching/recovery, finding-specific replay and reusable profile milestones
are implemented and locally verified. Final package `dist/AccessMaze-hackyard-preview`
was built from **746eaca94fae91a7749c1ce293ac721bc03f95a4**, **source_dirty=false**,
with **1,702 hashed files**, frozen Python and bundled Chromium. Later changes are
verification tools/documentation/evidence only. No application source changed after this build.

Actual native WebView2 → private Rust IPC → frozen worker → Chromium checks:

- `desktop_features.py`: **passed in 22.365 s**, three separately approved actions,
  root recovery, saved 125% layout-zoom profile reused across two projects, blocked
  keyboard run, observed-again replay, native-button correction and successful replay.
  Actual browser durations **1.692 / 1.809 / 1.630 / 6.008 s**, graph nodes **2 / 2 / 2 / 3**.
  Historical/live focus shows **8 failed Tab presses versus 1 successful press**.
  Owned feature projects/profile removed through the UI; screenshots visually inspected.
- `desktop_comparison.py`: actual blocked → completed journey, **passed-retest**,
  first divergent step `continue`, stale comparison hidden and owned project removed.
- `desktop_readiness.py`: actual Tab/Enter navigation/heading focus, private actionable
  schema error/input retention, native dialog initial/restored focus; all passed.
- `desktop_website_smoke.py`: actual per-action approval, **one POST**, no automatic
  external reset/replay, headed recorder H1 capture; passed after correcting an obsolete
  checkbox selector. The failed selector attempt is retained in the verification ledger.
- `desktop_crash.py --exe dist/AccessMaze-hackyard-preview/AccessMaze.exe`: actual worker
  kill during execution; replacement worker restored **interrupted** run/step evidence;
  **4 Chromium processes exited** through the Windows Job object.
- New `desktop_cancel.py` with the same executable guard: actual Emergency stop,
  persisted **cancelled** execution/task outcome, **1 retained graph node**, **4 Chromium
  processes exited**, owned project removed. First attempt had an ambiguous two-button
  test selector; scoping to Analysis workspace fixed the harness, without an app change.

Axe on the tested replay/comparison views: **0 violations**, **color-contrast incomplete**.
This is bounded automated evidence, not exhaustive UI accessibility or NVDA verification.
Raw records: ../hackyard/final-feature-verification.json and the files it indexes.
First native records at 7628688 are retained separately as native-features-first-{runs,verification}.json.

Portable verification commands actually executed:

```powershell
uv run --project engine python scripts/portable_smoke.py --package AccessMaze-hackyard-preview --complex --report docs/hackyard/final-complex-portable-verification.json
powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package ./dist/AccessMaze-hackyard-preview -Report docs/hackyard/final-portable-integrity-verification.json
uv run --project engine python scripts/desktop_startup.py --package AccessMaze-hackyard-preview
uv run --project engine python scripts/hackyard_demo.py --output dist/Hackyard-final-feature-evidence
```

The frozen worker passed with **System32-only PATH**, working directory with spaces,
portable Chromium, JSON/HTML exports and clean EOF exit. Startup **0.612 s**; actual
accessible/broken/conditional/owned-SPA runs **2.483 / 2.487 / 3.032 / 7.013 s**, expected
statuses and findings **0 / 1 / 0 / 0**; actual multipart bytes and single POST asserted.
PowerShell independently rehashed the manifest on this laptop and ran the three fixtures:
**passed**, startup **0.585 s**. Neither check is independent clean-machine verification.

Three sequential native launches reached connected UI in **4.746 / 4.028 / 3.720 s**,
summed ready RSS **448.97 / 446.24 / 441.50 MiB**, **8 children** each, all exited normally.
Final instrumented sequence close and separate ordinary non-CDP launch also exited all
children. Final idle sample: **493.88 MiB summed RSS / 3,687 handles / 8 children**.
Polling/CDP overhead, uncontrolled caches and shared pages limit these measurements;
no peak/leak/performance-budget/overnight claim. The earlier 7628688 instrumented retention
remains documented; subsequent passes do not establish its cause.

The fresh standalone Hackyard demo produced actual JSON/HTML/CSV, correction diff,
blocked keyboard → completed same-condition retest, **one 25-byte upload**, recorder replay
and separate blocked offline draft-loss assertion. Initial isolated axe findings **0**
do not contradict the later keyboard failure. Raw ../hackyard/final-demo-verification.json;
local reports `dist/Hackyard-final-feature-evidence/`.

Final archive `dist/AccessMaze-hackyard-preview-746eaca.zip`: **389,996,150 bytes**,
**1,703 ZIP entries** (1,702 manifest-covered files plus manifest), CRC passed;
SHA-256 **6165c5693f9e57803cfa88d93c0525c59c3830527331e3aa7c0a3bb1b0ec1a53**.
Command: `scripts/archive_preview.py --package dist/AccessMaze-hackyard-preview
--archive dist/AccessMaze-hackyard-preview-746eaca.zip
--report docs/hackyard/final-preview-artifact-verification.json` through the project Python.
The archive is unsigned; its local hash does not establish publisher authenticity.

A fresh ZIP extraction under `dist/Final portable verification Ω/` passed the same
manifest/fixture checker with System32-only PATH (**1.089 s** worker startup). The extracted
native desktop also reached **Worker connected in 5.239 s** with System32-only PATH and
closed **all 9 children**. Raw final-extracted-{portable,native}-verification.json. Existing
AppData and WebView2 were reused: this is neither fresh-user nor independent-machine evidence.
The extraction helper's post-extraction Unicode print and the first native probe's environment
key lookup failed; both diagnostic attempts and successful follow-ups are retained in the ledger.

**Disposable cleanup not completed:** automatic approval review rejected the guarded
PowerShell removal with “blocked by policy”. The extracted copy and the two exact UUID
Temp stores remain on disk; paths and required manual cleanup are in
../hackyard/final-feature-verification.json. No AccessMaze desktop remains running.
The original package/ZIP and real AppData history must be retained.

Final verification-tool checks: Ruff check passed and **72 files already formatted**;
TypeScript/ESLint, Prettier, generated contracts and Cargo fmt passed. Engine and React
source remained unchanged from the **112 / 9 passing regressions** recorded below;
verification tools were checked through their actual native executions. No remote CI run.

Remaining limits: bounded root recovery cannot undo external effects or replay prerequisite
form inputs; privately withheld discovery targets require an authored journey for replay;
layout zoom emulates viewport/device scale, not browser chrome/text zoom. Mandatory
independent Windows/NVDA/security/redistribution/signing/remote-CI/overnight/performance
and master-scope gates remain open in ../releases/remaining-actions.md. This is an unsigned
readiness preview, not production-ready or release-qualified.

### Corrected feature source — full regression and first native acceptance

Backend/source **7628688**: `uv run --project engine pytest engine/tests -q
--junitxml=dist/hackyard-verified-tests.xml`: **112 passed in 151.64 s**, including
both reproduced control-state/navigation regressions. No engine source changed afterward.
React after final replay binding/focus/discovery presentation changes: **9 passed in
5.32 s**; TypeScript/ESLint, Ruff/check/format, contracts, Prettier and Cargo fmt passed.
The earlier **1 Rust Windows Job regression** passed; no Rust behavior changed.

Clean intermediate package `AccessMaze-hackyard-verified` at 7628688:
1,702 manifest files, source_dirty=false, frozen Python/bundled Chromium, 782 notices
and existing native MPL sources. `desktop_features.py` actually passed in **19.413 s**:
three approved discovery actions, reusable 125% layout-zoom profile across two projects,
blocked keyboard run, observed-again replay, native-button correction and successful replay.
Actual browser durations **1.336 / 0.974 / 1.385 / 8.798 s**, graph nodes **2 / 2 / 2 / 3**.
Axe on this view: **0 violations**, color-contrast incomplete. Owned projects/profile
removed normally. Raw ../hackyard/native-features-first-{runs,verification}.json. Screenshots
were visually inspected. These records refer to the intermediate UI; final presentation
build and acceptance are recorded above, separately from this intermediate evidence.

Actual native schema-2 → 3 migration retained all **56 original projects / 56 original
run payloads unchanged**. A private pre-upgrade SQLite backup passed integrity_check;
it remains outside the repository. Raw ../hackyard/native-migration-verification.json.
One idle native measurement: **331.32 MiB summed RSS / 3,689 summed handles / 8 children**,
shared pages counted repeatedly; no leak/budget conclusion (native-features-memory.json).

CDP-instrumented desktop 81236 closed its host/worker and port, but three WebView2
processes remained beyond the five-second check. Only the verified orphan tree was
explicitly terminated, and subsequent inspection confirmed exit. Root cause is not
established. A separate **ordinary launch without CDP/browser automation** (PID 54532)
closed **all 8 children** normally. Preserve both results: native-shutdown-investigation.json
and native-nondebug-shutdown.json. Do not call instrumentation retention an independently
verified ordinary-release defect or discard it as irrelevant; repeat during qualification.

Visual review prompted compact historical/live focus tables, explicit step-to-runtime-input
mapping, visible discovery reachability and observed CSS viewport/zoom. Detailed raw
records remain available; no results are fabricated. Final UI package/crash/portable/demo
verification is recorded above. Independent NVDA, legal/security, signing, clean-machine,
remote-CI, overnight and performance-budget gates remain open.

### Verification correction — checked-state deduplication

A new actual Chromium regression initially failed: toggling a discovered checkbox produced
the same focus-normalized coverage key as its unchecked state. Observation capture omitted
checked/expanded/selected state. Fixed DOM checked/expanded/selected evidence and bounded
AX checked/expanded/selected/disabled/pressed enum evidence; arbitrary ARIA values are not
captured. The UI exposes actual computed control state.
A subsequent real multi-page test also exposed observation racing a document navigation:
the approved link passed but DOM capture's context was destroyed. Evidence capture now
retries only transient navigation/context failures within bounded attempts, checks document
epoch across DOM/AX capture, and never retries the interaction. A real Chromium regression
navigates between DOM and AX collection and verifies a consistent new-document snapshot. This prevents focus normalization
from silently merging checked and unchecked controls. Native verification must use the
subsequent build, not the intermediate clean 8c3b586 package.

The serial full suite before this final regression passed **110 tests in 170.31 s**.
An earlier concurrent-build run had **108 passed / 2 recorder startup-wait failures**
(346.09 s); a repeated React run also exceeded the existing 5-second comparison-test timeout.
Both recorder tests passed in the serial full run without changing their deadlines.
Resource contention is a plausible explanation, not an established diagnosis or a claim
of stability under arbitrary load. After the control-state/navigation fixes:
`pytest engine/tests/test_website_exploration.py -q`: **7 passed in 19.02 s**;
React **9 passed in 7.04 s**; type/lint/format/contracts passed. Updated ADR 003 records
the decisions. Subsequent full-suite/native/package checks are recorded above.

### Remaining-feature milestones 2–3 — implementation and browser verification

Historical/live failure reproduction now selects an actual stored finding, displays the
original step/state/focus trace, prepares the historical authored definition with fresh
runtime bindings, and requires new target/action authorization before real re-execution.
Original evidence is immutable; new runs retain source/finding provenance and conservative
observed-again/not-reproduced/inconclusive verdicts, with old/live step and focus comparison.
Private discovery targets cannot be reconstructed; those findings require an authored journey.

A persistent editable profile library now reuses condition snapshots across journeys.
SQLite schema 3 preserves older projects, runs and retests; backups include profiles.
Actual execution supports keyboard/pointer, viewport, motion, request delay, recorded
scheduled offline/recovery, final semantics audits and exact completion-focus assertions.
Layout zoom is explicitly viewport/device-scale **emulation**, not browser chrome zoom.
Run-history comparison shows both profile snapshots and actual outcomes; changed profiles
cannot verify a repair. Recovery marks interrupted discovery actions, clears stale proposals
and keeps the observed graph/frontier. Selecting a graph state no longer falls back to an
unrelated finding's screenshot.

Verification to this point:

- Full Python suite: **108 passed in 180.54 s** before the final migration/authorization regressions.
- Focused final replay/profile/lifecycle/storage checks: **15 passed in 24.18 s**, including
  genuine Chromium replay/correction/cancellation, input redaction, profile-dependent
  blocked/completed outcomes, actual offline/motion/zoom/audit/focus evidence, schema 1/2
  migration, stale crash approval cleanup, and cross-project/effect authorization rejection.
- Discovery checks after recovery deduplication: **5 passed in 16.31 s**.
- React: **9 passed in 16.60 s**, including recorded-state screenshot selection; TypeScript/ESLint, Ruff, contracts/format and **1 Rust Windows Job test** passed.
- Native feature acceptance script implemented against an owned HTTP target; latest packaged
  runtime, crash regression and native execution are **pending**, not inferred from development tests.

A simulated version-1 migration test initially retained the new profiles table and failed.
The test now constructs the genuine old schema; separate version-2 migration is covered.
No external target, authorization policy or distribution dependency was relaxed. This work
is workstation continuation after 8e074e7; no onsite/NVDA/independent qualification is claimed.
See ../hackyard/remaining-features.md for exact usage and current limits.

### Remaining-feature milestone 1 — approved branch recovery

Continuation baseline is **8e074e7**. Website discovery now uses deterministically
ordered computed accessible names for buttons, links, checkboxes and radios.
Opt-in root recovery requires its own fresh approval; it never automatically replays
forms or reverses server effects. Focus-normalized coverage keys avoid retrying the
same named action after approved recovery, while graph observations retain focus.
Earlier unvisited alternatives remain persisted, including when bounds stop exploration.
Executed actions retain keyboard reachability and focus evidence. Unknown paths are
not classified inaccessible. Candidate and AX limits are reported explicitly.

Actual local command: `uv run --project engine pytest engine/tests/test_website_exploration.py -q`:
**5 passed in 16.42 s**, including real multi-page and history-SPA branch recovery,
blocked unapproved destructive action, stale approvals, cancellation and persistence.
Native verification, packaging and broader regression checks for this increment remain pending.
This is workstation continuation, not claimed onsite development. Independent release gates remain open.


### Competition outcome milestone — native verification complete for this increment

Application source **504774a**, built clean as `dist/AccessMaze-competition-startup`;
source_dirty=false. **1,702 manifest-hashed files**, 782 collected notices and native MPL
sources retained; no dependency or security-policy relaxation. ZIP **389,992,385 bytes /
1,703 files**, CRC passed, SHA-256 **1313d9ddd959b90e9d419c19fcc9a9aa34a80703d737ec142681aa8d9d77aaa9**.
Raw artifact record: `../hackyard/preview-artifact-verification.json`. Later demo/test-tooling
and documentation changes do not alter this packaged runtime. This unsigned ZIP is a
locally tested preview, not independent release qualification.

Actual final verification:

- `uv run --project engine pytest engine/tests -q`: **102 passed in 122.19 s**, including the reproduced cold-start regression after its fix.
- `npm run check`, `npm test` (**6 tests**), `npm run format:check`, contracts, Ruff/check/format (**66 files**), Cargo fmt and locked Cargo test (**1 Windows Job test**) passed. Frontend/release build passed in packaging. Remote CI and NVDA remain unexecuted.
- `Test-AccessMazePortable.ps1 -Package ./dist/AccessMaze-competition-startup -Report ...`: all file hashes, frozen worker/bundled Chromium, three expected fixture outcomes, exports/EOF, System32-only PATH passed; worker startup **0.558 s**. Raw `../hackyard/portable-startup-verification.json`.
- `portable_smoke.py --package AccessMaze-competition-startup --complex --report ...`: three fixture outcomes and real owned 19-step HTTP SPA/upload passed, expected exact single upload/bytes asserted; worker **0.471 s**, complex run **5.425 s**. Raw `../hackyard/complex-portable-verification.json`.
- `desktop_comparison.py`: actual native WebView2/IPC/Chromium target, observed keyboard failure → correction → completion; Enter activates comparison, first divergent step is continue, passed keyboard retest, baseline inspection hides stale comparison. Axe **0 violations**, color-contrast incomplete. Unique passing project removed. Raw `../hackyard/native-comparison-verification.json`; screenshot `screenshots/journey-comparison.png` visually inspected.
- The first post-fix harness attempt reached both actual expected outcomes, then failed because an exact wrapped-label selector included option text. Fixed the harness selector to use the label prefix; the entire sequence reran successfully. This was a harness defect, not a product failure. Actual cancelled/pre-comparison failed-attempt records are preserved in `../hackyard/native-validation-attempts.json`; only the explicitly owned disposable projects were subsequently removed.
- `desktop_smoke.py`, `desktop_website_smoke.py`, `desktop_readiness.py`: native fixtures/light+dark axe (0 violations, contrast incomplete), per-action approval/one POST/no external replay, headed recorder/H1 capture, keyboard heading focus, safe schema errors/input retention and dialog focus all passed.
- `desktop_crash.py` on the exact new executable: actual worker restarted, interrupted run persisted and **4 Chromium descendants** cleaned. Raw `../testing/desktop-crash.json`. Native GUI PID 42220/eight children subsequently closed.
- Three actual native launches with System32-only PATH: connected UI **3.859 / 2.680 / 2.616 s**, ready summed RSS **445.31 / 440.37 / 443.82 MiB**. Archive compression ran concurrently; load/cache uncontrolled, no performance-regression or budget conclusion. All owned descendants closed. Raw `../hackyard/native-startup-verification.json`.
- Both checker-created temporary stores removed after validating their exact UUID paths; no matching desktop remained and ports 9224/9227 were closed. User AppData otherwise retained. Raw `../hackyard/owned-cleanup-verification.json`.

The strengthened demo additionally executes an **isolated initial-page axe audit** before
attempting the broken keyboard task. Actual current run: **0 axe violations / 0 incomplete
rules**, initial heading assertion passed; the keyboard journey then blocked at validate.
The native-button correction completed, its comparable retest passed, one 25-byte upload
occurred, and a separate offline/online form-state-loss assertion blocked as expected.
`pytest engine/tests/test_hackyard_demo.py -q`: **1 passed in 18.28 s** after this final
script-only enhancement. Standalone command `hackyard_demo.py --output
dist/Hackyard-competition-evidence` also passed; actual summary
`../hackyard/demo-competition-verification.json`. This is evidence of this isolated check
set versus this task, not an assertion that every accessibility check or WCAG criterion passed.

**Broader competition mission remains open:** reusable named profile library/true browser
zoom, expanded semantic/goal-directed discovery with appropriately authorized branching,
and dedicated historical-versus-live failure replay still need implementation and acceptance.
Existing narrower implementations remain documented in `../hackyard/gap-assessment.md`.
The nine requested materials and local document links were checked; onsite achievements
remain unclaimed. Independent release gates in `../releases/remaining-actions.md` remain
open. This increment does not establish competition completion or public-release readiness.


### Native validation exposed a cold-start readiness blocker — corrected

Clean milestone source **e84b34e** packaged as `dist/AccessMaze-competition-outcomes`.
Frozen PowerShell integrity/system-PATH/three-fixture/export checks passed, startup
**0.582 s**, source_dirty=false. Actual report: `../hackyard/portable-outcomes-verification.json`.
The first native comparison attempt instead failed before analysis navigation with
**Run initialization timed out**. Its saved run was cancelled before browser execution
(duration 0.011 s measured after the old environment initialization). This is a failed
native gate, not a passed result. A first checker invocation used wrong argument names;
corrected `-Package`/`-Report` invocation above passed. No application defect is inferred
from that command error.

Investigation found environment/version collection preceding both the first persistence
and the worker ready signal. A deliberately delayed OS probe reproduced the exact timeout:
`pytest engine/tests/test_worker.py::test_run_initial_record_is_available_before_slow_environment_probe -q`
**failed in 5.65 s before the fix**. Runner now persists a complete preparing record and
signals readiness before environment collection. Worker polling/cancellation can operate
while inspection finishes. The elapsed execution budget includes that work, with a check
before browser preparation. A blocked OS inspection itself cannot be forcibly cancelled
within Python; worker/Job termination remains the recovery boundary.

The new regression plus worker/browser/Hackyard focused suite passed **17 tests in 35.73 s**;
Ruff check and all **66 files** format check passed. Full-suite repetition and new clean-source
native verification are pending below, rather than attributing the older package's results
to this fix. Added `scripts/desktop_comparison.py` exercises actual UI/IPC/browser failure,
correction, keyboard-operated comparison, stale-state hiding, axe and uniquely owned cleanup.
The initial failed native GUI PID 54316 and its descendants were closed; zero remained.


### Hackyard mission milestone 1 — task outcomes and conservative comparisons

Baseline inspected clean at **9f3222a**. Targeted assessment and measurable remaining
feature gaps are in `../hackyard/gap-assessment.md`. Existing architecture and design
system are preserved. This milestone does not complete the larger competition mission.

New runs persist explicit derived task outcomes and mandatory assertion results on
progress saves. Exports and comparisons derive the same meaning for legacy records.
A confirmed failed required step blocks completion; missing assertions remain incomplete;
unknown browser failures and compromised coverage remain inconclusive. Optional/audit
findings do not automatically mean the task failed. Completion is not conformance.

Comparison now aligns stable step IDs, reports the first recorded status divergence,
added target identities, outcomes, changed conditions/environment, local state references
and warnings. Exact affected-target sets distinguish axe findings on different controls;
private per-run tokens are never matched as stable identities. Missing audit evidence
cannot verify an axe repair. A changed journey/order/environment remains descriptive,
not verified repair. Actual Chromium regression confirms the same rule on two different
controls is not incorrectly labeled persistent. See `../hackyard/comparison-rules.md`.
The React history workspace shows these records and prevents stale comparison rendering
when the selected run changes. Its keyboard-driven regression uses actual rendered controls.

The reproducible demo additionally exports a real engine run of a controlled form losing
its draft after Chromium offline/online events. Its assertion fails with form-state-lost;
this is explicitly browser emulation, not a physical network-adapter test. The original
owned HTTP failure/correction/upload and scripted recorder replay remain intact.

Actual commands/results:

- `uv run --project engine pytest engine/tests -q`: **101 passed in 144.67 s**.
- `npm test`: **6 passed** across three files after adding comparison keyboard/stale-state regression.
- `npm run check`, `npm run build`, `npm run format:check`, Ruff check/format and contracts check passed; type/lint and formatting repeated after the new UI test passed.
- Focused outcome/retest/report/browser batch: **20 passed in 18.74 s**; demo/comparison/outcome/retest batch: **10 passed in 29.82 s**.
- Standalone current-engine demo output: `dist/Hackyard-competition-outcomes`; actual summary is `../hackyard/demo-outcomes-verification.json` (blocked → completed, comparable passed keyboard retest, separate blocked draft-retention assertion, one 25-byte POST).

All nine requested Hackyard documents now exist, with publisher-backed competitor
research, a dated pre-mission boundary and an onsite ledger that claims no onsite work.
No exclusivity, competition eligibility, human NVDA or independent release claim is made.
Native integration of the changed runtime/UI is **pending a new clean-source build**;
the previous 228ad9c package does not verify this milestone. Reusable profile library,
broader discovery and dedicated failure replay remain outstanding in the gap assessment.


### Release-validation continuation — verified locally; qualification still blocked

Final application/package source **228ad9c**, built clean with `package_windows.py
--name AccessMaze-release-validation-final`. Manifest: **1,701 hashed files**, dirty=false,
including 782 collected original notices and five byte-verified MPL crate source archives;
standalone FFmpeg omitted. Final ZIP: **390,002,137 bytes / 1,702 files**, CRC passed,
SHA-256 **51d72674db90ff92feb06bf46d8aedd8991a2c9662f7c9e0cb5a3ebc9e3c180e**.
Record: `../releases/release-validation-artifact.json`. Subsequent verification-tooling
and documentation changes do not change this tested application runtime.

Actual verification commands/results:

- `uv run --project engine pytest engine/tests -q`: **94 passed in 99.38 s** after final license-scope regression. Earlier 90/92/93 runs remain recorded; no fabricated combined-suite result.
- TypeScript/ESLint, **5 React tests**, frontend production build, Ruff/check/format, contracts, Cargo formatting and **1 Windows Rust Job test** passed. Actual actionlint 1.7.7 validated `.github/workflows/ci.yml`; remote CI remains NOT RUN.
- `extended_stability.py --seconds 600 --output dist/stability-committed`: **607.26 s**, **11 persistent-worker journeys + 11 × 32 passing regression executions**, SQLite integrity/report/artifact deletion passed, zero surviving children at cycle boundaries. Engine hashes/selected regression code unchanged; unrelated notice tooling/docs changed later, explicitly recorded. Peak summed harness/children **704.16 MiB / 4,050 handles**; idle parent **64.47 → 42.85 MiB / 258 → 255 handles**. Not overnight or native UI soak/no-leak proof. Raw: `../testing/stability-committed.json`.
- `Test-AccessMazePortable.ps1` on final folder: integrity, system-only PATH, frozen Python/bundled Chromium, three expected fixture outcomes, exports/EOF passed; startup **0.656 s**. A freshly extracted ZIP passed the same check; its application directory and synthetic checker storage were removed. Same development workstation, not independent installation/removal. Raw: `../releases/extracted-zip-*.json`.
- Real `portable_smoke.py --complex` through a Unicode package junction alias and ordinary Unicode temporary storage: fixture outcomes plus 19-step SPA/actual multipart upload passed, expected single POST/bytes and connectivity limitation verified; startup **0.582 s**, complex run **4.650 s**. Alias/temp storage removed. Raw: `../releases/unicode-portable-smoke.json`.
- Final executable `desktop_smoke.py`, `desktop_website_smoke.py`, `desktop_readiness.py`: native fixture journeys, light/dark axe (contrast incomplete), per-action approval/one owned POST/no replay, visible recorder, heading/dialog focus, private actionable error and input retention passed. Design/source UI unchanged; actual screenshots updated.
- `desktop_crash.py` repeated **3 times** on the exact final executable: worker restarted, run interrupted, **4 Chromium children cleaned each time**. Raw: `../testing/repeated-native-crashes.json`. Owned GUI PID 52380/8 children closed; test ports verified closed.
- Three additional native launches inherited **SystemRoot/System32-only PATH**: connected UI **1.337 / 1.297 / 1.262 s**, ready summed RSS **438.74–442.37 MiB**, owned cleanup passed. Initial measurement harness close failed on bare `powershell` lookup under stripped PATH; owned PID 48892/8 children explicitly cleaned. Corrected absolute system helper path/fallback, reran successfully. This was a harness defect, recorded in `../testing/desktop-startup.json`.
- Actual existing-child ACL/SQLite startup with 5,000 **synthetic files**: **3.0528 / 2.1570 / 2.0426 s**. Background load uncontrolled; large-history/native UI budgets remain unqualified. Raw: `../testing/permissions-scaling.json`.
- Fresh npm/Python/Rust advisory scans: zero known vulnerability entries; same two informational Rust warnings outside ordinary Windows graph, not a blanket clean all-platform audit. Raw: `../testing/release-audit-*.json`.
- `hackyard_demo.py --output dist/Hackyard-release-validation`: real broken failure, native-button correction, fixed completion, comparable passed keyboard retest, recorded draft/replay and exactly one 25-byte synthetic upload reproduced. No hardcoded findings, human recording or NVDA claim.

All **87 original license/notice flags** have per-row evidence and disposition. Final
ordinary-edge Cargo scope identifies `defmt-parser` as build-graph-only; five other crate
rows retain required-attribution candidates conservatively, without claiming executable
linkage. Both npm inclusion changes and Cargo scope changes have regressions. Original
627-component inventory/73 non-distributed raw flags remain visible. Final basis:
`../legal/license-gap-review-final.json`; packaged inventory/source checks retained.

**Not production-ready or release-qualified.** Exact outstanding actions are in
`../releases/remaining-actions.md`: independent fresh-user/clean Windows/offline/upgrade
and removal, real human NVDA/manual evaluation, completed remote Actions, independent
security/redistribution review, browser/Microsoft/axe source-rights provenance, verified
binary SBOM, signing/authenticated distribution, overnight/native UI stability and
representative performance/master acceptance. No independent audit, AT verification,
WCAG certification, remote CI pass or overnight result is claimed.

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

### Internal security follow-up — reproduced failures corrected

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

### License gap investigation — original 87 rows classified

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

### Final readiness preview — verified locally, release gates open

Built `dist/AccessMaze-readiness-preview-final` from clean source **207a09a**, preserving
all previous previews. `package-manifest.json`: **1,690 hashed files**, dirty=false.
Frozen verification explicitly asserts that the new in-flight connectivity limitation
is present in saved/exportable run evidence. Actual final commands/results:

- `uv run --project engine python scripts/package_windows.py --name AccessMaze-readiness-preview-final`: native release host, frozen Python worker, freshly installed full Chromium/headless shell, dependency inventory/notices and exact browser credits built successfully.
- `powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package dist/AccessMaze-readiness-preview-final -Report docs/releases/readiness-final-powershell.json`: hashes/path containment, system-only PATH, three browser fixtures, report identity and EOF passed; worker startup **0.718 s**.
- `uv run --project engine python scripts/portable_smoke.py --package AccessMaze-readiness-preview-final --complex --report docs/releases/readiness-final-smoke.json`: three fixtures plus 19-step HTTP SPA/upload passed expected outcomes, coverage uncompromised, exact uploaded bytes/one POST and persisted connectivity limitation asserted; worker startup **1.669 s**. Concurrent checks/archive and laptop load produced fixture durations **18.657–26.355 s**, complex run **29.350 s**. This variability is retained, not presented as a performance-budget pass.
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

### Readiness follow-up — in-flight connectivity scope

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

### Readiness milestone 4 — frozen and native Windows revalidation

Built `dist/AccessMaze-readiness-preview` with
`uv run --project engine python scripts/package_windows.py --name AccessMaze-readiness-preview`.
Manifest records clean source `fcd95a8`, **1,690 hashed files**, 775 collected notices,
readable axe source, offline procedures and exact full Chromium credits. Earlier packages
are preserved. Native host compiled successfully; PyInstaller warned about optional
`tzdata`, which is not used by the tested UTC timestamp paths. No all-feature freeze claim.

Executed actual packaged checks:

- `powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package dist/AccessMaze-readiness-preview -Report docs/releases/readiness-portable-powershell.json`: integrity/path containment, system-only PATH, three real fixtures, exports and EOF passed; worker startup **0.662 s**.
- `uv run --project engine python scripts/portable_smoke.py --package AccessMaze-readiness-preview --complex --report docs/releases/readiness-portable-smoke.json`: three fixtures plus 19-step owned HTTP SPA passed expected outcomes, with exact actual uploaded bytes/one POST and uncompromised coverage; worker startup **0.713 s**. These independent processes ran concurrently on the same laptop, not independent machines.
- `uv run --project engine python scripts/desktop_startup.py --package AccessMaze-readiness-preview`: three native launches reached connected UI in **4.395 / 1.572 / 1.534 s**, ready summed RSS **437.70–447.93 MiB**, each owned process tree closed. Existing synthetic history, uncontrolled cache, CDP/poll overhead included.
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
| Finding accuracy | Confirmed false positives/negatives corrected with browser regressions; latest full engine suite 94 passed. Native semantics/axe do not prove AT behavior or exhaustively clear findings. |
| Hackyard differentiation | Real failure, evidence, native-button correction, comparable retest and recorder draft replay reproduced; synthetic owned target only. |
| Windows performance | Startup/browser/RSS/handles/backend graph/reports measured locally. 607-second persistent-worker/352-regression run and repeated native crash checks passed. Overnight/native UI soak, UI graph scaling and representative budgets NOT RUN. |
| Security | Local source/ACL/credential/retention/origin/isolation/integrity review complete; inherited/explicit child ACL and private diagnostic/frame defects fixed with regressions. Independent threat-model, bootstrap diagnostics privacy and hostile-target containment clearance OPEN. |
| Dependencies/distribution | 627-component inventory, collected notices, exact full-browser credits and advisory scans complete. all original 87 flags classified; notices and five byte-verified native MPL source archives delivered. Verified binary SBOM/browser/source-rights obligations remain OPEN. |
| Portable runtime | Fresh frozen/native/system-PATH tests passed on this developer laptop. Independent clean Windows installation/upgrade/removal/offline qualification NOT RUN. |
| Human accessibility | Documented NVDA procedure; actual human NVDA/high contrast/manual evaluation NOT RUN. Requires a human tester. |
| CI / authenticity | Windows CI not executed remotely; package unsigned, authenticated public distribution/signing unverified. No upstream push or publication performed. |

This environment has no independent Windows machine/image or human NVDA tester.
Those external prerequisites prevent release qualification. Distribution clearance needs
the documented matching-source/rights review. These unresolved gates must remain open;
the locally verified artifact is an **unsigned development preview**, not production-ready.

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

### Readiness milestone 3 — redistribution audit

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

- External exploration supports approved semantic branches and optional approved root navigation; exhaustive coverage, unreachable-state proof and resume after crash remain absent.
- Recording supports a reviewed subset. Preconditions, arbitrary zoom and advanced pointer profiles remain; runtime uploads are supported.
- Real assistive-technology integration, manual NVDA/high-contrast/keyboard evaluation and full UI performance testing remain.
- Retests are narrow; human annotations and a full finding lifecycle remain.
- Broader non-HTTP containment and comprehensive security review remain; DNS is now pinned for approved hosts.
- Literal journey inputs remain plain text; credentials must use run-only bindings. Redaction is best effort.
- Corruption recovery UI, large-history pagination and virtualization remain.
- The unsigned portable build was tested on this Windows machine with developer tools removed from PATH. Clean-machine installation, upgrade/removal, signing, complete third-party license manifest and SBOM remain unverified.
- CI is configured but has not run on GitHub. No upstream push or publication occurred.

## Next release actions

Follow `../releases/remaining-actions.md` for mandatory qualification evidence. Prioritize independent Windows/NVDA/security/rights review, authenticated CI/signing and sustained native/manual performance acceptance. Remaining major authoring/profile/finding-lifecycle features belong to the documented roadmap and master acceptance review; this continuation did not rewrite functioning components or silently mark them complete.

The current environment provides one existing Windows developer machine and no
independent clean Windows installation or human assistive-technology evaluation.
Those release gates cannot be established by the automated tests above.

No full-spec completion, WCAG conformance or release-readiness claim is made.
