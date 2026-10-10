// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { request } from "./api";
import ProfileLibrary from "./ProfileLibrary";
import FailureReplay from "./FailureReplay";
import type { Journey, Run } from "../../../packages/contracts";
vi.mock("./api", () => ({ request: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("applies a stored profile and saves edited concrete conditions", async () => {
  const profile = {
    keyboard_only: false,
    reduced_motion: true,
    viewport_width: 800,
    viewport_height: 600,
    network_latency_ms: 100,
  };
  const saved = { id: "profile", name: "Pointer", profile, updated_at: "now" };
  vi.mocked(request).mockImplementation(async (method) =>
    method === "profile.save" ? saved : [saved],
  );
  const onApply = vi.fn();
  render(<ProfileLibrary profile={profile} onApply={onApply} />);
  const user = userEvent.setup();
  await screen.findByRole("option", { name: "Pointer" });
  await user.selectOptions(
    screen.getByLabelText("Saved capability profile"),
    "profile",
  );
  expect(onApply).toHaveBeenCalledWith(profile);
  await user.click(
    screen.getByRole("button", { name: "Update saved profile" }),
  );
  expect(request).toHaveBeenCalledWith("profile.save", {
    id: "profile",
    profile: { name: "Pointer", profile },
  });
});

it("keeps historical evidence separate and requires approval before real replay IPC", async () => {
  const journey = {
    name: "Replay",
    profile: {},
    steps: [
      { id: "open", action: "navigate" },
      {
        id: "failed",
        action: "activate",
        effect: true,
        target: { role: "button", name: "Continue" },
      },
    ],
  } as Journey;
  const original = {
    id: "original",
    project_id: "project",
    started_at: "then",
    status: "failed",
    journey,
    steps: [
      {
        id: "failed",
        action: "activate",
        status: "failed",
        state_id: "state",
        interaction: { tab_presses: 4 },
      },
    ],
    nodes: [{ id: "state", observation: { title: "Historical" } }],
    findings: [
      {
        id: "finding",
        step_id: "failed",
        rule: "keyboard-unreachable",
        actual: "Not reached",
        expected: "Reachable",
      },
    ],
  } as unknown as Run;
  const next = { ...original, id: "live", status: "preparing", findings: [] };
  vi.mocked(request).mockImplementation(async (method) =>
    method === "run.replay.prepare"
      ? { journey }
      : method === "run.start"
        ? { id: "live" }
        : next,
  );
  const onStarted = vi.fn();
  render(
    <FailureReplay
      original={original}
      current={original}
      onStarted={onStarted}
    />,
  );
  const user = userEvent.setup();
  expect(
    screen.getByText(/Reading this evidence does not execute/),
  ).toBeVisible();
  expect(request).not.toHaveBeenCalled();
  await user.click(
    screen.getByRole("button", { name: "Review browser re-execution" }),
  );
  const start = await screen.findByRole("button", {
    name: "Run approved replay",
  });
  expect(start).toBeDisabled();
  await user.click(screen.getByLabelText(/I authorize this target/));
  start.focus();
  await user.keyboard("{Enter}");
  expect(request).toHaveBeenCalledWith(
    "run.start",
    expect.objectContaining({
      replay_source_id: "original",
      replay_finding_id: "finding",
      authorized: true,
      allow_effects: true,
    }),
  );
  expect(onStarted).toHaveBeenCalledWith(next);
});

it("uses the finding's recorded step state instead of an unrelated graph screenshot", async () => {
  const { default: RunWorkspace } = await import("./RunWorkspace");
  vi.mocked(request).mockResolvedValue({ url: "data:image/png;base64," });
  const observation = {
    url: "fixture://broken",
    title: "Observed",
    headings: [],
    controls: [],
    online: true,
    reduced_motion: false,
  };
  const run = {
    id: "run",
    status: "failed",
    started_at: "then",
    journey: {
      name: "Task",
      profile: { keyboard_only: true },
      steps: [{ id: "open" }, { id: "failed" }],
    },
    steps: [
      { id: "open", status: "passed", state_id: "shared" },
      { id: "failed", status: "failed", state_id: "shared" },
    ],
    findings: [
      {
        id: "finding",
        step_id: "failed",
        rule: "keyboard-unreachable",
        screenshot: "failure.png",
        actual: "Unreachable",
        expected: "Reachable",
        reproduction: [],
      },
    ],
    nodes: [
      { id: "shared", first_step: "open", observation },
      { id: "other", first_step: "other", observation },
    ],
    edges: [],
    limitations: [],
    environment: {},
  } as unknown as Run;
  render(<RunWorkspace run={run} onControl={() => {}} />);
  expect(request).not.toHaveBeenCalled();
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "01 · open" }));
  expect(request).toHaveBeenCalledWith("evidence.read", {
    id: "run",
    name: "failure.png",
  });
});
