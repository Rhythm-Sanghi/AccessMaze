import type { Action, Journey, Role, Step } from "../../../packages/contracts";
import NetworkPermissions from "./NetworkPermissions";

const actions: Action[] = [
  "navigate",
  "fill",
  "activate",
  "press",
  "assert_visible",
  "assert_value",
  "assert_errors",
  "assert_modal",
  "assert_focus",
  "offline",
  "online",
  "wait",
  "audit",
  "upload",
];
const roles: Role[] = [
  "button",
  "link",
  "textbox",
  "checkbox",
  "combobox",
  "heading",
  "status",
  "alert",
  "dialog",
  "radio",
  "spinbutton",
];
const targeted = new Set<Action>([
  "assert_modal",
  "assert_focus",
  "fill",
  "activate",
  "assert_visible",
  "assert_value",
]);
export default function JourneyEditor({
  journey,
  onChange,
}: {
  journey: Journey;
  onChange: (value: Journey) => void;
}) {
  const exploration = journey.exploration ?? {
    enabled: false,
    max_depth: 2,
    max_actions: 50,
  };
  function update(index: number, patch: Partial<Step>) {
    onChange({
      ...journey,
      steps: journey.steps.map((s, i) =>
        i === index ? { ...s, ...patch } : s,
      ),
    });
  }
  function move(index: number, direction: number) {
    const steps = [...journey.steps];
    const to = index + direction;
    [steps[index], steps[to]] = [steps[to], steps[index]];
    onChange({ ...journey, steps });
  }
  return (
    <section aria-labelledby="journey-heading">
      <div className="section-heading">
        <h2 id="journey-heading">Journey definition</h2>
        <span className="mono">SCHEMA / 01</span>
      </div>
      <div className="fields">
        <label>
          Journey name
          <input
            value={journey.name}
            onChange={(e) => onChange({ ...journey, name: e.target.value })}
          />
        </label>
        <label>
          Target URL
          <input
            value={journey.target}
            placeholder="https://your-authorized-test-site.example"
            onChange={(e) => onChange({ ...journey, target: e.target.value })}
          />
        </label>
      </div>
      <p className="muted">
        Use role and accessible name targets. Enter synthetic test data only.
        Saved journey inputs are stored locally as plain text; run evidence
        redacts entered values.
      </p>
      <ol className="editor-steps">
        {journey.steps.map((step, index) => (
          <li key={step.id}>
            <span className="step-number mono">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div className="step-fields">
              <div className="fields">
                <label>
                  Step ID
                  <input
                    aria-label={`Step ${index + 1} ID`}
                    value={step.id}
                    onChange={(e) => update(index, { id: e.target.value })}
                  />
                </label>
                <label>
                  Action
                  <select
                    aria-label={`Step ${index + 1} action`}
                    value={step.action}
                    onChange={(e) => {
                      const action = e.target.value as Action;
                      update(index, {
                        action,
                        effect: ["activate", "upload"].includes(action),
                        value_from: null,
                        target: targeted.has(action)
                          ? { role: "button", name: "Target name" }
                          : null,
                      });
                    }}
                  >
                    {actions.map((a) => (
                      <option key={a}>{a}</option>
                    ))}
                  </select>
                </label>
                {targeted.has(step.action) && (
                  <>
                    <label>
                      Locator
                      <select
                        aria-label={`Step ${index + 1} locator`}
                        value={step.target?.by ?? "role"}
                        onChange={(e) =>
                          update(index, {
                            target: {
                              ...step.target!,
                              by: e.target.value as "role" | "label",
                            },
                          })
                        }
                      >
                        <option value="role">Role and name</option>
                        <option value="label">Field label</option>
                      </select>
                    </label>
                    <label>
                      Role
                      <select
                        aria-label={`Step ${index + 1} role`}
                        value={step.target?.role ?? "button"}
                        onChange={(e) =>
                          update(index, {
                            target: {
                              ...step.target,
                              role: e.target.value as Role,
                              name: step.target?.name ?? "",
                            },
                          })
                        }
                      >
                        {roles.map((r) => (
                          <option key={r}>{r}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Accessible name
                      <input
                        aria-label={`Step ${index + 1} name`}
                        value={step.target?.name ?? ""}
                        onChange={(e) =>
                          update(index, {
                            target: {
                              ...step.target,
                              role: step.target?.role ?? "button",
                              name: e.target.value,
                            },
                          })
                        }
                      />
                    </label>
                  </>
                )}
                {step.action === "upload" && (
                  <label>
                    File input label
                    <input
                      aria-label={`Step ${index + 1} file label`}
                      value={step.file_label ?? ""}
                      onChange={(e) =>
                        update(index, { file_label: e.target.value })
                      }
                    />
                  </label>
                )}
                {["fill", "assert_value", "upload"].includes(step.action) && (
                  <label>
                    Run-only input key (optional for text)
                    <input
                      aria-label={`Step ${index + 1} runtime key`}
                      value={step.value_from ?? ""}
                      placeholder="test_password"
                      onChange={(e) =>
                        update(index, {
                          value_from: e.target.value || null,
                          value: e.target.value ? "" : step.value,
                        })
                      }
                    />
                  </label>
                )}
                {!step.value_from &&
                  ["fill", "press", "assert_value", "wait"].includes(
                    step.action,
                  ) && (
                    <label>
                      Value
                      <input
                        aria-label={`Step ${index + 1} value`}
                        value={step.value}
                        onChange={(e) =>
                          update(index, { value: e.target.value })
                        }
                      />
                    </label>
                  )}
              </div>
              <div className="step-options">
                <label className="check">
                  <input
                    type="checkbox"
                    checked={step.optional}
                    onChange={(e) =>
                      update(index, { optional: e.target.checked })
                    }
                  />
                  Optional
                </label>
                <label className="check">
                  <input
                    type="checkbox"
                    checked={step.effect}
                    onChange={(e) =>
                      update(index, { effect: e.target.checked })
                    }
                  />
                  Potential external effect
                </label>
                <button
                  disabled={index === 0}
                  onClick={() => move(index, -1)}
                  aria-label={`Move step ${index + 1} up`}
                >
                  ↑
                </button>
                <button
                  disabled={index === journey.steps.length - 1}
                  onClick={() => move(index, 1)}
                  aria-label={`Move step ${index + 1} down`}
                >
                  ↓
                </button>
                <button
                  onClick={() =>
                    onChange({
                      ...journey,
                      steps: journey.steps.filter((_, i) => i !== index),
                    })
                  }
                  aria-label={`Remove step ${index + 1}`}
                >
                  Remove
                </button>
              </div>
            </div>
          </li>
        ))}
      </ol>
      <button
        onClick={() =>
          onChange({
            ...journey,
            steps: [
              ...journey.steps,
              {
                id: `step-${crypto.randomUUID().slice(0, 8)}`,
                action: "assert_visible",
                target: { role: "heading", name: "Confirmation" },
                value: "",
                optional: false,
                effect: false,
              },
            ],
          })
        }
      >
        + Add step
      </button>
      <div className="section-heading">
        <h2>Concrete test conditions</h2>
        <span className="mono">PROFILE</span>
      </div>
      <div className="fields">
        <label>
          Action timeout (milliseconds)
          <input
            type="number"
            min="1000"
            max="30000"
            value={journey.profile.action_timeout_ms ?? 10000}
            onChange={(e) =>
              onChange({
                ...journey,
                profile: {
                  ...journey.profile,
                  action_timeout_ms: Number(e.target.value),
                },
              })
            }
          />
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={journey.profile.keyboard_only}
            onChange={(e) =>
              onChange({
                ...journey,
                profile: {
                  ...journey.profile,
                  keyboard_only: e.target.checked,
                },
              })
            }
          />
          Keyboard only
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={journey.profile.reduced_motion}
            onChange={(e) =>
              onChange({
                ...journey,
                profile: {
                  ...journey.profile,
                  reduced_motion: e.target.checked,
                },
              })
            }
          />
          Reduced motion preference
        </label>
        {(
          ["viewport_width", "viewport_height", "network_latency_ms"] as const
        ).map((key) => (
          <label key={key}>
            {key.replaceAll("_", " ")}
            <input
              type="number"
              value={journey.profile[key]}
              onChange={(e) =>
                onChange({
                  ...journey,
                  profile: {
                    ...journey.profile,
                    [key]: Number(e.target.value),
                  },
                })
              }
            />
          </label>
        ))}
        <label>
          Time budget (seconds)
          <input
            type="number"
            min="1"
            max="300"
            value={journey.max_seconds}
            onChange={(e) =>
              onChange({ ...journey, max_seconds: Number(e.target.value) })
            }
          />
        </label>
        <label>
          Tab budget per target
          <input
            type="number"
            min="1"
            max="200"
            value={journey.tab_budget}
            onChange={(e) =>
              onChange({ ...journey, tab_budget: Number(e.target.value) })
            }
          />
        </label>
      </div>
      <div className="section-heading">
        <h2>Bounded branch discovery</h2>
      </div>
      <label className="check">
        <input
          type="checkbox"
          checked={exploration.enabled}
          onChange={(e) =>
            onChange({
              ...journey,
              exploration: { ...exploration, enabled: e.target.checked },
            })
          }
        />
        {journey.target.startsWith("fixture://")
          ? "Explore named buttons after completion (resettable synthetic fixture)"
          : "Propose semantic buttons, links, checkboxes and radios; approve each action"}
      </label>
      {exploration.enabled && !journey.target.startsWith("fixture://") && (
        <label className="check">
          <input
            type="checkbox"
            checked={exploration.recover_navigation ?? false}
            onChange={(e) =>
              onChange({
                ...journey,
                exploration: {
                  ...exploration,
                  recover_navigation: e.target.checked,
                },
              })
            }
          />
          Offer separately approved navigation to the configured start for other
          branches. This does not undo effects or replay form inputs.
        </label>
      )}
      {exploration.enabled && (
        <div className="fields">
          <label>
            Exploration depth
            <input
              type="number"
              min="1"
              max="4"
              value={exploration.max_depth}
              onChange={(e) =>
                onChange({
                  ...journey,
                  exploration: {
                    ...exploration,
                    max_depth: Number(e.target.value),
                  },
                })
              }
            />
          </label>
          <label>
            Total exploration and replay actions
            <input
              type="number"
              min="1"
              max="200"
              value={exploration.max_actions}
              onChange={(e) =>
                onChange({
                  ...journey,
                  exploration: {
                    ...exploration,
                    max_actions: Number(e.target.value),
                  },
                })
              }
            />
          </label>
        </div>
      )}
      <p className="muted">
        {journey.target.startsWith("fixture://")
          ? "Fixture discovery repeats the authored journey to reset the fixture. All replay actions count toward the budget."
          : "Website exploration follows one bounded path. It waits for approval before every proposed action and never resets or replays external effects automatically. Approval time counts toward the run deadline."}
      </p>
      <label className="check">
        <input
          type="checkbox"
          checked={journey.allow_local}
          onChange={(e) =>
            onChange({ ...journey, allow_local: e.target.checked })
          }
        />
        Authorize private and loopback network target access
      </label>
      <p className="muted">
        Latency delays intercepted requests; it does not emulate bandwidth.
        Viewport sizing does not emulate browser zoom. Reduced motion sets a
        browser preference and requires human evaluation of behavior.
      </p>
      <NetworkPermissions journey={journey} onChange={onChange} />
    </section>
  );
}
