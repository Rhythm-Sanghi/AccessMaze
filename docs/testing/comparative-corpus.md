# Paired browser compatibility corpus

`scripts/comparative_benchmark.py` serves owned local applications and executes
sixteen real Chromium cases: broken/corrected date selection, intermediate form
steps, validation focus, error recovery, offline draft retention, SPA navigation,
conditional navigation and an unnamed-button calibration. Expected outcomes are
reviewable in `corpus()`; raw engine results determine actual outcomes. The test
fails for an incorrect task label, an absent expected rule, unexpected confirmed
findings, or a requested scanner that does not complete.

## Reproduce

From the repository root, with Node, uv and the repository browser cache installed:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/.accessmaze/browsers"
$env:PUPPETEER_SKIP_DOWNLOAD = 'true'
npm ci --prefix benchmarks/pa11y
uv run --project engine python scripts/comparative_benchmark.py --output dist/Corpus-review --pa11y
```

Use a new output directory. The script never overwrites an earlier run. Without
`--pa11y`, the optional scanner is explicitly recorded as not run. The optional
Pa11y 10.0.0 lock is outside application workspaces and packaging: it is a
benchmark tool, not a bundled application dependency. Its LGPL-3.0-only metadata
and its dependencies retain their own licenses; the application MIT license does
not relicense them. `npm audit --prefix benchmarks/pa11y --audit-level=moderate`
reported zero vulnerabilities locally. This is not a legal opinion.

## Scope and fairness

AccessMaze executes an authored keyboard task, including assertions at the relevant
interaction state. Axe and Pa11y/HTMLCS examine the same initial page in fresh
contexts with the recorded viewport. Pa11y can perform configured actions; this
baseline does not exercise them. A clean initial scan is not a false negative for
a later task failure. Workloads and timing differ: this experiment does not rank
scanner speed, establish general accuracy, or prove that other tools cannot test
these interactions. The cases are controlled applications, not a representative
sample of the public web. Accessibility Insights and manual announcements are
not evaluated. Offline mode uses Chromium network emulation.

Each output includes source commit/dirty state, timestamps, CPU/RAM/OS, actual
browser and engine versions, axe hash, tool lock hash, configuration, fixture HTML,
raw run JSON, scanner stdout/stderr, expected outcomes, actual outcomes, unexpected
confirmed findings, comparisons and timing. CI runs the regression on Windows and
Linux and uploads these records for fourteen days. Outputs contain only owned
synthetic content; do not substitute credentials or private sites into this corpus.

## Observed local result

On 11 October 2026, the CI-style regression with the locked Pa11y installation
passed: **1 test, 74.58 seconds**, sixteen cases. Seven broken journeys were blocked;
the other nine completed, including the static-calibration broken case whose task
is deliberately still possible. All eight expected rules were observed, all eight
working cases had no unexpected confirmed findings, and all eight paired
comparisons reported verified improvement under the script's matching conditions.
Both initial scanners identified the unnamed-button calibration; the other initial
pages had no reported violations. This does not establish absence of other defects.

Actual versions: Chromium 153.0.8010.12, Playwright 1.63.0, axe 4.10.3,
Pa11y 10.0.0, Python 3.13.9, NetworkX 3.7, Windows 11 build 26220.
Raw local records: `dist/Corpus-CI-local`; JUnit: `dist/corpus-regression.xml`.
The source was a dirty working tree based on `109d90e`; final clean-commit CI
verification remains a separate check. No NVDA or independent evaluation occurred.
