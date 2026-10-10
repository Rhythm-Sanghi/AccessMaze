# ADR 003 — Approved discovery, historical replay and condition snapshots

Accepted 2026-10-10, continuing clean baseline 8e074e7.

Keep the existing private stdio worker, fresh Chromium contexts, SQLite evidence,
exact origin policy and Workshop + Gridline + Studio Utility interface.

Website discovery uses computed semantic candidates in deterministic order. Every
activation and optional return to the configured URL is separately approved; recovery
consumes the shared action/time budget. No external prefix or form submission is
replayed automatically. Returning to a URL cannot undo server effects. Store the
unvisited frontier and actual keyboard attempts; bounds never create barrier findings.
Coverage deduplication ignores transient focus but retains safe computed control-state
enums. Preserve original observations/focus in the graph. DOM and AX document epochs
must match; retry evidence capture on bounded transient navigation races, never effects.
This does not make observations atomic across arbitrary SPA updates.

Replay reconstructs a stored authored definition, disables discovery and replaces
redacted literals with fresh runtime bindings. Require target/action authorization
again, keep immutable original evidence and source/finding provenance, and distinguish
observed-again from changed-site/non-reproduced/inconclusive outcomes. Withheld private
discovery names cannot be recovered; an authored journey is required for those paths.

Reusable profiles live in a separate SQLite schema-3 table. Applying one copies the
conditions into the journey; runs retain snapshots. Library edits/deletion never mutate
past evidence. Old schema migration is forward-only; older previews refuse schema 3.
Profile connectivity schedules reference authored step IDs and require explicit remapping
when reused with different definitions. Focus/semantics conditions insert actual recorded
checks. Compare changed-profile task outcomes descriptively without calling them repairs.

Layout zoom emulates reflow through CSS viewport and device scale, explicitly labelled.
It does not verify browser chrome/text zoom, OS magnification, assistive technology or
usability. No profile claims disability simulation. Independent manual and release gates
remain required.
