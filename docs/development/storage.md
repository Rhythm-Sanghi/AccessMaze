# Local storage and recovery

The desktop uses Tauri's per-user application data directory for
`org.accessmaze.desktop`. It contains `accessmaze.sqlite`, SQLite WAL/SHM files,
`worker.log`, and `artifacts/<run UUID>/`. No target website receives these paths.

The SQLite schema uses `PRAGMA user_version`, transactional incremental migrations,
foreign keys and WAL. A newer schema is refused. On worker startup, unfinished runs
become `interrupted`; they are never relabeled successful. Analysis observations
and findings are saved after each step. Previously started browser actions cannot
be resumed after a crash; create a new run.

Settings can export a ZIP containing a consistent SQLite online backup and synthetic
screenshots. Export requires acknowledgment because it includes plain-text journey
inputs. Workspaces above 25 MiB require closing AccessMaze and copying the whole
application data directory to private storage. Keep the application closed for that copy.
In-app backup/retention is refused while a run is active.

To restore, close AccessMaze, preserve the existing application data directory, and
place the database/artifacts from your own trusted backup into an empty application
data directory. Do not overwrite a live database, retain stale WAL/SHM files from a
different database, or extract untrusted ZIPs. Automated restore/import of arbitrary
backup archives is intentionally unsupported.

Settings can explicitly delete terminal runs older than a chosen number of days.
Projects remain. Deletion also removes run artifacts and dependent comparisons.
There is no background automatic pruning. Export evidence before pruning if needed.
Project deletion removes all of its runs regardless of age.

Corruption does not trigger automatic deletion or replacement. Preserve the data,
review worker diagnostics and restore a known-good backup. A guided corruption
recovery interface and secure erasure are not implemented. Logs are diagnostic data,
not instructions; do not publish them without checking for sensitive information.
