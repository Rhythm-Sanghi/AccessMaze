import type { Journey } from "../../../packages/contracts";

export default function NetworkPermissions({
  journey,
  onChange,
}: {
  journey: Journey;
  onChange: (value: Journey) => void;
}) {
  const network = journey.network ?? {
    navigation_origins: [],
    resource_origins: [],
  };
  return (
    <section aria-labelledby="network-heading">
      <div className="section-heading">
        <h2 id="network-heading">Website permissions</h2>
      </div>
      <p>
        The target origin is included. Add only origins you trust and are
        authorized to test. Scripts from approved resource origins can read page
        data. Use a dedicated test account.
      </p>
      <div className="fields">
        <label>
          Additional navigation and API origins
          <textarea
            rows={3}
            placeholder="https://login.example.org"
            value={network.navigation_origins.join("\n")}
            onChange={(e) =>
              onChange({
                ...journey,
                network: {
                  ...network,
                  navigation_origins: e.target.value
                    .split("\n")
                    .filter(Boolean),
                },
              })
            }
          />
        </label>
        <label>
          Additional read-only resource origins
          <textarea
            rows={3}
            placeholder="https://static.example.org"
            value={network.resource_origins.join("\n")}
            onChange={(e) =>
              onChange({
                ...journey,
                network: {
                  ...network,
                  resource_origins: e.target.value.split("\n").filter(Boolean),
                },
              })
            }
          />
        </label>
      </div>
      <p className="muted">
        One exact HTTP(S) origin per line, including a port if needed. No
        wildcards or paths. Resource permission allows reads, not navigation or
        writes. Mutating requests require an effect-declared action. Private
        networks need separate authorization.
      </p>
      <label className="check">
        <input
          type="checkbox"
          checked={network.embedded_frames ?? false}
          onChange={(e) =>
            onChange({
              ...journey,
              network: {
                ...network,
                mode: e.target.checked
                  ? "authorized-application"
                  : "restricted",
                embedded_frames: e.target.checked,
              },
            })
          }
        />
        Authorize embedded frame navigation at approved navigation origins
      </label>
      <p className="muted">
        Named-frame journey targets require this permission. Popups, WebSockets,
        service workers and downloads remain unsupported. Approval does not
        create a strong security sandbox.
      </p>
      <label className="check">
        <input
          type="checkbox"
          checked={journey.privacy?.capture_page_text ?? false}
          onChange={(e) =>
            onChange({
              ...journey,
              privacy: { capture_page_text: e.target.checked },
            })
          }
        />
        Save website headings, control names and URL paths in evidence
      </label>
      <p className="muted">
        Off by default for websites. Private text is replaced with per-run
        tokens; graph states remain distinguishable. Enabling this can save
        personal information. Website screenshots, cookies and response bodies
        are never included in reports.
      </p>
    </section>
  );
}
