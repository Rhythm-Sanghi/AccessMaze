import { useCallback, useRef, useState } from "react";
import type { HistoryPage } from "../../../packages/contracts";
import { request } from "./api";

const emptyPage = (): HistoryPage => ({
  items: [],
  total: 0,
  offset: 0,
  next_offset: null,
});

export function useRunHistory() {
  const [history, setHistory] = useState<HistoryPage>(emptyPage);
  const generation = useRef(0);
  const clearHistory = useCallback(() => {
    generation.current++;
    setHistory(emptyPage());
  }, []);
  const loadHistory = useCallback(async (projectId: string, offset = 0) => {
    const current = ++generation.current;
    const page = await request<HistoryPage>("run.history", {
      project_id: projectId,
      limit: 50,
      offset,
    });
    if (current === generation.current) setHistory(page);
    return page;
  }, []);
  return { history, loadHistory, clearHistory };
}
