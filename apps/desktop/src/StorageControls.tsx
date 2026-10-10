import { useState } from "react";
import { request } from "./api";

export default function StorageControls({
  onPrune,
}: {
  onPrune: () => Promise<void>;
}) {
  const [acknowledged, setAcknowledged] = useState(false);
  const [retention, setRetention] = useState(90);
  const [confirmPrune, setConfirmPrune] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function backup() {
    setBusy(true);
    setError("");
    try {
      const result = await request<{ base64: string; mime: string }>(
        "storage.backup",
        { acknowledge_plaintext: acknowledged },
      );
      const bytes = Uint8Array.from(atob(result.base64), (c) =>
        c.charCodeAt(0),
      );
      const url = URL.createObjectURL(new Blob([bytes], { type: result.mime }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "accessmaze-backup.zip";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage("Workspace backup exported. Keep it private.");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  async function prune() {
    setBusy(true);
    setError("");
    try {
      const result = await request<{ deleted_runs: number }>("storage.prune", {
        days: retention,
      });
      setMessage(
        `Deleted ${result.deleted_runs} old terminal runs and their evidence.`,
      );
      setConfirmPrune(false);
      await onPrune();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <h2>Backup & retention</h2>
      <p>
        Export a consistent SQLite backup with fixture evidence. In-app backups
        are bounded to 25 MiB. Restore only your own trusted backup while the
        application is closed; see the development guide.
      </p>
      <label className="check">
        <input
          type="checkbox"
          checked={acknowledged}
          onChange={(e) => setAcknowledged(e.target.checked)}
        />
        I understand the backup includes plain-text journey inputs.
      </label>
      <button disabled={!acknowledged || busy} onClick={() => void backup()}>
        Export workspace backup
      </button>
      <div className="fields">
        <label>
          Keep runs from the last (days)
          <input
            type="number"
            min="1"
            max="3650"
            value={retention}
            onChange={(e) => {
              setRetention(Number(e.target.value));
              setConfirmPrune(false);
            }}
          />
        </label>
      </div>
      <label className="check">
        <input
          type="checkbox"
          checked={confirmPrune}
          onChange={(e) => setConfirmPrune(e.target.checked)}
        />
        Permanently delete completed, failed and interrupted runs older than{" "}
        {retention} days and their evidence. Projects remain saved.
      </label>
      <button
        className="danger"
        disabled={!confirmPrune || busy}
        onClick={() => void prune()}
      >
        Delete old runs
      </button>
      <p role="status">{busy ? "Working…" : message}</p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}
