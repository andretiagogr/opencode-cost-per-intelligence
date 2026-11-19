"""Fetch OpenCode Go allowances from the published Markdown page into data/go-limits.json.

Source: https://opencode.ai/console/go.md  (listed in https://opencode.ai/llms.txt)
There is no public JSON API for Go; the Markdown table is the machine-readable copy.
Values are the Go plan monthly allowance in USD (e.g. "$15"); "∞" means unlimited.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://opencode.ai/console/go.md'
OUT = os.path.join(BASE, 'data', 'go-limits.json')
META = os.path.join(BASE, 'data', 'fetched_at.json')
MIN_MODELS = 20
REQUIRED = 'GLM-5.3'

# Badge words the Markdown table appends to model names. "Free" / "New" stay: they are part of the name.
BADGES = ('Contributor', 'Limited regions', 'Limited time')


def clean(name):
    name = name.replace('·', ' ')
    for badge in BADGES:
        name = re.sub(r'\s*\b' + re.escape(badge) + r'\b\s*', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()


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
        limits[clean(cols[0])] = parse_allowance(cols[3])

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
    meta['go'] = date.today().isoformat()
    with open(META, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    print(f'go: {len(limits)} models, {sum(v is None for v in limits.values())} unlimited')


if __name__ == '__main__':
    main()
