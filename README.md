# OpenCode Go × Artificial Analysis

Static one-page comparison of model cost per intelligence point on OpenCode Go pricing.

## Data

| File | Content | Origin |
|---|---|---|
| `data/aa-models.json` | Intelligence Index, cost per task, tokens/s | Artificial Analysis (free API, attribution required) |
| `data/go-limits.json` | Go monthly dollar allowance per model | https://opencode.ai/console/go.md |
| `data/merged.json` | Joined rows + `snapshot_date` | `python build.py` |

`snapshot_date` = fetch date of the two source files (file mtime), not the build date. It is written into `merged.json` and shown in the page header.

This page is a snapshot, not a live feed. For the current numbers use the live sources:
- https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index
- https://opencode.ai/console/go

## Refresh

Automated by `.github/workflows/refresh.yml`: daily at 03:23 UTC, plus manual `workflow_dispatch`.

1. `scripts/fetch_aa.py` — Artificial Analysis Free API, needs `AA_API_KEY` (repo secret).
2. `scripts/fetch_go.py` — parses `https://opencode.ai/console/go.md`; fails if the table shrinks or `GLM-5.3` disappears.
3. `python build.py` — rewrites `data/merged.json`.
4. Commits `data/` only when something changed.

Both fetchers write `data/fetched_at.json`; `snapshot_date` is the oldest of those dates, so a half-refreshed snapshot never claims to be newer than it is.

Manual run: `python scripts/fetch_aa.py`, `python scripts/fetch_go.py`, `python build.py`, then serve the folder (`python -m http.server`) and open `index.html`.

Hosting: Settings → Pages → Deploy from branch → `main` / root.

## Method

`$ / point = cost per task ÷ Intelligence Index`.

- Go $ / task = AA $ / task × plan price ÷ model monthly allowance (e.g. `1.5749 × 10 ÷ 500 = 0.0315`)
- Monthly tasks = model monthly allowance ÷ AA $ / task (= plan price ÷ Go $ / task), i.e. `500 ÷ 1.5749 = 317`
- Non-Go models: AA list price at 1:1, no allowance, so no monthly-task figure

Monthly tasks assumes the whole per-model allowance is used on that model; unused allowance does not transfer, and part use raises the real $ / task.

Unofficial; not affiliated with OpenCode / SST.
