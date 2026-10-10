import base64
import io
import json
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from accessmaze.permissions import private_directory
from accessmaze.storage import now


def backup(store):
    files = [path for path in (store.root / "artifacts").rglob("*.png") if not path.is_symlink()]
    limit = 25 * 1024**2
    error = "Workspace exceeds the 25 MiB in-app backup limit; use an offline directory copy"
    artifact_bytes = sum(path.stat().st_size for path in files)
    with store.connect() as source:
        # Logical pages include committed WAL data that the main file omits.
        database_bytes = (
            source.execute("PRAGMA page_count").fetchone()[0]
            * source.execute("PRAGMA page_size").fetchone()[0]
        )
    if database_bytes + artifact_bytes > limit:
        raise ValueError(error)
    output = io.BytesIO()
    with tempfile.TemporaryDirectory(prefix="AccessMaze backup ") as directory:
        private_directory(Path(directory))
        target = Path(directory) / "accessmaze.sqlite"
        with store.connect() as source:
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
                database_schema = destination.execute("PRAGMA user_version").fetchone()[0]
            finally:
                destination.close()
        # Recheck the consistent snapshot in case a writer grew it after preflight.
        if target.stat().st_size + sum(path.stat().st_size for path in files) > limit:
            raise ValueError(error)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(target, "accessmaze.sqlite")
            archive.writestr(
                "manifest.json",
                json.dumps(
                    {
                        "schema_version": 3,
                        "database_schema_version": database_schema,
                        "contains_plaintext_human_notes": True,
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
