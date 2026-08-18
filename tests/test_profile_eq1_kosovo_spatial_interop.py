# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import inspect
import json
import math
import unittest
from unittest import mock

from scripts import profile_eq1_kosovo_spatial_interop as interop


class TestCoordinateAssociation(unittest.TestCase):
    def test_identical_points_pass_all_thresholds(self) -> None:
        result = interop._profile_verified_coordinate_sets(
            [(20.0, 42.0), (21.0, 42.5)],
            [(20.0, 42.0), (21.0, 42.5)],
        )

        self.assertEqual(result["exposure_record_count"], 2)
        self.assertEqual(result["distinct_exposure_location_count"], 2)
        self.assertEqual(result["site_record_count"], 2)
        self.assertEqual(result["nearest_site_distance_km"]["maximum"], "0")
        self.assertTrue(result["default_distance_association"]["all_exposure_records_associated"])
        self.assertEqual(result["default_distance_association"]["discarded_exposure_record_count"], 0)

    def test_thresholds_are_monotonic(self) -> None:
        result = interop._profile_verified_coordinate_sets(
            [(20.0, 42.0), (20.08, 42.0), (20.30, 42.0)],
            [(20.0, 42.0)],
        )
        counts = [
            row["associated_exposure_record_count"]
            for row in result["threshold_diagnostics"]
        ]
        self.assertEqual(counts, sorted(counts))
        self.assertEqual(result["default_distance_association"]["threshold_km"], "15")
        self.assertGreater(
            result["default_distance_association"]["associated_exposure_record_count"],
            0,
        )

    def test_duplicate_exposure_locations_are_counted_without_raw_output(self) -> None:
        result = interop._profile_verified_coordinate_sets(
            [(20.0, 42.0), (20.0, 42.0), (20.1, 42.0)],
            [(20.0, 42.0)],
        )
        self.assertEqual(result["exposure_record_count"], 3)
        self.assertEqual(result["distinct_exposure_location_count"], 2)
        self.assertFalse(result["raw_coordinates_returned"])

    def test_rejects_empty_coordinate_sets(self) -> None:
        with self.assertRaisesRegex(interop.SpatialInteropProfileError, "exposure coordinate count"):
            interop._profile_verified_coordinate_sets([], [(20.0, 42.0)])
        with self.assertRaisesRegex(interop.SpatialInteropProfileError, "site coordinate count"):
            interop._profile_verified_coordinate_sets([(20.0, 42.0)], [])

    def test_rejects_out_of_range_coordinates(self) -> None:
        with self.assertRaisesRegex(interop.SpatialInteropProfileError, "exposure coordinate"):
            interop._profile_verified_coordinate_sets([(181.0, 42.0)], [(20.0, 42.0)])
        with self.assertRaisesRegex(interop.SpatialInteropProfileError, "site coordinate"):
            interop._profile_verified_coordinate_sets([(20.0, 42.0)], [(20.0, -91.0)])

    def test_cartesian_distance_matches_spherical_chord(self) -> None:
        left = interop._cartesian(20.0, 42.0)
        right = interop._cartesian(20.1, 42.0)
        observed = interop._chord_distance_km(left, right)
        central_angle = math.acos(
            math.sin(math.radians(42.0)) ** 2
            + math.cos(math.radians(42.0)) ** 2 * math.cos(math.radians(0.1))
        )
        expected = 2 * interop.OPENQUAKE_EARTH_RADIUS_KM * math.sin(central_angle / 2)
        self.assertAlmostEqual(observed, expected, places=9)


class TestFullProfileBoundary(unittest.TestCase):
    @mock.patch.object(interop, "_parse_verified_site_coordinates")
    @mock.patch.object(interop, "_parse_verified_exposure_coordinates")
    def test_full_profile_keeps_crs_and_authority_fail_closed(
        self,
        parse_exposure: mock.Mock,
        parse_site: mock.Mock,
    ) -> None:
        parse_exposure.return_value = [(20.0, 42.0), (20.05, 42.0)]
        parse_site.return_value = [(20.0, 42.0)]

        result = interop.profile_verified_kosovo_spatial_interop(b"exposure", b"site")

        parse_exposure.assert_called_once_with(b"exposure")
        parse_site.assert_called_once_with(b"site")
        self.assertTrue(result["reference_runtime_coordinate_role_verified"])
        self.assertFalse(result["source_crs_datum_epsg_verified"])
        self.assertFalse(result["reprojection_performed"])
        self.assertFalse(result["reprojection_authorized"])
        self.assertFalse(result["geographic_cross_source_equivalence_authorized"])
        self.assertFalse(result["raw_provider_coordinates_returned"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertEqual(result["reference_runtime"]["tag"], "v3.14.0")
        self.assertEqual(
            result["reference_runtime"]["commit_sha"],
            "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
        )

    @mock.patch.object(interop, "_parse_verified_site_coordinates")
    @mock.patch.object(interop, "_parse_verified_exposure_coordinates")
    def test_runtime_contract_is_bounded_to_site_model_hazard_mesh(
        self,
        parse_exposure: mock.Mock,
        parse_site: mock.Mock,
    ) -> None:
        parse_exposure.return_value = [(20.0, 42.0)]
        parse_site.return_value = [(20.0, 42.0)]

        result = interop.profile_verified_kosovo_spatial_interop(b"exposure", b"site")
        runtime = result["reference_runtime"]

        self.assertIn("when the supplied site-model mesh is the selected hazard mesh", runtime["association_contract"])
        self.assertIn("explicit sites", runtime["hazard_mesh_precondition"])
        self.assertIn("hazard-curves mesh", runtime["hazard_mesh_precondition"])
        self.assertIn("region_grid_spacing", runtime["hazard_mesh_precondition"])
        self.assertTrue(result["reference_runtime_coordinate_role_verified"])

    @mock.patch.object(interop, "_parse_verified_site_coordinates")
    @mock.patch.object(interop, "_parse_verified_exposure_coordinates")
    def test_serialized_profile_contains_no_coordinate_keys(
        self,
        parse_exposure: mock.Mock,
        parse_site: mock.Mock,
    ) -> None:
        parse_exposure.return_value = [(20.0, 42.0)]
        parse_site.return_value = [(20.0, 42.0)]
        result = interop.profile_verified_kosovo_spatial_interop(b"exposure", b"site")
        serialized = json.dumps(result, sort_keys=True)

        self.assertNotIn('"longitude"', serialized)
        self.assertNotIn('"latitude"', serialized)
        self.assertNotIn('"lon"', serialized)
        self.assertNotIn('"lat"', serialized)

    def test_coordinate_parser_rejects_non_finite_values(self) -> None:
        with self.assertRaisesRegex(interop.SpatialInteropProfileError, "outside geographic bounds"):
            interop._require_coordinate("NaN", role="test", minimum=-180, maximum=180)
        with self.assertRaisesRegex(interop.SpatialInteropProfileError, "outside geographic bounds"):
            interop._require_coordinate("Infinity", role="test", minimum=-180, maximum=180)


class TestDurableAcquisitionAuthority(unittest.TestCase):
    def test_production_entry_point_accepts_no_transport_or_clock_arguments(self) -> None:
        self.assertEqual(
            list(inspect.signature(interop.acquire_and_profile_kosovo_spatial_interop).parameters),
            [],
        )
        with self.assertRaises(TypeError):
            interop.acquire_and_profile_kosovo_spatial_interop(opener=object())
        with self.assertRaises(TypeError):
            interop.acquire_and_profile_kosovo_spatial_interop(monotonic=lambda: 0.0)

    @mock.patch.object(interop, "_acquire_and_profile_kosovo_spatial_interop")
    def test_production_entry_uses_canonical_transport_and_clock(self, acquire: mock.Mock) -> None:
        acquire.return_value = {"profiled": True}

        result = interop.acquire_and_profile_kosovo_spatial_interop()

        self.assertEqual(result, {"profiled": True})
        acquire.assert_called_once_with(
            opener=interop._CANONICAL_OPEN_FIXED,
            monotonic=interop._CANONICAL_MONOTONIC,
        )

    @mock.patch.object(interop, "_acquire_and_profile_kosovo_spatial_interop")
    def test_production_entry_rejects_runtime_rebinding_before_transport(
        self,
        acquire: mock.Mock,
    ) -> None:
        cases = (
            (mock.patch.object(interop, "_open_fixed", object()), "production transport"),
            (mock.patch.object(interop.time, "monotonic", lambda: 0.0), "monotonic clock"),
            (
                mock.patch.object(
                    interop.exposure,
                    "profile_verified_exposure_value_spatial",
                    lambda *_args, **_kwargs: {},
                ),
                "exposure profiler identity",
            ),
            (
                mock.patch.object(
                    interop.site_model,
                    "profile_verified_xml_bytes",
                    lambda *_args, **_kwargs: {},
                ),
                "site profiler identity",
            ),
            (
                mock.patch.object(
                    interop,
                    "profile_verified_kosovo_spatial_interop",
                    lambda *_args, **_kwargs: {},
                ),
                "spatial-interoperability profiler identity",
            ),
            (
                mock.patch.object(interop.exposure, "COMMIT_SHA", "0" * 40),
                "exposure commit",
            ),
            (
                mock.patch.object(interop.site_model, "EXPECTED_SHA256", "0" * 64),
                "site SHA-256",
            ),
        )
        for patcher, message in cases:
            with self.subTest(message=message), patcher:
                with self.assertRaisesRegex(interop.SpatialInteropProfileError, message):
                    interop.acquire_and_profile_kosovo_spatial_interop()
        acquire.assert_not_called()

    @mock.patch.object(interop, "profile_verified_kosovo_spatial_interop")
    @mock.patch.object(interop, "_fetch_exact_bytes")
    def test_private_acquisition_helper_keeps_test_injection_non_authoritative(
        self,
        fetch_exact: mock.Mock,
        profile: mock.Mock,
    ) -> None:
        fetch_exact.side_effect = [b"exposure", b"site"]
        profile.return_value = {"profiled": True}
        opener = object()
        monotonic = mock.Mock(side_effect=[100.0])

        result = interop._acquire_and_profile_kosovo_spatial_interop(
            opener=opener,
            monotonic=monotonic,
        )

        self.assertEqual(result, {"profiled": True})
        self.assertEqual(fetch_exact.call_count, 2)
        for call in fetch_exact.call_args_list:
            self.assertIs(call.kwargs["opener"], opener)
            self.assertIs(call.kwargs["monotonic"], monotonic)
            self.assertEqual(call.kwargs["deadline"], 100.0 + interop.TOTAL_DEADLINE_SECONDS)
        profile.assert_called_once_with(b"exposure", b"site")


if __name__ == "__main__":
    unittest.main()
