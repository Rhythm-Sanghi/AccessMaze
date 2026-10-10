import os
import subprocess

import pytest

from accessmaze.storage import Store


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL regression")
def test_storage_does_not_inherit_other_local_readers(tmp_path):
    root = tmp_path / "private evidence"
    root.mkdir()
    # Seed an explicit broad grant, which must also be replaced (not merely inheritance).
    subprocess.run(
        ["icacls", str(root), "/grant", "*S-1-1-0:(OI)(CI)(RX)"], capture_output=True, check=True
    )
    Store(root)
    result = subprocess.check_output(["icacls", str(root)], text=True)
    assert "Everyone" not in result
    assert "CodexSandboxUsers" not in result
    assert "(I)" not in result
    database = subprocess.check_output(["icacls", str(root / "accessmaze.sqlite")], text=True)
    assert "Everyone" not in database
    assert "CodexSandboxUsers" not in database
    assert "(I)" in database


@pytest.mark.skipif(os.name != "nt", reason="Windows DACL regression")
def test_existing_evidence_explicit_reader_grants_are_removed(tmp_path):
    root = tmp_path / "existing evidence"
    store = Store(root)
    evidence = root / "artifacts" / "prior.png"
    evidence.write_bytes(b"private evidence")
    for path in [root / "accessmaze.sqlite", evidence]:
        subprocess.run(
            ["icacls", str(path), "/grant", "*S-1-1-0:(RX)"],
            capture_output=True,
            check=True,
        )
    Store(root)
    for path in [root / "accessmaze.sqlite", evidence]:
        result = subprocess.check_output(["icacls", str(path)], text=True)
        assert "Everyone" not in result
    assert store.projects() == []
    assert evidence.read_bytes() == b"private evidence"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_storage_refuses_junction_without_changing_external_acl(tmp_path):
    root = tmp_path / "private workspace"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    before = subprocess.check_output(["icacls", str(outside)], text=True)
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(root / "linked"), str(outside)],
        check=True,
        capture_output=True,
    )
    with pytest.raises(OSError, match="reparse point"):
        Store(root)
    assert subprocess.check_output(["icacls", str(outside)], text=True) == before
