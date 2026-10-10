import asyncio
import hashlib
import importlib.util
import io
import json
import os
import tarfile
import zipfile
from pathlib import Path

import pytest


def script(name):
    path = Path(__file__).resolve().parents[2] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_notice_collection_preserves_nested_attribution(tmp_path):
    (tmp_path / "licenses").mkdir()
    for path in [
        "LICENSE-MIT",
        "mit.LICENSE",
        "NOTICE",
        "ThirdPartyNotices.txt",
        "licenses/third-party.txt",
        "not-a-notice.js",
    ]:
        (tmp_path / path).write_text("test")
    found = {p.relative_to(tmp_path).as_posix() for p in script("license_audit").notices(tmp_path)}
    assert found == {
        "LICENSE-MIT",
        "mit.LICENSE",
        "NOTICE",
        "ThirdPartyNotices.txt",
        "licenses/third-party.txt",
    }


def test_archive_preserves_epoch_dated_notices_and_refuses_overwrite(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "package-manifest.json").write_text(
        json.dumps({"source_commit": "test", "source_dirty": False})
    )
    notice = package / "LICENSE"
    notice.write_text("Retain this original notice")
    os.utime(notice, (1, 1))
    archive = tmp_path / "preview.zip"
    helper = script("archive_preview")
    result = helper.archive_preview(package, archive)
    assert result["zip_crc"] == "passed" and result["files"] == 2
    with zipfile.ZipFile(archive) as packed:
        assert packed.read("package/LICENSE") == notice.read_bytes()
    with pytest.raises(FileExistsError):
        helper.archive_preview(package, archive)


def test_packaging_removes_only_unused_standalone_video_encoder(tmp_path):
    browsers = tmp_path / "resources with spaces"
    browsers.mkdir()
    for name in ["ffmpeg-1011", "chromium-1243", "chromium_headless_shell-1243"]:
        child = browsers / name
        child.mkdir()
        (child / "binary").write_bytes(b"test")
    script("package_windows").remove_unused_video_encoder(browsers)
    assert not (browsers / "ffmpeg-1011").exists()
    assert (browsers / "chromium-1243/binary").read_bytes() == b"test"
    assert (browsers / "chromium_headless_shell-1243/binary").read_bytes() == b"test"


def test_covered_source_delivery_refuses_lock_or_compiled_source_mismatch(tmp_path):
    source = tmp_path / "registry/src/index/example-1.0"
    source.mkdir(parents=True)
    (source / "lib.rs").write_bytes(b"// original covered source")
    archive = tmp_path / "registry/cache/index/example-1.0.crate"
    archive.parent.mkdir(parents=True)
    with tarfile.open(archive, "w:gz") as packed:
        info = tarfile.TarInfo("example-1.0/lib.rs")
        info.size = len((source / "lib.rs").read_bytes())
        packed.addfile(info, io.BytesIO((source / "lib.rs").read_bytes()))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    helper = script("license_audit")
    output = tmp_path / "output"
    result = helper.preserve_covered_source(source, checksum, output)
    assert result["verified_source_files"] == 1
    assert (output / result["path"]).read_bytes() == archive.read_bytes()
    with pytest.raises(ValueError, match="Cargo.lock"):
        helper.preserve_covered_source(source, "0" * 64, output)
    (source / "lib.rs").write_bytes(b"// local modification")
    with pytest.raises(ValueError, match="Compiled covered source differs"):
        helper.preserve_covered_source(source, checksum, output)


@pytest.mark.browser
@pytest.mark.skipif(os.name != "nt", reason="Windows packaging credits")
def test_exact_chromium_credits_include_collapsed_licenses(tmp_path):
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parents[2]
    browsers = root / ".accessmaze/browsers"
    if not browsers.is_dir():
        with sync_playwright() as pw:
            browsers = Path(pw.chromium.executable_path).parents[2]
    result = asyncio.run(script("browser_credits").capture(browsers, tmp_path / "credits"))
    assert result["license_sections"] > 100
    text = (tmp_path / "credits/chromium-credits.txt").read_text(encoding="utf-8")
    assert "Apache License" in text
    assert len(text) > 1000000
    html = (tmp_path / "credits/chromium-credits.html").read_text(encoding="utf-8")
    assert "<script" not in html and "chrome://resources" not in html
