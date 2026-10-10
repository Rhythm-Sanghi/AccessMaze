import { useState } from "react";
import type { Journey, Run } from "../../../packages/contracts";
import { request } from "./api";
import RunInputs, { emptyInputs } from "./RunInputs";
import { activeRun } from "./RunWorkspace";

export default function FailureReplay({
  original,
  current,
  onStarted,
}: {
  original: Run;
  current: Run;
  onStarted: (run: Run) => void;
}) {
  const [findingId, setFindingId] = useState(original.findings[0]?.id ?? "");
  const [draft, setDraft] = useState<Journey | null>(null);
  const [inputs, setInputs] = useState(emptyInputs);
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const finding = original.findings.find((f) => f.id === findingId);
  const record = original.steps.find((s) => s.id === finding?.step_id);
  const action = original.journey.steps.find((s) => s.id === finding?.step_id);
  const node = original.nodes.find((n) => n.id === record?.state_id);
  async function prepare() {
    setError("");
    setAuthorized(false);
    setInputs(emptyInputs());
    setDraft(null);
    try {
      setDraft(
        (
          await request<{ journey: Journey }>("run.replay.prepare", {
            id: original.id,
            finding_id: findingId,
          })
        ).journey,
      );
    } catch (e) {
      setError(String(e));
    }
  }
  async function start() {
    setBusy(true);
    setError("");
    try {
      const started = await request<{ id: string }>("run.start", {
        project_id: original.project_id,
        replay_source_id: original.id,
        replay_finding_id: findingId,
        authorized,
        allow_effects: authorized,
        inputs,
      });
      setInputs(emptyInputs());
      setAuthorized(false);
      setDraft(null);
      onStarted(await request<Run>("run.get", { id: started.id }));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  if (!finding) return null;
  return (
    <section aria-labelledby="replay-heading">
      <div className="section-heading">
        <h2 id="replay-heading">Failure reproduction</h2>
        <span className="mono">HISTORICAL / LIVE</span>
      </div>
      <label>
        Recorded finding
        <select
          value={findingId}
          onChange={(e) => {
            setFindingId(e.target.value);
            setDraft(null);
            setInputs(emptyInputs());
            setAuthorized(false);
          }}
        >
          {original.findings.map((f) => (
            <option key={f.id} value={f.id}>
              {f.step_id}: {f.rule}
            </option>
          ))}
        </select>
      </label>
      <p>
        Historical run {original.id.slice(0, 8)} · {original.started_at}.
        Reading this evidence does not execute a browser.
      </p>
      <p>
        <strong>Failed action:</strong> {action?.action ?? "discovery action"}{" "}
        {action?.target?.name}. <strong>Expected:</strong> {finding.expected}
      </p>
      <p>
        <strong>Observed:</strong>{" "}
        {typeof finding.actual === "string"
          ? finding.actual
          : JSON.stringify(finding.actual)}
      </p>
      <details>
        <summary>Original trace and focus evidence</summary>
        <ol>
          {original.steps.map((s) => (
            <li key={s.id}>
              {s.id} / {s.action} / {s.status} / {s.state_id ?? "no state"}
            </li>
          ))}
        </ol>
        <pre>
          {JSON.stringify(
            {
              state: node?.observation ?? "Unavailable",
              interaction: record?.interaction ?? "Unavailable",
            },
            null,
            2,
          )}
        </pre>
      </details>
      {current.replay?.source_id === original.id &&
        current.replay.finding_id === findingId && (
          <p role="status">
            Live re-execution: {current.status} ·{" "}
            {current.replay.verdict ?? "pending"}. Compare the current graph and
            outcomes with the historical trace above. A missing finding is not
            proof of repair or unchanged conditions.
          </p>
        )}
      {current.replay?.source_id === original.id &&
        current.replay.finding_id === findingId && (
          <details>
            <summary>Compare historical and live step evidence</summary>
            <table>
              <thead>
                <tr>
                  <th>Step</th>
                  <th>Historical</th>
                  <th>Live</th>
                </tr>
              </thead>
              <tbody>
                {original.steps.map((s) => (
                  <tr key={s.id}>
                    <td>{s.id}</td>
                    <td>{s.status}</td>
                    <td>
                      {current.steps.find((c) => c.id === s.id)?.status ??
                        "not reached"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <pre>
              {JSON.stringify(
                {
                  historicalFocus: record?.interaction ?? "Unavailable",
                  liveFocus:
                    current.steps.find((s) => s.id === finding.step_id)
                      ?.interaction ?? "Unavailable",
                },
                null,
                2,
              )}
            </pre>
          </details>
        )}
      <button
        disabled={activeRun(current) || busy}
        onClick={() => void prepare()}
      >
        Review browser re-execution
      </button>
      {draft && (
        <div className="run-gate">
          <p>Target: {draft.target}</p>
          <details>
            <summary>Replay conditions and origin permissions</summary>
            <pre>
              {JSON.stringify(
                {
                  profile: draft.profile,
                  network: draft.network,
                  allow_local: draft.allow_local,
                },
                null,
                2,
              )}
            </pre>
          </details>
          <p>
            Re-execute the original authored journey in a fresh isolated
            browser. Discovery is disabled. Sites may have changed; effects are
            not undone. Supply new inputs; historical values are never
            recovered.
          </p>
          <ol>
            {draft.steps.map((s) => (
              <li key={s.id}>
                {s.id} / {s.action} / {s.target?.name ?? ""}
                {s.effect ? " / potentially state-changing" : ""}
              </li>
            ))}
          </ol>
          <RunInputs
            journey={draft}
            inputs={inputs}
            onChange={setInputs}
            onError={setError}
          />
          <label className="check">
            <input
              type="checkbox"
              checked={authorized}
              onChange={(e) => setAuthorized(e.target.checked)}
            />
            I authorize this target and every listed action, including possible
            submissions.
          </label>
          <button
            disabled={!authorized || busy || activeRun(current)}
            onClick={() => void start()}
          >
            Run approved replay
          </button>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
