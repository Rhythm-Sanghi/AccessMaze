import { invoke } from "@tauri-apps/api/core";
import type { Method } from "../../../packages/contracts";
export const desktopAvailable = "__TAURI_INTERNALS__" in window;
export async function request<T>(
  method: Method,
  params: Record<string, unknown> = {},
): Promise<T> {
  if (!desktopAvailable)
    throw new Error(
      "Analysis requires the desktop host. Start with npm run desktop.",
    );
  return invoke<T>("worker_request", { method, params });
}
export function download(name: string, content: string, mime: string) {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
