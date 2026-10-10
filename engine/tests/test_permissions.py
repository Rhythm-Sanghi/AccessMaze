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
