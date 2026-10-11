# Dated baseline and provenance

Baseline recorded 2026-10-10 from the clean repository at **9f3222a**. This is a technical
pre-mission boundary, not an assertion about the competition's official start date.
The entrant must supply the event's rules/date and contribution history.

Pre-existing: Tauri/React design system, Python worker, SQLite, authored journeys,
keyboard/focus/AX/axe checks, graph, origin restrictions, runtime bindings/uploads,
recording, approved website walk, fixture branch discovery, reports/retests, complex
owned application, broken/fixed demonstration, Windows packaging, internal security
fixes, licensing investigation and local verification through 9f3222a.

```powershell
git show --no-patch --format=fuller 9f3222a
git log --reverse --oneline 9f3222a..HEAD
git diff --stat 9f3222a..HEAD
git diff 9f3222a..HEAD
```

Preserve this boundary and all original commits. New continuation commits are material
engineering work, but cannot be called onsite work without actual event evidence.
React, Tauri, Python, Playwright/Chromium, axe, Pydantic, NetworkX and SQLite are reused
third-party foundations. The commit history records the implementation boundary;
competition eligibility depends on the event rules.

The remaining-feature continuation requested a second explicit baseline, **8e074e7**.
`git log --reverse --oneline 8e074e7..HEAD` identifies these new discovery/replay/profile
changes. This does not replace the original 9f3222a ledger or claim an onsite boundary.


The complete engineering continuation uses clean **c634573** as its third technical
boundary. Everything reachable at that commit is pre-existing for this continuation.
Subsequent work adds authorized named frames, scoped widget discovery, versioned
replay/editable drafts, observed task reachability, separate human records, profile
batches, the paired axe/Pa11y corpus, bounded history/polling, reproduced security/UI
fixes and delivery verification. Inspect `git log --reverse --oneline c634573..HEAD`
and the corresponding diff. Preserve all three boundaries. None proves event timing
or human-only authorship; the entrant must disclose actual tools and contributions
as required by the competition. No competition submission has been made here.

PR #1 was squash-merged at **91e0e7f** on 2026-10-11. The annotated tag
`pr-1-reviewed-2026-10-11` preserves its original head **05a34a5** and all eleven
development commits. To inspect those individual changes after the squash, use
`git log --reverse --oneline c634573..pr-1-reviewed-2026-10-11` and
`git diff c634573..pr-1-reviewed-2026-10-11`. The tag preserves technical provenance;
it is not a release qualification or proof of competition timing.
