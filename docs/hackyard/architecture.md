# Local execution architecture

```mermaid
flowchart LR
  Person[Reviewed journey / concrete profile / approval] --> UI[React / Tauri desktop]
  UI <-->|Validated private stdio| Worker[Python worker]
  Worker --> Policy[Exact origins / ephemeral inputs]
  Policy --> Browser[Fresh Chromium context / Playwright]
  Browser --> Site[Authorized target / controlled fixture]
  Browser --> Observations[Focus / computed AX / axe / assertions]
  Observations --> SQLite[Private SQLite / masked fixture artifacts]
  SQLite --> Investigation[Observed graph / task paths / reports / comparison]
  UI --> Human[Separate planned or attested human records]
  Human --> SQLite
  UI --> Profiles[Versioned profiles / bounded serial batches / run snapshots]
  Profiles --> Worker
  Investigation --> Replay[Versioned recipe / editable draft / fresh approved replay]
  Replay --> Worker
  Worker --> Proposal[One bounded proposed external action]
  Proposal --> Person
```

Rust owns worker and Chromium descendants through a Windows Job object. Each worker
permits one active run. Fresh browser contexts do not import personal cookies. Target
pages never receive desktop IPC. Origin policy is not an OS firewall or a hostile-target sandbox.

State identity normalizes bounded browser observations, omitting input values and URL
queries. Focus and dynamic labels can split equivalent states; absent application internals
can merge different states. Graphs describe observations, never exhaustive application models.
External discovery never automatically replays effects. Optional root navigation requires
fresh approval and cannot undo server state or restore forms. Only bundled resettable
fixtures permit automatic branch replay. Discovery coverage ignores focus-only changes
but retains checked/expanded/selected/pressed states and original focus evidence. See ../architecture/001-local-worker.md and 002-authorized-websites.md.
