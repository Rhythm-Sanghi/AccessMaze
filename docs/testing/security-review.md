# Local security review, 2026-10-10

Scope: source inspection, existing and new actual Chromium/protocol regressions,
Windows ACL inspection, package integrity checks and dependency advisory tools. This
is an engineering review on one developer laptop, not an independent penetration test.

| Area | Evidence / disposition |
| --- | --- |
| Credentials/uploads | `RunInputs` validates exact binding keys, bounded values and combined 4 MiB path-free buffers. Passwords require bindings and secure/authorized private origins. Worker-scoped HMAC input signature guards retest comparability. No personal profile import or persistent cookie jar. |
| Evidence | External text uses per-run HMAC tokens by default; screenshots restricted to fixtures. Known runtime values/names redacted before storage. Authored labels/URLs and literal journey input remain persistent; opt-in text can retain unrelated personal data. |
| Retention | SQLite/WAL and backup ZIPs are plaintext. Pruning removes completed historical runs/artifacts; SQLite backup API captures a consistent database. No secure SSD/WAL/backups erasure guarantee. Exported files inherit the chosen destination's permissions. |
| Filesystem | Actual `icacls` showed inherited RX for `CodexSandboxUsers` on this laptop's development and AppData directories. Storage now applies a protected inheritable DACL granting only current user, SYSTEM and Administrators; startup fails if it cannot apply it. A Windows test seeds broad Everyone access and verifies it is removed and the new database inherits private access. Existing child explicit ACL exceptions still require review; administrators and same-user processes remain trusted. |
| Browser isolation | Fresh context/browser per run; browser is separate from desktop WebView. Service workers, downloads, popups, embedded frames and WebSockets denied; DNS snapshot and redirect response interception tested. Exact read-only resources vs navigation/API scope preserved. No OS firewall/hostile-browser isolation claim. |
| Effects | Declared steps plus run authorization; each exploratory action separately approved and stale state refused. Recorder manual-session authorization permits background writes to authorized API origins. GET and page-loading scripts can still have effects; use dedicated authorized accounts. |
| Errors | Invalid schema now reports safe field locations and repair guidance, without Pydantic input/context. A private-stdio test verifies a supplied synthetic password is absent from stdout/stderr. Unexpected internal exceptions still reach private stderr and need diagnostic-log privacy review before release. |
| Integrity | Existing integrity test detects tampering/path traversal; package manifest hashes protect against accidental corruption only. Preview is unsigned; authenticated distribution/code signing and browser binary provenance remain gates. |

No external credentials were entered during this review. Python strings and browser
memory are not guaranteed zeroized; OS crash dumps, page files, malware, same-user
processes and administrators can expose memory. Full disk encryption/account hygiene
belong to deployment policy, not an application encryption claim. Inherited directory
hardening does not remediate previously copied/exported evidence.

Advisory commands: `npm audit --json` reported zero known advisories;
`uv run --project engine pip-audit --progress-spinner off --format json` reported zero
known dependency vulnerabilities, with the editable local project skipped. `cargo audit
--json` (0.22.2, advisory database commit
`7eebec69c352c7191b1f13eb95dd510eeca5d1de`) reported zero vulnerability entries but
two informational warnings: unmaintained proc-macro-error 1.0.4 and unsound glib 0.18.5.
`cargo tree --target x86_64-pc-windows-msvc -i` for each printed no dependency path;
both are outside the resolved Windows graph. Do not characterize that as a clean
all-platform audit. Re-run audits at release; advisory tools do not audit bundled browser
binaries or prove absence of vulnerabilities.

Open gates: independent threat-model/network containment review, hostile-target boundary,
diagnostic privacy, explicit child ACL review, authenticated/signable packaging,
complete third-party binary/source obligations and clean-machine/manual testing.
