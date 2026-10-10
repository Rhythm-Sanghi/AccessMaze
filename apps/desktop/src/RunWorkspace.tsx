import { useEffect, useState } from "react";
import type { Run } from "../../../packages/contracts";
import { request } from "./api";

export const activeRun = (run: Run | null) =>
  !!run &&
  ["preparing", "running", "paused", "awaiting_approval"].includes(run.status);
export default function RunWorkspace({
  run,
  onControl,
  onApprove,
}: {
  run: Run;
  onControl: (action: "cancel" | "pause" | "resume") => void;
  onApprove?: (proposal: string, choice: string) => void;
}) {
  const [selected, setSelected] = useState("");
  const [scale, setScale] = useState(1);
  const [image, setImage] = useState("");
  const [error, setError] = useState("");
  const node = run.nodes.find((n) => n.id === selected) ?? run.nodes.at(-1);
  const finding =
    run.findings.find((f) =>
      run.steps.some((s) => s.id === f.step_id && s.state_id === node?.id),
    ) ?? run.findings.find((f) => f.step_id === node?.first_step);
  useEffect(() => {
    let disposed = false;
    setImage("");
    setError("");
    if (finding?.screenshot)
      request<{ url: string }>("evidence.read", {
        id: run.id,
        name: finding.screenshot,
      })
        .then((r) => {
          if (!disposed) setImage(r.url);
        })
        .catch((e) => {
          if (!disposed) setError(String(e));
        });
    return () => {
      disposed = true;
    };
  }, [run.id, finding?.screenshot]);
  return (
    <section aria-label="Analysis workspace">
      <div className="section-heading">
        <div>
          <h2>{run.journey.name}</h2>
          <p className="mono muted">
            {run.id.slice(0, 8)} / {new Date(run.started_at).toLocaleString()}
          </p>
        </div>
        <div className="toolbar">
          <span className={`status ${run.status}`} role="status">
            {run.status.replaceAll("_", " ")}
          </span>
          {activeRun(run) && (
            <>
              <button
                disabled={run.status === "awaiting_approval"}
                onClick={() =>
                  onControl(run.status === "paused" ? "resume" : "pause")
                }
              >
                {run.status === "paused" ? "Resume" : "Pause after step"}
              </button>
              <button className="danger" onClick={() => onControl("cancel")}>
                Emergency stop
              </button>
            </>
          )}
        </div>
      </div>
      {run.error && (
        <p role="alert" className="error">
          {run.error}
        </p>
      )}
      {run.outcome && (
        <section aria-label="Task outcome">
          <h3>Task outcome: {run.outcome.status}</h3>
          <p>{run.outcome.reason}</p>
          {run.outcome.blocked_step_id && (
            <p className="mono">Blocked step: {run.outcome.blocked_step_id}</p>
          )}
          <ul>
            {run.outcome.assertions.map((a) => (
              <li key={a.step_id}>
                {a.step_id}: {a.status}
              </li>
            ))}
          </ul>
          <p className="muted">{run.outcome.limitation}</p>
        </section>
      )}
      {run.approval && run.status === "awaiting_approval" && (
        <section className="run-gate" aria-labelledby="approval-heading">
          <h3 id="approval-heading">Approve one website action</h3>
          <p>
            The browser is waiting. Each action can submit data or change
            external state. Approve only an interaction you are authorized to
            perform. Other branches remain untested. Names below are transient
            and remain withheld from private evidence.
          </p>
          <div className="toolbar">
            {run.approval.choices.map((choice) => (
              <button
                key={choice.id}
                onClick={() => onApprove?.(run.approval!.id, choice.id)}
              >
                Approve {choice.role}: {choice.name}
              </button>
            ))}
          </div>
          <button onClick={() => onApprove?.(run.approval!.id, "stop")}>
            Finish without further actions
          </button>
        </section>
      )}
      <div className="workspace-grid">
        <section className="journey-panel" aria-label="Journey execution">
          <h3>Executed path</h3>
          <p className="muted">
            {run.steps.filter((s) => s.status === "passed").length} /{" "}
            {run.journey.steps.length} steps passed
          </p>
          <ol className="run-steps">
            {run.journey.steps.map((s, i) => {
              const recorded = run.steps.find((r) => r.id === s.id);
              return (
                <li key={s.id}>
                  <button onClick={() => setSelected(recorded?.state_id ?? "")}>
                    <span className="mono muted">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span>
                      {s.id}
                      <small>{s.action}</small>
                    </span>
                    <span className="step-state">
                      {recorded?.status ?? "pending"}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
          <h3>Profile</h3>
          <p>
            {run.journey.profile.keyboard_only
              ? "Keyboard only"
              : "Pointer permitted"}
          </p>
          <p className="mono muted">
            {run.journey.profile.viewport_width} ×{" "}
            {run.journey.profile.viewport_height}
          </p>
          <p className="muted">
            Layout zoom emulation:{" "}
            {run.journey.profile.layout_zoom_percent ?? 100}%
            {node?.observation.viewport &&
              ` · observed CSS viewport ${node.observation.viewport.width} × ${node.observation.viewport.height}`}
          </p>
          <h3>Coverage limits</h3>
          {run.exploration && (
            <>
              <h3>Branch discovery</h3>
              <p>
                {run.exploration.actions.length}{" "}
                {run.exploration.mode?.startsWith("approved-")
                  ? "approved website actions"
                  : "replay/discovery actions"}
              </p>
              <p>
                {run.exploration.stop_reason === "running"
                  ? "Exploration in progress"
                  : `Stopped: ${run.exploration.stop_reason}`}
              </p>
              <p>
                {run.exploration.pending_branches.length} bounded frontier
                states or actions
              </p>
              <details>
                <summary>Executed discovery actions and reachability</summary>
                <p className="muted">
                  Each result describes an actual bounded attempt. Pending
                  branches have no accessibility verdict.
                </p>
                <div
                  className="table-scroll"
                  tabIndex={0}
                  role="region"
                  aria-label="Scrollable discovery execution evidence"
                >
                  <table aria-label="Approved discovery actions">
                    <thead>
                      <tr>
                        <th>Action</th>
                        <th>Target</th>
                        <th>Execution</th>
                        <th>Keyboard evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {run.exploration.actions.map((a) => (
                        <tr key={a.step_id}>
                          <td>
                            {a.step_id} / {a.action}
                          </td>
                          <td>{a.target?.name ?? "configured start"}</td>
                          <td>{a.status}</td>
                          <td>
                            {a.reachability ?? "See recorded interaction"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
              <details>
                <summary>Pending branches</summary>
                <ul>
                  {run.exploration.pending_branches.map((b, i) => (
                    <li key={i}>
                      {b.state_id.slice(0, 8)} / {b.path.join(" → ") || "root"}{" "}
                      / {b.reason ?? "untested"}
                    </li>
                  ))}
                </ul>
              </details>
            </>
          )}
          <ul className="limitations">
            {run.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </section>
        <div className="graph-panel">
          <div className="panel-heading">
            <h3>Observed state graph</h3>
            <div className="toolbar">
              <button
                aria-label="Zoom out"
                onClick={() => setScale((s) => Math.max(0.5, s - 0.25))}
              >
                −
              </button>
              <span className="mono">{Math.round(scale * 100)}%</span>
              <button
                aria-label="Zoom in"
                onClick={() => setScale((s) => Math.min(2, s + 0.25))}
              >
                +
              </button>
            </div>
          </div>
          <p className="muted">
            Each node is a distinct observed state. Scroll to pan; select a
            state to inspect it.
          </p>
          <div
            className="graph-scroll"
            tabIndex={0}
            role="region"
            aria-label="Scrollable observed-state graph"
          >
            <div
              className="graph"
              style={{
                width: Math.max(520, run.nodes.length * 175) * scale,
                height: 260 * scale,
              }}
            >
              <svg
                role="img"
                aria-label="Observed journey transitions; equivalent table below"
                width="100%"
                height="100%"
                viewBox={`0 0 ${Math.max(520, run.nodes.length * 175)} 260`}
              >
                <defs>
                  <marker
                    id="arrow"
                    markerWidth="8"
                    markerHeight="8"
                    refX="7"
                    refY="3"
                    orient="auto"
                  >
                    <path d="M0,0 L0,6 L8,3z" fill="currentColor" />
                  </marker>
                </defs>
                {run.edges.map((edge, i) => {
                  const x =
                    run.nodes.findIndex((n) => n.id === edge.source) * 175 + 65;
                  const y =
                    run.nodes.findIndex((n) => n.id === edge.target) * 175 + 65;
                  return (
                    <path
                      key={i}
                      d={
                        x === y
                          ? `M${x} 110 c-55 -85 55 -85 0 0`
                          : `M${x} 130 Q${(x + y) / 2} ${edge.cycle ? 20 : 130} ${y} 130`
                      }
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      markerEnd="url(#arrow)"
                    />
                  );
                })}
                {run.nodes.map((n, i) => (
                  <g key={n.id} transform={`translate(${i * 175 + 65},130)`}>
                    <circle
                      r="28"
                      className={n.id === node?.id ? "selected-node" : ""}
                    />
                    <text textAnchor="middle" y="5">
                      {String(i + 1).padStart(2, "0")}
                    </text>
                    <text textAnchor="middle" y="58" className="node-label">
                      {n.first_step}
                    </text>
                  </g>
                ))}
              </svg>
              <div className="graph-node-controls">
                {run.nodes.map((n, i) => (
                  <button
                    key={n.id}
                    aria-pressed={n.id === node?.id}
                    onClick={() => setSelected(n.id)}
                  >
                    {String(i + 1).padStart(2, "0")} · {n.first_step}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {!run.nodes.length && (
            <p className="empty-inline">
              States appear after real browser observations.
            </p>
          )}
          <details open>
            <summary>Accessible transition table</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Step</th>
                    <th>From</th>
                    <th>To</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {run.edges.map((e, i) => (
                    <tr key={i}>
                      <td>{e.step_id}</td>
                      <td className="mono">{e.source.slice(0, 6)}</td>
                      <td>
                        <button onClick={() => setSelected(e.target)}>
                          {e.target.slice(0, 6)}
                        </button>
                      </td>
                      <td>
                        {e.status}
                        {e.cycle ? " / cycle" : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
          {node && (
            <section className="observation">
              <h3>
                State / <span className="mono">{node.id.slice(0, 8)}</span>
              </h3>
              <p>{node.observation.title}</p>
              <p className="mono muted">{node.observation.url}</p>
              {node.observation.text_withheld && (
                <p className="muted">
                  Website text is private. Tokens identify states within this
                  run.
                </p>
              )}
              {node.observation.ax_tree && (
                <details>
                  <summary>Computed browser accessibility tree</summary>
                  <p className="muted">
                    {node.observation.ax_tree.source}. Bounded to depth 8 and
                    500 semantic nodes. This is browser data, not a screen
                    reader test. Field values are omitted.
                  </p>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Role</th>
                          <th>Computed name</th>
                          <th>Focus</th>
                          <th>Control state</th>
                        </tr>
                      </thead>
                      <tbody>
                        {node.observation.ax_tree.nodes.map((n, i) => (
                          <tr key={i}>
                            <td>{n.role}</td>
                            <td>{n.name}</td>
                            <td>{n.focused ? "focused" : ""}</td>
                            <td>{JSON.stringify(n.states ?? {})}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              )}
              <p>
                Network: {node.observation.online ? "online" : "offline"} ·
                Motion preference:{" "}
                {node.observation.reduced_motion ? "reduce" : "no preference"}
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Control</th>
                      <th>Accessible label signal</th>
                      <th>State</th>
                    </tr>
                  </thead>
                  <tbody>
                    {node.observation.controls.map((c, i) => (
                      <tr key={i}>
                        <td>{c.role ?? c.tag}</td>
                        <td>{c.name || "No observed label"}</td>
                        <td>
                          {c.focused ? "focused / " : ""}
                          {c.disabled
                            ? "disabled"
                            : c.visible
                              ? "visible"
                              : "hidden"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
        <section className="evidence-panel" aria-label="Evidence and findings">
          <h3>Evidence & findings</h3>
          <p className="muted">{run.findings.length} recorded findings</p>
          {run.findings.map((f) => (
            <article key={f.id} className="finding">
              <span className="status failed">{f.severity}</span>
              <h4>{f.title}</h4>
              <p className="mono">
                {f.rule} / {f.step_id}
              </p>
              <p>{f.verification}</p>
              <dl>
                <dt>Actual</dt>
                <dd>
                  {typeof f.actual === "string"
                    ? f.actual
                    : JSON.stringify(f.actual)}
                </dd>
                <dt>Expected</dt>
                <dd>{f.expected}</dd>
                <dt>Reproduce</dt>
                <dd>{f.reproduction.join(" → ")}</dd>
                <dt>Remediation</dt>
                <dd>{f.remediation}</dd>
              </dl>
            </article>
          ))}
          {!run.findings.length && (
            <p className="empty-inline">
              No findings recorded. This does not establish accessibility
              conformance.
            </p>
          )}
          {image && (
            <figure>
              <img
                src={image}
                alt="Captured failure state with form input contents masked"
              />
              <figcaption className="muted">
                Captured synthetic fixture. Form inputs masked.
              </figcaption>
            </figure>
          )}
          {error && <p role="alert">{error}</p>}
        </section>
      </div>
    </section>
  );
}
