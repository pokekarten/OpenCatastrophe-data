# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exploratory paired DWD FX_911 / Google ARCO ERA5 10fg Ciara hours.

This compares DWD's documented UTC last-hour gust maxima with ERA5 hourly
postprocessed gust at the historically verified nearest grid centre. The
providers' exact interval boundaries remain unverified. Results describe
one storm and three stations (two unique grid cells), not model skill,
calibration, building vulnerability or insured loss.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
import math
import sys
import tomllib

import ciara2020_dwd_hourly_fx_original_station_observations_v0 as dwd
import ciara2020_dwd_historical_feb2020_station_attestation_v0 as historical
import ciara2020_google_arco_real_96h_nrw_area_v0 as era5

SCHEMA = "CIARA2020_DWD_ERA5_MATCHED_HOURLY_EXPLORATION_V0"
STATIONS = ("02667", "15200", "00603")
LAGS = (-1, 0, 1)
START = datetime(2020, 2, 8)


class MatchedHourBlocked(ValueError):
    """Source support or historical station identity changed."""


def stats(observed: list[float], modeled: list[float]) -> dict:
    if len(observed) != len(modeled) or len(observed) < 2:
        raise MatchedHourBlocked("paired series need at least two aligned observations")
    errors = [m - o for o, m in zip(observed, modeled)]
    mean_o = sum(observed) / len(observed)
    mean_m = sum(modeled) / len(modeled)
    cov = sum((o-mean_o)*(m-mean_m) for o,m in zip(observed,modeled))
    var_o = sum((o-mean_o)**2 for o in observed)
    var_m = sum((m-mean_m)**2 for m in modeled)
    return {
        "paired_hour_count": len(observed),
        "mean_error_era5_minus_dwd_mps": sum(errors)/len(errors),
        "mean_absolute_error_mps": sum(abs(e) for e in errors)/len(errors),
        "root_mean_square_error_mps": math.sqrt(sum(e*e for e in errors)/len(errors)),
        "pearson_correlation": cov/math.sqrt(var_o*var_m) if var_o and var_m else None,
        "DWD_peak_mps": max(observed),
        "ERA5_peak_mps": max(modeled),
    }


def matched_hour_report(station_hourly: dict, era5_hourly: dict,
                        attestation: dict) -> dict:
    if (not isinstance(station_hourly, dict) or set(station_hourly) != set(STATIONS)
        or not isinstance(era5_hourly, dict) or set(era5_hourly) != set(STATIONS)
        or attestation.get("DWD_original_site_geography_Feb2020_verified") is not True
        or attestation.get("DWD_original_sensor_height_type_Feb2020_verified") is not True
        or attestation.get("DWD_original_FX911_hour_reference_declared_UTC") is not True
        or attestation.get("DWD_FX911_and_ERA5_10fg_exact_gust_aggregation_same") is not False):
        raise MatchedHourBlocked("verified historical DWD station/UTC attestation required")
    metadata = {s["station_id"]: s for s in attestation.get("stations", [])}
    if set(metadata) != set(STATIONS):
        raise MatchedHourBlocked("historical station metadata population changed")
    grid = {}
    for station, row, col in (("02667",7,6),("15200",5,6),("00603",7,6)):
        m = metadata[station]
        if (m.get("nearest_2020_ERA5_grid_lat") != era5.LATITUDE[row]
            or m.get("nearest_2020_ERA5_grid_lon") != era5.LONGITUDE[col]):
            raise MatchedHourBlocked("historical station-to-original-grid mapping changed")
        grid[station] = (row,col)
    output = []
    for station in STATIONS:
        obs = station_hourly[station]
        mod = era5_hourly[station]
        expected = [(START+timedelta(hours=i)).strftime("%Y%m%d%H") for i in range(96)]
        if (not isinstance(obs, dict) or list(obs) != expected
            or not isinstance(mod, list) or len(mod) != 96
            or any(type(v) not in (int,float) or not math.isfinite(v) or not 0 <= v <= 150
                   for v in list(obs.values())+mod)):
            raise MatchedHourBlocked("each source must contain the exact 96 valid UTC event hours")
        observed = [float(obs[t]) for t in expected]
        lag_reports = {}
        for lag in LAGS:
            # Positive lag compares DWD label t against ERA5 label t+lag.
            pairs = [(observed[i],float(mod[i+lag])) for i in range(96)
                     if 0 <= i+lag < 96]
            lag_reports[str(lag)] = {
                "ERA5_label_offset_hours_relative_to_DWD": lag,
                "metrics": stats([x[0] for x in pairs],[x[1] for x in pairs]),
            }
        output.append({
            "DWD_station_id": station,
            "historical_2020_latitude": metadata[station]["original_DWD_station_latitude_as_of_Feb2020"],
            "historical_2020_longitude": metadata[station]["original_DWD_station_longitude_as_of_Feb2020"],
            "historical_2020_sensor_height_m": metadata[station]["original_FX911_anemometer_height_above_ground_m_as_of_Feb2020"],
            "ERA5_grid_latitude": metadata[station]["nearest_2020_ERA5_grid_lat"],
            "ERA5_grid_longitude": metadata[station]["nearest_2020_ERA5_grid_lon"],
            "station_to_grid_distance_km": metadata[station]["historical_station_to_ERA5_grid_centre_km"],
            "lag_sensitivity_all_offsets_reported_no_best_lag_selected": lag_reports,
        })
    if ((output[0]["ERA5_grid_latitude"],output[0]["ERA5_grid_longitude"])
        != (output[2]["ERA5_grid_latitude"],output[2]["ERA5_grid_longitude"])):
        raise MatchedHourBlocked("Cologne and Heiderhof must share the verified ERA5 node")
    return {
        "schema": SCHEMA,
        "status": "ONE_EVENT_PAIRED_HOURLY_EXPLORATION_NO_SKILL_OR_CALIBRATION",
        "study_window_DWD_UTC_hour_labels": ["2020-02-08T00Z", "2020-02-11T23Z"],
        "DWD_variable": "FX_911 highest wind gust of the last hour (m/s)",
        "ERA5_variable": "10fg postprocessed hourly gust (m/s)",
        "DWD_hour_labels_documented_UTC": True,
        "DWD_and_ERA5_exact_interval_boundaries_proven_equal": False,
        "historical_station_2020_geometry_and_instruments_verified": True,
        "station_height_adjustment_applied": False,
        "stations": len(output),
        "unique_ERA5_grid_nodes": 2,
        "stations_results": output,
        "annual_or_multi_storm_validation": False,
        "bias_or_model_skill_admitted": False,
        "wind_vulnerability_or_loss_calibrated": False,
        "raw_hourly_source_values_in_receipt": False,
    }


def live_report() -> dict:
    dwd_result = dwd.live_dwd_2020_original_three_stations()
    dwd.verify_first_original_2020_station_receipt_against_live(dwd_result)
    metadata = historical.live_feb2020_attestation()
    weather = era5.original_96h_grid(include_internal_station_hourly=True)
    if weather.get("normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256") != (
        "5fb7c41963a94f88ee3651b51bfa84cc2f4bf379e1ee6f4eb4a4fb597d37f932"):
        raise MatchedHourBlocked("original Google ARCO decoded 96h source SHA changed")
    dwd_hourly = {}
    for station in dwd_result["stations"]:
        original_zip = dwd._get_publisher_bytes(
            station["original_DWD_historical_FX_zip_url"], dwd.MAX_ZIP,
        )
        parsed = dwd.measured_2020_gust_from_original_zip(original_zip, station["station_id"],
                                                          include_internal_hourly=True)
        if parsed["provider_original_zip_sha256"] != station["provider_original_zip_sha256"]:
            raise MatchedHourBlocked("original DWD ZIP SHA differs from verified live source")
        dwd_hourly[station["station_id"]] = parsed["_internal_observed_hourly_fx911_mps"]
    return matched_hour_report(dwd_hourly,weather["_internal_station_era5_hourly_10fg_mps"],metadata)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run",action="store_true")
    g.add_argument("--live-event",action="store_true")
    args=p.parse_args()
    if args.dry_run:
        print(json.dumps({"schema":SCHEMA,"status":"NO_SOURCE_READ_DRY_RUN",
                          "requires_original_DWD_ERA5":True,"skill_admitted":False},indent=2))
        return 0
    try:
        # Do not print source-derived station measurements or metrics to
        # stdout. The reviewed aggregate receipt is versioned separately.
        live_report()
        print(json.dumps({"schema":SCHEMA,
                          "status":"LIVE_SOURCE_COMPARISON_COMPLETED_AGGREGATE_RECEIPT_REVIEW_REQUIRED",
                          "source_values_or_metrics_written_to_stdout":False,
                          "bias_or_model_skill_admitted":False},indent=2,sort_keys=True))
        return 0
    except (MatchedHourBlocked,dwd.OriginalDWDRejected,historical.HistoricalDWDNoGo,
            era5.RealGridBlocked,OSError) as exc:
        p.exit(2,"CIARA2020_MATCHED_HOUR_NO_GO: "+str(exc)+"\n")


if __name__ == "__main__":
    sys.exit(main())
