import { useCallback, useEffect, useRef, useState } from "react";
import type { Journey, Project, Run } from "../../../packages/contracts";
import { desktopAvailable, download, request } from "./api";
import JourneyEditor from "./JourneyEditor";
import Projects from "./Projects";
import RunHistory from "./RunHistory";
import Reports from "./Reports";
import Settings from "./Settings";
import RunWorkspace, { activeRun } from "./RunWorkspace";

type Page = "projects" | "journey" | "analysis" | "reports" | "settings";
const pages: { id: Page; label: string; mark: string }[] = [
  { id: "projects", label: "Projects", mark: "01" },
  { id: "journey", label: "Journey builder", mark: "02" },
  { id: "analysis", label: "Analysis", mark: "03" },
  { id: "reports", label: "Reports", mark: "04" },
  { id: "settings", label: "Settings", mark: "05" },
];
export default function App() {
  const [page, setPage] = useState<Page>("projects");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [journey, setJourney] = useState<Journey | null>(null);
  const [templates, setTemplates] = useState<Record<string, Journey>>({});
  const [name, setName] = useState("Untitled investigation");
  const [run, setRun] = useState<Run | null>(null);
  const [history, setHistory] = useState<Run[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [effects, setEffects] = useState(false);
  const [confirmation, setConfirmation] = useState<Project | null>(null);
  const [theme, setTheme] = useState(
    localStorage.getItem("accessmaze-theme") ?? "light",
  );
  const fileInput = useRef<HTMLInputElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const deleteDialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("accessmaze-theme", theme);
  }, [theme]);
  useEffect(() => {
    heading.current?.focus();
  }, [page]);
  useEffect(() => {
    if (confirmation) deleteDialog.current?.showModal();
    else deleteDialog.current?.close();
  }, [confirmation]);
  const refresh = useCallback(async () => {
    setProjects(await request<Project[]>("project.list"));
  }, []);
  useEffect(() => {
    if (ready && page === "projects")
      void refresh().catch((e) => setError(String(e)));
  }, [page, ready, refresh]);
  const initialize = useCallback(async () => {
    try {
      const health = await request<{ templates: Record<string, Journey> }>(
        "health",
      );
      setTemplates(health.templates);
      await refresh();
      setReady(true);
      setError("");
    } catch (e) {
      setError(String(e));
      setReady(false);
    }
  }, [refresh]);
  useEffect(() => {
    if (desktopAvailable) void initialize();
  }, [initialize]);
  useEffect(() => {
    if (!activeRun(run)) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const current = await request<Run>("run.get", { id: run!.id });
        if (disposed) return;
        setRun(current);
        if (activeRun(current)) timer = setTimeout(poll, 600);
        else {
          setHistory(
            await request<Run[]>("run.list", {
              project_id: current.project_id,
            }),
          );
          setMessage(`Analysis ${current.status.replaceAll("_", " ")}`);
        }
      } catch (e) {
        if (!disposed) {
          setError(String(e));
          timer = setTimeout(poll, 2000);
        }
      }
    }
    timer = setTimeout(poll, 300);
    return () => {
      disposed = true;
      clearTimeout(timer);
    };
  }, [run?.id, run?.status]); // eslint-disable-line react-hooks/exhaustive-deps
  async function perform(task: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await task();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  function choose(project: Project) {
    if (activeRun(run)) {
      setError("Stop the active analysis before switching projects.");
      return;
    }
    setSelected(project);
    setJourney(structuredClone(project.journey));
    setName(project.name);
    setAuthorized(false);
    setEffects(false);
    setRun(null);
    setPage("journey");
    void perform(async () =>
      setHistory(await request<Run[]>("run.list", { project_id: project.id })),
    );
  }
  function create(kind: string) {
    setSelected(null);
    const next = structuredClone(
      templates[kind === "website" ? "accessible" : kind],
    );
    if (kind === "website") {
      next.name = "Website journey";
      next.target = "https://example.org";
      next.steps = [
        next.steps[0],
        {
          id: "complete",
          action: "assert_visible",
          target: { role: "heading", name: "Example Domain" },
          value: "",
          optional: false,
          effect: false,
        },
      ];
    }
    setJourney(next);
    setName(
      kind === "website" ? "Website investigation" : `Scholarship · ${kind}`,
    );
    setRun(null);
    setHistory([]);
    setAuthorized(false);
    setEffects(false);
    setPage("journey");
  }
  async function save() {
    if (activeRun(run))
      throw new Error("Stop the analysis before editing its project.");
    if (!journey) return;
    const saved = await request<Project>("project.save", {
      id: selected?.id,
      project: { name, journey },
    });
    setSelected(saved);
    setJourney(saved.journey);
    await refresh();
    setMessage("Project and journey saved");
    return saved;
  }
  async function start() {
    const saved = await save();
    if (!saved) return;
    const started = await request<{ id: string }>("run.start", {
      project_id: saved.id,
      authorized,
      allow_effects: effects,
    });
    setRun(await request<Run>("run.get", { id: started.id }));
    setPage("analysis");
  }
  async function control(action: "cancel" | "pause" | "resume") {
    if (run) await request(`run.${action}`, { id: run.id });
    setMessage(
      action === "pause"
        ? "Pause requested; current step will finish"
        : `${action} requested`,
    );
  }
  async function exportReport(format: string) {
    if (!run) return;
    const report = await request<{ content: string; mime: string }>(
      "report.export",
      { id: run.id, format },
    );
    download(
      `accessmaze-${run.id.slice(0, 8)}.${format}`,
      report.content,
      report.mime,
    );
    setMessage(`${format.toUpperCase()} report exported`);
  }
  const dirty =
    journey &&
    (JSON.stringify(journey) !== JSON.stringify(selected?.journey) ||
      name !== selected?.name);
  const hasEffects =
    journey?.steps.some((s) => s.effect) || journey?.exploration?.enabled;
  const changePage = (next: Page) => {
    setPage(next);
  };
  return (
    <div className="app">
      <a href="#main" className="skip-link">
        Skip to workspace
      </a>
      <aside className="rail">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            A<span>↳</span>
          </span>
          <div>
            AccessMaze<small>WORKFLOW INVESTIGATION</small>
          </div>
        </div>
        <nav aria-label="Main navigation">
          {pages.map((p) => (
            <button
              key={p.id}
              aria-current={page === p.id ? "page" : undefined}
              onClick={() => changePage(p.id)}
            >
              <span className="mono">{p.mark}</span>
              {p.label}
            </button>
          ))}
        </nav>
        <div className="rail-foot">
          <span className="mono">LOCAL / 0.1.0</span>
          <p>{ready ? "Worker connected" : "Worker unavailable"}</p>
          <small>Evidence before assumptions.</small>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>{selected?.name ?? "Local workspace"}</span>
          {activeRun(run) && (
            <button
              className="danger"
              onClick={() => void perform(() => control("cancel"))}
            >
              Emergency stop
            </button>
          )}
          <span className="mono">
            {dirty ? "UNSAVED CHANGES" : "ACCESSMAZE / DEVELOPMENT BUILD"}
          </span>
        </header>
        <main id="main" tabIndex={-1}>
          <div className="page-heading">
            <div>
              <p className="eyebrow mono">
                INVESTIGATION / {pages.find((p) => p.id === page)?.mark}
              </p>
              <h1 ref={heading} tabIndex={-1}>
                {pages.find((p) => p.id === page)?.label}
              </h1>
            </div>
            <span className="mono muted">
              No cloud services · Local storage
            </span>
          </div>
          <div role="status" aria-live="polite" className="announcement">
            {busy ? "Working…" : message}
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}
          {!desktopAvailable && (
            <div className="notice">
              <strong>Desktop host required</strong>
              <p>
                This browser preview displays the interface. Start{" "}
                <code>npm run desktop</code> to connect the local engine and run
                real analyses.
              </p>
            </div>
          )}
          {desktopAvailable && !ready && (
            <div className="notice">
              <p>
                The engine is unavailable. Install dependencies using the
                development guide, then reconnect.
              </p>
              <button onClick={() => void initialize()}>
                Reconnect worker
              </button>
            </div>
          )}
          {page === "projects" && (
            <Projects
              projects={projects}
              disabled={!ready || busy || activeRun(run)}
              onChoose={choose}
              onCreate={create}
              onDelete={setConfirmation}
              onArchive={(p) =>
                void perform(async () => {
                  await request("project.archive", {
                    id: p.id,
                    archived: !p.archived,
                  });
                  await refresh();
                })
              }
            />
          )}
          {page === "journey" &&
            (journey ? (
              <>
                <div className="editor-toolbar">
                  <label>
                    Project name
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </label>
                  <div className="toolbar">
                    <button
                      disabled={busy || !ready}
                      onClick={() =>
                        void perform(async () => {
                          await save();
                        })
                      }
                    >
                      Save project
                    </button>
                    <button
                      onClick={() =>
                        download(
                          "journey.json",
                          JSON.stringify(journey, null, 2),
                          "application/json",
                        )
                      }
                    >
                      Export journey
                    </button>
                    <button
                      disabled={activeRun(run)}
                      onClick={() => fileInput.current?.click()}
                    >
                      Import journey
                    </button>
                  </div>
                  <input
                    ref={fileInput}
                    type="file"
                    accept="application/json,.json"
                    hidden
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      void perform(async () => {
                        if (file.size > 1024 * 1024)
                          throw new Error(
                            "Journey files must be smaller than 1 MiB",
                          );
                        const imported: unknown = JSON.parse(await file.text());
                        const saved = await request<Project>("project.save", {
                          project: { name, journey: imported },
                        });
                        choose(saved);
                        await refresh();
                        setMessage(
                          "Imported and validated journey as a new project",
                        );
                      });
                      e.target.value = "";
                    }}
                  />
                </div>
                <JourneyEditor journey={journey} onChange={setJourney} />
                <div className="run-gate">
                  <h2>Run authorization</h2>
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={authorized}
                      onChange={(e) => setAuthorized(e.target.checked)}
                    />
                    I am authorized to test this target and will use synthetic
                    data.
                  </label>
                  {hasEffects && (
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={effects}
                        onChange={(e) => setEffects(e.target.checked)}
                      />
                      I authorize this journey’s state-changing actions,
                      including potential form submissions.
                    </label>
                  )}
                  <p className="muted">
                    Review all actions before running. Browser contexts are
                    isolated from your personal profile. Pause takes effect
                    between steps; emergency stop cancels an active action.
                  </p>
                  <button
                    className="primary"
                    disabled={
                      busy ||
                      !ready ||
                      !authorized ||
                      (!!hasEffects && !effects) ||
                      activeRun(run)
                    }
                    onClick={() => void perform(start)}
                  >
                    Run analysis →
                  </button>
                </div>
              </>
            ) : (
              <div className="empty">
                <h2>No journey selected</h2>
                <p>
                  Open a saved project or choose a local fixture from Projects.
                </p>
                <button onClick={() => setPage("projects")}>
                  Go to projects
                </button>
              </div>
            ))}
          {page === "analysis" &&
            (run ? (
              <RunWorkspace
                run={run}
                onControl={(action) => void perform(() => control(action))}
              />
            ) : (
              <div className="empty">
                <h2>No analysis selected</h2>
                <p>Run the configured journey or open a previous run below.</p>
              </div>
            ))}
          {(page === "analysis" || page === "reports") && (
            <RunHistory
              history={history}
              run={run}
              onSelect={(r) => {
                setRun(r);
                setPage("analysis");
              }}
            />
          )}
          {page === "reports" && (
            <Reports
              run={run}
              busy={busy}
              onExport={(format) => void perform(() => exportReport(format))}
            />
          )}
          {page === "settings" && (
            <Settings
              theme={theme}
              onTheme={setTheme}
              onPrune={async () => {
                await refresh();
                if (selected) {
                  const remaining = await request<Run[]>("run.list", {
                    project_id: selected.id,
                  });
                  setHistory(remaining);
                  if (run && !remaining.some((r) => r.id === run.id))
                    setRun(null);
                }
              }}
            />
          )}
        </main>
        <footer>
          <span>AccessMaze / Local workflow investigation</span>
          <span className="mono">AUTOMATION ≠ HUMAN EVALUATION</span>
        </footer>
      </div>
      <dialog
        ref={deleteDialog}
        aria-labelledby="delete-title"
        onCancel={() => setConfirmation(null)}
      >
        <h2 id="delete-title">Delete {confirmation?.name}?</h2>
        <p>
          This permanently removes the project, its runs and evidence files.
        </p>
        <div className="toolbar">
          <button autoFocus onClick={() => setConfirmation(null)}>
            Keep project
          </button>
          <button
            className="danger"
            onClick={() =>
              void perform(async () => {
                await request("project.delete", { id: confirmation!.id });
                if (selected?.id === confirmation!.id) {
                  setSelected(null);
                  setJourney(null);
                  setRun(null);
                  setHistory([]);
                }
                setConfirmation(null);
                await refresh();
                setMessage("Project deleted");
              })
            }
          >
            Delete permanently
          </button>
        </div>
      </dialog>
    </div>
  );
}
