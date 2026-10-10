import base64
import io
import sqlite3
import zipfile
from uuid import uuid4

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
    with sqlite3.connect(target) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
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
