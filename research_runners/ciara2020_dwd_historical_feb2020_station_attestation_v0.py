# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Attest actual Feb-2020 DWD station coordinates, wind instrument and FX UTC.

SOURCE: three real DWD-CDC historical hourly FX_911 station ZIPs
SHA-pinned by the independently accepted 2020 original-source receipt.
Check original geography, anemometer and FX parameter member byte SHA,
then select EXACTLY ONE row valid throughout Feb 8-11, 2020.
Do not equate DWD measured last-hour peak with modelled ERA5 postprocessed
gust on a different spatial support or calibrate insured wind damage.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import tomllib
import zipfile

import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import ciara2020_dwd_original_2020_station_metadata_inventory_v0 as inventory
import ciara2020_dwd_original_to_era5_station_peak_comparison_v0 as comparison
import ciara2020_google_arco_real_96h_nrw_area_v0 as era5

SCHEMA="CIARA2020_DWD_ORIGINAL_2020_STATION_GEO_INSTRUMENT_UTC_FX911_ATTESTATION_V0"
ORIGINAL_RESEARCH = (
    Path(__file__).resolve().parents[1] /
    "research/observations/ciara2020_dwd_original_historical_station_metadata_attestation_20261114.toml"
)
FIRST="20200208"
LAST="20200211"
SUPPORTED_IDS=("02667","15200","00603")


class HistoricalDWDNoGo(ValueError):
    """Unverified source date-range, station, instrument or time convention."""


def _metadata_rows(content: bytes, kind: str, station_id: str) -> list[dict]:
    if len(content) > inventory.MAX_SINGLE_METADATA_BYTES:
        raise HistoricalDWDNoGo("original DWD member over source size cap")
    try:
        text=content.decode("cp1252")
    except UnicodeError as exc:
        raise HistoricalDWDNoGo("DWD original member invalid character encoding") from exc
    records=list(csv.reader(io.StringIO(text, newline=""),delimiter=";",strict=True))
    if not records:
        raise HistoricalDWDNoGo("missing DWD original metadata header")
    head=[h.strip() for h in records[0]]
    if head and head[-1]=="":
        head.pop()
    expected={
        "geographie":("Stations_id","Stationshoehe","Geogr.Breite","Geogr.Laenge","von_datum","bis_datum","Stationsname"),
        "geraete":("Stations_ID","Stationsname","Geo. Laenge [Grad]","Geo. Breite [Grad]","Stationshoehe [m]","Geberhoehe ueber Grund [m]","Von_Datum","Bis_Datum","Geraetetyp Name","Messverfahren","eor"),
        "parameter":("Stations_ID","Von_Datum","Bis_Datum","Stationsname","Parameter","Parameterbeschreibung","Einheit","Datenquelle (Strukturversion=SV)","Zusatz-Info","Besonderheiten","Literaturhinweis","eor"),
    }
    if tuple(head) != expected[kind]:
        raise HistoricalDWDNoGo("DWD publisher original historical metadata schema changed")
    parsed=[]
    for row in records[1:]:
        stripped=[v.strip() for v in row]
        if stripped and stripped[-1]=="":
            stripped.pop()
        # Ignore original footer / legend, NOT arbitrary malformed
        # records claiming the real source station identity.
        if not stripped or not re.fullmatch(r"\d{1,5}",stripped[0]):
            continue
        if len(stripped)!=len(head):
            raise HistoricalDWDNoGo("incomplete original DWD historical metadata row")
        if int(stripped[0]) != int(station_id):
            raise HistoricalDWDNoGo("embedded metadata source station ID mismatch")
        parsed.append(dict(zip(head,stripped)))
    if not parsed:
        raise HistoricalDWDNoGo("missing original DWD station historical metadata data rows")
    return parsed


def _active_unique(rows:list[dict], begin_field:str, end_field:str) -> dict:
    hits=[]
    for row in rows:
        start=row[begin_field]
        end=row[end_field] or "99991231"
        if not re.fullmatch(r"\d{8}",start) or not re.fullmatch(r"\d{8}",end):
            raise HistoricalDWDNoGo("source original from/to date format ambiguous")
        if start>end:
            raise HistoricalDWDNoGo("source original metadata interval inverted")
        if start<=FIRST and end>=LAST:
            hits.append(row)
    if len(hits)!=1:
        raise HistoricalDWDNoGo("not exactly one original geography/instrument/parameter record spanning all Ciara2020 days")
    return hits[0]


def _safe_decimal(text: str) -> float:
    try:
        value=float(text)
    except (ValueError, TypeError) as exc:
        raise HistoricalDWDNoGo("original DWD geography/sensor numeric metadata invalid") from exc
    if not math.isfinite(value):
        raise HistoricalDWDNoGo("nonfinite source historical DWD coordinate or sensor height")
    return value


def attest_original_zip(station_id: str, original_zip: bytes, pinned_station: dict) -> dict:
    if station_id not in SUPPORTED_IDS or pinned_station.get("station_id") != station_id:
        raise HistoricalDWDNoGo("original source station identity changed")
    proof=inventory.inspect_original_metadata_zip(original_zip,station_id)
    if proof["original_archive_sha256"] != pinned_station.get("original_zip_sha256"):
        raise HistoricalDWDNoGo("DWD original 2020 ZIP SHA differs from independently reviewed original")
    with zipfile.ZipFile(io.BytesIO(original_zip)) as z:
        texts={}
        for kind in inventory.REQUIRED_CATEGORIES:
            metadata=proof["metadata"][kind]
            name=metadata["original_member_name"]
            if metadata["original_member_sha256"] != pinned_station.get(kind.replace("geographie","geo").replace("geraete","device") + "_member_sha256" if kind != "parameter" else "parameter_member_sha256"):
                raise HistoricalDWDNoGo("original DWD historical source member SHA mismatch")
            texts[kind]=z.read(name)
    geo=_active_unique(_metadata_rows(texts["geographie"],"geographie",station_id),"von_datum","bis_datum")
    device=_active_unique(_metadata_rows(texts["geraete"],"geraete",station_id),"Von_Datum","Bis_Datum")
    param=_active_unique(_metadata_rows(texts["parameter"],"parameter",station_id),"Von_Datum","Bis_Datum")
    if (param.get("Parameter")!="FX_911"
        or param.get("Zusatz-Info")!="in UTC"
        or param.get("Parameterbeschreibung")!="hoechste Windspitze der letzten Stunde"
        or param.get("Einheit") not in ("m/sec","m/s")
        or device.get("Messverfahren")!="Windmessung, elektr."
        or device.get("eor")!="eor"
        or param.get("eor")!="eor"):
        raise HistoricalDWDNoGo("official February 2020 FX911 gust UTC unit/measurement source is not attested")
    lat=_safe_decimal(geo["Geogr.Breite"])
    lon=_safe_decimal(geo["Geogr.Laenge"])
    site_elev=_safe_decimal(geo["Stationshoehe"])
    instrument_elev=_safe_decimal(device["Geberhoehe ueber Grund [m]"])
    if (not 49 <= lat <= 54 or not 5.5 <= lon <= 10.5
        or not 0 <= site_elev <= 2000
        or not 1 <= instrument_elev <= 150):
        raise HistoricalDWDNoGo("unphysical original historical DWD station geometry/height")
    if (abs(_safe_decimal(device["Geo. Breite [Grad]"])-lat)>.03
        or abs(_safe_decimal(device["Geo. Laenge [Grad]"])-lon)>.03
        or abs(_safe_decimal(device["Stationshoehe [m]"])-site_elev)>2):
        raise HistoricalDWDNoGo("historical DWD device geography and station geography disagree")
    row,col,distance=comparison.station_to_grid(lat,lon)
    result={
        "station_id":station_id,
        "original_DWD_station_latitude_as_of_Feb2020":lat,
        "original_DWD_station_longitude_as_of_Feb2020":lon,
        "original_DWD_station_elevation_m_as_of_Feb2020":site_elev,
        "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":instrument_elev,
        "original_FX911_instrument_type_as_of_Feb2020":device["Geraetetyp Name"],
        "original_FX911_procedure_as_of_Feb2020":device["Messverfahren"],
        "original_DWD_FX911_unit":"m/s",
        "original_DWD_FX911_hour_label_declared_UTC":True,
        "original_DWD_FX911_gust_highest_during_previous_hour":True,
        "original_geo_interval_from":geo["von_datum"],
        "original_geo_interval_to":geo["bis_datum"] or None,
        "original_instrument_interval_from":device["Von_Datum"],
        "original_instrument_interval_to":device["Bis_Datum"] or None,
        "original_parameter_interval_from":param["Von_Datum"],
        "original_parameter_interval_to":param["Bis_Datum"] or None,
        "nearest_2020_ERA5_grid_lat":era5.LATITUDE[row],
        "nearest_2020_ERA5_grid_lon":era5.LONGITUDE[col],
        "historical_station_to_ERA5_grid_centre_km":distance,
        "DWD_original_zip_sha256":proof["original_archive_sha256"],
        "historical_member_sha256":{k:v["original_member_sha256"] for k,v in proof["metadata"].items()},
        "DWD_FX911_exact_same_postprocess_window_as_ERA5_10fg_verified":False,
        "observed_German_insurer_loss_or_vulnerability_calibrated":False,
    }
    compare={
        "original_DWD_station_latitude_as_of_Feb2020":"feb2020_latitude",
        "original_DWD_station_longitude_as_of_Feb2020":"feb2020_longitude",
        "original_DWD_station_elevation_m_as_of_Feb2020":"feb2020_station_elevation_m",
        "original_FX911_anemometer_height_above_ground_m_as_of_Feb2020":"feb2020_wind_anemometer_height_above_ground_m",
        "original_FX911_instrument_type_as_of_Feb2020":"feb2020_instrument_type",
        "original_FX911_procedure_as_of_Feb2020":"feb2020_measurement_procedure",
        "original_geo_interval_from":"feb2020_geo_valid_from",
        "original_instrument_interval_from":"feb2020_device_valid_from",
        "original_parameter_interval_from":"feb2020_parameter_valid_from",
        "nearest_2020_ERA5_grid_lat":"2020_original_era5_comparison_grid_lat",
        "nearest_2020_ERA5_grid_lon":"2020_original_era5_comparison_grid_lon",
        "historical_station_to_ERA5_grid_centre_km":"nearest_original_era5_grid_distance_km",
    }
    if any(result[k]!=pinned_station.get(v) for k,v in compare.items()):
        raise HistoricalDWDNoGo("DWD real 2020 original site/height/metadata source differs from first independently reviewed live evidence")
    for key in ("feb2020_geo_valid_to","feb2020_device_valid_to"):
        if key in pinned_station:
            source_key="original_geo_interval_to" if "geo" in key else "original_instrument_interval_to"
            if result[source_key]!=pinned_station[key]:
                raise HistoricalDWDNoGo("source original 2020 sensor/site interval closed at wrong date")
    if param["Zusatz-Info"]!=pinned_station.get("feb2020_hour_reference") or param["Parameterbeschreibung"]!=pinned_station.get("feb2020_gust_reference"):
        raise HistoricalDWDNoGo("original FX UTC/hour definition changed")
    return result


def live_feb2020_attestation() -> dict:
    with ORIGINAL_RESEARCH.open("rb") as f:
        accepted=tomllib.load(f)
    if (accepted.get("schema")!=SCHEMA
        or accepted.get("first_original_metadata_github_run_id")!=43605892890
        or accepted.get("source_original_metadata_unmodified_shas_pinned") is not True
        or accepted.get("source_original_DWD_FX911_UTC_reference_hour_label_attested") is not True
        or accepted.get("ERA5_10fg_time_support_aggregation_equal_to_DWD_FX911_verified") is not False
        or accepted.get("DWD_to_ERA5_same_hour_model_bias_or_RMSE_approved") is not False
        or accepted.get("real_2020_RV_insurer_claims_or_insured_sites_observed") is not False):
        raise HistoricalDWDNoGo("pinned original DWD 2020 research receipt changed")
    records=accepted["stations"]
    if len(records)!=3 or [r["station_id"] for r in records]!=list(SUPPORTED_IDS):
        raise HistoricalDWDNoGo("frozen original 2020 source station population changed")
    data=[]
    with dwd.FROZEN_FIRST_REAL_DWD_SOURCE.open("rb") as f:
        first_dwd=tomllib.load(f)
    for record,original in zip(records,first_dwd["stations"]):
        if (original["station_id"]!=record["station_id"]
            or original["original_unmodified_zip_sha256"]!=record["original_zip_sha256"]):
            raise HistoricalDWDNoGo("2020 site provenance not same accepted original DWD ZIP source")
        raw=dwd._get_publisher_bytes(original["original_archive_url"],dwd.MAX_ZIP)
        data.append(attest_original_zip(record["station_id"],raw,record))
    if [x["nearest_2020_ERA5_grid_lat"] for x in data]!=[50.75,51.25,50.75]:
        raise HistoricalDWDNoGo("old 2020 actual grid support has changed")
    return {
        "schema":SCHEMA,
        "status":"ORIGINAL_DWD_FX911_FEB2020_HISTORIC_SITE_SENSOR_HEIGHT_AND_UTC_LABEL_SOURCE_ATTESTED",
        "DWD_original_source_rights":"CC BY 4.0; DWD attribution required",
        "station_count":3,
        "stations":data,
        "DWD_original_site_geography_Feb2020_verified":True,
        "DWD_original_sensor_height_type_Feb2020_verified":True,
        "DWD_original_FX911_hour_reference_declared_UTC":True,
        "DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same":False,
        "ERA5_station_matched_hour_bias_or_RMSE_approved":False,
        "insurer_real_2020_loss_vulnerability_GUL_IL_RI_OEP_AEP_admitted":False,
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    choices=parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--dry-run",action="store_true")
    choices.add_argument("--live-feb2020-attestation",action="store_true")
    args=parser.parse_args()
    try:
        if args.dry_run:
            result={
                "schema":SCHEMA,
                "expected_DWD_station_count":3,
                "actual_original_source_archives_retrieved":False,
                "historical_site_sensor_hour_UTC_attested_by_this_run":False,
                "insurer_loss_model_approved":False,
            }
        else:
            result=live_feb2020_attestation()
        print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=True))
        return 0
    except (HistoricalDWDNoGo,inventory.DWDMetadataBlocked,
            dwd.OriginalDWDRejected,comparison.DWDGridComparisonBlocked,
            OSError,ValueError) as exc:
        parser.exit(2,"CIARA2020_DWD_HISTORICAL_FEB2020_SITE_INSTRUMENT_UTC_NO_GO: "+str(exc)+"\n")


if __name__=="__main__":
    sys.exit(main())
