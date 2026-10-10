# Evidence-based differentiation

Research checked 2026-10-10 against publisher documentation. This is a feature/workflow
comparison, not an installed comparative benchmark or an assertion of unique invention.

| Tool                           | Documented capability already available elsewhere                                                         | AccessMaze's demonstrated combination                                                                                                                   |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| axe DevTools                   | Automated rules, guided testing and testing within user flows                                             | Uses axe itself; adds local task assertions, bounded keyboard attempts, recorded transitions, runtime-only bindings and conservative repair comparisons |
| Accessibility Insights for Web | FastPass combines automatic checks with assisted Tab-stop testing; assessment supports further evaluation | Stores authored execution paths, actual failure observations and repeatable candidate runs in a desktop workspace                                       |
| Pa11y                          | Actions can log in, enter fields, click and wait before a scan                                            | Makes interaction failure and task completion explicit; retains focus/state evidence and approves each external discovery action                        |

Sources: [Deque APIs and user flows](https://www.deque.com/accessible-development/api/),
[Deque guided testing](https://docs.deque.com/devtools-for-web/4/en/automated-igts/),
[Accessibility Insights FastPass](https://accessibilityinsights.io/docs/web/getstarted/fastpass/),
[Pa11y actions](https://github.com/pa11y/pa11y/blob/main/README.md#actions).

The distinction is the inspectable combination and its local evidence, not exclusive
ownership of keyboard checks, recording, workflows or automated rules. All analysis runs locally. General task understanding, exhaustive exploration, real AT integration and
independent release qualification remain outside current demonstrated capabilities.
