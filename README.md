# OpenCode Go × Artificial Analysis

Cost per intelligence point for every model on OpenCode Go pricing.

**Live: https://xhang1108.github.io/opencode-cost-per-intelligence/**

![Page](preview.jpg)

## Data

| File | Content |
|---|---|
| `data/aa-models.json` | Intelligence Index, cost per task, output tok/s — Artificial Analysis free API |
| `data/go-limits.json` | Go monthly allowance per model |
| `data/merged.json` | Joined rows + `snapshot_date`, from `python build.py` |

A snapshot, not a live feed. Current numbers: [Intelligence Index](https://artificialanalysis.ai/evaluations/artificial-analysis-intelligence-index) · [Go pricing](https://opencode.ai/console/go)

## Method

| Metric | Formula |
|---|---|
| Go $/task | AA $/task × $10 ÷ monthly allowance |
| $/point | Go $/task ÷ Intelligence Index |
| Tasks per $10 | monthly allowance ÷ AA $/task |

One model at a time: assumes the whole allowance is spent on that model, and unused allowance does not roll over.

## Refresh

Daily 03:23 UTC (11:23 Taipei) and on `workflow_dispatch`: fetch → build → commit `data/` only when it changed. Needs the `AA_API_KEY` repo secret.

Unofficial; not affiliated with OpenCode / SST.
