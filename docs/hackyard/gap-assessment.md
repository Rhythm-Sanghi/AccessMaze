# Scope and remaining work

The feature continuation began at `8e074e7`. It added approved semantic branch discovery
with root recovery, finding-specific browser replay and persistent reusable profiles.
These are integrated with the existing journey, evidence, graph and comparison interface.
Local browser/native acceptance is recorded in [engineering status](../development/status.md).

| Area       | Implemented                                                                                                                       | Remaining limit                                                                                 |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Discovery  | Ordered semantic candidates, per-action approval, state deduplication, bounds, saved graph/frontier and approved root recovery    | No exhaustive coverage, unreachable-state proof or automatic replay of prerequisites            |
| Replay     | Historical trace/state/focus, reviewed fresh execution and conservative comparison                                                | Private withheld discovery targets require an authored journey; changed sites may not reproduce |
| Profiles   | Persistent library, condition snapshots, keyboard/pointer, viewport/layout zoom, motion, delay, connectivity, focus and semantics | Layout zoom is emulation; no browser chrome/text zoom or disability simulation                  |
| Comparison | Step alignment, target-aware findings, task outcomes and changed-condition warnings                                               | Changed profiles cannot verify a repair; separate human records exist; actual human evaluation remains unverified            |
| Packaging  | Local frozen worker, bundled Chromium, native flows and ZIP integrity                                                             | Independent Windows, signing, complete distribution review and remote CI qualification remain   |

The complete master specification is not implemented. Release qualification also requires
[manual accessibility](../testing/nvda.md), security review, sustained stability and agreed
performance acceptance. See [remaining actions](../releases/remaining-actions.md).

The c634573 continuation additionally implements scoped widgets, opt-in named frames,
versioned discovery replay/editable drafts, observed task paths, planned/attested human
records and bounded profile batches. Current acceptance and hosted CI failures/results
are in status; earlier table wording does not establish qualification.
