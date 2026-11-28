#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-locked valid-on-Kyrill 2007 DWD geography + MAX gust sensor histories.

Strictly time-join ORIGINAL station metadata ZIPs for 17-20 January 2007.
The records prove reported station/instrument fields, not measurement accuracy,
wind-field representativeness, measured building losses or annual CAT risk.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from scripts.dwd_kyrill_2007_station_metadata_probe_v0 import (
    STATIONS, inspect_original_metadata, MetadataProbeBlocked,
)

CONTRACT = 'OC_DWD_KYRILL_2007_THREE_STATION_TIME_VALID_SOURCE_HISTORY_V0'
PINNED_SHA = {
    '00433':'8c683f7d01de4461f731bb07837818a1a87ba9c9bbff2f3c4a3774e2730c51f6',
    '01262':'a6c3e4bd40b37f26422a6cda5c0be1ebd760d2f1e3343a368953af44dea2684e',
    '03379':'5525ce5656d1231c5eb0ecbe1b4b482f60b84d41262fa0ff22a1f46643da5da3',
}
EXPECTED_2007 = {
    '00433':('52.4675','13.4021','47.72','10','Windsensor Classic 4.3303'),
    '01262':('48.3574','11.8078','443.60','10','Windsensor Classic 4.3303 (DWDSYN)'),
    '03379':('48.1632','11.5429','515.37','29.28','Windsensor Classic 4.3303'),
}
START='20070117'
END='20070120'

class DWDStationHistoryBlocked(ValueError):
    pass


def _date(value: str) -> str:
    if type(value) is not str or len(value)!=8 or not value.isascii() or not value.isdigit():
        raise DWDStationHistoryBlocked('provider date must be 8-digit YYYYMMDD')
    try: datetime.strptime(value,'%Y%m%d')
    except ValueError as e: raise DWDStationHistoryBlocked('unphysical provider date') from e
    return value


def _number(value: str, low: str, high: str) -> str:
    try: d=Decimal(value.strip())
    except InvalidOperation as e: raise DWDStationHistoryBlocked('invalid station geography or instrument number') from e
    if not d.is_finite() or not Decimal(low)<=d<=Decimal(high):
        raise DWDStationHistoryBlocked('station geography or sensor height out of bound')
    return str(d)


def _rows(z: ZipFile, member: str, header_prefix: tuple[str,...]) -> list[list[str]]:
    try: raw=z.read(member)
    except KeyError as e: raise DWDStationHistoryBlocked('required exact historical metadata TXT member absent') from e
    try: lines=raw.decode('utf-8-sig').splitlines()
    except UnicodeDecodeError: lines=raw.decode('cp1252').splitlines()
    useful=[x for x in lines if x.strip() and not x.startswith(('Legende:', 'generiert:'))]
    if not useful or len(useful)>1000:
        raise DWDStationHistoryBlocked('metadata TXT empty or unbounded')
    hdr=tuple(x.strip() for x in useful[0].split(';'))
    if hdr[:len(header_prefix)] != header_prefix:
        raise DWDStationHistoryBlocked('actual metadata header deviates from reviewed original')
    result=[]
    for line in useful[1:]:
        parts=[x.strip() for x in line.split(';')]
        if len(parts)<len(header_prefix):
            raise DWDStationHistoryBlocked('short metadata row')
        result.append(parts)
    return result


def _on_window(rows: list[list[str]], station: str, idx_from: int, idx_until: int,
               *, subset: str | None = None) -> list[list[str]]:
    chosen=[]
    for r in rows:
        if r[0].zfill(5)!=station:
            raise DWDStationHistoryBlocked('wrong station ID inside original source metadata')
        if subset is not None and r[4]!=subset:
            continue
        first=_date(r[idx_from]);last=_date(r[idx_until]) if r[idx_until] else '99991231'
        if first>last: raise DWDStationHistoryBlocked('reversed DWD station validity interval')
        if first<=START and END<=last:
            chosen.append(r)
    if len(chosen)!=1:
        raise DWDStationHistoryBlocked('missing or multiple full-Kyrill-window source interval rows')
    return chosen


def validate_station_metadata(raw: bytes, *, station: str, override_digest: str | None=None) -> dict:
    if station not in STATIONS: raise DWDStationHistoryBlocked('unknown source station')
    shape=inspect_original_metadata(raw,station=station)
    digest=sha256(raw).hexdigest()
    if digest!=(override_digest if override_digest is not None else PINNED_SHA[station]):
        raise DWDStationHistoryBlocked('original station metadata ZIP SHA256 differs from reviewed provider proof')
    prefix=f'Metadaten_Geographie_{station}.txt'
    sensor=f'Metadaten_Geraete_Windgeschwindigkeit_Maxwind_{station}.txt'
    parameter=f'Metadaten_Parameter_{station}.txt'
    with ZipFile(BytesIO(raw)) as z:
        geo=_on_window(_rows(z,prefix,('Stations_id','Stationshoehe','Geogr.Breite','Geogr.Laenge','von_datum','bis_datum','Stationsname')),
                       station,4,5)[0]
        inst=_on_window(_rows(z,sensor,('Stations_ID','Stationsname','Geo. Laenge [Grad]','Geo. Breite [Grad]',
                                         'Stationshoehe [m]','Geberhoehe ueber Grund [m]','Von_Datum','Bis_Datum','Geraetetyp Name','Messverfahren')),
                       station,6,7)[0]
        param=_on_window(_rows(z,parameter,('Stations_ID','Von_Datum','Bis_Datum','Stationsname','Parameter','Parameterbeschreibung','Einheit')),
                        station,1,2,subset='FX_10')[0]
        got=(_number(geo[2],'-90','90'),_number(geo[3],'-180','180'),
             _number(geo[1],'-500','9000'),_number(inst[5],'0.01','300'),inst[8])
        want=EXPECTED_2007[station]
        if got!=want:
            raise DWDStationHistoryBlocked('reviewed 2007 source geography, sensor height or type changed')
        if (abs(Decimal(inst[2])-Decimal(geo[3]))>Decimal('0.02') or
            abs(Decimal(inst[3])-Decimal(geo[2]))>Decimal('0.02') or
            abs(Decimal(inst[4])-Decimal(geo[1]))>Decimal('0.1')):
            raise DWDStationHistoryBlocked('source instrument and geography inconsistent')
        return {
          'contract':CONTRACT,'station_id':station,
          'source_original_metadata_zip_sha256':digest,
          'source_original_zip_byte_length':len(raw),
          'source_geography_member_sha256':sha256(z.read(prefix)).hexdigest(),
          'source_maxwind_device_member_sha256':sha256(z.read(sensor)).hexdigest(),
          'source_parameter_member_sha256':sha256(z.read(parameter)).hexdigest(),
          'geography_latitude_deg':got[0],'geography_longitude_deg':got[1],
          'geography_station_altitude_m':got[2],
          'maxwind_instrument_sensor_height_over_ground_m':got[3],
          'maxwind_instrument_model':got[4],
          'geography_interval_start':geo[4],'geography_interval_end':geo[5] or None,
          'maxwind_instrument_interval_start':inst[6],'maxwind_instrument_interval_end':inst[7] or None,
          'FX_10_parameter_interval_start':param[1],'FX_10_parameter_interval_end':param[2] or None,
          'valid_for_complete_2007_01_17_through_2007_01_20':True,
          'historical_2007_station_sensor_source_join_verified':override_digest is None,
          'QN1_data_reclassified_as_QN3':False,
          'historical_DWD_observation_QN1_or_QN3_independently_rechecked_here':False,
          'station_point_identical_to_CLIMK_fictional_marker':False,
          'physical_wind_calibrated':False,'vulnerability_calibrated':False,
          'annual_AAL':None,'annual_AEP':None,'annual_OEP':None,
        }


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    for station in STATIONS:p.add_argument('--zip-'+station,required=True,type=Path)
    args=p.parse_args()
    results=[]
    for station in STATIONS:
        path=getattr(args,'zip_'+station)
        if path.is_symlink() or not path.is_file():
            p.error('original metadata must be a regular downloaded ZIP')
        results.append(validate_station_metadata(path.read_bytes(),station=station))
    print(json.dumps({'contract':CONTRACT,'stations':results,'scientific_model_admitted':False},sort_keys=True,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
