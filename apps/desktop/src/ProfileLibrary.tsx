import { useEffect, useState } from "react";
import type { Journey, SavedProfile } from "../../../packages/contracts";
import { request } from "./api";

export default function ProfileLibrary({
  profile,
  onApply,
}: {
  profile: Journey["profile"];
  onApply: (profile: Journey["profile"]) => void;
}) {
  const [profiles, setProfiles] = useState<SavedProfile[]>([]);
  const [selected, setSelected] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    void request<SavedProfile[]>("profile.list")
      .then(setProfiles)
      .catch((e) => setError(String(e)));
  }, []);
  async function save(update: boolean) {
    setError("");
    try {
      const saved = await request<SavedProfile>("profile.save", {
        id: update ? selected : undefined,
        profile: { name, profile },
      });
      setProfiles(await request<SavedProfile[]>("profile.list"));
      setSelected(saved.id);
      setMessage(
        "Profile saved. Existing journeys retain their own condition snapshots.",
      );
    } catch (e) {
      setError(String(e));
    }
  }
  return (
    <section aria-label="Reusable capability profiles">
      <p>
        Reuse concrete conditions across journeys. Apply a saved profile, review
        its settings below, then authorize each run. Run another profile and
        compare the stored outcomes in run history. Different conditions cannot
        establish a repair.
      </p>
      <div className="fields">
        <label>
          Saved capability profile
          <select
            value={selected}
            onChange={(e) => {
              setSelected(e.target.value);
              const saved = profiles.find((p) => p.id === e.target.value);
              if (saved) {
                setName(saved.name);
                onApply(structuredClone(saved.profile));
                setMessage("Profile applied as an editable journey snapshot");
              }
            }}
          >
            <option value="">Choose profile</option>
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Profile name
          <input
            maxLength={120}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
      </div>
      <div className="toolbar">
        <button disabled={!name.trim()} onClick={() => void save(false)}>
          Save as new profile
        </button>
        <button
          disabled={!selected || !name.trim()}
          onClick={() => void save(true)}
        >
          Update saved profile
        </button>
        <button
          disabled={!selected}
          onClick={() =>
            void (async () => {
              try {
                await request("profile.delete", { id: selected });
                setProfiles(await request<SavedProfile[]>("profile.list"));
                setSelected("");
                setMessage(
                  "Library profile removed; journey snapshots retained",
                );
              } catch (e) {
                setError(String(e));
              }
            })()
          }
        >
          Remove from library
        </button>
      </div>
      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
      <p className="muted">
        Profiles do not simulate a disability or screen-reader use. Layout zoom
        emulates reflow through viewport and device scale, not browser chrome
        zoom. Delay is per-request delay, not bandwidth. Offline/recovery uses
        Chromium context connectivity; in-flight responses may finish. Focus and
        semantics checks verify only their configured targets and rules.
      </p>
    </section>
  );
}
