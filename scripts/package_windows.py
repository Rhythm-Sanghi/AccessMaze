"""Build a portable Windows preview with its own Python, driver, browser and axe script."""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    subprocess.run(args, cwd=ROOT, check=True, **kwargs)


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
        raise SystemExit(
            "dist/AccessMaze-portable exists; preserve or move it before rebuilding"
        )
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
        [sys.executable, "-m", "playwright", "install", "--only-shell", "chromium"],
        env=environment,
    )
    (output / "PREVIEW.txt").write_text(
        "AccessMaze development preview. Run AccessMaze.exe. Requires Windows WebView2.\n"
        "Python, Node and a preinstalled Playwright browser are not required.\n"
        "Unsigned. Clean-machine installation and complete license manifest remain release gates.\n"
        "Use synthetic local fixtures only. See resources/notices/SECURITY.md.\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
