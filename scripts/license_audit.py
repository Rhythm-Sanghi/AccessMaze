"""Inventory locked dependencies and preserve installed notices; not legal qualification."""

import argparse
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve_covered_source(folder, checksum, output):
    """Preserve the published crate only after checking lock bytes and compiled sources."""
    archive = folder.parents[2] / "cache" / folder.parent.name / f"{folder.name}.crate"
    if digest(archive) != checksum:
        raise ValueError("Covered source archive does not match Cargo.lock")
    count = 0
    with tarfile.open(archive, "r:gz") as packed:
        for member in packed.getmembers():
            relative = PurePosixPath(member.name).relative_to(folder.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe covered source archive path")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(
                    "Covered source archive contains a link or special file"
                )
            if (folder / Path(relative)).read_bytes() != packed.extractfile(
                member
            ).read():
                raise ValueError(
                    "Compiled covered source differs from published archive"
                )
            count += 1
    target = output / "covered-source" / archive.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(archive, target)
    return {
        "path": target.relative_to(output).as_posix(),
        "sha256": checksum,
        "verified_source_files": count,
        "license": "MPL-2.0",
        "scope": "Unmodified published source archive; compiled registry files matched byte for byte",
    }


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
                or p.name.upper().endswith((".LICENSE", ".LICENCE"))
                or p.name.upper().startswith(
                    (
                        "LICENSE",
                        "LICENCE",
                        "COPYING",
                        "NOTICE",
                        "COPYRIGHT",
                        "THIRDPARTY",
                        "THIRD_PARTY",
                        "THIRD-PARTY",
                    )
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
            if not license:
                # Preserve the publisher's classifier verbatim; do not infer an SPDX expression.
                license = (
                    "; ".join(
                        c
                        for c in dist.metadata.get_all("Classifier", [])
                        if c.startswith("License ::")
                    )
                    or None
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
    cargo_lock = tomllib.loads((ROOT / "apps/desktop/src-tauri/Cargo.lock").read_text())
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
        if "MPL-2.0" in (package["license"] or ""):
            locked = next(
                p
                for p in cargo_lock["package"]
                if p["name"] == package["name"]
                and p["version"] == package["version"]
                and p.get("source") == package["source"]
            )
            records[-1]["covered_source"] = preserve_covered_source(
                Path(package["manifest_path"]).parent, locked["checksum"], output
            )
        supplements = ROOT / "docs/legal/upstream/provenance.json"
        if supplements.is_file():
            for evidence in json.loads(supplements.read_text(encoding="utf-8")):
                if evidence["name"] != package["name"]:
                    continue
                vcs = Path(package["manifest_path"]).parent / ".cargo_vcs_info.json"
                revision = (
                    json.loads(vcs.read_text())["git"]["sha1"]
                    if vcs.is_file()
                    else None
                )
                if evidence.get("declaration_path"):
                    declaration = (
                        Path(package["manifest_path"]).parent
                        / evidence["declaration_path"]
                    )
                    if digest(declaration) != evidence["declaration_sha256"]:
                        raise ValueError("License declaration hash mismatch")
                    matching_revision = revision == evidence["crate_revision"]
                else:
                    matching_revision = revision and f"/{revision}/" in evidence["url"]
                if not matching_revision:
                    raise ValueError(
                        "Supplement does not match the locked crate revision"
                    )
                source = ROOT / evidence["path"]
                if digest(source) != evidence["sha256"]:
                    raise ValueError("Supplement hash mismatch")
                target = output / "notices" / f"{len(records) - 1:04d}" / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                records[-1]["notices"].append(
                    {
                        "path": target.relative_to(output).as_posix(),
                        "sha256": digest(target),
                        "upstream_url": evidence["url"],
                    }
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
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
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
            "If standalone FFmpeg is distributed, static LGPL source/relink obligations require a corresponding-source plan; current package recipe omits this unused encoder",
            "Microsoft graphics runtime redistribution and exact included binary provenance require review",
            "Verify release module inclusion against inventory; missing installed optional-platform notices do not prove a shipped violation",
            "MPL native crate sources are included and byte-verified; independent legal review of all covered-source and browser delivery obligations remains required",
        ],
    }
    (output / "inventory.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Third-party component notices",
        "",
        "Engineering inventory, including build dependencies; inclusion here does not establish binary linkage or redistribution clearance.",
        "Original license and copyright texts are preserved in the linked files. Do not replace them with this index.",
        "",
    ]
    for component in records:
        lines.extend(
            [
                f"## {component['ecosystem']}: {component['name']} {component['version']}",
                "",
                f"Publisher declaration: {component['declared_license'] or 'UNKNOWN; review required'}",
                "",
            ]
        )
        for notice in component["notices"]:
            lines.append(
                f"- [{notice['path']}]({notice['path']}) — SHA-256 `{notice['sha256']}`"
            )
        if source := component.get("covered_source"):
            lines.append(
                f"- Covered source, made available under MPL-2.0: [{source['path']}]({source['path']}) — SHA-256 `{source['sha256']}`. Original .crate is a gzip tar archive; extract with tar to read/modify it offline."
            )
        if not component["notices"]:
            lines.append(
                "No collected notice; see inventory unresolved entries and distribution review."
            )
        lines.append("")
    (output / "THIRD-PARTY-NOTICES.md").write_text("\n".join(lines), encoding="utf-8")
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
