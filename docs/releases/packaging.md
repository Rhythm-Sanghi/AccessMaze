# Windows portable preview and release gates

Build from the repository root after installing the development prerequisites:

```powershell
uv run --project engine python scripts/package_windows.py
```

The script builds the Rust release host, freezes Python with PyInstaller and includes
the Playwright driver, exact full Chromium and headless-shell revision and local axe-core.
The current recipe removes Playwright's separately installed FFmpeg video encoder:
AccessMaze records semantic events and never requests video recording. This avoids
redistributing that unused standalone static binary; it does not clear FFmpeg/codecs
incorporated inside Chromium or other browser obligations. Older previews still contain
the standalone encoder and retain their original unresolved source/relink gate.
Actual frozen fixture/SPA/upload and recorder checks are required after this exclusion.
It writes `dist/AccessMaze-portable` and refuses to overwrite an existing package.
Use `--name AccessMaze-preview` to choose another new output directory.
Keep the entire directory together and launch `AccessMaze.exe`. Windows WebView2
is required; Python, Node, uv and a preinstalled browser are not required at runtime.

Packages include `package-manifest.json` with source commit/dirty state, dependency
versions, file sizes and SHA-256 hashes. This detects accidental corruption, not
authenticity; the preview is unsigned. Run the bundled systems-only checker:

```powershell
powershell -NoProfile -File .\Test-AccessMazePortable.ps1 -Package .
```

It checks hashes/path containment, starts the frozen worker with system-only PATH
and temporary storage containing spaces, runs three real Chromium fixture journeys,
checks JSON report identity and orderly EOF shutdown. It preserves the uniquely named
storage directory for diagnosis. No Python/Node installation is needed by this check.

The local `dist/AccessMaze-web-preview-final` build at `2285147` passed real WebView2/IPC/browser journeys,
worker crash recovery and a frozen-worker test using only Windows system tools on
PATH, a temporary working directory containing spaces and bundled browser resources.
It also passed native per-action website approval and visible recorder checks.
See `portable-smoke.json`, `portable-powershell.json`, `../testing/desktop-website.json`,
`../testing/desktop-crash.json` and engineering status.
This is same-machine verification, not a clean-machine installation test.

The preserved ZIP is `dist/AccessMaze-web-preview-final.zip`. Extract the entire
directory before launching `AccessMaze.exe`. Archive size, CRC verification and
SHA-256 are recorded in `preview-artifact.json`; this remains a development preview.

The preview is unsigned. Required gates before a release candidate:

- Windows CI execution of locked builds, tests and dependency compatibility checks.
- Clean Windows 11 installation, upgrade/removal and offline validation.
- Complete bundled third-party licenses, credits and SBOM.
- Threat-model review and broader network containment.
- Manual accessibility evaluation, performance/stress evidence and master acceptance criteria.
- Remaining authoring, recovery and general bounded exploration features.

Linux/macOS packaging and code signing require separate validation and resources.

## Readiness preview

`dist/AccessMaze-readiness-preview` was built with clean manifest source `fcd95a8`.
It preserves the earlier previews and adds collected dependency notices/inventory,
unmodified readable axe source, exact full Chromium credits and offline testing procedures.
The manifest covers 1,690 files. Frozen checks pass with system-only PATH, including the
owned multi-step HTTP SPA and actual upload, and native UI/approval/recorder/crash checks
pass on the developer laptop. Raw evidence is in `readiness-portable-*.json` and
`../testing/desktop-*.json`; see authoritative engineering status for exact commands.

The archive/hash/CRC record is `readiness-artifact.json`. The checked archive is unsigned;
its hash is not an authenticated distribution channel. This remains a development preview.
The [independent clean-machine procedure](clean-machine.md) remains NOT RUN. Collected
notices are an improvement, not complete redistribution clearance; the
[license audit](../architecture/dependencies.md) records unresolved obligations.

Archive a new package using:

```powershell
uv run --project engine python scripts/archive_preview.py --package dist/AccessMaze-readiness-preview --archive dist/AccessMaze-readiness-preview-new.zip --report docs/releases/readiness-artifact-new.json
```

The archive output must not exist. ZIP timestamps are clamped to its supported range
because some upstream notices carry Unix-epoch timestamps; contents remain unchanged.
The helper verifies every ZIP entry's CRC and records archive SHA-256. Neither locked
builds nor archive generation currently promise bit-for-bit reproducible binaries.

The previous locally verified artifact is `dist/AccessMaze-readiness-preview-final.zip`,
clean source **207a09a**, **391,203,383 bytes / 1,691 files**, with CRC/hash recorded in
`readiness-final-artifact.json`. Both final system-PATH/frozen-complex checks passed,
including the persisted in-flight connectivity limitation, and native UI/approval/
recorder/keyboard/error/crash checks passed again. Earlier artifacts remain preserved.
This is still same-machine, unsigned preview validation, with independent clean-machine
and redistribution gates open. See engineering status for actual results and limitations.

The current notice recipe includes five original MPL-covered native crate source archives
under resources/notices/dependencies/covered-source, linked from THIRD-PARTY-NOTICES.md.
They are ordinary gzip tar (.crate) archives, verified against Cargo.lock and every
published source file used by the compiler. Recipients can extract/read/modify them
offline under MPL-2.0. Independent review of complete source/rights obligations is still
required; this action does not clear all incorporated browser binaries.

## Release-validation continuation

Latest local ZIP: `dist/AccessMaze-release-validation-final.zip`, clean application/package source **228ad9c**. **390,002,137 bytes / 1,702 files**, SHA-256 **51d72674db90ff92feb06bf46d8aedd8991a2c9662f7c9e0cb5a3ebc9e3c180e**; CRC passed. Manifest covers 1,701 files, including five byte-verified MPL source archives, notice index and bundled Python/Chromium; no standalone FFmpeg. See `release-validation-artifact.json`.

Actual systems-only PowerShell checks passed on the built folder and a freshly extracted ZIP copy. Actual frozen fixtures plus the complex owned SPA/upload passed through a Unicode package alias and Unicode temporary storage. Three native startups inherited systems-only PATH. Native approval/recording/focus/errors and three worker crashes/recovery passed. Extracted application and its synthetic test storage were removed; actual user AppData/history preserved. These are developer-workstation checks, not an independent installation/removal/fresh-user/offline qualification. Subsequent commits change verification tooling/records, not the tested application runtime.

[Remaining actions](remaining-actions.md) identify human, independent-machine, rights, CI and signing gates. Do not distribute this unsigned preview as release-qualified.

## Remaining Hackyard features (746eaca)

Current local unsigned artifact: `dist/AccessMaze-hackyard-preview-746eaca.zip`, clean
application source **746eaca94fae91a7749c1ce293ac721bc03f95a4**, source_dirty=false,
**389,996,150 bytes / 1,703 entries**. SHA-256
**6165c5693f9e57803cfa88d93c0525c59c3830527331e3aa7c0a3bb1b0ec1a53**;
CRC passed. The manifest covers 1,702 files including bundled Python/Chromium, notices
and existing MPL sources. Local native feature/replay/profile/comparison/cancel/crash,
frozen complex SPA/upload and System32-only worker checks passed. Exact commands and
limitations: ../development/status.md and ../hackyard/final-feature-verification.json.
These results supersede earlier artifacts for this feature source, while preserving
older evidence. No signing, independent fresh-user/clean-machine or complete distribution
rights clearance is implied. Verification-tool/doc changes after packaging do not change
this artifact's application source.
