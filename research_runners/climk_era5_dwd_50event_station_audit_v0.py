# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exploratory CLIMK ERA5 top-50 event maxima vs original DWD station gusts.

The CLIMK source contains the 50 ERA5 storms selected by its LI3D severity
ranking, not a complete or frequency-calibrated event set. This reader pairs
each row's 3-day footprint value with DWD FX_911 observations in the three
calendar days centred on the published Storm_Dates midpoint. Only complete
72-hour station windows enter the primary aggregate metrics. The two long-record
stations map to one CLIMK ERA5 grid node; the shorter third station adds one
separate node with only seven complete cases. This is not independent spatial
validation.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import sys
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import ciara2020_dwd_historical_feb2020_station_attestation_v0 as historical
from scripts.inspect_climk_winds_era5_v0 import (
    EXPECTED_DIMENSIONS, EXPECTED_FIELDS, verify_source_bytes, fetch_provider_bytes,
)

SCHEMA = "CLIMK_ERA5_TOP50_DWD_ORIGINAL_STATION_72H_EXPLORATION_V0"
STATIONS = ("02667", "00603", "15200")
MAX_UNCOMPRESSED = 25_000_000
MAX_ZIP_MEMBERS = 40
MAX_METADATA_BYTES = 250_000
EVENTS = 50
WINDOW_HOURS = 72
MAX_GUST_MPS = 150.0


class CLIMKDWDBlocked(ValueError):
    """Original source identity, support or station history could not be verified."""


def _finite_number(value: object, label: str, lo: float = 0.0,
                   hi: float = MAX_GUST_MPS) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
        raise CLIMKDWDBlocked(f"{label} is nonfinite or outside accepted physical bounds")
    return float(value)


def summarize_windows(windows: list[dict]) -> dict:
    """Summarize bounded station/event pairs; never return individual rows."""
    if type(windows) is not list or len(windows) != EVENTS:
        raise CLIMKDWDBlocked("exactly the original 50 CLIMK event rows are required")
    complete, complete_qn3 = [], []
    valid_windows = 0
    observed_hours = []
    grid_nodes, heights = set(), {}
    model_masked = 0
    for item in windows:
        if not isinstance(item, dict):
            raise CLIMKDWDBlocked("malformed internal station/event pair")
        observations = item.get("dwd_hourly_gust_qn")
        modeled = item.get("climk_72h_gust_mps")
        node = item.get("era5_grid_node")
        height = item.get("sensor_height_m")
        metadata_verified = item.get("historical_metadata_verified")
        if (not isinstance(observations, list) or len(observations) > WINDOW_HOURS
            or (node is not None and (not isinstance(node, (list, tuple)) or len(node) != 2))
            or type(metadata_verified) is not bool
            or type(height) not in (int, float) or not math.isfinite(height)
            or not 1.0 <= height <= 150.0):
            raise CLIMKDWDBlocked("invalid bounded DWD hourly, metadata or grid support")
        if node is not None:
            grid_nodes.add((float(node[0]), float(node[1])))
        checked = []
        for pair in observations:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise CLIMKDWDBlocked("malformed DWD value/quality pair")
            gust = _finite_number(pair[0], "DWD FX_911 gust")
            qn = pair[1]
            if type(qn) is not int or not 0 <= qn <= 10:
                raise CLIMKDWDBlocked("unsupported DWD QN_8 quality code")
            checked.append((gust, qn))
        count = len(checked)
        observed_hours.append(count)
        if not count:
            continue
        if modeled is None:
            model_masked += 1
            continue
        model_gust = _finite_number(modeled, "CLIMK ERA5 absolute_maxwindgusts")
        valid_windows += 1
        heights[str(float(height))] = heights.get(str(float(height)), 0) + 1
        if count == WINDOW_HOURS:
            record = (max(v for v, _ in checked), model_gust)
            complete.append(record)
            if all(q == 3 for _, q in checked):
                complete_qn3.append(record)

    def metrics(records: list[tuple[float, float]]) -> dict | None:
        if not records:
            return None
        observed = [x for x, _ in records]
        modeled = [y for _, y in records]
        errors = [y-x for x, y in records]
        mo, mm = sum(observed)/len(observed), sum(modeled)/len(modeled)
        cov = sum((x-mo)*(y-mm) for x, y in records)
        vo = sum((x-mo)**2 for x in observed)
        vm = sum((y-mm)**2 for y in modeled)
        return {
            "complete_72h_event_pairs": len(records),
            "mean_error_era5_minus_dwd_mps": sum(errors)/len(errors),
            "mean_absolute_error_mps": sum(abs(e) for e in errors)/len(errors),
            "root_mean_square_error_mps": math.sqrt(sum(e*e for e in errors)/len(errors)),
            "pearson_correlation": cov/math.sqrt(vo*vm) if vo and vm else None,
            "mean_DWD_72h_max_mps": mo,
            "mean_CLIMK_ERA5_72h_max_mps": mm,
        }

    return {
        "CLIMK_top50_rows": EVENTS,
        "event_windows_with_verified_historical_site_instrument_and_UTC_semantics": sum(
            bool(item["historical_metadata_verified"]) for item in windows
        ),
        "station_windows_with_any_valid_DWD_hours_and_unmasked_model_value": valid_windows,
        "station_windows_with_no_DWD_hours": sum(n == 0 for n in observed_hours),
        "station_windows_with_partial_DWD_hours": sum(0 < n < WINDOW_HOURS for n in observed_hours),
        "station_windows_with_complete_72h_DWD": len(complete),
        "station_windows_with_complete_72h_DWD_QN8_3": len(complete_qn3),
        "median_valid_DWD_hours_per_72h_event_window": statistics.median(observed_hours),
        "CLIMK_masked_cell_windows_with_DWD_observations": model_masked,
        "unique_nearest_CLIMK_ERA5_grid_nodes": len(grid_nodes),
        "historical_sensor_height_counts_m_for_windows_with_observations": heights,
        "complete_72h_primary_metrics_descriptive_only": metrics(complete),
        "complete_72h_QN8_3_sensitivity_metrics_descriptive_only": metrics(complete_qn3),
        "partial_DWD_windows_imputed_or_used_in_primary_metrics": False,
        "sensor_height_adjustment_applied": False,
    }


def _rows_from_metadata(raw: bytes, station_id: str) -> dict[str, list[dict]]:
    if len(raw) > dwd.MAX_ZIP:
        raise CLIMKDWDBlocked("original DWD source archive exceeds byte bound")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if (not 1 <= len(members) <= MAX_ZIP_MEMBERS
                or sum(x.file_size for x in members) > MAX_UNCOMPRESSED
                or any(x.file_size > MAX_UNCOMPRESSED or x.flag_bits & 1
                       or x.filename.startswith(("/", "\\")) or "/" in x.filename
                       or "\\" in x.filename or ".." in x.filename for x in members)):
                raise CLIMKDWDBlocked("unsafe or oversized original DWD ZIP contents")
            proof = historical.inventory.inspect_original_metadata_zip(raw, station_id)
            result = {}
            for kind in historical.inventory.REQUIRED_CATEGORIES:
                meta = proof["metadata"][kind]
                if meta["original_member_bytes"] > MAX_METADATA_BYTES:
                    raise CLIMKDWDBlocked("oversized original DWD metadata member")
                member = archive.read(meta["original_member_name"])
                if hashlib.sha256(member).hexdigest() != meta["original_member_sha256"]:
                    raise CLIMKDWDBlocked("DWD original metadata member SHA drift")
                result[kind] = historical._metadata_rows(member, kind, station_id)
            return result
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise CLIMKDWDBlocked("original DWD archive or metadata cannot be read") from exc


def _one_covering(rows: list[dict], start: str, end: str,
                  start_field: str, end_field: str) -> dict:
    candidates = []
    for row in rows:
        first = row.get(start_field, "")
        last = row.get(end_field, "") or "99991231"
        if (len(first) == len(last) == 8 and first.isdigit() and last.isdigit()
            and first <= start and last >= end):
            candidates.append(row)
    if len(candidates) != 1:
        raise CLIMKDWDBlocked("station metadata must uniquely cover each full 72-hour event window")
    return candidates[0]


def _covering_by_hour(rows: list[dict], start: datetime, hours: int,
                      start_field: str, end_field: str) -> list[dict]:
    """Require exactly one applicable source row for every hourly label."""
    selected = []
    for offset in range(hours):
        stamp = (start + timedelta(hours=offset)).strftime("%Y%m%d")
        candidates = []
        for row in rows:
            first = row.get(start_field, "")
            last = row.get(end_field, "") or "99991231"
            # DWD's inclusive date metadata often leaves the calendar day
            # between consecutive source ranges unassigned. The station file
            # has hourly labels; associate the UTC hour with its date interval
            # and require unique coverage for that hour's full day label.
            if (len(first) == len(last) == 8 and first.isdigit() and last.isdigit()
                and first <= stamp <= last):
                candidates.append(row)
        # Parameter tables have source-history gaps around schema transitions.
        # Do not guess semantics on that day: it blocks any window crossing it.
        if len(candidates) != 1:
            raise CLIMKDWDBlocked("original station metadata must uniquely cover every event-window hour")
        if not selected or selected[-1] != candidates[0]:
            selected.append(candidates[0])
    return selected


def _parse_original_hourly(raw: bytes, station_id: str) -> dict[str, tuple[float, int]]:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if (not 1 <= len(members) <= MAX_ZIP_MEMBERS
                or sum(x.file_size for x in members) > MAX_UNCOMPRESSED
                or any(x.file_size > MAX_UNCOMPRESSED or x.flag_bits & 1
                       or x.filename.startswith(("/", "\\")) or "/" in x.filename
                       or "\\" in x.filename or ".." in x.filename for x in members)):
                raise CLIMKDWDBlocked("unsafe or oversized original DWD observation ZIP")
            product = [x for x in members if x.filename.lower().startswith("produkt_")
                       and x.filename.endswith(".txt")]
            if len(product) != 1:
                raise CLIMKDWDBlocked("exactly one original DWD hourly product required")
            text = archive.read(product[0]).decode("cp1252")
    except (zipfile.BadZipFile, UnicodeError, OSError, RuntimeError) as exc:
        raise CLIMKDWDBlocked("original DWD hourly product unreadable") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";", strict=True)
    fields = {x.strip() for x in (reader.fieldnames or [])}
    if fields not in ({"STATIONS_ID", "MESS_DATUM", "QN_8", "FX_911"},
                      {"STATIONS_ID", "MESS_DATUM", "QN_8", "FX_911", "eor"}):
        raise CLIMKDWDBlocked("unexpected original DWD FX_911 product schema")
    observations = {}
    seen_timestamps = set()
    for row in reader:
        record = {k.strip(): v.strip() for k, v in row.items() if k and v is not None}
        if record.get("STATIONS_ID", "").zfill(5) != station_id:
            raise CLIMKDWDBlocked("DWD embedded station ID differs from archive identity")
        stamp = record.get("MESS_DATUM", "")
        if len(stamp) != 10 or not stamp.isdigit():
            raise CLIMKDWDBlocked("unexpected DWD timestamp format")
        if stamp in seen_timestamps:
            raise CLIMKDWDBlocked("duplicate original DWD hourly timestamp")
        seen_timestamps.add(stamp)
        try:
            gust = float(record["FX_911"])
            qn = int(record["QN_8"])
        except (ValueError, KeyError) as exc:
            raise CLIMKDWDBlocked("unparseable original DWD FX_911 row") from exc
        if not 0 <= qn <= 10:
            raise CLIMKDWDBlocked("DWD QN_8 quality code outside documented numeric domain")
        if "eor" in record and record["eor"].lower() not in ("", "eor"):
            raise CLIMKDWDBlocked("unexpected original DWD end-of-record marker")
        if gust == -999.0:
            continue
        observations[stamp] = (_finite_number(gust, "DWD FX_911 gust"), qn)
    return observations


def _climk_station_windows(source: bytes, station_id: str,
                            historical_rows: dict[str, list[dict]],
                            observations: dict[str, tuple[float, int]]) -> tuple[list[dict], list[str]]:
    import numpy as np
    from netCDF4 import Dataset

    try:
        with Dataset("climk-winds-era5-dwd-station-audit", mode="r", memory=source) as ds:
            dims = {name: len(dim) for name, dim in ds.dimensions.items()}
            if dims != EXPECTED_DIMENSIONS:
                raise CLIMKDWDBlocked("CLIMK ERA5 original grid dimensions changed")
            for name, (axes, unit) in EXPECTED_FIELDS.items():
                if name not in ds.variables:
                    raise CLIMKDWDBlocked("mandatory original CLIMK field is missing")
                field = ds.variables[name]
                if field.dimensions != axes or str(getattr(field, "units", "")) != unit:
                    raise CLIMKDWDBlocked("CLIMK original variable axes or units changed")
            names = [str(v).strip() for v in ds.variables["Storm_Names"][:]]
            labels = [str(v).strip() for v in ds.variables["Storm_Dates"][:]]
            latitudes = [float(v) for v in ds.variables["latitude"][:]]
            longitudes = [float(v) for v in ds.variables["longitude"][:]]
            if (len(names) != EVENTS or len(labels) != EVENTS
                or len(set(zip(names, labels))) != EVENTS):
                raise CLIMKDWDBlocked("original CLIMK event identity population is ambiguous")
            if (any(not math.isfinite(v) for v in latitudes+longitudes)
                or any(b >= a for a, b in zip(latitudes, latitudes[1:]))
                or any(b <= a for a, b in zip(longitudes, longitudes[1:]))):
                raise CLIMKDWDBlocked("CLIMK ERA5 native geographic axes are malformed")
            field = ds.variables["absolute_maxwindgusts"]
            windows = []
            date_labels = []
            for index, label in enumerate(labels):
                if len(label) != 8 or not label.isdigit():
                    raise CLIMKDWDBlocked("CLIMK Storm_Dates contains a non-YYYYMMDD label")
                middle = datetime.strptime(label, "%Y%m%d")
                begin = middle-timedelta(days=1)
                finish = middle+timedelta(days=1, hours=23)
                date_labels.append(label)
                # Source metadata can change inside a selected 72-hour storm
                # window. Resolve every hour against its applicable historical
                # row and require a single consistent value over the window.
                # DWD's station archive may not contain matching instrument
                # history before the first hourly measurements. Windows lacking
                # any DWD measurements remain countable with source-era metadata
                # only if it exists; otherwise report it as uncovered below.
                try:
                    geo_rows = _covering_by_hour(historical_rows["geographie"], begin,
                                                 WINDOW_HOURS, "von_datum", "bis_datum")
                    device_rows = _covering_by_hour(historical_rows["geraete"], begin,
                                                    WINDOW_HOURS, "Von_Datum", "Bis_Datum")
                    parameter_rows = _covering_by_hour(historical_rows["parameter"], begin,
                                                       WINDOW_HOURS, "Von_Datum", "Bis_Datum")
                except CLIMKDWDBlocked:
                    if any((begin + timedelta(hours=h)).strftime("%Y%m%d%H") in observations
                           for h in range(WINDOW_HOURS)):
                        raise
                    windows.append({
                        "dwd_hourly_gust_qn": [],
                        "climk_72h_gust_mps": None,
                        "era5_grid_node": None,
                        "sensor_height_m": 10.0,
                        "historical_metadata_verified": False,
                    })
                    continue
                geo = geo_rows[0]
                device = device_rows[0]
                parameter = parameter_rows[0]
                if (any(row != geo for row in geo_rows)
                    or any(row != device for row in device_rows)
                    or any(row != parameter for row in parameter_rows)):
                    raise CLIMKDWDBlocked("station geography, instrument or parameter changes inside a 72-hour event window")
                if (parameter.get("Parameter") != "FX_911"
                    or parameter.get("Zusatz-Info") != "in UTC"
                    or parameter.get("Parameterbeschreibung") != "hoechste Windspitze der letzten Stunde"
                    or parameter.get("Einheit") not in ("m/sec", "m/s")):
                    raise CLIMKDWDBlocked("original DWD FX_911 UTC/last-hour meaning changed")
                try:
                    lat = float(geo["Geogr.Breite"])
                    lon = float(geo["Geogr.Laenge"])
                    height = float(device["Geberhoehe ueber Grund [m]"])
                except (KeyError, ValueError) as exc:
                    raise CLIMKDWDBlocked("historical DWD station geography or height is unparseable") from exc
                if (not math.isfinite(lat) or not math.isfinite(lon) or not math.isfinite(height)
                    or not 49 <= lat <= 55 or not 5 <= lon <= 16 or not 1 <= height <= 150):
                    raise CLIMKDWDBlocked("historical DWD station geometry/height outside bounds")
                row = min(range(len(latitudes)), key=lambda i: abs(latitudes[i]-lat))
                col = min(range(len(longitudes)), key=lambda i: abs(longitudes[i]-lon))
                grid_lat, grid_lon = latitudes[row], longitudes[col]
                # This is a nearest centre, not an interpolated point value.
                lat_km = abs(lat-grid_lat)*111.2
                lon_km = abs(lon-grid_lon)*111.2*math.cos(math.radians(lat))
                distance = math.hypot(lat_km, lon_km)
                if distance > 25:
                    raise CLIMKDWDBlocked("historical station exceeds 25 km from a CLIMK ERA5 grid centre")
                cell = np.ma.asarray(field[index, row, col], dtype=float)
                modelled = None if bool(np.ma.is_masked(cell)) else _finite_number(float(cell), "CLIMK 72h gust")
                paired = []
                for h in range(WINDOW_HOURS):
                    stamp = (begin+timedelta(hours=h)).strftime("%Y%m%d%H")
                    if stamp in observations:
                        paired.append(list(observations[stamp]))
                windows.append({
                    "dwd_hourly_gust_qn": paired,
                    "climk_72h_gust_mps": modelled,
                    "era5_grid_node": [grid_lat, grid_lon],
                    "sensor_height_m": height,
                    "historical_metadata_verified": True,
                })
    except CLIMKDWDBlocked:
        raise
    except (OSError, RuntimeError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise CLIMKDWDBlocked("original CLIMK NetCDF event/grid extraction failed") from exc
    return windows, date_labels


def analyze_sources(climk_bytes: bytes, dwd_archives: dict[str, bytes],
                    expected_dwd_sha: dict[str, str]) -> dict:
    proof = verify_source_bytes(climk_bytes, require_sha256=True)
    if set(dwd_archives) != set(STATIONS) or set(expected_dwd_sha) != set(STATIONS):
        raise CLIMKDWDBlocked("exact original DWD station population required")
    results = []
    all_dates = None
    sha_receipts = {}
    all_grid_nodes = set()
    for station in STATIONS:
        raw = dwd_archives[station]
        sha = hashlib.sha256(raw).hexdigest()
        if sha != expected_dwd_sha[station]:
            raise CLIMKDWDBlocked("DWD source archive differs from independently pinned original SHA")
        history = _rows_from_metadata(raw, station)
        observations = _parse_original_hourly(raw, station)
        windows, dates = _climk_station_windows(climk_bytes, station, history, observations)
        all_grid_nodes.update(tuple(item["era5_grid_node"]) for item in windows
                              if item["era5_grid_node"] is not None)
        if all_dates is None:
            all_dates = dates
        elif all_dates != dates:
            raise CLIMKDWDBlocked("station event-date support differs within original CLIMK source")
        summary = summarize_windows(windows)
        summary.update({
            "station_id": station,
            "original_DWD_zip_sha256": sha,
            "original_DWD_metadata_member_sha256": {
                kind: hashlib.sha256(_original_member(raw, kind, station)).hexdigest()
                for kind in historical.inventory.REQUIRED_CATEGORIES
            },
        })
        results.append(summary)
        sha_receipts[station] = sha
    # A date label is the midpoint of a 3-day source event window. This
    # computes overlap among those 72h intervals without claiming independence.
    starts = [datetime.strptime(x, "%Y%m%d")-timedelta(days=1) for x in all_dates]
    overlap_count = sum(
        1 for i in range(EVENTS) for j in range(i+1, EVENTS)
        if max(starts[i], starts[j]) <= min(starts[i]+timedelta(hours=71),
                                            starts[j]+timedelta(hours=71))
    )
    return {
        "schema": SCHEMA,
        "status": "ORIGINAL_CLIMK_ERA5_AND_DWD_MULTI_EVENT_EXPLORATION_NO_SKILL_ADMISSION",
        "CLIMK_source_sha256": proof["sha256_observed"],
        "CLIMK_original_event_rows": EVENTS,
        "CLIMK_event_selection": "top 50 winter storms selected within ERA5 by LI3D severity; not a complete event set",
        "CLIMK_storm_date_label_semantics": "midpoint label of a 3-day LI3D event window",
        "comparison_window": "Storm_Dates minus one UTC calendar day through plus one day, inclusive (72 labels)",
        "DWD_parameter": "FX_911; highest gust of the previous hour; source metadata says UTC",
        "CLIMK_parameter": "absolute_maxwindgusts; maximum 3-second gust associated with the 72-hour footprint; m/s",
        "exact_DWD_and_CLIMK_temporal_support_equivalence_proven": False,
        "event_window_overlap_pairs_within_selected_top50": overlap_count,
        "DWD_and_ERA5_input_independence_proven": False,
        "station_height_adjustment_or_spatial_interpolation_applied": False,
        "stored_Storm_Ranks_used_for_order_or_weights": False,
        "stored_Storm_Ranks_source_inconsistency_already_identified": True,
        "station_count": len(results),
        "unique_CLIMK_ERA5_grid_nodes_across_stations": len(all_grid_nodes),
        "stations": results,
        "event_frequency_or_annual_OEP_AEP_admitted": False,
        "German_wind_vulnerability_or_insured_loss_calibrated": False,
        "model_skill_or_bias_correction_admitted": False,
        "raw_hourly_DWD_or_CLIMK_values_in_receipt": False,
        "DWD_original_zip_hashes": sha_receipts,
        "CLIMK_provider_original_product": "CLIMK-WINDS v2 ERA5, Flynn et al. (2025), Zenodo record 15305753, CC BY 4.0",
        "DWD_provider_original_product": "DWD CDC hourly extreme wind FX_911 historical archives, CC BY 4.0 with DWD attribution",
    }


def _original_member(raw: bytes, kind: str, station_id: str) -> bytes:
    proof = historical.inventory.inspect_original_metadata_zip(raw, station_id)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        return archive.read(proof["metadata"][kind]["original_member_name"])


def live_analysis() -> dict:
    source = fetch_provider_bytes()
    dwd_receipt = tomllib.loads(dwd.FROZEN_FIRST_REAL_DWD_SOURCE.read_text(encoding="utf-8"))
    if (dwd_receipt.get("schema") != dwd.SCHEMA
        or dwd_receipt.get("reported_station_count") != 3
        or dwd_receipt.get("DWD_reference_timestamps_UTC_harmonization_verified") is not False):
        raise CLIMKDWDBlocked("first genuine DWD original-source receipt changed")
    frozen = {item["station_id"]: item for item in dwd_receipt["stations"]}
    archives, digests = {}, {}
    for station in STATIONS:
        item = frozen.get(station)
        if not item:
            raise CLIMKDWDBlocked("DWD station is absent from accepted original archive receipt")
        raw = dwd._get_publisher_bytes(item["original_archive_url"], dwd.MAX_ZIP)
        if hashlib.sha256(raw).hexdigest() != item["original_unmodified_zip_sha256"]:
            raise CLIMKDWDBlocked("current DWD original bytes differ from frozen station archive receipt")
        archives[station] = raw
        digests[station] = item["original_unmodified_zip_sha256"]
    return analyze_sources(source, archives, digests)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--live-original-sources", action="store_true")
    parser.add_argument("--output", type=Path,
                        help="create an aggregate-only JSON receipt; refuses overwrite")
    args = parser.parse_args()
    if args.dry_run:
        print(json.dumps({"schema": SCHEMA, "status": "NO_SOURCE_READ_DRY_RUN",
                          "source_values_or_metrics_written_to_stdout": False,
                          "model_skill_admitted": False}, sort_keys=True))
        return 0
    try:
        result = live_analysis()
        if args.output:
            try:
                with args.output.open("x", encoding="utf-8") as stream:
                    json.dump(result, stream, sort_keys=True, indent=2)
                    stream.write("\n")
            except FileExistsError as exc:
                raise CLIMKDWDBlocked("refuse to overwrite an existing aggregate receipt") from exc
        print(json.dumps({"schema": SCHEMA,
                          "status": "LIVE_SOURCE_AUDIT_COMPLETED_AGGREGATE_RECEIPT_REVIEW_REQUIRED",
                          "aggregate_receipt_written": bool(args.output),
                          "source_values_or_metrics_written_to_stdout": False,
                          "model_skill_admitted": False}, sort_keys=True))
        return 0
    except (CLIMKDWDBlocked, dwd.OriginalDWDRejected,
            historical.HistoricalDWDNoGo, OSError, ValueError) as exc:
        parser.exit(2, "CLIMK_DWD_EVENT_AUDIT_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
