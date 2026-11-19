# OpenCode Console — Visual Design Language (Research Spec)

Scope: restyle a dark data page to match `opencode.ai` / OpenCode Console. All values below were extracted from the **live** site assets on 2026-11-19 (`/console` inline tokens, `entry-client-BKw9UnAW.css`, `landing-layout-BMjekhto.css`), not from third-party "design system" aggregators.

> **Correction to common web advice:** several DESIGN.md aggregator sites claim OpenCode uses "Berkeley Mono" and a warm `#201d1d` background. The live site does **not**: it ships `Inter` + `OpenTUI Mono` and neutral greys (`#0c0c0c` / `#161616`). Ignore the aggregator palette.

---

## 1. Font stack

| Use | Actual face | CSS stack (verbatim from site) |
|---|---|---|
| UI prose, headings, buttons | **Inter** (variable, 100–900, self-hosted `inter-latin-*.woff2`) | `"Inter", "Inter Fallback", sans-serif` |
| Numbers, labels, dates, code, data | **OpenTUI Mono** (self-hosted `opentui-mono-regular-latin-*.woff2` + bold) | `"OpenTUI Mono", "OpenTUI Mono Fallback", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` |

- OpenTUI Mono is a custom face; it is **not** on Google Fonts. Closest free substitutes, in order: `JetBrains Mono` → `IBM Plex Mono` → `SFMono-Regular` → `ui-monospace`. Keep `font-variant-numeric: tabular-nums`.
- Body defaults (Console landing): `font-size:15px; font-weight:440; line-height:24px; letter-spacing:0`.
- Buttons/labels: `13px / 500 / uppercase` (`--t-button-size`, `--t-button-weight`, `--t-button-case`). Eyebrow labels: `13px / 400 / uppercase / letter-spacing:.06em`.
- Headings: `400` weight, `line-height:1.1–1.2`, `letter-spacing:-.05em` (tight, not bold).
- `-webkit-font-smoothing: antialiased`; `font-optical-sizing: none`.
- **Never** introduce a serif. Mixing a second voice breaks the terminal-native identity.

## 2. Palette (dark — the relevant mode)

Two closely related token sets exist. Use **A** for app surfaces; use **B** for chart/data-ink (it is the muted, low-chroma set that produces the "restrained" look).

### A. Console app tokens (`--oc-*` → `--v2-*`, dark)
| Role | Token | Hex | Reasoning |
|---|---|---|---|
| Page bg | `--oc-bg` | `#161616` | grey-1100; neutral near-black, not pure `#000`, not warm-tinted |
| Deep bg | `--v2-background-bg-deep` | `#080808` | grey-1200, for sunken areas |
| Panel / surface | `--oc-surface` | `#242424` | grey-1000 (layer-01); layer-02 `#2e2e2e`, layer-03 `#3a3a3a` |
| Primary text | `--oc-text` | `#fafafa` | grey-100; off-white, not pure `#fff` |
| Muted text | `--oc-text-muted` | `#aeaeae` | grey-500; faint = `#808080` (grey-600) |
| Border | `--oc-border` | `#ffffff1a` | white @10% — alpha, never a solid grey |
| Border muted | `--oc-border-muted` | `#ffffff14` | white @8%; hairlines at 0.5px |
| Accent / link | `--oc-accent` | `#a2bcff` | blue-400 (hover blue-300); light mode `#3b5cf6` |
| Success | `--oc-success` | `#6bd586` | green-500 (light mode green-800 `#198b43`) |
| Warning | `--oc-warning` | `#f2cf76` | yellow-500 (light mode yellow-800 `#cb9f34`) |
| Danger | `--oc-danger` | `#f17471` | red-500 (light mode red-800 `#b82d35`) |

### B. Console landing / data-visual palette (muted, low-chroma)
| Role | Hex | Token |
|---|---|---|
| Page bg | `#0c0c0c` | `--console-grey-1` |
| Raised panel | `#161616` | grey-2 |
| Row hover | `#1a1a1a` | grey-3 |
| Fill / track | `#242424` | grey-4 |
| Faint text (axis, ticks) | `#8f8f8f` | grey-8 |
| Muted text | `#aeaeae` | grey-9 |
| Emphasis | `#dbdbdb` | grey-10 |
| Text | `#fafafa` | grey-11 |
| Success | `#8fbb9a` | `--console-landing-success` |
| Warning | `#cf9c80` | `--console-landing-warning` |
| Accent / blue | `#8d9bc4` | `--console-landing-accent` |
| Go / plus | `#a7bfd6` / `#cdb88f` | plan colors |
| Highlight | `#c9b28a` | `--console-landing-highlight` |

- Grey scale (memorize it): `#0c0c0c → #161616 → #1a1a1a → #242424 → #2e2e2e → #4b4b4b → #6a6a6a → #8f8f8f → #aeaeae → #dbdbdb → #fafafa`.
- Borders are **white at 6–10%**, often `0.5px`. No pure grey borders, no dark drop shadows.
- Semantic colors are dusty/desaturated (e.g. `#8fbb9a`, not `#30d158`). Signal with weight + opacity first, hue second.

## 3. Chart styling rules

- **Gridlines:** horizontal only, `stroke:#ffffff14` (white @8%) or neutral `#2e2e2e`; `stroke-width:.5`; `shape-rendering:crispEdges`. No vertical gridlines except at labeled ticks. No visible axis frame — at most one `0.5px` baseline.
- **Axis labels / ticks:** OpenTUI Mono, `10–11px`, fill `#8f8f8f`; `letter-spacing:.02–.06em`; dates uppercase (e.g. `MAR 14`). Tiny percentage labels sit just past line ends in muted grey. Tabular nums, `text-anchor` aligned to the tick.
- **Legend:** inline, mono `11px`, color `#aeaeae`; swatches = `6–8px` squares (not circles); items separated by a middle dot `·`; append a trailing timestamp like `Updated 26m ago`.
- **Tooltip:** compact floating panel, bg `#161616`/`#242424`, `1px solid #ffffff1a`, `border-radius:4px`, padding `6–8px`, mono `10–11px`, uppercase muted date header + bright value, subtle shadow only if needed. No large rounded cards.
- **Hover guide:** vertical `0.5px` dashed line at `stroke:#ffffff29` (white @16%); a `2–3px` dot with `1px` ring in the series color; nothing else changes.
- **Forecast / projected region:** hatch or dashed fill at low opacity (white @4–8% or series color @15%); behind actual data, never competing with it.
- **Data-ink hierarchy (brightest → dimmest):** headline value (`#fafafa`) → actual series line (`1–1.25px`, series color) → hover guide/dot → gridlines (`0.5px`) → hatch/forecast → axis text (`#8f8f8f`).
- **Spacing:** 8px grid. Chart inset ~`24px`; label-to-line gap `4px`; legend above plot with `8px` gap; panel padding `16px`; panel gap `16px`.

## 4. Button / segmented control / link styling

- **Neutral button** (`data-component="button-v2" data-variant="neutral"`):
  - bg `rgba(255,255,255,.06)` (`--v2-background-bg-button-neutral` = white @6%) — landing version = white @2% mixed over bg
  - `box-shadow: inset 0 0 0 1px rgba(255,255,255,.1)` (no `border` property)
  - `color:#fafafa`, `border-radius:4px` (radius-sm `.25rem`), height `32–40px`, `padding-inline:12–16px`
  - uppercase `13px / 500`; hover = white @2–6% overlay; active = slightly stronger overlay; disabled `opacity:.5`
  - **Contrast/primary** variant only for one hero CTA; keep it neutral everywhere else.
- **Segmented / filter control:** same neutral surface, flat row, `4px` radius, `4px` gap. Selected = text `#fafafa` + border `rgba(255,255,255,.28)` (or accent `#a2bcff` for active); unselected = `#aeaeae`. No pill shapes, no filled accent block.
- **Links:** default `#aeaeae`; hover `#fafafa` (inline prose) or `#a2bcff` (navigation); focus `1px` accent ring. Underline only inside body copy. External links use a tiny `6×6` diagonal-arrow SVG.

## 5. Rules of thumb — "looks like OpenCode"

1. **Mono for data, Inter for prose.** Every number, date, token, price and label is OpenTUI Mono with `tabular-nums`; prose stays Inter. Radius never exceeds `4–6px` (current `12px` panels / `8px` buttons are the biggest tell).
2. **Low-chroma signals.** Use dusty `#8fbb9a` / `#cf9c80` / `#a2bcff`, not saturated dashboard greens/oranges. Your current `#6b8fff` / `#fab283` / `#7fd88f` are too vivid — desaturate toward the landing palette.
3. **Hairlines, not boxes.** `0.5px` borders at 6–10% white; no heavy borders, no colored card backgrounds, no big shadows. Depth comes from `#0c0c0c → #161616 → #242424` steps.
4. **Terminal cadence.** Uppercase `11–13px` labels with slight tracking, tight line-height, `8px` grid, bracketed indexes (`[01]`), and relative timestamps ("Updated 26m ago").
5. **Restraint wins.** One accent, one CTA style, no gradients (except a 2% white hover wash), no decorative charts-within-charts. If an element shouts, remove color before removing information.

### Quick delta for `index.html` (do not apply here — reference only)
Current palette is already close (`#0c0c0c / #161616 / #2e2e2e / #fafafa / #8f8f8f`). Minimal fixes: radius `12px → 4px`; button radius `8px → 4px` + uppercase `13px/500` + inset white/0.1 border; accent `#6b8fff → #a2bcff`; good `#7fd88f → #8fbb9a`; orange `#fab283 → #cf9c80`; font fallback `"Berkeley Mono" → "OpenTUI Mono", "JetBrains Mono"`; add `font-variant-numeric: tabular-nums` to numeric cells; borders `1px solid #2e2e2e → .5px solid rgba(255,255,255,.1)`.
