import StorageControls from "./StorageControls";
export default function Settings({
  theme,
  onTheme,
  onPrune,
}: {
  theme: string;
  onTheme: (theme: string) => void;
  onPrune: () => Promise<void>;
}) {
  return (
    <section className="settings">
      <h2>Workspace preferences</h2>
      <label>
        Appearance
        <select value={theme} onChange={(e) => onTheme(e.target.value)}>
          <option value="light">Workshop light</option>
          <option value="dark">Workshop dark</option>
        </select>
      </label>
      <h2>Data & privacy</h2>
      <p>
        Projects and runs are stored in the desktop application data directory.
        No analytics or remote account is used. Deleting a project removes its
        saved runs and associated artifacts.
      </p>
      <p>
        Use synthetic data. Journey inputs are saved in plain text; evidence
        redacts entered values and masks fixture screenshot inputs. Redaction
        cannot guarantee removal of unrelated personal information displayed by
        a target.
      </p>
      <StorageControls onPrune={onPrune} />
      <h2>Analysis boundaries</h2>
      <p>
        Automated keyboard interaction and DOM accessibility semantics are
        supported. Real screen-reader evaluation, exhaustive branch exploration
        and WCAG conformance certification are not supported.
      </p>
      <h2>Retesting</h2>
      <p>
        Rerun the same journey after repairing the target, then compare the
        selected run with earlier evidence. A repair is verified only when the
        same configuration completes and its relevant assertion or rule passes.
        Each execution and comparison is saved separately.
      </p>
    </section>
  );
}
