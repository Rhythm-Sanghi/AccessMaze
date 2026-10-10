# Reproducible Hackyard demonstration

From the repository root with locked dependencies and Chromium installed:

```powershell
uv run --project engine python scripts/hackyard_demo.py --output dist/Hackyard-demo-new
```

Choose a new output folder; existing evidence is never overwritten. The script owns
two ephemeral HTTP servers and uses only synthetic names, references and file bytes.
It makes one actual multipart submission to its own API. No public site is modified.

Show these artifacts in order:

1. `journey.json`: the readable 19-step application, including validation, conditional
   radio navigation, dialog/focus restoration, connectivity interruption and upload.
2. `broken.html`: observed keyboard-unreachable Continue control and reproduction
   steps. This is a real Chromium run, with computed accessibility/focus observations
   retained in `broken.json`; no screenshot or AT result is fabricated.
3. `correction.diff`: replace the unfocusable role-button div with a native button.
4. `fixed.html` and `retest.json`: same live origins, journey, project and runtime
   input signature; the formerly failing assertion passes and the full journey ends
   at Application received. The server verifies one submission and exact file bytes.
5. `recorded-draft.json`: product recorder output from scripted real browser events,
   containing a named input binding rather than its entered value. It can be reviewed
   and edited. `recorded-replay.json` records successful execution of that draft with
   a newly supplied synthetic value.

Raw evidence and SQLite workspace are generated locally in the output folder. The
servers close afterward; ports/URLs are intentionally ephemeral. Regenerate the demo
to replay against a live target, rather than importing an expired URL and implying it
remains reachable. HTML/JSON/CSV artifacts remain viewable offline. The full application
source is `engine/tests/compatibility/application.html`; the diff changes only its
Continue control at render time.

Actual first execution summary is retained in `hackyard-demo.json`: broken failed;
fixed and recorded replay completed with limitations; comparable keyboard assertion
passed retest; one API POST with 25 synthetic upload bytes. A real-browser regression
also checks this sequence and refusal to overwrite evidence. This is a reproducible
scripted demonstration, not a human recording, NVDA result or WCAG certification.
