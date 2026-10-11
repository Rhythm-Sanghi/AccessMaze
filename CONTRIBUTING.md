# Contributing

Keep `main` as the only long-lived branch. Small, verified changes may go directly
to `main` when explicitly authorized and repository rules permit. Use a temporary
branch and normal pull-request review for high-risk changes; delete that branch
after verifying the merge. Never bypass required checks or branch protection.
Preserve release checkpoints and necessary development history with documented
commits or tags, rather than permanent development, staging or backup branches.
Before deleting a squash-merged branch, verify its content and preserve any
historical commits needed for legal or Hackyard evidence.

Use the setup and verification commands in README. Keep changes scoped to an observable
behavior, describe the problem and include the checks you actually ran. Never present
mocked browser results as integration or end-to-end evidence.

Python owns analysis, persistence and redaction. React owns presentation. Rust owns process
lifecycle and IPC. Edit Pydantic models first when changing contracts, regenerate schemas
with `npm run contracts`, update TypeScript types and add compatibility coverage.

Use synthetic fixture data only. Add regression tests for meaningful failures, avoid broad
exception suppression and document unsupported behavior. Run Ruff format, Prettier, type
checks, relevant tests and dependency audits. Do not commit environments, binaries, run data,
screenshots containing personal information, secrets or build output.

The optional Pa11y benchmark has its own lockfile and is not bundled with the app.
Follow docs/testing/comparative-corpus.md to run it against owned targets. Preserve
scanner failures as inconclusive results and keep task execution distinct from an
initial-page scan. Native harnesses require a dedicated test desktop; never attach
them to a session with unrelated active work. Save raw measurements outside Git and
record exact source, commands, results and limits in docs/development/status.md.

Discuss large architecture changes in an issue or ADR. See SECURITY.md for private reporting
and CODE_OF_CONDUCT.md for participation expectations. Contributions use the repository license.
