// @vitest-environment jsdom
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import HumanReviewPanel from "./HumanReviewPanel";
import { request } from "./api";
import type { Run } from "../../../packages/contracts";

vi.mock("./api", () => ({ request: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("prepares an unverified NVDA plan without claiming or running a human evaluation", async () => {
  vi.mocked(request).mockResolvedValue([]);
  render(
    <HumanReviewPanel
      run={
        {
          id: "run",
          journey: { steps: [{ id: "open" }] },
          findings: [],
        } as unknown as Run
      }
    />,
  );
  const user = userEvent.setup();
  await user.click(screen.getByText("Prepare or record a manual check"));
  await user.click(
    screen.getByRole("button", { name: "Prepare NVDA checklist" }),
  );
  expect(screen.getByLabelText("Human verification status")).toHaveValue(
    "planned",
  );
  expect(screen.getByLabelText(/I performed the recorded/)).not.toBeChecked();
  expect(screen.getByLabelText(/Actual behavior/)).toHaveValue("");
  await user.click(
    screen.getByRole("button", { name: "Save human observation" }),
  );
  await waitFor(() =>
    expect(request).toHaveBeenCalledWith(
      "review.save",
      expect.objectContaining({
        review: expect.objectContaining({
          status: "planned",
          performed_by_human: false,
          actual: "",
          run_id: "run",
        }),
      }),
    ),
  );
  expect(request).not.toHaveBeenCalledWith("run.start", expect.anything());
  expect(
    await screen.findByText(
      "Human observation saved separately from automated findings.",
    ),
  ).toBeVisible();
});
