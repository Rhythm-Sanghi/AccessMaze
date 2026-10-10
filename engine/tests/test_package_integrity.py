"""Exercise the actual systems-only PowerShell package checker on Windows."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows portable harness")
def test_package_integrity_detects_tampering_and_path_escape(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/Test-AccessMazePortable.ps1"
    payload = tmp_path / "PREVIEW.txt"
    payload.write_bytes(b"preview")
    manifest = {
        "files": [
            {"path": "PREVIEW.txt", "bytes": 7, "sha256": hashlib.sha256(b"preview").hexdigest()}
        ]
    }
    source = tmp_path / "package-manifest.json"
    source.write_text(json.dumps(manifest))

    def check():
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-File",
                str(script),
                "-Package",
                str(tmp_path),
                "-IntegrityOnly",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

    assert check().returncode == 0
    payload.write_bytes(b"altered")
    failed = check()
    assert failed.returncode != 0 and "integrity failed" in failed.stderr
    manifest["files"][0]["path"] = "../outside.txt"
    source.write_text(json.dumps(manifest))
    failed = check()
    assert failed.returncode != 0 and "escapes package" in failed.stderr
