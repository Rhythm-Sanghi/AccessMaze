import json

import pytest

from accessmaze.evidence import fingerprint, public_journey, redact, safe_url
from accessmaze.reports import export_report
from accessmaze.storage import Store, now
from accessmaze.templates import template


def test_restart_and_foreign_keys(store, project):
    p = project()
    run = {
        "id": "7b7cb030-b49a-4b2b-a85f-353648cb9d51",
        "project_id": p["id"],
        "status": "running",
        "started_at": now(),
    }
    store.save_run(run)
    restarted = Store(store.root)
    restarted.recover()
    assert restarted.project(p["id"])["journey"] == p["journey"]
    assert restarted.run(run["id"])["status"] == "interrupted"
    restarted.delete_project(p["id"])
    assert restarted.runs(p["id"]) == []
    assert not (store.root / "artifacts" / run["id"]).exists()


def test_newer_database_is_rejected(store):
    with store.connect() as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError, match="newer"):
        Store(store.root)


def test_artifact_paths_cannot_escape_storage(store):
    with pytest.raises(ValueError):
        store.artifact_dir("../../secret")


def test_redaction_and_fingerprints():
    assert redact({"a": ["Applicant Test"]}, ["Test"]) == {"a": ["Applicant [redacted]"]}
    assert "Test Applicant" not in json.dumps(public_journey(template()))
    assert (
        safe_url("https://user:secret@example.com/form?token=x#private")
        == "https://example.com/form"
    )
    assert fingerprint({"x": 1, "timestamp": "a"}) == fingerprint({"timestamp": "b", "x": 1})
    assert fingerprint({"x": 1}) != fingerprint({"x": 2})


def test_reports_escape_untrusted_text_and_preserve_data():
    run = {
        "id": "id",
        "status": "failed",
        "started_at": "now",
        "environment": {},
        "journey": {"name": "<script>evil</script>", "target": "fixture://broken"},
        "steps": [{"id": "date", "action": "activate", "status": "failed"}],
        "limitations": ["bounded"],
        "findings": [
            {
                "title": "<script>evil</script>",
                "step_id": "date",
                "rule": "keyboard-unreachable",
                "severity": "serious",
                "verification": "confirmed-automated",
                "actual": "=CMD()",
                "expected": "reachable",
                "reproduction": ["open", "date"],
            }
        ],
    }
    assert json.loads(export_report(run, "json")[0]) == run
    html = export_report(run, "html")[0]
    assert "<script>evil</script>" not in html
    assert "&lt;script&gt;evil&lt;/script&gt;" in html
    assert "'=CMD()" in export_report(run, "csv")[0]
