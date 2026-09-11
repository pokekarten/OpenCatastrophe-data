#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    path = Path(sys.argv[1])
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    if not rows:
        raise SystemExit('empty dataset')

    required = {'GRCODE', 'GRNAME', 'AccidentYear', 'DevelopmentYear', 'DevelopmentLag', 'LOB'}
    missing = sorted(required.difference(fields))
    if missing:
        raise SystemExit(f'missing required fields: {missing}')

    ay = [int(r['AccidentYear']) for r in rows]
    dy = [int(r['DevelopmentYear']) for r in rows]
    lag = [int(float(r['DevelopmentLag'])) for r in rows]
    grcodes = {int(r['GRCODE']) for r in rows}
    lobs = sorted({r['LOB'].strip() for r in rows})

    by_lob = Counter(r['LOB'].strip() for r in rows)
    company_lob = defaultdict(lambda: {'rows': 0, 'ays': set(), 'dys': set(), 'lags': set()})
    for r in rows:
        key = (int(r['GRCODE']), r['LOB'].strip())
        rec = company_lob[key]
        rec['rows'] += 1
        rec['ays'].add(int(r['AccidentYear']))
        rec['dys'].add(int(r['DevelopmentYear']))
        rec['lags'].add(int(float(r['DevelopmentLag'])))

    examples = []
    for (grcode, lob), rec in sorted(company_lob.items())[:30]:
        examples.append({
            'grcode': grcode,
            'lob': lob,
            'rows': rec['rows'],
            'ay_min': min(rec['ays']),
            'ay_max': max(rec['ays']),
            'ay_count': len(rec['ays']),
            'dy_min': min(rec['dys']),
            'dy_max': max(rec['dys']),
            'dy_count': len(rec['dys']),
            'lag_min': min(rec['lags']),
            'lag_max': max(rec['lags']),
            'lag_count': len(rec['lags']),
        })

    result = {
        'file': {
            'bytes': path.stat().st_size,
            'sha256': sha256(path),
        },
        'fields': fields,
        'rows': len(rows),
        'companies': len(grcodes),
        'lobs': lobs,
        'rows_by_lob': dict(sorted(by_lob.items())),
        'accident_year': {'min': min(ay), 'max': max(ay), 'count': len(set(ay))},
        'development_year': {'min': min(dy), 'max': max(dy), 'count': len(set(dy))},
        'development_lag': {'min': min(lag), 'max': max(lag), 'count': len(set(lag)), 'values': sorted(set(lag))},
        'development_year_minus_accident_year': sorted(set(d - a for a, d in zip(ay, dy))),
        'company_lob_count': len(company_lob),
        'company_lob_examples': examples,
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    Path('tmp/ffbk_clrd2025_cdr/inspection.json').write_text(
        json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
