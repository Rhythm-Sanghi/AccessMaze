# CI implementation and verification

The `verify` workflow runs on push, pull request and manual dispatch, with read-only
repository permissions, cancellation of obsolete runs and bounded job timeouts.
Windows and Ubuntu check locked Python/React tests, real Chromium, TypeScript/ESLint,
Ruff, formatting, contracts and npm/Python advisories. Windows also tests/formats Rust
and runs pinned cargo-audit. Advisory database changes can legitimately fail a later run;
do not blanket-ignore them. The previously observed all-platform informational Rust
warnings are documented in the security review.

After both check jobs pass, `windows-preview` builds the portable native/frozen package,
uses the systems-only PowerShell checker, runs the complex real-browser/upload smoke,
archives with CRC/SHA verification and uploads the ZIP plus results for 14 days.
Artifacts are unsigned previews. Hosted Windows CI does not replace independent fresh
standard-user/offline/upgrade/removal verification or actual NVDA evaluation.

Local workflow validation used actionlint **1.7.7**, downloaded from its official release
and checked against the release checksum list. Windows AMD64 archive SHA-256:
`7f12f1801bca3d480d67aaf7774f4c2a6359a3ca8eebe382c95c10c9704aa731`.
`dist/actionlint-1.7.7/actionlint.exe .github/workflows/ci.yml` passed. Prettier passed.
The package commands are also executed locally and recorded separately in engineering
status. Validation of syntax and local commands is not a remote Actions pass.

Remote status: **NOT RUN for this continuation**. GitHub CLI is absent. The available
GitHub connector can read commit/PR workflow results but exposes no workflow dispatch
operation. Its query for `275a4e1873cb022e6d6ca903a0e2c42d89906eeb` returned zero
PR-triggered runs; that limited result does not prove absence of every other trigger.
No workflow upload/push, remote run or publication is asserted.

Required maintainer action with repository write access:

1. Push the reviewed committed continuation to a branch on the repository; open its
   pull request or dispatch `verify` for that branch in GitHub Actions.
2. Wait for both `checks` matrix jobs and `windows-preview` to finish. Save the run URL,
   exact SHA, attempt number, job conclusions and logs. Correct failures and rerun.
3. Download the produced preview artifact; compare its source SHA, dirty=false and
   archive hash with the recorded results. Retain provenance before artifact expiry.
4. Update status only with the actual completed result, and submit that exact archive
   to the independent Windows and manual accessibility procedures.

GitHub's [artifact action documentation](https://github.com/actions/upload-artifact)
describes artifact handling. Uploading an artifact provides CI storage, not code signing
or independent distribution/legal qualification.
