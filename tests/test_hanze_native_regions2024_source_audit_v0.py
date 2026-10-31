# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic checks of native HANZE region glossary; original bytes never committed."""
from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from research_runners import hanze_native_regions2024_source_audit_v0 as target
from research_runners.historical_cat_benchmark_csv_preflight_v0 import HANZE_COLUMNS
from research_runners.dfo_floodrecords_csv_preflight_v0 import HEADER as DFO_HEADER
from research_runners.flood_event_link_candidates_v0 import link_candidates
from tests.test_flood_event_link_candidates_v0 import (
    csv_blob, dfo_row, hanze_row, crosswalk, sha,
)


def glossary_blob():
    codes = [f"AA{i:03d}" for i in range(999)] + ["DE111", "DE112"]
    return csv_blob(("Code", "Name"),
                    [{"Code": code, "Name": "Synthetic name"} for code in codes])


def fixture(**overrides):
    dfo = csv_blob(DFO_HEADER, [dfo_row()])
    han = csv_blob(HANZE_COLUMNS, [hanze_row(**{
        "admin_unit_nomenclature": "NUTS",
        "admin_unit_level": "3", "admin_unit_year": "2024",
        "admin_unit_code": "DE111; DE112", **overrides,
    })])
    m = crosswalk()
    overlap = link_candidates(dfo, sha(dfo), han, sha(han), m, sha(m))
    return han, overlap


def verify_with_synthetic_glossary(han, overlap, glossary=None):
    glossary = glossary if glossary is not None else glossary_blob()
    with patch.object(target, "PUBLISHER_BYTES", len(glossary)), \
         patch.object(target, "PUBLISHER_MD5", hashlib.md5(glossary, usedforsecurity=False).hexdigest()):
        return target.audit_hanze_s2_candidate_codes(
            han, sha(han), overlap, glossary, expected_s2_sha256=sha(glossary))


class HANZENativeRegionGlossaryTests(unittest.TestCase):
    def test_delimited_multi_region_list_is_not_flood_footprint(self):
        h, o = fixture()
        receipt = verify_with_synthetic_glossary(h, o)
        self.assertEqual(receipt["candidate_pair_count"], 1)
        self.assertEqual(receipt["status_counts"]["exact_multi_region_glossary_matched"], 1)
        self.assertEqual(receipt["region_tokens_from_accepted_lists"], 2)
        self.assertTrue(receipt["reference_admin_region_is_not_actual_inundation"])
        for key in ("gis_geometry_loaded", "source_event_identity_proven",
                    "original_raw_event_or_glossary_rows_exported",
                    "insurer_tiv_or_loss_created", "model_input_admitted",
                    "source_rights_and_geodata_sublicenses_reviewed"):
            self.assertFalse(receipt[key])
        self.assertNotIn("DE111", str(receipt))

    def test_single_exact_and_missing_or_unparseable_lists(self):
        for code, expected in [
            ("DE111", "exact_one_region_glossary_matched"),
            ("", "missing_raw_region_code"),
            ("DE111;DE111", "noncanonical_or_unsupported_region_list"),
            ("DE111;garbage", "noncanonical_or_unsupported_region_list"),
            ("DE111, DE112", "exact_multi_region_glossary_matched"),
            ("DE111|DE112", "exact_multi_region_glossary_matched"),
            ("DE111 DE112", "noncanonical_or_unsupported_region_list"),
            ("DE999", "missing_glossary_tokens"),
            ("FR111;DE112", "country_inconsistent_region_list"),
        ]:
            with self.subTest(code=code):
                h, o = fixture(admin_unit_code=code)
                result = verify_with_synthetic_glossary(h, o)
                self.assertEqual(result["status_counts"][expected], 1)

    def test_source_checksum_and_csv_header_fail_closed(self):
        b = glossary_blob()
        with patch.object(target, "PUBLISHER_BYTES", len(b)), \
             patch.object(target, "PUBLISHER_MD5", hashlib.md5(b, usedforsecurity=False).hexdigest()):
            codes, r = target.read_hanze_original_regions(b, expected_sha256=sha(b))
            self.assertEqual(len(codes), 1001)
            self.assertEqual(r["distinct_region_country_prefixes"], 2)
            self.assertFalse(r["model_input_admitted"])
            with self.assertRaisesRegex(target.HANZERegionGlossaryError, "SHA256"):
                target.read_hanze_original_regions(b, expected_sha256="0"*64)
        with self.assertRaisesRegex(target.HANZERegionGlossaryError, "byte length"):
            target.read_hanze_original_regions(b"bad csv")

    def test_duplicate_code_and_missing_glossary_fields_rejected(self):
        b = csv_blob(("Code", "Name"), [{"Code": "DE111", "Name": "One"},
                                           {"Code": "DE111", "Name": "Two"}])
        with patch.object(target, "PUBLISHER_BYTES", len(b)), \
             patch.object(target, "PUBLISHER_MD5", hashlib.md5(b, usedforsecurity=False).hexdigest()):
            with self.assertRaisesRegex(target.HANZERegionGlossaryError, "duplicate"):
                target.read_hanze_original_regions(b)

    def test_invalid_hanze_source_identity_or_fabricated_event_fails(self):
        h, o = fixture()
        o["common_event_identity_proven"] = True
        with self.assertRaisesRegex(target.HANZERegionGlossaryError, "invalid upstream"):
            verify_with_synthetic_glossary(h, o)
        h, o = fixture()
        o["candidate_pairs"][0]["hanze_event_id"] = "nonexistent"
        with self.assertRaisesRegex(target.HANZERegionGlossaryError, "missing"):
            verify_with_synthetic_glossary(h, o)

    def test_pinned_original_s2_glossary_receipt_no_false_loss_or_geometry(self):
        from research_runners.hanze_native_regions2024_source_receipt_v0 import HANZE_S2_V2024_RECEIPT
        from research_runners.hanze_native_regions2024_original_receipt_v0 import (
            PINNED_S2_SHA256, PINNED_S2_REGION_COUNT,
            PINNED_S2_COUNTRY_COUNT, PINNED_REGION_LIST_TOKENS,
        )
        r = HANZE_S2_V2024_RECEIPT
        self.assertEqual(r["observed_sha256"], PINNED_S2_SHA256)
        self.assertEqual(r["region_codes"], PINNED_S2_REGION_COUNT)
        self.assertEqual(r["country_prefixes"], PINNED_S2_COUNTRY_COUNT)
        self.assertEqual(r["total_region_tokens_in_9_compound_lists"], PINNED_REGION_LIST_TOKENS)
        self.assertEqual(r["all_token_sequences_exact_in_native_glossary"], 9)
        self.assertIsNone(r["unique_regions_or_flood_extent_count"])
        for key in ("underlying_geodata_sublicense_review_completed",
                    "source_events_confirmed_equivalent",
                    "administrative_region_is_an_observed_flood_footprint",
                    "source_rows_or_names_reproduced",
                    "insured_loss_or_exposure_created", "model_source_admitted"):
            self.assertFalse(r[key])

    def test_no_candidates_cannot_imply_zero_flood_exposure(self):
        h, o = fixture()
        o["candidate_pairs"] = []
        o["candidate_pair_count"] = 0
        result = verify_with_synthetic_glossary(h, o)
        self.assertEqual(sum(result["status_counts"].values()), 0)
        self.assertFalse(result["source_event_identity_proven"])


if __name__ == "__main__":
    unittest.main()
