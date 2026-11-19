import json, re, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = ('aa-models.json', 'go-limits.json')
AA = json.load(open(os.path.join(BASE,'data','aa-models.json'),encoding='utf-8'))
GO = json.load(open(os.path.join(BASE,'data','go-limits.json'),encoding='utf-8'))
PLAN_PRICE = 10.0

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

def norm(s):
    return re.sub(r'[^a-z0-9]+','', (s or '').lower())

go_norm = {norm(k): (k, v) for k, v in GO.items()}

def match(name):
    n = norm(name)
    # exact
    if n in go_norm:
        orig, limit = go_norm[n]
        return (n, orig, limit)
    best = None
    # Go base is prefix of AA variant
    for gn, (orig, limit) in go_norm.items():
        if len(gn) < 3: continue
        if n.startswith(gn):
            if best is None or len(gn) > len(best[0]):
                best = (gn, orig, limit)
    if best:
        return best
    # fallback: AA prefix of Go (specific Go variant)
    for gn, (orig, limit) in go_norm.items():
        if len(gn) < 3: continue
        if gn.startswith(n):
            if best is None or len(gn) > len(best[0]):
                best = (gn, orig, limit)
    return best

rows = []
for m in AA['models']:
    ii = m.get('intelligence_index')
    cpt = m.get('cost_per_task')
    if ii is None or cpt is None:
        continue
    hit = match(m['name'])
    if hit:
        go_name = hit[1]; limit = hit[2]; source = 'Go'
        if limit and limit not in (None, float('inf')):
            eff = cpt * (PLAN_PRICE / limit)
        else:
            eff = cpt; source = 'Go (unlimited)'
    else:
        go_name = None; limit = None; source = 'AA provider'
        eff = cpt
    cpi = (eff / ii) if (eff is not None and ii) else None
    ipd = (ii / eff) if (eff is not None and ii and eff) else None
    cap = (PLAN_PRICE / eff) if (limit and eff) else None
    rows.append({
        'name': m['name'],
        'slug': m['slug'],
        'intelligence_index': ii,
        'aa_cost_per_task': cpt,
        'go_model': go_name,
        'go_monthly_limit': limit,
        'go_effective_cost_per_task': eff,
        'cost_per_intelligence_point': cpi,
        'intelligence_per_dollar': ipd,
        'monthly_task_capacity': cap,
        'cost_source': source,
        'median_output_tokens_per_second': m.get('median_output_tokens_per_second'),
        'release_date': m.get('release_date'),
    })

rows.sort(key=lambda r: r['cost_per_intelligence_point'])

with open(os.path.join(BASE,'data','merged.json'),'w',encoding='utf-8') as f:
    json.dump({'intelligence_index_version': AA.get('intelligence_index_version'), 'plan_price': PLAN_PRICE,
               'snapshot_date': snapshot_date(), 'rows': rows}, f, ensure_ascii=False, indent=2)

print('total scored:', len(rows))
print('Go:', sum(1 for r in rows if r['cost_source'].startswith('Go')))
print('AA provider:', sum(1 for r in rows if r['cost_source']=='AA provider'))
print('snapshot:', snapshot_date())
