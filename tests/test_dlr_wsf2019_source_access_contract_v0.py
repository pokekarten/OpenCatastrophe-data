# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline exact DLR WSF2019 source-rights/host/fixed-range contract regression.

Do not touch provider network, download original pixels, or change admission.
"""
from copy import deepcopy
from pathlib import Path
import unittest

from scripts.probe_dlr_wsf_native_cog_tile_v0 import (
    HEADER_SIZE, HEADER_SHA256, NATIVE_TILE_BYTES,
    NATIVE_TILE_OFFSET, NATIVE_TILE_SHA256, SOURCE, URL,
)
from scripts.validate_source_access import (
    SourceAccessError, validate_contract, validate_path,
)

CONTRACT = Path(__file__).resolve().parents[1] / "access" / "dlr.wsf.2019.native-geotiff.json"


class DLRWSF2019AccessTests(unittest.TestCase):
    def test_original_identity_range_and_source_rights_not_live_admission(self):
        c = validate_path(CONTRACT)
        self.assertEqual(c["source_ids"], [SOURCE])
        self.assertEqual(c["access_id"], "dlr.wsf.2019.native-geotiff")
        self.assertEqual(c["interface_type"], "http_file")
        self.assertEqual(c["status"], "documented_only")
        self.assertEqual(c["service_root"] + c["request_contract"]["path_templates"][0], URL)
        self.assertEqual(c["authentication"]["mode"], "none")
        self.assertEqual(c["probe_contract"], {
            "mode": "none", "operation": None,
            "requires_credentials": False, "expected_evidence": [],
        })
        self.assertEqual(c["rights_and_policy"]["dataset_rights_status"], "verified")
        self.assertEqual(c["rights_and_policy"]["api_terms_status"], "unknown")
        self.assertEqual(c["rights_and_policy"]["commercial_automation_status"], "unknown")
        self.assertEqual(c["rights_and_policy"]["redistribution_status"], "unknown")
        self.assertEqual(c["implementation_decision"], "document_only")
        self.assertEqual(c["operational_constraints"]["max_probe_bytes"], HEADER_SIZE)
        self.assertEqual(c["operational_constraints"]["max_sample_bytes"],
                         HEADER_SIZE + NATIVE_TILE_BYTES)
        self.assertIn(f"bytes={NATIVE_TILE_OFFSET}-{NATIVE_TILE_OFFSET + NATIVE_TILE_BYTES - 1}",
                      c["request_contract"]["parameter_rules"])
        self.assertIn(HEADER_SHA256, c["operational_constraints"]["mutability_notes"])
        self.assertIn(NATIVE_TILE_SHA256, c["operational_constraints"]["mutability_notes"])
        self.assertIn("NOT the full GeoTIFF SHA-256",
                      c["operational_constraints"]["mutability_notes"])
        self.assertIn("not individual buildings",
                      c["response_contract"]["scientific_semantics"])

    def test_unknown_service_terms_cannot_enable_an_active_probe(self):
        c = deepcopy(validate_path(CONTRACT))
        c["status"] = "probe_ready"
        c["probe_contract"] = {
            "mode": "metadata_get",
            "operation": "fixed_original_geotiff_two_ranges",
            "requires_credentials": False,
            "expected_evidence": ["original SHA-256 and retrieval UTC"],
        }
        with self.assertRaises(SourceAccessError):
            validate_contract(c)

    def test_no_untrusted_host_or_traversal_in_documented_path(self):
        c = deepcopy(validate_path(CONTRACT))
        c["service_root"] = "http://127.0.0.1"
        with self.assertRaises(SourceAccessError):
            validate_contract(c)
        c = deepcopy(validate_path(CONTRACT))
        c["request_contract"]["path_templates"] = ["/WSF2019/files/../other.tif"]
        with self.assertRaises(SourceAccessError):
            validate_contract(c)


if __name__ == "__main__":
    unittest.main()
