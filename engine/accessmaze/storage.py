import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from accessmaze.permissions import private_directory


def now():
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        private_directory(self.root)
        (self.root / "artifacts").mkdir(exist_ok=True)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 2:
                raise RuntimeError("Database was created by a newer AccessMaze version")
            if version == 0:
                db.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE projects (
                        id TEXT PRIMARY KEY, name TEXT NOT NULL, journey TEXT NOT NULL,
                        archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)),
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE runs (
                        id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id)
                        ON DELETE CASCADE, status TEXT NOT NULL, started_at TEXT NOT NULL,
                        result TEXT NOT NULL
                    );
                    CREATE INDEX runs_by_project ON runs(project_id, started_at DESC);
                    PRAGMA user_version=1;
                    COMMIT;
                """)
            if version < 2:
                db.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE retests (
                        previous_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                        current_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                        compared_at TEXT NOT NULL, result TEXT NOT NULL,
                        PRIMARY KEY(previous_id,current_id)
                    );
                    PRAGMA user_version=2;
                    COMMIT;
                """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root / "accessmaze.sqlite", timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        try:
            with db:
                yield db
        finally:
            db.close()

    def recover(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id, result FROM runs WHERE status IN "
                "('preparing','running','paused','awaiting_approval')"
            ).fetchall()
            for row in rows:
                result = json.loads(row["result"])
                result.update(status="interrupted", error="Worker stopped before run completion")
                result["finished_at"] = now()
                for step in result.get("steps", []):
                    if step["status"] == "running":
                        step["status"] = "interrupted"
                db.execute(
                    "UPDATE runs SET status=?, result=? WHERE id=?",
                    ("interrupted", json.dumps(result), row["id"]),
                )

    def projects(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        projects = []
        for row in rows:
            with self.connect() as db:
                summaries = db.execute(
                    "SELECT started_at,status,json_extract(result,'$.findings') "
                    "AS findings FROM runs WHERE project_id=? ORDER BY started_at DESC",
                    (row["id"],),
                ).fetchall()
            runs = [
                {**dict(item), "findings": json.loads(item["findings"] or "[]")}
                for item in summaries
            ]
            projects.append(
                {
                    **dict(row),
                    "journey": json.loads(row["journey"]),
                    "summary": {
                        "last_analysis": runs[0]["started_at"] if runs else None,
                        "confirmed_findings": sum(
                            f.get("verification") == "confirmed-automated"
                            for run in runs
                            for f in run.get("findings", [])
                        ),
                        "incomplete_runs": sum(
                            run["status"]
                            in {
                                "preparing",
                                "running",
                                "paused",
                                "awaiting_approval",
                                "cancelled",
                                "interrupted",
                            }
                            for run in runs
                        ),
                    },
                }
            )
        return projects

    def project(self, project_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise ValueError("Project not found")
        return {**dict(row), "journey": json.loads(row["journey"])}

    def save_project(self, data, project_id=None):
        project_id = project_id or str(uuid4())
        with self.connect() as db:
            db.execute(
                """INSERT INTO projects(id,name,journey,updated_at) VALUES(?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,journey=excluded.journey,
                updated_at=excluded.updated_at""",
                (project_id, data.name, data.journey.model_dump_json(), now()),
            )
        return self.project(project_id)

    def archive(self, project_id, archived):
        with self.connect() as db:
            db.execute("UPDATE projects SET archived=? WHERE id=?", (int(archived), project_id))

    def delete_project(self, project_id):
        import shutil

        runs = self.runs(project_id)
        with self.connect() as db:
            db.execute("DELETE FROM projects WHERE id=?", (project_id,))
        for run in runs:
            shutil.rmtree(self.artifact_dir(run["id"]), ignore_errors=False)

    def save_run(self, result):
        with self.connect() as db:
            db.execute(
                """INSERT INTO runs VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,result=excluded.result""",
                (
                    result["id"],
                    result["project_id"],
                    result["status"],
                    result["started_at"],
                    json.dumps(result, ensure_ascii=False),
                ),
            )

    def run(self, run_id):
        with self.connect() as db:
            row = db.execute("SELECT result FROM runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("Run not found")
        return json.loads(row["result"])

    def runs(self, project_id):
        with self.connect() as db:
            rows = db.execute(
                "SELECT result FROM runs WHERE project_id=? ORDER BY started_at DESC", (project_id,)
            ).fetchall()
        return [json.loads(row["result"]) for row in rows]

    def save_retest(self, comparison):
        with self.connect() as db:
            db.execute(
                "INSERT INTO retests VALUES(?,?,?,?) ON CONFLICT(previous_id,current_id) "
                "DO UPDATE SET compared_at=excluded.compared_at,result=excluded.result",
                (
                    comparison["previous_id"],
                    comparison["current_id"],
                    now(),
                    json.dumps(comparison),
                ),
            )

    def artifact_dir(self, run_id):
        # IDs originate in the worker, but all caller-controlled lookups are validated too.
        from uuid import UUID

        UUID(run_id)
        path = self.root / "artifacts" / run_id
        path.mkdir(exist_ok=True)
        return path
