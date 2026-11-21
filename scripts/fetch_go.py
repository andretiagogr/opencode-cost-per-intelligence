"""Fetch OpenCode Go allowances from the published Markdown page into data/go-limits.json.

Source: https://opencode.ai/console/go.md  (listed in https://opencode.ai/llms.txt)
There is no public JSON API for Go; the Markdown table is the machine-readable copy.
Values are the Go plan monthly allowance in USD (e.g. "$15"); "∞" means unlimited.

The table appends badges to model names. "Contributor" and "Limited regions" are parsed
into flags because they change what Go actually serves: Contributor mode is a
lower-priced copy of the model that may train on your traffic, and regional routing can
disappear without the model changing. "Free" and "New" stay part of the name (they are how
the model is listed); "Limited time" is dropped as noise.

Output: {"<base name>": {"limit": 60.0 | null, "contributor": bool, "limited_regions": bool}}
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://opencode.ai/console/go.md'
OUT = os.path.join(BASE, 'data', 'go-limits.json')
META = os.path.join(BASE, 'data', 'fetched_at.json')
MIN_MODELS = 20
REQUIRED = 'GLM-5.3'


def today():
    """Calendar date in Asia/Taipei (UTC+8, no DST) so CI and local runs agree."""
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()

# Badge -> output flag. "Free" / "New" stay: they are part of the name.
BADGES = {'Contributor': 'contributor', 'Limited regions': 'limited_regions'}
DROP = ('Limited time',)


def split_badges(label):
    """'Muse Spark 1.3 Contributor Limited regions' -> ('Muse Spark 1.3', {'contributor': True, ...})"""
    text = label.replace('·', ' ')
    flags = {key: False for key in BADGES.values()}
    for badge, key in BADGES.items():
        if re.search(r'\b' + re.escape(badge) + r'\b', text):
            flags[key] = True
            text = re.sub(r'\s*\b' + re.escape(badge) + r'\b\s*', ' ', text)
    for badge in DROP:
        text = re.sub(r'\s*\b' + re.escape(badge) + r'\b\s*', ' ', text)
    return re.sub(r'\s+', ' ', text).strip(), flags


def parse_allowance(cell):
    """'Go: $15; Go Plus: $60' -> 15.0 ; 'Go: ∞; Go Plus: ∞' -> None"""
    m = re.search(r'Go:\s*\$?([\d,]+)', cell)
    if not m:
        if '∞' in cell:
            return None
        raise ValueError(f'unreadable monthly limit cell: {cell!r}')
    return float(m.group(1).replace(',', ''))


def main():
    req = urllib.request.Request(URL, headers={'accept': 'text/markdown', 'user-agent': 'opencode-go-cost/1.0'})
    with urllib.request.urlopen(req, timeout=60) as res:
        text = res.read().decode('utf-8')

    limits = {}
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cols = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cols) != 4 or cols[0] in ('Model', '') or set(cols[0]) <= {'-'}:
            continue
        name, flags = split_badges(cols[0])
        limits[name] = {
            'limit': parse_allowance(cols[3]),
            'contributor': flags['contributor'],
            'limited_regions': flags['limited_regions'],
        }

    if len(limits) < MIN_MODELS:
        sys.exit(f'go: parsed {len(limits)} models, expected >= {MIN_MODELS} — page format likely changed')
    if REQUIRED not in limits:
        sys.exit(f'go: {REQUIRED!r} missing — page format likely changed')

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted(limits.items())), f, ensure_ascii=False, indent=2)

    meta = {}
    if os.path.exists(META):
        with open(META, encoding='utf-8') as f:
            meta = json.load(f)
    meta['go'] = today()
    with open(META, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    print(f'go: {len(limits)} models, {sum(1 for v in limits.values() if v["limit"] is None)} unlimited, '
          f'{sum(1 for v in limits.values() if v["contributor"])} contributor, '
          f'{sum(1 for v in limits.values() if v["limited_regions"])} limited regions')


if __name__ == '__main__':
    main()
