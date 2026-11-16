# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed offline contract regression for conflicting official JRC licences."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.validate_source_access import (
    SourceAccessError,
    validate_contract,
    validate_path,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "access" / "ec-jrc.cems.global-river-flood-hazard-maps.2026.rp10-id122.json"
PRODUCT_README = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/"
    "CEMS-GLOFAS/flood_hazard/README.txt"
)
PRODUCT_COPYRIGHT = (
    "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/"
    "CEMS-GLOFAS/flood_hazard/copyright.txt"
)
JRC_CATALOGUE = "https://data.jrc.ec.europa.eu/dataset/jrc-floods-floodmapgl_rp50y-tif"


class JrcGlofasRp10OfficialLicenseConflictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.obj = validate_path(CONTRACT)

    def test_exact_rp10_tile_remains_documentation_only(self) -> None:
        obj = self.obj
        self.assertEqual(
            obj["source_ids"],
            ["ec-jrc.cems.global-river-flood-hazard-maps.2026"],
        )
        self.assertIn("v2.1.2", obj["api_version"])
        self.assertIn("RP10 tile ID122 N50_E10", obj["api_version"])
        self.assertEqual(obj["status"], "documented_only")
        self.assertEqual(obj["probe_contract"]["mode"], "none")
        self.assertIsNone(obj["probe_contract"]["operation"])
        self.assertEqual(obj["implementation_decision"], "document_only")
        self.assertEqual(obj["authentication"]["mode"], "none")

    def test_official_licence_conflict_never_becomes_implicit_clearance(self) -> None:
        obj = self.obj
        rights = obj["rights_and_policy"]
        self.assertEqual(rights["dataset_rights_status"], "conflicting")
        self.assertEqual(rights["api_terms_status"], "unknown")
        self.assertEqual(rights["commercial_automation_status"], "unknown")
        self.assertEqual(rights["redistribution_status"], "unknown")
        self.assertFalse(bool(obj["probe_contract"]["expected_evidence"]))
        self.assertIn(PRODUCT_README, obj["evidence_urls"])
        self.assertIn(PRODUCT_COPYRIGHT, obj["evidence_urls"])
        self.assertIn(JRC_CATALOGUE, obj["evidence_urls"])
        self.assertIn("ODbL 1.0", rights["notes"])
        self.assertIn("CC BY 4.0", rights["notes"])
        self.assertIn("publisher clarification", rights["notes"])
        self.assertEqual(obj["reviewed_at"], "2026-11-15")

    def test_cannot_upgrade_redistribution_or_automation_with_conflicting_rights(self) -> None:
        for key in ("redistribution_status", "commercial_automation_status"):
            with self.subTest(key=key):
                candidate = copy.deepcopy(self.obj)
                candidate["rights_and_policy"][key] = "allowed"
                with self.assertRaises(SourceAccessError):
                    validate_contract(candidate)

    def test_cannot_activate_probe_with_unknown_service_terms(self) -> None:
        candidate = copy.deepcopy(self.obj)
        candidate["status"] = "probe_ready"
        candidate["probe_contract"]["mode"] = "metadata_get"
        candidate["probe_contract"]["operation"] = "fetch_rp10_depth"
        candidate["probe_contract"]["expected_evidence"] = ["bounded synthetic metadata evidence only"]
        with self.assertRaises(SourceAccessError):
            validate_contract(candidate)

    def test_cannot_promote_adapter_with_conflicting_rights(self) -> None:
        candidate = copy.deepcopy(self.obj)
        candidate["implementation_decision"] = "build_adapter_now"
        with self.assertRaises(SourceAccessError):
            validate_contract(candidate)


if __name__ == "__main__":
    unittest.main()
