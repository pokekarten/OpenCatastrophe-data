# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Corporate dwelling opportunities/official multi-LWU WFS are not insured sites."""
import tomllib,unittest,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"research/observations/rva_berlin_named_housing_public_stock_geography_2025_v0.toml"
TARGET={"WBM Wohnungsbaugesellschaft Berlin-Mitte mbH","GESOBAU AG","degewo AG"}
FALSES=("source_webpage_asset_sha256_verified","source_rights_reuse_corporate_pages_reviewed","known_company_insured_property_schedule","known_2025_rva_policy_count_for_named_clients",
        "known_rva_company_client_gross_tiv","known_joint_degewo_rva_consortium_cession",
        "known_2026_rva_policy_renewal","specific_client_loss_experience_by_peril_observed",
        "real_rva_site_geocodes_observed","can_merge_stock_into_1060546_insurer_solo_connected_building_contracts",
        "geospatial_join_approved")
WFS_FALSES=("published_polygon_contains_company_owner_id","published_polygon_contains_legal_insurer",
            "published_polygon_contains_insured_tiv","original_wfs_data_bytes_acquired",
            "source_WFS_feature_type_schema_live_tested",
            "company_specific_portfolio_join_possible_from_current_fields",
            "all_residential_company_dwellings_included_in_wfs",
            "individual_parcel_is_a_wbm_or_gesobau_or_degewo_insured_building")
CLIENT_FALSES=("actual_rva_insured_building_list_observed",
               "actual_rva_policy_contracts_observed","unit_is_individual_physical_building")
def load():return tomllib.loads(P.read_text(encoding="utf-8"))
def validate(d):
    if (d.get("schema_version")!="BERLIN_RVA_NAMED_HOUSING_ACCOUNTS_2025_PUBLIC_STOCK_OPPORTUNITIES_V0"
        or d.get("insurer_relationship_date")!="2025-04-01" or
        d.get("source_date_company_stocks")!="2025-12-31"
        or d.get("company_stocks_and_insurer_contracts_are_same_point_in_time") is not False
        or d.get("source_corporate_dwellings_are_not_actual_insured_buildings") is not True):
        raise ValueError("corporate stock / insurer source or time conflation")
    if any(d.get(k) is not False for k in FALSES):
        raise ValueError("company stock falsely promoted to insurer physical exposure")
    rows=d.get("corporate_stock",[])
    if len(rows)!=3 or {r.get("entity") for r in rows}!=TARGET:
        raise ValueError("incorrect primary reported housing corporations")
    m={r["entity"]:r for r in rows}
    wbm=m["WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"]
    ges=m["GESOBAU AG"]
    deg=m["degewo AG"]
    if (wbm.get("residential_dwelling_units")!=34498 or
        wbm.get("residential_floor_area_m2")!=2159600 or
        wbm.get("commercial_floor_area_m2")!=314000 or
        ges.get("residential_dwelling_units")!=48800 or
        ges.get("residential_dwelling_count_is_exact_as_published") is not False or
        deg.get("residential_dwelling_lower_bound_exclusive")!=83000 or
        deg.get("residential_dwelling_count_is_exact_as_published") is not False):
        raise ValueError("wrong publicly reported housing-unit opportunity counts")
    for r in rows:
        if any(r.get(k) is not False for k in CLIENT_FALSES):
            raise ValueError("dwelling mistaken for insured building or policy")
        if r.get("reference_year")!=2025 or not r.get("source_url","").startswith("https://"):
            raise ValueError("source vintage/origin invalid")
    wfs=d["berlin_official_wfs"]
    if (wfs.get("source_url")!="https://daten.berlin.de/datensaetze/wohnungsbestand-der-landeseigenen-wohnungsunternehmen-wfs-4c4e0115" or
        wfs.get("official_technical_data_description_url")!="https://gdi.berlin.de/data/lwu/docs/Datenformatbeschreibung_LWU.pdf" or
        wfs.get("reference_date")!="2025-12-31" or
        wfs.get("license")!="Datenlizenz Deutschland Zero 2.0" or
        wfs.get("geometry")!="polygon_of_cadastral_parcel_not_individual_building" or
        wfs.get("threshold_min_residential_units_per_address")!=4 or
        wfs.get("published_polygon_attributes")!=["gisid","typ"] or
        wfs.get("parcel_can_include_housing_stock_of_other_landlords") is not True):
        raise ValueError("unverified official WFS contents or per-parcel company attribution")
    if any(wfs.get(k) is not False for k in WFS_FALSES):
        raise ValueError("public parcel footprint wrongly treated as insured insurer site")
    return m

class PublicNamedHousingOpportunityTests(unittest.TestCase):
    def setUp(self):self.c=load()
    def test_three_named_public_original_stock_sources(self):self.assertEqual(len(validate(self.c)),3)
    def test_corporate_inventory_is_not_insurer_2025_sites(self):
        validate(self.c)
        self.assertTrue(all(self.c[x] is False for x in FALSES))
    def test_two_exact_reported_wbm_2025_figures(self):
        m=validate(self.c);v=m["WBM Wohnungsbaugesellschaft Berlin-Mitte mbH"]
        self.assertEqual(v["residential_dwelling_units"],34498)
        self.assertEqual(v["residential_floor_area_m2"],2159600)
    def test_gesobau_2025_units_approx_not_exact(self):
        m=validate(self.c);r=m["GESOBAU AG"]
        self.assertEqual(r["additional_third_party_managed_dwelling_units_approx"],700)
        self.assertFalse(r["residential_dwelling_count_is_exact_as_published"])
    def test_degewo_coinsurance_2025_and_company_dwellings_not_share(self):
        m=validate(self.c);r=m["degewo AG"]
        self.assertIn("Allianz",r["named_building_insurer_2025_senate"])
        self.assertFalse(self.c["known_joint_degewo_rva_consortium_cession"])
    def test_open_wfs_source_has_no_company_identifier(self):
        w=validate(self.c) and self.c["berlin_official_wfs"]
        self.assertEqual(w["published_polygon_attributes"],["gisid","typ"])
        self.assertFalse(w["company_specific_portfolio_join_possible_from_current_fields"])
    def test_wfs_polygon_can_contain_other_landlord_units(self):
        w=self.c["berlin_official_wfs"]
        self.assertTrue(w["parcel_can_include_housing_stock_of_other_landlords"])
        self.assertFalse(w["individual_parcel_is_a_wbm_or_gesobau_or_degewo_insured_building"])
    def test_malformed_wbm_units_rejected(self):
        self.c["corporate_stock"][0]["residential_dwelling_units"]+=1
        with self.assertRaises(ValueError):validate(self.c)
    def test_false_company_specific_geometry_rejected(self):
        self.c["berlin_official_wfs"]["company_specific_portfolio_join_possible_from_current_fields"]=True
        with self.assertRaises(ValueError):validate(self.c)
    def test_false_wfs_original_acquisition_rejected(self):
        self.c["berlin_official_wfs"]["original_wfs_data_bytes_acquired"]=True
        with self.assertRaises(ValueError):validate(self.c)
    def test_false_2025_rv_stock_claim_rejected(self):
        self.c["known_company_insured_property_schedule"]=True
        with self.assertRaises(ValueError):validate(self.c)
    def test_company_site_join_privacy_not_inferred(self):
        self.c["corporate_stock"][0]["actual_rva_insured_building_list_observed"]=True
        with self.assertRaises(ValueError):validate(self.c)

if __name__=="__main__":
    unittest.main()
