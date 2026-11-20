# Audit — index.html (pre-redesign, 221 lines) — archived

> Kept as the record of the state before the canvas rewrite. The Chinese glosses it quotes were removed from the page; they are described in English here.

## 1. Structure / Traditional Chinese to translate
- `<html lang="zh-Hant">` (L2) → should be `en`.
- Header `.sub` (L43–44): Chinese copy about Go effective pricing, attribution, and unofficial disclaimer — needs EN.
- Chart panel h3 (L56): "Intelligence Index vs. Cost per Task" plus a two-character Chinese gloss meaning "kill line" (i.e. Pareto frontier).
- HTML legend (L58): fully Chinese, needs EN or removal.
- Footer (L84–88): five Chinese lines (data source, Go pricing, effective-cost formula, CPI formula, disclaimer).
- Dataset label "Pareto" plus the same Chinese gloss (L174).
- Already English: title, badges, stats labels, filter buttons, all table headers.

## 2. Chart config (L154–203)
- Chart.js 4.4.1 + Hammer 2.0.8 + chartjs-plugin-zoom 2.2.0 via CDN (L92–94); registration accepts `window.ChartZoom` OR `window.chartjsPluginZoom` (L96–97).
- `type:'scatter'`, `responsive:true`, `maintainAspectRatio:false`, `animation:false` (L178).
- Datasets (L170–175):
  1. `Go models` — goRows, x=`px(go_effective_cost_per_task)`, y=`intelligence_index`, `r`=row; radius `max(3,10-cpi*30)`; orange fill.
  2. `AA original (Go models)` — same goRows, x=`px(aa_cost_per_task)`; radius 4; translucent gray.
  3. `AA provider models` — aaRows, x=`px(go_effective_cost_per_task)`; radius `max(3,10-cpi*30)`; gray.
  4. `Pareto` + gloss — `type:'line'`, pf rows, border `#e06c75`, `pointRadius:0`, `tension:0.2`, `borderWidth:2`.
- Scales: x logarithmic, fixed 1-2-5 ticks via `afterBuildTicks` (L181–188); y linear, fixed step-10 ticks (L190–194).
- Bounds from FULL `data.rows`: `allX` = both cost fields >0/finite; `xLo=10^floor(log10(min))`, `xHi=10^ceil(log10(max))`, `yHi=ceil(maxII/10)*10+10`.
- `px(v)` (L165): v if `v>0 && isFinite(v)`, else `xLo` — clamps zero-cost models onto the log axis.
- Zoom plugin: limits x `{min:xLo,max:xHi,minRange:0.0002}`, y `{min:0,max:yHi,minRange:2}`; wheel/pinch enabled, mode `xy`; pan enabled, mode `xy`.
- Tooltip callback shows `name II xx $/pt xx [cost_source]`, empty for Pareto points.
- `pareto()` sorts by `go_effective_cost_per_task`, keeps increasing II.

## 3. Interactive features
- Wheel/pinch zoom + drag pan via plugin, bounded by limits/minRange.
- Table sort: click `th[data-k]`, `rank` ignored, toggle/replace key, re-render.
- Filters All/Go/AA; `filteredRows()` uses `startsWith('Go')` / `==='AA provider'`. Chart rebuilt + table re-rendered on each click.

## 4. Change map for the redesign
- **Color by company:** no `company` field in `merged.json`; derive from name/slug using `company-palette.json`. Rewrite dataset construction (one dataset per company, or single dataset with color array); update tooltip and HTML legend.
- **Hide company/model:** add hidden sets; extend `filteredRows()` and apply to chart rows and Pareto; recalc axes on hide; add UI near filters.
- **Go ring instead of fill:** keep `cost_source.startsWith('Go')`; company-based fill + `borderColor`/`borderWidth` ring only for Go; update legend.
- **$ on x-axis:** title include `$`; `ticks.callback` prefix `$`; update legend/header.
- **Remove source legend:** `plugins.legend.display:false`, delete/replace HTML legend; optionally drop `.src-go/.src-aa` CSS and Source column.

## 5. Latent bugs / fragile spots
- Zero-cost rows collapse to `xLo` via `px()`, overplot at left edge; tooltip shows true 0 — misleading.
- `best` reduce has no initial value (throws on empty) and picks `cpi=0` from costless models → "Best" shows `0.0000`.
- `pareto()` uses `go_effective_cost` for AA-only rows; zero-cost AA rows jump to the frontier and distort the line.
- `filteredRows().sort()` mutates `data.rows` in place when filter=`all`.
- Chart fully destroyed/recreated on filter, losing zoom/pan state.
- Tooltip returns empty label on Pareto hover; `isFinite(null)===true` so null II would plot as 0.
- Plugin global-name fallback can silently fail to register → zoom dead with no error.
- No SRI on CDN scripts; `startsWith('Go')` misclassifies future "Go…" sources; CSS colors hardcoded.
