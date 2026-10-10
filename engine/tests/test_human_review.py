import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from accessmaze.models import HumanReview, ProjectInput, Request
from accessmaze.runner import RunControl, execute
from accessmaze.storage import Store
from accessmaze.templates import template
from accessmaze.worker import Worker


@pytest.mark.browser
def test_human_review_persists_separately_and_exports_as_manual_evidence(tmp_path):
    worker = Worker(tmp_path, Path.cwd())

    def call(method, **params):
        return worker.dispatch(Request(version=1, id="manual-test", method=method, params=params))

    try:
        journey = template()
        project = worker.store.save_project(
            ProjectInput(name="Manual review boundary", journey=journey)
        )
        original = asyncio.run(
            execute(worker.store, project["id"], journey, RunControl(), worker.fixtures, worker.axe)
        )
        assert not original["findings"]
        review = HumanReview(
            run_id=original["id"], step_id="open", notes="<script>synthetic</script>"
        )
        saved = call("review.save", review=review.model_dump())
        assert saved["status"] == "planned" and not saved["performed_by_human"]
        assert worker.store.run(original["id"]) == original
        assert len(call("review.list", run_id=original["id"])) == 1
        reopened = Store(tmp_path)
        assert reopened.reviews(original["id"])[0]["id"] == saved["id"]
        html = call("report.export", id=original["id"], format="html")["content"]
        assert "Human observations" in html and "&lt;script&gt;synthetic&lt;/script&gt;" in html
        assert "<script>synthetic</script>" not in html
        assert (
            '"human_reviews"' in call("report.export", id=original["id"], format="json")["content"]
        )
        with pytest.raises(ValueError, match="step"):
            call("review.save", review={**review.model_dump(), "step_id": "missing"})
        with pytest.raises(ValueError, match="finding"):
            call("review.save", review={**review.model_dump(), "finding_id": "missing"})
        with pytest.raises(ValidationError, match="attestation"):
            call("review.save", review={**review.model_dump(), "status": "verified-human"})
        with pytest.raises(ValueError, match="belong"):
            call("review.save", id=str(uuid4()), review=review.model_dump())
        assert len(call("review.list", run_id=original["id"])) == 1
        call("review.delete", run_id=str(uuid4()), id=saved["id"])
        assert len(call("review.list", run_id=original["id"])) == 1
        call("review.delete", run_id=original["id"], id=saved["id"])
        assert call("review.list", run_id=original["id"]) == []
        assert worker.store.run(original["id"]) == original
    finally:
        worker.close()


def test_version_three_migration_preserves_history(store, project):
    p = project()
    run_id = str(uuid4())
    result = {
        "id": run_id,
        "project_id": p["id"],
        "status": "completed_with_limitations",
        "started_at": "2026-10-10",
        "journey": p["journey"],
        "steps": [],
        "findings": [],
    }
    store.save_run(result)
    with store.connect() as db:
        db.execute("DROP TABLE human_reviews")
        db.execute("PRAGMA user_version=3")
    migrated = Store(store.root)
    assert migrated.run(run_id) == result
    assert migrated.project(p["id"]) == p
    assert migrated.reviews(run_id) == []
    migrated.save_review(HumanReview(run_id=run_id, step_id="open"))
    migrated.delete_project(p["id"])
    with migrated.connect() as db:
        assert db.execute("SELECT count(*) FROM human_reviews").fetchone()[0] == 0
        assert db.execute("PRAGMA user_version").fetchone()[0] == 4
