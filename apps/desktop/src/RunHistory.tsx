import { useState } from "react";
import type { Run } from "../../../packages/contracts";
import { request } from "./api";
import { activeRun } from "./RunWorkspace";

interface Comparison {
  comparable: boolean;
  findings: {
    finding_id: string;
    rule: string;
    step_id: string;
    verdict: string;
  }[];
  limitation: string;
}
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
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function compare() {
    if (!run) return;
    setBusy(true);
    setError("");
    try {
      setComparison(
        await request<Comparison>("run.compare", {
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
            <h2>Compare a retest</h2>
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
          {comparison && (
            <>
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
