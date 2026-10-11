# Evidence-based differentiation

Research checked 2026-10-10 against publisher documentation. This is a feature/workflow
comparison, not an assertion of unique invention. The later controlled corpus below
is a separate measured comparison with narrower workloads.

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


The [paired corpus](../testing/comparative-corpus.md) executes sixteen actual browser
cases: eight broken/working pairs. AccessMaze executes authored tasks; axe and locked
Pa11y 10.0.0/HTML_CodeSniffer scan the initial page in fresh contexts. Local results
classified all sixteen tasks correctly and observed eight verified improvements.
Both initial-page scanners detected the unnamed-button calibration; the other task
failures arose after interaction. That absence is not a scanner false negative: the
workloads differ, and Pa11y itself supports actions. This establishes no general
speed/accuracy ranking. Accessibility Insights and real NVDA were not executed.
CI scanner failures remain inconclusive until corrected and actually rerun.
