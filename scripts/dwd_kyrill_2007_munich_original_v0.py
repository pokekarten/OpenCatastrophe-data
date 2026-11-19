#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Two distinct original DWD Munich 10min FX_10 stations during Kyrill, research only.

Does NOT claim calibrated ERA5, spatial damage dependence, observed claims,
annual event frequency, or that different measurement heights are comparable.
Download source ZIPs separately; do not commit them. Original SHA256 digests
are reported, not pre-declared authoritative until verified real-source replay.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile, BadZipFile

from scripts.dwd_kyrill_2007_berlin_original_v0 import (
    OriginalDWDGateError, _gust, _utc_stamp, _header, _member,
    WINDOW_START, WINDOW_END, DAYS, REQUIRED, MAX_ARCHIVE,
    MAX_LINE, MAX_ROWS, UTC_SOURCE_START,
)

STATIONS = {
    '01262': {'name':'Muenchen-Flughafen', 'source_filename':
        '10minutenwerte_extrema_wind_01262_20000101_20091231_hist.zip'},
    '03379': {'name':'Muenchen-Stadt', 'source_filename':
        '10minutenwerte_extrema_wind_03379_20000101_20091231_hist.zip'},
}
CONTRACT = 'OC_DWD_KYRILL_2007_TWO_MUNICH_STATION_GUST_HOLDOUT_V0'
SOURCE_DIRECTORY = ('https://opendata.dwd.de/climate_environment/CDC/'
                    'observations_germany/climate/10_minutes/extreme_wind/historical/')


def audit_station(raw: bytes, *, station_id: str, expected_sha256: str | None = None) -> dict:
    """Read complete original DWD 2000-09 ZIP; disclose four daily aggregates only."""
    if type(station_id) is not str or station_id not in STATIONS:
        raise OriginalDWDGateError('approved original Munich station ID required')
    if type(raw) is not bytes or not 100 <= len(raw) <= MAX_ARCHIVE or raw[:4] != b'PK\x03\x04':
        raise OriginalDWDGateError('complete bounded DWD ZIP required')
    digest = sha256(raw).hexdigest()
    if expected_sha256 is not None:
        if (type(expected_sha256) is not str or not re.fullmatch('[0-9a-f]{64}', expected_sha256)
                or expected_sha256 != digest):
            raise OriginalDWDGateError('exact original source SHA256 differs')
    rows=0
    first=last=None
    prelude=0
    daily={day: {'observed':0,'missing':0,'qn':Counter(),'max_all':None,'max_qn23':None}
           for day in DAYS}
    try:
        with ZipFile(BytesIO(raw)) as z:
            product, header = _member(z)
            cols={k:header.index(k) for k in REQUIRED}
            with z.open(product) as reader:
                if _header(reader.readline(MAX_LINE+1))!=header:
                    raise OriginalDWDGateError('unexpected DWD source header drift')
                for line in reader:
                    if not line.strip():continue
                    if len(line)>MAX_LINE: raise OriginalDWDGateError('oversized DWD row')
                    try: pieces=[p.strip().strip('"') for p in line.decode('utf-8').rstrip('\r\n').split(';')]
                    except UnicodeError as exc: raise OriginalDWDGateError('unreadable DWD source row') from exc
                    if len(pieces)!=len(header):raise OriginalDWDGateError('DWD row/header mismatch')
                    ident,ts,qn,gust=(pieces[cols[x]] for x in REQUIRED)
                    if (not ident.isascii() or not ident.isdigit() or
                            ident.zfill(5)!=station_id):
                        raise OriginalDWDGateError('wrong original DWD station ID')
                    when=_utc_stamp(ts)
                    if last is not None and when<=last:
                        raise OriginalDWDGateError('nonmonotone or duplicated DWD source clock')
                    if first is None:first=when
                    last=when
                    if qn not in ('1','2','3'):
                        raise OriginalDWDGateError('unreviewed DWD historical quality class')
                    value=_gust(gust)
                    rows+=1
                    if rows>MAX_ROWS:raise OriginalDWDGateError('original source row ceiling exceeded')
                    if when < UTC_SOURCE_START:prelude+=1
                    if WINDOW_START<=when<=WINDOW_END:
                        entry=daily[when.date().isoformat()]
                        entry['observed']+=1;entry['qn'][qn]+=1
                        if value is None:entry['missing']+=1
                        else:
                            entry['max_all']=value if entry['max_all'] is None else max(value,entry['max_all'])
                            if qn in ('2','3'):
                                entry['max_qn23']=value if entry['max_qn23'] is None else max(value,entry['max_qn23'])
            # Verify CRC on all other ZIP components too; no metadata emitted.
            for info in z.infolist():
                if info.is_dir() or info.filename==product.filename: continue
                with z.open(info) as file:
                    while file.read(65536):pass
    except (BadZipFile,OSError,EOFError,RuntimeError) as exc:
        raise OriginalDWDGateError('invalid DWD archive or ZIP CRC') from exc
    if not first or not last or first>WINDOW_START or last<WINDOW_END or rows<1:
        raise OriginalDWDGateError('DWD original does not bracket Kyrill 2007')
    table=[]
    for day in DAYS:
        x=daily[day]
        if x['observed']>144 or x['missing']>x['observed']:
            raise OriginalDWDGateError('impossible DWD 10min window cardinality')
        table.append({'day_utc':day,
                      'observed_10minute_records':x['observed'],
                      'unobserved_10minute_slots':144-x['observed'],
                      'missing_value_records':x['missing'],
                      'valid_gust_records':x['observed']-x['missing'],
                      'quality_flag_record_counts':dict(sorted(x['qn'].items())),
                      'max_3second_gust_mps_all_quality':str(x['max_all']) if x['max_all'] is not None else None,
                      'max_3second_gust_mps_qn2_or_qn3':str(x['max_qn23']) if x['max_qn23'] is not None else None})
    return {'dwd_station_id':station_id,
            'station_label_candidate':STATIONS[station_id]['name'],
            'original_archive_filename':STATIONS[station_id]['source_filename'],
            'original_archive_sha256':digest,
            'original_archive_bytes':len(raw),
            'full_product_rows':rows,
            'first_original_clock':first.isoformat(),
            'first_source_clock_is_utc':first>=UTC_SOURCE_START,
            'pre_2000_local_clock_prelude_excluded':prelude,
            'last_source_clock_utc':last.isoformat()+'Z',
            'four_day_window_utc':table,
            'fx10_statistic':'MAX_3SECOND_GUST_IN_LAST_10MIN; ORIGINAL_UTC_ENDSTAMP',
            'measuring_height_and_location_in_2007_source_metadata_verified':False,
            'event_attribution_independently_verified':False,
            'observed_building_damage':False}


def compare_munich(*, airport: bytes, city: bytes,
                   airport_sha256: str | None = None, city_sha256: str | None = None) -> dict:
    x=audit_station(airport,station_id='01262',expected_sha256=airport_sha256)
    y=audit_station(city,station_id='03379',expected_sha256=city_sha256)
    if x['original_archive_sha256']==y['original_archive_sha256']:
        raise OriginalDWDGateError('two separately verified original station archives required')
    return {'contract':CONTRACT,
            'status':'TWO_REAL_DWD_STATION_ARCHIVES_WINDOW_RESEARCH_NOT_CALIBRATED',
            'source_directory':SOURCE_DIRECTORY,
            'stations':[x,y],
            'source_archive_sha256_runtime_computed':True,
            'all_original_sources_independently_prior_pinned':False,
            'both_2007_instrument_histories_verified':False,
            'same_measurement_height_verified':False,
            'dwd_vs_climk_spatial_scale_normalized':False,
            'same_historical_storm_attribution_proven':False,
            'reported_2007_munich_maxima_are_insurer_claims':False,
            'fitted_vulnerability':False,'fitted_spatial_damage_dependence':False,
            'annual_AAL':None,'annual_AEP':None,'annual_OEP':None,'annual_event_rate':None}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--airport',type=Path,required=True)
    p.add_argument('--city',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args(argv)
    src=(a.airport.resolve(),a.city.resolve())
    if src[0]==src[1] or any(not item.is_file() or item.is_symlink() for item in (a.airport,a.city)):
        p.error('separate regular original source ZIP paths required')
    if a.output is not None and (a.output.exists() or a.output.resolve() in src):
        p.error('new separate receipt path required')
    report=compare_munich(airport=a.airport.read_bytes(),city=a.city.read_bytes())
    rendered=json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open('x',encoding='utf-8') as f:f.write(rendered)
    else: print(rendered,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
