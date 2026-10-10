"""Build a portable Windows preview with its own Python, driver, browser and axe script."""

import argparse
import hashlib
import json
import importlib.metadata
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def remove_unused_video_encoder(browser_root):
    # AccessMaze records semantic journey events, not video. Do not redistribute the
    # standalone static LGPL encoder installed by Playwright for record_video_dir.
    root = browser_root.resolve()
    for path in browser_root.glob("ffmpeg-*"):
        if not re.fullmatch(r"ffmpeg-\d+", path.name) or path.resolve().parent != root:
            raise ValueError(
                "Unexpected encoder path outside packaged browser resources"
            )
        if path.is_symlink() or path.is_junction():
            raise ValueError("Packaged encoder must be an ordinary directory")
        shutil.rmtree(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="AccessMaze-portable")
    args = parser.parse_args()
    if not re.fullmatch(r"AccessMaze-[A-Za-z0-9-]+", args.name):
        raise SystemExit(
            "Package name must be AccessMaze- followed by letters, digits or hyphens"
        )
    if sys.platform != "win32":
        raise SystemExit("This packaging recipe is currently Windows-only")
    output = ROOT / "dist" / args.name
    if output.exists():
        raise SystemExit(f"{output} exists; preserve or move it before rebuilding")
    output.mkdir(parents=True)
    npm = shutil.which("npm.cmd")
    if not npm:
        raise SystemExit("npm.cmd is missing")
    run([npm, "run", "tauri", "-w", "apps/desktop", "--", "build", "--no-bundle"])
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--exclude-module",
            "pytest",
            "--exclude-module",
            "tkinter",
            "--exclude-module",
            "IPython",
            "--exclude-module",
            "numpy",
            "--exclude-module",
            "scipy",
            "--exclude-module",
            "matplotlib",
            "--name",
            "accessmaze-worker",
            "--collect-all",
            "playwright",
            "--copy-metadata",
            "playwright",
            "--copy-metadata",
            "pydantic",
            "--copy-metadata",
            "networkx",
            "--paths",
            str(ROOT / "engine"),
            "--distpath",
            str(ROOT / "engine/dist"),
            "--workpath",
            str(ROOT / "engine/build"),
            "--specpath",
            str(ROOT / "engine/build"),
            str(ROOT / "scripts/worker_entry.py"),
        ]
    )
    shutil.copytree(ROOT / "engine/dist/accessmaze-worker", output, dirs_exist_ok=True)
    shutil.copy2(
        ROOT / "apps/desktop/src-tauri/target/release/accessmaze.exe",
        output / "AccessMaze.exe",
    )
    resources = output / "resources"
    resources.mkdir()
    shutil.copy2(ROOT / "node_modules/axe-core/axe.min.js", resources / "axe.min.js")
    notices = resources / "notices"
    notices.mkdir()
    for filename in ["LICENSE", "README.md", "SECURITY.md"]:
        shutil.copy2(ROOT / filename, notices / filename)
    for filename in ["LICENSE", "LICENSE-MIT", "LICENSE-APACHE"]:
        source = ROOT / "node_modules/axe-core" / filename
        if source.exists():
            shutil.copy2(source, notices / f"axe-core-{filename}")
    environment = {
        **os.environ,
        "PLAYWRIGHT_BROWSERS_PATH": str(resources / "browsers"),
    }
    run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=environment,
    )
    remove_unused_video_encoder(resources / "browsers")
    run(
        [
            sys.executable,
            "scripts/license_audit.py",
            "--output",
            str(notices / "dependencies"),
        ]
    )
    run(
        [
            sys.executable,
            "scripts/browser_credits.py",
            "--browsers",
            str(resources / "browsers"),
            "--output",
            str(notices / "chromium"),
        ],
        env=environment,
    )
    # Preserve the readable MPL-covered source alongside the unmodified minified script.
    shutil.copy2(ROOT / "node_modules/axe-core/axe.js", notices / "axe-core-source.js")
    for folder in ["testing", "releases"]:
        destination = notices / "procedures" / folder
        destination.mkdir(parents=True)
        for source in (ROOT / "docs" / folder).glob("*.md"):
            shutil.copy2(source, destination / source.name)
    (output / "PREVIEW.txt").write_text(
        "AccessMaze development preview. Run AccessMaze.exe. Requires Windows WebView2.\n"
        "Python, Node and a preinstalled Playwright browser are not required.\n"
        "Unsigned. Clean-machine installation and complete license manifest remain release gates.\n"
        "Standalone FFmpeg video encoder omitted; journey recording uses semantic events.\n"
        "Use only authorized test sites/accounts. See resources/notices/SECURITY.md.\n",
        encoding="utf-8",
    )
    shutil.copy2(
        ROOT / "scripts/Test-AccessMazePortable.ps1",
        output / "Test-AccessMazePortable.ps1",
    )
    manifest = {
        "schema_version": 1,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
        "python": sys.version,
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ["playwright", "pydantic", "networkx", "pyinstaller"]
        },
        "files": [
            {
                "path": path.relative_to(output).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": file_hash(path),
            }
            for path in sorted(output.rglob("*"))
            if path.is_file()
        ],
    }
    (output / "package-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(output)


if __name__ == "__main__":
    main()
