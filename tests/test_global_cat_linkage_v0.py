# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""New worldwide CAT source link hypotheses remain non-admission research."""
from __future__ import annotations

import unittest

from scripts.source_landscape_contract import load_landscape_shards
from scripts.source_linkage_audit_v0 import build_audit


NEW_LINK_IDS = {
    "jrc-flood-depth-versus-gfm-shared-source",
    "openbuildingmap-overture-ghsl-common-upstream",
    "aqueduct-v2-versus-jrc-flood-hazard",
    "gem-global-seismic-exposure-vulnerability",
    "iris-ibtracs-storm-dependence",
    "aqueduct-water-risk-versus-aqueduct-floods",
}
NEW_SOURCE_IDS = {
    "ec.jrc.satellite-flood-depth-europe.2015-2024",
    "gfz.openbuildingmap.global.2025",
    "wri.aqueduct-flood-hazard.v2.2020",
    "wri.aqueduct.water-risk-atlas.v4.0",
    "gem.global-seismic-hazard-map.v2026.1",
    "imperial.iris.synthetic-tropical-cyclones.2024",
}


class GlobalCatLinkageTests(unittest.TestCase):
    def test_new_sources_have_no_implied_admission_or_rights(self):
        audit = build_audit(load_landscape_shards())
        found = {r["candidate_id"]: r for r in audit["source_inventory"]}
        self.assertTrue(NEW_SOURCE_IDS.issubset(found))
        for source in NEW_SOURCE_IDS:
            with self.subTest(source=source):
                row = found[source]
                self.assertEqual(row["admission_status"], "not_admitted")
                self.assertEqual(row["rights_review_status"], "not_reviewed")
                self.assertEqual(row["scientific_review_status"], "not_reviewed")
                self.assertFalse(row["automated_model_import_allowed_by_this_audit"])

    def test_all_new_linkages_are_conservative_and_bidirectional_in_provenance(self):
        audit = build_audit(load_landscape_shards())
        links = {r["recipe_id"]: r for r in audit["linkage_hypotheses"]}
        self.assertTrue(NEW_LINK_IDS.issubset(links))
        for recipe in NEW_LINK_IDS:
            with self.subTest(recipe=recipe):
                link = links[recipe]
                self.assertTrue(link["validation_only"])
                self.assertFalse(link["automatic_source_join_allowed"])
                self.assertFalse(link["scientific_independence_proven"])
                self.assertFalse(link["model_input_admitted"])
                self.assertGreaterEqual(len(link["source_candidate_ids"]), 2)
                self.assertTrue(link["required_join_evidence"])
                self.assertTrue(link["prohibited_inferences"])

    def test_derived_and_distinct_products_remain_distinguishable(self):
        audit = build_audit(load_landscape_shards())
        links = {r["recipe_id"]: r for r in audit["linkage_hypotheses"]}
        self.assertIn("same_sentinel1", links["jrc-flood-depth-versus-gfm-shared-source"]["relationship"])
        self.assertIn("shared", links["openbuildingmap-overture-ghsl-common-upstream"]["relationship"])
        self.assertIn("distinct", links["aqueduct-water-risk-versus-aqueduct-floods"]["relationship"])
        self.assertIn("observational_input", links["iris-ibtracs-storm-dependence"]["relationship"])


if __name__ == "__main__":
    unittest.main()
