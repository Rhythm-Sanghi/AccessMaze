import type { Journey } from "../../../packages/contracts";

export interface Inputs {
  values: Record<string, string>;
  files: Record<string, { name: string; base64: string }>;
}
export const emptyInputs = (): Inputs => ({ values: {}, files: {} });

export default function RunInputs({
  journey,
  inputs,
  onChange,
  onError,
}: {
  journey: Journey;
  inputs: Inputs;
  onChange: (inputs: Inputs) => void;
  onError: (message: string) => void;
}) {
  const text = [
    ...new Set(
      journey.steps
        .filter((s) => s.value_from && s.action !== "upload")
        .map((s) => s.value_from!),
    ),
  ];
  const files = [
    ...new Set(
      journey.steps
        .filter((s) => s.action === "upload" && s.value_from)
        .map((s) => s.value_from!),
    ),
  ];
  if (!text.length && !files.length) return null;
  return (
    <section aria-labelledby="inputs-heading">
      <h2 id="inputs-heading">Inputs for this run</h2>
      <p className="muted">
        Held in memory and cleared after launch. Values, file names and contents
        are excluded from saved journeys and reports. Use a dedicated test
        account and review upload destinations. Combined file limit: 4 MiB.
      </p>
      <div className="fields">
        {text.map((key) => (
          <label key={key}>
            {key}
            <input
              type="password"
              autoComplete="off"
              value={inputs.values[key] ?? ""}
              onChange={(e) =>
                onChange({
                  ...inputs,
                  values: { ...inputs.values, [key]: e.target.value },
                })
              }
            />
          </label>
        ))}
        {files.map((key) => (
          <label key={key}>
            {key}
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                if (file.size > 4 * 1024 ** 2) {
                  onError("File exceeds the 4 MiB upload limit");
                  return;
                }
                const reader = new FileReader();
                reader.onload = () =>
                  onChange({
                    ...inputs,
                    files: {
                      ...inputs.files,
                      [key]: {
                        name: file.name,
                        base64: String(reader.result).split(",")[1],
                      },
                    },
                  });
                reader.onerror = () => onError("Cannot read selected file");
                reader.readAsDataURL(file);
              }}
            />
          </label>
        ))}
      </div>
    </section>
  );
}
