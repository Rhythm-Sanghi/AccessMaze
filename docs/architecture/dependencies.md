# Dependency and license review

AccessMaze's own source is MIT. The direct dependency choices are compatible with
permissive open-source distribution; this is an engineering inventory, not legal advice.

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
