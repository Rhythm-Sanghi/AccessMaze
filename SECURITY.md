# Security

This is an early development build for synthetic fixtures and authorized test sites.
Use dedicated test accounts and synthetic data. Do not test hostile sites, import
personal browser profiles or enter production secrets or unrelated personal data.

- No remote account, analytics or network analysis endpoint is used.
- The desktop WebView never loads target pages; fresh Chromium contexts do.
- Target URLs allow HTTP(S) only. Embedded credentials and target queries are rejected.
- Private/reserved addresses need explicit authorization. Configured host DNS answers
  are pinned for the browser lifetime. Exact navigation/API and read-only resource
  origins are separate permissions. Response interception checks HTTP redirects.
  Popups/embedded frames, service workers/downloads and WebSockets are disabled.
- This is not a strong security sandbox. DNS rebinding, WebSocket/WebRTC traffic and
  browser vulnerabilities require additional containment before hostile-target use.
- Activations and Enter/Space require an effect declaration. Every run requires target
  authorization, and effectful runs require explicit additional authorization.
  GET requests can have effects too; use synthetic targets and inspect every action.
- External exploration requires approval of each specific proposed action and never
  resets/replays an external workflow. Bounded fingerprints can refuse observed changes;
  they cannot guarantee identical hidden state or prevent all concurrent application changes.
- Recording has separate target/manual-session authorization. Background scripts may
  write to approved navigation/API origins during that session. Typed values/files are
  not captured, but labels and explicitly captured completion text require privacy review.
- Imported definitions use strict schemas, bounded strings/budgets and semantic targets.
  Arbitrary scripts, commands and file navigation are unsupported. Uploads accept only
  selected buffers with path-free names, bounded to 4 MiB combined per run.
- Password fields require run-only input bindings and HTTPS or an approved private
  test origin. Values and file buffers are in memory only; cookies use isolated ephemeral
  contexts. Saved literal journey input values are plain text in SQLite.
  Run evidence removes those values; screenshots mask form fields and are enabled only
  for synthetic fixtures. Unrelated sensitive text is not guaranteed to be removed.
- External page text is withheld using per-run tokens by default. Enabling page-text
  evidence can persist unrelated personal data. Authored labels and target URLs are saved.
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
