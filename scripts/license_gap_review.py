"""Classify the original 87 gaps using actual UI and frozen-worker inclusion evidence."""

import argparse
import ast
import hashlib
import importlib.metadata as metadata
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(baseline, inventory, modules, toc):
    old = json.loads(baseline.read_text(encoding="utf-8"))
    new = json.loads(inventory.read_text(encoding="utf-8"))
    module_ids = json.loads(modules.read_text(encoding="utf-8"))
    normal_graph = ""
    if any(g["ecosystem"] == "cargo" for g in old["unresolved"]):
        normal_graph = subprocess.check_output(
            [
                "cargo",
                "tree",
                "--locked",
                "--target",
                "x86_64-pc-windows-msvc",
                "--edges",
                "normal",
                "--prefix",
                "none",
                "--format",
                "{p}",
            ],
            cwd=ROOT / "apps/desktop/src-tauri",
            text=True,
            encoding="utf-8",
        )
    # Analysis-00.toc is a Python literal, never executable Python.
    analysis = ast.literal_eval(toc.read_text(encoding="utf-8"))
    sources = {
        str(x[1]).replace("\\", "/").casefold()
        for field in analysis
        if isinstance(field, list)
        for x in field
        if isinstance(x, tuple) and len(x) == 3 and isinstance(x[1], str)
    }
    rows = []
    for gap in old["unresolved"]:
        current = next(
            r
            for r in new["components"]
            if all(r[k] == gap[k] for k in ("ecosystem", "name", "version"))
        )
        row = {
            **gap,
            "declared_license": current["declared_license"],
            "notice_evidence": current["notices"],
        }
        if gap["ecosystem"] == "npm":
            included = any(
                m.startswith(f"node_modules/{gap['name']}/") for m in module_ids
            )
            if included:
                raise ValueError(
                    f"Unexpected previously missing npm package in production UI: {gap['name']}"
                )
            row.update(
                classification="false positive / non-distributed build or platform dependency",
                disposition="excluded from application redistribution gap count",
                basis="Absent from actual Vite production module graph; package recipe copies no node_modules and separately ships axe-core (not this component). Not a license grant or clearance for distributing development tools.",
            )
        elif gap["ecosystem"] == "python":
            try:
                dist = metadata.distribution(gap["name"])
                hits = [
                    str(f)
                    for f in dist.files or []
                    if str(dist.locate_file(f)).replace("\\", "/").casefold() in sources
                ]
            except metadata.PackageNotFoundError:
                hits = []
            row["frozen_source_matches"] = hits
            if hits:
                row.update(
                    classification="missing metadata / required attribution",
                    disposition="metadata recovered and original notices preserved"
                    if current["declared_license"] and current["notices"]
                    else "OPEN",
                    basis="Actual PyInstaller Analysis source matches; publisher license classifiers retained verbatim without SPDX inference. See hashed original notices.",
                )
            else:
                row.update(
                    classification="false positive / non-distributed development or platform dependency",
                    disposition="excluded from application redistribution gap count",
                    basis="No distribution RECORD file matched any source in actual frozen Analysis TOC. macholib is macOS-only and absent on this Windows environment. Build-hook generated code and PyInstaller bootloader obligations are reviewed separately; absence is not universal source-package clearance.",
                )
        else:
            ordinary_path = any(
                line.startswith(f"{gap['name']} v{gap['version']}")
                for line in normal_graph.splitlines()
            )
            row["ordinary_windows_dependency_path"] = ordinary_path
            row.update(
                classification=(
                    "required attribution / conservative Windows scope; linkage not proven"
                    if ordinary_path
                    else "build-graph-only dependency / conservatively retained notice"
                ),
                disposition="original upstream notice preserved"
                if current["notices"]
                else "OPEN: missing full upstream notice",
                basis="Actual cargo tree with normal edges records presence/absence of an ordinary dependency path; proc-macro and generated code still need separate interpretation. Retain original notice conservatively, without asserting executable linkage or inventing a redistribution obligation. Supplement matches exact crate revision/declaration and SHA-256. Covered native source archives are delivered separately.",
            )
        rows.append(row)
    return {
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            )
        ),
        "scope": "All original metadata/notice gaps classified. Not legal clearance, binary SBOM, independently verified linkage or third-party runtime clearance. Re-run for every changed build.",
        "inputs_sha256": {
            p.name: digest(p) for p in [baseline, inventory, modules, toc]
        },
        "components": len(new["components"]),
        "windows_normal_graph_sha256": hashlib.sha256(
            normal_graph.encode()
        ).hexdigest(),
        "original_gaps": len(rows),
        "resolutions": rows,
        "remaining_metadata_gaps": new["unresolved"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--modules", type=Path, required=True)
    parser.add_argument(
        "--toc",
        type=Path,
        default=ROOT / "engine/build/accessmaze-worker/Analysis-00.toc",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review(
        ROOT / "docs/testing/license-inventory.json",
        args.inventory,
        args.modules,
        args.toc,
    )
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "components": result["components"],
                "classified": result["original_gaps"],
                "open_rows": sum(
                    r["disposition"].startswith("OPEN") for r in result["resolutions"]
                ),
            }
        )
    )
