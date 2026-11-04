# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline census county and MaStR-derived PV bridge guards. No external fetch."""
from pathlib import Path
import tempfile
import unittest

from research_runners import rva_nrw_53kreis_pv_zensus_physical_source_bridge_v0 as m


class NRW53CountyPhysicalBridgeTests(unittest.TestCase):
    def test_reproducible_official_53_county_source_population(self):
        b,a=m.load_public_county_context()
        self.assertEqual(len(b),53)
        self.assertEqual(len(a),53)
        self.assertEqual(set(b),set(a))
        self.assertEqual(sum(r["geb_mit_wohnraum"] for r in b.values()),4042220)
        self.assertTrue(all(x.startswith("05") and len(x)==5 for x in b))

    def test_publisher_age_bands_are_2022_physical_not_2025_roof_age(self):
        b,a=m.load_public_county_context()
        for key in b:
            self.assertEqual(len(a[key]["age_bands_source_order"]),10)
            self.assertLessEqual(
                abs(sum(a[key]["age_bands_source_order"])-b[key]["geb_mit_wohnraum"]),20
            )

    def test_2022_census_source_and_2026_registry_stay_distinct(self):
        self.assertNotEqual(m.BUILDINGS.name,m.AGE.name)
        self.assertEqual(len(m.SOURCE_ORIGINAL_CENSUS_SHA),64)
        self.assertNotEqual(
            m.SOURCE_ORIGINAL_CENSUS_SHA,m.ma.THIRD_PARTY_BLOB_SHA1
        )
        self.assertEqual(m.EXPECTED_KREIS_NRW,53)

    def test_first_five_digit_prefix_joins_census_kreis(self):
        b,_=m.load_public_county_context()
        self.assertIn("05162",b)
        self.assertIn("05978",b)

    def test_modified_2022_vintage_blocks_source_import(self):
        with tempfile.TemporaryDirectory() as path:
            source=m.BUILDINGS.read_text(encoding="utf-8")
            source=source.replace('source_event_date = "2022-05-15"',
                                  'source_event_date = "2025-12-31"')
            tmp=Path(path)/"changed.toml"
            tmp.write_text(source,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SOURCE_OR_PERIMETER_INVALID"):
                m.load_public_county_context(building_file=tmp)

    def test_mutated_census_original_sha_blocks(self):
        with tempfile.TemporaryDirectory() as path:
            source=m.AGE.read_text(encoding="utf-8")
            source=source.replace(m.SOURCE_ORIGINAL_CENSUS_SHA,"0"*64)
            tmp=Path(path)/"forged-age.toml"
            tmp.write_text(source,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SOURCE_OR_PERIMETER_INVALID"):
                m.load_public_county_context(age_file=tmp)

    def test_forged_2025_insurer_model_admission_blocks(self):
        with tempfile.TemporaryDirectory() as path:
            source=m.AGE.read_text(encoding="utf-8")
            source=source.replace("insurer_model_input_admitted = false",
                                  "insurer_model_input_admitted = true")
            tmp=Path(path)/"forged-ages.toml"
            tmp.write_text(source,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"SOURCE_OR_PERIMETER_INVALID"):
                m.load_public_county_context(age_file=tmp)

    def test_district_universe_has_nonzero_official_building_denominator(self):
        b,_=m.load_public_county_context()
        self.assertTrue(all(
            type(r["geb_mit_wohnraum"]) is int and r["geb_mit_wohnraum"]>0
            for r in b.values()
        ))

    def test_no_company_location_claim_in_report_schema(self):
        text=(Path(__file__).resolve().parents[1] /
            "research_runners" /
            "rva_nrw_53kreis_pv_zensus_physical_source_bridge_v0.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"2025_RV_company_policy_locations_estimated_from_these_data":False',text)
        self.assertIn('"installed_unit_count_equals_roof_or_insured_building":False',text)
        self.assertIn('"hazard_loss_model_admitted":False',text)


if __name__=="__main__":
    unittest.main()
