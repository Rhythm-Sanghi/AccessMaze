# Security

This is an early development build for synthetic fixtures and authorized test sites.
Do not use it to test hostile sites or enter secrets, credentials or real personal data.

- No remote account, analytics or network analysis endpoint is used.
- The desktop WebView never loads target pages; fresh Chromium contexts do.
- Target URLs allow HTTP(S) only. Embedded credentials and target queries are rejected.
- Private/reserved network targets need explicit authorization; requests are restricted
  to the configured origin, including redirects. Service workers/downloads are disabled.
- This is not a strong security sandbox. DNS rebinding, WebSocket/WebRTC traffic and
  browser vulnerabilities require additional containment before hostile-target use.
- Activations and Enter/Space require an effect declaration. Every run requires target
  authorization, and effectful runs require explicit additional authorization.
  GET requests can have effects too; use synthetic targets and inspect every action.
- Imported definitions use strict schemas, bounded strings/budgets and semantic targets.
  Arbitrary scripts, commands, file navigation and file upload are unsupported.
- Password fields are blocked. Journey input values are plain text in SQLite.
  Run evidence removes those values; screenshots mask form fields and are enabled only
  for synthetic fixtures. Unrelated sensitive text is not guaranteed to be removed.
- HTML reports escape target content and disable scripts. CSV neutralizes formula prefixes.
- Artifact lookups require a run-owned filename and validated UUID directory.
- Deleting a project cascades saved runs and removes artifact directories. Secure erasure
  of SSD blocks, SQLite WAL history and backups is not guaranteed.

Report suspected vulnerabilities privately through GitHub's private vulnerability reporting
for this repository if enabled. Otherwise contact the repository owner privately before
publishing exploit details. Do not include personal information in public issues.

Before public release: complete threat-model review, strengthen network policy, audit all
bundled binaries, test retention/recovery and verify clean-machine installation. No trusted
code signing is claimed. Unsigned Windows builds can trigger SmartScreen warnings.
