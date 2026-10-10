export type Action =
  | "navigate"
  | "fill"
  | "activate"
  | "press"
  | "assert_visible"
  | "assert_value"
  | "assert_errors"
  | "assert_modal"
  | "assert_focus"
  | "offline"
  | "online"
  | "wait"
  | "audit"
  | "upload";
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
  target?: { role: Role; name: string; by?: "role" | "label" } | null;
  value_from?: string | null;
  file_label?: string;
  value: string;
  optional: boolean;
  effect: boolean;
}
export interface Journey {
  privacy?: { capture_page_text: boolean };
  network?: { navigation_origins: string[]; resource_origins: string[] };
  exploration?: {
    enabled: boolean;
    recover_navigation?: boolean;
    max_depth: number;
    max_actions: number;
  };
  schema_version: 1;
  name: string;
  target: string;
  steps: Step[];
  profile: {
    action_timeout_ms?: number;
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
  text_withheld?: boolean;
  ax_tree?: {
    source: string;
    max_depth?: number;
    max_nodes?: number;
    nodes: { role: string; name: string; focused: boolean }[];
  };
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
  outcome?: TaskOutcome;
  approval?: {
    id: string;
    state_id: string;
    choices: { id: string; role: string; name: string }[];
  };
  input_signature?: string | null;
  exploration?: {
    mode?: "approved-walk" | "approved-branches";
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
export interface TaskOutcome {
  status: "completed" | "blocked" | "incomplete" | "cancelled" | "inconclusive";
  reason: string;
  assertions: { step_id: string; status: string }[];
  blocked_step_id: string | null;
  limitation: string;
}
export interface RunComparison {
  previous_id: string;
  current_id: string;
  comparable: boolean;
  findings: {
    finding_id: string;
    rule: string;
    step_id: string;
    verdict: string;
  }[];
  added_findings: { finding_id: string; step_id: string; rule: string }[];
  steps: {
    step_id: string;
    previous_status: string;
    current_status: string;
    previous_state_id?: string | null;
    current_state_id?: string | null;
  }[];
  first_divergent_step: {
    step_id: string;
    previous_status: string;
    current_status: string;
  } | null;
  previous_outcome: TaskOutcome;
  current_outcome: TaskOutcome;
  changed_conditions: string[];
  environment_changes: string[];
  warnings: string[];
  matching_rule: string;
  limitation: string;
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
  | "run.approve"
  | "run.compare"
  | "report.export"
  | "evidence.read"
  | "storage.backup"
  | "storage.prune"
  | "recorder.start"
  | "recorder.get"
  | "recorder.stop"
  | "recorder.assert";
export interface Recording {
  id: string;
  status: "preparing" | "recording" | "stopping" | "stopped";
  origin: string;
  steps: Step[];
  warnings: string[];
}
