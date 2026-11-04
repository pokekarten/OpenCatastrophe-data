# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Deterministic synthetic-only ecCodes four-cell science boundary tests."""

from __future__ import annotations

import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research_runners import noaa_mrms_keller_eccodes_point_v0 as k


def geo() -> dict:
    return {
        "geometry_checked": True,
        "nx": 7000, "ny": 3500,
        "latitude_first_deg": 54.995,
        "longitude_first_east_0_360_deg": 230.005,
        "latitude_increment_deg": 0.01,
        "longitude_increment_deg": 0.01,
        "i_eastward": True,
        "j_northward": False,
    }


def receipt() -> dict:
    return {
        "reference_utc": "2021-04-29T01:36:39+00:00",
        "grid_geography": geo(),
        "compressed_sha256": "f" * 64,
        "gzip_crc32_checked": True,
        "decoded_grib_bytes": 90747,
    }


class FakeEcCodes:
    __version__ = "test-only"

    def __init__(self):
        self.released = False
        self.override = {}
        self.nearest = [
            SimpleNamespace(index=2207 * 7000 + 3270, lat=32.925,
                            lon=262.705, distance=0.73, value=60.0),
            SimpleNamespace(index=2207 * 7000 + 3271, lat=32.925,
                            lon=262.715, distance=0.73, value=65.0),
            SimpleNamespace(index=2208 * 7000 + 3270, lat=32.915,
                            lon=262.705, distance=0.73, value=63.0),
            SimpleNamespace(index=2208 * 7000 + 3271, lat=32.915,
                            lon=262.715, distance=0.73, value=67.0),
        ]

    def codes_new_from_message(self, data: bytes) -> object:
        return object()

    def codes_get(self, handle: object, key: str):
        expected = {
            "discipline": 209, "parameterCategory": 3, "parameterNumber": 28,
            "numberOfPoints": 24500000, "Ni": 7000, "Nj": 3500,
            "scanningMode": 0, "gridType": "regular_ll",
            "missingValue": 9.999e20,
        }
        return self.override.get(key, expected[key])

    def codes_grib_find_nearest(self, handle: object, lat: float, lon: float,
                                is_lsm: bool, npoints: int):
        assert (lat, lon, is_lsm, npoints) == (32.92, -97.29, False, 4)
        return self.nearest

    def codes_release(self, handle: object) -> None:
        self.released = True


def decode(fake: FakeEcCodes, data: dict | None = None):
    with (patch.object(k, "audit_original", return_value=data or receipt()),
          patch.object(k, "inflate_gzip_capped", return_value=b"GRIB-test-only")):
        return k.decode_original_keller(b"synthetic-never-source-bytes", fake)


class KellerEcCodesFourCellTests(unittest.TestCase):
    def test_four_neighbours_are_extracted_as_radar_data_not_ground_truth(self):
        fake = FakeEcCodes()
        result = decode(fake)
        self.assertTrue(fake.released)
        self.assertEqual(result["source_grid_nx"], 7000)
        self.assertEqual(result["independent_reported_hail_diameter_mm"], 63.5)
        self.assertEqual(result["valid_neighbour_count"], 4)
        self.assertEqual(result["decoded_local_min_radar_mesh_mm"], 60.0)
        self.assertEqual(result["decoded_local_max_radar_mesh_mm"], 67.0)
        self.assertEqual(
            set(r["decoded_radar_mesh_mm"] for r in result["four_nearest_radar_cells"]),
            {60.0, 63.0, 65.0, 67.0},
        )
        self.assertTrue(result["report_point_has_four_near_equal_neighbours"])
        self.assertFalse(result["physical_model_skill_established"])
        self.assertFalse(result["source_or_model_admitted"])
        self.assertFalse(result["annual_hail_frequency_estimated"])
        self.assertFalse(result["insured_losses_or_tiv_inferred"])
        self.assertFalse(result["original_source_bytes_committed_or_uploaded"])

    def test_missing_radar_neighbours_not_converted_to_zero(self):
        fake = FakeEcCodes()
        fake.nearest[0].value = 9.999e20
        result = decode(fake)
        self.assertEqual(result["missing_neighbour_count"], 1)
        self.assertIsNone(result["four_nearest_radar_cells"][0]["decoded_radar_mesh_mm"])
        self.assertEqual(result["decoded_local_min_radar_mesh_mm"], 63.0)
        self.assertEqual(result["decoded_local_max_radar_mesh_mm"], 67.0)

    def test_missing_all_radar_values_does_not_fake_no_hail(self):
        fake = FakeEcCodes()
        for point in fake.nearest:
            point.value = 9.999e20
        result = decode(fake)
        self.assertEqual(result["valid_neighbour_count"], 0)
        self.assertIsNone(result["decoded_local_min_radar_mesh_mm"])
        self.assertIsNone(result["decoded_local_max_radar_mesh_mm"])

    def test_wrong_parameter_and_grid_are_blocked_even_if_source_hash_valid(self):
        for key, value in (("parameterNumber", 29), ("gridType", "rotated_ll"),
                           ("Ni", 3500), ("numberOfPoints", 9999),
                           ("scanningMode", 0x40)):
            with self.subTest(key=key):
                fake = FakeEcCodes()
                fake.override[key] = value
                with self.assertRaisesRegex(k.PointDecodeError, "definition drift"):
                    decode(fake)
                self.assertTrue(fake.released)

    def test_position_and_duplicate_index_disagreements_blocked(self):
        for variant in ("out_of_neighbourhood", "duplicate", "distance", "coordinate"):
            with self.subTest(variant=variant):
                fake = FakeEcCodes()
                if variant == "out_of_neighbourhood":
                    fake.nearest[1].index += 3500
                elif variant == "duplicate":
                    fake.nearest[1].index = fake.nearest[0].index
                elif variant == "distance":
                    fake.nearest[1].distance = 100.0
                else:
                    fake.nearest[1].lat = 30.0
                with self.assertRaises(k.PointDecodeError):
                    decode(fake)

    def test_out_of_range_value_rejected_not_labeled_intensity(self):
        fake = FakeEcCodes()
        fake.nearest[1].value = -1
        with self.assertRaisesRegex(k.PointDecodeError, "unphysical"):
            decode(fake)
        fake = FakeEcCodes()
        fake.nearest[1].value = 1001
        with self.assertRaisesRegex(k.PointDecodeError, "unphysical"):
            decode(fake)

    def test_source_timestamp_or_grid_is_not_trusted_from_comments(self):
        fake = FakeEcCodes()
        wrong = receipt()
        wrong["reference_utc"] = "2021-04-29T02:00:00+00:00"
        with self.assertRaisesRegex(k.PointDecodeError, "UTC"):
            decode(fake, wrong)
        wrong = receipt()
        wrong["grid_geography"] = {"geometry_checked": False}
        with self.assertRaises(k.PointDecodeError):
            decode(FakeEcCodes(), wrong)

    def test_rounded_report_is_four_cell_corner_not_unique_nearest(self):
        ids = k._expected_four_indices(geo())
        self.assertEqual(
            ids, {row * 7000 + col
                  for row in (2207, 2208) for col in (3270, 3271)}
        )


if __name__ == "__main__":
    unittest.main()
