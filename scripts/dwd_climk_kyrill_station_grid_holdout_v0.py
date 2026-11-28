#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned 2007 DWD stations versus ERA5 grid sampled AT station locations.

Station coordinates are original DWD metadata, NOT synthetic exposure points.
A model's storm-footprint maximum and an observed 10-min FX_10 daily maximum
are different operators; descriptive contrasts do not calibrate model or loss.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha1, sha256
from math import asin, cos, isfinite, radians, sin, sqrt
import json
from pathlib import Path
import re


CONTRACT = 'OC_CLIMK_KYRILL_2007_DWD_STATION_NATIVE_GRID_HOLDOUT_V0'
SOURCE_SHA256 = '92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102'
STORM_INDEX = 0
ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    'history': ('docs/research/evidence/dwd-kyrill-2007-three-station-history-source-receipt-20261106.md',
                '7e87179d21a217d7a9d6f14e998c484865d05321'),
    'berlin': ('docs/research/evidence/dwd-kyrill-2007-berlin-tempelhof-original-fx10-20261106.md',
               '20ac79115e60beb6a8124789cf02956992b39e86'),
    'munich': ('docs/research/evidence/dwd-kyrill-2007-munich-two-stations-original-fx10-20261106.md',
               'dace35c11ac5272797662ea2860bdb768e080462'),
}
STATIONS = {
    '00433': {'lat':'52.4675','lon':'13.4021','height':'10','qn':'1','peak':'33.5',
              'metadata_sha':'8c683f7d01de4461f731bb07837818a1a87ba9c9bbff2f3c4a3774e2730c51f6'},
    '01262': {'lat':'48.3574','lon':'11.8078','height':'10','qn':'1','peak':'33.0',
              'metadata_sha':'a6c3e4bd40b37f26422a6cda5c0be1ebd760d2f1e3343a368953af44dea2684e'},
    '03379': {'lat':'48.1632','lon':'11.5429','height':'29.28','qn':'3','peak':'29.0',
              'metadata_sha':'5525ce5656d1231c5eb0ecbe1b4b482f60b84d41262fa0ff22a1f46643da5da3'},
}
# Fictional locations have NO claim to represent the DWD stations or insurer assets.
MARKERS = {'FICTIONAL_BERLIN': (13.405,52.520,142,78,31090),
           'FICTIONAL_MUNICH': (11.582,48.1351,134,95,33976)}

class GridHoldoutBlocked(ValueError):
    pass


def _git_blob_sha1(content: bytes) -> str:
    return sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()


def _unique(pairs):
    out = {}
    for key, val in pairs:
        if key in out:
            raise GridHoldoutBlocked('duplicate JSON source field')
        out[key] = val
    return out


def parse_source_doc(kind: str, raw: bytes) -> dict:
    if kind not in DOCUMENTS or type(raw) is not bytes or not 100 < len(raw) < 15_000:
        raise GridHoldoutBlocked('missing or unbounded source receipt')
    if _git_blob_sha1(raw) != DOCUMENTS[kind][1]:
        raise GridHoldoutBlocked(f'{kind}: original independent Git blob proof changed')
    try:
        txt = raw.decode('utf-8')
        matches = re.findall(r'(?ms)^```json\n(.*?)\n```$', txt)
        if len(matches) != 1:
            raise GridHoldoutBlocked('exactly one original JSON receipt block required')
        return json.loads(matches[0], object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(GridHoldoutBlocked('invalid numeric literal')))
    except (ValueError, UnicodeError) as exc:
        raise GridHoldoutBlocked('invalid original JSON receipt') from exc


def load_source_docs(base: Path = ROOT) -> dict:
    docs = {}
    for kind, (relative, _) in DOCUMENTS.items():
        p = base / relative
        if not p.is_file() or p.is_symlink():
            raise GridHoldoutBlocked('required recorded source receipt missing')
        docs[kind] = parse_source_doc(kind, p.read_bytes())
    return docs


def _equal(value, expected, label):
    if type(value) is not type(expected) or value != expected:
        raise GridHoldoutBlocked(f'original {label} proof mismatch')


def _peak(day_list, *, station: str, qn: str, key: str) -> str:
    if type(day_list) is not list or len(day_list) != 4:
        raise GridHoldoutBlocked('original DWD four-day source aggregates required')
    for i, item in enumerate(day_list):
        if type(item) is not dict:
            raise GridHoldoutBlocked('invalid DWD daily aggregate')
        _equal(item.get('day_utc'), f'2007-01-{17+i}', 'daily UTC day')
        _equal(item.get('observed_10minute_records'), 144, 'complete-day observations')
        _equal(item.get('valid_gust_records'), 144, 'nonmissing observations')
        _equal(item.get('missing_value_records'), 0, 'missing observations')
        _equal(item.get('unobserved_10minute_slots'), 0, 'missing 10-minute slots')
        _equal(item.get('quality_flag_record_counts'), {qn:144}, 'original QN classification')
    peak = day_list[1].get(key)
    if type(peak) is not str or Decimal(peak) != Decimal(STATIONS[station]['peak']):
        raise GridHoldoutBlocked('original 2007-01-18 measured FX_10 gust mismatch')
    return peak


def verified_station_lines(docs: dict) -> dict:
    if type(docs) is not dict or set(docs) != set(DOCUMENTS):
        raise GridHoldoutBlocked('all three immutable original evidence records needed')
    history = docs['history']
    if (history.get('contract') != 'OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0'
            or history.get('scientific_model_admitted') is not False
            or type(history.get('stations')) is not list or len(history['stations']) != 3):
        raise GridHoldoutBlocked('unverified DWD valid-at-2007 source history')
    out = {}
    for row in history['stations']:
        if type(row) is not dict or type(row.get('station_id')) is not str:
            raise GridHoldoutBlocked('invalid historical DWD station row')
        station = row['station_id']
        if station not in STATIONS or station in out:
            raise GridHoldoutBlocked('unreviewed or duplicate DWD historical station')
        expect = STATIONS[station]
        for key, val in (
            ('geography_latitude_deg',expect['lat']),
            ('geography_longitude_deg',expect['lon']),
            ('maxwind_instrument_sensor_height_over_ground_m',expect['height']),
            ('source_original_metadata_zip_sha256',expect['metadata_sha']),
            ('valid_for_complete_2007_01_17_through_2007_01_20',True),
            ('historical_2007_station_sensor_source_join_verified',True),
            ('QN1_data_reclassified_as_QN3',False),
            ('physical_wind_calibrated',False),
        ):
            _equal(row.get(key),val,station+'.'+key)
        out[station] = {'latitude_deg': float(expect['lat']),
                        'longitude_deg':float(expect['lon']),
                        'sensor_height_m':expect['height'],'original_QN':expect['qn'],
                        'observed_jan18_fx10_max_mps':expect['peak']}
    if set(out) != set(STATIONS):
        raise GridHoldoutBlocked('missing historical station')
    berlin = docs['berlin']; munich = docs['munich']
    _equal(berlin.get('contract'), 'OC_DWD_2007_KYRILL_BERLIN_TEMPELHOF_ORIGINAL_GUST_PREFLIGHT_V0','Berlin gust contract')
    _equal(berlin.get('dwd_station_id'),'00433','Berlin station')
    _equal(berlin.get('original_archive_sha256'),
           '56d4e4d64958ca1dc926af58dabed796c550e2ff4969f81868cfb797b1ed891e','Berlin ZIP')
    _peak(berlin.get('daily_10minute_gust_aggregates'),station='00433',qn='1',
          key='max_3second_gust_within_10minutes_mps_all_quality')
    _equal(munich.get('contract'),'OC_DWD_KYRILL_2007_TWO_MUNICH_STATION_GUST_HOLDOUT_V0','Munich gust contract')
    mrows = munich.get('stations')
    if type(mrows) is not list or len(mrows)!=2:
        raise GridHoldoutBlocked('both Munich observed 2007 sources required')
    expected_sha = {'01262':'ca273211d92b48449c1e92e140a3b6c5b4c99999307aa1ef2fad4fcb6c486fca',
                    '03379':'4a5abf0fdfbf073cee91179f018863e871a496e23199d8c9476d96ff934f0ff7'}
    seen=set()
    for row in mrows:
        if type(row) is not dict or row.get('dwd_station_id') not in expected_sha:
            raise GridHoldoutBlocked('unknown Munich original station')
        sid=row['dwd_station_id']
        if sid in seen:
            raise GridHoldoutBlocked('duplicate Munich station')
        seen.add(sid)
        _equal(row.get('original_archive_sha256'),expected_sha[sid],sid+'.original_gust_sha')
        _peak(row.get('four_day_window_utc'),station=sid,qn=STATIONS[sid]['qn'],
              key='max_3second_gust_mps_all_quality')
    if seen!={'01262','03379'}:
        raise GridHoldoutBlocked('Munich original source missing')
    return out


def _haversine_km(lat1,lon1,lat2,lon2) -> float:
    for val in (lat1,lon1,lat2,lon2):
        if type(val) not in (int,float) or not isfinite(val):
            raise GridHoldoutBlocked('invalid source coordinate')
    if not all((-90<=x<=90 for x in (lat1,lat2))) or not all(-180<=x<=180 for x in (lon1,lon2)):
        raise GridHoldoutBlocked('source latitude/longitude outside globe')
    a = sin(radians(lat2-lat1)/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(radians(lon2-lon1)/2)**2
    return 2*6371.0088*asin(min(1,sqrt(max(0,a))))


def validate_sampled_grid(*, stations: dict, sample: dict) -> dict:
    """Pure tests: sample may be a synthetic fixture; never authenticates NetCDF."""
    if type(stations) is not dict or set(stations)!=set(STATIONS) or type(sample) is not dict:
        raise GridHoldoutBlocked('reviewed 3 station metadata / CLIMK sampler result needed')
    pinned = {'source_sha256':SOURCE_SHA256,'source_storm_name':'KYRILL',
              'source_storm_date_label':'20070118',
              'source_storm_index_zero_based':0,
              'source_event_key':'climk-winds:v2:ERA5:storm-index:0',
              'physical_intensity_unit':'m s**-1',
              'source_points_sampled':5}
    for key, val in pinned.items():
        _equal(sample.get(key),val,'CLIMK '+key)
    items=sample.get('samples')
    if type(items) is not list or len(items)!=5:
        raise GridHoldoutBlocked('exactly five original sampled points required')
    expected_points={f'DWD_{sid}':(x['longitude_deg'],x['latitude_deg']) for sid,x in stations.items()}
    expected_points.update({name:(m[0],m[1]) for name,m in MARKERS.items()})
    received={}
    for row in items:
        if type(row) is not dict or set(row)!={'point_id','longitude_deg','latitude_deg',
                'native_cell_x','native_cell_y','grid_center_lon_deg','grid_center_lat_deg',
                'original_era5_storm_gust_mps'}:
            raise GridHoldoutBlocked('original native site sample lacks exact fields')
        name=row['point_id']
        if name not in expected_points or name in received:
            raise GridHoldoutBlocked('unknown/duplicated original station or fictional marker')
        lon,lat=expected_points[name]
        for field, value in (('longitude_deg',lon),('latitude_deg',lat)):
            _equal(row.get(field),value,'point geography '+name+'.'+field)
        ix=row['native_cell_x'];iy=row['native_cell_y'];gust=row['original_era5_storm_gust_mps']
        if (type(ix) is not int or not 0<=ix<269 or type(iy) is not int or not 0<=iy<181
                or type(gust) not in (int,float) or not isfinite(gust) or not 0<=gust<=200):
            raise GridHoldoutBlocked('invalid ERA5 cell or modelled maximum gust')
        km=_haversine_km(lat,lon,row['grid_center_lat_deg'],row['grid_center_lon_deg'])
        if km>80:
            raise GridHoldoutBlocked('native station-to-grid-centre distance implausible')
        if name in MARKERS:
            marker=MARKERS[name]
            mm=int((Decimal(str(gust))*1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            if (ix,iy,mm)!=(marker[2],marker[3],marker[4]):
                raise GridHoldoutBlocked('original fictional source marker drift')
        received[name]={'cell':(ix,iy),'gust':gust,'distance_km':round(km,3)}
    if set(received)!=set(expected_points):
        raise GridHoldoutBlocked('missing expected original native sampling point')
    out=[]
    for sid in STATIONS:
        p=received['DWD_'+sid];obs=stations[sid]
        marker_name='FICTIONAL_BERLIN' if sid=='00433' else 'FICTIONAL_MUNICH'
        marker=received[marker_name]
        out.append({'dwd_station_id':sid,
                    'source_station_lon_deg':obs['longitude_deg'],
                    'source_station_lat_deg':obs['latitude_deg'],
                    'original_sensor_height_m':obs['sensor_height_m'],
                    'source_observation_quality_level':obs['original_QN'],
                    'observed_DWD_2007_01_18_max_3s_10min_gust_mps':obs['observed_jan18_fx10_max_mps'],
                    'era5_native_cell_x':p['cell'][0],'era5_native_cell_y':p['cell'][1],
                    'era5_grid_cell_center_distance_km':p['distance_km'],
                    'era5_original_kyrill_storm_footprint_max_gust_mps':str(Decimal(str(p['gust'])).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP)),
                    'in_same_era5_cell_as_fictional_city_marker':p['cell']==marker['cell'],
                    'fictional_marker_gust_mps':str(Decimal(str(marker['gust'])).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP)),
                    'descriptive_DWD_minus_ERA5_mps_not_validated_bias':str(Decimal(obs['observed_jan18_fx10_max_mps'])-Decimal(str(p['gust'])).quantize(Decimal('0.001'),rounding=ROUND_HALF_UP)),
                    'same_wind_measurement_operator_validated':False,
                    'height_or_roughness_normalized':False,
                    'observed_building_claims':False,
                    'science_admitted_for_wind_model_calibration':False})
    return {'contract':CONTRACT,
            'status':'REAL_DWD_STATION_COORDINATES_SAMPLED_IN_CLIMK_ERA5_KYRILL_NOT_CALIBRATION',
            'source_era5_sha256':SOURCE_SHA256,
            'source_dwd_metadata_proofs_git_blobs':{k:v[1] for k,v in DOCUMENTS.items()},
            'station_to_grid_results':out,
            'real_dwd_stations':3,'fictional_comparison_markers':2,
            'era5_sample_original_bytes_verified_in_this_pure_function':False,
            'same_physical_wind_operator_established':False,
            'wind_model_bias_calibrated':False,
            'vulnerability_calibrated':False,
            'annual_event_rate':None,'annual_AAL':None,'annual_AEP':None,'annual_OEP':None}


def sample_original_era5_station_points(original: bytes, stations: dict) -> dict:
    """Use DWD REAL coordinates directly; never pass them as synthetic assets."""
    from scripts.climk_era5_synthetic_native_sample_v0 import (
        nearest_native_cell, _source_storm_label, _safe_variable_value,
    )
    from scripts.inspect_climk_winds_era5_v0 import (
        EXPECTED_DIMENSIONS, inspect_netcdf_header, verify_source_bytes,
    )
    if type(original) is not bytes or sha256(original).hexdigest()!=SOURCE_SHA256:
        raise GridHoldoutBlocked('original ERA5 bytes differ from exact source SHA256')
    verify_source_bytes(original, require_sha256=True)
    if inspect_netcdf_header(original)['dimensions']!=EXPECTED_DIMENSIONS:
        raise GridHoldoutBlocked('CLIMK native grid dimensions changed')
    try:
        from netCDF4 import Dataset
    except ImportError as e:
        raise GridHoldoutBlocked('netCDF4 original source reader required') from e
    wanted={f'DWD_{sid}':(x['longitude_deg'],x['latitude_deg']) for sid,x in stations.items()}
    wanted.update({name:(p[0],p[1]) for name,p in MARKERS.items()})
    with Dataset('climk-era5-original',mode='r',memory=original) as ds:
        lons=tuple(float(x) for x in ds.variables['longitude'][:])
        lats=tuple(float(x) for x in ds.variables['latitude'][:])
        name=_source_storm_label(ds.variables['Storm_Names'][STORM_INDEX],'Storm_Names')
        date=_source_storm_label(ds.variables['Storm_Dates'][STORM_INDEX],'Storm_Dates')
        gust=ds.variables['absolute_maxwindgusts']
        samples=[]
        for ident,(lon,lat) in sorted(wanted.items()):
            ix,cx=nearest_native_cell(lons,lon)
            iy,cy=nearest_native_cell(lats,lat)
            value=_safe_variable_value(gust[STORM_INDEX,iy,ix],'source maximum gust',200.0)
            samples.append({'point_id':ident,'longitude_deg':lon,'latitude_deg':lat,
                            'native_cell_x':ix,'native_cell_y':iy,
                            'grid_center_lon_deg':cx,'grid_center_lat_deg':cy,
                            'original_era5_storm_gust_mps':value})
    return {'source_sha256':SOURCE_SHA256,'source_storm_name':name,
            'source_storm_date_label':date,'source_storm_index_zero_based':STORM_INDEX,
            'source_event_key':'climk-winds:v2:ERA5:storm-index:0',
            'physical_intensity_unit':'m s**-1',
            'source_points_sampled':len(samples),'samples':samples}


def run_live() -> dict:
    stations=verified_station_lines(load_source_docs())
    from scripts.inspect_climk_winds_era5_v0 import fetch_provider_bytes
    original=fetch_provider_bytes()
    sample=sample_original_era5_station_points(original,stations)
    result=validate_sampled_grid(stations=stations,sample=sample)
    result['era5_sample_original_bytes_verified_in_this_pure_function']=True
    result['original_dwd_measurement_and_metadata_receipts_git_blob_authenticated']=True
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    result=run_live()
    wire=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if args.out is None:
        print(wire,end='')
    else:
        if args.out.exists():
            ap.error('refusing to overwrite existing DWD/CLIMK source comparison evidence')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x',encoding='utf-8') as f:f.write(wire)

if __name__=='__main__': main()
