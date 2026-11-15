# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Screen 15 spatially spread original DWD hourly FX_911 archives.

This is an exploratory source audit of a purposive station sample against
CLIMK-WINDS v2 ERA5's selected top-50 storms. It never writes hourly source
values or event-level comparisons to disk or stdout. Only hash-pinned source
bytes and complete Storm_Dates-day aggregates are admitted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import climk_era5_dwd_50event_station_audit_v0 as audit
from scripts.inspect_climk_winds_era5_v0 import (
    PINNED_SHA256, fetch_provider_bytes, verify_source_bytes,
)

SCHEMA = "CLIMK_ERA5_DWD_SPATIALLY_DISTRIBUTED_STATION_DAILY_SCREEN_V1"
MANIFEST = ROOT / "research/observations/climk_era5_dwd_spatial_station_candidate_sources_20261114.toml"
WINDOW_HOURS = 72
EVENTS = 50
MAX_LIST_ROWS = 10_000


class CandidateScreenBlocked(ValueError):
    """Frozen candidate population or one or more input sources changed."""


def load_manifest(path: Path = MANIFEST) -> dict:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise CandidateScreenBlocked("candidate source manifest cannot be read") from exc
    candidates = value.get("candidate_archives")
    ids = [item.get("station_id") for item in candidates] if isinstance(candidates, list) else []
    if (value.get("schema") != "CLIMK_ERA5_DWD_SPATIALLY_DISTRIBUTED_STATION_CANDIDATE_SOURCES_V0"
        or value.get("status") != "SOURCE_HASHES_PINNED_FOR_EXPLORATORY_SCREEN_ONLY"
        or value.get("climk_source_sha256") != PINNED_SHA256
        or value.get("dwd_station_list_url") != dwd.STATION_LIST
        or value.get("dwd_historical_index_url") != dwd.INDEX
        or len(ids) != 15 or len(set(ids)) != 15 or ids != sorted(ids)):
        raise CandidateScreenBlocked("candidate source manifest identity/population changed")
    seen_files = set()
    for item in candidates:
        station = item.get("station_id")
        filename = item.get("filename")
        digest = item.get("sha256")
        match = re.fullmatch(r"stundenwerte_FX_(\d{5})_(\d{8})_(\d{8})_hist\.zip", str(filename))
        if (not isinstance(station, str) or not re.fullmatch(r"\d{5}", station)
            or match is None or match.group(1) != station or filename in seen_files
            or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or type(item.get("filename_supported_event_windows")) is not int
            or not 1 <= item["filename_supported_event_windows"] <= EVENTS):
            raise CandidateScreenBlocked("candidate station filename/hash/date identity is malformed")
        if int(match.group(2)) > int(match.group(3)):
            raise CandidateScreenBlocked("candidate station filename interval is reversed")
        seen_files.add(filename)
    return value


def _listed_sources(station_list: bytes, historical_index: bytes,
                    manifest: dict) -> dict:
    if hashlib.sha256(station_list).hexdigest() != manifest["dwd_station_list_sha256"]:
        raise CandidateScreenBlocked("DWD source station list SHA256 drift")
    if hashlib.sha256(historical_index).hexdigest() != manifest["dwd_historical_index_sha256"]:
        raise CandidateScreenBlocked("DWD historical index SHA256 drift")
    try:
        lines = station_list.decode("cp1252").splitlines()
        index_parser = dwd.LinkIndex()
        index_parser.feed(historical_index.decode("utf-8"))
        index_parser.close()
    except (UnicodeError, ValueError) as exc:
        raise CandidateScreenBlocked("DWD station list/index encoding or HTML is invalid") from exc
    if not lines or lines[0].split()[:6] != [
        "Stations_id", "von_datum", "bis_datum", "Stationshoehe", "geoBreite", "geoLaenge"
    ]:
        raise CandidateScreenBlocked("DWD original hourly station-list header changed")
    found = {}
    data_rows = 0
    for line in lines[2:]:
        fields = line.split(maxsplit=8)
        if not fields or not re.fullmatch(r"\d{5}", fields[0]):
            continue
        data_rows += 1
        if data_rows > MAX_LIST_ROWS or len(fields) < 7:
            raise CandidateScreenBlocked("DWD station list has too many or malformed rows")
        try:
            first, last = fields[1], fields[2]
            elevation, latitude, longitude = int(fields[3]), float(fields[4]), float(fields[5])
        except (ValueError, IndexError) as exc:
            raise CandidateScreenBlocked("DWD station list has malformed source values") from exc
        if (not re.fullmatch(r"\d{8}", first) or not re.fullmatch(r"\d{8}", last)
            or first > last or not 0 <= elevation <= 10_000
            or not 47 <= latitude <= 56 or not 5 <= longitude <= 16):
            # Non-German and offshore stations outside this screen's spatial
            # support are outside the selected candidate population.
            continue
        if fields[0] in {x["station_id"] for x in manifest["candidate_archives"]}:
            if fields[0] in found:
                raise CandidateScreenBlocked("candidate DWD station ID is duplicated in station list")
            found[fields[0]] = {"first": first, "last": last}

    if data_rows != manifest["dwd_station_list_record_count"]:
        raise CandidateScreenBlocked("DWD station-list data-row count changed")
    names = index_parser.links
    for item in manifest["candidate_archives"]:
        station = item["station_id"]
        filename = item["filename"]
        if names.count(filename) != 1 or station not in found:
            raise CandidateScreenBlocked("frozen candidate absent or ambiguous in DWD original listings")
        match = dwd.ZIP_RE.fullmatch(filename)
        if (found[station]["first"] > match.group(2)
            or found[station]["last"] < match.group(3)):
            raise CandidateScreenBlocked("DWD station-list interval no longer envelops frozen archive")
    valid_archives = {
        link for link in names if isinstance(link, str) and dwd.ZIP_RE.fullmatch(link)
    }
    if len(valid_archives) != manifest["dwd_historical_archive_count"]:
        raise CandidateScreenBlocked("DWD historical archive-link count changed")
    return {"station_list_data_rows": data_rows,
            "historical_hourly_FX_zip_archive_links": len(valid_archives)}


def _window_support(filename: str, labels: list[str]) -> int:
    match = dwd.ZIP_RE.fullmatch(filename)
    first, last = match.group(2), match.group(3)
    return sum(first <= (datetime.strptime(label, "%Y%m%d")-timedelta(days=1)).strftime("%Y%m%d")
               and last >= (datetime.strptime(label, "%Y%m%d")+timedelta(days=1)).strftime("%Y%m%d")
               for label in labels)


def audit_candidate_sources(climk_bytes: bytes, station_list: bytes,
                            historical_index: bytes,
                            candidate_archives: dict[str, bytes],
                            manifest: dict | None = None) -> dict:
    manifest = manifest or load_manifest()
    source_identity = verify_source_bytes(climk_bytes, require_sha256=True)
    if source_identity["sha256_observed"] != manifest["climk_source_sha256"]:
        raise CandidateScreenBlocked("CLIMK original ERA5 SHA differs from source manifest")
    roster = _listed_sources(station_list, historical_index, manifest)
    expected_ids = [item["station_id"] for item in manifest["candidate_archives"]]
    if set(candidate_archives) != set(expected_ids):
        raise CandidateScreenBlocked("actual original station archive population differs from frozen candidates")
    results, union_nodes, all_labels = [], set(), None
    for item in manifest["candidate_archives"]:
        station = item["station_id"]
        raw = candidate_archives[station]
        observed_sha = hashlib.sha256(raw).hexdigest()
        if observed_sha != item["sha256"]:
            raise CandidateScreenBlocked("original DWD station archive SHA differs from pinned source")
        try:
            history = audit._rows_from_metadata(raw, station)
            observations = audit._parse_original_hourly(raw, station)
            windows, labels = audit._climk_station_windows(climk_bytes, station,
                                                            history, observations)
            summary = audit.summarize_windows(windows)
        except (audit.CLIMKDWDBlocked, dwd.OriginalDWDRejected, ValueError) as exc:
            results.append({
                "station_id": station,
                "filename": item["filename"],
                "original_DWD_zip_sha256": observed_sha,
                "filename_supported_CLIMK_event_context_windows": item["filename_supported_event_windows"],
                "status": "BLOCKED_STATION_HISTORY_OR_SOURCE_SEMANTICS",
                "block_reason": str(exc),
            })
            continue
        if all_labels is None:
            all_labels = labels
        elif all_labels != labels:
            raise CandidateScreenBlocked("CLIMK event labels differ across candidate stations")
        union_nodes.update(tuple(win["era5_grid_node"]) for win in windows
                           if win["era5_grid_node"] is not None)
        count = summary["station_storm_dates_with_complete_24h_DWD"]
        if count == 0:
            status = "AUDITED_NO_COMPLETE_STORM_DATE_DAYS"
        elif count < 10:
            status = "AUDITED_LOW_COMPLETE_STORM_DATE_COVERAGE"
        else:
            status = "AUDITED_COMPLETE_STORM_DATE_DAILY_CONTRASTS_DESCRIPTIVE_ONLY"
        results.append({
            "station_id": station,
            "filename": item["filename"],
            "original_DWD_zip_sha256": observed_sha,
            "filename_supported_CLIMK_event_context_windows": _window_support(item["filename"], labels),
            "status": status,
            **summary,
        })
    if len(results) != len(expected_ids):
        raise CandidateScreenBlocked("candidate result population is incomplete")
    return {
        "schema": SCHEMA,
        "status": "ORIGINAL_DWD_STATION_CANDIDATE_SCREEN_NO_MODEL_SKILL_ADMISSION",
        "CLIMK_source_sha256": source_identity["sha256_observed"],
        "DWD_station_list_sha256": manifest["dwd_station_list_sha256"],
        "DWD_historical_index_sha256": manifest["dwd_historical_index_sha256"],
        **roster,
        "candidate_selection": manifest["selection"],
        "candidate_count": len(expected_ids),
        "candidate_count_with_verified_historical_metadata_and_hourly_semantics": sum(
            "event_windows_with_verified_historical_site_instrument_and_UTC_semantics" in x
            for x in results
        ),
        "candidate_count_with_any_complete_storm_date_day": sum(
            x.get("station_storm_dates_with_complete_24h_DWD", 0) > 0 for x in results
        ),
        "candidate_count_with_10_or_more_complete_storm_date_days": sum(
            x.get("station_storm_dates_with_complete_24h_DWD", 0) >= 10 for x in results
        ),
        "candidate_count_with_zero_complete_storm_date_days": sum(
            x.get("station_storm_dates_with_complete_24h_DWD", 0) == 0
            and x.get("status") != "BLOCKED_STATION_HISTORY_OR_SOURCE_SEMANTICS" for x in results
        ),
        "candidate_count_blocked_by_history_or_semantics": sum(
            x["status"] == "BLOCKED_STATION_HISTORY_OR_SOURCE_SEMANTICS" for x in results
        ),
        "unique_nearest_CLIMK_ERA5_grid_nodes_across_audited_candidates": len(union_nodes),
        "stations": results,
        "DWD_and_CLIMK_temporal_support_equivalence_proven": False,
        "DWD_daily_calendar_date_aligned_to_CLIMK_Storm_Dates": True,
        "CLIMK_Storm_Dates_UTC_day_boundary_proven": False,
        "gust_averaging_duration_equivalence_proven": False,
        "DWD_and_CLIMK_input_independence_proven": False,
        "sensor_height_adjustment_or_spatial_interpolation_applied": False,
        "partial_windows_used_in_primary_metrics": False,
        "source_top50_is_complete_event_catalog": False,
        "annual_frequency_or_OEP_AEP_admitted": False,
        "german_wind_loss_or_vulnerability_calibrated": False,
        "model_skill_or_bias_correction_admitted": False,
        "raw_hourly_values_or_event_level_rows_in_receipt": False,
        "DWD_attribution": "Deutscher Wetterdienst (DWD); source data CC BY 4.0",
    }


def live_analysis() -> dict:
    manifest = load_manifest()
    station_list = dwd._get_publisher_bytes(dwd.STATION_LIST, dwd.MAX_STATION_LIST)
    historical_index = dwd._get_publisher_bytes(dwd.INDEX, dwd.MAX_INDEX)
    source = fetch_provider_bytes()
    archives = {}
    for item in manifest["candidate_archives"]:
        url = dwd.INDEX + item["filename"]
        archives[item["station_id"]] = dwd._get_publisher_bytes(url, dwd.MAX_ZIP)
    return audit_candidate_sources(source, station_list, historical_index,
                                   archives, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--live-original-sources", action="store_true")
    parser.add_argument("--output", type=Path,
                        help="write aggregate-only JSON locally; refuses overwrite")
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
                raise CandidateScreenBlocked("refuse to overwrite an existing candidate-screen receipt") from exc
        print(json.dumps({"schema": SCHEMA,
                          "status": "LIVE_CANDIDATE_SCREEN_COMPLETED_AGGREGATE_REVIEW_REQUIRED",
                          "aggregate_receipt_written": bool(args.output),
                          "source_values_or_metrics_written_to_stdout": False,
                          "model_skill_admitted": False}, sort_keys=True))
        return 0
    except (CandidateScreenBlocked, audit.CLIMKDWDBlocked,
            dwd.OriginalDWDRejected, OSError, ValueError) as exc:
        parser.exit(2, "CLIMK_DWD_CANDIDATE_SCREEN_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
