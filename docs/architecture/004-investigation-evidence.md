# Investigation evidence and safe replay

Status: accepted for the readiness preview, 2026-10-10.

Keep the existing local Python/Chromium engine and SQLite run snapshots. A target
can add a named frame, named semantic scope, stable element ID and ARIA description
to its role/name or label. These constraints intersect; a failure never triggers a
broader locator, index guess or raw CSS fallback. IDs are validated, and descriptions
currently cover `aria-describedby` and `aria-description`, not every computed
description source. Scoped discovery verifies uniqueness before proposing an action.
Repeated names without reliable context remain an explicit ambiguous frontier.
Locator provenance records the strategies used, without duplicating private text.

Navigation identity removes only DOM/AX focus flags. It retains checked, selected,
expanded, disabled, validation, live-region text, visible control and URL changes.
Interaction identity is the full observation fingerprint, including focus. Neither
identity includes field values or hidden application/server state. They cannot prove
that two server states are equivalent. Observation limits remain 200 DOM controls,
500 AX nodes/depth 8; dynamic same-document snapshots are not atomic transactions.

External discovery remains a user-guided walk. Computed semantic actions are ordered
deterministically; each activation or root navigation needs fresh approval. There is
no automatic reset/repetition of external writes. Controlled fixtures retain bounded
breadth-first traversal and observed prerequisite paths. Action, depth, wall-clock and
state bounds all leave unknown frontiers, never inferred global inaccessibility.
Supported roving composites use bounded arrows; `aria-activedescendant` can establish
logical focus within its current owner, including an externally controlled listbox
when a focused input/combobox explicitly names that owner through `aria-controls`
or `aria-owns`. An unrelated active-descendant claim does not establish reachability. This does not cover arbitrary custom widget
key protocols. Native select choices require authored keys; listbox containers are
not treated as activatable options.

Replay recipes are version 1 chronological witnesses. They retain configuration,
permission requirements, observation references and supported discovery steps. For
fixtures, the actual resettable prerequisite path is retained. For external websites,
all approved actions through the failure are prerequisites; root navigation does not
undo their server effects. No recipe runs automatically. Run-only inputs are supplied
again, and saved literal values become fresh bindings. Private target text remains
withheld by default, making that discovered recipe unavailable. Explicit page-text
retention allows a subsequent supported path to be replayed or saved as a separate
editable project. Recipes exceeding the import step bound remain unavailable.

Graph analysis reports witnessed objectives, blocking attempts and shortest observed
state paths. Alternative search inspects at most 1,000 edges and retains at most
three paths per state. These paths are explanations, not safe replay recipes: state
normalization omits private values and server prerequisites. Only the chronological
recipe may be reviewed for re-execution. Unknown branches remain visible.

Comparisons match stable step/rule/affected-target identities and require matching
journey, environment and keyed input signatures, distinct runs and uncompromised
coverage. Signatures cover saved literals as well as runtime values without retaining
plaintext. Worker restarts change the private key; unmatched signatures are
inconclusive. Per-run private text tokens never become cross-run identities. Focus
and control changes are descriptive; no difference alone proves a regression.
Changed replay targets/environments and changed input signatures cannot establish a
matched-condition repair. Non-reproduction is never a general claim that a defect is
fixed. Older evidence lacking new identities may need manual target review.


Run snapshots have a monotonic execution revision. `run.poll` returns a small
unchanged response when the supplied revision matches SQLite; otherwise it returns
the same full evidence and transient approval overlay as `run.get`. Legacy records
without revisions always return full snapshots. Recovery and unexpected execution
failure advance revisions. Paused runs save only the transition into pause, avoiding
repeated unchanged writes. Polling remains periodic, not event-driven; the change
reduces transport and React updates without adding subscriptions or global state.
