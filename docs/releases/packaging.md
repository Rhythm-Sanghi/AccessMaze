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

Clean application source: `746eaca94fae91a7749c1ce293ac721bc03f95a4`.
Archive: `dist/AccessMaze-hackyard-preview-746eaca.zip`, 389,996,150 bytes, 1,703 entries.
SHA-256: `6165c5693f9e57803cfa88d93c0525c59c3830527331e3aa7c0a3bb1b0ec1a53`.

Native feature/replay/profile/comparison/cancellation/crash checks, complex frozen
execution and System32-only checks passed. A fresh extraction under a Unicode/space
path also passed worker verification and native startup/shutdown. These checks reused
the developer machine's AppData/WebView2; they are not independent installation tests.
See [engineering status](../development/status.md).

## Release gates

The preview is unsigned. Complete [clean-machine verification](clean-machine.md),
manual accessibility/NVDA, independent security and redistribution review, CI,
performance/stability acceptance and signing before qualifying a release.
[Remaining actions](remaining-actions.md) specifies the required evidence.
Linux and macOS packaging have not been verified.
