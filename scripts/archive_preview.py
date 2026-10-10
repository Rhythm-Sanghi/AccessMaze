"""Archive a complete preview without overwriting evidence; verify CRC and hash."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def archive_preview(package, archive):
    manifest = json.loads(
        (package / "package-manifest.json").read_text(encoding="utf-8")
    )
    # Some upstream notice files have Unix-epoch timestamps; ZIP's range starts in 1980.
    with zipfile.ZipFile(
        archive, "x", zipfile.ZIP_DEFLATED, compresslevel=6, strict_timestamps=False
    ) as output:
        for path in sorted(package.rglob("*")):
            if path.is_symlink():
                raise ValueError("Refusing package symlinks")
            if path.is_file():
                output.write(path, path.relative_to(package.parent))
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None:
            raise RuntimeError("Archive CRC verification failed")
        count = len(check.infolist())
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "artifact": archive.name,
        "bytes": archive.stat().st_size,
        "sha256": digest,
        "zip_crc": "passed",
        "files": count,
        "source_commit": manifest["source_commit"],
        "source_dirty": manifest["source_dirty"],
        "scope": "Unsigned local preview. ZIP timestamps clamp to supported range; file hashes remain authoritative. No bit-for-bit build or independent qualification claim.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = archive_preview(args.package.resolve(), args.archive.resolve())
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
