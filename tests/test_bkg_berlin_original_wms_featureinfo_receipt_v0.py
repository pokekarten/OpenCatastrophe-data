# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict offline checks for the original BKG Berlin WMS no-unit receipt."""
from __future__ import annotations

from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = (ROOT / "docs/research" /
        "bkg-berlin-original-wms-featureinfo-receipt-20261101.toml")
ORIGINAL_INFO_SHA = "6f6429b2def52bb12f9bdcd5f8092e88761e6d38e50023222bd26761c4a4f038"
ORIGINAL_CAP_SHA = "1f5050be9a560c4a2e2bce3f5e17c74ed4ff8973c62e63b975da5c5e5d07f75f"
BKG_ORIGINAL_TIFF_SHA = "7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f"


def check_original_receipt(d):
    if not isinstance(d, dict):
        raise ValueError("unreviewed original source receipt")
    expected = {
        "receipt_schema": "bkg-berlin-official-wms-kostra-actual-original-featureinfo-v0",
        "research_only": True,
        "source_url": "https://sgx.geodatenzentrum.de/wms_starkregen",
        "source_wms_layer": "be_tiefe_agw",
        "source_wms_version": "1.3.0",
        "source_query_crs": "EPSG:25832",
        "original_github_actions_run_id": 41354445114,
        "original_github_actions_url": "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41354445114",
        "original_main_commit": "a1a342ac8e41e9129928674d5c5e81cb7e5820ca",
        "original_capabilities_sha256_only": ORIGINAL_CAP_SHA,
        "original_capabilities_bytes": 480596,
        "original_featureinfo_response_sha256_only": ORIGINAL_INFO_SHA,
        "original_featureinfo_response_bytes": 205,
        "actual_original_layer_found": True,
        "actual_original_layer_queryable": True,
        "actual_original_featureinfo_format": "application/json",
        "feature_info_explicit_physical_unit_label_candidate_found": False,
        "provider_wms_explicit_units_or_scaling_proven": False,
        "wms_and_original_tiff_same_numeric_encoding_proven": False,
        "original_download_tiff_full_sha256_independent": BKG_ORIGINAL_TIFF_SHA,
        "original_download_tiff_physical_depth_unit_proven": False,
        "original_wms_payload_saved": False,
        "per_building_risk_or_raw_source_values_saved": False,
        "unscaled_pixel_value_converted_to_depth": False,
        "source_rights_full_publication_review_complete": False,
        "insurance_cat_model_input_admitted": False,
    }
    for key, canonical in expected.items():
        if type(d.get(key)) is not type(canonical) or d[key] != canonical:
            raise ValueError("original source WMS receipt altered: " + key)
    for key in ("original_capabilities_sha256_only",
                "original_featureinfo_response_sha256_only",
                "original_download_tiff_full_sha256_independent"):
        if not re.fullmatch(r"[0-9a-f]{64}", d[key]):
            raise ValueError("unreviewed original source SHA")
    return {
        "source_WMS_capabilities_and_featureinfo_verified": True,
        "explicit_WMS_physical_unit_found": False,
        "WMS_to_original_TIFF_depth_scale_proven": False,
        "original_BKG_Int16_water_depth_conversion_allowed": False,
        "insurer_loss_or_CAT_model_admitted": False,
        "evidence_run_id": 41354445114,
    }


class OriginalBkgBerlinWmsReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = tomllib.loads(FILE.read_text(encoding="utf-8"))

    def test_actual_source_exposure_read_only(self):
        output = check_original_receipt(self.source)
        self.assertTrue(output["source_WMS_capabilities_and_featureinfo_verified"])
        self.assertFalse(output["original_BKG_Int16_water_depth_conversion_allowed"])
        self.assertFalse(output["insurer_loss_or_CAT_model_admitted"])

    def test_original_independent_wms_and_tiff_hashes_not_confused(self):
        self.assertEqual(self.source["original_capabilities_sha256_only"], ORIGINAL_CAP_SHA)
        self.assertEqual(self.source["original_featureinfo_response_sha256_only"],
                         ORIGINAL_INFO_SHA)
        self.assertEqual(self.source["original_download_tiff_full_sha256_independent"],
                         BKG_ORIGINAL_TIFF_SHA)
        self.assertNotEqual(ORIGINAL_CAP_SHA, BKG_ORIGINAL_TIFF_SHA)
        self.assertNotEqual(ORIGINAL_INFO_SHA, BKG_ORIGINAL_TIFF_SHA)

    def test_fabricated_unit_layer_or_map_same_encoding_never_admitted(self):
        import copy
        for field, value in (
            ("feature_info_explicit_physical_unit_label_candidate_found", True),
            ("wms_and_original_tiff_same_numeric_encoding_proven", True),
            ("source_wms_layer", "be_tiefe_extrem"),
            ("original_download_tiff_physical_depth_unit_proven", True),
            ("insurance_cat_model_input_admitted", True),
            ("source_rights_full_publication_review_complete", True),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.source)
                changed[field] = value
                with self.assertRaises(ValueError):
                    check_original_receipt(changed)

    def test_modified_original_sha_and_byte_counts_fail_closed(self):
        import copy
        for field, value in (
            ("original_capabilities_sha256_only", "0"*64),
            ("original_featureinfo_response_sha256_only", "0"*64),
            ("original_featureinfo_response_bytes", 204),
            ("original_capabilities_bytes", 0),
            ("original_main_commit", "a"*40),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.source)
                changed[field] = value
                with self.assertRaises(ValueError):
                    check_original_receipt(changed)

    def test_missing_layer_or_run_and_duplicate_metadata_fail_closed(self):
        d = dict(self.source)
        del d["actual_original_layer_queryable"]
        with self.assertRaises(ValueError):
            check_original_receipt(d)
        with self.assertRaises(tomllib.TOMLDecodeError):
            tomllib.loads('actual_original_layer_found=true\nactual_original_layer_found=false')


if __name__ == "__main__":
    unittest.main()
