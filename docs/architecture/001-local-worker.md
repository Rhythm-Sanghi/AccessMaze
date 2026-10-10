# ADR 001: private worker and authored-path analysis

Accepted for the development preview, 2026-10-10.

React renders the application in Tauri 2. Rust owns one persistent Python process.
Version 1 messages use UTF-8, one JSON object per line. Requests contain `version`,
`id`, `method`, `params`; responses echo version/id and contain `result` or `error`.
Only a fixed method allowlist is accepted. No imported Python, shell command or
JavaScript is executed. Runs execute on a dedicated Python thread with a separate
asyncio loop. SQLite connections are short-lived, transactional and foreign-key aware.
Frontend polling reads real persisted progress at most about twice per second.

This avoids a local analysis HTTP service, authentication tokens and listening ports.
The synthetic fixture server is the sole loopback listener. Target pages run in
fresh Playwright contexts outside the desktop WebView; they never receive Tauri IPC.
The host serializes short commands and applies a response timeout. Transport failures
discard the worker; a subsequent request starts it again. Windows assigns the worker
to a job object so surviving descendants terminate when its owning handle closes.
Closing stdin
requests cancellation/cleanup; Windows process-tree termination is a last resort.

The authored-path runner is easier to audit than an unconstrained crawler.
Each run has at most 100 steps, 200 Tab presses per target, 300 seconds and one browser.
An assertion is mandatory. State identity hashes a normalized URL without queries,
document title, heading text, bounded control attributes, focus and network/motion state.
Input contents are reduced to a populated flag. Redaction precedes hashing/persistence.
Dynamic labels can split equivalent states; omitted application internals can merge
distinct states. A graph is an observation record, not a complete model of a site.
Multi-edges retain repeated actions even when nodes deduplicate.

An opt-in breadth-first explorer supports only resettable bundled fixtures. It discovers
named visible buttons in sorted order, replays the base journey and prior path, verifies
the replay fingerprint, then activates one candidate. Every replay and discovery action
counts against a shared action budget. Depth, wall time, duplicate-state suppression,
cancellation and recorded frontier bounds apply. A divergent replay is skipped and
recorded. No claim is made about unnamed controls, links, field-value combinations or
arbitrary external applications.

## Reuse and differentiation

[Playwright actions](https://playwright.dev/python/docs/input) provide real key presses
and semantic locators. [Playwright accessibility guidance](https://playwright.dev/docs/accessibility-testing)
supports reusing axe-core while retaining manual evaluation. AccessMaze adds task
assertions, capability-specific action execution, state transitions, evidence, persistence
and recovery checks. It does not reproduce axe-core's individual rules.

[Tauri sidecars](https://v2.tauri.app/develop/sidecar/) support packaged workers.
Development uses the repository virtual environment; release mode requires a frozen
worker and bundled matching Chromium. A development Python installation is not a
distribution strategy. Packaging gates are documented separately.

## Principal risks

- Keyboard activation can reach a control while its subsequent result still fails.
  Explicit completion assertions must verify the application outcome.
- A finite Tab budget provides bounded evidence, not proof over all possible key sequences.
- A live region's existence does not prove an assistive technology announces an error.
- Same-origin routing can break external assets; this is recorded as a limitation.
- DNS preflight is not a hardened network sandbox; DNS rebinding and non-HTTP browser
  transports require additional containment before hostile-target use.
- Paused wall time counts toward the run deadline; a paused run can time out.
- Screenshots and dynamic labels can expose data; synthetic targets remain the intended use.
