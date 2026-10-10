import base64
import io
import json
import sqlite3
import zipfile
from uuid import uuid4

import pytest

from accessmaze.maintenance import backup, prune


def test_backup_is_a_consistent_database_with_artifacts(store, project, tmp_path):
    p = project()
    run_id = str(uuid4())
    store.save_run(
        {
            "id": run_id,
            "project_id": p["id"],
            "status": "failed",
            "started_at": "2020-01-01T00:00:00+00:00",
        }
    )
    (store.artifact_dir(run_id) / "evidence.png").write_bytes(b"synthetic")
    data = backup(store)
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(data["base64"]))) as archive:
        assert f"artifacts/{run_id}/evidence.png" in archive.namelist()
        target = tmp_path / "restored.sqlite"
        target.write_bytes(archive.read("accessmaze.sqlite"))
        manifest = json.loads(archive.read("manifest.json"))
    with sqlite3.connect(target) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert (
            manifest["database_schema_version"] == db.execute("PRAGMA user_version").fetchone()[0]
        )
        assert manifest["contains_plaintext_human_notes"] is True
        assert db.execute("SELECT name FROM projects").fetchone()[0] == p["name"]


def test_retention_preserves_projects_and_active_runs(store, project):
    p = project()
    old = str(uuid4())
    active = str(uuid4())
    for run_id, status in [(old, "completed_with_limitations"), (active, "running")]:
        store.save_run(
            {
                "id": run_id,
                "project_id": p["id"],
                "status": status,
                "started_at": "2020-01-01T00:00:00+00:00",
            }
        )
        store.artifact_dir(run_id)
    assert prune(store, 1) == {"deleted_runs": 1}
    assert store.project(p["id"])
    assert store.run(active)["status"] == "running"
    assert not (store.root / "artifacts" / old).exists()


def test_backup_limit_includes_committed_wal_pages(store):
    # Keep a reader open so closing the writer cannot checkpoint its large WAL.
    with store.connect() as reader:
        reader.execute("BEGIN")
        reader.execute("SELECT count(*) FROM projects").fetchone()
        with store.connect() as writer:
            writer.execute("CREATE TABLE backup_load (payload BLOB)")
            writer.execute("INSERT INTO backup_load VALUES (zeroblob(?))", (26 * 1024**2,))
        assert (store.root / "accessmaze.sqlite").stat().st_size < 25 * 1024**2
        assert (store.root / "accessmaze.sqlite-wal").stat().st_size > 25 * 1024**2
        with pytest.raises(ValueError, match="25 MiB"):
            backup(store)
