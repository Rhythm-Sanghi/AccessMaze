# Local Windows performance baseline

Executed `uv run --project engine python scripts/readiness_benchmark.py` on
2026-10-10. Raw timings and 0.2-second summed RSS/handle samples are in
`dist/Readiness-before-engineering.json` (preserved before the October 11 rerun). Windows 11 build 26220, Python 3.13.9, 12 logical CPUs,
15.66 GiB RAM. Ordinary laptop background applications were present; short regression
tests also ran during the measurement. This is a baseline, not a controlled comparison.
Worker startup was measured before the subsequent permission-hardening change.

| Measurement | Observed |
| --- | --- |
| Development worker start, health response, EOF shutdown | 1.062–1.095 s, three fresh processes |
| Headless Chromium launch | 62.08–64.72 ms, three warm-cache samples |
| New context and local navigation | 109.20–112.49 ms |
| Sequential fixture journeys | 60, all expected statuses: 24 complete, 36 deliberately defective failures |
| Median journey by fixture | accessible 1.582 s; broken 1.767 s; errors 1.212 s; recovery 1.100 s; branch 2.396 s |
| Persistent browser soak | 181.04 s, 88 real page reloads and field edits |
| Summed RSS | peak 421.74 MiB; sample median 396.06 MiB |
| Median report generation | HTML 0.227 ms; JSON 0.166 ms; CSV 0.024 ms |
| History/project loading | maximum 182.125 ms across the growing test workspace |
| Synthetic directed graph build/path/serialization | 1k nodes 4.617 ms; 10k 34.651 ms; 50k 214.587 ms |

Graph loads are generated backend scaling probes, not observed browser states or UI
render measurements. RSS counts shared pages once per process and includes this Python
harness, driver and owned children. Short peaks do not prove a leak. The deliberately
broken/error/recovery fixtures are expected to fail their assertions; failures are not
silently converted to successful runs. Existing packaged/native startup measurements
remain recorded separately in engineering status.

Repeat the command on AC power with a documented power profile, after closing unrelated
applications, and preserve the original JSON before replacing it. `--runs 500
--soak-seconds 3600` extends the bounded probe. Before qualification, run an overnight
worker/UI soak, monitor post-run idle memory and handles, repeat cancellation/crashes,
measure native startup and large-history graph rendering, and set reviewed budgets on
representative hardware. No overnight stability, memory-leak clearance, or release
performance pass is claimed by this five-minute execution.

Packaged follow-up: `uv run --project engine python scripts/desktop_startup.py --package
AccessMaze-readiness-preview` measured three real WebView2/worker launches to connected
UI at 4.395 / 1.572 / 1.534 s, with 437.70–447.93 MiB ready summed RSS. Cache state is
uncontrolled and CDP polling overhead is included. Owned process trees exited after each
sample. Frozen worker health startup in separate system-PATH checks was 0.662 and 0.713 s.
See `desktop-startup.json` and `../releases/readiness-portable-*.json`. Large UI graphs,
overnight stability and independent hardware remain unverified.

The final 207a09a package also ran under concurrent integrity/worker/archive activity.
Its preserved results show startup 0.718 / 1.669 s, fixture execution 18.657–26.355 s
and the complex path 29.350 s (`../releases/readiness-final-*.json`). These conditions
are not comparable to the earlier sequential baseline. The spread demonstrates why
controlled repeat measurements and reviewed workload budgets remain release gates.

## Sustained regression procedure

Use `uv run --project engine python scripts/extended_stability.py --seconds 600 --output dist/stability-new` from a clean committed tree. The new output directory is exclusive. A persistent in-process Worker executes alternating real fixture journeys/cancellation, checks SQLite integrity, exports a report and deletes actual artifacts. Each cycle also runs a fresh pytest browser battery covering recording, socket interruption/recovery, persistence/backup and retention. Memory/handles include the entire harness and child test processes, not only the application. Idle samples measure the same persistent parent worker. Source fingerprints must remain unchanged. A failed cycle or surviving child fails the measurement.

The initial 60-second harness validation actually completed two cycles of 32 passing tests plus two persistent-worker journeys, SQLite checks and cleanup. The earlier exploratory 619.71-second / 18-cycle run is retained in `stability-exploratory.json`; code/tests changed near its end, so it is not fixed-source qualification. Final committed-source measurements are recorded separately in status. The duration parameter can request an actual overnight run (for example 43200 seconds); no such run is claimed here. Native host crash/Job recovery is separately verified.

Final sustained result: `stability-committed.json`, **607.26 s / 11 persistent-worker journeys / 11 cycles × 32 regression tests = 352 passing regression executions**. Engine hashes/selected tests remained unchanged; unrelated notice tooling/docs changed later. Peak summed harness/test-child RSS **704.16 MiB**, peak handles **4,050**; idle parent RSS **64.47 → 42.85 MiB**, handles **258 → 255**, zero surviving children at all cycle boundaries. This is bounded evidence, not a no-leak proof or overnight result. Three native crash/restart tests separately cleaned four Chromium children each.

Latest systems-only-PATH native startup: **1.337 / 1.297 / 1.262 s**, ready summed RSS **438.74–442.37 MiB**, with existing synthetic AppData/cache. Initial close-helper lookup failed when powershell was absent from PATH; its owned process/8 children were cleaned. The harness now uses the absolute Windows system PowerShell path with a termination fallback; rerun cleanup passed.

Actual private ACL/storage initialization with **5,000 synthetic existing files** took **3.0528 / 2.1570 / 2.0426 s**; 1,000 files **0.2658–0.3477 s**. These measure actual ACL traversal/SQLite initialization, not real screenshot capture or native UI history performance. Background builds/load were uncontrolled. Raw data: `permissions-scaling.json`.


## October 11 measured rerun

Clean `432dd5f` on the i7-1365U laptop (10 cores/12 threads, 15.66 GiB usable RAM,
Windows 11 build 26220), `python scripts/readiness_benchmark.py --runs 10 --soak-seconds 60`:
91.01 s overall, 61.55 s persistent browser interval, 30 reloads. Worker start/health/EOF
1.2937–1.5122 s; Chromium launch 85.41–90.21 ms; context/navigation 131.22–153.00 ms.
Ten actual fixture journeys took 1.382–3.954 s, with expected complete/defective outcomes.
Report generation measured 0.021–0.529 ms; peak summed harness/browser RSS 522.66 MiB.
The 50,000-node synthetic graph build/path/serialization took 160.092 ms. This is
backend graph processing, not native UI rendering or a controlled performance ranking.
Raw current output is copied to `dist/Readiness-432dd5f.json`; old raw data was preserved.

The clean `10a3fc6` worker run completed **1,223.77 s**, 24 persistent journeys and
**816 passing regression executions** (24 cycles × 34). Engine hashes stayed unchanged.
Peak summed harness/test-child RSS 740.88 MiB, handles 4,105; idle parent RSS
65.32 → 67.41 MiB (44.80–69.68 range), handles 256 → 251, zero surviving children
at all cycle boundaries. Raw `dist/Stability-10a3fc6/measurements.json` and cycle logs.
This includes headed recording, cancellation, actual socket interruption, SQLite
integrity/backup and artifact cleanup. It does not establish overnight stability.

`native_stability.py` accepts an explicit owned host PID, exact package executable,
endpoint, new output directory and 60..86400-second interval. It runs real fixtures
through packaged private IPC, inspects UI history/analysis, exports reports, samples
the native process tree and checks Chromium cleanup after every run. It deletes only
its own unique project and closes the selected host, then checks known descendants.
Launch a dedicated test preview first; never select a desktop with unrelated active work:

```powershell
uv run --project engine python scripts/launch_preview.py --package AccessMaze-investigation-preview
# Substitute the exact PID printed by the launcher.
uv run --project engine python scripts/native_stability.py --pid PID --exe dist/AccessMaze-investigation-preview/AccessMaze.exe --seconds 600 --output dist/native-soak-new
```

The first 600-second harness records `export_seconds` over export plus the 0.5-second
cleanup observation delay; those fields are not standalone report-generation timings.
Its exact script is preserved beside the raw results. The current harness separates
export timing from that delay and uses the absolute Windows close-helper path; a
separate actual validation is recorded in status. Native results and shutdown
disposition are recorded separately in engineering status.


Native probe caveats: the first interval failed a post-deletion harness query. The
second completed 170 cycles but its historical-PID wait reported replacements from
unrelated processes as survivors. Neither raw result is rewritten as passed. The
current harness uses creation-time-aware `Process.is_running()`, retains observed
identities and excludes reused PIDs without terminating them. The third interval's
actual result is recorded in status. Ordinary non-CDP extraction shutdown separately
closed all eight children. These corrections do not resolve the older application
retention report or qualify overnight stability.


Use one dedicated desktop during lifecycle measurements. Multiple native windows can
share WebView2 processes, so closing one is not a valid global-child-cleanup test while
another is alive. Worker run/batch concurrency limits apply per worker; concurrent
desktop-instance qualification is not established by these single-host measurements.


The final creation-time-aware native probe passed **157 cycles / 601.33 s**, including
owned history removal and zero survivors after close. It retained 781 child identities
and safely excluded six reused PIDs. Peak summed RSS 1,025.90 MiB, handles 5,565; idle
RSS 534.37 → 560.85 MiB (534.37–700.33 range), handles 3,655 → 3,664. Each cycle
reloads the UI before inspecting history/analysis. This measures a long-lived native
host/worker, not uninterrupted single-document retention, overnight stability or
proof of no leaks. Raw `dist/Native-sustained-identities-432dd5f/measurements.json`.
