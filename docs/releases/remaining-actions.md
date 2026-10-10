# Remaining qualification actions

AccessMaze remains an unsigned readiness preview. Local evidence is in engineering
status; none of the following is implicitly passed by the browser regression suite.

| Gate | Exact required action |
| --- | --- |
| Independent Windows / fresh user | Give the recorded ZIP/hash to a separate Windows 11 machine or fresh VM with a standard user, no developer tools/caches/history. Follow clean-machine.md including WebView2 prerequisite, fresh-user startup, real network disconnection, upgrade/restore and removal. Save tester/image identity, package hash and each result. Development-laptop extraction/PATH checks are separate evidence. |
| Actual NVDA / manual accessibility | A human tester follows ../testing/nvda.md with real NVDA, speech/focus observations, keyboard/high-contrast/zoom tasks and exact versions. Record failures/inconclusive checks; no automated browser AX substitute. |
| Remote CI | A maintainer with write access pushes the reviewed commits and triggers verify. Follow ../testing/ci-verification.md; retain completed job/run URLs and exact SHA/artifact, fix failures. No remote success is recorded here. |
| Distribution rights / source | Review the exact shipped Chrome for Testing/headless-shell and incorporated codec/library obligations; Microsoft graphics and WebView2 loader redistribution permissions; Playwright Node incorporated notices; axe preferred-source delivery; all binary provenance against the inventory. Native MPL crate sources are now included and byte-verified. Standalone FFmpeg is absent from the new ZIP; older previews retain their LGPL source/relink gate. Obtain independent redistribution review and a verified binary SBOM; package labels alone cannot clear embedded libraries. |
| Security review | Independent reviewer evaluates the documented threat model, browser/network limits, imported/protocol inputs, bootstrap diagnostics/crash dumps, plaintext retention/export and same-user/admin trust. Reproduce the internal regression evidence; record findings and fixes without calling the internal review independent. |
| Signing / authenticity | An authorized release owner obtains signing credentials/certificates, signs the exact deliverable and verifies provenance/SmartScreen policy. Publish its hash through an authenticated channel. Local hashes/CRC do not authenticate an unsigned archive. |
| Overnight / native UI stability | On a host reserved for the run, use `uv run --project engine python scripts/extended_stability.py --seconds 43200 --output dist/stability-overnight-new`. Keep engine/tests unchanged and host awake; save raw measurements/logs. Add a separately measured long-lived native UI/Job-crash run. The completed 607-second worker run is not overnight or native UI soak qualification. |
| Performance acceptance | Release owner sets representative-hardware budgets, verifies native large-graph/history rendering and sustained workload variance. Backend synthetic graph and local startup/RSS measurements do not establish these budgets. Existing-child ACL traversal measured 2.043–3.053 seconds with 5,000 synthetic files; repeat on representative retained histories. |
| Master acceptance | Reconcile the remaining master-spec acceptance/feature limits in status with the proposed release scope. Human finding lifecycle, broader profiles/recording, corruption-recovery UI and other documented roadmap items are not silently completed by these validation milestones. Approve scope or implement/test required blockers before qualification. |

Useful procedures: [clean Windows](clean-machine.md), [package/build](packaging.md),
[internal security](../testing/security-review.md),
[license evidence](../legal/license-gap-review.md),
[stability measurements](../testing/readiness-benchmark.md),
[Hackyard transparency](../testing/hackyard-presentation.md).

Competition start date/eligibility, entrant/team contribution history and required
AI-assistance disclosures must be supplied by the entrant. The Git boundary ledger
documents pre-existing work; it does not certify competition eligibility.
