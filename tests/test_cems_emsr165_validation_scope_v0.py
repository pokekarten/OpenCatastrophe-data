# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests using solely synthetic CEMS-like metadata, no network."""
import unittest

from research_runners.cems_emsr165_validation_scope_v0 import ReviewBlocked, preflight


def synthetic_summary():
    return {
        "code": "EMSR165", "category": {"slug": "flood"},
        "countries": [{"short_name": "France"}],
        "n_aois": 8, "n_products": 21,
        "activationTime": "2016-06-01T18:45:00Z",
        "lastUpdate": "2016-06-10T02:59:00Z",
    }


def synthetic_product():
    return {
        "activation_code": "EMSR165", "aoi_id": "AOI01",
        "aoi_bbox_wgs84": [2.2, 48.7, 2.6, 48.9],
        "product_type": "DEL",
        "image_acquired_utc": "2016-06-03T12:00:00Z",
        "product_delivered_utc": "2016-06-04T18:00:00Z",
        "product_version": 1, "original_vector_sha256": None,
        "original_vector_bytes": None,
    }


def envelope(product=None):
    return {"activation": synthetic_summary(), "selected_product": product}


class EMSR165ScienceGates(unittest.TestCase):
    def test_activation_is_only_a_candidate(self):
        r = preflight(envelope())
        self.assertTrue(r["activation_metadata_shape_valid"])
        self.assertFalse(r["provider_product_url_or_bytes_acquired"])
        self.assertFalse(r["model_input_admitted"])
        self.assertIsNone(r["aoi_bbox_covers_paris_station"])

    def test_even_perfect_synthetic_product_does_not_gain_rights_or_truth(self):
        r = preflight(envelope(synthetic_product()))
        self.assertTrue(r["aoi_bbox_covers_paris_station"])
        self.assertTrue(r["image_utc_date_equals_paris_daily_peak_date"])
        self.assertTrue(r["product_metadata_shape_valid"])
        self.assertTrue(r["product_type_suitable_for_extent_comparison"])
        self.assertFalse(r["asset_original_bytes_authenticated"])
        self.assertFalse(r["model_input_admitted"])
        self.assertFalse(r["insured_loss_inference_allowed"])

    def test_AOI_outside_paris_does_not_inherit_same_flood_event_match(self):
        prod = synthetic_product()
        prod["aoi_bbox_wgs84"] = [2.2, 47.9, 2.7, 48.2]
        r = preflight(envelope(prod))
        self.assertFalse(r["aoi_bbox_covers_paris_station"])
        self.assertIn("candidate_AOI_does_not_contain_paris_station", r["blockers"])

    def test_grading_is_not_extent_and_not_insured_loss(self):
        prod = synthetic_product()
        prod["product_type"] = "GRA"
        r = preflight(envelope(prod))
        self.assertFalse(r["product_type_suitable_for_extent_comparison"])
        self.assertFalse(r["insured_loss_inference_allowed"])
        self.assertIn("not_an_extent_delineation_product", r["blockers"])

    def test_delivery_is_not_sensor_acquisition_time(self):
        prod = synthetic_product()
        prod["image_acquired_utc"] = "2016-06-02T12:00:00Z"
        prod["product_delivered_utc"] = "2016-06-03T18:00:00Z"
        r = preflight(envelope(prod))
        self.assertFalse(r["image_utc_date_equals_paris_daily_peak_date"])

    def test_later_product_cannot_precede_imagery(self):
        prod = synthetic_product()
        prod["product_delivered_utc"] = "2016-06-02T11:00:00Z"
        with self.assertRaises(ReviewBlocked):
            preflight(envelope(prod))

    def test_unchanged_product_hash_shape_not_authenticated(self):
        prod = synthetic_product()
        prod["original_vector_sha256"] = "a" * 64
        prod["original_vector_bytes"] = 512
        r = preflight(envelope(prod))
        self.assertTrue(r["reported_original_sha256_format_valid"])
        self.assertFalse(r["asset_original_bytes_authenticated"])

    def test_partial_or_malformed_hash_blocks(self):
        for sha, size in (("a" * 64, None), (None, 3), ("not-sha", 3),
                          ("A" * 64, 3), ("a" * 64, True)):
            with self.subTest(sha=sha, size=size):
                prod = synthetic_product()
                prod["original_vector_sha256"] = sha
                prod["original_vector_bytes"] = size
                with self.assertRaises(ReviewBlocked):
                    preflight(envelope(prod))

    def test_wrong_activation_and_counts_fail_closed(self):
        for key, value in (("code", "EMSN028"), ("n_aois", 4),
                           ("n_products", 8), ("n_aois", True)):
            with self.subTest(key=key, value=value):
                env = envelope()
                env["activation"][key] = value
                with self.assertRaises(ReviewBlocked):
                    preflight(env)

    def test_bad_coordinate_and_cross_event(self):
        for bbox in ([2.5, 48.7, 2.1, 48.9], [181, 48, 182, 49],
                     [2.2, 48.7, True, 48.9],
                     [2.2, float("nan"), 2.6, 48.9]):
            with self.subTest(bbox=bbox):
                prod = synthetic_product()
                prod["aoi_bbox_wgs84"] = bbox
                with self.assertRaises(ReviewBlocked):
                    preflight(envelope(prod))

    def test_bad_time_format_and_source_product(self):
        prod = synthetic_product()
        prod["image_acquired_utc"] = "2016-06-03"
        with self.assertRaises(ReviewBlocked):
            preflight(envelope(prod))
        prod = synthetic_product()
        prod["activation_code"] = "EMSR166"
        with self.assertRaises(ReviewBlocked):
            preflight(envelope(prod))

    def test_huge_json_integer_coordinate_blocks_instead_of_crashing(self):
        prod = synthetic_product()
        prod["aoi_bbox_wgs84"] = [2.2, 48.7, 10 ** 3000, 48.9]
        with self.assertRaises(ReviewBlocked):
            preflight(envelope(prod))

    def test_unhashable_or_nonstr_product_class_is_rejected(self):
        for value in (["DEL"], {"type": "DEL"}, None, 4):
            with self.subTest(value=value):
                prod = synthetic_product()
                prod["product_type"] = value
                with self.assertRaises(ReviewBlocked):
                    preflight(envelope(prod))

    def test_injected_approval_field_forbidden(self):
        prod = synthetic_product()
        prod["model_ready"] = True
        with self.assertRaises(ReviewBlocked):
            preflight(envelope(prod))


if __name__ == "__main__":
    unittest.main()
