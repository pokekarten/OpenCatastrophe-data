# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three genuinely measured DWD Ciara-2020 station peaks vs two ERA5 grid peaks.

Original DWD station archive/quality receipt is SHA-frozen in #1564.
Original 96x160 Google Research ARCO ERA5 10fg grid is SHA-frozen
in #1556. This comparator performs a spatial NEAREST-GRID-CENTRE
exploratory join only. Station coordinates are the publisher's CURRENT
coordinates and 2020 instrument/geography/UTC harmonization is NOT done.
Even differences between 96h event maxima are NOT model bias, skill,
insured building risk, calibrated vulnerability or an insurer loss.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
import tomllib

import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import ciara2020_google_arco_real_96h_nrw_area_v0 as era5

FROZEN_DWD = dwd.FROZEN_FIRST_REAL_DWD_SOURCE
SCHEMA = "CIARA2020_DWD_FX911_STATION_TO_GOOGLE_ARCO_ERA5_GRID_PEAK_RESEARCH_V0"
ERA5_DECODED_96H_160_SHA = (
    "5fb7c41963a94f88ee3651b51bfa84cc2f4bf379e1ee6f4eb4a4fb597d37f932"
)
STUDY_DATE = ("2020-02-08", "2020-02-11")
MAX_SEPARATION_KM = 20.0
EXPECTED_STATIONS = ("02667", "15200", "00603")


class DWDGridComparisonBlocked(ValueError):
    """Unverified DWD source, false temporal alignment, or ERA5 source drift."""


def station_to_grid(lat: float, lon: float) -> tuple[int, int, float]:
    """Choose a real ERA5 original 0.25° grid centre; reject ties & large gaps."""
    if (type(lat) is not float or type(lon) is not float
        or not math.isfinite(lat) or not math.isfinite(lon)
        or not 50.0 <= lat <= 52.75 or not 5.5 <= lon <= 9.75):
        raise DWDGridComparisonBlocked("current DWD station coordinates invalid")
    nearest_lats = sorted(
        ((abs(lat-v), i) for i, v in enumerate(era5.LATITUDE)),
    )
    nearest_lons = sorted(
        ((abs(lon-v), i) for i, v in enumerate(era5.LONGITUDE)),
    )
    if (len(nearest_lats) < 2 or len(nearest_lons) < 2
        or nearest_lats[1][0] - nearest_lats[0][0] < 1e-10
        or nearest_lons[1][0] - nearest_lons[0][0] < 1e-10):
        raise DWDGridComparisonBlocked("station is exactly on ERA5 cell tie midpoint")
    row, col = nearest_lats[0][1], nearest_lons[0][1]
    grid_lat, grid_lon = era5.LATITUDE[row], era5.LONGITUDE[col]
    if abs(lat-grid_lat) > .125 or abs(lon-grid_lon) > .125:
        raise DWDGridComparisonBlocked("station cannot be represented by verified NRW ERA5 grid")
    # Local great-circle distance; this is a SUPPORT check, not interpolation.
    lat1, lat2 = math.radians(lat), math.radians(grid_lat)
    dlat = lat2-lat1
    dlon = math.radians(grid_lon - lon)
    hav = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    distance = 2*6371.0088*math.asin(min(1, math.sqrt(hav)))
    if not (0 <= distance <= MAX_SEPARATION_KM):
        raise DWDGridComparisonBlocked("station more than 20 km from current nearest ERA5 grid centre")
    return row, col, round(distance, 3)


def combine_original_2020_station_and_grid_peaks(
    stations: dict, weather: dict,
) -> dict:
    """Research event-maximum crosswalk; NO matched-hour bias/skill claim."""
    dwd.verify_first_original_2020_station_receipt_against_live(stations)
    if (stations.get("station_count") != 3
        or stations.get("historic_reference_time_interpretation_verified_as_UTC") is not False
        or stations.get("station_coordinates_reported_are_current_not_verified_historic_2020") is not True
        or stations.get("actual_2020_insurer_losses_or_building_vulnerability_calibrated") is not False
        or stations.get("native_NextGen_Oasis_GUL_IL_RI_OEP_AEP_admitted") is not False
        or weather.get("normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256")
            != ERA5_DECODED_96H_160_SHA
        or weather.get("actual_hourly_ERA5_original_grid_timestamps_verified") != 96
        or weather.get("original_source_0p25_degree_nodes") != 160
        or weather.get("previous_original_metadata_SHA256s_match") is not True
        or weather.get("German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted") is not False
        or weather.get("real_RV_insurer_claims_or_policy_terms_obtained") is not False):
        raise DWDGridComparisonBlocked("DWD station or ERA5 original-source scientific gate changed")
    peaks = weather.get("_internal_public_10x16_event_peak_gust_mps")
    if (not isinstance(peaks, list) or len(peaks) != len(era5.LATITUDE)
        or any(not isinstance(row, list) or len(row) != len(era5.LONGITUDE)
               for row in peaks)
        or any(type(gust) not in (int, float) or not math.isfinite(gust)
               or not 0 <= gust <= 150 for row in peaks for gust in row)):
        raise DWDGridComparisonBlocked("missing or invalid exact original 96h ERA5 grid-cell maxima")
    reports, grid_keys = [], set()
    records = stations.get("stations", [])
    if ([r.get("station_id") for r in records] != list(EXPECTED_STATIONS)):
        raise DWDGridComparisonBlocked("expected accepted 2020 original DWD station order changed")
    for station in records:
        lat = station.get("latitude_as_publisher_lists_today")
        lon = station.get("longitude_as_publisher_lists_today")
        row, col, separation = station_to_grid(lat, lon)
        gust = peaks[row][col]
        measured = station.get("measured_2020_02_08_through_11_max_hourly_gust_mps")
        if (type(measured) not in (int, float) or not math.isfinite(measured)
            or not 0 <= measured <= 150
            or station.get("original_station_fx911_hourly_valid_count") != 96
            or station.get("DWD_QN8_quality_level_hour_counts") != {"3": 96}
            or station.get("observed_station_max_gust_hours_full_96h") is not True):
            raise DWDGridComparisonBlocked("DWD source original measured 2020 gust/quality changed")
        grid_keys.add((row, col))
        reports.append({
            "original_dwd_station_id": station["station_id"],
            "original_dwd_station_name": station["name_as_publisher_lists_today"].split("    ")[0].strip(),
            "publisher_current_station_lat": lat,
            "publisher_current_station_lon": lon,
            "dwd_measured_original_2020_96h_peak_FX911_mps": measured,
            "dwd_peak_hour_label_unharmonized": station[
                "measured_2020_Ciara_window_peak_hour_as_publisher_reports"
            ],
            "dwd_original_zip_sha256": station["provider_original_zip_sha256"],
            "dwd_observed_hour_count": 96,
            "dwd_QN8_quality_level": 3,
            "nearest_era5_grid_lat": era5.LATITUDE[row],
            "nearest_era5_grid_lon": era5.LONGITUDE[col],
            "distance_publisher_current_station_to_era5_grid_km": separation,
            "google_era5_modelled_original_2020_96h_peak_10fg_mps": gust,
            "descriptive_peak_difference_era5_minus_dwd_mps_not_bias_or_skill": round(gust - measured, 6),
            "matched_hourly_time_support_and_station_instrument_verified": False,
        })
    if len(grid_keys) != 2 or len(reports) != 3:
        raise DWDGridComparisonBlocked("three measured DWD stations must map to exactly two actual ERA5 cells")
    if (reports[0]["nearest_era5_grid_lat"], reports[0]["nearest_era5_grid_lon"]) != (
        reports[2]["nearest_era5_grid_lat"], reports[2]["nearest_era5_grid_lon"]
    ):
        raise DWDGridComparisonBlocked("Cologne and Koenigswinter shared ERA5 cell changed")
    return {
        "schema": SCHEMA,
        "status": "RESEARCH_ONLY_THREE_MEASURED_DWD_STATION_PEAKS_VS_TWO_MODELLED_ERA5_CELL_PEAKS",
        "DWD_source": dwd.INDEX,
        "DWD_source_license": "CC BY 4.0; Deutscher Wetterdienst attribution required",
        "ERA5_source": weather.get("public_original_source"),
        "ERA5_source_license": "Copernicus Licence; C3S and Google Research attribution",
        "ERA5_2020_original_decoded_96h_160_SHA256": ERA5_DECODED_96H_160_SHA,
        "event_window_calendar_days": list(STUDY_DATE),
        "source_verified_dwd_stations": 3,
        "source_verified_unique_nearest_era5_grid_cells": len(grid_keys),
        "total_original_DWD_FX911_observed_hours": 288,
        "station_to_original_ERA5_peak_only": reports,
        "DWD_2020_station_historic_instrument_and_geography_verified": False,
        "DWD_2020_hour_label_UTC_and_gust_window_aligned_with_ERA5": False,
        "matched_hour_errors_RMSE_or_model_skill_admitted": False,
        "2020_actual_RV_insured_sites_or_claims_observed": False,
        "German_wind_damage_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted": False,
        "annual_event_frequency_or_capital_model_admitted": False,
    }


FIRST_ACTUAL_SOURCE_COMPARISON = (
    Path(__file__).resolve().parents[1] /
    "research/observations/ciara2020_dwd3_era5_two_cells_original_peak_comparison_20261114.toml"
)


def verify_first_original_station_era5_comparison_receipt(result: dict) -> None:
    """Fail closed on the very first independently verified actual 2020 result."""
    with FIRST_ACTUAL_SOURCE_COMPARISON.open("rb") as f:
        actual = tomllib.load(f)
    if (
        actual.get("schema") != SCHEMA
        or actual.get("status") != result.get("status")
        or actual.get("first_genuine_source_comparison_github_run") != 43603655228
        or actual.get("first_genuine_source_comparison_github_job") != 132473533297
        or actual.get("ERA5_original_2020_96x160_decoded_float32_le_sha256") != ERA5_DECODED_96H_160_SHA
        or result.get("ERA5_2020_original_decoded_96h_160_SHA256") != ERA5_DECODED_96H_160_SHA
        or actual.get("source_genuine_DWD_stations") != 3
        or actual.get("source_genuine_distinct_ERA5_025degree_nodes") != 2
        or actual.get("source_DWD_original_2020_hour_values_total") != 288
        or actual.get("publisher_current_locations_not_verified_historical_2020") is not True
        or actual.get("2020_DWD_hour_reference_and_ERA5_window_UTC_harmonized") is not False
        or actual.get("station_2020_instrument_height_exposure_verified") is not False
        or actual.get("ERA5_bias_RMSE_skill_model_approved") is not False
        or actual.get("actual_2020_real_RV_insurer_sites_claims_observed") is not False
        or actual.get("native_GUL_IL_RI_OEP_AEP_or_annual_EP_approved") is not False
        or result.get("DWD_2020_station_historic_instrument_and_geography_verified") is not False
        or result.get("matched_hour_errors_RMSE_or_model_skill_admitted") is not False
        or result.get("German_wind_damage_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted") is not False
        or result.get("source_verified_dwd_stations") != 3
        or result.get("source_verified_unique_nearest_era5_grid_cells") != 2
        or result.get("total_original_DWD_FX911_observed_hours") != 288
    ):
        raise DWDGridComparisonBlocked("first real historical DWD/ERA5 comparison identity or scientific no-go drift")
    station_data = result.get("station_to_original_ERA5_peak_only", [])
    if len(station_data) != 3 or len(actual.get("stations", [])) != 3:
        raise DWDGridComparisonBlocked("first accepted three DWD/two ERA5 station population changed")
    pairs = (
        ("station_id", "original_dwd_station_id"),
        ("original_DWD_zip_sha256", "dwd_original_zip_sha256"),
        ("publisher_current_lat", "publisher_current_station_lat"),
        ("publisher_current_lon", "publisher_current_station_lon"),
        ("nearest_era5_grid_lat", "nearest_era5_grid_lat"),
        ("nearest_era5_grid_lon", "nearest_era5_grid_lon"),
        ("distance_to_grid_km", "distance_publisher_current_station_to_era5_grid_km"),
        ("DWD_original_observed_hourly_gust_count", "dwd_observed_hour_count"),
        ("DWD_QN_8", "dwd_QN8_quality_level"),
        ("DWD_observed_2020_event_peak_FX911_mps", "dwd_measured_original_2020_96h_peak_FX911_mps"),
        ("original_google_era5_2020_event_peak_10fg_mps", "google_era5_modelled_original_2020_96h_peak_10fg_mps"),
        ("descriptive_ERA5_minus_DWD_peak_difference_mps_not_model_bias",
         "descriptive_peak_difference_era5_minus_dwd_mps_not_bias_or_skill"),
    )
    for original, observed in zip(actual["stations"], station_data):
        if any(original.get(k) != observed.get(v) for k, v in pairs):
            raise DWDGridComparisonBlocked("verified first original 2020 DWD station/ERA5 peak data changed")
        if observed.get("matched_hourly_time_support_and_station_instrument_verified") is not False:
            raise DWDGridComparisonBlocked("station UTC and instrument not actually harmonized")


def live_original_comparison() -> dict:
    measured = dwd.live_dwd_2020_original_three_stations()
    dwd.verify_first_original_2020_station_receipt_against_live(measured)
    original_weather = era5.original_96h_grid(include_public_grid_peaks=True)
    result = combine_original_2020_station_and_grid_peaks(measured, original_weather)
    verify_first_original_station_era5_comparison_receipt(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--dry-run", action="store_true")
    options.add_argument("--live-original-station-grid", action="store_true")
    args = parser.parse_args()
    try:
        if args.dry_run:
            receipt = {
                "schema": SCHEMA,
                "status": "SOURCE_ORIGINAL_2020_DWD_PLUS_GOOGLE_ARCO_STATION_GRID_CANDIDATE_NOT_FETCHED",
                "dwd_original_station_count": 3,
                "ERA5_actual_distinct_gridpoint_count_expected": 2,
                "2020_original_sources_reloaded": False,
                "skill_or_insurer_damage_admitted": False,
            }
        else:
            receipt = live_original_comparison()
        print(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=True))
        return 0
    except (DWDGridComparisonBlocked, dwd.OriginalDWDRejected,
            era5.RealGridBlocked, OSError, ValueError) as exc:
        parser.exit(2, "DWD_ERA5_CIARA2020_STATION_GRID_PEAK_COMPARISON_NO_GO: "+str(exc)+"\n")


if __name__ == "__main__":
    sys.exit(main())
