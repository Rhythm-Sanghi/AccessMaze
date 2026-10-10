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

## Completed outcome increment

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
Broader discovery/profile/replay features and independent release gates remain open.

Remaining-feature backend verification: **112 Python tests passed (151.64 s)** at 7628688;
React **9 passed**, including replay approval/input mapping, profile persistence controls,
and graph-state evidence selection. First real native acceptance is recorded in
native-features-verification.json and native-features-runs.json; ordinary/instrumented
shutdown results are separate. Current final artifact/source acceptance is authoritative
in ../development/status.md, including any later presentation-only increment.
