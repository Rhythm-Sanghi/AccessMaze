import type { Run } from "../../../packages/contracts";
export default function Reports({
  run,
  busy,
  onExport,
}: {
  run: Run | null;
  busy: boolean;
  onExport: (format: string) => void;
}) {
  return (
    <>
      <div className="section-heading">
        <h2>Export recorded evidence</h2>
      </div>
      <p>
        Reports include recorded findings, step results, configuration, versions
        and coverage limitations. Entered values are redacted. Screenshot files
        remain in local run storage.
      </p>
      {run ? (
        <>
          <p className="mono">Selected run: {run.id}</p>
          <div className="toolbar">
            {["json", "html", "csv"].map((format) => (
              <button
                disabled={busy}
                key={format}
                onClick={() => onExport(format)}
              >
                Export {format.toUpperCase()}
              </button>
            ))}
          </div>
          <p className="muted">
            JSON is the authoritative complete run record. CSV summarizes
            findings. HTML is a readable snapshot. PDF export is not yet
            supported.
          </p>
        </>
      ) : (
        <p>Select a recorded run to enable exports.</p>
      )}
    </>
  );
}
