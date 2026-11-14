# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only offline safety and science tests for NSI 2026 fields."""
from __future__ import annotations

import json
import unittest

from scripts.audit_usace_nsi_2026_sample_v0 import (
    MAX_BYTES,
    MAX_FEATURES,
    NSI2026SampleBlocked,
    inspect_nsi_2026_geojson,
)


def feature(fd_id=1, *, x=-80., y=30., footprint="shared", fullrep=120., val_struct=90.):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [x, y]},
        "properties": {"fd_id": fd_id, "x": x, "y": y,
                       "ftprntid": footprint, "fullrep": fullrep,
                       "val_struct": val_struct, "cbfips": "012345678901234"},
    }


def raw(*features):
    return json.dumps({"type": "FeatureCollection", "features": list(features)}).encode()


class NSI2026ScientificScreenTests(unittest.TestCase):
    def test_distinct_stacked_structures_are_retained(self):
        result = inspect_nsi_2026_geojson(raw(feature(1), feature(2)))
        self.assertEqual(result["feature_count"], 2)
        self.assertEqual(result["shared_footprint_extra_records"], 1)
        self.assertEqual(result["unique_fd_id_count"], 2)
        self.assertFalse(result["legal_or_model_admission_verified"])
        self.assertFalse(result["source_native_original_receipt_verified"])
        self.assertEqual(len(result["input_byte_sha256"]), 64)
        self.assertNotIn("012345678901234", json.dumps(result))

    def test_duplicates_by_fd_id_not_footprint(self):
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(raw(feature(1), feature(1)))

    def test_coordinates_must_match_wgs84_properties(self):
        obj = feature()
        obj["geometry"]["coordinates"][0] = -81.
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(raw(obj))
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(raw(feature(x=195.)))

    def test_missing_valuations_remain_missing_not_zero(self):
        result = inspect_nsi_2026_geojson(raw(feature(fullrep=None, val_struct=None)))
        self.assertEqual(result["missing_fullrep_count"], 1)
        self.assertEqual(result["missing_val_struct_count"], 1)

    def test_conflicting_depreciated_value_is_flagged_not_rewritten(self):
        result = inspect_nsi_2026_geojson(raw(feature(fullrep=90., val_struct=120.)))
        self.assertEqual(result["val_struct_exceeds_fullrep_count"], 1)
        self.assertIn("not insured TIV", result["valuation_caution"])

    def test_invalid_values_rejected(self):
        for kwargs in ({"fullrep": -1.}, {"val_struct": -2.}, {"fullrep": "12"}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(NSI2026SampleBlocked):
                    inspect_nsi_2026_geojson(raw(feature(**kwargs)))

    def test_malformed_point_and_id_rejected(self):
        obj = feature()
        obj["geometry"]["type"] = "Polygon"
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(raw(obj))
        for invalid in (True, -1, "1"):
            with self.subTest(fd_id=invalid):
                with self.assertRaises(NSI2026SampleBlocked):
                    inspect_nsi_2026_geojson(raw(feature(fd_id=invalid)))

    def test_duplicate_json_keys_nonfinite_and_html_rejected(self):
        for original in (b'{"type":"FeatureCollection","type":"FeatureCollection","features":[]}',
                         b'{"features":NaN}', b'<html>not JSON</html>', b'\xff\xfe'):
            with self.subTest(raw=original[:20]):
                with self.assertRaises(NSI2026SampleBlocked):
                    inspect_nsi_2026_geojson(original)

    def test_reject_float_exponent_overflow_in_ignored_fields(self):
        base = raw(feature())
        tampered = base[:-1] + b',"supposedly_ignored":1e999}'
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(tampered)
        tampered2 = base.replace(b'"fullrep": 120.0', b'"fullrep": 1e999')
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(tampered2)

    def test_empty_too_many_and_oversize_rejected(self):
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(raw())
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(raw(*[feature(i) for i in range(MAX_FEATURES + 1)]))
        with self.assertRaises(NSI2026SampleBlocked):
            inspect_nsi_2026_geojson(b' ' * (MAX_BYTES + 1))

    def test_never_leaks_source_specific_fields(self):
        obj = feature()
        obj["properties"]["private_vendor_token"] = "synthetic-test-secret"
        result = inspect_nsi_2026_geojson(raw(obj))
        self.assertNotIn("synthetic-test-secret", json.dumps(result))
        self.assertFalse(result["provider_network_request_performed"])
        self.assertFalse(result["provider_bytes_persisted"])


if __name__ == "__main__":
    unittest.main()
