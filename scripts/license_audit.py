"""Inventory locked dependencies and preserve installed notices; not legal qualification."""

import argparse
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notices(folder):
    if not folder.is_dir():
        return []
    candidates = list(folder.iterdir())
    for name in ["licenses", "license", "LICENSES"]:
        child = folder / name
        if child.is_dir():
            candidates.extend(child.rglob("*"))
    return sorted(
        {
            p
            for p in candidates
            if p.is_file()
            and (
                p.parent != folder
                or p.name.upper().startswith(
                    ("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT")
                )
            )
        }
    )


def audit(output):
    output.mkdir(parents=True, exist_ok=False)
    records = []

    def record(ecosystem, name, version, license, folder, **extra):
        index = len(records)
        copied = []
        for source in notices(folder):
            target = output / "notices" / f"{index:04d}" / source.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(
                {
                    "path": target.relative_to(output).as_posix(),
                    "sha256": digest(target),
                }
            )
        records.append(
            {
                "ecosystem": ecosystem,
                "name": name,
                "version": version,
                "declared_license": license,
                "notices": copied,
                **extra,
            }
        )

    lock = json.loads((ROOT / "package-lock.json").read_text())
    for path, package in lock["packages"].items():
        if not path or package.get("link") or not path.startswith("node_modules/"):
            continue
        record(
            "npm",
            path.split("node_modules/")[-1],
            package.get("version"),
            package.get("license"),
            ROOT / path,
            integrity=package.get("integrity"),
            scope="locked build/runtime dependency; dev flag does not prove absence from bundle",
            dev=package.get("dev", False),
        )
    python_lock = tomllib.loads((ROOT / "engine/uv.lock").read_text())
    for package in python_lock["package"]:
        if package["name"] == "accessmaze-engine":
            continue
        try:
            dist = metadata.distribution(package["name"])
            folder = Path(dist._path)
            license = dist.metadata.get("License-Expression") or dist.metadata.get(
                "License"
            )
        except metadata.PackageNotFoundError:
            folder, license = Path("__not_installed__"), None
        record(
            "python",
            package["name"],
            package["version"],
            license,
            folder,
            scope="uv locked build/runtime environment",
            artifacts=package.get("wheels", []),
        )
    cargo = json.loads(
        subprocess.check_output(
            [
                "cargo",
                "metadata",
                "--locked",
                "--format-version",
                "1",
                "--filter-platform",
                "x86_64-pc-windows-msvc",
            ],
            cwd=ROOT / "apps/desktop/src-tauri",
            text=True,
            encoding="utf-8",
        )
    )
    resolved = {n["id"] for n in cargo["resolve"]["nodes"]}
    for package in cargo["packages"]:
        if package["id"] not in resolved or package["name"] == "accessmaze":
            continue
        record(
            "cargo",
            package["name"],
            package["version"],
            package["license"],
            Path(package["manifest_path"]).parent,
            scope="resolved Windows graph, includes build dependencies",
            source=package["source"],
        )
    record(
        "runtime",
        "CPython",
        sys.version.split()[0],
        "PSF-2.0 and incorporated notices",
        Path(sys.base_prefix),
        scope="frozen Python runtime",
    )
    driver = ROOT / "engine/.venv/Lib/site-packages/playwright/driver"
    record(
        "runtime",
        "Playwright Node driver",
        metadata.version("playwright"),
        "see notices",
        driver,
        scope="bundled node.exe",
    )
    record(
        "runtime",
        "playwright-core driver bundle",
        metadata.version("playwright"),
        "Apache-2.0 and incorporated notices",
        driver / "package",
        scope="bundled JavaScript driver",
    )
    result = {
        "schema": "AccessMaze engineering dependency inventory v1; not SPDX/CycloneDX certification",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "lock_sha256": {
            p: digest(ROOT / p)
            for p in [
                "package-lock.json",
                "engine/uv.lock",
                "apps/desktop/src-tauri/Cargo.lock",
            ]
        },
        "components": records,
        "unresolved": [
            {
                "ecosystem": r["ecosystem"],
                "name": r["name"],
                "version": r["version"],
                "missing": [
                    k
                    for k, value in {
                        "declared_license": r["declared_license"],
                        "notice_files": r["notices"],
                    }.items()
                    if not value
                ],
            }
            for r in records
            if not r["declared_license"] or not r["notices"]
        ],
        "release_blockers": [
            "Component labels are not a verified redistribution clearance",
            "Chromium/headless-shell exact binary credits and incorporated libraries require review",
            "FFmpeg static LGPL source/relink obligations require a reproducible corresponding-source plan",
            "Microsoft graphics runtime redistribution and exact included binary provenance require review",
            "Verify release module inclusion against inventory; missing installed optional-platform notices do not prove a shipped violation",
        ],
    }
    (output / "inventory.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    shutil.copy2(ROOT / "docs/architecture/dependencies.md", output / "REVIEW.md")
    return {
        "components": len(records),
        "unresolved": len(result["unresolved"]),
        "notice_files": sum(len(r["notices"]) for r in records),
        "output": str(output),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New output directory"
    )
    print(json.dumps(audit(parser.parse_args().output), indent=2))
