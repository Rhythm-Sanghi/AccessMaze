# Browser investigation milestones

Baseline: clean `main` at `c634573`, inspected on 2026-10-10. Work continues on
`engineering/browser-investigation`; existing architecture and design tokens stay
in place. Local baseline: 112 Python tests (140.921 s), 9 React tests (3.99 s),
1 Rust test. GitHub run 38071630094 failed: 23 Linux browser-dependent tests
failed after the demo selected an unpopulated repository cache. Windows was
cancelled and packaging skipped. This is a delivery defect, not a website defect.

| Area | Baseline | Implementation and acceptance |
| --- | --- | --- |
| Browser permissions | Exact origins, DNS snapshot, redirects and effect windows work; frames/popups/sockets/service workers blocked | Explicit authorized-application frame permission; named-frame targeting; real two-origin frame containment tests. Keep unsupported capabilities restricted. |
| Failure meaning | Rule and verification exist; missing explicit categories | Central classification with policy precedence; execution failures separate from accessibility findings; browser regressions. |
| Discovery | Approved buttons/links/checkboxes/radios; deterministic walk and approved root recovery | Scoped targets, ARIA widget support, distinct navigation/interaction identity, state budget and explicit frontier reasons. No automatic repetition of external writes. |
| Replay | Authored path replay works; discovered paths unavailable | Versioned recipes with prerequisites, fresh bindings and explicit withheld-target limitations; editable draft; actual Chromium replay. |
| Reachability | Assertion-based outcome exists | Actual graph paths, blocking attempts, bounded alternatives and unknown frontier; never infer global unreachability. |
| Comparisons | Stable rule/step/target identities and conservative repair verification | Focus/control differences and overall verdict under comparable conditions; changed environments remain inconclusive. |
| Profiles | Saved snapshots and real conditions work | Versioned snapshots and bounded sequential batch runner. Preserve accurate layout-emulation terminology. |
| Human review | Manual NVDA procedure only | Structured local human observations, separate from automation, exact versions/settings and verification status; no fabricated NVDA execution. |
| Benchmarks | Controlled demo and timing tools | Paired broken/working corpus, same-page axe baseline, machine-readable configuration/results and honest detection limits. Other tools only when actually executed. |
| Performance/UI | Full-history payloads; project summary N+1 queries; polling | Measure and reduce query/payload costs; targeted components and accessible compact result views. Retain polling unless a measured alternative is justified. |
| Security/delivery | Internal regressions, manifests/notices, unsigned package | Regression tests for verified defects, immutable CI actions, completed remote checks, rebuilt portable/native verification and updated procedures. |
| Hackyard | Reproducible failure/fix/retest; existing explanation and transparency ledger | Branching/recovery demos, timed scripts, final submission copy and explicit pre-event boundary. No event eligibility or submission claims. |

Each milestone records commands, actual results and unresolved limits in status.
External gates remain independent Windows/fresh-user qualification, real human NVDA
evaluation, independent security and redistribution review, signing credentials,
release-owner performance budgets and event eligibility/build-window evidence.
An overnight run requires an actual reserved, awake host and elapsed run; short
stability runs cannot satisfy it. Retained WebView2 children remain an unresolved
risk until reproduced and explained.
