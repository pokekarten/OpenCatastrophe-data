# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Nine wholly fictional Berlin-grid commercial OED 5.0 smoke locations.

September's TED award describes *nine* commercial objects but contains NO
object addresses, insured TIV, BI, construction, legal coverage or insurer
allocations. This generator borrows ONLY that count as a test size. All
coordinates, EUR amounts, portfolio IDs, perils and account are invented.

Do not use this fixture to infer WBM's actual nine sites or the risk of HDI,
Helvetia or R+V. It is a format/layout smoke test, not a model lookup/GUL/FM,
loss simulation, treaty, geocode or in-force insurance exposure.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

from .export_synthetic_oed_v0 import (
    ACCOUNT_FIELDS, LOCATION_FIELDS, OED_VERSION, SyntheticOedError,
)

PORT = "BERLIN-UNAFFILIATED-FICTIONAL-9-V0"
ACCOUNT = "FAKE-COMMERCIAL-ACC-01"
POLICY = "FAKE-COMMERCIAL-POL-01"
PERILS = "WW2;OO1"
COUNT = 9
TOTAL_FAKE_BUILDING_EUR = 108_000_000
INVENTED_BASE_EUR = 4_000_000
INVENTED_STEP_EUR = 2_000_000
LATITUDES = ("52.420000", "52.490000", "52.560000")
LONGITUDES = ("13.250000", "13.350000", "13.450000")
SCHEMA = "BERLIN_NINE_FICTIONAL_COMMERCIAL_OED_5_0_FORMAT_DEMO_V0"

def prepare() -> tuple[list[dict[str, str]], list[dict[str, str]], dict]:
    locations = []
    for n in range(1, COUNT + 1):
        value = INVENTED_BASE_EUR + INVENTED_STEP_EUR * (n - 1)
        locations.append({
            "PortNumber": PORT,
            "AccNumber": ACCOUNT,
            "LocNumber": f"FICTITIOUS-SITE-{n:02d}",
            "CountryCode": "DE",
            "Latitude": LATITUDES[(n - 1) // 3],
            "Longitude": LONGITUDES[(n - 1) % 3],
            "LocPerilsCovered": PERILS,
            "BuildingTIV": str(value),
            "OtherTIV": "0",
            "ContentsTIV": "0",
            "BITIV": "0",
            "LocCurrency": "EUR",
            "NumberOfBuildings": "1",
            "OEDVersion": OED_VERSION,
        })
    accounts = [{
        "PortNumber": PORT, "AccNumber": ACCOUNT, "AccCurrency": "EUR",
        "PolNumber": POLICY, "PolPerilsCovered": PERILS,
        "OEDVersion": OED_VERSION,
    }]
    manifest = {
        "schema_version": SCHEMA,
        "origin": "self_generated_format_validation_fixture",
        "oed_format_version": OED_VERSION,
        "fictional_portfolio_name": PORT,
        "only_real_world_input_used": "notice_668506_2026_says_nine_commercial_objects",
        "count_nine_based_on_notice_text_not_verified_site_list": True,
        "location_count": COUNT,
        "sum_building_eur_entirely_invented": TOTAL_FAKE_BUILDING_EUR,
        "value_recipe": "EUR 4000000 + (n-1)*EUR 2000000 for n=1..9",
        "latitude_grid_purely_invented_not_actual_asset_locations": True,
        "all_account_policy_names_invented": True,
        "all_site_coordinates_invented": True,
        "all_tiv_values_invented": True,
        "coverage_perils_WW2_OO1_invented": True,
        "insurer_legal_entity_or_carrier_share": None,
        "real_property_ownership_or_location_verified": False,
        "source_estimated_property_replacement_tiv_obtained": False,
        "wBM_group_asset_portfolio_valuation_used_for_tiv": False,
        "real_insurance_policy_coverage_or_2027_inception_confirmed": False,
        "gross_or_net_model_loss_simulated": False,
        "ods_tools_validation_performed_by_this_generator": False,
        "actual_insurer_CAT_exposure_admitted": False,
    }
    validate(locations, accounts, manifest)
    return locations, accounts, manifest


def validate(locations: object, accounts: object, manifest: object) -> None:
    """Fail closed if a fake fixture becomes plausible real insurer evidence."""
    if not isinstance(locations, list) or len(locations) != COUNT:
        raise SyntheticOedError("expected exact nine fictional rows")
    if not isinstance(accounts, list) or len(accounts) != 1:
        raise SyntheticOedError("expected exactly one fictional account")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA:
        raise SyntheticOedError("invalid fictional provenance")
    for field in (
        "count_nine_based_on_notice_text_not_verified_site_list",
        "latitude_grid_purely_invented_not_actual_asset_locations",
        "all_account_policy_names_invented", "all_site_coordinates_invented",
        "all_tiv_values_invented", "coverage_perils_WW2_OO1_invented",
    ):
        if manifest.get(field) is not True:
            raise SyntheticOedError("fictionality marker not preserved: " + field)
    if manifest.get("insurer_legal_entity_or_carrier_share") is not None:
        raise SyntheticOedError("company identity or coverage share not allowed")
    for field in (
        "real_property_ownership_or_location_verified",
        "source_estimated_property_replacement_tiv_obtained",
        "wBM_group_asset_portfolio_valuation_used_for_tiv",
        "real_insurance_policy_coverage_or_2027_inception_confirmed",
        "gross_or_net_model_loss_simulated",
        "ods_tools_validation_performed_by_this_generator",
        "actual_insurer_CAT_exposure_admitted",
    ):
        if manifest.get(field) is not False:
            raise SyntheticOedError("prohibited provenance promotion: " + field)
    expected_manifest = {
        "location_count": COUNT,
        "sum_building_eur_entirely_invented": TOTAL_FAKE_BUILDING_EUR,
        "only_real_world_input_used": "notice_668506_2026_says_nine_commercial_objects",
    }
    if any(manifest.get(key) != value for key, value in expected_manifest.items()):
        raise SyntheticOedError("fixture bound or count changed")
    if accounts[0] != {
        "PortNumber": PORT, "AccNumber": ACCOUNT, "AccCurrency": "EUR",
        "PolNumber": POLICY, "PolPerilsCovered": PERILS,
        "OEDVersion": OED_VERSION,
    }:
        raise SyntheticOedError("real or edited account/policy terms not allowed")

    total = Decimal(0)
    for n, row in enumerate(locations, 1):
        expected = {
            "PortNumber": PORT, "AccNumber": ACCOUNT,
            "LocNumber": f"FICTITIOUS-SITE-{n:02d}",
            "CountryCode": "DE",
            "Latitude": LATITUDES[(n - 1) // 3],
            "Longitude": LONGITUDES[(n - 1) % 3],
            "LocPerilsCovered": PERILS,
            "BuildingTIV": str(INVENTED_BASE_EUR + INVENTED_STEP_EUR * (n-1)),
            "OtherTIV": "0", "ContentsTIV": "0", "BITIV": "0",
            "LocCurrency": "EUR", "NumberOfBuildings": "1",
            "OEDVersion": OED_VERSION,
        }
        if row != expected:
            raise SyntheticOedError(f"fictional location {n} modified")
        total += Decimal(row["BuildingTIV"])
    if total != TOTAL_FAKE_BUILDING_EUR:
        raise SyntheticOedError("invented total not conserved")


def export(outdir: Path) -> tuple[Path, Path, Path]:
    locations, accounts, manifest = prepare()
    # Input is not accepted, so there is no chance to launder external or
    # private records as an officially approved synthetic scenario.
    if outdir.exists() or not outdir.parent.is_dir():
        raise SyntheticOedError("output directory must be new with existing parent")
    outdir.mkdir(mode=0o700)
    try:
        files = []
        for name, fields, rows in (
            ("location.csv", LOCATION_FIELDS, locations),
            ("account.csv", ACCOUNT_FIELDS, accounts),
        ):
            path = outdir / name
            with path.open("x", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            files.append(path)
        manifest_path = outdir / "fictional-provenance.json"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        files.append(manifest_path)
    except BaseException:
        for path in outdir.iterdir():
            path.unlink()
        outdir.rmdir()
        raise
    return files[0], files[1], files[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path,
                        help="fresh directory for 2 OED CSVs and source manifest")
    args = parser.parse_args()
    try:
        location, account, provenance = export(args.output_directory)
    except (OSError, ValueError) as exc:
        print("NINE_FICTIONAL_OED_EXPORT_BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print("FICTIONAL ONLY, NO ACTUAL WBM/R+V CAT EXPOSURE: "
          + f"{location} | {account} | {provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
