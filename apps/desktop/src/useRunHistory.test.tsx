// @vitest-environment jsdom
import { expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useRunHistory } from "./useRunHistory";
import { request } from "./api";
import type { HistoryPage } from "../../../packages/contracts";
vi.mock("./api", () => ({ request: vi.fn() }));

it("ignores an older project's delayed history response", async () => {
  let resolveOld!: (page: HistoryPage) => void;
  vi.mocked(request).mockImplementation(async (_method, params) =>
    params?.project_id === "old"
      ? new Promise<HistoryPage>((resolve) => {
          resolveOld = resolve;
        })
      : { items: [], total: 2, offset: 0, next_offset: null },
  );
  const view = renderHook(useRunHistory);
  let old!: Promise<HistoryPage>;
  await act(async () => {
    old = view.result.current.loadHistory("old");
    await view.result.current.loadHistory("new");
  });
  await act(async () => {
    resolveOld({ items: [], total: 99, offset: 0, next_offset: null });
    await old;
  });
  expect(view.result.current.history.total).toBe(2);
  act(() => view.result.current.clearHistory());
  expect(view.result.current.history.total).toBe(0);
});
