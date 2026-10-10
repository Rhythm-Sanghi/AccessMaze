import { useState } from "react";
import type { Project } from "../../../packages/contracts";

const fixtures = [
  {
    id: "accessible",
    name: "Accessible application",
    description: "Complete the corrected scholarship preparation workflow.",
  },
  {
    id: "broken",
    name: "Keyboard blocker",
    description: "Find a pointer-only date control.",
  },
  {
    id: "errors",
    name: "Error discoverability",
    description: "Inspect missing error associations and live semantics.",
  },
  {
    id: "recovery",
    name: "Connection recovery",
    description: "Check entered values after offline / online transitions.",
  },
  {
    id: "branch",
    name: "Conditional path & reset",
    description:
      "Traverse successful and validation paths; observe repeated states.",
  },
  {
    id: "slow",
    name: "Long-running journey",
    description: "Verify cancellation on a slow page and deliberate wait.",
  },
  {
    id: "modal",
    name: "Modal focus behavior",
    description: "Inspect focus escaping an open modal.",
  },
  {
    id: "conditional",
    name: "Conditional application",
    description: "Fill a dynamic field and submit a synthetic application.",
  },
];
interface Props {
  projects: Project[];
  disabled: boolean;
  onChoose: (p: Project) => void;
  onCreate: (kind: string) => void;
  onArchive: (p: Project) => void;
  onDelete: (p: Project) => void;
}
export default function Projects({
  projects,
  disabled,
  onChoose,
  onCreate,
  onArchive,
  onDelete,
}: Props) {
  const [showArchived, setShowArchived] = useState(false);
  const visible = projects.filter((p) => showArchived || !p.archived);
  return (
    <>
      <div className="section-heading">
        <div>
          <h2>Saved investigations</h2>
          <p className="muted">
            Define a task. Apply concrete constraints. Inspect what happened.
          </p>
        </div>
        <label className="check">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
          />
          Show archived
        </label>
      </div>
      {visible.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Project / target</th>
                <th>Last analysis</th>
                <th>Confirmed findings</th>
                <th>Incomplete runs</th>
                <th>State</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((p) => (
                <tr key={p.id}>
                  <td>
                    <button
                      disabled={disabled}
                      className="text-button"
                      onClick={() => onChoose(p)}
                    >
                      {p.name}
                    </button>
                    <small className="mono muted">{p.journey.target}</small>
                  </td>
                  <td>
                    {p.summary?.last_analysis
                      ? new Date(p.summary.last_analysis).toLocaleString()
                      : "Never run"}
                  </td>
                  <td>{p.summary?.confirmed_findings ?? 0}</td>
                  <td>{p.summary?.incomplete_runs ?? 0}</td>
                  <td>{p.archived ? "Archived" : "Active"}</td>
                  <td>
                    <div className="toolbar">
                      <button disabled={disabled} onClick={() => onChoose(p)}>
                        Open
                      </button>
                      <button disabled={disabled} onClick={() => onArchive(p)}>
                        {p.archived ? "Restore" : "Archive"}
                      </button>
                      <button
                        disabled={disabled}
                        className="danger"
                        onClick={() => onDelete(p)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty">
          <span className="mono large-index">00 / PROJECTS</span>
          <h2>Your first investigation starts with a task.</h2>
          <p>
            Choose a bundled synthetic workflow below. Its results come from a
            real browser run.
          </p>
        </div>
      )}
      <div className="section-heading">
        <h2>Test your website</h2>
        <button disabled={disabled} onClick={() => onCreate("website")}>
          + Website investigation
        </button>
      </div>
      <p className="muted">
        Start with a target URL and a completion assertion. Review origin
        permissions before running.
      </p>
      <div className="section-heading">
        <h2>Start from a local fixture</h2>
        <span className="mono">OFFLINE READY AFTER SETUP</span>
      </div>
      <div className="fixture-list">
        {fixtures.map((fixture, i) => (
          <button
            disabled={disabled}
            key={fixture.id}
            onClick={() => onCreate(fixture.id)}
          >
            <span className="mono">0{i + 1}</span>
            <span>
              <strong>{fixture.name}</strong>
              <small>{fixture.description}</small>
            </span>
            <span aria-hidden="true">↗</span>
          </button>
        ))}
      </div>
    </>
  );
}
