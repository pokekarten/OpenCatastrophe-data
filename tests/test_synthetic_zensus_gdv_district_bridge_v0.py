# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent fictional 2022->2025 district, contract and market-cover tests."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"research_runners"))
from synthetic_regional_property_book_v0 import SyntheticBookError
from synthetic_zensus_gdv_district_bridge_v0 import compare_fictional_district_priors


def fixture():
    def row(ags, a, b, cover):
        return {
            "kreis_ags_2022": ags, "fictional_residential_buildings_2022":"80",
            "hypothetical_building_growth_factor_to_2025":"1",
            "hypothetical_contract_equivalents_per_building_capacity":"1.5",
            "carrier_prior_affinity_a":a, "carrier_prior_affinity_b":b,
            "hypothetical_market_elemental_cover_share":cover,
            "hypothetical_carrier_elemental_multiplier":"0.8",
            "hypothetical_written_premium_relativity":"1",
        }
    return {
        "schema_version":"0.1.0", "scenario_kind":"fully_synthetic_test_only",
        "country":"DE", "geo_scope":"kreis_ags_as_of_2022_05_15",
        "zensus_vintage":"2022-05-15", "market_cover_vintage":"2025-12-31",
        "company_reporting_year_end":"2025-12-31",
        "zensus_population":"buildings_with_residential_use_not_dwellings",
        "market_cover_population":"hypothetical_industry_full_elemental_cover_not_carrier",
        "issuer_population":"fictional_year_end_annual_duration_contracts_not_buildings",
        "gwp_basis":"fictional_annual_direct_gross_written_eur_cents",
        "gdv_extraction_status":"no_gdv_original_data_mining_or_acquisition",
        "source_bytes_status":"no_real_source_bytes_used",
        "fictional_carrier_contract_count":"100",
        "fictional_annual_direct_gwp_eur_cents":"1234567",
        "districts":[row("01001","3","1","0.5"),row("09162","1","3","0.8")]
    }


class ZensusGDVDistrictBridgeTests(unittest.TestCase):
    def test_two_cases_conserve_exact_integer_and_cents(self):
        out=compare_fictional_district_priors(fixture())
        self.assertEqual(out["hypothetical_contracts_shifted_between_priors"],50)
        self.assertEqual(out["total_variation_geographic_share"],"0.500000")
        self.assertEqual(out["district_count"],2)
        self.assertEqual(out["synthetic_national_contract_count"],100)
        for case in ("A","B"):
            rows=out["cases"][case]["regions"]
            self.assertEqual(sum(x["synthetic_contracts_at_year_end"] for x in rows),100)
            self.assertEqual(sum(x["hypothetical_regional_annual_gwp_eur_cents"] for x in rows),1234567)
            self.assertTrue(out["cases"][case]["synthetic_total_contracts_conserved"])
            self.assertTrue(out["cases"][case]["synthetic_total_annual_written_gwp_cents_conserved"])

    def test_case_changes_not_national_controls(self):
        out=compare_fictional_district_priors(fixture())
        a={x["region_code"]:x["synthetic_contracts_at_year_end"] for x in out["cases"]["A"]["regions"]}
        b={x["region_code"]:x["synthetic_contracts_at_year_end"] for x in out["cases"]["B"]["regions"]}
        self.assertEqual(a,{"KREIS_01001":75,"KREIS_09162":25})
        self.assertEqual(b,{"KREIS_01001":25,"KREIS_09162":75})

    def test_repeatability_order_and_explicit_input_sha(self):
        inp=fixture();first=compare_fictional_district_priors(inp)
        self.assertEqual(first,compare_fictional_district_priors(inp))
        inp["districts"].reverse()
        second=compare_fictional_district_priors(inp)
        self.assertEqual(first["total_variation_geographic_share"],second["total_variation_geographic_share"])
        self.assertEqual(first["cases"]["A"]["regions"],second["cases"]["A"]["regions"])
        self.assertNotEqual(first["input_sha256"],second["input_sha256"])

    def test_no_real_source_or_cat_authority(self):
        out=compare_fictional_district_priors(fixture())
        for k in ("zensus_2022_original_data_consumed","gdv_2025_original_data_consumed",
                  "original_insurer_records_consumed",
                  "different_vintages_reconciled_by_observation",
                  "building_to_contract_mapping_is_observed",
                  "regional_insurer_allocation_is_observed","cat_losses_observed",
                  "model_input_approved"):
            self.assertFalse(out[k],k)

    def test_population_scope_and_gwp_basis_are_typed(self):
        for k,wrong in [
            ("zensus_population","number_of_dwellings"),
            ("market_cover_population","insurer_observed_elemental"),
            ("issuer_population","unique_insured_buildings"),
            ("gwp_basis","net_earned_premiums")]:
            inp=fixture();inp[k]=wrong
            with self.subTest(field=k),self.assertRaisesRegex(SyntheticBookError,"source year"):
                compare_fictional_district_priors(inp)

    def test_original_external_gdv_acquisition_claim_rejected(self):
        for k,wrong in [
            ("gdv_extraction_status","scraped_gdv_map_2025"),
            ("source_bytes_status","genuine_original_data_with_sha"),
            ("scenario_kind","actual_company_book")]:
            inp=fixture();inp[k]=wrong
            with self.subTest(field=k),self.assertRaisesRegex(SyntheticBookError,"source year"):
                compare_fictional_district_priors(inp)

    def test_time_mismatch_and_geography_mismatch_rejected(self):
        for k,wrong in [("zensus_vintage","2025-12-31"),
                        ("market_cover_vintage","2024-12-31"),
                        ("company_reporting_year_end","2024-12-31"),
                        ("geo_scope","wgs84_house_coords")]:
            inp=fixture();inp[k]=wrong
            with self.subTest(field=k),self.assertRaisesRegex(SyntheticBookError,"source year"):
                compare_fictional_district_priors(inp)

    def test_duplicate_and_nonfive_digit_districts_fail(self):
        inp=fixture();inp["districts"][1]["kreis_ags_2022"]="01001"
        with self.assertRaisesRegex(SyntheticBookError,"duplicate"):
            compare_fictional_district_priors(inp)
        inp=fixture();inp["districts"][0]["kreis_ags_2022"]="0101"
        with self.assertRaisesRegex(SyntheticBookError,"five-digit"):
            compare_fictional_district_priors(inp)
        inp=fixture();inp["districts"][0]["kreis_ags_2022"]="99001"
        with self.assertRaisesRegex(SyntheticBookError,"five-digit"):
            compare_fictional_district_priors(inp)

    def test_buildings_not_dwellings_and_nonnegative_canonical_count(self):
        for bad in ("0","-1","NaN","1e4","1.5",12,None,False):
            inp=fixture();inp["districts"][0]["fictional_residential_buildings_2022"]=bad
            with self.subTest(value=bad),self.assertRaises(SyntheticBookError):
                compare_fictional_district_priors(inp)

    def test_missing_and_suppressed_census_counts_rejected(self):
        for bad in (None,"/","-","..."):
            inp=fixture();inp["districts"][0]["fictional_residential_buildings_2022"]=bad
            with self.subTest(value=bad),self.assertRaises(SyntheticBookError):
                compare_fictional_district_priors(inp)

    def test_growth_and_building_contract_conversion_must_be_explicit(self):
        for field,bad in [
            ("hypothetical_building_growth_factor_to_2025","0.1"),
            ("hypothetical_building_growth_factor_to_2025","3"),
            ("hypothetical_contract_equivalents_per_building_capacity","0"),
            ("hypothetical_contract_equivalents_per_building_capacity","5.1")]:
            inp=fixture();inp["districts"][0][field]=bad
            with self.subTest(field=field,value=bad),self.assertRaises(SyntheticBookError):
                compare_fictional_district_priors(inp)

    def test_explicit_capacity_infeasibility_rejects_national_claim(self):
        inp=fixture();inp["fictional_carrier_contract_count"]="241"
        with self.assertRaisesRegex(SyntheticBookError,"exceeds regional assumed capacity"):
            compare_fictional_district_priors(inp)

    def test_regional_capacity_saturation_can_reduce_prior_difference(self):
        inp=fixture();inp["districts"][0]["hypothetical_contract_equivalents_per_building_capacity"]="0.5"
        out=compare_fictional_district_priors(inp)
        for case in ("A","B"):
            counts={x["region_code"]:x["synthetic_contracts_at_year_end"]
                    for x in out["cases"][case]["regions"]}
            self.assertLessEqual(counts["KREIS_01001"],40)
            self.assertEqual(sum(counts.values()),100)

    def test_carrier_multiplier_not_identifiable_from_market_share(self):
        inp=fixture();out=compare_fictional_district_priors(inp)
        inp["districts"][0]["hypothetical_carrier_elemental_multiplier"]="0"
        alt=compare_fictional_district_priors(inp)
        for case in ("A","B"):
            self.assertEqual(
              out["cases"][case]["regions"][0]["synthetic_contracts_at_year_end"],
              alt["cases"][case]["regions"][0]["synthetic_contracts_at_year_end"])
            self.assertEqual(alt["cases"][case]["regions"][0]["hypothetical_elemental_cover_contract_equivalents"],0)
        self.assertFalse(alt["model_input_approved"])

    def test_nonfinite_percentage_and_excess_share_blocked(self):
        for bad in ("1.1","NaN","-0.1","0,8",0.8):
            inp=fixture();inp["districts"][1]["hypothetical_market_elemental_cover_share"]=bad
            with self.subTest(bad=bad),self.assertRaises(SyntheticBookError):
                compare_fictional_district_priors(inp)

    def test_same_priors_allow_zero_geographic_distance(self):
        inp=fixture()
        for row in inp["districts"]:
            row["carrier_prior_affinity_b"]=row["carrier_prior_affinity_a"]
        out=compare_fictional_district_priors(inp)
        self.assertEqual(out["hypothetical_contracts_shifted_between_priors"],0)
        self.assertEqual(out["total_variation_geographic_share"],"0.000000")

    def test_invalid_unused_authority_field_rejected(self):
        inp=fixture();inp["source_rights_approved"]=True
        with self.assertRaisesRegex(SyntheticBookError,"exact synthetic schema"):
            compare_fictional_district_priors(inp)


if __name__ == "__main__":
    unittest.main()
