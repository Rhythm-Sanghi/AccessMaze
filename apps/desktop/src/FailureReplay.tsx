import { useState } from "react";
import type { Journey, Project, Run } from "../../../packages/contracts";
import { request } from "./api";
import RunInputs, { emptyInputs } from "./RunInputs";
import { activeRun } from "./RunWorkspace";

function focusSummary(interaction?: Record<string, unknown>) {
  const history = interaction?.focus_history;
  if (!Array.isArray(history)) return "Unavailable";
  const visible = history
    .slice(0, 12)
    .map((f) => String(f.name || f.role || f.tag || "unnamed").slice(0, 80));
  return (
    visible.join(" → ") +
    (history.length > 12 ? " → … (more in recorded evidence)" : "")
  );
}

export default function FailureReplay({
  original,
  current,
  onStarted,
  onAuthored,
}: {
  original: Run;
  current: Run;
  onStarted: (run: Run) => void;
  onAuthored: (project: Project) => void;
}) {
  const [findingId, setFindingId] = useState(original.findings[0]?.id ?? "");
  const [draft, setDraft] = useState<Journey | null>(null);
  const [inputs, setInputs] = useState(emptyInputs);
  const [authorized, setAuthorized] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const finding = original.findings.find((f) => f.id === findingId);
  const record =
    original.steps.find((s) => s.id === finding?.step_id) ??
    original.exploration?.actions.find((s) => s.step_id === finding?.step_id);
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
            <table aria-label="Historical and live focus comparison">
              <thead>
                <tr>
                  <th>Evidence</th>
                  <th>Tab presses</th>
                  <th>Recorded focus path</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Historical</td>
                  <td>
                    {String(record?.interaction?.tab_presses ?? "Unavailable")}
                  </td>
                  <td>{focusSummary(record?.interaction)}</td>
                </tr>
                <tr>
                  <td>Live</td>
                  <td>
                    {String(
                      current.steps.find((s) => s.id === finding.step_id)
                        ?.interaction?.tab_presses ?? "Unavailable",
                    )}
                  </td>
                  <td>
                    {focusSummary(
                      current.steps.find((s) => s.id === finding.step_id)
                        ?.interaction,
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
            <details>
              <summary>Raw focus evidence</summary>
              <pre>
                {JSON.stringify(
                  {
                    historicalFocus: record?.interaction,
                    liveFocus: current.steps.find(
                      (s) => s.id === finding.step_id,
                    )?.interaction,
                  },
                  null,
                  2,
                )}
              </pre>
            </details>
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
            Re-execute the recorded path in a fresh isolated browser. Discovery
            is disabled. Sites may have changed; effects are not undone. Supply
            new inputs; historical values are never recovered.
          </p>
          <ol>
            {draft.steps.map((s) => (
              <li key={s.id}>
                {s.id} / {s.action} / {s.target?.name ?? ""}
                {s.value_from ? ` / input: ${s.value_from}` : ""}
                {s.effect ? " / potentially state-changing" : ""}
              </li>
            ))}
          </ol>
          <button
            disabled={busy || activeRun(current)}
            onClick={() => {
              setBusy(true);
              setError("");
              request<Project>("project.save", {
                project: {
                  name: `${draft.name} replay`.slice(0, 120),
                  journey: draft,
                },
              })
                .then(onAuthored)
                .catch((e) => setError(String(e)))
                .finally(() => setBusy(false));
            }}
          >
            Save as an editable journey
          </button>
          <p className="muted">
            Creates a separate project for editing prerequisites and assertions.
            Editing does not establish that server state can be restored.
          </p>
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
