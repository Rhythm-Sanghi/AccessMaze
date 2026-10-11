# Independent Windows portable qualification

Status: **NOT RUN independently**. A stripped PATH on the development laptop checks
bundled resources but does not establish a clean-machine result.

Use a separate physical Windows 11 machine or a fresh VM image that has never hosted
the development tree. Record tester, date, machine/image identity, Windows build,
standard-user account type, RAM/CPU, WebView2 version and network state. Do not copy
Python, Node, Rust, uv, developer certificates, Playwright caches or application data.
Record any separately installed WebView2 prerequisite, its source and offline availability.

1. Obtain the portable archive and its SHA-256 through independently authenticated
   distribution. Calculate the archive hash with Windows tools before extraction.
   The embedded file manifest detects corruption; it cannot authenticate an unsigned
   package whose archive and manifest could both have been replaced. Record signature
   and SmartScreen behavior; the development preview is unsigned.
2. Extract all files into a user-writable directory containing spaces and non-ASCII characters. From ordinary
   PowerShell, run `powershell -NoProfile -File .\Test-AccessMazePortable.ps1 -Package .`
   and preserve its JSON result and temporary-storage path. All integrity checks,
   three browser fixture journeys, exports and EOF shutdown must pass.
3. Launch `AccessMaze.exe` as a standard user. Run accessible, broken, validation,
   modal, conditional and recovery journeys through the UI. Compare reported defects
   with known fixture behavior. Verify cancel, restart and retained history.
4. Test the controlled multi-step app hosted on a second explicitly authorized test
   computer: allow only its exact frontend/API origins. Verify actual uploaded synthetic
   bytes, conditional navigation, dialog return focus, offline draft retention and one
   explicitly approved submission. Verify denied API origins fail visibly.
5. Record a visible-browser journey. Stop and review/edit its draft, bind synthetic
   run-only input/upload, then replay it. Verify secrets and upload names/contents are
   absent from persisted reports. No personal browser profile may be imported.
6. Disconnect networking after prerequisites are installed. Repeat local fixtures and
   report exports; website failures must explain unavailable connectivity. Reconnect
   and verify recovery without automatically replaying external effects.
7. While a fixture is running, terminate only the test worker using Task Manager.
   Confirm Chromium descendants exit, run becomes interrupted, restart works and
   saved history survives. Repeat after an ordinary desktop restart.
8. Back up test history, replace the application directory with a newer package and
   verify history compatibility. Exercise unsupported future-schema refusal and restore
   a backup in isolated test storage; never alter the only copy of evidence.
9. Remove the extracted application directory. Confirm no process remains. Document
   retained AppData/history/backups and explicitly delete only disposable test data if
   desired. Deletion is not a secure erase claim. Repeat in an account without admin rights.

Record every step as PASS / FAIL / INCONCLUSIVE / NOT RUN, with package/source hashes,
commands, raw results and defects. Have the independent tester attest that no developer
runtime/cache was present. Re-run failed steps after correction; do not transfer local
passes into this record. Release qualification additionally requires the security,
license, manual accessibility, CI and acceptance gates in engineering status.

For the remaining-feature build, additionally save/apply/update a reusable profile across
two projects; verify keyboard/pointer outcomes and layout-zoom/motion/connectivity
observations. Approve separate branches and root recovery against owned targets; verify
no unapproved write. Reproduce a stored authored failure with fresh input, correct the
owned target and replay again; inspect both traces. Cancel during approval/replay and
crash the worker while a profile run is active. Record each result independently.

Current database schema is 4. Migration is forward-only. Before upgrading a real
store, retain a verified backup; older previews must refuse newer schemas rather than
modify them. A downgrade requires the matching older backup in isolated storage.
Verify separate human records survive upgrade/export without becoming automated
findings. Save an editable replay draft without executing it; check paged history,
named-frame permission/refusal, scoped controls and fresh profile-batch authorization.
Record planned NVDA checks as planned until a human actually performs them.
