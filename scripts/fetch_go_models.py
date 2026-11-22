"""Snapshot the live OpenCode Go models endpoint into data/go-models.json.

Source: https://opencode.ai/inference/go/v1/models
The browser fetches the same endpoint and falls back to this file, so keeping it current
also keeps the offline page priced. build.py reads the snapshot's reasoning efforts to
decide whether an AA score is an upper bound ("≤") for the effort Go actually sells.

Output: the endpoint document unchanged ({"object": ..., "data": [...]}).
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'https://opencode.ai/inference/go/v1/models'
OUT = os.path.join(BASE, 'data', 'go-models.json')
META = os.path.join(BASE, 'data', 'fetched_at.json')
MIN_MODELS = 10


def today():
    """Calendar date in Asia/Taipei (UTC+8, no DST) so CI and local runs agree."""
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()


def main():
    req = urllib.request.Request(
        URL,
        headers={'accept': 'application/json', 'user-agent': 'opencode-go-cost/1.0'},
    )
    with urllib.request.urlopen(req, timeout=60) as res:
        body = json.load(res)

    models = body.get('data') if isinstance(body, dict) else None
    if not isinstance(models, list) or len(models) < MIN_MODELS:
        count = len(models) if isinstance(models, list) else 0
        sys.exit(f'go-models: got {count} models, expected >= {MIN_MODELS} — refusing to overwrite')

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(body, f, ensure_ascii=False, indent=2)

    # build.py's snapshot_date() takes the oldest date in this file. go_models is
    # refreshed daily and is therefore never older than the AA / go-limits stamps,
    # so adding it does not move snapshot_date.
    meta = {}
    if os.path.exists(META):
        with open(META, encoding='utf-8') as f:
            meta = json.load(f)
    meta['go_models'] = today()
    with open(META, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    print(f'go-models: {len(models)} models')


if __name__ == '__main__':
    main()
