# Engineering status

Updated 2026-10-11. AccessMaze is an unsigned readiness preview. It is not
production-ready or release-qualified. The current engineering continuation begins
at clean `c634573`; preserve the earlier milestone history below.

## Repository review and post-merge recorder correction

### Interrupted-navigation context cleanup

Final-main [run 38115447841](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38115447841)
at `473eb93` failed Windows: **134 passed, 1 failed, 363.25 s**. Ubuntu passed
**128 tests, 7 skipped, 202.59 s**; packaging was skipped. All five separate Windows
cancellation executions passed before the full-suite failure. Diagnostic timestamps
show cancellation reached `browser.close()` after **29 ms**, but that call had not
returned after the ten-second thread join. Driver shutdown had not started. The
successful PR #3 run does not resolve this subsequent main-branch failure.

The recorder created an explicit context but left it open until browser shutdown.
[Playwright's browser-close documentation](https://playwright.dev/python/docs/api/class-browser#browser-close)
recommends closing explicitly created contexts first. A real headed Chromium
regression observed **one open context at browser close** and failed before the
change (`pytest engine/tests/test_recorder.py::test_recorder_stop_cancels_slow_initial_navigation
-q`: **1 failed, 4.22 s**). This establishes the ownership-order defect, not the
internal cause of the intermittent hosted stall.

Recorder cleanup now closes its context before the browser, retaining browser
cleanup in a nested `finally` if context cleanup raises. Both remain within the
live Playwright driver scope. Origin restrictions and cancellation limits are
unchanged. The test observes actual context/browser/driver calls, requires zero
contexts at browser close and retains the three-second stop bound. Context-close
timestamps distinguish a future context stall from a browser/driver stall.

Initial local verification: `uv run --project engine pytest
engine/tests/test_recorder.py -q`: **4 passed, 9.43 s**. After adding context-stage
instrumentation, the same suite passed **4 tests in 15.89 s**, with JUnit output
`dist/Context-cleanup-recorder.xml`; the full suite was running concurrently. Ruff
lint/format, contract validation and `git diff --check` passed. Further local and
hosted results must be recorded before
treating this candidate as a verified correction. This is an internal review;
independent Windows, NVDA, signing, legal and overnight gates remain open.

Fresh full-suite verification at `d9a3656`: `uv run --project engine pytest
engine/tests -q --junitxml=dist/Context-cleanup-full.xml` with real Chromium,
`ACCESSMAZE_CORPUS_PA11Y=1` and `ACCESSMAZE_CORPUS_OUTPUT=dist/Context-cleanup-corpus`:
**135 passed, 324.02 s**. Ten additional separate slow-navigation executions passed
with distinct `dist/Context-cleanup-repeat-*.xml` reports, stopping on first failure;
none failed. `npm run check` and `npm run format:check` also passed. The later context
timestamp instrumentation was exercised by the recorder suite and those repetitions.

`scripts/package_windows.py --name AccessMaze-context-d9a3656` built a fresh frozen
package; its manifest records full source `d9a365673edc9620cfd88af54a94ec9c766dab7c`
and `source_dirty: false`. `Test-AccessMazePortable.ps1` and
`portable_smoke.py --complex` passed integrity/frozen runtime/System32-only PATH and
temporary working-directory checks. Startup **0.303 s**; accessible, broken,
conditional and owned-SPA runs **1.638 / 2.291 / 2.501 / 5.460 s**, expected finding
counts **0 / 1 / 0 / 0**. These are uncontrolled same-laptop observations, not budgets.
Reports: `dist/Context-cleanup-portable.json`, `dist/Context-cleanup-complex.json`.
`archive_preview.py` passed ZIP CRC checks: **1,707 files, 390,025,055 bytes**,
SHA-256 `8bae625aada5b205bf2e231c188549d9604c6a503ec95a86c3e3ea012abcd126`.
The unsigned local archive retains clean `d9a3656` provenance; this is not a
bit-for-bit reproducibility or independent clean-machine result.

`launch_preview.py --package AccessMaze-context-d9a3656` and
`desktop_website_smoke.py --endpoint http://127.0.0.1:9224` passed actual packaged
WebView2/IPC/Chromium approval and headed recorder completion/stop. Exactly one
approved POST occurred; the owned project was removed. Normal owned desktop close
left **zero of eight** observed child processes. Original screenshot and raw native
report were restored byte-for-byte; fresh evidence is under
`dist/Context-cleanup-native`. No other process was closed.

`hackyard_demo.py --output dist/Context-cleanup-hackyard` passed actual broken/fixed
journeys, verified-improvement comparison and recorded-draft replay. The controlled
server observed one approved POST and a 25-byte upload. These results do not claim
NVDA verification or accessibility certification. Hosted final-head and post-merge
results remain necessary before reporting successful delivery.

[Final-head run 38127805981](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38127805981)
at `0952bf1` failed Windows: **134 passed, 1 failed, 364.35 s**. Ubuntu passed
**128 tests, 7 skipped, 195.19 s**; packaging was skipped. All five slow-navigation
repetitions and the full-suite slow-navigation regression passed. This time the
ordinary headed recorder lifecycle test found the thread alive after its unchanged
eight-second join. Explicit context cleanup is therefore insufficient to establish
reliable shutdown; PR #4 remains unmerged. The previous superseded run at `d9a3656`
passed Windows Python (**135 tests, 390.47 s**) but was cancelled during Rust checks
by the documentation push, so it is not an all-jobs pass.

Both real headed tests now share the actual Playwright cleanup observer and retain
their original shutdown bounds. The ordinary lifecycle test records context/browser/
driver stages too. `DEBUG=pw:browser` is enabled only for these owned synthetic tests
to distinguish Chromium process exit from temporary-profile cleanup in a future
failure; no credentials or real user pages are used. Windows CI repeats both tests
five times, stopping on first failure. This is diagnostic coverage, not another
application fix or automatic retry. Local `pytest engine/tests/test_recorder.py -q
--junitxml=dist/Context-cleanup-lifecycle-diagnostics.xml`: **4 passed, 14.39 s**.
Ruff lint/format passed. The hosted recorder lifecycle defect remains a delivery
blocker regardless of the successful local package and demo checks.

PR #1 was squash-merged as `91e0e7fada546ed9129ca25b211675d9b4fdc3d8` after
rechecking its unchanged head `05a34a5`, completed green CI and fresh local checks.
Tag `pr-1-reviewed-2026-10-11` preserves all eleven original PR commits and the
`9f3222a`, `8e074e7`, `c634573` technical boundaries. The merged tree matched that
tag exactly; the PR branch was retained and the default branch remained `main`.

All 217 tracked files, ignored/untracked inventory, script purposes/references,
Markdown targets and screenshot hashes were reviewed. No tracked generated-file
candidate, missing Markdown file target or byte-identical screenshot duplicate was
found. A targeted private-key/GitHub/cloud-token scan found no matching patterns;
this is not an exhaustive secret audit. No justified deletion, move or ignore change
was identified. Cleanup classifications:

| Candidate | Decision and basis |
| --- | --- |
| Safe tracked deletion | None confirmed; filename, age and size alone were not used |
| Runtime/build/cache/browser/package/database/log outputs and raw local JSON | Keep locally, already ignored; no local deletion attempted |
| Historical verification/legal inventories | Retain distinct baseline/provenance; no consolidation justified |
| Source, tests, fixtures, migrations, lockfiles, contracts, ADRs, security/legal notices, Hackyard materials, screenshots and release scripts | Retain; references and purposes checked |
| Ambiguous deletion | None attempted; no confirmation needed |

Fresh pre-merge verification: TypeScript/ESLint/Prettier, production frontend build,
Ruff lint/format, contracts, React **13 passed**, Rust **1 passed**, Python
**135 passed in 370.35 s** including Chromium/Pa11y. npm/Python advisories passed;
the local editable engine could not be audited through PyPI. Cargo retained its
two documented warnings. All seven native feature/comparison/readiness/website/
investigation/cancel/crash scripts passed, including three approvals, headed
recording, separate manual-plan export and persistence. Native close left zero of
eight observed children. Frozen portable/complex checks and the actual Hackyard
failure/fix/retest passed. New raw evidence is under ignored `dist/Premerge-*`;
earlier local JSON and tracked screenshots were preserved and restored.

[Post-merge run 38107753260](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38107753260)
passed Ubuntu (**128 passed, 7 skipped, 195.01 s**) but failed Windows
(**134 passed, 1 failed, 348.43 s**); packaging was skipped. The existing recorder
slow-navigation test measured shutdown **7.413 s**, exceeding its unchanged
three-second assertion. This is retained as a failure, not relabeled as a green run.

Inspection and a deterministic real-Chromium regression reproduced incorrect
resource ordering: the recorder exited its Playwright driver scope with Chromium
still connected, then attempted browser cleanup outside that scope. The regression
failed with `[True]` before the fix. Browser cleanup now runs in an inner `finally`
while the driver is usable, matching the journey runner's ownership order. The
three-second assertion remains; the test server also tolerates the expected Windows
connection-aborted exception during cancellation. All four recorder tests passed
in **10.78 s**, followed by **ten passing slow-navigation repetitions**. This does
not establish overnight stability or resolve the earlier WebView2 retention gate.

Commands: `uv run --project engine pytest engine/tests/test_recorder.py -q
--junitxml=dist/Recorder-shutdown-fixed.xml`; ten separate invocations of
`pytest engine/tests/test_recorder.py::test_recorder_stop_cancels_slow_initial_navigation -q`
through the same uv environment, with distinct JUnit files; Ruff lint/format and
`python scripts/contracts.py --check` passed. The before-fix regression result is
retained as `dist/Premerge-recorder-before-fix.xml`.
The full corrected suite then passed: `uv run --project engine pytest engine/tests
-q --junitxml=dist/Recorder-fix-full.xml`, with `ACCESSMAZE_CORPUS_PA11Y=1` and
distinct `dist/Recorder-fix-corpus` output: **135 passed in 337.21 s**. The actual
owned-browser corpus and headed recording tests ran; no browser tests were mocked
or skipped on this Windows run. Source changes remain limited to recorder ownership,
its real-browser regression and this record.

The follow-up source and its final hosted conclusions are separately tracked by
[recorder correction checks](https://github.com/Rhythm-Sanghi/AccessMaze/actions?query=branch%3Acodex%2Frecorder-shutdown).
The failed `91e0e7f` run does not verify the correction; later results require their
own completed checks and exact source/artifact provenance.

The ordering fix is not sufficient to qualify recorder shutdown. Final-main
[run 38111832499](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38111832499)
at `1dab8aa` passed Linux (**128 passed, 7 skipped, 195.47 s**) but failed Windows
(**134 passed, 1 failed, 363.40 s**); packaging was skipped. The same slow-navigation
test found the recorder thread alive after its ten-second join. This is an unresolved
hosted Windows lifecycle defect despite the successful correction PR/local runs.
The next diagnostic records monotonic browser-close and driver-exit stages through
the actual Playwright APIs. Windows CI now executes the existing cancellation test
five times before the full suite, stopping on the first failure; it is not an automatic
retry. The three-second bound, thread termination and connection-order assertions
remain unchanged. No further application fix is claimed before the stalled stage
is identified and independently exercised by a completed hosted run.
Local diagnostic check: `pytest engine/tests/test_recorder.py -q
--junitxml=dist/Recorder-cleanup-diagnostics.xml` through uv: **4 passed, 10.81 s**;
Prettier, Ruff lint/format and `git diff --check` passed. Application code is unchanged
in this diagnostic step.

Resumed repository review: GitHub confirms PR #1 remains merged at `91e0e7f`;
remote `main` remains `1dab8aa`, and the working tree was clean. The unpublished
`2d8000b` commit contained the repeated CI check and the preceding status entry,
but its intended test instrumentation had been removed during concurrent editing.
That commit is preserved. Browser-close/driver-exit instrumentation is now restored
on `codex/recorder-shutdown-diagnostics`, using actual Playwright calls and reporting
only stage names and monotonic timestamps. Fresh recorder verification:
`uv run --project engine pytest engine/tests/test_recorder.py -q
--junitxml=dist/Recorder-resumed-diagnostics.xml`: **4 passed, 8.73 s**.
This does not resolve the intermittent hosted failure. No application behavior,
shutdown bound, origin policy or assertion has been weakened.

Fresh local checks at `45f348c` passed: Python **135 passed, 331.03 s** with real
Chromium and locked Pa11y corpus (`ACCESSMAZE_CORPUS_PA11Y=1`,
`ACCESSMAZE_CORPUS_OUTPUT=dist/Resumed-corpus`, JUnit `dist/Resumed-full.xml`);
React **13 passed, 41.89 s**; Rust **1 passed, 0.03 s**. Commands: `npm run check`,
`npm run format:check`, `npm test`, `npm run build`; Ruff lint/format; `python
scripts/contracts.py --check` through uv; Cargo check/fmt/test with the locked
desktop manifest. `npm audit --audit-level=moderate` for the application and Pa11y
and `uv run --project engine pip-audit` found no known vulnerabilities (local editable
engine excluded by pip-audit). Cargo audit retained the same two allowed warnings.
Actionlint 1.7.7 and `git diff --check` passed.

Fresh inventory again found **217 tracked files**, no tracked generated candidates,
missing Markdown file targets, byte-identical PNG duplicates or unignored untracked
files. The targeted private-key/GitHub/cloud-token patterns found no matches; this
remains a limited scan. No file deletion or move was justified. Raw inventory is
`dist/Resumed-repository-audit.json`. The remaining-actions package reference and
Hackyard instructions now identify the corrected package and the provenance tag.

The unchanged `1a2809b` frozen package passed `scripts/Test-AccessMazePortable.ps1`
and `scripts/portable_smoke.py --complex`: system-only PATH, temporary directory
with spaces, startup **0.663 s**, accessible/broken/conditional/owned-SPA runs
**2.643/4.499/4.730/6.339 s**, expected finding counts **0/1/0/0**. Reports:
`dist/Resumed-portable.json`, `dist/Resumed-complex.json`. No new package build or
independent clean-machine result is claimed. Existing seven-script native acceptance
above remains applicable because application, UI, contracts and scripts are unchanged.
`scripts/hackyard_demo.py --output dist/Resumed-hackyard` passed actual broken/fixed
journeys, strict repair comparison and recorded-draft replay; the controlled server
observed one approved POST and a 25-byte upload. No screenshots or prior evidence
were overwritten by these resumed checks.

[PR #3](https://github.com/Rhythm-Sanghi/AccessMaze/pull/3) merged at
`cea218b2325d43af124a81db35973ba73f36097b`, preserving the three diagnostic/evidence
commits. Local `main` fast-forwarded without discarding `2d8000b`; the merged tree
matches reviewed head `7f9b603` exactly. No branches, tags or other edits were deleted.
[Final PR run 38113635962](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38113635962)
completed all three jobs successfully: Windows **135 Python passes, 372.80 s**, five
separate cancellation passes, **13 React passes** and **1 Rust pass**; Ubuntu
**128 passes, 7 skips, 194.92 s**. Quality/contracts/build/advisory checks passed with
the two existing Cargo warnings. The earlier diagnostic run `38112976146` was cancelled
by the documentation push after its Python tests passed; it is not a green full run.

Hosted packaging/frozen runtime/System32-PATH/complex smoke/manifest/ZIP CRC checks
passed. Clean synthetic source `838e0fb9be91141d4f6fe337980c0c919eae2217` was fetched
and verified tree-identical to `7f9b603`. Inner ZIP: **389,882,771 bytes, 1,707 files**,
SHA-256 `669d56af9851da0021f6bb92d4907df1ed719f57214227008ef12de2cac5158f`.
[Artifact 11693082697](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38113635962/artifacts/11693082697)
is an unsigned 14-day preview; the distinct outer Actions digest is
`2de65fa5a6bf6f3c1271a3c72ced4052a02345a2d88890a0fb8461ce8413cd3f`.
Frozen startup was **0.493 s**; accessible/broken/conditional/owned-SPA runs took
**2.156/7.337/12.062/19.993 s**, with expected findings **0/1/0/0**. A hosted runner
with development tools does not establish independent consumer-machine acceptance.
The [main-branch workflow](https://github.com/Rhythm-Sanghi/AccessMaze/actions?query=branch%3Amain)
must have its own completed conclusions; the PR run is recorded separately.

The recorder stall remains unresolved. An
[upstream Windows profile-cleanup report](https://github.com/microsoft/playwright/issues/42109)
is an unconfirmed lead, not AccessMaze's established cause. Read-only inspection of
nine leftover local profiles found four relevant cache directories; all four were
readable with inherited permissions enabled. No profile or permission was changed.
Raw inspection: `dist/Resumed-temp-profile-inspection.json`. If the shutdown failure
recurs, retain the browser-close/driver-exit timestamps and inspect that runner's
profile/process state before choosing a fix. No dependency patch, test weakening,
lifecycle resolution or release qualification is claimed by these passing repetitions.

## Current verified implementation

The original investigation acceptance package uses clean source
`432dd5f385aaecbfebb8b36fae28cc439ac1019b`. The later recorder correction is
packaged from clean `1a2809bd5293b47def41d3682e5ee88c926fa39d`, as recorded below.

- Authorized journeys, exact navigation/API versus resource origins, DNS/redirect
  checks, run-only credentials/uploads and private evidence remain in place.
- Explicit named-frame permission, scoped semantic widgets, bounded discovery,
  per-action approval and separately approved root recovery.
- Versioned failure recipes, editable journey drafts and observed task reachability;
  withheld targets and unknown frontiers remain explicit limitations.
- Versioned reusable profiles and bounded serial profile batches. Layout emulation
  is not browser chrome/text zoom or a disability simulation.
- Separate planned/attested human investigation records. No actual NVDA test occurred.
- Database schema 4, paged metadata history and revision-based polling. Existing
  full-run retrieval remains available; unchanged graphs are not repeatedly transferred.
- WAL-aware backup bounds, preserved structural evidence IDs and distinct React
  panel keys fix defects reproduced by real storage/browser/native checks.

## Current local verification

Available laptop: Intel Core i7-1365U, 10 cores/12 threads, 15.66 GiB usable RAM,
Windows 11 build 26220. Background activity and cache state were uncontrolled.

| Check | Actual result |
| --- | --- |
| Full Python suite at clean `10a3fc6` | 134 passed, 296.67 s, including actual Chromium and the locked Pa11y corpus |
| React after duplicate-key correction | 13 passed, 5.19 s |
| Rust Windows Job regression | 1 passed; formatting/checks passed |
| TypeScript/ESLint, Ruff, Prettier, generated contracts | Passed |
| Native approved branches/replay/profile reuse | Passed, 14.539 s; three separate approvals, observed-again then not-reproduced after correction |
| Native strict repair comparison | Blocked → completed; passed-retest; divergent step `continue` |
| Native history/manual/editable draft | Passed, 5.974 s; separate planned-only record/export, four history switches without duplicate panels, draft saves without execution |
| Native keyboard/errors/dialogs | Passed; retained invalid input and restored dialog focus |
| Native website/recorder | One approved POST; actual headed recorder completion capture; no external automatic replay |
| Native cancellation/crash | Cancelled partial node persisted; crash interrupted run and restarted worker; four Chromium children cleaned in each test |
| Replay/comparison UI axe | Zero violations; aria-prohibited-attr and color-contrast remain incomplete, not passes |
| Frozen complex runtime | System-only PATH startup 0.421 s; accessible/broken/conditional/owned-SPA 2.056/2.596/2.551/5.280 s, expected findings 0/1/0/0 |
| Sustained native UI/worker run | 601.33 s; 157 journey/UI cycles, owned history removed, zero owned children after close; six reused PIDs excluded by creation-time identity |
| Portable integrity/Unicode extraction | Manifest, CRC and frozen checks passed on development laptop |
| License distribution regressions | 5 passed, 4.37 s; all 87 original rows reclassified against current 627-component build, zero open original rows; broader redistribution gates remain |
| Sustained worker/browser regression | 1,223.77 s; 24 persistent journeys and 24 × 34 = 816 passing regression executions; no surviving children at cycle boundaries |

The 20-minute worker run began at clean `10a3fc6`; engine source fingerprints stayed
unchanged. Later changes were UI/test-harness/docs/CI, not engine source. Peak summed
harness/test-child RSS 740.88 MiB, handles 4,105. Idle worker RSS 65.32 → 67.41 MiB
(range 44.80–69.68), handles 256 → 251. This is not overnight, a native UI soak or
proof of no memory leak. The separate native sustained run passed as recorded below.

## Current portable artifact

Earlier local archive `dist/AccessMaze-investigation-preview-432dd5f.zip`: **390,039,679 bytes**,
**1,707 ZIP entries**. SHA-256:
`cfb33a28ca777acb801279e666560ec9abc7bddc49e075e9aff05905dc25449c`.
Source is clean `432dd5f`. Bundled Python 3.13.9, Playwright 1.63.0 and Chromium
153.0.8010.12 executed; no developer runtime was needed on PATH. A new Unicode/space
extraction passed frozen checks. These reuse this laptop's Windows/AppData/WebView2
and are not independent fresh-user or clean-machine results. The package is unsigned.

The latest local directory package is `dist/AccessMaze-recorder-1a2809b`, with
manifest source `1a2809bd5293b47def41d3682e5ee88c926fa39d`, dirty=false. Its
portable manifest/System32-PATH check and frozen complex smoke passed:
startup **0.611 s**; accessible/broken/conditional/owned-SPA **2.477 / 4.410 /
3.164 / 6.679 s**, expected findings **0 / 1 / 0 / 0**. Actual native website
approval, headed recorder and completion capture passed through that frozen worker;
one approved synthetic POST, owned project removed, zero of eight children after
close. Raw `dist/Recorder-fix-portable.json`, `dist/Recorder-fix-complex.json` and
`dist/Recorder-fix-native/`; baseline screenshots/local JSON were preserved/restored.
An interrupted packaging attempt before the clean commit was not used as evidence.

[Correction PR run 38108860709](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38108860709)
completed all three jobs successfully: Windows **135 passed, 381.47 s**; Ubuntu
**128 passed, 7 skipped, 169.87 s**; React 13 on each; Rust 1. Quality/advisory
checks passed with the two documented Cargo warnings. Hosted package source is
synthetic merge `43338ffd1932567b2b17a7d23a47168274466feb`; direct fetch/tree
comparison against `1a2809b` returned no differences. Inner ZIP **389,883,227 bytes**,
SHA-256 `f9e8e8ef0e5c98557c4ebe8e90f3cf529c0c68b899c6c7f8bb866caf4cfbb916`.
[Artifact 11691339217](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38108860709/artifacts/11691339217)
is unsigned with 14-day retention. PR #2 is confirmed merged at `1a2809b`.
Later documentation commits require their own completed checks; current final-main
conclusions are recorded in [main Actions runs](https://github.com/Rhythm-Sanghi/AccessMaze/actions?query=branch%3Amain)
and the [PR #2 verification record](https://github.com/Rhythm-Sanghi/AccessMaze/pull/2).

## CI and release gates

[Run 38102629066](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38102629066)
passed Ubuntu but failed Windows's optional scanner; packaging was skipped. Browser
stderr identified sandbox access denied. A narrow cache read/execute correction was
pushed as `81f813d`; [run 38103235350](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38103235350)
completed all three jobs successfully. The PR workflow checks GitHub's synthetic
merge commit `c8474870ba08ae917b12b4f23a8472344f615691`, whose tree matches head
`81f813d` exactly. Its package is clean and unsigned. Subsequent documentation/test
commits require their own completed run; final-head conclusions are linked through
[PR #1 checks](https://github.com/Rhythm-Sanghi/AccessMaze/pull/1/checks).

Open qualification gates: independent Windows/fresh-user/offline/upgrade/removal;
actual human NVDA and zoom/accessibility evaluation; independent security and embedded
binary redistribution review; signing/authenticity; overnight stability and the
unexplained earlier WebView2 retention; reviewed performance budgets/representative
hardware; release-owner master-spec scope acceptance. Human records are implemented,
but this does not complete human verification. Follow [remaining actions](../releases/remaining-actions.md).
Competition eligibility, actual team/tool disclosures and demo-video recording require
the entrant. [Submission handoff](../hackyard/submission.md) contains reviewable copy.

## Historical record before the c634573 continuation

The following October 10 measurements and package claims describe their recorded
commits. They are preserved for traceability and do not supersede the current summary.

### Current implementation

- Authorized browser journeys with keyboard or permitted pointer interaction,
  explicit completion assertions, recording and editable semantic steps.
- Exact origin permissions, DNS pinning, redirect guards, fresh browser contexts,
  run-only credentials/uploads and private website evidence by default.
- Bounded semantic discovery with individual action approval, optional approved
  root navigation, duplicate detection, partial graphs and unexplored frontiers.
- Finding-specific replay using the historical journey, fresh input and new
  authorization. Historical evidence remains separate from live execution.
- Persistent, editable profiles for viewport/layout zoom, motion, request delay,
  connectivity, focus and semantics. Each run retains its condition snapshot.
- SQLite history, partial results, interruption recovery, report exports, backups
  and retention controls. Windows Job objects own worker/browser descendants.

### Verified application source

The latest portable package uses clean source `746eaca94fae91a7749c1ce293ac721bc03f95a4`.
Subsequent changes concern verification tools and documentation.

| Check                                                              | Result                                                                                                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| Python regression suite                                            | 112 passed in 151.64 s; real Chromium included                                                                                        |
| React tests                                                        | 9 passed in 5.32 s                                                                                                                    |
| Rust Windows Job regression                                        | 1 passed                                                                                                                              |
| TypeScript, ESLint, Ruff, Prettier, contracts and Cargo formatting | Passed                                                                                                                                |
| Native feature sequence                                            | Passed in 22.365 s: three approved actions, root recovery, profile reuse across two projects, reproduced failure and corrected replay |
| Native comparable retest                                           | Blocked → completed; passed-retest; first divergent step `continue`                                                                   |
| Native keyboard/error/dialog checks                                | Passed navigation, heading focus, private schema errors, input retention and restored dialog focus                                    |
| Website approval and recorder                                      | One approved POST, no automatic reset/replay; headed recorder completion capture passed                                               |
| Worker crash                                                       | Interrupted run recovered; all 4 Chromium children exited                                                                             |
| Emergency stop                                                     | Cancelled outcome persisted; 1 partial graph node retained; all 4 Chromium children exited                                            |
| Native schema 2 → 3 migration                                      | 56 existing projects and 56 run payloads unchanged; private backup integrity check passed                                             |
| Replay/comparison view axe checks                                  | 0 violations; color contrast incomplete                                                                                               |

Replay focus evidence showed eight unsuccessful Tab presses before correction and
one successful press afterward. This verifies the tested journey, not every keyboard
path or WCAG conformance. NVDA has not been tested.

### Portable package

Local archive: `dist/AccessMaze-hackyard-preview-746eaca.zip`.

- 389,996,150 bytes; 1,703 ZIP entries, including 1,702 manifest-covered files.
- SHA-256: `6165c5693f9e57803cfa88d93c0525c59c3830527331e3aa7c0a3bb1b0ec1a53`.
- CRC and manifest hashes passed. Bundled Python and Chromium worked with a
  System32-only PATH and a working directory containing spaces.
- Frozen accessible/broken/conditional/owned-SPA runs took
  2.483 / 2.487 / 3.032 / 7.013 s, with the expected 0 / 1 / 0 / 0 findings.
- Fresh extraction under a Unicode/space path passed the worker checks and native
  startup. Connected UI took 5.239 s; all nine children exited on close.

These checks reused the development laptop's AppData and WebView2. They are not
independent clean-machine or fresh-user tests. The archive is unsigned and is not
published as a qualified release.

### Performance and stability

Three sequential native startups reached connected UI in 4.746 / 4.028 / 3.720 s,
with summed ready RSS of 448.97 / 446.24 / 441.50 MiB. All eight children exited after
each sample. A later idle sample measured 493.88 MiB and 3,687 summed handles.
Polling overhead, uncontrolled caches and repeated counting of shared pages limit
these measurements; no leak or performance-budget pass is established.

An earlier 607.26-second fixed-engine worker run completed 11 journeys and
11 cycles of 32 browser regressions (352 passing executions), with no surviving
children at cycle boundaries. This was not an overnight or native UI soak.
See [performance procedures](../testing/readiness-benchmark.md).

### Regressions and unsuccessful checks

- Checked-state omission merged checked and unchecked discovery states. Control
  and accessibility-tree enum states are now captured; the Chromium regression passes.
- Navigation between DOM and accessibility-tree capture could destroy the execution
  context. Bounded observation retries and document-epoch checks fixed the reproduced
  case. Interactions are never retried automatically; SPA snapshots remain finite samples.
- Concurrent package builds caused recorder startup waits and a React test to exceed
  existing deadlines. Serial reruns passed without extending deadlines. Resource
  contention is plausible but not established as the sole cause.
- One instrumented `7628688` close retained three WebView2 processes. Its ordinary-launch
  follow-up and final instrumented/ordinary repeats passed. The cause remains unknown.
- Native harness attempts failed on an obsolete checkbox label and an ambiguous stop
  selector. Updated selectors passed against the same package.
- An extraction diagnostic print failed under cp1252; a separate probe failed before
  launch on an environment-key lookup. Follow-up package and native checks passed.

### Security, licensing and release blockers

The [internal security review](../testing/security-review.md) records tested boundaries
and remaining risks. It is not an independent audit. All 87 original license/notice
gaps were classified against distribution evidence; 73 raw metadata flags remain
visible. The [license review](../legal/license-gap-review.md) retains the basis and
outstanding browser/native redistribution obligations.

Root recovery cannot undo external writes or restore prerequisites. Withheld private
discovery targets require an authored journey for replay. Layout zoom changes viewport
and device scale; it does not operate browser chrome zoom or text-only zoom.

Independent Windows installation/upgrade/removal, NVDA/manual accessibility, security,
distribution rights, signing, completed remote CI, overnight stability and agreed
performance budgets remain open. Master-spec acceptance also remains incomplete.
Follow [remaining actions](../releases/remaining-actions.md).

### Repository publication checks

After documentation/report cleanup, the unchanged application passed:

- `uv run --project engine pytest engine/tests -q --junitxml=dist/github-push-tests.xml`:
  112 passed in 244.62 s.
- `npm test`: 9 passed in 20.17 s.
- `cargo test --locked --manifest-path apps/desktop/src-tauri/Cargo.toml`: 1 passed.
- TypeScript/ESLint, Prettier, Ruff check/format, contracts and Cargo formatting passed.
- Local documentation links resolve to files in the published tree.

Generated reports, caches, runtimes and packages are excluded from the published tree.
Required license records remain tracked. Remote CI must be checked for the pushed SHA;
local checks do not establish its result.

### Reproducing verification

Commands are in [testing strategy](../testing/strategy.md),
[feature evidence](../hackyard/technical-evidence.md) and
[packaging](../releases/packaging.md). Raw reports are local generated outputs and
are ignored by Git; the original license inventory and legal evidence remain tracked.
Prior measurements and milestone records are also preserved in Git history.

The repository cleanup removes duplicate report snapshots and machine diagnostics from
the published tree. Source behavior, tests, license notices and commit history are retained.
Disposable extraction/Temp directories from local testing remain on disk after guarded
cleanup was rejected by execution policy. This does not affect the Git working tree.


## Engineering continuation — baseline and CI repair

Working branch: `engineering/browser-investigation`, baseline `c634573`.
Repository-wide assessment and file/test milestones: [engineering-plan.md](engineering-plan.md).
Fresh baseline commands: `uv run --project engine pytest engine/tests -q
--junitxml=dist/engineering-baseline.xml` (112 passed, 140.921 s), `npm test`
(9 passed, 3.99 s), `cargo test --locked --manifest-path
apps/desktop/src-tauri/Cargo.toml` (1 passed).

Actual GitHub [run 38071630094](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38071630094)
failed on Linux (23 failures, 82 passed, 7 skipped). The demo unconditionally
selected a repository browser cache after CI had installed browsers elsewhere;
subsequent browser launches could not find Chromium. Windows was cancelled and
packaging skipped. The repair uses one explicit install/test cache in CI, avoids
selecting a nonexistent cache in the standalone demo, restores test environment
state, and disables matrix fail-fast so both platforms report their own results.
Action references are immutable SHAs resolved from official repositories; checkout
and setup-node use their Node 24 v5 actions. Permissions remain contents/read.
Affected real-browser demo regression: 1 passed in 15.42 s. Ruff and workflow
Prettier validation passed after formatting. Remote verification of the repair is
pending; no CI success is inferred from local tests.


## Phase A — browser compatibility and failure meaning

Added explicit restricted/authorized-application modes and opt-in embedded-frame
network navigation at approved navigation origins. Authored steps can select an
unambiguous named frame. Existing DNS, resource/navigation separation, redirect
and effect-window checks remain in force. Restricted frames still fail closed;
read-only resource origins cannot grant frame navigation. New UI controls use the
existing permission panel and journey editor.

Findings now include an explicit evidence category (accessibility, completion
assertion, environment, policy, authorization, unavailable state, definition,
transient execution or inconclusive). Outer execution-budget and preparation
failures carry separate run failure categories. Ambiguous visible assertions are
definition errors, rather than confirmed missing completion states.

Commands: `pytest engine/tests/test_browser_capabilities.py
engine/tests/test_network_policy.py engine/tests/test_hackyard_demo.py -q`
with the documented local Playwright cache: **7 passed, 25.04 s**. Actual browser
checks covered an approved cross-origin frame, one approved POST, refusal with
resource-only approval, restricted frame requests and duplicate frame names.
`npm run check`, `npm test` (**9 passed, 5.06 s**), Ruff, contract freshness and
Git whitespace checks passed. Local baseline totals remain recorded separately.

Limits: named-frame steps only; discovery remains on the primary page. Inline
srcdoc/blank frame targets and complete cross-frame focus/AX verification are
unsupported. Frame permission controls network navigation, not a hostile-site
sandbox. Popups, WebSockets, service workers and downloads remain restricted.
Cross-origin APIs/resources already supported by exact origin permissions retain
the existing containment tests. No independent security or assistive-technology
verification is claimed. New source has not yet been packaged or tested natively.


## Phase B — discovery, replay and graph investigation

Added intersecting named semantic scopes, stable IDs and ARIA description constraints
with explicit ambiguity refusal and locator provenance. Discovery now offers tabs,
menu items/checkable menu items, switches, options, tree items and custom comboboxes
alongside the existing actions. Roving composites and active-descendant ownership
use actual bounded keyboard navigation; unsupported native-select/container actions,
ambiguous targets and unavailable states remain frontier entries. Navigation and
interaction IDs are separate; full focus observations remain in the graph. Explicit
state budgets supplement action/depth/time bounds for websites and controlled fixtures.

Version-1 recipes retain supported approved discovery paths with permission/profile
requirements and observation references. Controlled fixture recipes use observed
prerequisites. External recipes require explicitly retained page text; withheld names
are never reconstructed. All replay needs fresh authorization and runtime inputs.
The replay panel can save a separate editable project. Target/environment changes and
unmatched input signatures cannot claim matched-condition non-reproduction.

Graph analysis records actual objective witnesses, blocking attempts, chronological
prerequisites, shortest state paths, up to three observed alternatives per state and
unknown frontiers. Search is bounded to 1,000 edges. Paths do not automatically become
replay recipes or prove global unreachability. Comparison adds overall conservative
verdicts and focus/control changes. A verified comparison defect was fixed: signatures
now cover redacted saved literal inputs, so different plaintext no longer appears
comparable. Discovery target identities are also retained or explicitly unmatchable.

Acceptance: full `pytest engine/tests -q --junitxml=dist/phase-b-suite.xml`:
**121 passed, 175.26 s**. After controlled-fixture recipe/state-bound additions,
`pytest test_investigation.py test_exploration.py test_accessibility_semantics.py
 test_browser_capabilities.py -q`: **15 passed, 43.61 s**. Final collision-safe step
IDs and bounded alternatives: `pytest test_investigation.py test_reachability.py -q`:
**8 passed, 17.81 s**. Actual Chromium checks cover roving tabs, active-descendant
options, ARIA descriptions, duplicate scoped buttons, focus identity, retained/private
recipes, real broken/corrected replay, input-signature mismatch and state exhaustion.
`npm run check`, `npm test` (**9 passed, 5.42 s**), formatting, Ruff and contract checks
passed. React replay regression verifies saving an editable draft does not execute it.
Architecture/limits: [004-investigation-evidence.md](../architecture/004-investigation-evidence.md).

Remote PR run [38073119309](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38073119309)
at `6f2360d`: Linux and Windows check jobs completed successfully; packaging was still
running when recorded. This does not verify the later Phase B source. Native/portable
verification of the new UI remains pending. No new independent release gate is cleared.


## Phase C — human investigation and versioned profile batches

Added a collapsed, keyboard-operable manual investigation panel with planned,
observed, inconclusive and tester-attested verified-human records. Exact context,
action, expected/actual observations and attestation are required for observed or
verified-human status. NVDA preparation always starts planned with no actual result.
Manual records remain separate from automated findings/outcomes/retests; JSON/HTML
exports label them explicitly. SQLite schema 4 preserves existing run JSON and adds
FK-cascaded manual records. Plaintext retention/export and upgrade rollback limits
are documented in [human-investigation.md](../testing/human-investigation.md).
Actual NVDA evaluation remains **NOT RUN**.

Profiles now use version-1 snapshots. `scripts/profile_batch.py` runs 1–8 reviewed
profiles sequentially, with a maximum 1,800-second execution budget, fresh contexts,
explicit repeated-effect authorization, private outputs and no automatic retry or
discovery. Condition differences remain descriptive/inconclusive for repair claims.
Layout emulation remains explicitly distinct from real browser/text zoom.
See [profile-batches.md](../testing/profile-batches.md).

Commands/results: human review, profiles, lifecycle and storage/report regressions:
**15 passed, 14.82 s**. New batch/manual integration checks: **3 passed, 6.46 s**,
including actual keyboard-versus-pointer execution and authorization before output.
React: **10 passed, 4.41 s**, including unverified NVDA preparation and save without
browser execution. `npm run check`, Prettier, Ruff and contracts passed.
Actual CLI batch used `--seconds 120 --authorized --allow-effects`: two profiles in
**5.467 s**, keyboard task blocked (3.548 s), pointer task completed (1.881 s),
comparison `inconclusive-different-conditions`. Raw local evidence:
`dist/Profile-batch-readiness/batch.json`; no credentials or generated results are
added to the repository. Comparative benchmark work remains in progress; native UI
and packaging verification for schema 4 remain pending.


## Phase C — paired compatibility corpus

Added sixteen actual browser cases and an optional locked Pa11y 10 benchmark tool,
with recorded oracle outcomes, actual axe version/hash and timing, source/host
provenance, scanner configurations and raw results. CI installs the optional tool,
audits it separately, and uploads corpus artifacts on both operating systems.
Branch pushes no longer duplicate pull-request pipelines; main pushes remain tested.
See [comparative-corpus.md](../testing/comparative-corpus.md) for workload differences,
reproduction and scope. No static scanner's lack of task execution is counted as a
false negative. Accessibility Insights and assistive technology remain not run.

Actual CI-style command: `pytest engine/tests/test_comparative_benchmark.py -q
--junitxml=dist/corpus-regression.xml`, with `ACCESSMAZE_CORPUS_PA11Y=1` and
`ACCESSMAZE_CORPUS_OUTPUT=dist/Corpus-CI-local`: **1 passed, 74.58 s**, all sixteen
case outcomes correct, eight expected rules observed, eight working cases without
unexpected confirmed findings and eight paired improvements. Raw local output is
ignored by Git; remote CI artifacts provide downloadable evidence. Optional tool
`npm audit --prefix benchmarks/pa11y --audit-level=moderate`: zero vulnerabilities.

Remote run [38074436461](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38074436461)
at `39609b0`: **Linux checks, Windows checks and Windows preview packaging all
completed successfully**. This verifies that commit, not the later working tree.


## Phase D — measured history loading

Replaced project-summary N+1 reads with one SQLite aggregate, added bounded
metadata-only history pages and lazy full-run inspection, and isolated history
request state in a small hook with stale-response guards. Existing run retrieval
and UI design remain intact. Keyboard pagination and useful empty states were added.

Actual measurement and limitations: [history-performance.md](../testing/history-performance.md).
Synthetic 776-run storage workload: 25 to 1 summary connections, 479.864 to
283.906 ms warm summary medians, 35,389,000-byte full history versus 28,007-byte
first page. These are development-host storage measurements, not executed browser
results, native rendering measurements, peak memory or accepted release budgets.
`pytest test_history.py test_storage_reports.py -q --junitxml=dist/history-regression.xml`:
**7 passed, 2.11 s**. `npm run check` passed; React **12 passed** including out-of-order
history responses and keyboard paging. Ruff, Prettier and contract checks passed.
New history UI still requires native-package acceptance; polling remains periodic.


## Phase D — confirmed backup and redaction defects

Added regressions before fixing two internally reproduced defects. With an open
SQLite reader and 26 MiB committed in the WAL, the old backup accepted a workspace
above its 25 MiB limit. The check now uses logical database pages and rechecks the
consistent snapshot before compression. Backup temporary storage receives private
permissions; the manifest distinguishes archive format 3 from actual database
schema 4 and explicitly warns about plaintext human notes.

A real browser run with runtime input `a` corrupted executable hashes, state IDs
and reproduction references through substring redaction. Generated structural
references, host environment versions/hashes and audit engine metadata now remain
intact; page names, descriptions and input values still undergo redaction. This
fix protects evidence integrity, not a claim of encryption or hostile-site isolation.

Before fixes: `pytest test_maintenance.py test_runtime_inputs.py -q`:
**3 failed, 5 passed, 17.88 s**, including both reproduced defects and missing schema
metadata. After fixes: `pytest test_maintenance.py test_runtime_inputs.py
 test_investigation.py -q --junitxml=dist/security-after.xml`: **15 passed, 38.06 s**,
including actual private login/upload, single-character input, retained/withheld
replay, SQLite WAL and restored snapshot integrity. Two initial attempted commands
named nonexistent privacy test files and ran no tests; these are not counted as
verification. This is internal regression review, not an independent security audit.


## Phase D — conditional polling and widget regressions

`run.poll` now returns only a revision when evidence is unchanged, avoiding repeated
full graph transfer and React replacement during approval waits. Changed runs use
the existing complete snapshot; legacy records always return complete evidence.
Recovery and unexpected failure advance revisions, and paused runs no longer write
unchanged records every 100 ms. The actual worker/browser approval test demonstrates
a response below 100 bytes versus a snapshot above 1,000 bytes, then observes
cancellation and legacy recovery. No event-driven or CPU-performance claim is made.

A genuine combobox false positive was reproduced: an active-descendant option in an
externally controlled listbox was called keyboard-unreachable (**1 failed, 3.93 s**).
Logical focus now requires the explicit owner relationship and document focus;
a forged/unrelated ownership claim remains unreachable. A real menu/switch test
also reproduced missing DOM checked states (**1 failed, 1.95 s**). Custom ARIA checks
and native indeterminate checkboxes now retain boolean/mixed state alongside the
existing computed AX evidence. Both final widget regressions: **2 passed, 2.45 s**.

`pytest test_run_poll.py test_investigation.py test_worker.py test_lifecycle.py -q`:
**23 passed, 45.20 s** (before the additional menu-state case). Poll test authoring
initially omitted required journey fields/assertions; failed setup attempts were
corrected, not counted as product defects. Actual zoom probe in headed and headless
Chromium 153.0.8010.12 used `Control++`: viewport, DPR and visualViewport scale did
not change. Raw `dist/Zoom-probe.json`; browser/text zoom remains manual and layout
emulation remains clearly labeled. These probes do not establish all zoom APIs are
impossible or verify accessibility under real zoom.


Public/owned compatibility rerun: `python scripts/compatibility.py --public
--output dist/Compatibility-engineering.json` completed all four paths without
compromised origin coverage: owned 19-step application **6.893 s**, Selenium's
official automation form **7.375 s**, W3C BAD before **1.891 s**, after **1.667 s**.
Owned API received one POST and exactly 25 selected bytes. Before reported seven
rule IDs; after reported two. These public demo totals are observations, not stable
oracles or a certification. Existing exact origin permissions were preserved.
React **12 passed, 30.54 s**; TypeScript/ESLint passed. Formatting errors caught in
new test HTML and the checked-state TypeScript union were corrected before commit.


## Delivery verification — October 11

Clean `10a3fc6` full suite with the locked Pa11y probe:
`pytest engine/tests -q --junitxml=dist/engineering-final-suite.xml`:
**134 passed, 296.67 s**. Corpus source provenance is clean; sixteen cases,
all requested scanners completed, **71.513 s**. Rust Job-object test passed;
application npm audit, optional-tool npm audit and pip-audit reported no known
vulnerabilities (editable local engine skipped by pip-audit).

Portable build `AccessMaze-engineering-preview` completed from clean `10a3fc6`:
627 components, 782 copied notices, 73 retained raw metadata flags and 754 exact
full-Chromium credit sections. System-only PATH verification passed. Frozen startup
0.767 s; accessible/broken/conditional/owned-SPA 3.050/9.226/4.755/5.812 s, expected
0/1/0/0 findings. Native UI acceptance is **not passed**: it reproduced duplicate
replay panels/landmarks and a disabled stale replay control. React siblings shared
the same run-ID key. The comparison function itself completed, but its UI axe
check failed `landmark-unique`. Keyboard/error/dialog checks passed. Failed native
captures are retained locally; the earlier screenshots are preserved in Git.

Remote run 38077376024 at `e6e8aa8` failed: Linux **1 failed, 123 passed, 7 skipped**;
Windows failed the optional scanner and a timer-dependent stale-state test. Linux
artifact stderr establishes `No usable sandbox` on the hosted runner. Windows
artifacts retain two `net::ERR_ABORTED` initial scanner navigations; their root cause
is not established. No automatic retry or successful scanner result is invented.
The owned corpus now has an explicit optional-scanner-only `--pa11y-no-sandbox`
setting for hosted Linux, recorded in configuration, plus browser stderr diagnostics.
This does not change application origin/isolation policy. The stale-state test now
releases an actual server response only after the proposal and waits for the page's
acknowledgement, removing the load-time timer race. Its actual browser regression
passed **1 test, 2.84 s**. Windows diagnostic calibration rerun: two real cases,
**8.659 s**, correct outcomes and completed Pa11y. Remote rerun remains required.


The native duplicate-panel defect was also reproduced in a full App component
regression before the fix: switching saved runs left **three replay regions** where
one was expected, with React duplicate-key warnings. Replay and human-panel keys
now use distinct prefixes. The test inspects alternating saved runs four times and
requires exactly one of each region and an enabled replay control. This is a UI
component test, not fabricated browser execution; native acceptance is repeated on
the rebuilt package. Native axe output identifying the duplicated replay landmark
is retained in `dist/Native-duplicate-panels.json`. Initial test setup needed jsdom
dialog-method shims and a complete finding fixture before reproducing the defect.


After the key fix: React **13 passed, 5.19 s**; TypeScript/ESLint, formatting,
Ruff and schema checks passed. The native package at `10a3fc6` remains a failed UI
acceptance build; a later build must pass before its replacement is recommended.


## Hosted Windows scanner permissions

Run [38102629066](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38102629066)
completed Ubuntu checks successfully; Windows recorded **1 failed, 133 passed,
251.49 s** and packaging was skipped. Four optional Pa11y navigations were
inconclusive. Raw artifact 11688945880 identifies sandbox executable access denied
(0x5), followed by network-service failure and ERR_ABORTED. This establishes a
browser-cache permission defect in the hosted scanner setup, not a successful scan.
The workflow now grants read/execute to the Windows application-package SID only
on its downloaded test-browser cache. It grants no write permission and does not
change private evidence ACLs or application sandbox policy. This follows the
[Puppeteer Windows sandbox procedure](https://pptr.dev/troubleshooting#chrome-reports-sandbox-errors-on-windows).
The correction still needs an actual completed remote run. No retries or suppressed
scanner assertions were introduced.


## Current package and demonstration acceptance

`python scripts/package_windows.py --name AccessMaze-investigation-preview` completed
from clean `432dd5f`. `Test-AccessMazePortable.ps1`, `portable_smoke.py --complex`
and `archive_preview.py` passed; a new Unicode/space extraction also passed frozen
checks. Exact artifact/hash and measured durations are in the current summary.

Actual packaged `desktop_features.py`, `desktop_comparison.py`, `desktop_readiness.py`,
`desktop_website_smoke.py`, `desktop_cancel.py`, `desktop_crash.py` and new
`desktop_investigation.py --output dist/Native-investigation-432dd5f` all passed.
The last harness executes actual accessible/broken fixture journeys, checks paged
metadata history, saves/exports a planned-only NVDA record separately from automated
findings, switches stored runs four times and saves an editable draft without
executing it. This is no claim of actual human or assistive-technology testing.
Updated screenshots show the current actual UI. Raw native results remain local.

`python scripts/hackyard_demo.py --output dist/Hackyard-investigation-432dd5f` completed
with initial-page axe zero findings, broken task blocked at `validate`, corrected
task completed and verified-improvement under unchanged conditions. The server
received one actual multipart POST with 25 selected bytes. Scripted recorder replay
completed; offline/reconnect retention assertion blocked after input loss. No
results were hardcoded. The handoff includes reviewable submission copy, architecture,
a five-minute video plan, fair tool comparison and all three technical contribution
boundaries. Entrant recording, event timing/eligibility and actual disclosures remain
required; no competition submission occurred.

Fresh local `cargo audit --json` reported zero vulnerability advisories and retained
one unmaintained and one unsound informational warning (proc-macro-error/glib).
These are not silently converted to zero warnings or binary security clearance.
Five distribution tests passed in 4.37 s. Ruff check/format covered 88 Python files;
contracts and `git diff --check` passed. All local Markdown links resolved across
39 source documents. Original legal evidence remains tracked; generated runtime,
reports, extracted packages and raw diagnostics remain ignored.


## Native sustained harness correction

The first 600-second native attempt completed **164 fixture/UI cycles** but failed
its final harness assertion: after `project.delete`, it called `run.history` for
the deleted project, which correctly returned `Project not found`. No complete
stability pass is claimed for that attempt. Raw progress and the exact original
script are in `dist/Native-sustained-432dd5f`. The correction verifies absence via
`project.list`, separates export timing from its 0.5-second observation delay and
uses the absolute Windows close-helper path. A full 600-second repeat is required.

During cleanup follow-up, another test host was accidentally launched before the
first closed; a shell continuing after assertion failure launched a third. Closing
only one host left shared WebView2 processes while the other windows were alive.
After closing both additional exact owned hosts, all known children exited. This
overlap confounds that shutdown observation and does not resolve the earlier
`7628688` retention. It is not reported as a leak or a fixed application defect.
No unrelated process was killed. The repeat runs one dedicated desktop only.

Website/recorder and worker-crash harnesses now assign unique project names and
delete only their exact owned synthetic project after successful verification.
Both actual native reruns passed, including headed recorder and crash/restart;
four Chromium children exited after the crash. Two exact synthetic IDs left by
the failed `10a3fc6` feature test were also removed after verifying their names;
raw failure evidence was preserved. Existing unrelated history remains untouched.


The preview launcher now refuses an occupied loopback test port before spawning a
second host. Actual attempt against the active dedicated desktop exited with
`Test port 9224 is occupied; close the existing test desktop first`; no duplicate
was launched. Formatting caught and corrected the new line wrapping. A free-port
launch is repeated after the sustained test. This guard addresses the test-harness
overlap, not the undiagnosed historical application retention.


The corrected native attempt completed **170 cycles / 611.472 s including shutdown
wait**, removed its own history, then failed the accumulated-child measurement.
Raw `dist/Native-sustained-corrected-432dd5f/measurements.json` remains **failed**,
not rewritten as a pass. Peak summed RSS 1,022.85 MiB, handles 5,866; idle summed
RSS 564.93 → 574.05 MiB, handles 3,728 → 3,636. Each journey boundary had zero
surviving Chromium; these resource samples are not controlled performance budgets.

Follow-up showed reported survivor PIDs now belonged to unrelated Codex/Chrome
process trees, with later creation times; others had exited. The harness had retained
historical Process objects across hundreds of launches and used `psutil.wait_procs`,
whose Windows wait path can wait on a replacement PID before identity comparison.
Installed source inspection confirmed `Process.is_running()` checks PID plus creation
time. The harness now uses that check, records observed child identities and separately
records reused PIDs. No unrelated process is terminated. A third full interval
validates this measurement correction; it does not change application lifecycle code.
The historical `7628688` retention remains unresolved.

Ordinary native launch from the Unicode/space extracted `432dd5f` package, without
CDP and with System32-only PATH, started worker/WebView2 in the observation interval
**3.884 s** and closed **all eight children**. This is process-start/shutdown evidence,
not timed connected-UI or independent clean-machine verification. Read-only inspection
of the actual existing native database returned schema 4, integrity `ok`, zero foreign
key violations; unrelated records were preserved.

Remote `81f813d` checks have now completed successfully: Ubuntu **127 passed,
7 skipped, 195.04 s**; Windows **134 passed, 311.27 s**; React 13 on both; Rust
1 passed. npm/Python advisories passed; cargo-audit retained two informational
warnings. Windows packaging is still running, so this is not yet an all-jobs pass.


## Adversarial protocol coverage

Added a bounded deterministic malformed-frame corpus through the actual worker
stdin/stdout process: invalid UTF-8, truncated/non-object JSON, 2,000 nested arrays,
invalid version/ID/method/parameter types and a sensitive unknown field name. All
28 invalid frames return errors, no supplied private marker appears on stdout/stderr,
and the following health request succeeds. This extends risk-based parser/privacy
coverage; it is not an exhaustive fuzzer or evidence of a new application vulnerability.
`pytest engine/tests/test_worker.py -q --junitxml=dist/Protocol-adversarial-October11.xml`:
**10 passed, 14.03 s**. Earlier 134-test full-suite totals remain tied to their exact
commits; the final pushed suite includes this additional test. Engine code is unchanged.


## Completed hosted package verification

[Run 38103235350](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38103235350)
completed **both check jobs and windows-preview successfully**. Workflow head is
`81f813d`; checkout/package provenance is the synthetic PR merge commit
`c8474870ba08ae917b12b4f23a8472344f615691`. Fetching `refs/pull/1/merge` and comparing
trees against `81f813d` returned no differences. This distinction is retained rather
than relabeling the package as a head-commit build.

Hosted portable/complex smoke, archive CRC and manifest checks passed. Inner ZIP
**389,879,391 bytes**, SHA-256
`3e73fd6d3242417447976ca539628f2950d5c9b72cbe9a26ab21ab044becae1b`.
[Artifact 11688539971](https://github.com/Rhythm-Sanghi/AccessMaze/actions/runs/38103235350/artifacts/11688539971)
is retained for 14 days; outer Actions artifact digest is separate from the inner
ZIP hash. This is hosted packaging evidence, not an independent interactive
standard-user/offline/NVDA qualification. Later verification/test/docs commits
require final-head CI; no queued run is reported as passed.


## Completed native sustained verification

`native_stability.py --pid 2480 --exe dist/AccessMaze-investigation-preview/AccessMaze.exe
--seconds 600 --output dist/Native-sustained-identities-432dd5f` completed **157 cycles
in 601.33 s**, including cleanup/shutdown. The exact exercised script and full raw
measurements are preserved in that exclusive output directory. Fixture outcomes,
cancellation, history counts, UI inspection and report export passed in each cycle.
The owned project/history was deleted, and zero owned children survived close.
Creation-time-aware tracking retained **781 identities** and excluded **six reused
PIDs** without touching replacement processes. The console summary now omits the
large identity array; complete raw evidence still retains it.

Peak summed native/worker/browser RSS **1,025.90 MiB**, handles **5,565**; idle
summed RSS **534.37 → 560.85 MiB** (range **534.37–700.33**), handles **3,655 → 3,664**.
These count shared pages repeatedly and include uncontrolled laptop load. UI reloads
between cycles; this is a long-lived host/worker workload, not uninterrupted single-
document UI retention or an overnight/leak-clearance result. The old retention gate
remains open. Earlier failed harness attempts remain recorded above.


Final same-laptop System32-only-PATH native startup recheck passed three sequential
launches: connected UI **3.054 / 1.851 / 1.688 s**, ready summed RSS
**466.09 / 461.27 / 443.96 MiB**, children **8 / 9 / 8**; every tree closed.
Existing AppData/cache and CDP overhead remain part of these measurements. Raw
`dist/Native-startup-432dd5f.json`. The guarded launcher then succeeded on a free
port, and all eight owned children closed. Actual native database integrity remains
`ok`, schema 4, zero foreign-key violations, read-only inspection. No test port
or owned desktop remains open.
