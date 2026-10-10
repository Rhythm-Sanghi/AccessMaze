# Verification

[Engineering status](../development/status.md) records the tested source, results,
measurements, failures and release blockers. The latest application package is from
clean commit `746eaca`; later changes concern verification tools and documentation.

## Regression coverage

| Tests                                           | What they verify                                                                                                                          |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `test_website_exploration.py`                   | Multi-page/SPA branches, approvals, bounded recovery, frontier persistence, control-state identity and navigation-consistent observations |
| `test_replay.py`                                | Reproduction, correction, cancellation, redaction, immutable history and authorization boundaries                                         |
| `test_profiles.py`                              | Profile persistence, migration, browser conditions, keyboard/pointer outcomes, connectivity and focus assertions                          |
| `test_outcomes.py`                              | Mandatory assertions, cancellation, interruption and inconclusive coverage                                                                |
| `test_comparison_browser.py`, `test_retests.py` | Target-aware findings, changed conditions and conservative repair comparisons                                                             |
| `test_hackyard_demo.py`                         | Broken/fixed workflow, upload bytes, recorder replay and offline draft loss                                                               |

The recorded suite passed 112 Python, 9 React and 1 Rust tests. Browser regressions
launch Chromium; component tests separately exercise the interface.

## Native Windows checks

Launch the local preview with the test-only CDP helper, then run the harnesses:

```powershell
uv run --project engine python scripts/launch_preview.py --package AccessMaze-hackyard-preview
uv run --project engine python scripts/desktop_features.py --endpoint http://127.0.0.1:9224
uv run --project engine python scripts/desktop_comparison.py --endpoint http://127.0.0.1:9224
uv run --project engine python scripts/desktop_readiness.py --endpoint http://127.0.0.1:9224
uv run --project engine python scripts/desktop_website_smoke.py --endpoint http://127.0.0.1:9224
uv run --project engine python scripts/desktop_cancel.py --endpoint http://127.0.0.1:9224 --exe dist/AccessMaze-hackyard-preview/AccessMaze.exe
uv run --project engine python scripts/desktop_crash.py --endpoint http://127.0.0.1:9224 --exe dist/AccessMaze-hackyard-preview/AccessMaze.exe
```

These passed against the packaged WebView2/private IPC/frozen worker/Chromium stack
on the development laptop. Harnesses use owned targets and synthetic input. The CDP
port is test instrumentation; application code does not enable it.

Run [the demonstration](demo-script.md) to generate reports, a correction diff,
comparison and private SQLite evidence. Generated JSON reports remain local and are
ignored by Git. Screenshots in `docs/development/screenshots` come from the application.

Layout zoom is emulation. Browser semantics and keyboard automation are not NVDA
verification. Local packaging and test passes do not clear the independent release gates.
