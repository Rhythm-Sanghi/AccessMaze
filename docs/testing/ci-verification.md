# CI verification

The `verify` workflow runs on main-branch pushes, pull requests and manual dispatches. Repository
permissions are read-only; obsolete runs are cancelled and jobs have bounded timeouts.

Windows and Ubuntu run locked Python/React tests with real Chromium, TypeScript/ESLint,
Ruff, formatting, contract validation and npm/Python advisory checks. Windows also
checks, formats and tests Rust, then runs cargo-audit. Advisory changes may fail a later
run; investigate them rather than suppressing the check.

After both check jobs pass, `windows-preview` builds the portable package, verifies it
with system-only PATH, runs the complex SPA/upload smoke and archives it with CRC/SHA
verification. The ZIP and reports are retained as Actions artifacts for 14 days.
Artifacts are unsigned previews.

The workflow previously passed local actionlint 1.7.7 and formatting checks. Local
syntax validation and package execution do not establish a completed remote CI result.

To verify a pushed commit:

1. Open the repository's Actions tab and select the `verify` run for the exact SHA.
2. Wait for both `checks` jobs and `windows-preview`; retain the run URL and conclusions.
3. Investigate failures and rerun after correction. Do not report queued jobs as passed.
4. Download the preview, check its source SHA/dirty state/hash and follow the independent
   Windows and accessibility procedures before release qualification.

Hosted Windows CI does not replace fresh standard-user, offline, upgrade/removal or
NVDA testing. Artifact storage does not provide code signing or legal clearance.


October 11 actual remote failures are retained in engineering status. The optional
owned-page Pa11y probe on Linux explicitly records `--no-sandbox` because the hosted
runner denied usable namespaces; this is not an application setting. Windows grants
only read/execute to the application-package SID on the downloaded test-browser cache,
following [Puppeteer sandbox guidance](https://pptr.dev/troubleshooting#chrome-reports-sandbox-errors-on-windows).
No credential/evidence path is granted and no scanner failure is automatically retried
or represented as a clean scan. Verify actual final-head conclusions before reporting success.
