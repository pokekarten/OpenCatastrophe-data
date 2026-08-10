# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.dresden_acquisition_intent import (
    PEGELONLINE_STATION_NUMBER,
    PEGELONLINE_STATION_UUID,
    AcquisitionIntentError,
    acquisition_intent,
    acquisition_intent_sha256,
    finalize_acquisition_intent,
)
from scripts.hydrology_grid_matching import DRESDEN_DRAINAGE_AREA_KM2, GlofasGridCell


class AcquisitionIntentIntegrityTests(unittest.TestCase):
    def _finalized(self) -> dict[str, object]:
        return finalize_acquisition_intent(
            pegelonline_station_number=PEGELONLINE_STATION_NUMBER,
            pegelonline_station_uuid=PEGELONLINE_STATION_UUID,
            pegelonline_equidistance_minutes=15,
            station_latitude=51.05,
            station_longitude=13.74,
            glofas_candidate_cells=[GlofasGridCell(51.06, 13.74, DRESDEN_DRAINAGE_AREA_KM2)],
        )

    def test_hash_accepts_exact_frozen_intents(self) -> None:
        self.assertEqual(len(acquisition_intent_sha256(acquisition_intent())), 64)
        self.assertEqual(len(acquisition_intent_sha256(self._finalized())), 64)

    def test_hash_rejects_unexpected_or_weakened_contract_fields(self) -> None:
        finalized = self._finalized()

        extra = dict(finalized)
        extra["unreviewed_extension"] = {"enabled": True}
        with self.assertRaisesRegex(AcquisitionIntentError, "canonical frozen"):
            acquisition_intent_sha256(extra)

        weakened_stop = dict(finalized)
        weakened_stop["hard_stops"] = []
        with self.assertRaisesRegex(AcquisitionIntentError, "canonical frozen"):
            acquisition_intent_sha256(weakened_stop)

        weakened_receipt = dict(finalized)
        weakened_receipt["required_external_receipt"] = {
            "per_file": ["logical_identity"],
            "per_request": [],
            "forbidden_in_git": [],
        }
        with self.assertRaisesRegex(AcquisitionIntentError, "canonical frozen"):
            acquisition_intent_sha256(weakened_receipt)

        initial_extra = acquisition_intent()
        initial_extra["unexpected"] = True
        with self.assertRaisesRegex(AcquisitionIntentError, "canonical frozen"):
            acquisition_intent_sha256(initial_extra)


if __name__ == "__main__":
    unittest.main()
