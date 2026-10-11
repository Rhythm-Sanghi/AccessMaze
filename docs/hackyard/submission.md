# AccessMaze: browser journeys with inspectable accessibility evidence

Submission copy for entrant review. No submission, eligibility decision or demo-video
publication has occurred. Repository: [Rhythm-Sanghi/AccessMaze](https://github.com/Rhythm-Sanghi/AccessMaze).

## Short description

AccessMaze is a local desktop workspace for testing whether an authored browser task
can finish under concrete keyboard and environment conditions. It records the steps,
focus, accessibility observations and task assertions behind a failure, then compares
a fresh approved retest with the original evidence.

## Problem and approach

A page scan can identify rule violations without establishing whether a multi-step
application can be completed. AccessMaze combines axe with authored tasks, bounded
keyboard attempts, observed transitions and explicit completion assertions. Investigators
can inspect a failed step, review a reproducible recipe, save an editable draft and
test a correction under the same conditions. Graphs show observed paths and unknown
frontiers; they do not claim exhaustive reachability.

The demonstration uses an owned application with an unfocusable Continue control.
An actual keyboard run blocks. Replacing it with a native button permits the task
to finish, and the retest identifies the divergent step. A second case loses a draft
after interrupted connectivity. Findings and reports come from real engine execution.
See the [live sequence and video plan](demo-script.md).

## Current implementation

Tauri/React retains the Workshop + Gridline + Studio Utility interface. A private
validated pipe connects Rust to a Python worker. Playwright runs fresh Chromium
contexts; SQLite retains private evidence locally. Windows Job objects own worker
and browser descendants. There is no required account, cloud analysis or paid API.
The [architecture diagram](architecture.md) shows data flow and approval boundaries.

Current capabilities include scoped semantic targets and named-frame permission,
recording with reviewed input bindings, separately approved workflow exploration,
versioned replay recipes, editable drafts, observed task paths, reusable profiles,
bounded serial profile batches, paged history, exports and separate human records.
Manual records distinguish planned checks from attested observations; preparing an
NVDA checklist never produces an automated NVDA pass.

## Evidence and differentiation

The controlled corpus has eight broken/working pairs. AccessMaze executes authored
tasks; axe and Pa11y scan the initial page separately. The local run classified all
sixteen tasks correctly and recorded eight verified improvements. This is a small
controlled corpus with different workloads, not a universal accuracy or speed ranking.
Pa11y also supports actions. Accessibility Insights was researched but not executed.
See [method and raw-output reproduction](../testing/comparative-corpus.md) and the
[comparison with existing tools](differentiation.md).

Native acceptance at clean application source `432dd5f` exercises actual frozen-worker
execution, approvals, failure/fix/retest, recording, cancellation, crash recovery,
manual-plan export, paged history and editable drafts. Exact test results, failed
attempts, archive hashes and later CI conclusions belong in
[engineering status](../development/status.md).

## Limits and roadmap

This is an unsigned readiness preview. No WCAG certification, real NVDA verification,
independent security audit, independent clean-machine qualification or overnight
stability is claimed. Browser chrome/text zoom needs manual testing. Popups, service
workers, downloads and WebSockets remain restricted; frame support is explicit and
bounded. Private text can prevent automatic recipe replay. Human notes and backups
are plaintext. The application is not a hostile-target sandbox.

Release work includes independent Windows/fresh-user testing, human accessibility
evaluation, redistribution review of embedded browser/native libraries, signing,
reviewed performance budgets and sustained overnight/native verification. These are
gates, not silently completed roadmap items. Broader platform and AT integration
remain future work subject to an approved release scope.

## Contribution disclosure and handoff

The [provenance ledger](preexisting-work.md) preserves the technical boundaries
`9f3222a`, `8e074e7` and `c634573`. Existing application work and third-party foundations
must be disclosed. Commits after a boundary do not establish onsite timing or human-only
authorship. The entrant supplies actual event dates, team contributions and tool-use
disclosures under the rules.

Before submission, the entrant must:

- Confirm eligibility and accurately disclose pre-existing work and assistance.
- Record the five-minute actual demo and provide captions/transcript and a video URL.
- Verify the final repository commit, completed CI and engineering status.
- Describe the software as a readiness preview and retain its release limitations.
- Review the required submission fields and publish through the authorized event account.
