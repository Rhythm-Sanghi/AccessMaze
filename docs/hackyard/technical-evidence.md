# Technical evidence index

Current continuation: see [discovery, replay and reusable conditions](remaining-features.md)
for the implemented workflow, approvals and explicit limits. Baseline **8e074e7**;
workstation development, not claimed onsite. Native/package acceptance is recorded
in [engineering status](../development/status.md), separately from older evidence below.


The source of truth is ../development/status.md, with actual commands, results and limits.
Baseline verification belongs to 9f3222a and its earlier package source 228ad9c; it is not
proof that later UI or engine changes passed native tests.

New meaningful regressions:

- engine/tests/test_outcomes.py: mandatory assertions, cancellation, interruption,
  coverage compromise, unknown browser failure and optional/manual scope.
- engine/tests/test_comparison_browser.py: actual Chromium/axe observations on different
  unnamed controls must not be conflated solely because the rule and step match.
- engine/tests/test_retests.py: missing audit, private tokens, changed step ordering and
  conservative repair verification.
- engine/tests/test_browser.py: actual blocked/completed task outcomes persisted to SQLite.
- engine/tests/test_hackyard_demo.py: failure, correction, exact upload, recorder replay
  and environmental draft-loss evidence from real engine execution.

Run the script in demo-script.md to generate JSON/HTML/CSV, diffs, summary and private
SQLite records. Matching semantics and outcome definitions are in comparison-rules.md.
Full-suite/native/package measurements must be recorded in status after execution;
this index does not claim a pending check passed. Independent NVDA and clean-machine
procedures remain unexecuted unless separately attested.

## Earlier completed outcome increment (504774a)

Clean packaged application source 504774a passed the real native comparison, fixture,
approval, recorder, UI focus and worker-crash checks. `native-comparison-verification.json`,
`portable-startup-verification.json`, `complex-portable-verification.json`,
`native-startup-verification.json` and `preview-artifact-verification.json` retain actual
results. `native-validation-attempts.json` preserves earlier failed attempts; none is
silently described as a pass. Full suite: 102 Python, 6 React and 1 Rust tests.

`demo-competition-verification.json` records an actual isolated initial-page audit with
zero rule violations, followed by a keyboard task failure on that same broken application,
the correction/comparable passed retest and a separate environmental draft-loss failure.
All results are produced by the engine. See status for exact commands, durations and limits.
At that earlier boundary, broader discovery/profile/replay features remained open; the new feature acceptance below is separate. Independent release gates remain open.

Remaining-feature backend verification: **112 Python tests passed (151.64 s)** at 7628688;
React **9 passed**, including replay approval/input mapping, profile persistence controls,
and graph-state evidence selection. First real native acceptance is retained in
native-features-first-verification.json and native-features-first-runs.json; ordinary/instrumented
shutdown results are separate. Current final artifact/source acceptance is authoritative
in ../development/status.md, including any later presentation-only increment.

## Final feature acceptance (746eaca)

[Verification ledger](final-feature-verification.json) lists actual commands, raw results,
source provenance and failed harness attempts. Latest native feature/replay records,
strict comparison, cancellation and actual worker-crash cleanup passed. Three native
startup/shutdown samples and a separate ordinary-launch close passed; earlier WebView2
retention is preserved, without a claimed diagnosis. Screenshot evidence is from real
WebView2 execution and was visually reviewed.

[Complex frozen worker](final-complex-portable-verification.json),
[manifest/fixture check](final-portable-integrity-verification.json),
[standalone demo](final-demo-verification.json) and
[ZIP CRC/hash](final-preview-artifact-verification.json) identify the exact final source
and same-machine scope. Layout zoom is emulation; private discovery names cannot be
reconstructed for replay. No independent gate is inferred from these local passes.

The freshly extracted Unicode/space-path ZIP also passed System32-only worker checks
and actual native UI startup/normal shutdown. See final-extracted-portable-verification.json
and final-extracted-native-verification.json. Guarded disposable cleanup was policy-blocked;
the retained paths and manual action are recorded in the ledger, without a cleanup pass claim.
