# ADR 002: explicit website permissions and private evidence

Accepted 2026-10-10. Extends ADR 001 without changing worker ownership or storage.

The target origin is always permitted. Additional navigation/API and read-only
resource origins are separate exact HTTP(S) allowlists, validated without paths,
wildcards, credentials or queries. Resource permission does not permit document
navigation or writes. Every configured hostname is resolved before launch; any
non-global answer requires explicit local-network authorization. Chromium uses
the fixed snapshot through host-resolver rules with system proxies disabled.
This trades automatic DNS failover/proxy compatibility for a stable test boundary.

Playwright request routing filters initial requests. Chromium CDP Fetch response
interception checks redirect destinations before the browser follows them.
An actual HTTP 302 regression test demonstrated why request routing alone was
insufficient. The page's interceptor must attach before navigation; other pages
default to denied. Popups and embedded document navigations are unsupported.
Service workers, downloads and WebSockets remain disabled. These are application
controls, not an OS network sandbox or protection against browser vulnerabilities.

Write permission exists while an effect-declared authored action executes and for
250 ms afterward to let requests scheduled by its DOM event reach interception.
Background writes outside that window are blocked, potentially changing application
behavior. GET can also have external effects; user authorization remains required.
If traffic is blocked, findings are inconclusive and repair comparisons cannot pass.

External website text is private by default. Titles, headings, control names and URL
paths become per-run HMAC tokens before observation persistence and fingerprinting.
The random key exists in memory only. Users may explicitly enable page-text evidence.
Authored labels/URLs are still intentionally saved; screenshots are fixture-only.
No HTTP bodies, cookies, browser traces or console text are included in reports.

Sources: [Playwright routing](https://playwright.dev/python/docs/api/class-route),
[isolated contexts](https://playwright.dev/python/docs/api/class-browsercontext),
[Chromium Fetch response interception](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/).

Further milestones must reuse these controls for authentication, recording and
exploration. No arbitrary imported code, persistent personal browser profiles or
unreviewed recorder replay is allowed.

Run-only input bindings contain names, never values or paths, in saved definitions.
Text and selected file buffers pass through private IPC and exist in memory during
execution. Password fields require run-only bindings. Files are bounded to 4 MiB
combined and set with Playwright's buffer API; imported paths cannot read disk.
Sensitive input requires HTTPS or explicitly approved private-address origins.
HMAC signatures use an ephemeral per-worker key; repair comparison refuses changed
inputs and comparisons across worker restarts rather than storing reusable secrets.
Native file chooser accessibility is outside this programmatic upload check.
