# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One bounded 2020 ERA5 area-request preview covering source-authenticated NRW sites.

This script never calls CDS or opens credentials. Public 2022 physical building
candidates linked to 2025-like *fictional* policies are NOT actual R&V sites.
ERA5 original data, Ciara losses, German wind vulnerability and annual EP
remain NOT ACQUIRED / NOT ADMITTED. Only aggregates, never site records, print.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

from rva_nrw_hu22_to_nextgen_c3s_spatial_v0 import SOURCE_SHA, SOURCE_SCHEMA
from rva_nrw_hu_gfk_residential_candidate_v0 import classify_gfk
from eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0 import (
    CONTRACT, DS, VAR, DATE_START, DATE_END, HOURS, validate_contract
)
import tomllib

# SHA of the 10k original-HU2022-derived fictional OED artefact from
# GitHub original-source workflow run 42097472463 / artifact 13447603258.
SOURCE_ARTIFACT_SHA256 = "5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757"
SOURCE_CSV_SHA256 = {
    "account.csv": "fe5f7fc20bc2fbd4001c79a169d7cac5a925f71b83059737c29632658c9e20a0",
    "location.csv": "c3ebcba4ab7279e4275cbb867c20271109935d0e8ba1063dbf67231a2547df3c",
    "physical_candidate_evidence.csv": "360ed86bd5ebda1346132951755ba8507c5eac97a7716b8b2e7291f8d41df207",
}
EXPECTED_SITES = 10000
EXPECTED_COUNTIES = 53
EXPECTED_SOURCE_TIV_EUR = 4_826_029_500
STEP = Decimal("0.25")
GRID_DEGREES_MAX = Decimal(5)
SOURCE_ARCHIVE_MEMBERS = set(SOURCE_CSV_SHA256) | {"manifest.json"}


class CiaraAreaBlocked(ValueError):
    """Unproven source, overstated spatial support or insurer model admission."""


def _read_csv(blob: bytes) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8"), newline=""), strict=True)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise CiaraAreaBlocked("missing or duplicate source CSV columns")
        data = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise CiaraAreaBlocked("invalid source CSV encoding or structure") from exc
    if not data or any(None in row or any(v is None for v in row.values()) for row in data):
        raise CiaraAreaBlocked("empty or malformed source CSV")
    return data


def _unique(rows: list[dict[str, str]], key: str, expected: int) -> dict[str, dict[str, str]]:
    if len(rows) != expected or any(not row.get(key) for row in rows):
        raise CiaraAreaBlocked("site/account/evidence population changed")
    result = {row[key]: row for row in rows}
    if len(result) != expected:
        raise CiaraAreaBlocked("duplicated physical source or fictional policy ID")
    return result


def _coordinate(text: str, lo: str, hi: str) -> Decimal:
    try:
        x = Decimal(text)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CiaraAreaBlocked("unparseable public WGS84 coordinate") from exc
    if not x.is_finite() or not Decimal(lo) < x < Decimal(hi):
        raise CiaraAreaBlocked("outside supported NRW coordinate range")
    # CDS point rounding is only described as 'nearest'; refuse exact ties
    # rather than silently guessing a server-specific tie-breaker.
    if x / STEP % 1 == Decimal("0.5"):
        raise CiaraAreaBlocked("ERA5 grid midpoint tie must be reviewed")
    return x


def build_area_plan(locations: list[dict], accounts: list[dict], physical: list[dict],
                    *, expected_sites: int = EXPECTED_SITES,
                    expected_counties: int = EXPECTED_COUNTIES,
                    expected_tiv: int = EXPECTED_SOURCE_TIV_EUR) -> dict:
    if (type(expected_sites) is not int or not 1 <= expected_sites <= 10000
        or type(expected_counties) is not int or not 1 <= expected_counties <= 53
        or type(expected_tiv) is not int or not 0 < expected_tiv <= 10**15):
        raise CiaraAreaBlocked("bounded research population required")
    by_site = _unique(locations, "LocNumber", expected_sites)
    acc = _unique(accounts, "AccNumber", expected_sites)
    ev = _unique(physical, "LocNumber", expected_sites)
    if set(by_site) != set(acc) or set(by_site) != set(ev):
        raise CiaraAreaBlocked("source and fictional insurance 1:1 crosswalk drift")
    lat_steps, lon_steps = [], []
    cell_counts: Counter[tuple[int, int]] = Counter()
    county_counts = Counter()
    orig_ids = set()
    original_tiv = 0
    for sid, row in by_site.items():
        evidence = ev[sid]
        county = row.get("LocGroup", "")
        if (not re.fullmatch(r"KREIS-05[0-9]{3}", county)
            or evidence.get("KreisAGS2022") != county[6:]
            or evidence.get("SourcePhysicalCandidateNotInsuredSite") != "true"
            or classify_gfk(evidence.get("SourceGFK", ""))[0] != "residential_function_candidate_only"
            or row.get("AccNumber") != sid or acc[sid].get("PolNumber") != sid
            or row.get("CountryCode") != "DE" or row.get("OEDVersion") != "5.0.0"
            or row.get("LocCurrency") != "EUR" or row.get("LocPerilsCovered") != "WW2"
            or acc[sid].get("OEDVersion") != "5.0.0"
            or not re.fullmatch(r"[0-9a-f]{64}", evidence.get("SourceOiSHA256", ""))):
            raise CiaraAreaBlocked("county, original building use, insured-site nonadmission or policy ID drift")
        if evidence["SourceOiSHA256"] in orig_ids:
            raise CiaraAreaBlocked("same public polygon assigned more than once")
        orig_ids.add(evidence["SourceOiSHA256"])
        try:
            tiv = int(row.get("BuildingTIV", ""))
        except (TypeError, ValueError) as exc:
            raise CiaraAreaBlocked("invalid fictional building value") from exc
        if not 0 < tiv <= 500_000_000 or str(tiv) != row["BuildingTIV"]:
            raise CiaraAreaBlocked("invalid fictional source building value")
        original_tiv += tiv
        lat = _coordinate(row.get("Latitude"), "50", "52.8") / STEP
        lon = _coordinate(row.get("Longitude"), "5.5", "10") / STEP
        nlat = int(lat.to_integral_value(rounding=ROUND_HALF_UP))
        nlon = int(lon.to_integral_value(rounding=ROUND_HALF_UP))
        cell_counts[(nlat, nlon)] += 1
        lat_steps.append(lat)
        lon_steps.append(lon)
        county_counts[county[6:]] += 1
    if original_tiv != expected_tiv or len(county_counts) != expected_counties:
        raise CiaraAreaBlocked("fictional value control or all-NRW-counties coverage changed")
    north = int(max(lat_steps).to_integral_value(rounding=ROUND_CEILING))
    south = int(min(lat_steps).to_integral_value(rounding=ROUND_FLOOR))
    west = int(min(lon_steps).to_integral_value(rounding=ROUND_FLOOR))
    east = int(max(lon_steps).to_integral_value(rounding=ROUND_CEILING))
    if (north <= south or east <= west
        or STEP * (north - south) > GRID_DEGREES_MAX
        or STEP * (east - west) > GRID_DEGREES_MAX
        or any(not (south <= la <= north and west <= lo <= east)
               for la, lo in cell_counts)):
        raise CiaraAreaBlocked("ERA5 spatial coverage or maximum 5-degree area violated")
    requested_nodes = (north - south + 1) * (east - west + 1)
    if not 1 <= len(cell_counts) <= requested_nodes <= 441:
        raise CiaraAreaBlocked("unbounded ERA5 atmospheric grid count")
    signature = "".join(
        f"{lat}:{lon}:{cell_counts[(lat,lon)]}\n" for lat,lon in sorted(cell_counts)
    ).encode("ascii")
    return {
        "schema": "CIARA2020_NRW_HU22_10K_ERA5_10FG_AREA_REQUEST_PLAN_V0",
        "status": "SOURCE_DERIVED_HAZARD_REQUEST_PREVIEW_NOT_DOWNLOADED_NOT_INSURER_MODEL",
        "official_source_dataset": DS,
        "official_source_doi": "10.24381/1cf1ad76",
        "request": {
            "variable": [VAR],
            "date": [DATE_START, DATE_END],
            "area": [float(STEP * n) for n in (north, west, south, east)],
            "data_format": "netcdf",
        },
        "area_order": "north_west_south_east",
        "requested_atmospheric_grid_nodes_0p25deg": requested_nodes,
        "occupied_grid_nodes_by_public_building_candidates": len(cell_counts),
        "occupied_nodes_count_sha256": hashlib.sha256(signature).hexdigest(),
        "public_building_candidates": expected_sites,
        "source_2022_NRW_counties": len(county_counts),
        "historical_source_fictional_building_TIV_EUR": original_tiv,
        "event_hourly_timesteps": HOURS,
        "maximum_requested_gridpoint_hours_if_all_nodes_returned": requested_nodes * HOURS,
        "time_spatial_original_1990_Daria_does_not_match_Ciara2020": True,
        "2022_public_buildings_are_real_RV_insured_sites": False,
        "original_CDS_source_data_acquired_or_attested": False,
        "CDS_data_licence_accepted_by_operator_verified": False,
        "observed_2020_insurer_claims_or_exposure_denominator_loaded": False,
        "German_wind_vulnerability_or_gross_net_EP_model_admitted": False,
        "request_executed": False,
    }


def plan_from_archived_source(path: Path) -> dict:
    if (path.is_symlink() or not path.is_file()
        or not 0 < path.stat().st_size <= 30_000_000
        or hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_ARTIFACT_SHA256):
        raise CiaraAreaBlocked("exact pinned original-source-derived 10k archive required")
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        if (len(members) != len(SOURCE_ARCHIVE_MEMBERS)
            or {x.filename for x in members} != SOURCE_ARCHIVE_MEMBERS
            or any(x.file_size > 12_000_000 or x.flag_bits & 1 for x in members)
            or sum(x.file_size for x in members) > 30_000_000
            or z.testzip() is not None):
            raise CiaraAreaBlocked("source ZIP members changed, oversized or corrupt")
        contents = {name: z.read(name) for name in SOURCE_ARCHIVE_MEMBERS}
    for name, sha in SOURCE_CSV_SHA256.items():
        if hashlib.sha256(contents[name]).hexdigest() != sha:
            raise CiaraAreaBlocked("original-derived public source CSV SHA mismatch")
    manifest = json.loads(contents["manifest.json"])
    if (manifest.get("schema") != SOURCE_SCHEMA
        or manifest.get("status") != "GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED"
        or manifest.get("source_original_2022_HU_complete_archive_SHA256") != SOURCE_SHA
        or manifest.get("source_original_2022_HU_full_CRCs_verified") is not True
        or manifest.get("output_file_SHA256") != SOURCE_CSV_SHA256
        or manifest.get("physical_building_candidates_selected") != EXPECTED_SITES
        or manifest.get("real_source_counties_represented") != EXPECTED_COUNTIES
        or manifest.get("fictional_policy_count") != EXPECTED_SITES
        or manifest.get("model_input_approved") is not False
        or manifest.get("insurer_building_TIV_observed") is not False
        or manifest.get("physical_building_footprints_are_actual_RV_insured_sites") is not False):
        raise CiaraAreaBlocked("archive source/insurance scientific admission receipt drift")
    with CONTRACT.open("rb") as f:
        validate_contract(tomllib.load(f))
    result = build_area_plan(_read_csv(contents["location.csv"]),
                             _read_csv(contents["account.csv"]),
                             _read_csv(contents["physical_candidate_evidence.csv"]))
    result["historical_original_NRW_HU2022_zip_sha256"] = SOURCE_SHA
    result["source_derived_10k_archive_sha256"] = SOURCE_ARTIFACT_SHA256
    result["source_derived_csv_sha256"] = dict(SOURCE_CSV_SHA256)
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_archived_10k_oed_zip", type=Path)
    p.add_argument("--receipt-json", type=Path)
    args = p.parse_args()
    try:
        result = plan_from_archived_source(args.source_archived_10k_oed_zip)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.receipt_json:
            path = args.receipt_json
            if path.is_symlink() or path.exists() or not path.parent.is_dir():
                raise CiaraAreaBlocked("receipt target must be fresh regular path")
            path.write_text(payload, encoding="utf-8")
        print(payload)
        return 0
    except (OSError, CiaraAreaBlocked, ValueError, KeyError, zipfile.BadZipFile) as exc:
        p.exit(2, "CIARA_2020_10K_ERA5_AREA_NOT_ADMITTED: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
