// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import RecorderPanel from "./RecorderPanel";
import RunWorkspace from "./RunWorkspace";
import type { Run } from "../../../packages/contracts";

afterEach(cleanup);
describe("Explicit browser approvals", () => {
  it("requires separate target and manual session approvals before opening a recorder", async () => {
    render(
      <RecorderPanel
        scope="website"
        disabled={false}
        onActive={vi.fn()}
        onStart={vi.fn()}
        onApply={vi.fn()}
      />,
    );
    const open = screen.getByRole("button", { name: "Open recording browser" });
    expect(open).toBeDisabled();
    const user = userEvent.setup();
    await user.click(screen.getByLabelText(/authorized to record/));
    expect(open).toBeDisabled();
    await user.click(
      screen.getByLabelText(/authorize interactions and requests/),
    );
    expect(open).toBeEnabled();
  });
  it("does not approve a proposed website action until its specific button is activated", async () => {
    const approve = vi.fn();
    const run: Run = {
      id: "run",
      project_id: "project",
      started_at: new Date().toISOString(),
      status: "awaiting_approval",
      environment: {},
      limitations: [],
      steps: [],
      findings: [],
      nodes: [],
      edges: [],
      journey: {
        schema_version: 1,
        name: "Website",
        target: "https://example.org",
        steps: [],
        max_seconds: 60,
        tab_budget: 60,
        allow_local: false,
        profile: {
          keyboard_only: true,
          reduced_motion: false,
          viewport_width: 1280,
          viewport_height: 800,
          network_latency_ms: 0,
        },
      },
      approval: {
        id: "proposal",
        state_id: "state",
        choices: [{ id: "choice", role: "button", name: "Submit test" }],
      },
    };
    render(<RunWorkspace run={run} onControl={vi.fn()} onApprove={approve} />);
    expect(approve).not.toHaveBeenCalled();
    const action = screen.getByRole("button", {
      name: "Approve button: Submit test",
    });
    action.focus();
    await userEvent.setup().keyboard("{Enter}");
    expect(approve).toHaveBeenCalledExactlyOnceWith("proposal", "choice");
  });
});
