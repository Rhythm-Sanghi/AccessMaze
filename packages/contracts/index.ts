export type Action =
  | "navigate"
  | "fill"
  | "activate"
  | "press"
  | "assert_visible"
  | "assert_value"
  | "assert_errors"
  | "assert_modal"
  | "offline"
  | "online"
  | "wait"
  | "audit";
export type Role =
  | "button"
  | "link"
  | "textbox"
  | "checkbox"
  | "combobox"
  | "heading"
  | "status"
  | "alert"
  | "dialog"
  | "radio"
  | "spinbutton";
export interface Step {
  id: string;
  action: Action;
  target?: { role: Role; name: string } | null;
  value: string;
  optional: boolean;
  effect: boolean;
}
export interface Journey {
  exploration?: { enabled: boolean; max_depth: number; max_actions: number };
  schema_version: 1;
  name: string;
  target: string;
  steps: Step[];
  profile: {
    keyboard_only: boolean;
    reduced_motion: boolean;
    viewport_width: number;
    viewport_height: number;
    network_latency_ms: number;
  };
  max_seconds: number;
  tab_budget: number;
  allow_local: boolean;
}
export interface Project {
  summary?: {
    last_analysis: string | null;
    confirmed_findings: number;
    incomplete_runs: number;
  };
  id: string;
  name: string;
  journey: Journey;
  archived: number;
  updated_at: string;
}
export interface Finding {
  id: string;
  step_id: string;
  rule: string;
  title: string;
  severity: string;
  verification: string;
  actual: unknown;
  expected: string;
  timestamp: string;
  reproduction: string[];
  remediation: string;
  screenshot?: string;
}
export interface Observation {
  url: string;
  title: string;
  controls: {
    tag: string;
    role: string | null;
    name: string;
    disabled: boolean;
    visible: boolean;
    invalid: string | null;
    populated: boolean;
    focused: boolean;
  }[];
  headings: string[];
  online: boolean;
  reduced_motion: boolean;
}
export interface Run {
  exploration?: {
    actions: {
      step_id: string;
      kind: string;
      action: string;
      status: string;
      target: { role: string; name: string } | null;
      timestamp: string;
    }[];
    discovered_states: number;
    pending_branches: { state_id: string; path: string[]; reason?: string }[];
    stop_reason: string;
  };
  id: string;
  project_id: string;
  status: string;
  started_at: string;
  finished_at?: string;
  error?: string;
  duration_seconds?: number;
  journey: Journey;
  steps: {
    id: string;
    action: Action;
    status: string;
    timestamp: string;
    index: number;
    state_id?: string;
  }[];
  findings: Finding[];
  nodes: { id: string; observation: Observation; first_step: string }[];
  edges: {
    source: string;
    target: string;
    step_id: string;
    status: string;
    cycle: boolean;
  }[];
  limitations: string[];
  environment: Record<string, string>;
}
export type Method =
  | "health"
  | "project.list"
  | "project.save"
  | "project.delete"
  | "project.archive"
  | "run.start"
  | "run.get"
  | "run.list"
  | "run.cancel"
  | "run.pause"
  | "run.resume"
  | "run.compare"
  | "report.export"
  | "evidence.read"
  | "storage.backup"
  | "storage.prune";
