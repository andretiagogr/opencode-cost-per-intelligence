import copy, json, re, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = ('aa-models.json', 'go-limits.json')
AA = json.load(open(os.path.join(BASE,'data','aa-models.json'),encoding='utf-8'))
GO = json.load(open(os.path.join(BASE,'data','go-limits.json'),encoding='utf-8'))
PLAN_PRICE = 10.0

# DeepSeek bills peak and off-peak rates. AA's own Intelligence Index cost breakdown
# prices DeepSeek at peak (V4.1 Flash Max: 174.36M output tokens x $1.20/M = $209.23
# output cost, exactly AA's figure), so the AA row is the peak one and the off-peak
# twin is half. Both rows are emitted; the label says which is which.
DEEPSEEK_OFFPEAK_FACTOR = 0.5

# Snapshot date = when the source snapshots were fetched, not when this ran.
def snapshot_date():
    meta_path = os.path.join(BASE, 'data', 'fetched_at.json')
    if os.path.exists(meta_path):
        with open(meta_path, encoding='utf-8') as f:
            stamps = [v for v in json.load(f).values() if v]
        if stamps:
            return min(stamps)  # oldest half of the snapshot
    stamps = [os.path.getmtime(os.path.join(BASE,'data',f)) for f in SRC]
    return datetime.fromtimestamp(max(stamps)).strftime('%Y-%m-%d')

# When the AA scores were fetched (the footer's "AA scores: snapshot of …"), independent of
# the Go fetchers, which run even when the AA fetch is skipped for want of a key.
def aa_snapshot_date():
    meta_path = os.path.join(BASE, 'data', 'fetched_at.json')
    if os.path.exists(meta_path):
        with open(meta_path, encoding='utf-8') as f:
            aa = json.load(f).get('aa')
        if aa:
            return aa
    return datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, 'data', 'aa-models.json'))).strftime('%Y-%m-%d')

# Go serves Meta's Contributor mode for Muse Spark: same tokens, published at list price
# so the model's data may be used for training. AA measures cost/task at standard prices,
# so convert with the published price ratio instead of hard-coding a multiplier.
# Meta list prices, USD per 1M tokens, blended 7:2:1 cache-hit : input : output.
BLEND = (0.7, 0.2, 0.1)
STANDARD = (0.15, 1.25, 4.25)      # cached / input / output, standard mode
CONTRIBUTOR = (0.002, 0.10, 0.20)  # cached / input / output, contributor mode

def blended(price):
    return sum(w * p for w, p in zip(BLEND, price))

CONTRIBUTOR_RATIO = blended(CONTRIBUTOR) / blended(STANDARD)  # 0.0414 / 0.78 ≈ 0.053077

def go_value(v):
    """go-limits.json entry: new dict, or the old bare float/None. -> (limit, contributor, limited_regions)"""
    if isinstance(v, dict):
        return v.get('limit'), bool(v.get('contributor')), v.get('limited_regions')
    return v, False, None

def norm(s):
    return re.sub(r'[^a-z0-9]+','', (s or '').lower())

go_norm = {norm(k): (k, go_value(v)) for k, v in GO.items()}

# AA and Go list the same model under different product names. Verified against
# Go canonical_id reflection/beam-1.0-501b-a23b and AA slug reflection-beam.
GO_ALIASES = {
    'beam10': 'Beam Free',        # AA Beam 1.0 / Go Beam Free — canonical reflection/beam-1.0-501b-a23b
    'tencenthy4': 'Hy4 New',      # AA Tencent Hy4 / Go Hy4 — canonical tencent/hy4 (release 2026-11-03/04)
}

def match(name):
    n = norm(name)
    if n in GO_ALIASES:
        go_name = GO_ALIASES[n]
        return (norm(go_name), go_name, go_norm[norm(go_name)][1])
    # exact
    if n in go_norm:
        orig, rec = go_norm[n]
        return (n, orig, rec)
    best = None
    # Go base is prefix of AA variant
    for gn, (orig, rec) in go_norm.items():
        if len(gn) < 3: continue
        if n.startswith(gn):
            if best is None or len(gn) > len(best[0]):
                best = (gn, orig, rec)
    if best:
        return best
    # fallback: AA prefix of Go (specific Go variant)
    for gn, (orig, rec) in go_norm.items():
        if len(gn) < 3: continue
        if gn.startswith(n):
            if best is None or len(gn) > len(best[0]):
                best = (gn, orig, rec)
    return best

def make_row(m, slug, used, go_name, limit, limited, source, pricing_mode, label=None, eff_override=None):
    ii = m['intelligence_index']
    cpt = m['cost_per_task']
    if eff_override is not None:
        eff = eff_override
    elif limit and limit not in (None, float('inf')):
        eff = used * (PLAN_PRICE / limit)
    else:
        eff = used
    return {
        'name': m['name'],
        'label': label or m['name'],          # chart/tooltip name; tells the two tiers apart
        'slug': slug,
        'intelligence_index': ii,
        'aa_cost_per_task': cpt,
        'aa_cost_per_task_standard': cpt,
        'aa_cost_per_task_used': used,
        'go_model': go_name,
        'go_monthly_limit': limit,
        'go_limited_regions': limited,
        'go_effective_cost_per_task': eff,
        'cost_per_intelligence_point': (eff / ii) if (eff is not None and ii) else None,
        'intelligence_per_dollar': (ii / eff) if (eff is not None and ii and eff) else None,
        'monthly_task_capacity': (PLAN_PRICE / eff) if (limit and eff) else None,
        'cost_source': source,
        'pricing_mode': pricing_mode,
        'median_output_tokens_per_second': m.get('median_output_tokens_per_second'),
        'release_date': m.get('release_date'),
    }

rows = []
for m in AA['models']:
    if m.get('intelligence_index') is None or m.get('cost_per_task') is None:
        continue
    hit = match(m['name'])
    if not hit:
        rows.append(make_row(m, m['slug'], m['cost_per_task'], None, None, None, 'AA provider', 'aa-standard'))
        continue
    go_name = hit[1]
    limit, contributor, limited = hit[2]
    if limit is None:
        # Go free tier: no monthly allowance and $0/task. Keep the AA list-price
        # row for reference, and add a Go row at $0 — same two-row pattern as
        # Contributor, but the cheaper side is free rather than discounted.
        rows.append(make_row(m, m['slug'], m['cost_per_task'], None, None, None, 'AA provider', 'aa-standard'))
        rows.append(make_row(m, m['slug'] + '-go-free', m['cost_per_task'], go_name, None, limited,
                             'Go (free)', 'go-free', label=go_name, eff_override=0))
        continue
    source = 'Go' if (limit and limit not in (None, float('inf'))) else 'Go (unlimited)'
    if contributor:
        # Two tiers, two rows: Meta still sells standard (what AA measured) at list price,
        # while Go sells the Contributor variant at the discounted card. Showing only one
        # hides a ~19x gap; showing both lets the reader pick.
        rows.append(make_row(m, m['slug'], m['cost_per_task'], None, None, None, 'AA provider', 'aa-standard'))
        rows.append(make_row(m, m['slug'] + '-contributor', m['cost_per_task'] * CONTRIBUTOR_RATIO,
                             go_name, limit, limited, source, 'go-contributor',
                             label=m['name'] + ' · Contributor'))
    else:
        rows.append(make_row(m, m['slug'], m['cost_per_task'], go_name, limit, limited, source, 'go-standard'))

def recompute(r):
    ii, eff = r['intelligence_index'], r['go_effective_cost_per_task']
    r['cost_per_intelligence_point'] = (eff / ii) if (eff is not None and ii) else None
    r['intelligence_per_dollar'] = (ii / eff) if (eff and ii) else None
    r['monthly_task_capacity'] = (PLAN_PRICE / eff) if (r.get('go_monthly_limit') and eff) else None

# AA may have scored a model at an effort Go does not sell (Muse Spark 1.3 Contributor
# stops at Xhigh; AA's scored run is Max). The Go endpoint lists each model's efforts.
# If AA has a scored run of the same model at the highest effort Go allows, the Go row
# uses it; otherwise the row keeps the higher run and is flagged as an upper bound, so
# the page can show "≤". When AA scores the allowed run, the next build switches by itself.
EFFORTS = ['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']

def split_effort(name):
    m = re.match(r'^(.*?)\s*\(([^)]*)\)\s*$', name or '')
    if not m:
        return (name or '').strip(), None
    eff = m.group(2).split(',')[0].strip().lower()
    return m.group(1).strip(), (eff if eff in EFFORTS else None)

def go_endpoint_efforts():
    """norm(Go model name) -> efforts list from the go-models.json snapshot, or {} when absent."""
    path = os.path.join(BASE, 'data', 'go-models.json')
    if not os.path.exists(path):
        return {}
    data = json.load(open(path, encoding='utf-8'))
    out = {}
    for x in data.get('data', []):
        eff = ((x.get('capabilities') or {}).get('reasoning') or {}).get('effort')
        if eff:
            out[norm(x.get('name'))] = eff
    return out

def go_max_effort(go_name, endpoint):
    g = norm(go_name)
    eff = endpoint.get(g)
    if eff is None:  # go.md drops suffixes the endpoint keeps ("Muse Spark 1.3" vs "… Contributor")
        cands = sorted((k for k in endpoint if k.startswith(g)), key=len)
        eff = endpoint[cands[0]] if cands else None
    ranks = [EFFORTS.index(e) for e in (eff or []) if e in EFFORTS]
    return EFFORTS[max(ranks)] if ranks else None

ENDPOINT_EFFORTS = go_endpoint_efforts()
AA_SCORED = [m for m in AA['models'] if m.get('intelligence_index') is not None and m.get('cost_per_task') is not None]

for r in rows:
    if not r.get('go_model') or r['pricing_mode'] == 'aa-standard':
        continue
    base, eff = split_effort(r['name'])
    cap = go_max_effort(r['go_model'], ENDPOINT_EFFORTS)
    if eff is None or cap is None or EFFORTS.index(eff) <= EFFORTS.index(cap):
        continue
    allowed = [(EFFORTS.index(e), m) for m in AA_SCORED
               for b, e in [split_effort(m['name'])]
               if b == base and e is not None and EFFORTS.index(e) <= EFFORTS.index(cap)]
    if allowed:
        # The allowed run matches the same Go model in the loop above and already has its own
        # Go row(s). This run is not sold by Go: drop its extra Go row (Contributor / free twin),
        # or, when it is the plain row, keep it as AA-provider data only.
        if r['pricing_mode'] in ('go-contributor', 'go-free'):
            r['_drop'] = True
        else:
            r.update(go_model=None, go_monthly_limit=None, go_limited_regions=None,
                     go_effective_cost_per_task=r['aa_cost_per_task'], cost_source='AA provider',
                     pricing_mode='aa-standard')
            recompute(r)
    else:
        r['score_upper_bound'] = True   # Intelligence Index is from a run Go does not sell
        r['score_effort'] = eff
        r['go_max_effort'] = cap
        r['label'] = base + r['label'][len(r['name']):]

rows = [r for r in rows if not r.pop('_drop', False)]

# DeepSeek is listed twice: AA's row at peak rates and a half-price off-peak twin.
# The twin is a full copy so Go's monthly-allowance maths works out the same way:
# off-peak tasks consume half the allowance, so the effective Go price halves too.
for r in [x for x in rows if 'deepseek' in x['slug']]:
    base_label = r['label']
    r['deepseek_variant'] = 'peak'
    r['label'] = base_label + ' · Peak'
    twin = copy.deepcopy(r)
    twin['slug'] = r['slug'] + '-offpeak'
    twin['label'] = base_label + ' · Off-peak'
    twin['deepseek_variant'] = 'off-peak'
    for key in ('aa_cost_per_task', 'aa_cost_per_task_used', 'go_effective_cost_per_task'):
        if twin.get(key) is not None:
            twin[key] *= DEEPSEEK_OFFPEAK_FACTOR
    recompute(twin)
    rows.append(twin)

rows.sort(key=lambda r: r['cost_per_intelligence_point'])

with open(os.path.join(BASE,'data','merged.json'),'w',encoding='utf-8') as f:
    json.dump({'intelligence_index_version': AA.get('intelligence_index_version'), 'plan_price': PLAN_PRICE,
               'snapshot_date': snapshot_date(), 'aa_snapshot_date': aa_snapshot_date(), 'build_date': datetime.now().strftime('%Y-%m-%d'), 'rows': rows}, f, ensure_ascii=False, indent=2)

print('total scored:', len(rows))
print('Go:', sum(1 for r in rows if r['cost_source'].startswith('Go')))
print('AA provider:', sum(1 for r in rows if r['cost_source']=='AA provider'))
print('snapshot:', snapshot_date())
