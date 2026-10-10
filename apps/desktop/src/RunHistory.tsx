import { useState } from "react";
import type { Run, RunComparison } from "../../../packages/contracts";
import { request } from "./api";
import { activeRun } from "./RunWorkspace";

export default function RunHistory({
  history,
  run,
  onSelect,
}: {
  history: Run[];
  run: Run | null;
  onSelect: (run: Run) => void;
}) {
  const [previous, setPrevious] = useState("");
  const [comparison, setComparison] = useState<RunComparison | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function compare() {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      setComparison(
        await request<RunComparison>("run.compare", {
          previous_id: previous,
          current_id: run.id,
        }),
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="section-heading">
        <h2>Run history</h2>
        <span className="mono">{history.length} SAVED RUNS</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Started</th>
              <th>Status</th>
              <th>Findings</th>
              <th>Duration</th>
              <th>Open</th>
            </tr>
          </thead>
          <tbody>
            {history.map((r) => (
              <tr key={r.id}>
                <td>{new Date(r.started_at).toLocaleString()}</td>
                <td>{r.status.replaceAll("_", " ")}</td>
                <td>{r.findings.length}</td>
                <td>{r.duration_seconds ?? "—"} s</td>
                <td>
                  <button
                    disabled={activeRun(run)}
                    onClick={() => {
                      onSelect(r);
                      setComparison(null);
                    }}
                  >
                    Inspect run
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!history.length && (
        <p className="muted">Open a project to load its run history.</p>
      )}
      {run && history.length > 1 && (
        <section className="retest">
          <div className="section-heading">
            <h2>Journey comparison</h2>
          </div>
          <p className="muted">
            Compare the selected run with earlier evidence. Only identical
            journey configurations can verify a repair.
          </p>
          <div className="fields">
            <label>
              Previous run
              <select
                value={previous}
                onChange={(e) => {
                  setPrevious(e.target.value);
                  setComparison(null);
                }}
              >
                <option value="">Select earlier evidence</option>
                {history
                  .filter((r) => r.id !== run.id)
                  .map((r) => (
                    <option key={r.id} value={r.id}>
                      {new Date(r.started_at).toLocaleString()} /{" "}
                      {r.id.slice(0, 8)} / {r.status}
                    </option>
                  ))}
              </select>
            </label>
          </div>
          <button
            disabled={!previous || busy || activeRun(run)}
            onClick={() => void compare()}
          >
            {busy ? "Comparing…" : "Compare findings"}
          </button>
          {comparison &&
            comparison.current_id === run.id &&
            comparison.previous_id === previous && (
              <>
                <h3>Task outcome</h3>
                <p>
                  Baseline: {comparison.previous_outcome.status} · Candidate:{" "}
                  {comparison.current_outcome.status}
                </p>
                <p>{comparison.current_outcome.reason}</p>
                <p>
                  First divergent execution step:{" "}
                  {comparison.first_divergent_step?.step_id ??
                    "No recorded status divergence"}
                </p>
                <p>
                  Changed journey conditions:{" "}
                  {comparison.changed_conditions.join(", ") || "None"}
                </p>
                <p>
                  Changed environment fields:{" "}
                  {comparison.environment_changes.join(", ") || "None"}
                </p>
                <ul>
                  {comparison.warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
                <p role="status">
                  {comparison.comparable
                    ? "Configurations match"
                    : "Configurations differ; repair verification is inconclusive"}
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Step</th>
                      <th>Rule</th>
                      <th>Retest result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.findings.map((f) => (
                      <tr key={f.finding_id}>
                        <td>{f.step_id}</td>
                        <td>{f.rule}</td>
                        <td>{f.verdict}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!comparison.findings.length && (
                  <p>No baseline findings to verify.</p>
                )}
                <h3>Added candidate findings</h3>
                {comparison.added_findings.length ? (
                  <ul>
                    {comparison.added_findings.map((f) => (
                      <li key={f.finding_id}>
                        {f.step_id} / {f.rule}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No new matchable finding identities.</p>
                )}
                <details>
                  <summary>Compare concrete profile conditions</summary>
                  <pre>
                    {JSON.stringify(
                      {
                        baseline: history.find(
                          (r) => r.id === comparison.previous_id,
                        )?.journey.profile,
                        candidate: run.journey.profile,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
                <h3>Step evidence and observed transitions</h3>
                <div className="toolbar">
                  <button
                    onClick={() => {
                      const baseline = history.find(
                        (r) => r.id === comparison.previous_id,
                      );
                      if (baseline) onSelect(baseline);
                    }}
                  >
                    Inspect baseline run
                  </button>
                  <button onClick={() => onSelect(run)}>
                    Inspect candidate run
                  </button>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Step</th>
                        <th>Baseline</th>
                        <th>Candidate</th>
                        <th>Observed states</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.steps.map((s) => (
                        <tr key={s.step_id}>
                          <td>{s.step_id}</td>
                          <td>{s.previous_status}</td>
                          <td>{s.current_status}</td>
                          <td className="mono">
                            {s.previous_state_id?.slice(0, 8) ?? "—"} /{" "}
                            {s.current_state_id?.slice(0, 8) ?? "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="muted">
                  State IDs are local observations, not cross-run equivalence.
                  Inspect each run for its graph, focus and artifacts.
                </p>
                <p className="muted">{comparison.matching_rule}</p>
                <p className="muted">{comparison.limitation}</p>
              </>
            )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </section>
      )}
    </>
  );
}
