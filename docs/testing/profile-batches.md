# Bounded profile batches

Profiles now retain a version-1 condition snapshot. Existing unversioned profiles
load with version-1 defaults. The desktop library still edits each concrete condition.
Layout zoom changes CSS viewport/device scale; it is not browser chrome zoom,
text-only zoom, OS magnification or a simulation of human assistive technology.

For repeatable authored-path batches, export a journey and prepare a JSON array of
1–8 objects containing `name` and `profile`, for example:

```json
[
  {"name":"Keyboard", "profile":{"keyboard_only":true}},
  {"name":"Pointer", "profile":{"keyboard_only":false,"reduced_motion":true}}
]
```

From the development checkout:

```powershell
uv run --project engine python scripts/profile_batch.py --journey journey.json --profiles profiles.json --output dist/My-profile-batch --seconds 600 --authorized --allow-effects
```

The output directory must be new. Every run uses a fresh Chromium context and its
own persisted evidence. Concurrency is exactly one; at most eight profiles and
1,800 execution seconds are accepted. The total budget can shorten a run's recorded
time bound. Browser closing and persistence add overhead to this execution budget.
Ctrl+C stops further profiles and preserves partial results; there is no automatic
retry. A finished batch can contain failed/inconclusive task runs: inspect each outcome.

`--authorized` confirms target authorization. `--allow-effects` explicitly authorizes
the reviewed authored action sequence for **each** profile, including repeated writes.
Fresh contexts do not reset server state. Use isolated synthetic accounts/data, and
do not batch consequential production workflows. Discovery is refused because each
external exploratory action needs its own contemporaneous approval.

Supply run-only values/files with `--inputs private-inputs.json` when needed, using
the same `values`/`files` structure as worker run inputs. That file is not copied into
results; secure and remove your own input file afterwards. Do not commit it. Stored
literal journey values remain plaintext in project configuration, so use runtime
bindings for credentials. Batch output uses private filesystem permissions.

`batch.json` records profile snapshots, browser/tool environment, outcomes and
descriptive comparisons. Different profiles are different conditions; their comparison
does not verify a repair or prove that one human capability is superior to another.
