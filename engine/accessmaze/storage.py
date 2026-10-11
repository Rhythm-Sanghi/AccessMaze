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
            if version > 4:
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

            if version < 3:
                db.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE profiles (
                        id TEXT PRIMARY KEY, name TEXT NOT NULL,
                        profile TEXT NOT NULL, updated_at TEXT NOT NULL
                    );
                    PRAGMA user_version=3;
                    COMMIT;
                """)

            if version < 4:
                db.executescript("""
                    BEGIN IMMEDIATE;
                    CREATE TABLE human_reviews (
                        id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id)
                        ON DELETE CASCADE, result TEXT NOT NULL, updated_at TEXT NOT NULL
                    );
                    CREATE INDEX reviews_by_run ON human_reviews(run_id, updated_at);
                    PRAGMA user_version=4;
                    COMMIT;
                """)

    def reviews(self, run_id):
        self.run(run_id)
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM human_reviews WHERE run_id=? ORDER BY updated_at,id", (run_id,)
            ).fetchall()
        return [
            {"id": row["id"], "updated_at": row["updated_at"], **json.loads(row["result"])}
            for row in rows
        ]

    def save_review(self, review, review_id=None):
        run = self.run(review.run_id)
        valid_steps = {s["id"] for s in run["journey"]["steps"]} | {
            a["step_id"] for a in run.get("exploration", {}).get("actions", [])
        }
        if review.step_id not in valid_steps:
            raise ValueError("Human review must reference a step in this run")
        if review.finding_id and review.finding_id not in {f["id"] for f in run["findings"]}:
            raise ValueError("Linked automated finding does not belong to this run")
        with self.connect() as db:
            if review_id:
                existing = db.execute(
                    "SELECT run_id FROM human_reviews WHERE id=?", (review_id,)
                ).fetchone()
                if not existing or existing["run_id"] != review.run_id:
                    raise ValueError("Human review does not belong to this run")
            elif (
                db.execute(
                    "SELECT count(*) FROM human_reviews WHERE run_id=?", (review.run_id,)
                ).fetchone()[0]
                >= 100
            ):
                raise ValueError("A run can retain at most 100 human observations")
            review_id = review_id or str(uuid4())
            db.execute(
                "INSERT INTO human_reviews VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "result=excluded.result,updated_at=excluded.updated_at",
                (review_id, review.run_id, review.model_dump_json(), now()),
            )
        return next(r for r in self.reviews(review.run_id) if r["id"] == review_id)

    def delete_review(self, run_id, review_id):
        with self.connect() as db:
            db.execute("DELETE FROM human_reviews WHERE id=? AND run_id=?", (review_id, run_id))

    def profiles(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM profiles ORDER BY name COLLATE NOCASE, id").fetchall()
        return [{**dict(row), "profile": json.loads(row["profile"])} for row in rows]

    def save_profile(self, data, profile_id=None):
        profile_id = profile_id or str(uuid4())
        with self.connect() as db:
            db.execute(
                "INSERT INTO profiles VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "name=excluded.name,profile=excluded.profile,updated_at=excluded.updated_at",
                (profile_id, data.name, data.profile.model_dump_json(), now()),
            )
        return next(p for p in self.profiles() if p["id"] == profile_id)

    def delete_profile(self, profile_id):
        with self.connect() as db:
            db.execute("DELETE FROM profiles WHERE id=?", (profile_id,))

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
                result["revision"] = result.get("revision", 0) + 1
                result["finished_at"] = now()
                for step in result.get("steps", []):
                    if step["status"] == "running":
                        step["status"] = "interrupted"
                result.pop("approval", None)
                exploration = result.get("exploration")
                if exploration:
                    exploration["stop_reason"] = "interrupted"
                    for action in exploration.get("actions", []):
                        if action["status"] == "running":
                            action["status"] = "interrupted"
                from accessmaze.outcomes import task_outcome

                if result.get("journey"):
                    result["outcome"] = task_outcome(result)
                db.execute(
                    "UPDATE runs SET status=?, result=? WHERE id=?",
                    ("interrupted", json.dumps(result), row["id"]),
                )

    def projects(self):
        with self.connect() as db:
            rows = db.execute("""
                WITH totals AS (
                    SELECT project_id, MAX(started_at) AS last_analysis,
                        SUM(status IN ('preparing','running','paused','awaiting_approval',
                            'cancelled','interrupted')) AS incomplete_runs,
                        SUM((SELECT COUNT(*) FROM json_each(runs.result,'$.findings')
                            WHERE json_extract(value,'$.verification')='confirmed-automated'))
                            AS confirmed_findings
                    FROM runs GROUP BY project_id
                )
                SELECT projects.*, totals.last_analysis,
                    COALESCE(totals.incomplete_runs,0) AS incomplete_runs,
                    COALESCE(totals.confirmed_findings,0) AS confirmed_findings
                FROM projects LEFT JOIN totals ON projects.id=totals.project_id
                ORDER BY projects.updated_at DESC
            """).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["summary"] = {
                key: item.pop(key)
                for key in ("last_analysis", "incomplete_runs", "confirmed_findings")
            }
            item["journey"] = json.loads(item["journey"])
            result.append(item)
        return result

    def history(self, project_id, limit=50, offset=0):
        if (
            type(limit) is not int
            or type(offset) is not int
            or not 1 <= limit <= 100
            or not 0 <= offset <= 1000000
        ):
            raise ValueError("History requires a 1–100 page size and a bounded nonnegative offset")
        self.project(project_id)
        with self.connect() as db:
            total = db.execute(
                "SELECT count(*) FROM runs WHERE project_id=?", (project_id,)
            ).fetchone()[0]
            rows = db.execute(
                """
                SELECT id,project_id,status,started_at,
                    json_array_length(result,'$.findings') AS finding_count,
                    json_extract(result,'$.duration_seconds') AS duration_seconds,
                    json_extract(result,'$.journey.profile') AS profile
                FROM runs WHERE project_id=? ORDER BY started_at DESC,id DESC LIMIT ? OFFSET ?
            """,
                (project_id, limit, offset),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["journey"] = {"profile": json.loads(item.pop("profile") or "{}")}
            item["finding_count"] = item["finding_count"] or 0
            items.append(item)
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "next_offset": offset + len(items) if offset + len(items) < total else None,
        }

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

    def run_revision(self, run_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT json_extract(result,'$.revision') FROM runs WHERE id=?", (run_id,)
            ).fetchone()
        if row is None:
            raise ValueError("Run not found")
        return row[0]

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
