# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests for R+V external calibration source landscape: NO source downloads."""
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

PATH = Path(__file__).resolve().parents[1] / "research" / "observations" / "rva_external_calibration_source_candidates_v0.json"
DOMAINS = {
    "www.ruv.de", "berichte.bvr.de", "www.destatis.de", "genesis.destatis.de",
    "opendata.dwd.de", "gdz.bkg.bund.de", "www.gdv.de",
}
FIELDS = {
    "source_id", "publisher", "title", "url", "scope", "role", "grain",
    "vintage", "rights_gate", "original_asset_sha256_verified_here",
    "insurer_location_or_tiv_proven", "model_input_admitted", "limitation",
}


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def validate(payload):
    assert payload["schema_version"] == "RVA_EXTERNAL_CALIBRATION_SOURCE_CANDIDATES_V0"
    assert payload["target_entity"] == "R+V Allgemeine Versicherung AG"
    assert payload["admission_status"] == "NOT_ADMITTED_RESEARCH_ONLY"
    assert payload["assessed_at"] == "2026-11-04"
    assert payload["SPDX-License-Identifier"] == "Apache-2.0"
    records = payload["records"]
    assert len(records) == payload["source_count"] >= 20
    ids = set()
    for row in records:
        assert set(row) == FIELDS
        assert isinstance(row["source_id"], str) and row["source_id"] not in ids
        ids.add(row["source_id"])
        u = urlsplit(row["url"])
        assert u.scheme == "https" and u.hostname in DOMAINS and not u.username and not u.password
        assert not row["source_id"].startswith("rv.group.") or row["scope"] == "group"
        assert row["scope"] in {
            "solo", "group", "issuer_unspecified", "industry_proxy",
            "physical_stock", "building_valuation", "meteorological",
            "hazard_scenario", "industry",
        }
        assert row["role"] in {
            "control", "longitudinal_control", "context_only", "historical_holdout_candidate",
            "distribution_proxy", "building_stock_prior", "valuation_index_prior",
            "event_frequency_candidate", "hazard_marginal", "spatial_scenario_challenge",
        }
        assert row["original_asset_sha256_verified_here"] is False
        assert row["insurer_location_or_tiv_proven"] is False
        assert row["model_input_admitted"] is False
        assert len(row["limitation"]) >= 35
        assert row["rights_gate"] not in {"approved", "free_commercial_reuse", "unrestricted"}
    return {r["source_id"]: r for r in records}


class RvaExternalSourcesTests(unittest.TestCase):
    def test_json_and_complete_research_inventory(self):
        self.assertEqual(len(validate(load())), 21)

    def test_group_not_solo_and_claims_not_peril_loss(self):
        rows = validate(load())
        for name in ("rv.group.cat2025", "rv.group.bernd2021",
                     "rv.group.hail2024", "rv.group.flood2024"):
            self.assertEqual(rows[name]["scope"], "group")
            self.assertFalse(rows[name]["model_input_admitted"])
        self.assertIn("not pure residential", rows["rv.group.hail2024"]["limitation"].lower())

    def test_gdv_tdm_explicitly_blocked_even_if_public_pages_readable(self):
        rows = validate(load())
        for n in ("gdv.ngr2026", "gdv.storm.hail.state2026"):
            self.assertEqual(rows[n]["rights_gate"], "gdv_tdm_explicit_consent_required")
            self.assertFalse(rows[n]["original_asset_sha256_verified_here"])

    def test_bkg_missing_region_no_zero_hazard_assumption(self):
        rows = validate(load())
        r = rows["bkg.pluvial2026"]
        self.assertEqual(r["role"], "spatial_scenario_challenge")
        self.assertIn("BY/BW/HE/SL", r["limitation"])
        self.assertFalse(r["insurer_location_or_tiv_proven"])

    def test_radar_event_alternatives_are_not_independent_catalogues(self):
        rows = validate(load())
        self.assertEqual(rows["dwd.catrare.w3.2026"]["vintage"], rows["dwd.catrare.t5.2026"]["vintage"])
        self.assertIn("RADKLIM", rows["dwd.catrare.t5.2026"]["limitation"])
        self.assertEqual(rows["dwd.kostra2020"]["role"], "hazard_marginal")

    def test_2025_cooperative_bank_sector_not_insurer_distribution(self):
        rows = validate(load())
        self.assertIn("NOT 640+", rows["bvr.regional2025"]["limitation"])
        self.assertEqual(rows["rv.distribution.network"]["scope"], "group")

    def test_separate_valuation_indices_not_insured_tiv(self):
        rows = validate(load())
        self.assertEqual(rows["destatis.baukosten2025"]["role"], "valuation_index_prior")
        self.assertEqual(rows["destatis.baupreis2025"]["role"], "valuation_index_prior")
        self.assertFalse(rows["destatis.zensus2022"]["insurer_location_or_tiv_proven"])

    def test_fail_when_promoted_to_model_input(self):
        d = load()
        d["records"][0]["model_input_admitted"] = True
        with self.assertRaises(AssertionError):
            validate(d)

    def test_fail_when_group_loss_falsely_marked_solo(self):
        d = load()
        for r in d["records"]:
            if r["source_id"] == "rv.group.bernd2021":
                r["scope"] = "solo"
        with self.assertRaises(AssertionError):
            validate(d)


if __name__ == "__main__":
    unittest.main()
