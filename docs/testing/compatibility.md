# Compatibility corpus

Run from the repository root with the documented workspace Chromium cache:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.accessmaze/browsers'
uv run --project engine pytest engine/tests/test_compatibility_app.py engine/tests/test_compatibility_regressions.py -q
uv run --project engine python scripts/compatibility.py
uv run --project engine python scripts/compatibility.py --public
```

The default executes only owned loopback servers. `--public` explicitly enables three
allowlisted educational cases, once each, sequentially. It does not crawl links, log in,
upload to public sites or interact with production accounts. Do not put arbitrary sites
in this corpus without establishing scope/authorization. Public availability and content
can change; failures must be retained, investigated and distinguished from engine defects.

| Case | Purpose / scope | Expected evidence |
| --- | --- | --- |
| Owned Hackyard application | HTTP SPA + separate CORS API, delayed mount, validation, radio route, conditional passport field, native dialog/restore, offline/reconnect, multipart upload and confirmation | 19 authored steps, one actual API submission, exact selected bytes and international route; no axe violations in this bounded scenario |
| Selenium official web form | Keyboard fill and GET submit to its dedicated automation example, then confirmation audit | Completion assertion and recorded audit; incomplete/manual checks remain |
| W3C BAD before | Read-only educational inaccessible page audit | Observed missing-alt/name/language findings; exact totals are not a stable oracle |
| W3C BAD after | Read-only comparison audit | Fewer observed rules, not a certification or a guarantee of zero axe findings |

Sources/scope rationale: Selenium's [official first-script tutorial](https://www.selenium.dev/documentation/webdriver/getting_started/first_script/)
demonstrates this form submission. W3C's [Before and After Demonstration](https://www.w3.org/WAI/demos/bad/Overview.html)
provides educational before/after examples. Selenium's CDN origins were inspected and
approved as read-only resources, separately from navigation. Neither source grants
authorization for unrelated workflows or load testing. Public pages are not copied into
the distribution. Controlled application code is original MIT-licensed project test code.

`compatibility.json` records actual latest results. `compatibility-initial.json` preserves
the first probe: incomplete resource permissions for Selenium and incorrectly authored
W3C heading names. The names were corrected against actual browser headings (including
the hyphen), and exact CDN origins were added; no networking controls were relaxed.
The final local run completed all four paths without compromised origin coverage.
W3C before exposed seven rule IDs; after still exposed `landmark-one-main` and `region`.
This is not a WCAG assessment or an assertion that the teaching site is defective under
every modern rule. Axe outcomes depend on rule version, rendering, scope and manual review.

## Confirmed automation defects and regression oracles

- Native radio activation used Enter, which did not select the option. Space now selects it.
- A checked native radio group has one Tab stop. A bounded, actual ArrowRight search
  within the same native name/form/root now reaches other options; it does not use `.check()`.
- Dynamic fill rejected an absent field before waiting. It now waits within the action timeout.
- A disabled target was called keyboard-unreachable. It now yields an inconclusive prerequisite finding.
- An unrelated populated live region could mask undiscoverable errors. Only related
  error text/containers or focused invalid fields satisfy the implemented signal check.
  Unverified discoverability and native browser validation are reported inconclusively.
- A native dialog moves focus into browser chrome between Tab cycles. `document.hasFocus()`
  was false: that is not evidence of focus reaching another page control. Page-focus escape
  is still detected, and browser-chrome/OS focus remains explicitly manual. The final
  keyboard move is now checked as well.
- A real axe audit detects an unnamed button and clears that rule after adding its actual
  name. That oracle does not imply axe can assess whether a name is meaningful or correct.

Known false-negative classes remain: misleading labels/alt text, usability, meaningful
reading order, closed shadow trees, OS focus, AT announcements and unvisited states.
No automated result upgrades these into verified conformance.
