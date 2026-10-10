// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import RunHistory from "./RunHistory";
import { request } from "./api";
import type { Run, RunComparison } from "../../../packages/contracts";

vi.mock("./api", () => ({ request: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("compares through keyboard controls and hides evidence when the selected run changes", async () => {
  const journey = { name: "Application" } as Run["journey"];
  const baseline = {
    id: "baseline",
    journey,
    status: "failed",
    started_at: "2026-10-10T00:00:00Z",
    findings: [],
    steps: [],
    nodes: [],
    edges: [],
  } as unknown as Run;
  const candidate = {
    ...baseline,
    id: "candidate",
    status: "completed_with_limitations",
  };
  const outcome = {
    status: "completed",
    reason: "All required assertions passed.",
    assertions: [],
    blocked_step_id: null,
    limitation: "Bounded task only.",
  } as const;
  const comparison: RunComparison = {
    previous_id: baseline.id,
    current_id: candidate.id,
    comparable: true,
    previous_outcome: { ...outcome, assertions: [], status: "blocked" },
    current_outcome: { ...outcome, assertions: [] },
    findings: [
      {
        finding_id: "barrier",
        step_id: "continue",
        rule: "keyboard-unreachable",
        verdict: "passed-retest",
      },
    ],
    added_findings: [],
    steps: [
      {
        step_id: "continue",
        previous_status: "failed",
        current_status: "passed",
      },
    ],
    first_divergent_step: {
      step_id: "continue",
      previous_status: "failed",
      current_status: "passed",
    },
    changed_conditions: [],
    environment_changes: [],
    warnings: [],
    matching_rule: "Stable step identity",
    limitation: "Bounded task only.",
  };
  vi.mocked(request).mockResolvedValue(comparison);
  const onSelect = vi.fn();
  const props = { history: [baseline, candidate], run: candidate, onSelect };
  const view = render(<RunHistory {...props} />);
  const user = userEvent.setup();
  await user.selectOptions(screen.getByLabelText("Previous run"), "baseline");
  screen.getByRole("button", { name: "Compare findings" }).focus();
  await user.keyboard("{Enter}");
  expect(await screen.findByText("passed-retest")).toBeVisible();
  expect(
    screen.getByText("Baseline: blocked · Candidate: completed"),
  ).toBeVisible();
  expect(
    screen.getByText("First divergent execution step: continue"),
  ).toBeVisible();
  expect(request).toHaveBeenCalledWith("run.compare", {
    previous_id: "baseline",
    current_id: "candidate",
  });
  await user.click(
    screen.getByRole("button", { name: "Inspect baseline run" }),
  );
  expect(onSelect).toHaveBeenCalledWith(baseline);
  view.rerender(<RunHistory {...props} run={baseline} />);
  expect(screen.queryByText("passed-retest")).not.toBeInTheDocument();
});
