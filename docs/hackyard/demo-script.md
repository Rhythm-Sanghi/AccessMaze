# Three cases, real browser evidence

Prepare locked dependencies and bundled Chromium, then run from the repository root:

```powershell
uv run --project engine python scripts/hackyard_demo.py --output dist/Hackyard-competition-new
```

Choose a new output folder; evidence is never overwritten. Only owned loopback servers
and synthetic fixtures receive interactions. No public-site write is performed.

1. Show journey.json: keyboard-only profile, bounded steps and explicit task assertions.
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
