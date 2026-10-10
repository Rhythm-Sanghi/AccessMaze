# Engineering status

Updated 2026-10-10. AccessMaze is a Windows development preview. Independent release
qualification is incomplete.

## Current implementation

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

## Verified application source

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

## Portable package

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

## Performance and stability

Three sequential native startups reached connected UI in 4.746 / 4.028 / 3.720 s,
with summed ready RSS of 448.97 / 446.24 / 441.50 MiB. All eight children exited after
each sample. A later idle sample measured 493.88 MiB and 3,687 summed handles.
Polling overhead, uncontrolled caches and repeated counting of shared pages limit
these measurements; no leak or performance-budget pass is established.

An earlier 607.26-second fixed-engine worker run completed 11 journeys and
11 cycles of 32 browser regressions (352 passing executions), with no surviving
children at cycle boundaries. This was not an overnight or native UI soak.
See [performance procedures](../testing/readiness-benchmark.md).

## Regressions and unsuccessful checks

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

## Security, licensing and release blockers

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

## Repository publication checks

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

## Reproducing verification

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
