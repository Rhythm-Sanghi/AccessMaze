# Windows portable packaging

Build from the repository root with the development prerequisites in README installed:

```powershell
uv run --project engine python scripts/package_windows.py --name AccessMaze-preview
```

The output directory must not already exist. The script builds the Rust release host,
freezes Python with PyInstaller and bundles Playwright, Chromium/headless-shell,
axe-core, third-party notices and covered native source archives. AccessMaze does not
record video; the unused standalone FFmpeg encoder is excluded. Incorporated browser
codec obligations still require review.

Keep the directory together and launch `AccessMaze.exe`. WebView2 is required;
Python, Node, uv and a separately installed browser are not runtime prerequisites.

## Verification

`package-manifest.json` records the source commit, dirty state, dependency versions,
file sizes and SHA-256 hashes. Hashes detect corruption; they do not authenticate an
unsigned publisher.

```powershell
powershell -NoProfile -File scripts/Test-AccessMazePortable.ps1 -Package dist/AccessMaze-preview -Report dist/portable-verification.json
uv run --project engine python scripts/portable_smoke.py --package AccessMaze-preview --complex --report dist/complex-verification.json
uv run --project engine python scripts/desktop_startup.py --package AccessMaze-preview
uv run --project engine python scripts/archive_preview.py --package dist/AccessMaze-preview --archive dist/AccessMaze-preview.zip --report dist/archive-verification.json
```

The PowerShell checker runs without developer tools on PATH. It verifies the manifest,
executes three bundled fixture journeys, checks exported run identity and tests EOF
shutdown. The complex smoke adds an owned SPA, API calls and multipart upload.
The archive helper refuses overwrite, checks CRC and records SHA-256. ZIP timestamps
are clamped to the supported range; bit-for-bit build reproducibility is not established.
Reports are generated locally and ignored by Git.

## Latest local preview

Clean application source: `432dd5f385aaecbfebb8b36fae28cc439ac1019b`.
Archive: `dist/AccessMaze-investigation-preview-432dd5f.zip`, 390,039,679 bytes, 1,707 entries.
SHA-256: `cfb33a28ca777acb801279e666560ec9abc7bddc49e075e9aff05905dc25449c`.

Native approvals/replay/profile/comparison/manual-plan/history/draft/cancellation/crash
checks, complex frozen execution and system-only-PATH checks passed. Unicode/space
extraction passed frozen verification. These reuse the developer machine's
AppData/WebView2; independent installation remains unverified. Older `746eaca`
measurements are historical. See [engineering status](../development/status.md).

## Release gates

The preview is unsigned. Complete [clean-machine verification](clean-machine.md),
manual accessibility/NVDA, independent security and redistribution review, CI,
performance/stability acceptance and signing before qualifying a release.
[Remaining actions](remaining-actions.md) specifies the required evidence.
Linux and macOS packaging have not been verified.
