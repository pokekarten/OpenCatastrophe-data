# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One original XWS Daria 1990 wind event -> INVENTED direct-value impact sensitivities.

No licensed original CSVs are copied here. Accepts only the previously vetted
source-derived 10k NRW site-gust ZIP with independent hashes and explicit
non-insurer semantics. Original 1990 hazard and invented 2025-like values do
NOT yield actual carrier losses, native Oasis output or annual OEP/AEP.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

SOURCE_HASHES = {
    "grid": "decb09d473db9086df7a497bcebc95641238d4ee365ff26d8e83c266a6f32599",
    "daria_lower95": "4381de5fdb5e66489efde09ac587e295b93906cac643325ad5517a278d5e2bff",
    "daria_mean": "34b9c02768aa6f54aa541e185381e4735f3b2cd852fc23a724ddc00c301a1d50",
    "daria_upper95": "8b63a95adf0961da00c1e8874fbb99a49cd38b58de6263f8c4f1c65637cc6007",
}
HAZARD_STATUS = "REAL_XWS_HISTORICAL_WIND_HAZARD_ON_PUBLIC_GEOSITES_WITH_FICTIONAL_INSURANCE_ONLY"
HAZARD_SCHEMA = "RVA_NRW_2022_HU10K_XWS_DARIA1990_ORIGINAL_3S_GUST_HAZARD_ONLY_V0"
OUTPUT_SCHEMA = "RVA_NRW_XWS_DARIA_INVENTED_EVENT_CONDITIONAL_DIRECT_IMPACT_V0"
SITE_NAME = "daria_1990_original_source_site_gust_only.csv"
COUNTY_NAME = "daria_1990_NRW_53kreis_event_gust_summary.csv"
MANIFEST_NAME = "source_and_no_CAT_loss_manifest.json"
SITE_COLUMNS = (
    "FictionalSiteId", "Original2022KreisAGS", "XWS1990DariaNearestSourceGridId",
    "NearestXWSGridPointKm", "Daria1990Lower95GustMps",
    "Daria1990MeanGustMps", "Daria1990Upper95GustMps",
    "Fictional2025BuildingTIVEUR", "ActualRVInsuredSiteObserved",
)
COUNTY_COLUMNS = (
    "KreisAGS2022", "FictionalSiteCount", "FictionalBuildingTIVEUR",
    "TIVWeightedDaria1990MeanGustMps", "FictionalBuildingsWithMeanGustGE25Mps",
    "FictionalTIVWithMeanGustGE25MpsEUR",
)
VARIANTS = {
    "lower95": "Daria1990Lower95GustMps",
    "mean": "Daria1990MeanGustMps",
    "upper95": "Daria1990Upper95GustMps",
}
# Purely invented illustrative direct-damage fractions; NOT a copied or
# calibrated German construction/roof vulnerability curve. Never auto-admit.
KNOT_SPEED = (0, 20, 30, 40, 55, 75, 100, 150, 200, 300)
CURVES = {
    "illustrative_resilient": ("0", "0", ".002", ".01", ".04", ".10", ".20", ".40", ".60", ".60"),
    "illustrative_fragile": ("0", "0", ".02", ".10", ".30", ".65", ".90", "1", "1", "1"),
}
CASE_FIELDS = (
    "PhysicalStorm", "XWSUncertaintyViewSameEvent", "InventedDamageCurve",
    "FictionalSiteId", "KreisAGS2022", "Source3SecondGustMps",
    "InventedBuildingTIVEUR", "InventedDirectValueImpactEURCents",
    "ActualInsurerLossObserved",
)
COUNTY_FIELDS = (
    "PhysicalStorm", "XWSUncertaintyViewSameEvent", "InventedDamageCurve",
    "KreisAGS2022", "FictionalSiteCount", "InventedBuildingTIVEUR",
    "InventedDirectValueImpactEURCents",
)


class InventedDamageBlocked(ValueError):
    """An input is not an exact, self-consistent hazard-only source fixture."""


def _decimal(value: str, maximum: int) -> Decimal:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise InventedDamageBlocked("missing or noncanonical numeric input")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise InventedDamageBlocked("invalid numeric input") from exc
    if not number.is_finite() or number < 0 or number > maximum:
        raise InventedDamageBlocked("invalid nonfinite or out-of-range value")
    return number


def _csv(blob: bytes, fields: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(blob.decode("utf-8"), newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != fields:
            raise InventedDamageBlocked("exact upstream CSV schema changed")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise InventedDamageBlocked("invalid upstream UTF-8 CSV") from exc
    if not rows or len(rows) > 10_000 or any(
        None in row or any(value is None or value == "" for value in row.values())
        for row in rows
    ):
        raise InventedDamageBlocked("incomplete or malformed source rows")
    return rows


def _ratio(gust: Decimal, curve: str) -> Decimal:
    if gust > 300:
        raise InventedDamageBlocked("invented curve has no support above 300 m/s")
    knots = tuple(Decimal(s) for s in CURVES[curve])
    for i in range(1, len(KNOT_SPEED)):
        right = Decimal(KNOT_SPEED[i])
        if gust <= right:
            left = Decimal(KNOT_SPEED[i - 1])
            return knots[i - 1] + (
                (gust - left) * (knots[i] - knots[i - 1]) / (right - left)
            )
    return knots[-1]


def _rows_csv(rows: list[dict], fields: tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _unique_json_object(pairs):
    """Reject ambiguous duplicated source receipt keys before validating hashes."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise InventedDamageBlocked("duplicate original source receipt JSON key: " + key)
        result[key] = value
    return result


def calculate(
    hazard_zip: Path, *,
    expected_sites: int = 10_000,
    expected_counties: int = 53,
    expected_tiv_eur: int = 4_826_029_500,
    source_hashes: dict[str, str] | None = None,
) -> dict:
    """Original source restriction is constant for CLI; overrides only for tests."""
    original_hashes = SOURCE_HASHES if source_hashes is None else source_hashes
    if (
        hazard_zip.is_symlink() or not hazard_zip.is_file()
        or not 1 <= hazard_zip.stat().st_size <= 20_000_000
    ):
        raise InventedDamageBlocked("bounded real hazard-derived ZIP is required")
    data = hazard_zip.read_bytes()
    input_sha = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.infolist()
        if (
            len(info) != 3
            or {f.filename for f in info} != {SITE_NAME, COUNTY_NAME, MANIFEST_NAME}
            or any(f.is_dir() or f.file_size > 10_000_000 for f in info)
            or archive.testzip() is not None
        ):
            raise InventedDamageBlocked("unexpected or corrupted original hazard ZIP")
        files = {name: archive.read(name) for name in (SITE_NAME, COUNTY_NAME, MANIFEST_NAME)}
    try:
        manifest = json.loads(files[MANIFEST_NAME], object_pairs_hook=_unique_json_object)
    except (ValueError, UnicodeError) as exc:
        raise InventedDamageBlocked("source receipt JSON invalid") from exc
    if not isinstance(manifest, dict):
        raise InventedDamageBlocked("source receipt JSON root must be an object")
    if (
        manifest.get("schema") != HAZARD_SCHEMA
        or manifest.get("status") != HAZARD_STATUS
        or manifest.get("real_original_XWS_historical_storm") != "Daria 1990"
        or manifest.get("storm_uncertainty_variants_are_same_physical_event") is not True
        or manifest.get("source_weather_maximum_3sec_gust_at_10m_mps") is not True
        or manifest.get("site_wind_gust_not_insured_damage_or_loss") is not True
        or manifest.get("actual_1990_RV_insured_geographies_or_2025_RV_coverage_known") is not False
        or manifest.get("German_wind_vulnerability_by_material_roof_construction_validated") is not False
        or manifest.get("XWS_extreme_storm_selection_is_valid_annual_frequency_model") is not False
        or manifest.get("native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed") is not False
        or manifest.get("source_physical_building_site_count") != expected_sites
        or manifest.get("source_2022_NRW_Kreise_count") != expected_counties
        or manifest.get("fictional_building_TIV_eur") != expected_tiv_eur
    ):
        raise InventedDamageBlocked("source is not accepted hazard-only fictional scope")
    got_files = manifest.get("output_sha256", {})
    if not isinstance(got_files, dict) or set(got_files) != {SITE_NAME, COUNTY_NAME}:
        raise InventedDamageBlocked("original derived file SHA receipt is absent")
    for name in (SITE_NAME, COUNTY_NAME):
        if hashlib.sha256(files[name]).hexdigest() != got_files[name]:
            raise InventedDamageBlocked("original hazard-derived CSV content SHA mismatch")
    source = manifest.get("provider_original_four_XWS_CSV_source_receipt")
    source_files = source.get("original_files") if isinstance(source, dict) else None
    if (
        not isinstance(source_files, dict)
        or source.get("status") != "OFFICIAL_ORIGINAL_XWS_CSV_BYTES_PARSED_NOT_MODEL_ADMITTED"
        or set(source_files) != set(original_hashes)
        or any(not isinstance(source_files[k], dict) or
               source_files[k].get("full_sha256") != sha
               for k, sha in original_hashes.items())
    ):
        raise InventedDamageBlocked("original provider CSV SHA identity mismatch")

    sites = _csv(files[SITE_NAME], SITE_COLUMNS)
    counties = _csv(files[COUNTY_NAME], COUNTY_COLUMNS)
    if len(sites) != expected_sites or len(counties) != expected_counties:
        raise InventedDamageBlocked("hazard source population not conserved")
    site_ids: set[str] = set()
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    impacts: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0, 0])
    per_site = []
    t_sum = 0
    for site in sites:
        sid, county = site["FictionalSiteId"], site["Original2022KreisAGS"]
        if (
            not sid or sid in site_ids or len(county) != 5 or not county.isdigit()
            or site["ActualRVInsuredSiteObserved"] != "false"
            or not site["XWS1990DariaNearestSourceGridId"].isdigit()
            or _decimal(site["NearestXWSGridPointKm"], 45) > 45
        ):
            raise InventedDamageBlocked("false insurer geography or duplicate physical site")
        site_ids.add(sid)
        tiv_str = site["Fictional2025BuildingTIVEUR"]
        if not tiv_str.isdigit() or str(int(tiv_str)) != tiv_str or not 1 <= int(tiv_str) <= 500_000_000:
            raise InventedDamageBlocked("invalid fictional building TIV")
        tiv = int(tiv_str)
        gust = {v: _decimal(site[field], 300) for v, field in VARIANTS.items()}
        if not gust["lower95"] <= gust["mean"] <= gust["upper95"]:
            raise InventedDamageBlocked("same-event uncertainty variants reversed")
        c = totals[county]
        c[0] += 1
        c[1] += tiv
        if gust["mean"] >= 25:
            c[2] += 1
            c[3] += tiv
        t_sum += tiv
        for curve in CURVES:
            for view in VARIANTS:
                cents = int((Decimal(tiv) * 100 * _ratio(gust[view], curve)).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                ))
                if not 0 <= cents <= tiv * 100:
                    raise InventedDamageBlocked("invented direct impact violates economic bound")
                counts = impacts[(curve, view, county)]
                counts[0] += 1
                counts[1] += tiv
                counts[2] += cents
                per_site.append({
                    "PhysicalStorm": "XWS_DARIA_1990",
                    "XWSUncertaintyViewSameEvent": view,
                    "InventedDamageCurve": curve,
                    "FictionalSiteId": sid, "KreisAGS2022": county,
                    "Source3SecondGustMps": str(gust[view]),
                    "InventedBuildingTIVEUR": tiv,
                    "InventedDirectValueImpactEURCents": cents,
                    "ActualInsurerLossObserved": "false",
                })
    if t_sum != expected_tiv_eur or len(totals) != expected_counties:
        raise InventedDamageBlocked("source building TIV or county count mismatch")
    county_index = {}
    for r in counties:
        key = r["KreisAGS2022"]
        if key in county_index:
            raise InventedDamageBlocked("duplicate original county summary")
        county_index[key] = r
    if set(county_index) != set(totals):
        raise InventedDamageBlocked("source county roster changed")
    for county, (count, tiv, ge25, ge25tiv) in totals.items():
        r = county_index[county]
        if (
            (r["FictionalSiteCount"], r["FictionalBuildingTIVEUR"],
             r["FictionalBuildingsWithMeanGustGE25Mps"],
             r["FictionalTIVWithMeanGustGE25MpsEUR"])
            != tuple(str(v) for v in (count, tiv, ge25, ge25tiv))
        ):
            raise InventedDamageBlocked("county and source-site exposure inconsistent")
    by_county = []
    matrix = []
    for curve in CURVES:
        for view in VARIANTS:
            impact_total = 0
            for county in sorted(totals):
                count, tiv, cents = impacts[(curve, view, county)]
                impact_total += cents
                by_county.append({
                    "PhysicalStorm": "XWS_DARIA_1990",
                    "XWSUncertaintyViewSameEvent": view,
                    "InventedDamageCurve": curve,
                    "KreisAGS2022": county, "FictionalSiteCount": count,
                    "InventedBuildingTIVEUR": tiv,
                    "InventedDirectValueImpactEURCents": cents,
                })
            matrix.append({
                "same_physical_event": "XWS_DARIA_1990",
                "original_hazard_uncertainty_view": view,
                "invented_damage_curve": curve,
                "fictional_site_count": len(sites),
                "invented_total_tiv_eur": t_sum,
                "invented_direct_value_impact_eur_cents": impact_total,
            })
    for curve in CURVES:
        ms = {r["original_hazard_uncertainty_view"]: r["invented_direct_value_impact_eur_cents"]
              for r in matrix if r["invented_damage_curve"] == curve}
        if not ms["lower95"] <= ms["mean"] <= ms["upper95"]:
            raise InventedDamageBlocked("conditional damage must preserve same-storm hazard ordering")
    result = {
        "schema": OUTPUT_SCHEMA,
        "status": "ILLUSTRATIVE_EVENT_CONDITIONAL_DIRECT_VALUE_ONLY_NOT_INSURANCE_CAT",
        "input_hazard_derived_zip_sha256": input_sha,
        "input_site_csv_sha256": got_files[SITE_NAME],
        "source_original_csv_sha256": original_hashes,
        "historical_source_vintage": "Daria 1990",
        "building_geometry_vintage": "2022",
        "fictional_insurer_values_vintage": "2025-like",
        "fictional_counties": expected_counties,
        "fictional_sites": expected_sites,
        "fictional_tiv_eur": t_sum,
        "scenario_count": len(matrix),
        "one_physical_event_only": True,
        "invented_curve_points_mps": list(KNOT_SPEED),
        "invented_curve_damage_ratios": {k: list(v) for k, v in CURVES.items()},
        "original_gust_variants_are_same_event_not_annual_samples": True,
        "no_geocoded_insured_RV_sites": True,
        "no_scientifically_calibrated_German_vulnerability": True,
        "no_actual_insured_GUL_IL_RI_loss": True,
        "no_annual_event_frequency_or_OEP_AEP": True,
    }
    return {"site_rows": per_site, "county_rows": by_county, "scenario_matrix": matrix,
            "receipt": result}


def write_output(path: Path, result: dict) -> dict:
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise InventedDamageBlocked("new output ZIP path is required")
    components = {
        "invented_event_conditional_site_direct_value.csv":
            _rows_csv(result["site_rows"], CASE_FIELDS),
        "invented_event_conditional_county_direct_value.csv":
            _rows_csv(result["county_rows"], COUNTY_FIELDS),
        "invented_event_conditional_six_scenarios.json":
            (json.dumps(result["scenario_matrix"], sort_keys=True, indent=2) + "\n").encode(),
    }
    receipt = dict(result["receipt"])
    receipt["output_sha256"] = {k: hashlib.sha256(v).hexdigest()
                                for k, v in components.items()}
    components["invented_not_insurer_loss_receipt.json"] = (
        json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    try:
        with zipfile.ZipFile(path, "x") as archive:
            for name, content in components.items():
                meta = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                meta.compress_type = zipfile.ZIP_DEFLATED
                meta.external_attr = 0o644 << 16
                archive.writestr(meta, content)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-hazard-zip", type=Path, required=True)
    p.add_argument("--out-fictional-direct-impact-zip", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        result = calculate(a.source_hazard_zip)
        receipt = write_output(a.out_fictional_direct_impact_zip, result)
        print(json.dumps({"status": receipt["status"], "fictional_sites": receipt["fictional_sites"],
                          "scenario_totals_eur_cents": result["scenario_matrix"],
                          "annual_ep_or_insurer_loss": False}, sort_keys=True))
        return 0
    except (InventedDamageBlocked, OSError, ValueError, zipfile.BadZipFile) as exc:
        print("XWS_DARIA_INVENTED_DIRECT_IMPACT_BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
