# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned one-storm XWS Daria wind/exposure sensitivity; NO loss or EP.

Combines a previously archived 10k original NRW HU2022 physical-candidate
fictional OED and the original-XWS-derived Daria1990 historical gust receipt.
Only original-derived CSVs with exact independently audited SHA256 are admitted.
Different historical vintages are never inferred to be actual insured sites.
All three rebuild cost/storey assumptions are fictional, not observed TIV.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from rva_nrw_hu22_geocoded_area_rebuild_tiv_v0 import SCENARIOS
from rva_nrw_hu22_to_nextgen_c3s_spatial_v0 import SOURCE_SHA, SOURCE_SCHEMA
from rva_nrw_hu_gfk_residential_candidate_v0 import classify_gfk
from rva_nrw_xws_daria_10k_original_gust_overlay_v0 import (
    SCHEMA as WIND_SCHEMA, PINNED_SOURCE_FILES, MAX_DISTANCE_KM
)

OED_PINS = {
    "account.csv": "fe5f7fc20bc2fbd4001c79a169d7cac5a925f71b83059737c29632658c9e20a0",
    "location.csv": "c3ebcba4ab7279e4275cbb867c20271109935d0e8ba1063dbf67231a2547df3c",
    "physical_candidate_evidence.csv": "360ed86bd5ebda1346132951755ba8507c5eac97a7716b8b2e7291f8d41df207",
}
WIND_PINS = {
    "daria_1990_original_source_site_gust_only.csv": "c2de478fb9164073805f9a41548de50a182d89b23662240c89dd7a24ef58c879",
    "daria_1990_NRW_53kreis_event_gust_summary.csv": "6838e0784807b01156793af97741edbdd76acc408b87fb2374fd271d02aa3e24",
}
SITES = 10_000
COUNTIES = 53
ORIGINAL_FICTIONAL_TIV = 4_826_029_500
THRESHOLDS = (25, 30, 35, 40)
WIND_FIELDS = {
    "lower95": "Daria1990Lower95GustMps",
    "mean": "Daria1990MeanGustMps",
    "upper95": "Daria1990Upper95GustMps",
}


class ExposureBlocked(ValueError):
    """Fail-closed input provenance, identity, or scientific boundary."""


def _archive(path: Path, pins: dict[str, str]) -> dict[str, bytes]:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 30_000_000:
        raise ExposureBlocked("bounded regular source-derived archive required")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        expected = set(pins) | {"manifest.json" if "location.csv" in pins
                                else "source_and_no_CAT_loss_manifest.json"}
        if (len(infos) != len(expected)
            or {entry.filename for entry in infos} != expected
            or any(entry.file_size > 12_000_000 or entry.flag_bits & 1 for entry in infos)
            or sum(entry.file_size for entry in infos) > 30_000_000
            or archive.testzip() is not None):
            raise ExposureBlocked("unsupported, oversized or corrupt archive members")
        blobs = {name: archive.read(name) for name in expected}
    for name, sha in pins.items():
        if hashlib.sha256(blobs[name]).hexdigest() != sha:
            raise ExposureBlocked("source-derived original CSV pin mismatch: " + name)
    return blobs


def _rows(blob: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(blob.decode("utf-8"), newline=""))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ExposureBlocked("missing/duplicate CSV fields")
    result = list(reader)
    if not result or any(None in row for row in result):
        raise ExposureBlocked("malformed source-derived CSV records")
    return result


def _unique(rows: list[dict[str, str]], key: str, expected: int) -> dict[str, dict[str, str]]:
    if len(rows) != expected or any(not row.get(key) for row in rows):
        raise ExposureBlocked("source-derived population or ID missing")
    keyed = {row[key]: row for row in rows}
    if len(keyed) != expected:
        raise ExposureBlocked("duplicate source/fictional identifier")
    return keyed


def _decimal(text: str, lo: str, hi: str) -> Decimal:
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise ExposureBlocked("unparseable source numeric") from exc
    if not value.is_finite() or not Decimal(lo) <= value <= Decimal(hi):
        raise ExposureBlocked("numeric source outside bounded physical/research range")
    return value


def aggregate(locations: list[dict[str, str]], accounts: list[dict[str, str]],
              evidence: list[dict[str, str]], wind: list[dict[str, str]],
              county: list[dict[str, str]], *,
              expected_sites: int = SITES, expected_counties: int = COUNTIES) -> dict:
    """Pure unprivileged identity-checked 3x3x4 hazard/TIV research comparison."""
    loc = _unique(locations, "LocNumber", expected_sites)
    acc = _unique(accounts, "AccNumber", expected_sites)
    phy = _unique(evidence, "LocNumber", expected_sites)
    gust = _unique(wind, "FictionalSiteId", expected_sites)
    county_map = _unique(county, "KreisAGS2022", expected_counties)
    if set(loc) != set(acc) or set(loc) != set(phy) or set(loc) != set(gust):
        raise ExposureBlocked("1:1 OED account/location/physical/gust crosswalk failed")
    county_counts = Counter()
    county_original_tiv = Counter()
    county_gte25 = Counter()
    county_tiv_gte25 = Counter()
    value_map: dict[str, dict[str, int]] = {name: {} for name in SCENARIOS}
    gust_map: dict[str, dict[str, Decimal]] = {}
    base_tiv = 0
    for site_id, row in loc.items():
        if (row.get("AccNumber") != site_id or acc[site_id].get("AccNumber") != site_id
            or row.get("CountryCode") != "DE" or row.get("OEDVersion") != "5.0.0"):
            raise ExposureBlocked("original fictional policy identity or OED schema drift")
        ev, wx = phy[site_id], gust[site_id]
        kreis = row.get("LocGroup", "")
        if (len(kreis) != 11 or not kreis.startswith("KREIS-05")
            or not kreis[6:].isascii() or not kreis[6:].isdigit()
            or ev.get("KreisAGS2022") != kreis[6:]
            or wx.get("Original2022KreisAGS") != kreis[6:]
            or wx.get("ActualRVInsuredSiteObserved") != "false"
            or ev.get("SourcePhysicalCandidateNotInsuredSite") != "true"
            or classify_gfk(ev.get("SourceGFK", ""))[0] != "residential_function_candidate_only"):
            raise ExposureBlocked("county, GFK, or insurer-observation boundary drift")
        area = _decimal(ev.get("SourceFootprintAreaM2"), "20", "100000")
        distance = _decimal(wx.get("NearestXWSGridPointKm"), "0", str(MAX_DISTANCE_KM))
        _ = distance  # validated spatial distance is evidence, not loss severity
        try:
            old_tiv = int(row.get("BuildingTIV", ""))
            original_wind_tiv = int(wx.get("Fictional2025BuildingTIVEUR", ""))
        except (TypeError, ValueError) as exc:
            raise ExposureBlocked("unparseable fictional source TIV") from exc
        if (not 0 < old_tiv <= 500_000_000 or str(old_tiv) != row["BuildingTIV"]
            or old_tiv != original_wind_tiv):
            raise ExposureBlocked("historical gust/source OED fictional TIV mismatch")
        vals = {name: _decimal(wx.get(field), "0", "200")
                for name, field in WIND_FIELDS.items()}
        if not vals["lower95"] <= vals["mean"] <= vals["upper95"]:
            raise ExposureBlocked("one-event wind uncertainty ordering drift")
        gust_map[site_id] = vals
        county_id = kreis[6:]
        county_counts[county_id] += 1
        county_original_tiv[county_id] += old_tiv
        base_tiv += old_tiv
        if vals["mean"] >= 25:
            county_gte25[county_id] += 1
            county_tiv_gte25[county_id] += old_tiv
        for name, (storeys, euro_m2) in SCENARIOS.items():
            tiv = int((area * Decimal(storeys) * Decimal(euro_m2)).quantize(
                Decimal(1), rounding=ROUND_HALF_UP))
            if not 0 < tiv <= 500_000_000:
                raise ExposureBlocked("fictional rebuilding TIV scenario bound failed")
            value_map[name][site_id] = tiv
    if len(county_counts) != expected_counties or set(county_counts) != set(county_map):
        raise ExposureBlocked("county universe/representation incomplete")
    for kreis, item in county_map.items():
        if (int(item["FictionalSiteCount"]) != county_counts[kreis]
            or int(item["FictionalBuildingTIVEUR"]) != county_original_tiv[kreis]
            or int(item["FictionalBuildingsWithMeanGustGE25Mps"]) != county_gte25[kreis]
            or int(item["FictionalTIVWithMeanGustGE25MpsEUR"]) != county_tiv_gte25[kreis]):
            raise ExposureBlocked("original independent county wind/exposure receipt drift")
    result = {}
    for case, values in value_map.items():
        views = {}
        for variant in WIND_FIELDS:
            thresholds = {}
            for threshold in THRESHOLDS:
                selected = [site_id for site_id in loc
                            if gust_map[site_id][variant] >= threshold]
                thresholds[str(threshold)] = {
                    "public_candidate_site_count": len(selected),
                    "fictional_tiv_eur": sum(values[site_id] for site_id in selected),
                }
            views[variant] = thresholds
        result[case] = {
            "assumed_storeys": SCENARIOS[case][0],
            "assumed_rebuilding_eur_per_m2": SCENARIOS[case][1],
            "fictional_total_tiv_eur": sum(values.values()),
            "one_event_historical_gust_thresholds_mps": views,
        }
    return {
        "matched_original_derived_public_physical_candidates": expected_sites,
        "verified_NRW_counties": len(county_counts),
        "original_fictional_tiv_eur": base_tiv,
        "wind_views_are_one_physical_1990_storm": True,
        "event_gust_wind_is_not_a_damage_ratio": True,
        "original_1990_insurer_portfolio_or_rebuild_costs_observed": False,
        "German_wind_vulnerability_or_native_Oasis_NextGen_loss_calibrated": False,
        "annual_event_frequency_or_AEP_OEP_admitted": False,
        "fictional_rebuilding_value_cases": result,
    }


def analyze(original_oed_zip: Path, original_derived_wind_zip: Path) -> dict:
    source = _archive(original_oed_zip, OED_PINS)
    wind = _archive(original_derived_wind_zip, WIND_PINS)
    src = json.loads(source["manifest.json"])
    gust = json.loads(wind["source_and_no_CAT_loss_manifest.json"])
    if (src.get("schema") != SOURCE_SCHEMA
        or src.get("source_original_2022_HU_complete_archive_SHA256") != SOURCE_SHA
        or src.get("source_original_2022_HU_full_CRCs_verified") is not True
        or src.get("model_input_approved") is not False
        or src.get("insurer_building_TIV_observed") is not False
        or src.get("physical_building_footprints_are_actual_RV_insured_sites") is not False
        or src.get("physical_building_candidates_selected") != SITES
        or src.get("fictional_policy_count") != SITES
        or src.get("real_source_counties_represented") != COUNTIES
        or src.get("output_file_SHA256") != OED_PINS
        or gust.get("schema") != WIND_SCHEMA
        or gust.get("original_NRW_HU22_full_archived_SHA256") != SOURCE_SHA
        or gust.get("status") !=
            "REAL_XWS_HISTORICAL_WIND_HAZARD_ON_PUBLIC_GEOSITES_WITH_FICTIONAL_INSURANCE_ONLY"
        or gust.get("storm_uncertainty_variants_are_same_physical_event") is not True
        or gust.get("source_grid_IS_original_rotated_0p22_degree_not_C3S_0p25") is not True
        or gust.get("native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed") is not False
        or gust.get("German_wind_vulnerability_by_material_roof_construction_validated") is not False
        or gust.get("source_physical_building_site_count") != SITES
        or gust.get("source_2022_NRW_Kreise_count") != COUNTIES
        or gust.get("output_sha256") != WIND_PINS):
        raise ExposureBlocked("archival original source or no-CAT admission receipt drift")
    source_files = gust.get("provider_original_four_XWS_CSV_source_receipt", {}).get("original_files", {})
    pinned = {name: (entry.get("full_bytes"), entry.get("full_sha256"))
              for name, entry in source_files.items()}
    if pinned != PINNED_SOURCE_FILES:
        raise ExposureBlocked("original four XWS Daria publisher-file SHA/size drift")
    result = aggregate(
        _rows(source["location.csv"]), _rows(source["account.csv"]),
        _rows(source["physical_candidate_evidence.csv"]),
        _rows(wind["daria_1990_original_source_site_gust_only.csv"]),
        _rows(wind["daria_1990_NRW_53kreis_event_gust_summary.csv"])
    )
    if result["original_fictional_tiv_eur"] != ORIGINAL_FICTIONAL_TIV:
        raise ExposureBlocked("previous independently verified original OED TIV drift")
    return {
        "schema": "NRW_HU22_10K_XWS_DARIA1990_FICTIONAL_FOOTPRINT_TIV_EXPOSURE_V0",
        "status": "ONE_HISTORICAL_STORM_RESEARCH_HAZARD_EXPOSURE_NOT_LOSS_OR_EP",
        "public_NRW_original_2022_HU_full_archive_sha256": SOURCE_SHA,
        "original_derived_OED_CSV_sha256": OED_PINS,
        "original_derived_XWS_Daria_CSV_sha256": WIND_PINS,
        "original_XWS_four_publisher_CSV_sha256": {
            name: sha for name, (_, sha) in sorted(PINNED_SOURCE_FILES.items())
        },
        "source_vintages_are_different": "1990 wind / 2022 public buildings / fictional insurance",
        **result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_derived_oed_zip", type=Path)
    parser.add_argument("original_derived_daria_hazard_zip", type=Path)
    parser.add_argument("--out-receipt", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.original_derived_oed_zip, args.original_derived_daria_hazard_zip)
        payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
        if args.out_receipt:
            if (args.out_receipt.is_symlink() or args.out_receipt.exists()
                or not args.out_receipt.parent.is_dir()):
                raise ExposureBlocked("output receipt must be new regular path")
            args.out_receipt.write_text(payload, encoding="utf-8")
        print(payload)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(2, "SOURCE_BOUND_HAZARD_EXPOSURE_BLOCKED: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
