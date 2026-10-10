# Review of the original 87 license and notice gaps

Internal engineering review, 2026-10-10. All 627 original components remain inventoried. The original inventory is retained at `../testing/license-inventory.json`; per-component evidence is in `license-gap-review.json` and immutable notice provenance in `upstream/provenance.json`. This is not independent legal clearance.

Actual commands:

```powershell
node scripts/license_ui_evidence.mjs dist/license-review-ui
uv run --project engine python scripts/license_audit.py --output dist/license-review-complete
uv run --project engine python scripts/license_gap_review.py --inventory dist/license-review-complete/inventory.json --modules dist/license-review-ui/modules.json --output docs/legal/license-gap-review.json
uv run --project engine pytest engine/tests/test_distribution_notices.py -q
```

Results: 627 components, 782 original notice files collected, 73 remaining raw metadata/notice flags. All 87 original rows classified: 71 npm packages excluded by the actual production module graph; 8 Python build/platform packages excluded by the actual frozen source TOC; 2 shipped Python packages have publisher classifier declarations and existing notices; 6 Windows crates now have preserved license text. The 73 raw flags represent 71 npm build/platform packages and two non-shipped Python packages (macholib and packageurl-python). They remain visible, not silently removed. Three distribution regressions passed, including actual full Chromium credits extraction.

`markdown-it-py` and `mdurl` really occur in the frozen worker despite being development-environment dependencies. Their notices remain mandatory. Five Rust texts come from exact crate VCS revisions. The selectors crate source itself explicitly names MPL 2.0; its full text comes from Mozilla, with the declaring source hash and crate revision recorded. The initial two attempted upstream LICENSE paths returned 404; the initial one-open-row review is preserved as `license-gap-review-initial.json`. No license was inferred from a package name.

The audit now recognizes suffix filenames such as `mit.LICENSE`, preserves publisher License classifiers verbatim when expression fields are absent, verifies supplement revision and bytes, and generates a human-readable THIRD-PARTY-NOTICES.md index linking original complete texts. Original declarations may not be SPDX expressions.

Potential incompatibilities / remaining obligations:

- No incompatibility was established solely by these 87 metadata flags. This does not clear the complete distribution.
- MPL-covered executable code requires accessible corresponding covered source, including exact selectors/cssparser/other covered crates and axe. The package includes readable unmodified axe source; establish and verify source delivery for all covered native code before release. See [Mozilla FAQ, executable distribution](https://www.mozilla.org/en-US/MPL/2.0/FAQ/#q8-i-want-to-distribute-outside-my-organization-executable-programs-or-libraries-that-i-have-compiled-from-someone-elses-unchanged-mpl-licensed-source-code-either-standalone-or-part-of-a-larger-work-what-do-i-have-to-do).
- FFmpeg static LGPL matching-source/build/relink compliance remains OPEN; copying license text is insufficient. Chromium/headless-shell incorporated source/notice obligations, Microsoft graphics and WebView2 loader redistribution provenance remain OPEN.
- PyInstaller bootloader exception is retained; development hook classifiers containing GPL are not a blanket GPL classification of AccessMaze. Review generated/runtime hooks separately.
- This graph/TOC evidence applies to the measured build recipe and lock hashes. Rebuild and reclassify after dependency or recipe changes. Binary embedded-library provenance is outside the 627 package labels.

| Component | Classification | Disposition |
| --- | --- | --- |
| npm @esbuild/aix-ppc64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/android-arm 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/android-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/android-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/darwin-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/darwin-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/freebsd-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/freebsd-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-arm 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-ia32 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-loong64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-mips64el 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-ppc64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-riscv64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-s390x 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/linux-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/netbsd-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/netbsd-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/openbsd-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/openbsd-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/openharmony-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/sunos-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/win32-arm64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/win32-ia32 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @esbuild/win32-x64 0.28.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @humanfs/types 0.15.0 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @napi-rs/lzma-linux-x64-gnu 1.5.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-android-arm-eabi 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-android-arm64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-darwin-arm64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-darwin-x64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-freebsd-arm64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-freebsd-x64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-arm-gnueabihf 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-arm-musleabihf 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-arm64-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-arm64-musl 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-loong64-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-loong64-musl 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-ppc64-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-ppc64-musl 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-riscv64-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-riscv64-musl 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-s390x-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-x64-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-linux-x64-musl 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-openbsd-x64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-openharmony-arm64 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-win32-arm64-msvc 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-win32-ia32-msvc 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-win32-x64-gnu 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @rollup/rollup-win32-x64-msvc 4.64.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-darwin-arm64 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-darwin-x64 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-linux-arm-gnueabihf 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-linux-arm64-gnu 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-linux-arm64-musl 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-linux-riscv64-gnu 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-linux-x64-gnu 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-linux-x64-musl 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-win32-arm64-msvc 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-win32-ia32-msvc 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm @tauri-apps/cli-win32-x64-msvc 2.12.1 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm esrecurse 4.3.0 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm fsevents 2.3.3 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm imurmurhash 0.1.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm keyv 4.5.4 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm natural-compare 1.4.0 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm saxes 6.0.0 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| npm stackback 0.0.2 | false positive / non-distributed build or platform dependency | excluded from application redistribution gap count |
| python colorama 0.4.6 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python macholib 1.16.4 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python markdown-it-py 4.2.0 | missing metadata / required attribution | metadata recovered and original notices preserved |
| python mdurl 0.1.2 | missing metadata / required attribution | metadata recovered and original notices preserved |
| python packageurl-python 0.17.6 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python pip-audit 2.10.1 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python pip-requirements-parser 32.0.1 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python pyinstaller-hooks-contrib 2026.8 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python ruff 0.13.1 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| python tomli-w 1.2.0 | false positive / non-distributed development or platform dependency | excluded from application redistribution gap count |
| cargo alloc-stdlib 0.3.0 | genuine redistribution obligation / required notices | original upstream notice preserved |
| cargo defmt-parser 1.0.0 | genuine redistribution obligation / required notices | original upstream notice preserved |
| cargo selectors 0.38.0 | genuine redistribution obligation / required notices | original upstream notice preserved |
| cargo webview2-com 0.39.1 | genuine redistribution obligation / required notices | original upstream notice preserved |
| cargo webview2-com-macros 0.8.1 | genuine redistribution obligation / required notices | original upstream notice preserved |
| cargo webview2-com-sys 0.39.1 | genuine redistribution obligation / required notices | original upstream notice preserved |

## Covered native source delivery follow-up

The audit now preserves the five resolved MPL crate source archives offline, links them from THIRD-PARTY-NOTICES.md, and explicitly makes the covered source available under MPL-2.0. Each original .crate matches Cargo.lock SHA-256 and all 66 published files match the actual compiler registry sources byte for byte. The five archive hashes/counts are in covered-source-verification.json. A regression rejects either a lock checksum mismatch or modified compiler sources. Five distribution tests passed; actual audit still reports 627 components, 782 notices and 73 non-distributed raw flags. Browser incorporated code/source, axe preferred-source review, Microsoft runtime provenance and independent legal clearance remain open. Earlier paragraphs describe the initial review and are superseded only for this native-source delivery action.
