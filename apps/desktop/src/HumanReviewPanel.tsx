import { useEffect, useState } from "react";
import type { HumanReview, Run } from "../../../packages/contracts";
import { request } from "./api";

function plannedReview(run: Run): HumanReview {
  return {
    schema_version: 1,
    run_id: run.id,
    step_id: run.journey.steps[0].id,
    finding_id: null,
    status: "planned",
    performed_by_human: false,
    assistive_technology: "",
    browser: "",
    os: "",
    settings: "",
    action: "",
    expected: "",
    actual: "",
    notes: "",
  };
}

export default function HumanReviewPanel({ run }: { run: Run }) {
  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [draft, setDraft] = useState(() => plannedReview(run));
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    let disposed = false;
    request<HumanReview[]>("review.list", { run_id: run.id })
      .then((value) => {
        if (!disposed) setReviews(value);
      })
      .catch((e) => {
        if (!disposed) setError(String(e));
      });
    return () => {
      disposed = true;
    };
  }, [run.id]);
  const steps = [
    ...new Set([
      ...run.journey.steps.map((s) => s.id),
      ...(run.exploration?.actions.map((a) => a.step_id) ?? []),
    ]),
  ];
  const fields = [
    [
      "assistive_technology",
      "Assistive technology and exact version (or None)",
    ],
    ["browser", "Browser and exact version used manually"],
    ["os", "Operating system and version"],
    ["settings", "Relevant settings"],
    ["action", "Tested action"],
    ["expected", "Expected behavior"],
    ["actual", "Actual behavior and exact speech or focus"],
    ["notes", "Evidence references and notes"],
  ] as const;
  async function save() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const review = { ...draft };
      delete review.id;
      delete review.updated_at;
      await request("review.save", { id: draft.id, review });
      setReviews(
        await request<HumanReview[]>("review.list", { run_id: run.id }),
      );
      setDraft(plannedReview(run));
      setMessage("Human observation saved separately from automated findings.");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section aria-labelledby="human-review-heading" className="retest">
      <div className="section-heading">
        <h2 id="human-review-heading">Human investigation</h2>
        <span className="mono">MANUAL / SEPARATE EVIDENCE</span>
      </div>
      <p>
        Automated semantics cannot verify announcements, reading order or
        cognitive usability. Record what a human actually tested. This does not
        establish WCAG certification.
      </p>
      <p className="muted">
        Notes are stored locally as plain text and included in JSON/HTML exports
        and backups. Use synthetic data and omit credentials. An automated run
        does not perform NVDA testing.
      </p>
      <details
        open={expanded}
        onToggle={(e) => setExpanded(e.currentTarget.open)}
      >
        <summary>Prepare or record a manual check</summary>
        <button
          disabled={busy}
          onClick={() =>
            setDraft({
              ...plannedReview(run),
              action:
                "Start NVDA and record its version. Navigate headings, controls, validation and dialogs using browse and focus modes. Repeat the task after a correction.",
              expected:
                "Write the expected speech and focus destination for each action before testing.",
              notes:
                "Preparation only; NVDA evaluation has not been performed. Record NVDA/browser/OS versions, settings, exact speech, focus, outcome and evidence references.",
            })
          }
        >
          Prepare NVDA checklist
        </button>
        <a
          href="https://github.com/Rhythm-Sanghi/AccessMaze/blob/main/docs/testing/nvda.md"
          target="_blank"
          rel="noreferrer"
        >
          Manual NVDA procedure
        </a>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <fieldset className="plain-fieldset" disabled={busy}>
            <div className="fields">
              <label>
                Reviewed step
                <select
                  value={draft.step_id}
                  onChange={(e) =>
                    setDraft({ ...draft, step_id: e.target.value })
                  }
                >
                  {steps.map((id) => (
                    <option key={id}>{id}</option>
                  ))}
                </select>
              </label>
              <label>
                Linked automated finding (optional)
                <select
                  value={draft.finding_id ?? ""}
                  onChange={(e) =>
                    setDraft({ ...draft, finding_id: e.target.value || null })
                  }
                >
                  <option value="">Separate manual observation</option>
                  {run.findings.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.step_id} / {f.rule}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Human verification status
                <select
                  value={draft.status}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      status: e.target.value as HumanReview["status"],
                    })
                  }
                >
                  <option value="planned">Planned — not performed</option>
                  <option value="observed">Observed by human</option>
                  <option value="inconclusive">Inconclusive</option>
                  <option value="verified-human">
                    Verified by human for this task
                  </option>
                </select>
              </label>
              {fields.map(([field, label]) => (
                <label key={field}>
                  {label}
                  <textarea
                    rows={field === "actual" || field === "notes" ? 3 : 2}
                    value={draft[field]}
                    maxLength={
                      field === "actual" || field === "notes"
                        ? 4000
                        : ["browser", "os", "assistive_technology"].includes(
                              field,
                            )
                          ? 200
                          : 2000
                    }
                    onChange={(e) =>
                      setDraft({ ...draft, [field]: e.target.value })
                    }
                  />
                </label>
              ))}
            </div>
            <label className="check">
              <input
                type="checkbox"
                checked={draft.performed_by_human}
                onChange={(e) =>
                  setDraft({ ...draft, performed_by_human: e.target.checked })
                }
              />
              I performed the recorded manual actions in the stated environment.
            </label>
            <div className="toolbar">
              <button type="submit">Save human observation</button>
              <button
                type="button"
                onClick={() => setDraft(plannedReview(run))}
              >
                New observation
              </button>
            </div>
          </fieldset>
        </form>
        <div role="status">{busy ? "Saving human observation…" : message}</div>
        {error && <p role="alert">{error}</p>}
      </details>
      {!reviews.length && (
        <p className="empty-inline">
          No manual observations recorded for this run.
        </p>
      )}
      {reviews.map((review) => (
        <article className="finding" key={review.id}>
          <h3>
            {review.step_id} / {review.status}
          </h3>
          <p>{review.actual || "Planned check; no actual result recorded."}</p>
          <p className="muted">
            {review.assistive_technology || "Technology not recorded"} ·{" "}
            {review.browser || "Browser not recorded"} ·{" "}
            {review.os || "OS not recorded"}
          </p>
          <button
            disabled={busy}
            onClick={() => {
              setDraft(review);
              setExpanded(true);
            }}
          >
            Edit human observation
          </button>
          <button
            disabled={busy}
            onClick={() => {
              setBusy(true);
              setError("");
              request("review.delete", { run_id: run.id, id: review.id })
                .then(() =>
                  request<HumanReview[]>("review.list", { run_id: run.id }),
                )
                .then(setReviews)
                .catch((e) => setError(String(e)))
                .finally(() => setBusy(false));
            }}
          >
            Remove human observation
          </button>
        </article>
      ))}
    </section>
  );
}
