# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Replay original DWD station FX_911 observations for the Kyrill 2007 window.

Aggregate-only evidence of DWD observation and metadata coverage; it does not
pair ERA5 or prove hazard-model skill, vulnerability or insured loss.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import ciara2020_dwd_historical_feb2020_station_attestation_v0 as historical
import climk_era5_dwd_50event_station_audit_v0 as audit

MANIFEST=ROOT/"research/observations/kyrill_2007_dwd_station_hourly_source_v0.toml"
START=datetime(2007,1,16,tzinfo=timezone.utc)
HOURS=96
SCHEMA="KYRILL_2007_DWD_FX911_ORIGINAL_STATION_HOURLY_SOURCE_V0"


class KyrillDWDSourceBlocked(ValueError):
    """Original DWD archive, event-window or historical metadata failed gates."""


def _matches_finite_metadata(actual: float, expected: float, tolerance: float) -> bool:
    """Reject nonfinite metadata before comparing against the source receipt."""
    return (math.isfinite(actual) and math.isfinite(expected)
            and abs(actual-expected) <= tolerance)


def _manifest() -> dict:
    with MANIFEST.open("rb") as f:
        data=tomllib.load(f)
    stations=data.get("stations",[])
    if (data.get("schema")!=SCHEMA or data.get("study_window_hours")!=HOURS
        or data.get("study_window_start_utc")!="2007-01-16T00:00:00Z"
        or data.get("study_window_end_utc_inclusive")!="2007-01-19T23:00:00Z"
        or [s.get("station_id") for s in stations]!=["02667","00603"]
        or data.get("dwd_station_list_sha256")!="7183352071fede0bdbe817a542587e75da14f58a4efa01b0ede0dbb34750358c"
        or data.get("dwd_archive_index_sha256")!="fba730a76c1ff7ae0f5f7eda9b22403987d2bb50444983cd3a65a8cd62065696"):
        raise KyrillDWDSourceBlocked("Kyrill DWD source manifest or frozen event window changed")
    for item in stations:
        if (not re.fullmatch(r"stundenwerte_FX_\d{5}_\d{8}_\d{8}_hist\.zip",item.get("archive_file",""))
            or not re.fullmatch(r"[0-9a-f]{64}",item.get("archive_sha256",""))):
            raise KyrillDWDSourceBlocked("malformed DWD original archive identity pin")
    return data


def _sources(opener=None) -> tuple[dict,list[dict]]:
    manifest=_manifest()
    stations_blob=dwd._get_publisher_bytes(dwd.STATION_LIST,dwd.MAX_STATION_LIST,opener)
    index_blob=dwd._get_publisher_bytes(dwd.INDEX,dwd.MAX_INDEX,opener)
    if hashlib.sha256(stations_blob).hexdigest()!=manifest["dwd_station_list_sha256"]:
        raise KyrillDWDSourceBlocked("DWD original station-list bytes differ from pinned source")
    if hashlib.sha256(index_blob).hexdigest()!=manifest["dwd_archive_index_sha256"]:
        raise KyrillDWDSourceBlocked("DWD original archive-index bytes differ from pinned source")
    try:
        html=index_blob.decode("utf-8")
    except UnicodeError as exc:
        raise KyrillDWDSourceBlocked("DWD original archive index is not UTF-8") from exc
    parser=dwd.LinkIndex(); parser.feed(html)
    links=set(parser.links)
    results=[]
    for expected in manifest["stations"]:
        filename=expected["archive_file"]
        if filename not in links:
            raise KyrillDWDSourceBlocked("pinned DWD original archive is absent from official index")
        url=dwd.INDEX+filename
        blob=dwd._get_publisher_bytes(url,dwd.MAX_ZIP,opener)
        digest=hashlib.sha256(blob).hexdigest()
        if digest!=expected["archive_sha256"]:
            raise KyrillDWDSourceBlocked("DWD original station archive SHA differs from source pin")
        station_id=expected["station_id"]
        metadata=audit._rows_from_metadata(blob,station_id)
        observations=audit._parse_original_hourly(blob,station_id)
        geo=audit._covering_by_hour(metadata["geographie"],START,HOURS,"von_datum","bis_datum")
        device=audit._covering_by_hour(metadata["geraete"],START,HOURS,"Von_Datum","Bis_Datum")
        parameter=audit._covering_by_hour(metadata["parameter"],START,HOURS,"Von_Datum","Bis_Datum")
        if (any(row!=geo[0] for row in geo) or any(row!=device[0] for row in device)
            or any(row!=parameter[0] for row in parameter)):
            raise KyrillDWDSourceBlocked("original station, sensor or parameter metadata changes within window")
        g,dev,param=geo[0],device[0],parameter[0]
        try:
            lat=float(g["Geogr.Breite"]); lon=float(g["Geogr.Laenge"])
            elevation=float(g["Stationshoehe"]); height=float(dev["Geberhoehe ueber Grund [m]"])
        except (KeyError,ValueError) as exc:
            raise KyrillDWDSourceBlocked("unparseable original DWD event-era station/sensor metadata") from exc
        if (param.get("Parameter")!="FX_911" or param.get("Zusatz-Info")!="in UTC"
            or param.get("Parameterbeschreibung")!="hoechste Windspitze der letzten Stunde"
            or param.get("Einheit") not in ("m/sec","m/s")
            or not _matches_finite_metadata(lat,expected["historical_latitude"],1e-8)
            or not _matches_finite_metadata(lon,expected["historical_longitude"],1e-8)
            or not _matches_finite_metadata(elevation,expected["historical_station_elevation_m"],0.02)
            or not _matches_finite_metadata(height,expected["historical_anemometer_height_m_agl"],1e-8)):
            raise KyrillDWDSourceBlocked("historical DWD site/device/FX911 UTC semantics differ from pin")
        values=[]
        for index in range(HOURS):
            stamp=(START+timedelta(hours=index)).strftime("%Y%m%d%H")
            if stamp in observations:
                values.append((stamp,*observations[stamp]))
        qn3=[item for item in values if item[2]==3]
        if (len(values)!=expected["expected_valid_hours"]
            or len(qn3)!=expected["expected_qn8_3_hours"]
            or max((v for _,v,_ in values),default=None)!=expected["observed_window_max_gust_mps"]
            or max(values,key=lambda x:x[1])[0]!=datetime.fromisoformat(expected["observed_window_peak_hour_utc"].replace("Z","+00:00")).strftime("%Y%m%d%H")):
            raise KyrillDWDSourceBlocked("DWD event-window aggregate differs from source-attested pin")
        results.append({
            "station_id":station_id,"name":expected["name"],"original_archive_sha256":digest,
            "original_archive_bytes":len(blob),"historical_latitude":lat,
            "historical_longitude":lon,"historical_station_elevation_m":elevation,
            "historical_sensor_height_m_agl":height,
            "historical_FX911_definition":param["Parameterbeschreibung"],
            "historical_hour_label_timezone":param["Zusatz-Info"],
            "valid_FX911_hours_in_96h_window":len(values),"QN8_3_hours_in_window":len(qn3),
            "observed_window_max_gust_mps":max(v for _,v,_ in values),
            "observed_window_peak_hour_utc":datetime.strptime(max(values,key=lambda x:x[1])[0],"%Y%m%d%H").replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z"),
        })
    return manifest,results


def replay(opener=None) -> dict:
    manifest,stations=_sources(opener)
    return {"schema":SCHEMA,"status":"ORIGINAL_DWD_KYRILL_WINDOW_STATION_SOURCE_COVERAGE_ONLY",
            "historical_event":manifest["historical_event"],
            "publisher_event_time_utc":manifest["publisher_event_time_utc"],
            "study_window_start_utc":manifest["study_window_start_utc"],
            "study_window_end_utc_inclusive":manifest["study_window_end_utc_inclusive"],
            "original_DWD_station_list_sha256":manifest["dwd_station_list_sha256"],
            "original_DWD_archive_index_sha256":manifest["dwd_archive_index_sha256"],
            "DWD_original_historical_site_sensor_and_UTC_parameter_verified":True,
            "ERA5_station_hourly_pairing_performed":False,
            "model_skill_or_bias_admitted":False,"loss_or_vulnerability_calibrated":False,
            "stations":stations}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run",action="store_true")
    modes.add_argument("--live-original-dwd",action="store_true")
    args=parser.parse_args()
    try:
        if args.dry_run:
            result={"schema":SCHEMA,"status":"DWD_KYRILL_ORIGINAL_SOURCE_NOT_READ",
                    "source_bytes_retrieved":False,"loss_or_vulnerability_calibrated":False}
        else:
            result=replay()
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (KyrillDWDSourceBlocked,audit.CLIMKDWDBlocked,dwd.OriginalDWDRejected,
            historical.HistoricalDWDNoGo,OSError,ValueError) as exc:
        parser.exit(2,"KYRILL_2007_DWD_SOURCE_NO_GO: "+str(exc)+"\n")


if __name__=="__main__":
    sys.exit(main())
