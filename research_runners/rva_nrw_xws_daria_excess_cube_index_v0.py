# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""XWS Daria 1990: source-bound *severity index*, NOT financial loss.

Separate an independently documented fixed 25 m/s excess-cubed wind
severity method from the research-only invented wind-to-loss responses.
This asset-sampled NRW index must NOT be mistaken for the catalogue's
grid-point SSI, a locally calibrated 98th percentile, insurer loss or EP.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from rva_nrw_xws_daria_10k_original_gust_overlay_v0 import (
    original_source_files, overlay, PINNED_SOURCE_FILES, SITE_FIELDS, COUNTY_FIELDS,
    SCHEMA as SOURCE_SCHEMA,
)

SOURCE_STATUS = (
    "REAL_XWS_HISTORICAL_WIND_HAZARD_ON_PUBLIC_GEOSITES_WITH_FICTIONAL_INSURANCE_ONLY"
)
SCHEMA = "XWS_DARIA_1990_ASSET_SAMPLED_EXCESS_CUBED_INTENSITY_INDEX_V0"
THRESHOLD_MPS = Decimal("25")
VIEWS = (
    ("lower95", "Daria1990Lower95GustMps"),
    ("mean", "Daria1990MeanGustMps"),
    ("upper95", "Daria1990Upper95GustMps"),
)
OUTPUT_FIELDS = (
    "PhysicalEvent", "SameEventWindView", "KreisAGS2022",
    "PublicCandidateBuildingCount", "FictionalBuildingTIVEUR",
    "CountSitesWindAbove25Mps", "AssetSampledExcessCubeMps3",
    "FictionalTIVWeightedExcessCubeEUR_Mps3",
)


class WindIndexBlocked(ValueError):
    """Fail closed instead of promoting a synthetic output into real losses."""


def _number(value: str, *, maximum: Decimal) -> Decimal:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise WindIndexBlocked("source numeric text not canonical")
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise WindIndexBlocked("source numeric text invalid") from exc
    if not d.is_finite() or not Decimal(0) <= d <= maximum:
        raise WindIndexBlocked("nonfinite or out-of-range source numeric")
    return d


def _format(value: Decimal) -> str:
    return format(value, "f")


def _csv(rows: list[dict], fields: tuple[str, ...]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def compute_index(
    study: dict, *,
    expected_sites: int = 10_000,
    expected_counties: int = 53,
    expected_tiv: int = 4_826_029_500,
) -> dict:
    """Consume only original-source-validated site overlay; never infer money losses."""
    if not isinstance(study, dict) or set(study) != {"site_rows", "county_rows", "receipt"}:
        raise WindIndexBlocked("original overlay structure is required")
    receipt = study["receipt"]
    source = receipt.get("provider_original_four_XWS_CSV_source_receipt", {})
    full_files = source.get("original_files", {}) if isinstance(source, dict) else {}
    if (
        receipt.get("schema") != SOURCE_SCHEMA
        or receipt.get("status") != SOURCE_STATUS
        or receipt.get("real_original_XWS_historical_storm") != "Daria 1990"
        or receipt.get("storm_uncertainty_variants_are_same_physical_event") is not True
        or receipt.get("site_wind_gust_not_insured_damage_or_loss") is not True
        or receipt.get("actual_1990_RV_insured_geographies_or_2025_RV_coverage_known") is not False
        or receipt.get("German_wind_vulnerability_by_material_roof_construction_validated") is not False
        or receipt.get("XWS_extreme_storm_selection_is_valid_annual_frequency_model") is not False
        or receipt.get("native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed") is not False
        or receipt.get("source_physical_building_site_count") != expected_sites
        or receipt.get("source_2022_NRW_Kreise_count") != expected_counties
        or receipt.get("fictional_building_TIV_eur") != expected_tiv
        or source.get("status") != "OFFICIAL_ORIGINAL_XWS_CSV_BYTES_PARSED_NOT_MODEL_ADMITTED"
        or set(full_files) != set(PINNED_SOURCE_FILES)
        or any(
            full_files[name].get("full_sha256") != sha
            or full_files[name].get("full_bytes") != size
            for name, (size, sha) in PINNED_SOURCE_FILES.items()
        )
    ):
        raise WindIndexBlocked("unverified original source or false model-admission claim")

    sites, counties = study["site_rows"], study["county_rows"]
    if not isinstance(sites, list) or not isinstance(counties, list):
        raise WindIndexBlocked("source overlay rows are not lists")
    if len(sites) != expected_sites or len(counties) != expected_counties:
        raise WindIndexBlocked("incomplete physical source population")

    unique: set[str] = set()
    county_exposure: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    county_index: dict[tuple[str, str], list] = defaultdict(
        lambda: [0, Decimal(0), 0, Decimal(0)]
    )
    totals: dict[str, list] = {
        view: [0, Decimal(0), 0, Decimal(0)] for view, _ in VIEWS
    }
    for row in sites:
        if not isinstance(row, dict) or set(row) != set(SITE_FIELDS):
            raise WindIndexBlocked("original site schema changed")
        ident, county = row["FictionalSiteId"], row["Original2022KreisAGS"]
        if (
            not isinstance(ident, str) or not ident or ident in unique
            or not isinstance(county, str) or len(county) != 5 or not county.isdigit()
            or row["ActualRVInsuredSiteObserved"] != "false"
            or not row["XWS1990DariaNearestSourceGridId"].isdigit()
            or _number(row["NearestXWSGridPointKm"], maximum=Decimal(45)) > 45
        ):
            raise WindIndexBlocked("duplicate/nonphysical or claimed insured site")
        unique.add(ident)
        tiv_text = row["Fictional2025BuildingTIVEUR"]
        if (
            not isinstance(tiv_text, str) or not tiv_text.isdigit()
            or str(int(tiv_text)) != tiv_text
            or not 1 <= int(tiv_text) <= 500_000_000
        ):
            raise WindIndexBlocked("invented TIV source not conserved")
        tiv = int(tiv_text)
        gusts = [_number(row[field], maximum=Decimal(300)) for _, field in VIEWS]
        if not gusts[0] <= gusts[1] <= gusts[2]:
            raise WindIndexBlocked("reversed same-event original XWS wind uncertainty views")
        ce = county_exposure[county]
        ce[0] += 1
        ce[1] += tiv
        if gusts[1] >= THRESHOLD_MPS:
            ce[2] += 1
            ce[3] += tiv
        for (view, _), gust in zip(VIEWS, gusts):
            excess = max(Decimal(0), gust - THRESHOLD_MPS)
            cube = excess * excess * excess
            positive = int(excess > 0)
            row_group = county_index[(county, view)]
            row_group[0] += 1
            row_group[1] += cube
            row_group[2] += positive
            row_group[3] += cube * tiv
            total = totals[view]
            total[0] += 1
            total[1] += cube
            total[2] += positive
            total[3] += cube * tiv

    observed = {}
    for row in counties:
        if not isinstance(row, dict) or set(row) != set(COUNTY_FIELDS):
            raise WindIndexBlocked("original county schema changed")
        county = row["KreisAGS2022"]
        if county in observed:
            raise WindIndexBlocked("duplicate source county")
        observed[county] = row
    if set(observed) != set(county_exposure):
        raise WindIndexBlocked("original county population differs from site roster")
    if sum(x[1] for x in county_exposure.values()) != expected_tiv:
        raise WindIndexBlocked("national fictional TIV not conserved")
    for county, values in county_exposure.items():
        source_row = observed[county]
        actual_text = (
            source_row["FictionalSiteCount"],
            source_row["FictionalBuildingTIVEUR"],
            source_row["FictionalBuildingsWithMeanGustGE25Mps"],
            source_row["FictionalTIVWithMeanGustGE25MpsEUR"],
        )
        if actual_text != tuple(str(v) for v in values):
            raise WindIndexBlocked("original county/site exposure not reconciled")

    result_rows = []
    for view, _ in VIEWS:
        for county in sorted(county_exposure):
            count, cube, positive, weighted_cube = county_index[(county, view)]
            value = county_exposure[county][1]
            result_rows.append({
                "PhysicalEvent": "XWS_DARIA_1990",
                "SameEventWindView": view,
                "KreisAGS2022": county,
                "PublicCandidateBuildingCount": count,
                "FictionalBuildingTIVEUR": value,
                "CountSitesWindAbove25Mps": positive,
                "AssetSampledExcessCubeMps3": _format(cube),
                "FictionalTIVWeightedExcessCubeEUR_Mps3": _format(weighted_cube),
            })
    summary = []
    for view, _ in VIEWS:
        count, cube, positives, weighted = totals[view]
        if (
            count != expected_sites
            or sum(r["CountSitesWindAbove25Mps"] for r in result_rows
                   if r["SameEventWindView"] == view) != positives
            or sum(Decimal(r["AssetSampledExcessCubeMps3"]) for r in result_rows
                   if r["SameEventWindView"] == view) != cube
            or sum(Decimal(r["FictionalTIVWeightedExcessCubeEUR_Mps3"]) for r in result_rows
                   if r["SameEventWindView"] == view) != weighted
        ):
            raise WindIndexBlocked("asset sampled index fails county/national reconciliation")
        summary.append({
            "physical_event": "XWS_DARIA_1990",
            "original_wind_view_same_event": view,
            "candidate_sites": count,
            "candidate_sites_above_25_mps": positives,
            "asset_sampled_excess_cubed_mps3": _format(cube),
            "fictional_TIV_weighted_excess_cubed_EUR_mps3": _format(weighted),
        })
    for key in ("asset_sampled_excess_cubed_mps3",
                "fictional_TIV_weighted_excess_cubed_EUR_mps3"):
        ordered = [Decimal(s[key]) for s in summary]
        if ordered != sorted(ordered):
            raise WindIndexBlocked("same-event wind severity ordering broken")

    proof = {
        "schema": SCHEMA,
        "status": "SOURCE_AUTHENTICATED_ONE_EVENT_ASSET_SAMPLED_SEVERITY_INDEX_NOT_LOSS",
        "method_reference": "https://www.europeanwindstorms.org/method/select/",
        "fixed_wind_excess_threshold_mps": str(THRESHOLD_MPS),
        "unit_excess_cube": "m^3/s^3 (m/s cubed)",
        "unit_TIV_weighted_excess_cube": "fictional EUR * (m/s)^3",
        "original_grid_SSI_not_reproduced": True,
        "local_98th_percentile_not_estimated": True,
        "frequency_or_annual_probability_not_estimated": True,
        "no_real_RV_insured_sites_or_money_losses": True,
        "no_GUL_IL_RI_OEP_AEP": True,
        "same_physical_storm_uncertainty_views_not_independent_events": True,
        "input_original_source_file_sha256": {
            name: source["original_files"][name]["full_sha256"]
            for name in sorted(PINNED_SOURCE_FILES)
        },
        "input_original_2022_HU_archive_sha256":
            receipt["original_NRW_HU22_full_archived_SHA256"],
        "input_repacked_original_source_OED_zip_sha256":
            receipt["original_NRW_source_derived_OED_artifact_SHA256"],
        "fictional_site_count": expected_sites,
        "fictional_county_count": expected_counties,
        "fictional_building_TIV_eur": expected_tiv,
        "threshold_index_views": summary,
    }
    return {"county_rows": result_rows, "receipt": proof}


def write_zip(path: Path, result: dict) -> dict:
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise WindIndexBlocked("refuse to overwrite existing output")
    data = _csv(result["county_rows"], OUTPUT_FIELDS)
    receipt = dict(result["receipt"])
    receipt["output_sha256"] = {
        "one_storm_asset_sampled_excess_cubed_counties.csv":
            hashlib.sha256(data).hexdigest()
    }
    contents = {
        "one_storm_asset_sampled_excess_cubed_counties.csv": data,
        "one_storm_severity_index_not_insurer_loss_receipt.json":
            (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    }
    try:
        with zipfile.ZipFile(path, "x") as zipout:
            for filename, contents_bytes in contents.items():
                entry = zipfile.ZipInfo(filename, (1980, 1, 1, 0, 0, 0))
                entry.external_attr = 0o644 << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                zipout.writestr(entry, contents_bytes)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-xws-csv-dir", type=Path, required=True)
    p.add_argument("--original-geocoded-nrw-oed-zip", type=Path, required=True)
    p.add_argument("--out-severity-index-zip", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        source = original_source_files(a.original_xws_csv_dir)
        study = overlay(source, a.original_geocoded_nrw_oed_zip)
        result = compute_index(study)
        proof = write_zip(a.out_severity_index_zip, result)
        print(json.dumps({
            "status": proof["status"],
            "one_original_storm": "Daria 1990",
            "fictional_sites": proof["fictional_site_count"],
            "fixed_threshold_mps": proof["fixed_wind_excess_threshold_mps"],
            "same_event_index_views": proof["threshold_index_views"],
            "insured_losses_or_annual_EP": False,
        }, sort_keys=True))
        return 0
    except (WindIndexBlocked, OSError, ValueError, KeyError, TypeError,
            zipfile.BadZipFile) as exc:
        print("DARIA_SOURCE_BOUND_SEVERITY_INDEX_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
