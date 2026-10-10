// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import JourneyEditor from "./JourneyEditor";
import type { Journey } from "../../../packages/contracts";

afterEach(cleanup);

const journey: Journey = {
  schema_version: 1,
  name: "Apply",
  target: "fixture://accessible",
  profile: {
    keyboard_only: true,
    reduced_motion: false,
    viewport_width: 1280,
    viewport_height: 800,
    network_latency_ms: 0,
  },
  steps: [
    {
      id: "open",
      action: "navigate",
      value: "",
      optional: false,
      effect: false,
    },
  ],
  max_seconds: 60,
  tab_budget: 60,
  allow_local: false,
};
describe("Journey editing", () => {
  it("adds a named completion assertion through the keyboard", async () => {
    const change = vi.fn();
    render(<JourneyEditor journey={journey} onChange={change} />);
    const user = userEvent.setup();
    screen.getByRole("button", { name: "+ Add step" }).focus();
    await user.keyboard("{Enter}");
    expect(change.mock.calls[0][0].steps[1]).toMatchObject({
      action: "assert_visible",
      target: { role: "heading", name: "Confirmation" },
    });
  });
  it("exposes concrete profile settings with accessible labels", () => {
    render(<JourneyEditor journey={journey} onChange={vi.fn()} />);
    expect(screen.getByLabelText("Keyboard only")).toBeChecked();
    expect(screen.getByLabelText("Time budget (seconds)")).toHaveValue(60);
  });
});
