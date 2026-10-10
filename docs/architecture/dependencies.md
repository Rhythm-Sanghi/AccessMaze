# Dependency and license review

AccessMaze's own source is MIT. Third-party distribution includes permissive and
file-level copyleft components. This inventory does not establish redistribution clearance.

| Component | Upstream license | Distribution consideration |
| --- | --- | --- |
| Tauri | MIT OR Apache-2.0 | Retain copyright and notices for bundled components |
| React, TypeScript, Vite, Vitest | MIT (TypeScript Apache-2.0) | Include resolved dependency notices |
| Playwright Python | Apache-2.0 | Include license and NOTICE where supplied |
| Pydantic | MIT | Retain license |
| NetworkX | BSD-3-Clause | Retain notice and disclaimer |
| axe-core | MPL-2.0 | Ship unmodified script with license/source attribution; modifications have file-level obligations |
| Python | PSF | Include runtime license when freezing |
| Chromium | BSD and third-party licenses | Ship Chromium's LICENSE/credits and all required notices |
| PyInstaller | GPL with bootloader exception | Review exception for executable distribution |
| SQLite | Public domain | Included through Python runtime |

Upstream references: [axe-core](https://github.com/dequelabs/axe-core),
[Playwright Python](https://github.com/microsoft/playwright-python),
[Tauri](https://github.com/tauri-apps/tauri).

The UI uses system fonts; no font files are redistributed. Platform icons are generated
from the repository's SVG. Lockfiles fix resolved Node, Python and Rust dependency sets.
CI audits Node/Python dependencies. A complete transitive license/notice manifest and
Rust advisory review are release gates; a table of direct dependencies alone does not
constitute a final redistribution audit.

## Readiness audit, 2026-10-10

`uv run --project engine python scripts/license_audit.py --output dist/license-audit-new`
inventories npm/uv locked packages and the resolved Windows Cargo graph, including
build dependencies. Latest execution: **627 components** (331 npm, 50 Python,
243 Cargo, 3 runtimes), **775 notice files copied**, **87 unresolved declarations or
notice sets**. Raw inventory/lock hashes: `../testing/license-inventory.json`. An initial
Windows locale decode failure was fixed by explicitly decoding Cargo metadata as UTF-8.
Missing optional-platform packages remain unresolved, not silently omitted or treated
as shipped infringements. This is not a complete verified SPDX/CycloneDX SBOM.

Packaging now preserves installed notices and unmodified readable `axe.js` alongside
the minified script and MPL license. It extracts notices offline from the exact full
Chromium binary, with executable hash/version provenance. The corrected extractor
preserves **754 sections / 8,296,049 characters**, including collapsed license bodies;
a browser regression checks this. Exported HTML is standalone, escaped and script-free.
Headless-shell and separately shipped DLLs still need an exact-binary review.

| Obligation family | Required distribution work / remaining review |
| --- | --- |
| MIT/BSD/ISC/Apache | Retain exact notices/disclaimers, supplied NOTICE and relevant patent terms; verify bundled modules against inventory. |
| MPL-2.0 | Preserve license, identify covered files and offer corresponding preferred source. axe readable source is now bundled. Cargo MPL components and source availability/notice plan still require review. |
| Unicode/CC-BY and other declarations | Preserve specific notice/attribution requirements; do not reduce compound expressions to MIT. Establish build-only inclusion. |
| Python/Node/PyInstaller | Include incorporated runtime notices and PyInstaller bootloader exception; the exception does not erase other components' obligations. |
| Chromium/graphics DLLs | Review exact credits, headless-shell, ANGLE/SwiftShader/Vulkan, Microsoft runtime redistribution rights and binary/source provenance. |
| FFmpeg | Actual `ffmpeg-win64.exe -L` identifies n7.0.1-playwright-build-1011, static LGPL 2.1-or-later build, libvpx and zlib. Copying LGPL text alone does not establish corresponding-source/relink compliance. A reproducible matching source/build plan remains a blocker. |

Primary references: [MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/),
[Chromium license](https://github.com/chromium/chromium/blob/main/LICENSE),
[FFmpeg legal guidance](https://ffmpeg.org/legal.html). Exact installed license texts,
not these summaries, govern distribution. Resolve missing entries, map source obligations
to shipped files, archive matching source/build information and obtain qualified
redistribution review before public release. No license clearance is claimed.
