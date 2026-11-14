# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline customer-vs-anonymous host legal evidence and no-GET gate.

These tests do not access JRC or CloudFerro and do not grant permission.
"""
from __future__ import annotations

from copy import deepcopy
import tomllib
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from scripts.validate_source_access import validate_path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "research_runners/policies/jrc_gsw_v15_cloudferro_host_scope_v0.toml"
CONTRACT = ROOT / "access/ec-jrc.global-surface-water.1984-2024.json"
EVIDENCE_DOC = ROOT / "docs/research/jrc-gsw-v15-cloudferro-public-host-policy-20261114.md"

EXPECTED_TILE = (
    "https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/"
    "download2024/Aggregated/VER1-5/occurrence/"
    "occurrence_10E_50N_v1_5_2024.tif"
)


def is_live_probe_authorized(policy: dict, contract: dict) -> bool:
    """Conservative test-only gate: true requires INDEPENDENT reviewed approvals.

    Current source contract and policy must return false. This explicitly
    rejects unilateral edits of the policy 'approved' flag and ensures that
    a downloadable script never counts as network automation authorization.
    """
    return (
        policy.get("source_id") == "ec-jrc.global-surface-water.1984-2024"
        and policy.get("fixed_tile_url") == EXPECTED_TILE
        and policy.get("public_anonymous_download_permission") == "reviewed_allowed"
        and policy.get("customer_terms_applicability_to_anonymous_reader") == "reviewed"
        and isinstance(policy.get("anonymous_http_rate_cap"), int)
        and policy["anonymous_http_rate_cap"] > 0
        and isinstance(policy.get("approved_network_requests"), int)
        and policy["approved_network_requests"] > 0
        and isinstance(policy.get("approved_original_download_bytes"), int)
        and policy["approved_original_download_bytes"] > 0
        and policy.get("live_provider_probe_approved") is True
        and contract.get("status") == "probe_ready"
        and contract.get("probe_contract", {}).get("mode") != "none"
        and contract.get("rights_and_policy", {}).get("api_terms_status") == "reviewed_allowed"
        and contract.get("rights_and_policy", {}).get("commercial_automation_status") == "allowed"
    )


class JRCCloudFerroHostScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = tomllib.loads(POLICY.read_text(encoding="utf-8"))
        cls.contract = validate_path(CONTRACT)
        cls.doc = EVIDENCE_DOC.read_text(encoding="utf-8")

    def test_exact_publisher_and_tile_without_arbitrary_host(self):
        p = self.policy
        self.assertEqual(p["source_id"], self.contract["source_ids"][0])
        self.assertEqual(p["access_id"], self.contract["access_id"])
        self.assertEqual(p["fixed_tile_url"], EXPECTED_TILE)
        source = urlsplit(p["fixed_tile_url"])
        self.assertEqual(source.scheme, "https")
        self.assertEqual(source.netloc, p["delivery_host"])
        self.assertFalse(source.query or source.fragment or source.username)
        self.assertIn(source.path, self.contract["request_contract"]["path_templates"])
        self.assertNotIn("VER1-4",source.path)
        self.assertNotIn("monthlyhistory",source.path.lower())
        self.assertEqual(p["fixed_product"],
                         "GSW v1.5 1984-2024 corrected 2026-11-10 Occurrence")

    def test_licence_not_copied_to_http_service_permission(self):
        p = self.policy
        self.assertEqual(p["dataset_reuse_status"], "allowed_with_attribution")
        self.assertEqual(p["required_attribution"], "Source: EC JRC/Google")
        self.assertEqual(p["publisher_script_status"],
                         "verified_direct_cloudferro_downloader")
        self.assertEqual(p["public_anonymous_download_permission"], "unknown")
        self.assertEqual(p["customer_terms_applicability_to_anonymous_reader"],
                         "unverified")
        self.assertEqual(p["anonymous_http_rate_cap"], "unknown")
        self.assertEqual(p["approved_network_requests"], 0)
        self.assertEqual(p["approved_original_download_bytes"], 0)
        self.assertFalse(p["live_provider_probe_approved"])
        self.assertEqual(self.contract["status"], "documented_only")
        self.assertEqual(self.contract["probe_contract"]["mode"], "none")
        self.assertEqual(self.contract["rights_and_policy"]["api_terms_status"],
                         "separate_unreviewed")
        self.assertEqual(self.contract["rights_and_policy"]["commercial_automation_status"],
                         "unknown")
        self.assertIsNone(self.contract["rights_and_policy"]["terms_url"])
        self.assertFalse(is_live_probe_authorized(p,self.contract))

    def test_customer_terms_are_evidence_not_permission(self):
        p=self.policy
        self.assertIn("general_terms_and_conditions.pdf",
                      p["provider_host_customer_general_terms"])
        self.assertIn("excessive", p["customer_terms_clause"])
        self.assertIn("section V.11",p["customer_terms_clause"])
        self.assertIn("customer contract",p["evidence_note"].lower())
        self.assertIn("no numerical",self.doc.lower()) if "no numerical" in self.doc.lower() else self.assertIn("no exact",self.doc.lower())
        self.assertIn("GET, HEAD, HTTP Range",self.doc)
        self.assertIn("2026-11-10",self.doc)
        self.assertIn("Monthly Recurrence",self.doc)

    def test_cannot_flip_one_flag_to_authorize_probing(self):
        p=deepcopy(self.policy)
        p["live_provider_probe_approved"]=True
        self.assertFalse(is_live_probe_authorized(p,self.contract))
        p["public_anonymous_download_permission"]="reviewed_allowed"
        self.assertFalse(is_live_probe_authorized(p,self.contract))
        p["approved_network_requests"]=1
        p["approved_original_download_bytes"]=65536
        p["anonymous_http_rate_cap"]=1
        self.assertFalse(is_live_probe_authorized(p,self.contract))
        p["fixed_tile_url"]="https://attacker.example/fake-v1_5.tif"
        self.assertFalse(is_live_probe_authorized(p,self.contract))

    def test_science_and_raw_storage_remain_separately_unapproved(self):
        p=self.policy
        for key in ("original_provider_bytes_acquired",
                    "original_tiff_values_acquired",
                    "full_source_sha_verified",
                    "post_2026_11_10_pixel_correction_verified",
                    "monthly_recurrence_science_validated",
                    "insurer_model_input_approved"):
            with self.subTest(key=key):
                self.assertIs(p[key],False)
        self.assertIn("no provider original bytes acquired",self.doc.lower())

    def test_no_original_provider_requests_are_made_in_this_gate(self):
        source=POLICY.read_text(encoding="utf-8") + self.doc
        for forbidden in ("urllib.request.urlopen(","requests.get(",
                          "boto3.client(","http.client.HTTPSConnection(",
                          "curl --location", "wget -r"):
            self.assertNotIn(forbidden,source)


if __name__=="__main__":
    unittest.main()
