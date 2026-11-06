# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely fictional Daria site-gust to invented direct-impact negative tests."""
from __future__ import annotations

import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import rva_nrw_xws_daria_invented_damage_v0 as model

SYNTHETIC_PINS = {
    "grid": "a" * 64,
    "daria_lower95": "b" * 64,
    "daria_mean": "c" * 64,
    "daria_upper95": "d" * 64,
}


def _csv(records: list[dict], fields: tuple[str, ...]) -> bytes:
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return text.getvalue().encode()


def fake_hazard(
    destination: Path, *, mutate_manifest=None, mutate_sites=None,
    mutate_counties=None, preserve_bad_site_hash=False, extra=False
) -> None:
    originals = [
        ("SYN-05362-1", "05362", 100_000, "10", "15", "20"),
        ("SYN-05974-1", "05974", 200_000, "20", "25", "30"),
        ("SYN-05774-1", "05774", 300_000, "30", "35", "40"),
    ]
    sites = []
    counties = []
    for i, (sid, county, tiv, lo, mid, hi) in enumerate(originals):
        sites.append(dict(zip(model.SITE_COLUMNS, (
            sid, county, str(i), "0.011", lo, mid, hi, str(tiv), "false"
        ))))
        counties.append(dict(zip(model.COUNTY_COLUMNS, (
            county, "1", str(tiv), mid, "1" if Decimal(mid) >= 25 else "0",
            str(tiv) if Decimal(mid) >= 25 else "0"
        ))))
    if mutate_sites is not None:
        mutate_sites(sites)
    if mutate_counties is not None:
        mutate_counties(counties)
    original_site = _csv([dict(zip(model.SITE_COLUMNS, (
        sid, county, str(i), "0.011", lo, mid, hi, str(tiv), "false"
    ))) for i, (sid, county, tiv, lo, mid, hi) in enumerate(originals)], model.SITE_COLUMNS)
    site = _csv(sites, model.SITE_COLUMNS)
    county = _csv(counties, model.COUNTY_COLUMNS)
    manifest = {
        "schema": model.HAZARD_SCHEMA,
        "status": model.HAZARD_STATUS,
        "real_original_XWS_historical_storm": "Daria 1990",
        "storm_uncertainty_variants_are_same_physical_event": True,
        "source_weather_maximum_3sec_gust_at_10m_mps": True,
        "site_wind_gust_not_insured_damage_or_loss": True,
        "actual_1990_RV_insured_geographies_or_2025_RV_coverage_known": False,
        "German_wind_vulnerability_by_material_roof_construction_validated": False,
        "XWS_extreme_storm_selection_is_valid_annual_frequency_model": False,
        "native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed": False,
        "source_physical_building_site_count": 3,
        "source_2022_NRW_Kreise_count": 3,
        "fictional_building_TIV_eur": 600000,
        "provider_original_four_XWS_CSV_source_receipt": {
            "status": "OFFICIAL_ORIGINAL_XWS_CSV_BYTES_PARSED_NOT_MODEL_ADMITTED",
            "original_files": {key: {"full_sha256": sha} for key, sha in SYNTHETIC_PINS.items()},
        },
        "output_sha256": {
            model.SITE_NAME: hashlib.sha256(
                original_site if preserve_bad_site_hash else site
            ).hexdigest(),
            model.COUNTY_NAME: hashlib.sha256(county).hexdigest(),
        },
    }
    if mutate_manifest is not None:
        mutate_manifest(manifest)
    with zipfile.ZipFile(destination, "w") as archive:
        archive.writestr(model.SITE_NAME, site)
        archive.writestr(model.COUNTY_NAME, county)
        archive.writestr(model.MANIFEST_NAME, json.dumps(manifest))
        if extra:
            archive.writestr("unexpected.csv", "secret data prohibited")


def calculate(path: Path):
    return model.calculate(
        path, expected_sites=3, expected_counties=3,
        expected_tiv_eur=600000, source_hashes=SYNTHETIC_PINS
    )


class TestInventedDariaDirectImpact(unittest.TestCase):
    def test_exact_manually_calculated_same_storm_six_scenarios(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "source.zip"
            fake_hazard(p)
            result = calculate(p)
            self.assertEqual(len(result["site_rows"]), 3 * 2 * 3)
            self.assertEqual(len(result["county_rows"]), 3 * 2 * 3)
            self.assertEqual(len(result["scenario_matrix"]), 6)
            values = {
                (r["invented_damage_curve"], r["original_hazard_uncertainty_view"]):
                r["invented_direct_value_impact_eur_cents"]
                for r in result["scenario_matrix"]
            }
            self.assertEqual(values[("illustrative_resilient", "lower95")], 60_000)
            self.assertEqual(values[("illustrative_resilient", "mean")], 200_000)
            self.assertEqual(values[("illustrative_resilient", "upper95")], 340_000)
            self.assertEqual(values[("illustrative_fragile", "lower95")], 600_000)
            self.assertEqual(values[("illustrative_fragile", "mean")], 2_000_000)
            self.assertEqual(values[("illustrative_fragile", "upper95")], 3_400_000)
            self.assertTrue(result["receipt"]["one_physical_event_only"])
            self.assertTrue(result["receipt"]["no_annual_event_frequency_or_OEP_AEP"])
            self.assertTrue(result["receipt"]["no_actual_insured_GUL_IL_RI_loss"])

    def test_deterministic_output_bytes_and_no_insurer_loss_label(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            source = root / "source.zip"
            fake_hazard(source)
            result = calculate(source)
            a, b = root / "a.zip", root / "b.zip"
            receipt = model.write_output(a, result)
            model.write_output(b, result)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as z:
                self.assertEqual(len(z.namelist()), 4)
                for file, sha in receipt["output_sha256"].items():
                    self.assertEqual(hashlib.sha256(z.read(file)).hexdigest(), sha)
                contents = z.read("invented_event_conditional_site_direct_value.csv").decode()
                self.assertIn("ActualInsurerLossObserved", contents)
                self.assertIn("false", contents)
            with self.assertRaisesRegex(model.InventedDamageBlocked, "new output ZIP"):
                model.write_output(a, result)

    def test_manifest_false_insurer_or_year_scope_rejected(self):
        changes = (
            ("actual_1990_RV_insured_geographies_or_2025_RV_coverage_known", True),
            ("XWS_extreme_storm_selection_is_valid_annual_frequency_model", True),
            ("German_wind_vulnerability_by_material_roof_construction_validated", True),
            ("storm_uncertainty_variants_are_same_physical_event", False),
            ("status", "MODEL_ADMITTED"),
        )
        with TemporaryDirectory() as d:
            for i, (key, value) in enumerate(changes):
                p = Path(d) / f"bad-{i}.zip"
                fake_hazard(p, mutate_manifest=lambda m, k=key, v=value: m.__setitem__(k, v))
                with self.assertRaisesRegex(model.InventedDamageBlocked, "hazard-only"):
                    calculate(p)

    def test_changed_source_hash_and_original_provider_hash_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "source.zip"
            fake_hazard(p, mutate_sites=lambda rows: rows[0].__setitem__(
                "Daria1990MeanGustMps", "19"
            ), preserve_bad_site_hash=True)
            with self.assertRaisesRegex(model.InventedDamageBlocked, "content SHA"):
                calculate(p)
            q = Path(d) / "bad-pin.zip"
            fake_hazard(q, mutate_manifest=lambda m: m[
                "provider_original_four_XWS_CSV_source_receipt"]["original_files"][
                    "grid"].__setitem__("full_sha256", "0"*64))
            with self.assertRaisesRegex(model.InventedDamageBlocked, "provider CSV SHA"):
                calculate(q)

    def test_duplicate_sites_and_county_mismatch_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "duplicate.zip"
            fake_hazard(p, mutate_sites=lambda rows: rows[1].__setitem__(
                "FictionalSiteId", rows[0]["FictionalSiteId"]))
            with self.assertRaisesRegex(model.InventedDamageBlocked, "duplicate physical site"):
                calculate(p)
            q = Path(d) / "county.zip"
            fake_hazard(q, mutate_counties=lambda rows: rows[1].__setitem__(
                "FictionalBuildingTIVEUR", "999999"))
            with self.assertRaisesRegex(model.InventedDamageBlocked, "county and source-site"):
                calculate(q)

    def test_wrong_uncertainty_order_unsupported_wind_and_unsafe_zip_rejected(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            p = root / "inverted.zip"
            fake_hazard(p, mutate_sites=lambda rows: rows[0].__setitem__(
                "Daria1990Lower95GustMps", "30"))
            with self.assertRaisesRegex(model.InventedDamageBlocked, "reversed"):
                calculate(p)
            q = root / "unsupported.zip"
            fake_hazard(q, mutate_sites=lambda rows: rows[0].__setitem__(
                "Daria1990Upper95GustMps", "301"))
            with self.assertRaisesRegex(model.InventedDamageBlocked, "out-of-range"):
                calculate(q)
            t = root / "extra.zip"
            fake_hazard(t, extra=True)
            with self.assertRaisesRegex(model.InventedDamageBlocked, "unexpected"):
                calculate(t)

    def test_no_missing_source_or_symlink_input(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaisesRegex(model.InventedDamageBlocked, "hazard-derived ZIP"):
                calculate(root / "missing.zip")
            p = root / "real.zip"
            fake_hazard(p)
            link = root / "link.zip"
            link.symlink_to(p)
            with self.assertRaisesRegex(model.InventedDamageBlocked, "hazard-derived ZIP"):
                calculate(link)


if __name__ == "__main__":
    unittest.main()
