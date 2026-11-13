# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned 2022 public NRW 10k candidates × ORIGINAL 2020 Ciara 10fg.

This is a meteorological counterfactual: public 2022 building candidates
are mapped to maximum 2020 Google ARCO reanalysis gust at a 0.25° grid
centre. Insurance policy count and TIV are entirely fictional.
NO observed insurer losses, R+V insured risks, vulnerability curve,
annual frequency, native GUL, IL, RI, OEP, AEP, or SCR may be inferred.
Only 93 aggregated cells, not 10k individual sites, are published.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import ROUND_HALF_UP
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import tomllib
import zipfile

import ciara2020_nrw_10k_era5_area_request_v0 as area
import ciara2020_google_arco_real_96h_nrw_area_v0 as wind

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CELL_CSV = ROOT / "research/observations/ciara2020_nrw_hu22_10k_93cell_source_aggregate_v0.csv"
SOURCE_CELL_CSV_SHA256 = "fe012f9e0a42b67ad7b73b49bb7ca24edd1be7c785db2321b3997ebc466315e7"
SOURCE_COUNT_SIGNATURE_SHA256 = "de10099a9b79febb1a254bc765dc477a47589cb1f49ba75415bfe6b9723c2ebd"
ORIGINAL_ERA5_MATRIX_SHA256 = "5fb7c41963a94f88ee3651b51bfa84cc2f4bf379e1ee6f4eb4a4fb597d37f932"
EXPECTED_SITES = 10_000
EXPECTED_CELLS = 93
EXPECTED_COUNTIES = 53
EXPECTED_TIV = 4_826_029_500
SCHEMA = "CIARA2020_NRW_HU22_10K_PUBLIC_SITE_ERA5_GUST_COUNTERFACTUAL_V0"
THRESHOLDS = (25, 30, 35, 40)
CSV_COLUMNS = ("latitude_quarter_index", "longitude_quarter_index",
               "public_building_candidate_count", "fictional_building_tiv_eur")


class CiaraCounterfactualBlocked(ValueError):
    """Source-identity, weather or science support mismatch."""


def load_source_cell_aggregates(path: Path = SOURCE_CELL_CSV) -> dict[tuple[int, int], tuple[int, int]]:
    """Validate exact public 2022 HU-derived 93-cell CSV bytes and population."""
    if (path.is_symlink() or not path.is_file()
        or not 100 <= path.stat().st_size < 10_000):
        raise CiaraCounterfactualBlocked("source cell CSV must be one bounded regular file")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_CELL_CSV_SHA256:
        raise CiaraCounterfactualBlocked("93-cell HU22 source bytes mismatch pinned SHA256")
    try:
        csv_reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True)
        if tuple(csv_reader.fieldnames or ()) != CSV_COLUMNS:
            raise CiaraCounterfactualBlocked("exact source aggregate CSV schema required")
        result = {}
        previous_key = None
        for record in csv_reader:
            try:
                key = (int(record["latitude_quarter_index"]),
                       int(record["longitude_quarter_index"]))
                sites = int(record["public_building_candidate_count"])
                tiv = int(record["fictional_building_tiv_eur"])
            except (ValueError, KeyError, TypeError) as exc:
                raise CiaraCounterfactualBlocked("invalid source-derived cell count or value") from exc
            if (any(record[k] != str(v) for k, v in zip(CSV_COLUMNS, (*key, sites, tiv)))
                or not 201 <= key[0] <= 210 or not 23 <= key[1] <= 38
                or previous_key is not None and not previous_key < key
                or not 1 <= sites <= EXPECTED_SITES or not 0 < tiv <= EXPECTED_TIV):
                raise CiaraCounterfactualBlocked("unbounded, duplicated or unordered original cell")
            previous_key = key
            result[key] = (sites, tiv)
    except (UnicodeError, csv.Error) as exc:
        raise CiaraCounterfactualBlocked("source 93-cell CSV invalid encoding") from exc
    if (len(result) != EXPECTED_CELLS
        or sum(n for n, _ in result.values()) != EXPECTED_SITES
        or sum(t for _, t in result.values()) != EXPECTED_TIV):
        raise CiaraCounterfactualBlocked("source 10k population / 93-cell / fictional-TIV sum drift")
    signature = "".join(
        f"{la}:{lo}:{result[la,lo][0]}\n" for la, lo in sorted(result)
    ).encode("ascii")
    if hashlib.sha256(signature).hexdigest() != SOURCE_COUNT_SIGNATURE_SHA256:
        raise CiaraCounterfactualBlocked("original 93-cell occupancy signature drift")
    return result


def validate_original_zip_against_source_cells(path: Path) -> dict:
    """Offline reproduce from actual 2022 HU source-derived archive, not fake rows."""
    # plan_from_archived_source verifies the entire archive SHA, three
    # constituent CSV byte SHA pins, account/physical evidence crosswalk,
    # 53 original NRW counties, building use classification and fictional TIV.
    plan = area.plan_from_archived_source(path)
    if (plan.get("source_derived_10k_archive_sha256") != area.SOURCE_ARTIFACT_SHA256
        or plan.get("occupied_grid_nodes_by_public_building_candidates") != EXPECTED_CELLS
        or plan.get("occupied_nodes_count_sha256") != SOURCE_COUNT_SIGNATURE_SHA256
        or plan.get("source_2022_NRW_counties") != EXPECTED_COUNTIES
        or plan.get("public_building_candidates") != EXPECTED_SITES
        or plan.get("historical_source_fictional_building_TIV_EUR") != EXPECTED_TIV):
        raise CiaraCounterfactualBlocked("2022 public-source archive does not match frozen 93 cells")
    with zipfile.ZipFile(path) as archived:
        source_rows = area._read_csv(archived.read("location.csv"))
    recomputed = Counter()
    value = Counter()
    for site in source_rows:
        lat = area._coordinate(site["Latitude"], "50", "52.8") / area.STEP
        lon = area._coordinate(site["Longitude"], "5.5", "10") / area.STEP
        key = (int(lat.to_integral_value(rounding=ROUND_HALF_UP)),
               int(lon.to_integral_value(rounding=ROUND_HALF_UP)))
        recomputed[key] += 1
        value[key] += int(site["BuildingTIV"])
    if dict((k, (recomputed[k], value[k])) for k in recomputed) != load_source_cell_aggregates():
        raise CiaraCounterfactualBlocked("live 10k original archive differs from pinned 93-cell count/TIV")
    return {
        "schema": SCHEMA,
        "status": "ACTUAL_ORIGINAL_HU22_10K_ZIP_REPRODUCED_93_CELL_SOURCE_AGGREGATES_NO_WEATHER",
        "source_derived_10k_archive_sha256": area.SOURCE_ARTIFACT_SHA256,
        "original_2022_HU_archive_sha256": plan["historical_original_NRW_HU2022_zip_sha256"],
        "reproduced_cells": len(recomputed),
        "reproduced_public_building_candidates": sum(recomputed.values()),
        "reproduced_2022_counties": EXPECTED_COUNTIES,
        "fictional_tiv_eur": sum(value.values()),
        "source_93cell_csv_sha256": SOURCE_CELL_CSV_SHA256,
        "real_RV_insured_sites_or_2020_claims": False,
        "actual_2020_google_weather_join_executed": False,
        "German_wind_damage_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def summarize_exposure_by_public_source_grid(
    cells: dict[tuple[int, int], tuple[int, int]], peaks: list[list[float]]
) -> dict:
    """Pure deterministic 93-source-cell weighted *hazard* at real 2020 wind."""
    if (len(cells) != EXPECTED_CELLS
        or len(peaks) != 10 or any(len(row) != 16 for row in peaks)
        or any(type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 150
               for row in peaks for p in row)):
        raise CiaraCounterfactualBlocked("incorrect 160 original meteorological wind maxima grid")
    selected = []
    for (quarter_lat, quarter_lon), (count, tiv) in sorted(cells.items()):
        row, col = 210 - quarter_lat, quarter_lon - 23
        if (not 0 <= row < 10 or not 0 <= col < 16
            or type(count) is not int or type(tiv) is not int
            or count < 1 or tiv < 1):
            raise CiaraCounterfactualBlocked("source 2022 public cell outside original 2020 grid")
        selected.append((float(peaks[row][col]), count, tiv))
    if (sum(n for _, n, _ in selected) != EXPECTED_SITES
        or sum(v for _, _, v in selected) != EXPECTED_TIV):
        raise CiaraCounterfactualBlocked("source population/TIV not conserved in wind overlay")
    statistics = {}
    for threshold in THRESHOLDS:
        matched = [(n, tiv) for gust, n, tiv in selected if gust >= threshold]
        statistics[str(threshold)] = {
            "public_2022_building_candidate_count": sum(n for n, _ in matched),
            "fictional_2025_like_building_tiv_eur": sum(v for _, v in matched),
            "distinct_occupied_0p25deg_grid_cells": len(matched),
        }
    return {
        "source_occupied_original_2022_building_grid_cells": len(selected),
        "public_2022_building_candidate_count": sum(n for _, n, _ in selected),
        "fictional_2025_like_building_tiv_eur": sum(v for _, _, v in selected),
        "candidate_weighted_2020_ciara_96h_peak_wind_mps": math.fsum(
            p * n for p, n, _ in selected) / EXPECTED_SITES,
        "fictional_tiv_weighted_2020_ciara_96h_peak_wind_mps": math.fsum(
            p * v for p, _, v in selected) / EXPECTED_TIV,
        "occupied_grid_cell_peak_mps_min": min(p for p, _, _ in selected),
        "occupied_grid_cell_peak_mps_max": max(p for p, _, _ in selected),
        "peak_wind_hazard_threshold_mps": statistics,
    }


ACCEPTED_SOURCE_JOIN_TOML = (
    ROOT / "research/observations/"
    "ciara2020_nrw_hu22_10k_public_2022_2020_gust_counterfactual_receipt_v0.toml"
)


def require_independently_accepted_actual_source_counterfactual(result: dict) -> None:
    """Freeze independently observed 2020/2022 COUNTERFACTUAL exposure only."""
    with ACCEPTED_SOURCE_JOIN_TOML.open("rb") as accepted_file:
        source = tomllib.load(accepted_file)
    if (source.get("schema") != SCHEMA
        or source.get("status") != result.get("status")
        or source.get("first_successful_original_live_github_run") != 43489088388
        or source.get("first_successful_original_live_github_job") != 132105176207
        or source.get("source_original_2022_HU_derived_10k_archive_sha256")
            != area.SOURCE_ARTIFACT_SHA256
        or source.get("source_original_2022_HU_10k_93cell_csv_sha256")
            != SOURCE_CELL_CSV_SHA256
        or source.get("source_10k_93cell_occupancy_signature_sha256")
            != SOURCE_COUNT_SIGNATURE_SHA256
        or source.get("2020_google_arco_original_96h_160cell_decoded_sha256")
            != ORIGINAL_ERA5_MATRIX_SHA256
        or result.get("2020_google_arco_original_decoded_96h_160cell_sha256")
            != ORIGINAL_ERA5_MATRIX_SHA256
        or source.get("public_2022_building_candidate_count") != EXPECTED_SITES
        or source.get("source_2022_NRW_counties") != EXPECTED_COUNTIES
        or source.get("source_2022_occupied_0p25deg_grid_cells") != EXPECTED_CELLS
        or source.get("fictional_building_tiv_eur") != EXPECTED_TIV
        or source.get("historical_2020_google_era5_hourly_gust_frames") != 96):
        raise CiaraCounterfactualBlocked("accepted independent source/2020 weather receipt changed")
    field_map = (
        ("candidate_weighted_2020_ciara_96h_peak_wind_mps",
         "candidate_weighted_2020_ciara_96h_peak_wind_mps"),
        ("fictional_tiv_weighted_2020_ciara_96h_peak_wind_mps",
         "fictional_tiv_weighted_2020_ciara_96h_peak_wind_mps"),
        ("source_occupied_cell_96h_peak_gust_mps_min",
         "occupied_grid_cell_peak_mps_min"),
        ("source_occupied_cell_96h_peak_gust_mps_max",
         "occupied_grid_cell_peak_mps_max"),
    )
    if any(source.get(key) != result.get(value_key) for key, value_key in field_map):
        raise CiaraCounterfactualBlocked("actual 10k 2020 wind exposure statistics differ from first original live source")
    thresholds = result.get("peak_wind_hazard_threshold_mps", {})
    accepted_thresholds = source.get("threshold_mps", {})
    if set(accepted_thresholds) != {str(x) for x in THRESHOLDS} or set(thresholds) != set(accepted_thresholds):
        raise CiaraCounterfactualBlocked("real 2020 hazard threshold set changed")
    for threshold in THRESHOLDS:
        actual = thresholds[str(threshold)]
        accepted = accepted_thresholds[str(threshold)]
        if (actual.get("public_2022_building_candidate_count")
            != accepted.get("public_2022_building_candidate_count")
            or actual.get("fictional_2025_like_building_tiv_eur")
            != accepted.get("fictional_building_tiv_eur")
            or actual.get("distinct_occupied_0p25deg_grid_cells")
            != accepted.get("occupied_grid_cells")):
            raise CiaraCounterfactualBlocked("2020 original 10fg × source-derived 2022 wind threshold parity failed")
    if (any(source.get(flag) is not False for flag in (
        "public_2022_building_occupancy_as_of_2020_verified",
        "real_RV_2020_insured_site_universe_observed",
        "2020_insurer_coverage_or_claims_observed",
        "original_GCS_compressed_chunk_SHA_or_CDS_GRIB_parity_verified",
        "German_wind_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted",
        "annual_stochastic_EP_or_capital_model_admitted",
    )) or result.get("German_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted") is not False
        or result.get("annual_stochastic_EP_or_capital_model_admitted") is not False
        or result.get("individual_sites_or_polygon_coordinates_published") is not False):
        raise CiaraCounterfactualBlocked("real insurer model/no-original-loss scientific quarantine changed")


def run_live_counterfactual() -> dict:
    cells = load_source_cell_aggregates()
    # Existing full 96-hour Google ARCO weather reader repeats publisher
    # metadata SHA checks, the earlier independently verified 1h gust
    # parity, and 96x160 decoded data SHA from real GitHub CI. The grid
    # peaks are returned only in memory and not via public original CLI.
    weather = wind.original_96h_grid(include_public_grid_peaks=True)
    matrix = weather.pop("_internal_public_10x16_event_peak_gust_mps", None)
    if (weather.get("normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256")
        != ORIGINAL_ERA5_MATRIX_SHA256
        or weather.get("actual_hourly_ERA5_original_grid_timestamps_verified") != 96
        or weather.get("original_source_0p25_degree_nodes") != 160
        or weather.get("previous_original_metadata_SHA256s_match") is not True
        or weather.get("real_RV_insurer_claims_or_policy_terms_obtained") is not False
        or weather.get("German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted") is not False
        or not isinstance(matrix, list)):
        raise CiaraCounterfactualBlocked("real weather source identity or science gate drift")
    summary = summarize_exposure_by_public_source_grid(cells, matrix)
    result = {
        "schema": SCHEMA,
        "status": "2020_ORIGINAL_GOOGLE_ERA5_WIND_ON_2022_PUBLIC_BUILDINGS_10K_COUNTERFACTUAL_NO_LOSS",
        "source_original_2022_hu22_derived_fictional_10k_archive_sha256": area.SOURCE_ARTIFACT_SHA256,
        "source_original_2022_hu22_10k_93cell_csv_sha256": SOURCE_CELL_CSV_SHA256,
        "source_original_building_count_signature_sha256": SOURCE_COUNT_SIGNATURE_SHA256,
        "2020_google_arco_original_hourly_10fg_source": weather.get("public_original_source"),
        "2020_google_arco_original_decoded_96h_160cell_sha256": ORIGINAL_ERA5_MATRIX_SHA256,
        "historical_2020_hourly_gust_frames": 96,
        "2022_public_NRW_Kreise_represented": EXPECTED_COUNTIES,
        "2020_wind_source_C3S_attribution": "Copernicus Climate Change Service (C3S), Google Research ARCO-ERA5",
        **summary,
        "risk_interpretation": "hypothetical wind exposure; 2022 public candidates placed into 2020 storm",
        "underlying_2020_real_RV_policy_positions_or_claims_observed": False,
        "actual_2020_NRWs_buildings_assumed_identical_to_2022": False,
        "wind_2020_to_2022_public_exposure_is_counterfactual": True,
        "original_2020_CDS_GRIB_or_compressed_GCS_chunk_sha_independently_verified": False,
        "German_vulnerability_native_GUL_IL_RI_OEP_AEP_admitted": False,
        "annual_stochastic_EP_or_capital_model_admitted": False,
        "individual_sites_or_polygon_coordinates_published": False,
    }
    require_independently_accepted_actual_source_counterfactual(result)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--verify-source-zip", type=Path)
    mode.add_argument("--live-google", action="store_true")
    args = p.parse_args()
    try:
        if args.dry_run:
            cells = load_source_cell_aggregates()
            result = {
                "schema": SCHEMA,
                "status": "2022_PUBLIC_SOURCE_93_CELLS_VERIFIED_2020_GOOGLE_REPLAY_NOT_EXECUTED",
                "source_93cell_csv_sha256": SOURCE_CELL_CSV_SHA256,
                "public_building_candidates": sum(n for n, _ in cells.values()),
                "source_occupied_nodes": len(cells),
                "2020_public_google_live_weather_join_executed": False,
                "real_insured_claims_or_loss_model": False,
            }
        elif args.verify_source_zip is not None:
            result = validate_original_zip_against_source_cells(args.verify_source_zip)
        else:
            result = run_live_counterfactual()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (CiaraCounterfactualBlocked, area.CiaraAreaBlocked, wind.RealGridBlocked,
            OSError, ValueError, zipfile.BadZipFile) as exc:
        p.exit(2, "CIARA2020_HU22_10K_PUBLIC_GRID_HAZARD_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
