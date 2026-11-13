# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read original quality-checked DWD hourly FX_911 gusts for Ciara 2020.

DWD CDC publicly distributes historical *measured* hourly station gusts
under CC BY 4.0 (DWD attribution). This is deliberately distinct from
Google ARCO ERA5 *reanalysis*, weather-station siting/move uncertainty,
and fictional HU2022 building exposure. NO insurer loss/calibration.
Read only official DWD host paths; never publish source zip or site data.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
import hashlib
from html.parser import HTMLParser
import io
import json
from math import asin, cos, isfinite, radians, sin, sqrt
from pathlib import Path
import re
import tomllib
import sys
from urllib import error, request
import zipfile

ROOT = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/extreme_wind/"
INDEX = ROOT + "historical/"
STATION_LIST = INDEX + "FX_Stundenwerte_Beschreibung_Stationen.txt"
DWD_RIGHTS = "https://opendata.dwd.de/climate_environment/CDC/Nutzungsbedingungen_German.txt"
DWD_FORMAT = ROOT + "BESCHREIBUNG_obsgermany_climate_hourly_extreme_wind_de.pdf"
SCHEMA = "CIARA2020_DWD_CDC_ORIGINAL_HOURLY_FX911_3_NRW_STATIONS_V0"
EVENT_START = datetime(2020, 2, 8, 0)
HOURS = 96
EVENT_END = EVENT_START + timedelta(hours=HOURS - 1)
# Select 3 nearest *publisher-listed currently located* stations to the
# independently sampled 2020 Google ERA5 grid centre 51N/7E.
TARGET_LAT = 51.0
TARGET_LON = 7.0
MAX_STATIONS = 3
MAX_CANDIDATE_ARCHIVES = 12
MAX_RADIUS_KM = 120.0
MAX_STATION_LIST = 900_000
MAX_INDEX = 450_000
MAX_ZIP = 2_000_000
MAX_UNCOMPRESSED = 25_000_000
MIN_REPORTED_HOURS = 48
ZIP_RE = re.compile(r"^stundenwerte_FX_(\d{5})_(\d{8})_(\d{8})_hist\.zip$")
STATION_LINE = re.compile(
    r"^\s*(\d{5})\s+(\d{8})\s+(\d{8})\s+(-?\d{1,5})\s+"
    r"(\d{1,2}\.\d{2,6})\s+(\d{1,2}\.\d{2,6})\s+(.+)$"
)
EXPECTED_COLUMNS = {"STATIONS_ID", "MESS_DATUM", "QN_8", "FX_911"}


class OriginalDWDRejected(ValueError):
    """The publisher-original measured 2020 gust evidence did not pass."""


class NoRedirects(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OriginalDWDRejected("DWD original-source redirect is disallowed")


class LinkIndex(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attr = dict(attrs)
        href = attr.get("href")
        if isinstance(href, str):
            self.links.append(href)


def _get_publisher_bytes(url: str, max_bytes: int, opener=None) -> bytes:
    if (url not in (STATION_LIST, INDEX)
        and not (url.startswith(INDEX) and ZIP_RE.fullmatch(url[len(INDEX):]))):
        raise OriginalDWDRejected("only exact publicly published DWD CDC FX archive URLs admitted")
    if max_bytes not in (MAX_STATION_LIST, MAX_INDEX, MAX_ZIP):
        raise OriginalDWDRejected("bounded DWD source HTTP bytes required")
    opener = opener or request.build_opener(NoRedirects())
    try:
        with opener.open(request.Request(
            url, headers={"User-Agent": "OpenCatastrophe-DWD-FX911-source-v0"}
        ), timeout=18) as r:
            if r.status != 200:
                raise OriginalDWDRejected("DWD historical original response is not HTTP 200")
            blob = r.read(max_bytes + 1)
    except (TimeoutError, OSError, error.URLError) as exc:
        raise OriginalDWDRejected("original DWD public host could not be read") from None
    if not 40 <= len(blob) <= max_bytes:
        raise OriginalDWDRejected("publisher original metadata/archive too small or oversized")
    return blob


def haversine_km(lat: float, lon: float) -> float:
    """Distance to independent 51N,7E ERA5 point, not a station/ERA5 equality."""
    a, b = radians(lat), radians(lon)
    c, d = radians(TARGET_LAT), radians(TARGET_LON)
    alpha = sin((c - a) / 2) ** 2 + cos(a) * cos(c) * sin((d - b) / 2) ** 2
    return 2 * 6371.0088 * asin(min(1.0, sqrt(alpha)))


def station_candidates(station_description: bytes) -> list[dict]:
    try:
        source = station_description.decode("cp1252")
    except UnicodeError as exc:
        raise OriginalDWDRejected("DWD station list has unexpected text encoding") from exc
    result = {}
    for line in source.splitlines():
        m = STATION_LINE.match(line)
        if not m:
            continue
        station_id, start, end, altitude, lat_s, lon_s, name = m.groups()
        if not start <= "20200208" <= "20200211" <= end:
            continue
        lat, lon = float(lat_s), float(lon_s)
        if not (50.0 <= lat <= 52.75 and 5.5 <= lon <= 9.75):
            continue
        distance = haversine_km(lat, lon)
        if distance > MAX_RADIUS_KM:
            continue
        if station_id in result:
            raise OriginalDWDRejected("DWD original station identity appeared more than once")
        result[station_id] = {
            "station_id": station_id,
            "name_as_publisher_lists_today": name.strip()[:120],
            "latitude_as_publisher_lists_today": lat,
            "longitude_as_publisher_lists_today": lon,
            "height_as_publisher_lists_today_m": int(altitude),
            "distance_to_original_era5_51N_7E_km": round(distance, 3),
        }
    if len(result) < MAX_STATIONS:
        raise OriginalDWDRejected("too few geographically eligible historical 2020 DWD stations")
    return sorted(result.values(),
                  key=lambda x: (x["distance_to_original_era5_51N_7E_km"],
                                 x["station_id"]))


def historical_zip_links(index_html: bytes) -> dict[str, str]:
    try:
        doc = index_html.decode("utf-8")
    except UnicodeError as exc:
        raise OriginalDWDRejected("invalid DWD original archive directory") from exc
    parser = LinkIndex()
    parser.feed(doc)
    archives = {}
    for link in parser.links:
        m = ZIP_RE.fullmatch(link)
        if not m or not m[2] <= "20200208" <= "20200211" <= m[3]:
            continue
        if m[1] in archives:
            raise OriginalDWDRejected("ambiguous multiple original FX historical archives")
        archives[m[1]] = INDEX + link
    if len(archives) < MAX_STATIONS:
        raise OriginalDWDRejected("no original 2020 historical DWD FX archives available")
    return archives


def measured_2020_gust_from_original_zip(blob: bytes, station_id: str) -> dict:
    if not re.fullmatch(r"\d{5}", station_id):
        raise OriginalDWDRejected("station id must exactly match official 5-digit station ID")
    original_sha = hashlib.sha256(blob).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            parts = archive.infolist()
            if (not 1 <= len(parts) <= 40
                or any(not info.filename or info.file_size > MAX_UNCOMPRESSED
                       or info.flag_bits & 1 or "../" in info.filename or
                       info.filename.startswith(("/", "\\")) for info in parts)
                or sum(info.file_size for info in parts) > MAX_UNCOMPRESSED):
                raise OriginalDWDRejected("archive contains unbounded or ambiguous original members")
            products = [info for info in parts if info.filename.lower().startswith("produkt_")
                        and info.filename.endswith(".txt")]
            if len(products) != 1:
                raise OriginalDWDRejected("exactly one original DWD hourly FX product required")
            source = archive.read(products[0]).decode("cp1252")
    except (zipfile.BadZipFile, UnicodeError, RuntimeError, OSError) as exc:
        raise OriginalDWDRejected("DWD original ZIP/product unreadable") from exc
    reader = csv.DictReader(io.StringIO(source, newline=""), delimiter=";", strict=True)
    fieldnames = [x.strip() for x in (reader.fieldnames or [])]
    if (set(fieldnames) not in (EXPECTED_COLUMNS, EXPECTED_COLUMNS | {"eor"})
        or len(fieldnames) not in (4, 5)):
        raise OriginalDWDRejected("unexpected DWD hourly FX source schema")
    # DWD normally contains padded columns and sometimes an empty trailing
    # column; reject that silently misaligned structure in an actual run
    # rather than substituting mean speed or reinterpreting a marker.
    expected_timestamps = {
        (EVENT_START + timedelta(hours=i)).strftime("%Y%m%d%H")
        for i in range(HOURS)
    }
    valid, invalid, qn_counts, all_seen = {}, 0, {}, set()
    for row in reader:
        record = {k.strip(): v.strip() for k, v in row.items()
                  if k is not None and v is not None}
        day = record.get("MESS_DATUM", "")
        if day not in expected_timestamps:
            continue
        if day in all_seen:
            raise OriginalDWDRejected("duplicate original station hourly timestamp")
        all_seen.add(day)
        if record.get("STATIONS_ID", "").zfill(5) != station_id:
            raise OriginalDWDRejected("ZIP filename / embedded station original ID mismatch")
        try:
            gust = float(record["FX_911"])
            qn = int(record["QN_8"])
        except (ValueError, KeyError) as exc:
            raise OriginalDWDRejected("unparseable original DWD measured FX_911") from exc
        if not 0 <= qn <= 10:
            raise OriginalDWDRejected("unsupported DWD QN_8 quality code")
        if "eor" in fieldnames and record.get("eor", "").strip().lower() not in ("", "eor"):
            raise OriginalDWDRejected("unexpected DWD original product end-of-record marker")
        qn_counts[str(qn)] = qn_counts.get(str(qn), 0) + 1
        # DWD missing value = -999; do not silently replace with zero.
        if gust == -999.0:
            invalid += 1
        elif not (isfinite(gust) and 0 <= gust <= 150):
            raise OriginalDWDRejected("original DWD station gust invalid/outside physical bound")
        else:
            valid[day] = gust
    if len(valid) < MIN_REPORTED_HOURS:
        raise OriginalDWDRejected("original DWD 2020 FX_911 hour coverage too sparse")
    if any(day not in expected_timestamps for day in valid):
        raise OriginalDWDRejected("DWD station observation not in original historical study window")
    return {
        "provider_original_zip_sha256": original_sha,
        "exact_original_station_product_member": products[0].filename,
        "original_station_fx911_hourly_valid_count": len(valid),
        "original_station_fx911_missing_marker_count": invalid,
        "original_station_fx911_unreported_hour_count": HOURS - len(all_seen),
        "DWD_QN8_quality_level_hour_counts": qn_counts,
        "measured_2020_02_08_through_11_max_hourly_gust_mps": max(valid.values()),
        "measured_2020_Ciara_window_peak_hour_as_publisher_reports": min(
            hour for hour, gust in valid.items() if gust == max(valid.values())
        ),
        "observed_station_max_gust_hours_full_96h": len(valid) == HOURS,
    }


def live_dwd_2020_original_three_stations(*, opener=None) -> dict:
    station_bytes = _get_publisher_bytes(STATION_LIST, MAX_STATION_LIST, opener)
    html = _get_publisher_bytes(INDEX, MAX_INDEX, opener)
    stations = station_candidates(station_bytes)
    links = historical_zip_links(html)
    chosen = [station for station in stations if station["station_id"] in links][:MAX_CANDIDATE_ARCHIVES]
    if len(chosen) < MAX_STATIONS:
        raise OriginalDWDRejected("three eligible original 2020 station archives are required")
    reports = []
    skipped_incomplete_stations = []
    for station in chosen:
        original_url = links[station["station_id"]]
        zip_blob = _get_publisher_bytes(original_url, MAX_ZIP, opener)
        try:
            measured = measured_2020_gust_from_original_zip(zip_blob, station["station_id"])
        except OriginalDWDRejected as exc:
            # A historical archive *covers the date range* but the original
            # 2020 hourly gust product can be too sparse. Record that
            # explicitly, reject it, and try the next nearest original
            # candidate. Do NOT bypass malformed ZIP, source-ID or QN flags.
            if str(exc) != "original DWD 2020 FX_911 hour coverage too sparse":
                raise
            skipped_incomplete_stations.append({
                "original_station_id": station["station_id"],
                "original_station_zip_sha256": hashlib.sha256(zip_blob).hexdigest(),
                "reason": "LESS_THAN_48_VALID_FX911_HOURS_IN_96H_STUDY",
            })
            continue
        reports.append({
            **station,
            "original_DWD_historical_FX_zip_url": original_url,
            **measured,
        })
        if len(reports) == MAX_STATIONS:
            break
    if len(reports) != MAX_STATIONS:
        raise OriginalDWDRejected("too few sufficiently complete original DWD 2020 stations in bounded nearest 12")
    return {
        "schema": SCHEMA,
        "status": "REAL_DWD_ORIGINAL_FX911_STATION_OBSERVATIONS_2020_NO_ERA5_LOSS_CALIBRATION",
        "source": "Deutscher Wetterdienst (DWD), Climate Data Center, hourly extreme wind historical",
        "original_station_list_sha256": hashlib.sha256(station_bytes).hexdigest(),
        "original_archives_index_sha256": hashlib.sha256(html).hexdigest(),
        "source_product": "hourly extreme_wind historical",
        "source_variable": "FX_911",
        "units": "m/s",
        "historic_reference_time_interpretation_verified_as_UTC": False,
        "observed_Ciara_date_window": ["2020-02-08", "2020-02-11"],
        "station_coordinates_reported_are_current_not_verified_historic_2020": True,
        "origin": INDEX,
        "source_rights": "CC BY 4.0 with attribution to Deutscher Wetterdienst (DWD)",
        "source_rights_evidence": DWD_RIGHTS,
        "source_variable_schema": DWD_FORMAT,
        "station_count": len(reports),
        "historical_station_archive_candidates_checked": len(reports) + len(skipped_incomplete_stations),
        "skipped_original_archives_due_to_insufficient_2020_gust_coverage": skipped_incomplete_stations,
        "stations": reports,
        "original_DWD_station_winds_measured_not_ERA5_grid_reanalysis": True,
        "same_station_temporal_spatial_methods_as_ERA5_verified": False,
        "actual_2020_insurer_losses_or_building_vulnerability_calibrated": False,
        "native_NextGen_Oasis_GUL_IL_RI_OEP_AEP_admitted": False,
        "real_RV_insured_location_universe_observed": False,
    }


FROZEN_FIRST_REAL_DWD_SOURCE = (
    Path(__file__).resolve().parents[1] /
    "research/observations/ciara2020_dwd_original_fx911_three_stations_receipt_20261113.toml"
)


def verify_first_original_2020_station_receipt_against_live(live: dict) -> None:
    """Protect genuine DWD archive/peak/QN3 source proof from silent drift."""
    with FROZEN_FIRST_REAL_DWD_SOURCE.open("rb") as fp:
        source = tomllib.load(fp)
    if (source.get("schema") != SCHEMA
        or source.get("status") != live.get("status")
        or source.get("first_original_live_github_run_id") != 43499602678
        or source.get("first_original_live_github_job_id") != 132144371691
        or source.get("official_source_index") != INDEX
        or source.get("source_rights_evidence") != DWD_RIGHTS
        or source.get("original_hourly_parameter") != "FX_911"
        or source.get("original_units") != "m/s"
        or live.get("source_variable") != "FX_911"
        or live.get("units") != "m/s"
        or source.get("reported_station_count") != MAX_STATIONS
        or live.get("station_count") != MAX_STATIONS
        or source.get("reported_all_stations_96_original_hours") is not True
        or source.get("station_QN8_10_highest_quality_met") is not False
        or source.get("DWD_reference_timestamps_UTC_harmonization_verified") is not False
        or source.get("actual_2020_real_RV_insurer_claims_observed") is not False
        or source.get("German_wind_damage_function_calibrated") is not False
        or source.get("native_Oasis_NextGen_GUL_IL_RI_OEP_AEP_admitted") is not False
        or live.get("actual_2020_insurer_losses_or_building_vulnerability_calibrated") is not False
        or live.get("native_NextGen_Oasis_GUL_IL_RI_OEP_AEP_admitted") is not False
        or live.get("historic_reference_time_interpretation_verified_as_UTC") is not False):
        raise OriginalDWDRejected("original DWD 2020 source/global scientific identity drift")
    expected = source.get("stations", [])
    actual = live.get("stations", [])
    if len(expected) != MAX_STATIONS or len(actual) != MAX_STATIONS:
        raise OriginalDWDRejected("actual DWD 2020 station-set population drift")
    for pinned, observed in zip(expected, actual):
        pairs = (
            ("station_id", "station_id"),
            ("original_archive_url", "original_DWD_historical_FX_zip_url"),
            ("original_unmodified_zip_sha256", "provider_original_zip_sha256"),
            ("current_publisher_latitude", "latitude_as_publisher_lists_today"),
            ("current_publisher_longitude", "longitude_as_publisher_lists_today"),
            ("distance_to_51N_7E_km", "distance_to_original_era5_51N_7E_km"),
            ("published_2020_peak_hour_label", "measured_2020_Ciara_window_peak_hour_as_publisher_reports"),
            ("observed_2020_96h_peak_gust_mps", "measured_2020_02_08_through_11_max_hourly_gust_mps"),
            ("valid_2020_hour_count", "original_station_fx911_hourly_valid_count"),
            ("missing_original_value_count", "original_station_fx911_missing_marker_count"),
        )
        if any(pinned.get(left) != observed.get(right) for left, right in pairs):
            raise OriginalDWDRejected("DWD original 2020 archive/station/quality/wind peak parity drift")
        if observed.get("DWD_QN8_quality_level_hour_counts") != {
            "3": pinned.get("source_quality_QN8_3_hour_count")
        } or observed.get("observed_station_max_gust_hours_full_96h") is not True:
            raise OriginalDWDRejected("DWD observed 2020 QN8 or all-96h station support drift")
    rejected = live.get("skipped_original_archives_due_to_insufficient_2020_gust_coverage")
    if (len(rejected) != source.get("source_archives_rejected_for_insufficient_2020_hours")
        or live.get("historical_station_archive_candidates_checked") != source.get("source_archives_inspected")
        or rejected[0].get("original_station_id") != source.get("rejected_station_id")
        or rejected[0].get("original_station_zip_sha256") != source.get("rejected_original_zip_sha256")):
        raise OriginalDWDRejected("original DWD first rejected 2020 sparse station archive drift")


def dry_run() -> dict:
    return {
        "schema": SCHEMA,
        "status": "DWD_HOURLY_FX911_PUBLIC_ORIGINAL_SOURCE_CANDIDATE_NOT_DOWNLOADED",
        "station_metadata_url": STATION_LIST,
        "archive_index": INDEX,
        "rights_url": DWD_RIGHTS,
        "requested_stations": MAX_STATIONS,
        "requested_2020_study_hours": HOURS,
        "DWD_original_stations_fetched": False,
        "native_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--dry-run", action="store_true")
    choices.add_argument("--live-dwd", action="store_true")
    args = parser.parse_args()
    try:
        result = live_dwd_2020_original_three_stations() if args.live_dwd else dry_run()
        if args.live_dwd:
            verify_first_original_2020_station_receipt_against_live(result)
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
        return 0
    except (OriginalDWDRejected, OSError, ValueError) as exc:
        parser.exit(2, "DWD_ORIGINAL_2020_CIARA_STATION_QC_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
