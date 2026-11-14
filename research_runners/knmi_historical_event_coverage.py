# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline receipt-pinned coverage of candidate three-day storm windows."""
import argparse
from datetime import datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import zipfile
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_runners.knmi_historical_wind_acquisition import inspect


def window(observations, date):
    middle = datetime.strptime(date, '%Y%m%d')
    hours = [middle - timedelta(days=1) + timedelta(hours=i) for i in range(1, 73)]
    present = sum(t in observations for t in hours)
    valid = sum(observations.get(t) is not None for t in hours)
    return {'present_hours':present, 'valid_gust_hours':valid,
            'missing_rows':72-present, 'missing_gust_values':present-valid,
            'complete':valid == 72}


def read_archive(path, expected_hash, station):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise ValueError('Original archive hash mismatch')
    inspect(raw, station)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        lines = z.read(z.namelist()[0]).decode('utf-8-sig').splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith('# STN,'))
    fields = [v.strip() for v in lines[start][2:].split(',')]
    observations = {}
    for line in lines[start+1:]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        row = dict(zip(fields, [v.strip() for v in line.split(',')]))
        stamp = datetime.strptime(row['YYYYMMDD'], '%Y%m%d') + timedelta(hours=int(row['HH']))
        observations[stamp] = int(row['FX']) / 10 if row['FX'] else None
    return observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--hazard', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Refusing output overwrite')
    from netCDF4 import Dataset
    with Dataset(args.hazard) as d:
        events = list(zip(map(str,d.variables['Storm_Names'][:]), map(str,d.variables['Storm_Dates'][:])))
    receipt_raw = args.receipt.read_bytes()
    receipt = json.loads(receipt_raw)
    stations = {}
    for r in receipt['results']:
        if r['status'] != 'downloaded_and_parsed':
            raise ValueError('Failed acquisition in receipt')
        station = r['station']
        path = args.archive_dir / f"uurgeg_{station}_{r['period']}.zip"
        series = read_archive(path, r['sha256'], station)
        existing = stations.setdefault(station, {})
        if existing.keys() & series.keys():
            raise ValueError('Overlapping archive timestamps')
        existing.update(series)
    rows = []
    for i, (name, date) in enumerate(events):
        coverage = {str(station):window(obs,date) for station,obs in sorted(stations.items())}
        rows.append({'source_storm_index':i, 'source_name':name, 'source_date':date,
                     'stations':coverage, 'all_stations_complete':bool(coverage) and all(v['complete'] for v in coverage.values())})
    result = {'schema':'KNMI_HISTORICAL_EVENT_COVERAGE_V1',
              'receipt_sha256':hashlib.sha256(receipt_raw).hexdigest(),
              'hazard_sha256':hashlib.sha256(args.hazard.read_bytes()).hexdigest(),
              'window_basis':'candidate: source date minus one day 01 UTC through following day 24 UTC',
              'exact_source_window_verified':False, 'scientific_validation_complete':False,
              'annual_catalogue_complete':False,
              'event_era_station_positions_verified':False,
              'current_fx_height_correction_status_verified':False,
              'bias_calibration_eligible':False,
              'station_metadata_review':'research/observations/knmi_wind_metadata_review.json',
              'common_complete_events':sum(r['all_stations_complete'] for r in rows), 'events':rows}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'common_complete_events':result['common_complete_events'],
                      'complete_by_station':{str(s):sum(r['stations'][str(s)]['complete'] for r in rows) for s in stations}}))

if __name__ == '__main__':
    main()
