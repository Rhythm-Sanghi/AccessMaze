import csv
import html
import io
import json

from accessmaze.outcomes import task_outcome


def export_report(run, format, screenshots=None):
    run = {**run, "outcome": task_outcome(run)}
    if format == "json":
        return json.dumps(run, ensure_ascii=False, indent=2), "application/json"
    if format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(
            ["run_id", "status", "step", "rule", "severity", "verification", "actual", "expected"]
        )
        for finding in run["findings"]:
            cells = [
                run["id"],
                run["status"],
                finding["step_id"],
                finding["rule"],
                finding["severity"],
                finding["verification"],
                str(finding["actual"]),
                finding["expected"],
            ]
            # Spreadsheet applications can execute formula-prefixed untrusted website text.
            writer.writerow(
                [
                    "'" + cell if cell.startswith(("=", "+", "-", "@", "\t", "\r")) else cell
                    for cell in cells
                ]
            )
        return output.getvalue(), "text/csv"
    if format == "html":
        esc = lambda value: html.escape(str(value))  # noqa: E731
        screenshots = screenshots or {}

        def image(finding):
            uri = screenshots.get(finding.get("screenshot"), "")
            if not uri.startswith("data:image/png;base64,"):
                return ""
            return f'<figure><img src="{esc(uri)}" alt="Masked fixture failure state"></figure>'

        findings = "".join(
            f"<article><h2>{esc(f['title'])}</h2><dl>"
            f"<dt>Step / rule</dt><dd>{esc(f['step_id'])} / {esc(f['rule'])}</dd>"
            f"<dt>Verification</dt><dd>{esc(f['verification'])}</dd>"
            f"<dt>Actual</dt><dd>{esc(f['actual'])}</dd>"
            f"<dt>Expected</dt><dd>{esc(f['expected'])}</dd>"
            f"<dt>Reproduce</dt><dd>{esc(' → '.join(f['reproduction']))}</dd></dl>"
            f"{image(f)}</article>"
            for f in run["findings"]
        )
        steps = "".join(
            f"<tr><td>{esc(s['id'])}</td><td>{esc(s['action'])}</td>"
            f"<td>{esc(s['status'])}</td></tr>"
            for s in run["steps"]
        )
        limitations = "".join(f"<li>{esc(item)}</li>" for item in run["limitations"])
        return (
            f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy"
content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
<title>AccessMaze report</title><style>body{{font:16px system-ui;max-width:960px;margin:40px auto;
line-height:1.6;padding:20px;color:#222}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #aaa;text-align:left;padding:8px}}dt{{font-weight:bold}}
article{{border-top:1px solid #aaa;margin:24px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
img{{max-width:100%}}</style>
<h1>{esc(run["journey"]["name"])}</h1><p>Run {esc(run["id"])} · {esc(run["status"])}</p>
<h2>Task outcome: {esc(run["outcome"]["status"])}</h2>
<p>{esc(run["outcome"]["reason"])}</p><p>{esc(run["outcome"]["limitation"])}</p>
<pre>{esc(json.dumps(run["outcome"]["assertions"], indent=2))}</pre>
<p>Target: {esc(run["journey"]["target"])} · Started: {esc(run["started_at"])}</p>
<h2>Execution</h2><table><tr><th>Step</th><th>Action</th><th>Status</th></tr>{steps}</table>
<h2>Findings ({len(run["findings"])})</h2>{findings}<h2>Coverage limitations</h2><ul>{
                limitations
            }</ul>
<h2>Human observations — separate from automation</h2>
<p>These are tester-entered records. Planned checks do not establish verification.</p>
<pre>{esc(json.dumps(run.get("human_reviews", []), indent=2))}</pre>
<h2>Configuration and provenance</h2><pre>{
                esc(
                    json.dumps(
                        {"journey": run["journey"], "environment": run["environment"]}, indent=2
                    )
                )
            }</pre><h2>Observed states, transitions and incomplete exploration</h2>
<pre>{
                esc(
                    json.dumps(
                        {
                            "nodes": run.get("nodes", []),
                            "edges": run.get("edges", []),
                            "exploration": run.get("exploration"),
                            "reachability": run.get("reachability"),
                        },
                        indent=2,
                    )
                )
            }</pre></html>""",
            "text/html",
        )
    raise ValueError("Supported report formats: json, html, csv")
