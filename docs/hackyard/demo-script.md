# Three cases, real browser evidence

## New-feature live sequence

1. Create/record and review an authorized journey; save named keyboard conditions.
2. Enable discovery and optional approved root recovery; approve a branch, recovery,
   and another branch. Show observed graph/frontier and the budget stop.
3. Run an authored journey against the owned broken Continue control. Select its
   stored finding in Failure reproduction; expand original trace/focus.
4. Review target/steps and authorize actual replay. Show the observed-again result.
5. Change the owned application to its native-button correction; authorize replay
   again. Show not-reproduced, completion and old/live step/focus evidence.
6. Apply another saved profile to the same journey; run with fresh authorization.
   Compare actual outcomes and both condition snapshots. Explain why changed-profile
   success cannot certify a keyboard repair.
7. Run a normal unchanged-condition retest and compare it under the existing stricter
   rules. Show the exact stored result, including limitations.

`desktop_features.py` is an automated native acceptance sequence against an owned HTTP
application. It requires a launched preview/CDP harness; it is not evidence of human
recording, NVDA use or onsite work. The existing reproducible engine demonstration below
continues to use actual findings rather than hardcoded result objects.

## Reproducible engine demonstration

Prepare locked dependencies and bundled Chromium, then run from the repository root:

```powershell
uv run --project engine python scripts/hackyard_demo.py --output dist/Hackyard-competition-new
```

Choose a new output folder; evidence is never overwritten. Only owned loopback servers
and synthetic fixtures receive interactions. No public-site write is performed.

1. First show isolated-check.html and isolated-check.json: an actual initial-page axe scan
   and heading assertion pass, while keyboard task completion remains untested. Then show journey.json: keyboard-only profile, bounded steps and explicit task assertions.
2. Show broken.html and broken.json: Continue is an unfocusable role-button div. Read
   the failed step, actual bounded focus attempt and not-reached assertions.
3. Show correction.diff: replace that control with a native button.
4. Show fixed.html and retest.json: the same conditions now reach Application received.
   Inspect the first divergent execution step, resolved/persistent/inconclusive findings
   and state references. Exactly one actual synthetic multipart submission is asserted.
5. Show environment.html and environment.json: a controlled form goes offline, reconnects
   and loses its input. The retained-value assertion blocks completion. The observation
   path includes offline and online states. This is Chromium offline emulation, not a
   physical adapter interruption; in-flight requests may finish. A separate regression
   engine/tests/test_connectivity_interruption.py
   exercises a real owned TCP drop and explicit retry.
6. Optional technical extension: recorded-draft.json contains input bindings, and
   recorded-replay.json shows real replay with fresh synthetic input. Recording input
   here is scripted, not a human session or an assistive-technology test.

The HTTP servers close after the run. Regenerate to obtain live origins; do not replay
expired URLs. Generated reports remain viewable offline. Identify stored evidence as
historical execution, including its timestamp, whenever it replaces a live demonstration.
A failed run must remain visible rather than being replaced with fabricated findings.

The latest local reports are under `dist/Hackyard-investigation-432dd5f`; raw native
reports are also generated locally. They are ignored by Git. Published results and
tested source commits are in [engineering status](../development/status.md).


## Ninety-second explanation

AccessMaze asks a concrete question: can this browser task finish under the conditions
we selected? A rule scan is useful, but an initial-page result does not establish
whether a person can complete a multi-step workflow.

Here the task is to complete an application using the keyboard. The Continue control
looks actionable, but the actual browser cannot reach it within the configured Tab
budget. AccessMaze records the attempted step, focus sequence and unmet assertions.
The graph shows what was observed and where evidence remains unknown.

We review the failure recipe before replaying it. After changing the control to a
native button, a fresh approved run reaches the completion assertion. The comparison
shows the first divergent step and preserves the original failure. Success applies
to this tested configuration; it does not certify the whole application.

The desktop, browser engine and evidence store run locally. External exploration
requires separate action approval, and runtime inputs are supplied afresh. Manual
observations are separate from automated findings. This is a readiness preview;
real NVDA evaluation and independent release qualification remain open.

The [three-minute technical sequence](../testing/hackyard-presentation.md)
provides the shorter live version.

## Five-minute recording plan

- 0:00–0:30: State the task and show exact keyboard conditions/authorized owned target.
- 0:30–1:30: Execute the broken Continue journey; show the actual blocked assertion,
  bounded focus trace and graph witness. Explain the initial-page scanner's limited scope.
- 1:30–2:30: Show the native-button correction and approved same-condition retest;
  inspect completion and the first divergent step, retaining the original failure.
- 2:30–3:30: Approve two branches and root recovery; show the frontier/state budget.
- 3:30–4:15: Save an editable replay draft and show profile changes make a repair
  comparison inconclusive. Show a planned manual checklist, explicitly not an NVDA pass.
- 4:15–5:00: Show local architecture, actual corpus results and open release gates.

Capture the actual current application; retain failures in the video if they occur.
The demo video still needs human recording/editing and an accessible transcript.
`desktop_investigation.py --output dist/native-investigation-new` verifies planned
records, paged history and editable drafts against a launched packaged host.
