# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from pathlib import Path

from scripts.dresden_acquisition_intent import (
    GLOFAS_MANIFEST,
    GLOFAS_REVIEW,
    PEGELONLINE_MANIFEST,
    PEGELONLINE_REVIEW,
    PEGELONLINE_STATION_NUMBER,
    PEGELONLINE_STATION_UUID,
    AcquisitionIntentError,
    acquisition_intent,
    acquisition_intent_sha256,
    canonical_intent_bytes,
    finalize_acquisition_intent,
)
from scripts.hydrology_grid_matching import DRESDEN_DRAINAGE_AREA_KM2, GlofasGridCell

ROOT = Path(__file__).resolve().parents[1]


class AcquisitionIntentTests(unittest.TestCase):
    def test_repository_bindings_exist(self) -> None:
        for relative in (
            PEGELONLINE_MANIFEST,
            PEGELONLINE_REVIEW,
            GLOFAS_MANIFEST,
            GLOFAS_REVIEW,
        ):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_pre_target_intent_freezes_known_scope_but_not_metadata_results(self) -> None:
        intent = acquisition_intent()
        self.assertEqual(intent["profile_version"], "1.0.0")
        self.assertEqual(intent["phase"], "metadata_resolution")
        self.assertTrue(intent["target_values_must_not_be_inspected"])
        self.assertEqual(intent["pegelonline"]["station_number"], "501060")
        self.assertEqual(
            intent["pegelonline"]["station_uuid"],
            "70272185-b2b3-4178-96b8-43bea330dcae",
        )
        self.assertEqual(intent["pegelonline"]["variable"], "Q")
        self.assertEqual(
            intent["pegelonline"]["required_local_coverage_start"],
            "2020-01-01T01:00:00+01:00",
        )
        self.assertEqual(
            intent["pegelonline"]["required_local_coverage_end_exclusive"],
            "2024-01-01T01:00:00+01:00",
        )
        self.assertEqual(intent["pegelonline"]["sampling_interval"]["status"], "unresolved")
        self.assertEqual(
            intent["pegelonline"]["sampling_interval"]["must_freeze_from"],
            "retrieved_series_metadata.equidistance_minutes",
        )
        self.assertEqual(intent["glofas"]["system_version"], "version_4_0")
        self.assertEqual(intent["glofas"]["hydrological_model"], "lisflood")
        self.assertEqual(intent["glofas"]["product_type"], "consolidated")
        self.assertEqual(
            intent["glofas"]["variable"],
            "river_discharge_in_the_last_24_hours",
        )
        self.assertEqual(intent["glofas"]["expected_daily_labels"], 1461)
        self.assertEqual(intent["glofas"]["first_end_label_utc"], "2020-01-02T00:00:00+00:00")
        self.assertEqual(intent["glofas"]["last_end_label_utc"], "2024-01-01T00:00:00+00:00")
        self.assertEqual(intent["glofas"]["grid_cell"]["status"], "unresolved")

    def test_canonical_bytes_and_hash_are_deterministic(self) -> None:
        first = acquisition_intent()
        second = acquisition_intent()
        self.assertEqual(canonical_intent_bytes(first), canonical_intent_bytes(second))
        self.assertEqual(acquisition_intent_sha256(first), acquisition_intent_sha256(second))
        self.assertEqual(len(acquisition_intent_sha256(first)), 64)
        self.assertTrue(canonical_intent_bytes(first).startswith(b'{"glofas":'))

    def test_finalization_accepts_source_equidistance_minutes_and_freezes_sampling(self) -> None:
        candidates = [
            GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2 * 1.02),
            GlofasGridCell(51.10, 13.74, DRESDEN_DRAINAGE_AREA_KM2 * 1.01),
        ]
        plan = finalize_acquisition_intent(
            pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
            pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
            pegelonline_equidistance_minutes=15,
            station_latitude=51.05,
            station_longitude=13.74,
            glofas_candidate_cells=candidates,
        )
        self.assertEqual(plan["phase"], "target_acquisition")
        self.assertFalse(plan["target_values_must_not_be_inspected"])
        self.assertEqual(plan["pegelonline"]["sampling_interval"]["equidistance_minutes"], 15)
        self.assertEqual(plan["pegelonline"]["sampling_interval"]["seconds"], 900)
        self.assertEqual(plan["metadata_resolution"]["pegelonline_station_number"], PEGELONLINE_STATION_NUMBER)
        self.assertEqual(plan["metadata_resolution"]["pegelonline_station_uuid"], PEGELONLINE_STATION_UUID)
        self.assertEqual(plan["metadata_resolution"]["pegelonline_equidistance_minutes"], 15)
        self.assertEqual(plan["metadata_resolution"]["pegelonline_sampling_interval_seconds"], 900)
        self.assertEqual(
            plan["pegelonline"]["sampling_interval"]["expected_observations_per_24h"],
            96,
        )
        self.assertEqual(plan["glofas"]["grid_cell"]["latitude"], 51.10)
        self.assertAlmostEqual(
            plan["metadata_resolution"]["glofas_grid_match"]["relative_drainage_area_mismatch"],
            0.01,
        )
        self.assertEqual(
            plan["metadata_resolution"]["station_coordinate_wgs84"],
            {"latitude": 51.05, "longitude": 13.74},
        )

    def test_finalization_is_independent_of_candidate_order(self) -> None:
        candidates = [
            GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2 * 1.02),
            GlofasGridCell(51.10, 13.74, DRESDEN_DRAINAGE_AREA_KM2 * 1.01),
        ]
        common = {
            "pegelonline_station_number": PEGELONLINE_STATION_NUMBER,
            "pegelonline_station_uuid": PEGELONLINE_STATION_UUID,
            "pegelonline_equidistance_minutes": 15,
            "station_latitude": 51.05,
            "station_longitude": 13.74,
        }
        forward = finalize_acquisition_intent(
            **common,
            glofas_candidate_cells=candidates,
        )
        reverse = finalize_acquisition_intent(
            **common,
            glofas_candidate_cells=reversed(candidates),
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(acquisition_intent_sha256(forward), acquisition_intent_sha256(reverse))

    def test_station_identity_mismatch_fails_closed_before_grid_selection(self) -> None:
        candidate = GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2)
        with self.assertRaisesRegex(AcquisitionIntentError, "station_number"):
            finalize_acquisition_intent(
                pegelonline_station_number="different-station",
                pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
                pegelonline_equidistance_minutes=15,
                station_latitude=51.05,
                station_longitude=13.74,
                glofas_candidate_cells=[candidate],
            )
        with self.assertRaisesRegex(AcquisitionIntentError, "station_uuid"):
            finalize_acquisition_intent(
                pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
                pegelonline_station_uuid="different-station-uuid",
                pegelonline_equidistance_minutes=15,
                station_latitude=51.05,
                station_longitude=13.74,
                glofas_candidate_cells=[candidate],
            )

    def test_invalid_sampling_or_no_matching_cell_fails_closed(self) -> None:
        good_candidate = GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2)
        with self.assertRaisesRegex(AcquisitionIntentError, "sampling interval"):
            finalize_acquisition_intent(
                pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
                pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
                pegelonline_equidistance_minutes=17,
                station_latitude=51.05,
                station_longitude=13.74,
                glofas_candidate_cells=[good_candidate],
            )

        with self.assertRaisesRegex(AcquisitionIntentError, "grid cell"):
            finalize_acquisition_intent(
                pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
                pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
                pegelonline_equidistance_minutes=15,
                station_latitude=51.05,
                station_longitude=13.74,
                glofas_candidate_cells=[
                    GlofasGridCell(52.0, 13.74, DRESDEN_DRAINAGE_AREA_KM2)
                ],
            )

    def test_type_confused_equidistance_and_station_metadata_fail_closed(self) -> None:
        candidate = GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2)
        with self.assertRaisesRegex(AcquisitionIntentError, "equidistance_minutes"):
            finalize_acquisition_intent(
                pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
                pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
                pegelonline_equidistance_minutes=True,
                station_latitude=51.05,
                station_longitude=13.74,
                glofas_candidate_cells=[candidate],
            )
        with self.assertRaisesRegex(AcquisitionIntentError, "grid cell"):
            finalize_acquisition_intent(
                pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
                pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
                pegelonline_equidistance_minutes=15,
                station_latitude=True,
                station_longitude=13.74,
                glofas_candidate_cells=[candidate],
            )


if __name__ == "__main__":
    unittest.main()
