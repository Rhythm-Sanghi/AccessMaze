import type { Run } from "../../../packages/contracts";

export default function TaskReachability({ run }: { run: Run }) {
  const evidence = run.reachability;
  if (!evidence) return null;
  return (
    <section aria-label="Observed task reachability">
      <h3>Observed task reachability: {evidence.status}</h3>
      <p>
        {evidence.reachable_observed_states} reachable states in the recorded
        graph / {evidence.observed_states} observed states.
      </p>
      <ul>
        {evidence.objectives.map((objective) => (
          <li key={objective.step_id}>
            {objective.step_id}: {objective.status}
            {objective.shortest_observed_state_path?.length
              ? ` · state path: ${objective.shortest_observed_state_path.join(" → ")}`
              : ""}
          </li>
        ))}
      </ul>
      {evidence.blocking_attempts.length > 0 && (
        <details>
          <summary>Blocking attempts and prerequisites</summary>
          <ul>
            {evidence.blocking_attempts.map((attempt) => (
              <li key={attempt.step_id}>
                {attempt.step_id} · prerequisites:{" "}
                {attempt.chronological_prerequisites.join(" → ") ||
                  "None recorded"}
              </li>
            ))}
          </ul>
        </details>
      )}
      <p>
        {evidence.unexplored_frontier.length} recorded frontier entries remain
        untested.
      </p>
      <p className="muted">{evidence.limitation}</p>
    </section>
  );
}
