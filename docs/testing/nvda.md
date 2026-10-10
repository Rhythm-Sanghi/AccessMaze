# Manual NVDA verification procedure

The Analysis workspace can prepare and retain this procedure using the
[human investigation workflow](human-investigation.md). Preparation stays planned;
only actual human observations can be attested. No NVDA execution is automated.

Status: **NOT RUN**. Chromium AX snapshots, axe checks and scripted keyboard events
are not NVDA verification. A human tester with NVDA and the packaged application must
complete this procedure. Record failures and uncertainty; do not infer conformance.

Use a separate Windows standard-user account and synthetic test data. Record date,
tester, Windows build, display scaling, keyboard layout, NVDA version/configuration,
WebView2 version, package SHA-256, source commit and whether other accessibility tools
were running. Preserve the unmodified package and a separate test storage backup.

Start NVDA and AccessMaze without a mouse. Verify the configured NVDA modifier
(Insert or Caps Lock) and keyboard layout. Optionally enable Tools → Speech Viewer
to capture announcements, with the tester's consent. Keep recordings free of credentials
and personal information. Check ordinary Tab/Shift+Tab and browse navigation. NVDA+Space
switches browse/focus mode; H, F and B navigate headings, fields and buttons in browse
mode; NVDA+F7 opens the elements list. Do not count browse-mode activation as evidence
that a control is reachable using ordinary Tab. See the
[official NVDA user guide](https://download.nvaccess.org/releases/stable/documentation/en/userGuide.html).

Run each task in both light and dark themes and repeat critical dialogs at 200% scaling.
Record exact spoken output, focus destination, expected outcome, observed outcome,
pass/fail/inconclusive and evidence file for each task:

| Task | Required observation | Result |
| --- | --- | --- |
| Start with empty storage | Application name, main regions and usable empty-state action; no silent dead end | NOT RUN |
| Create project and edit journey | Every input has a useful name; help/errors associated; JSON editor usable or limitation explicit | NOT RUN |
| Invalid journey / unavailable worker | Error announced once, actionable explanation; input retained; recovery reachable | NOT RUN |
| Authorize website, origin and effects | Permission scope understandable; checks and buttons announced; no accidental authorization | NOT RUN |
| Start, observe, cancel run | Busy/progress and completion announced without flooding; cancel always reachable | NOT RUN |
| Exploration proposal | Proposed action and state-changing risk readable before approval; decline/cancel works | NOT RUN |
| Recorder | Start/stop/completion controls and limitations readable; draft editable; no secret in saved evidence | NOT RUN |
| Findings and graph alternative | Severity, verification limits, evidence and ordered journey readable without relying on visual graph | NOT RUN |
| Validation and upload | Invalid fields/errors discoverable; native file picker cancellation and focus restoration usable | NOT RUN |
| Dialogs | Name/role, initial focus, Tab boundaries, Escape where supported and restored invoking focus | NOT RUN |
| Reusable profiles | Saved profile selection/name/settings announced; apply/edit/remove reachable; snapshots and zoom-emulation limits understandable | NOT RUN |
| Failure replay | Historical versus live evidence announced distinctly; target/steps/permissions readable before authorization; focus retained through new results and non-reproduction | NOT RUN |
| Approved root recovery | Navigation risk and retained untested branches readable; stopping never announced as inaccessible coverage | NOT RUN |
| Retest and reports | Failed/passed/inconclusive distinctions announced; exported HTML has meaningful structure | NOT RUN |
| Worker interruption | Interrupted status and restart path readable; no misleading success announcement | NOT RUN |

Use the owned compatibility app and accessible/broken fixtures, then a specifically
authorized real site. NVDA tests on the desktop shell and on a tested website are
separate results. Do not enter real passwords for a public demonstration. Include a
manual external-browser comparison if a WebView2 announcement differs.

Fail when a necessary task cannot be completed, focus is lost, a critical error is
silent, or a control's name/state is wrong. Mark unclear speech or browser-chrome focus
behavior inconclusive and investigate with a second human/configuration. Attach defects
with minimal reproducible journeys and repeat the exact task after correction. Store
the completed matrix in a dated record; update engineering status only after execution.
This procedure alone does not establish WCAG certification or a release pass.
