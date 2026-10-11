// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import App from "./App";
import { request } from "./api";
import type { Journey, Run } from "../../../packages/contracts";

vi.mock("./api", () => ({
  desktopAvailable: true,
  request: vi.fn(),
  download: vi.fn(),
}));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("keeps exactly one replay and human panel while inspecting different saved runs", async () => {
  const journey = {
    schema_version: 1,
    name: "Run switching",
    target: "fixture://broken",
    profile: {
      keyboard_only: true,
      reduced_motion: false,
      viewport_width: 1280,
      viewport_height: 800,
      network_latency_ms: 0,
    },
    steps: [
      { id: "open", action: "navigate" },
      {
        id: "date",
        action: "activate",
        effect: true,
        target: { role: "button", name: "Choose date" },
      },
    ],
    max_seconds: 60,
    tab_budget: 8,
    allow_local: false,
  } as Journey;
  const project = {
    id: "project",
    name: "Saved investigation",
    journey,
    archived: 0,
    updated_at: "2026-10-11",
  };
  const runs = ["first", "second"].map(
    (id) =>
      ({
        id,
        project_id: project.id,
        journey,
        started_at: "2026-10-11T00:00:00Z",
        status: "failed",
        steps: [],
        nodes: [],
        edges: [],
        environment: {},
        limitations: [],
        findings: [
          {
            id: `${id}-finding`,
            step_id: "date",
            rule: "keyboard-unreachable",
            actual: "Bounded attempt failed",
            expected: "Keyboard reach",
            severity: "serious",
            verification: "confirmed-automated",
            title: "Date unreachable",
            reproduction: ["open", "date"],
            timestamp: "2026-10-11T00:00:00Z",
            remediation: "Review the failed keyboard action",
          },
        ],
      }) as Run,
  );
  vi.mocked(request).mockImplementation(async (method, params) => {
    if (method === "health") return { templates: { broken: journey } };
    if (method === "project.list") return [project];
    if (method === "profile.list" || method === "review.list") return [];
    if (method === "run.history")
      return {
        items: runs.map((r) => ({ ...r, finding_count: 1 })),
        total: 2,
        offset: 0,
        next_offset: null,
      };
    if (method === "run.get") return runs.find((r) => r.id === params?.id);
    throw new Error(`Unexpected component-test request: ${method}`);
  });
  // jsdom lacks dialog methods; native dialog behavior is checked separately.
  HTMLDialogElement.prototype.close = vi.fn();
  HTMLDialogElement.prototype.showModal = vi.fn();
  render(<App />);
  const user = userEvent.setup();
  await user.click(
    await screen.findByRole("button", {
      name: "Saved investigation",
    }),
  );
  await user.click(screen.getByRole("button", { name: /03\s*Analysis/ }));
  await screen.findAllByRole("button", { name: "Inspect run" });
  for (const index of [0, 1, 0, 1]) {
    await user.click(
      screen.getAllByRole("button", { name: "Inspect run" })[index],
    );
    await waitFor(() =>
      expect(
        screen.getByText(new RegExp(`Historical run ${runs[index].id}`)),
      ).toBeVisible(),
    );
    expect(
      screen.getAllByRole("region", { name: "Failure reproduction" }),
    ).toHaveLength(1);
    expect(
      screen.getAllByRole("region", { name: "Human investigation" }),
    ).toHaveLength(1);
    expect(
      screen.getByRole("button", { name: "Review browser re-execution" }),
    ).toBeEnabled();
  }
});
