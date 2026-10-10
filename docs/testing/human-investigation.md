# Guided human investigation

Open a completed run in Analysis, then expand **Prepare or record a manual check**.
The automated findings, graph and limitations remain historical evidence. Human
records are a separate SQLite collection; they never change automated finding counts,
task outcomes or retest verdicts.

1. Select the exact step, optionally link a specific automated finding, and write the
   expected behavior before testing. Use the [NVDA procedure](nvda.md) for actual
   screen-reader evaluation. **Prepare NVDA checklist** creates a planned checklist;
   it does not start NVDA or establish that any evaluation happened.
2. Use an authorized test account and synthetic data in a dedicated manual browser.
   Record the actual assistive technology/version (or None), browser/version, OS,
   settings, tested actions, exact speech/focus/reading-order observations and evidence
   references. Desktop-shell and website evaluations are separate observations.
3. Choose observed/inconclusive/verified-human as supported by the actual observation.
   Observed and verified-human require the tester's attestation and complete context,
   action, expected and actual fields. A saved status is a tester-entered statement,
   not independent validation or a compliance certificate.
4. Repeat the same task after correction. Preserve each relevant observation as a
   separate record, or explicitly edit the existing note. Automated replay is separate.

Records are private local plaintext, editable/removable and capped at 100 per run.
Do not include passwords, personal information or sensitive screenshots in notes.
JSON and HTML exports include human records with an explicit separate heading; CSV
remains an automated-finding export. Backups contain the SQLite records. Deleting a
run/project cascades its manual observations.

SQLite schema 4 adds this collection without rewriting historical run JSON. Back up
the workspace before upgrading; earlier schema-3 previews cannot open the upgraded
database. This workflow has automated persistence/UI tests, but actual NVDA testing
remains **NOT RUN** until a human completes and records the procedure.
