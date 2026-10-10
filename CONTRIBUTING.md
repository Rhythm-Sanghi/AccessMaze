# Contributing

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

Discuss large architecture changes in an issue or ADR. See SECURITY.md for private reporting
and CODE_OF_CONDUCT.md for participation expectations. Contributions use the repository license.
