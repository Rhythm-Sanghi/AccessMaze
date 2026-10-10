# Windows portable preview and release gates

Build from the repository root after installing the development prerequisites:

```powershell
uv run --project engine python scripts/package_windows.py
```

The script builds the Rust release host, freezes Python with PyInstaller and includes
the Playwright driver, exact full Chromium and headless-shell revision and local axe-core.
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

The local `dist/AccessMaze-preview` build passed real WebView2/IPC/browser journeys,
worker crash recovery and a frozen-worker test using only Windows system tools on
PATH, a temporary working directory containing spaces and bundled browser resources.
See `portable-smoke.json`, `../testing/desktop-crash.json` and engineering status.
This is same-machine verification, not a clean-machine installation test.

The preview is unsigned. Required gates before a release candidate:

- Windows CI execution of locked builds, tests and dependency compatibility checks.
- Clean Windows 11 installation, upgrade/removal and offline validation.
- Complete bundled third-party licenses, credits and SBOM.
- Threat-model review and broader network containment.
- Manual accessibility evaluation, performance/stress evidence and master acceptance criteria.
- Remaining authoring, recovery and general bounded exploration features.

Linux/macOS packaging and code signing require separate validation and resources.
