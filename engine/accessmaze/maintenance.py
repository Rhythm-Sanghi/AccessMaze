import base64
import io
import json
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from accessmaze.storage import now


def backup(store):
    files = [path for path in (store.root / "artifacts").rglob("*.png") if not path.is_symlink()]
    database = store.root / "accessmaze.sqlite"
    if database.stat().st_size + sum(path.stat().st_size for path in files) > 25 * 1024**2:
        raise ValueError(
            "Workspace exceeds the 25 MiB in-app backup limit; use an offline directory copy"
        )
    output = io.BytesIO()
    with tempfile.TemporaryDirectory(prefix="AccessMaze backup ") as directory:
        target = Path(directory) / "accessmaze.sqlite"
        with store.connect() as source:
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
            finally:
                destination.close()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(target, "accessmaze.sqlite")
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "schema_version": 2,
                        "created_at": now(),
                        "contains_plaintext_journey_inputs": True,
                    }
                ),
            )
            for path in files:
                resolved = path.resolve()
                if not resolved.is_relative_to(store.root):
                    raise ValueError("Artifact points outside workspace; backup refused")
                archive.write(resolved, resolved.relative_to(store.root).as_posix())
    return {
        "base64": base64.b64encode(output.getvalue()).decode("ascii"),
        "mime": "application/zip",
    }


def prune(store, days):
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 3650:
        raise ValueError("Retention must be an integer between 1 and 3650 days")
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    with store.connect() as db:
        rows = db.execute(
            "SELECT id FROM runs WHERE started_at<? AND status NOT IN "
            "('preparing','running','paused','awaiting_approval')",
            (cutoff,),
        ).fetchall()
        for row in rows:
            db.execute("DELETE FROM runs WHERE id=?", (row["id"],))
    import shutil

    for row in rows:
        directory = store.artifact_dir(row["id"])
        if not directory.resolve().is_relative_to(store.root / "artifacts"):
            raise ValueError("Artifact directory escaped storage")
        shutil.rmtree(directory)
    return {"deleted_runs": len(rows)}
