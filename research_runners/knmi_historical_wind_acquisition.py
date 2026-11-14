# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Acquire bounded original KNMI decades outside Git, retaining missing gusts."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile
from datetime import datetime, timedelta

BASE = 'https://cdn.knmi.nl/knmi/map/page/klimatologie/gegevens/uurgegevens/'


def inspect(raw, station):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].file_size > 100_000_000:
            raise ValueError('Unexpected or oversized archive')
        lines = archive.read(members[0]).decode('utf-8-sig').splitlines()
    header = next(line for line in lines if line.startswith('# STN,'))
    fields = [v.strip() for v in header[2:].split(',')]
    if not {'STN', 'YYYYMMDD', 'HH', 'FX'} <= set(fields):
        raise ValueError('Missing required fields')
    stamps, valid = set(), 0
    for line in lines[lines.index(header) + 1:]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        values = [v.strip() for v in next(csv.reader([line]))]
        if len(values) != len(fields):
            raise ValueError('Malformed source row')
        row = dict(zip(fields, values))
        if int(row['STN']) != station or not 1 <= int(row['HH']) <= 24:
            raise ValueError('Wrong station or hour')
        stamp = datetime.strptime(row['YYYYMMDD'], '%Y%m%d') + timedelta(hours=int(row['HH']))
        if stamp in stamps:
            raise ValueError('Duplicate timestamp')
        stamps.add(stamp)
        if row['FX']:
            if int(row['FX']) < 0:
                raise ValueError('Negative gust')
            valid += 1
    if not stamps:
        raise ValueError('Empty series')
    expected = int((max(stamps)-min(stamps)).total_seconds()/3600)+1
    return {'rows': len(stamps), 'valid_fx': valid, 'missing_fx': len(stamps)-valid,
            'missing_hours_between_endpoints': expected-len(stamps),
            'first_hour_end_utc': min(stamps).isoformat(), 'last_hour_end_utc': max(stamps).isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--stations', nargs='+', type=int, default=[235,260,280,310,330])
    parser.add_argument('--periods', nargs='+', choices=['1981-1990','1991-2000'], default=['1981-1990','1991-2000'])
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if any((p / '.git').exists() for p in [out, *out.parents]):
        raise ValueError('Originals must remain outside Git')
    out.mkdir(parents=True, exist_ok=True)
    receipt = out / 'receipt.json'
    if receipt.exists():
        raise ValueError('Receipt already exists')
    results = []
    for station in args.stations:
        for period in args.periods:
            name = f'uurgeg_{station}_{period}.zip'
            target = out / name
            url = BASE + name
            result = {'station':station, 'period':period, 'url':url}
            try:
                if target.exists():
                    raise ValueError('Refusing original overwrite')
                with urllib.request.urlopen(url, timeout=45) as response:
                    raw = response.read(30_000_001)
                if len(raw) > 30_000_000:
                    raise ValueError('Download exceeds 30 MB bound')
                summary = inspect(raw, station)
                with target.open('xb') as stream:
                    stream.write(raw)
                result.update(summary, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), status='downloaded_and_parsed')
            except Exception as exc:
                result.update(status='failed', error=str(exc))
            results.append(result)
            print(json.dumps(result), flush=True)
    receipt.write_text(json.dumps({'schema':'KNMI_HISTORICAL_ACQUISITION_V1',
        'scientifically_admitted':False, 'rights_admitted':False,
        'gust_duration_and_station_history_verified':False, 'results':results}, indent=2)+'\n')
    return int(any(r['status']=='failed' for r in results))

if __name__ == '__main__':
    raise SystemExit(main())
