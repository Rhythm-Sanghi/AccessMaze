# Engineering status

Updated 2026-10-10. Verification below records actual local execution.

## Implemented

Working Windows desktop preview with React/TypeScript, Tauri, a private-stdio Python
worker, SQLite and real Playwright Chromium journeys. Includes saved projects,
semantic journey authoring/import/export, runtime budgets, explicit authorization,
keyboard and permitted pointer interactions, completion assertions, local axe audits,
offline/reconnect checks, observed-state graphs, evidence and JSON/HTML/CSV reports.

Eight synthetic fixtures cover accessible and broken keyboard flows, error semantics,
value loss, branching/reset loops, long-running actions, modal focus and conditional
submission. Opt-in bounded discovery replays named button branches on resettable
fixtures only, counts actions and records unexplored frontier bounds.

Runs support cancellation, pause between steps, partial evidence and interruption
recovery. Windows job objects clean browser descendants after worker termination.
Retest comparisons enforce identical redacted configuration. Consistent ZIP backup,
explicit retention cleanup and storage migrations are implemented.

## Observed verification

| Check | Result |
| --- | --- |
| Python suite with real Chromium fixtures | 42 passed |
| React component tests | 2 passed |
| Rust Windows lifecycle test | 1 passed |
| TypeScript, ESLint, Ruff, formatting and generated contracts | Passed |
| Production frontend and Windows release host | Built successfully |
| npm and Python dependency audits | No known vulnerabilities; local Python project excluded from PyPI lookup |
| Actual packaged WebView2 → Rust → frozen Python → Chromium | Broken, accessible and conditional journeys passed |
| Desktop axe audit, light and dark | No reported violations; color contrast incomplete and requires manual evaluation |
| Frozen worker, system-only PATH, temporary directory with spaces | Three fixture runs and report checks passed; startup 1.634 seconds |
| Real worker crash | Development and packaged host recovery and Chromium cleanup passed |

Desktop audit injection uses test-only CDP evaluation; journey checks run with normal
application CSP. The packaged CSP correctly rejected ordinary inline script injection.
Screenshots in `screenshots/` are from the actual application.

The 15-run sequential benchmark measured 398.38 MiB peak summed RSS and 330.91 MiB
median sampled RSS for Python and child processes. Shared pages count in every
process's RSS. It excludes UI startup and long-running stress. Raw machine details
and timings are in `../testing/benchmark.json`; portable results are in
`../releases/portable-smoke.json`.

## Milestone and release limits

This is an operational preview across parts of milestones 1–7, with milestone 8
hardening. It does not complete the master specification. Milestone 9 remains gated.

- General external-site discovery, unreachable-state proof and resume after crash are absent.
- Recording assistance, uploads, preconditions, arbitrary zoom and advanced pointer profiles remain.
- Real assistive-technology integration, manual NVDA/high-contrast/keyboard evaluation and full UI performance testing remain.
- Retests are narrow; human annotations and a full finding lifecycle remain.
- DNS rebinding/non-HTTP containment and comprehensive security review remain.
- Journey inputs are plain text; synthetic data only. Redaction is best effort.
- Corruption recovery UI, large-history pagination and virtualization remain.
- The unsigned portable build was tested on this Windows machine with developer tools removed from PATH. Clean-machine installation, upgrade/removal, signing, complete third-party license manifest and SBOM remain unverified.
- CI is configured but has not run on GitHub. No upstream push or publication occurred.

## Next engineering tasks

1. Add recording assistance, upload/precondition authoring and viewport zoom checks.
2. Strengthen network containment before general external workflow discovery.
3. Expand stress, keyboard and assistive-technology evaluation.
4. Complete license/SBOM review and run Windows CI and clean-machine release checks.

The current environment provides one existing Windows developer machine and no
independent clean Windows installation or human assistive-technology evaluation.
Those release gates cannot be established by the automated tests above.

No full-spec completion, WCAG conformance or release-readiness claim is made.
