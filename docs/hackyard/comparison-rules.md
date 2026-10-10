# Outcome and comparison semantics

Task outcome is derived from the saved journey and actual step results:

- Cancelled execution: cancelled, with partial evidence retained.
- Compromised origin coverage: inconclusive.
- Failed mandatory step with a confirmed automated finding: blocked in this bounded attempt.
- Failed mandatory step without confirmed barrier evidence: inconclusive.
- Completed execution with all mandatory assertions recorded passed: completed.
- Otherwise: incomplete, including interrupted execution and assertions not reached.

Optional assertions do not define completion. Completed is not a conformance verdict;
audit findings can coexist with task completion. A timeout without confirmed barrier
evidence remains incomplete. Legacy runs derive outcomes during comparison/export;
new runs persist outcomes with every progress save. No database migration is needed.

Finding identity is stable step ID, rule and canonical sorted axe target set. Non-axe
findings use step ID/rule within the exact journey. Private target tokens are deliberately
not stable across runs; where a rule remains observed, affected-target matching is
inconclusive. Changed target sets are reported as added identities, but absence of an
old target is not verified repair while its rule still fails elsewhere. This is conservative.

Repair verification requires exact journey/project/runtime-input-signature/environment,
a different run, uncompromised candidate coverage, completed execution and a passed
relevant step. Axe findings additionally require an actual audit without that violation
or an incomplete result. Matching positions are never used. Reordered/edited journeys
retain descriptive ID-aligned steps and changed-condition warnings, without repair claims.
The first divergent step is the first baseline-ordered recorded status difference, then
candidate-only steps; it is not a claim about the first DOM difference. State hashes are
local observations, especially when private HMAC tokens change; never equate them across runs.
