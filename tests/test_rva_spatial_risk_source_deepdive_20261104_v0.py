# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed source-discovery checks, with no original download and no model/DB writes."""
from pathlib import Path
import tomllib
import unittest
from urllib.parse import urlsplit

PATH = (Path(__file__).resolve().parents[1] / "research" /
        "observations" / "rva_spatial_risk_source_deepdive_20261104_v0.toml")
EXPECTED = {
    "destatis.zensus.heated.1km.2026", "destatis.zensus.age.100m.2022",
    "destatis.zensus.ownership.100m.2026", "bavaria.lod2.open.citygml",
    "nrw.lod2.open.citygml", "saxony.lod2.open.citygml", "bw.lod2.open.citygml",
    "adv.hu-de.restricted.2026", "bkg.lod2-de.restricted.2026",
    "nrw.solar.roof.category.municipality", "nrw.solar.potential.geometry",
    "bnetza.mastr.public.xml", "immo.nhk2010.legal", "thuenen.agraratlas.v1.2022",
    "destatis.agri.atlas.2020", "regionalstatistik.sme.52111-01-02-4",
    "bavaria.fluvial.hq100.wms", "bavaria.fluvial.depth.wms",
    "rlp.fluvial.hq.depth.wfs", "rlp.pluvial.sri7.sri10", "nrw.fluvial.hq100",
    "dwd.konrad3d.operational", "dwd.wind.hourly.historical",
    "essl.eswd.report.api", "rv.group.saarland.2024-05",
    "vTV.solo.report.2025", "kravag.2025.affiliates",
    "mastr.geo.versioned.pv.secondary",
}
FIELDS = {
    "id", "publisher", "url", "kind", "years", "geography",
    "intended_scenario_use", "rights_gate", "priority",
    "original_dataset_bytes_sha256_verified",
    "real_rv_insured_building_identity_observed",
    "source_dataset_automatically_mined_or_ingested",
    "source_approved_for_cat_model", "limitation",
}
HOSTS = {
    "www.destatis.de", "geodaten.bayern.de", "www.opengeodata.nrw.de",
    "www.geodaten.sachsen.de", "www.lglbw.de", "www.lvg.bayern.de",
    "gdz.bkg.bund.de", "www.marktstammdatenregister.de",
    "www.gesetze-im-internet.de", "zenodo.org", "www.regionalstatistik.de",
    "www.lfu.bayern.de", "wasserportal.rlp-umwelt.de", "open.nrw",
    "www.dwd.de", "opendata.dwd.de", "eswd.eu", "www.ruv.de",
    "www.kravag.de",
}
NEVER_TRUE = (
    "original_dataset_bytes_sha256_verified",
    "real_rv_insured_building_identity_observed",
    "source_dataset_automatically_mined_or_ingested",
    "source_approved_for_cat_model",
)
TOP_LEVEL_NEVER_TRUE = (
    "company_addresses_observed", "company_tiv_observed",
    "historical_company_regional_shares_observed",
    "actual_contract_coverage_observed", "cat_model_inputs_approved",
)

def load():
    return tomllib.loads(PATH.read_text(encoding="utf-8"))

def verify(d):
    if (d.get("schema_version")!="RVA_SPATIAL_RISK_SOURCE_DEEPDIVE_V0"
        or d.get("target_company")!="R+V Allgemeine Versicherung AG"
        or d.get("record_date")!="2026-11-04"
        or d.get("records_are_public_candidates_only") is not True
        or any(d.get(k) is not False for k in TOP_LEVEL_NEVER_TRUE)):
        raise ValueError("R+V public discovery scope changed or promotion to production")
    items=d.get("sources",[])
    if len(items)!=d.get("source_count") or len(items)!=len(EXPECTED):
        raise ValueError("Unexpected source count")
    by_id={}
    for row in items:
        if set(row)!=FIELDS or not isinstance(row.get("id"),str) or row["id"] in by_id:
            raise ValueError("Missing/duplicate/unsupported source attributes")
        url=urlsplit(row["url"])
        if url.scheme!="https" or url.hostname not in HOSTS or url.username or url.password or url.fragment:
            raise ValueError("Nonoriginal / unapproved source URL")
        if any(row.get(k) is not False for k in NEVER_TRUE):
            raise ValueError("Unverified company original data or rights promoted as approved")
        if row["priority"] not in ("P0","P1","P2") or len(row["limitation"])<75:
            raise ValueError("Missing priority or scientifically bounded source definition")
        if not row.get("rights_gate") or row["rights_gate"] in ("approved","unrestricted","public_data_production"):
            raise ValueError("Source licensing shortcut")
        by_id[row["id"]]=row
    if set(by_id)!=EXPECTED:
        raise ValueError("Source identity drift")
    if by_id["rv.group.saarland.2024-05"]["kind"]!="rv_group_event_loss_snapshot":
        raise ValueError("Issuer group May 2024 event incorrectly attributed to solo")
    if by_id["bnetza.mastr.public.xml"]["kind"]!="pv_installed_public_registry":
        raise ValueError("Installed PV source is not rooftop potential")
    if by_id["nrw.solar.roof.category.municipality"]["kind"]!="pv_roof_potential":
        raise ValueError("PV roof opportunity is not physically installed or insurer-owned PV")
    if not all(by_id[k]["rights_gate"].startswith(("license_",)) for k in (
        "adv.hu-de.restricted.2026","bkg.lod2-de.restricted.2026")):
        raise ValueError("Restricted national building footprints cannot be open by fiat")
    if by_id["thuenen.agraratlas.v1.2022"]["kind"]!="agrarian_modelled_municipality":
        raise ValueError("Thuenen estimated municipality farmland is not insured R+V buildings")
    if by_id["rlp.pluvial.sri7.sri10"]["kind"]!="pluvial_hazard_scenario":
        raise ValueError("Pluvial is distinct from river flooding")
    if by_id["rlp.fluvial.hq.depth.wfs"]["kind"]!="fluvial_hazard_scenario":
        raise ValueError("Fluvial hazard not insured flood claims or rainfall")
    return by_id

class RvSpatialSourceResearchTests(unittest.TestCase):
    def test_complete_original_source_inventory(self):
        self.assertEqual(len(verify(load())),28)

    def test_no_provider_raw_rows_insurer_geocodes_or_model_admission(self):
        rows=verify(load())
        self.assertTrue(all(not x["source_approved_for_cat_model"] for x in rows.values()))

    def test_two_separate_2024_flood_events_cannot_be_passed_as_solo(self):
        d=load()
        for row in d["sources"]:
            if row["id"]=="rv.group.saarland.2024-05":
                row["kind"]="solo_verified_cat_loss"
        with self.assertRaises(ValueError): verify(d)

    def test_national_lod2_hude_are_not_open_assets(self):
        d=load()
        for row in d["sources"]:
            if row["id"]=="adv.hu-de.restricted.2026":
                row["rights_gate"]="approved"
        with self.assertRaises(ValueError): verify(d)

    def test_mastr_registered_units_not_potential(self):
        d=load()
        for row in d["sources"]:
            if row["id"]=="bnetza.mastr.public.xml":
                row["kind"]="pv_roof_potential"
        with self.assertRaises(ValueError):verify(d)

    def test_nrw_potential_not_actual_installed_pv(self):
        d=load()
        for row in d["sources"]:
            if row["id"]=="nrw.solar.roof.category.municipality":
                row["kind"]="pv_installed_public_registry"
        with self.assertRaises(ValueError):verify(d)

    def test_agraratlas_is_estimate_not_company_farm_sites(self):
        d=load()
        for row in d["sources"]:
            if row["id"]=="thuenen.agraratlas.v1.2022":
                row["kind"]="observed_rv_insured_farm_sites"
        with self.assertRaises(ValueError):verify(d)

    def test_fluvial_and_pluvial_not_relabelled_same_event_stream(self):
        d=load()
        for row in d["sources"]:
            if row["id"]=="rlp.pluvial.sri7.sri10":
                row["kind"]="fluvial_hazard_scenario"
        with self.assertRaises(ValueError):verify(d)

    def test_explicit_rejection_of_unverified_pdf_bytes(self):
        d=load();d["sources"][0]["original_dataset_bytes_sha256_verified"]=True
        with self.assertRaises(ValueError):verify(d)

    def test_explicit_rejection_of_real_rv_site_claim(self):
        d=load();d["sources"][0]["real_rv_insured_building_identity_observed"]=True
        with self.assertRaises(ValueError):verify(d)

    def test_explicit_rejection_of_noncandidate_catalogue(self):
        d=load();d["records_are_public_candidates_only"]=False
        with self.assertRaises(ValueError):verify(d)

    def test_reject_unknown_source_url(self):
        d=load();d["sources"][0]["url"]="https://suspicious.invalid/redirect"
        with self.assertRaises(ValueError):verify(d)

if __name__ == "__main__":
    unittest.main()
