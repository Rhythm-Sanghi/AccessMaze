import { useEffect, useState } from "react";
import type { Recording, Step } from "../../../packages/contracts";
import { request } from "./api";

export default function RecorderPanel({
  disabled,
  scope,
  onStart,
  onActive,
  onApply,
}: {
  disabled: boolean;
  scope: string;
  onStart: () => Promise<string | undefined>;
  onActive: (value: boolean) => void;
  onApply: (steps: Step[]) => void;
}) {
  const [recording, setRecording] = useState<Recording | null>(null);
  const [approved, setApproved] = useState(false);
  const [effects, setEffects] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const active = !!recording && recording.status !== "stopped";
  useEffect(() => {
    if (!active) {
      setApproved(false);
      setEffects(false);
    }
  }, [scope]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!active || !recording) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const current = await request<Recording>("recorder.get", {
          id: recording!.id,
        });
        if (cancelled) return;
        setRecording(current);
        onActive(current.status !== "stopped");
        if (current.status !== "stopped") timer = setTimeout(poll, 500);
      } catch {
        if (!cancelled) {
          setError(
            "Recording interrupted. Unsaved drafts are lost after worker restart.",
          );
          setRecording(null);
          onActive(false);
        }
      }
    }
    timer = setTimeout(poll, 200);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [active, recording?.id, onActive]); // eslint-disable-line react-hooks/exhaustive-deps
  async function start() {
    setBusy(true);
    setError("");
    try {
      const project_id = await onStart();
      if (!project_id) return;
      const current = await request<Recording>("recorder.start", {
        project_id,
        authorized: approved,
        allow_effects: effects,
      });
      setRecording(current);
      onActive(true);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function command(method: "recorder.stop" | "recorder.assert") {
    if (!recording) return;
    try {
      setRecording(await request<Recording>(method, { id: recording.id }));
    } catch (e) {
      setError(String(e));
    }
  }
  return (
    <section className="retest" aria-labelledby="recorder-heading">
      <div className="section-heading">
        <h2 id="recorder-heading">Record a browser journey</h2>
        <span className="mono">LOCAL / MANUAL</span>
      </div>
      <p>
        Open an isolated browser and perform the task yourself. Recording
        captures supported clicks, navigation keys and field labels. Typed
        values and file names are never recorded; fill and upload steps become
        run-only input bindings. Review every step before replay.
      </p>
      <p className="muted">
        The session uses the origin permissions above. Page scripts can issue
        background writes while the authorized manual session is open. Popups
        and embedded frames are blocked. Labels and explicitly captured
        completion headings can contain personal information.
      </p>
      <label className="check">
        <input
          type="checkbox"
          checked={approved}
          disabled={active}
          onChange={(e) => setApproved(e.target.checked)}
        />
        I am authorized to record this website using a dedicated test account.
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={effects}
          disabled={active}
          onChange={(e) => setEffects(e.target.checked)}
        />
        I authorize interactions and requests during this manual session,
        including submissions and uploads.
      </label>
      <div className="toolbar">
        <button
          disabled={disabled || busy || active || !approved || !effects}
          onClick={() => void start()}
        >
          Open recording browser
        </button>
        {active && (
          <>
            <button
              disabled={recording?.status !== "recording"}
              onClick={() => void command("recorder.assert")}
            >
              Capture current H1 as completion
            </button>
            <button
              className="danger"
              onClick={() => void command("recorder.stop")}
            >
              Stop recording
            </button>
          </>
        )}
      </div>
      {recording && (
        <>
          <p role="status">
            {recording.status} · {recording.steps.length} steps ·{" "}
            {recording.origin}
          </p>
          <ol>
            {recording.steps.map((s) => (
              <li key={s.id}>
                <span className="mono">{s.action}</span> ·{" "}
                {s.target?.name ?? s.file_label ?? s.value}
                {s.value_from ? ` / run input: ${s.value_from}` : ""}
              </li>
            ))}
          </ol>
          <ul>
            {recording.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
          {recording.status === "stopped" && (
            <button onClick={() => onApply(recording.steps)}>
              Review these steps in the editor
            </button>
          )}
          <p className="muted">
            A recording is an editable draft, not a passed test. Capture a real
            completion condition or add one in the editor before saving.
          </p>
        </>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
