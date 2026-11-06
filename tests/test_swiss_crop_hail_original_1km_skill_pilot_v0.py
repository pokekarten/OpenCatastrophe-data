# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, fail-closed Swiss crop hail original 1 km model tests."""
from __future__ import annotations

import unittest

from research_runners import swiss_crop_hail_original_1km_skill_pilot_v0 as pilot
from research_runners.swiss_crop_hail_asset_preflight_v0 import Blocked


class FakeIntensity:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, selection):
        import numpy as np
        event, locations = selection
        return FakeRow(np.asarray(self.values[event])[locations])


class FakeRow:
    def __init__(self, values):
        self.values = values

    def toarray(self):
        return self.values.reshape(1, -1)


class SwissCropHailSkillTests(unittest.TestCase):
    def test_published_step_function_equal_threshold_is_prediction(self):
        self.assertTrue(pilot.require_threshold("MESHS", 20, 20))
        self.assertFalse(pilot.require_threshold("MESHS", 20, 19.999))
        self.assertTrue(pilot.require_threshold("POH", 80, 80))
        self.assertFalse(pilot.require_threshold("POH", 80, 79.999))

    def test_suspicious_variable_threshold_and_units_fail_closed(self):
        for args in [
            ("MESHS", 19, 50), ("POH", 20, 50), ("BAD", 20, 40),
            ("MESHS", 20.0, 50), ("MESHS", 40, -1), ("POH", 80, 110),
        ]:
            with self.subTest(args=args):
                with self.assertRaises(Blocked):
                    pilot.require_threshold(*args)

    def test_event_cropped_scorer_known_contingency_counts(self):
        import numpy as np
        date1, date2 = 100, 200
        hazard = {
            "variable": "MESHS",
            "dates": (date1, date2),
            "csr": FakeIntensity([[15, 20, 30, 60], [40, 10, 60, 0]]),
        }
        observations = {
            date1: np.asarray([False, True, False, True]),
            date2: np.asarray([True, False, True, False]),
        }
        d = pilot.run_skill("wheat", hazard, np.arange(4), observations)
        self.assertEqual(d["evaluation_population_counts_across_selected_event_days"], 8)
        self.assertEqual(d["observed_selected_event_count"], 2)
        t = d["threshold_metrics"]["20"]
        self.assertEqual([t[k] for k in ("hits", "false_alarms", "misses", "correct_negatives")],
                         [4, 1, 0, 3])
        h = d["threshold_metrics"]["60"]
        self.assertEqual([h[k] for k in ("hits", "false_alarms", "misses", "correct_negatives")],
                         [2, 0, 2, 4])
        self.assertGreater(t["pod"], h["pod"])

    def test_poh_uses_percentage_thresholds_not_mes_hail_size(self):
        import numpy as np
        hazard = {"variable": "POH", "dates": (100,),
                  "csr": FakeIntensity([[40, 50, 90, 100]])}
        d = pilot.run_skill("barley", hazard, np.arange(4),
                            {100: np.asarray([True, False, True, False])})
        score = d["threshold_metrics"]["90"]
        self.assertEqual((score["hits"], score["false_alarms"], score["misses"], score["correct_negatives"]),
                         (1, 1, 1, 1))
        self.assertEqual(d["threshold_unit"], "percent")

    def test_bad_unmatched_dates_never_assumed_zero(self):
        import numpy as np
        hazard = {"variable": "MESHS", "dates": (10,),
                  "csr": FakeIntensity([[40]])}
        with self.assertRaises(KeyError):
            pilot.run_skill("maize", hazard, np.arange(1),
                            {20: np.asarray([False])})

    def test_real_released_1km_binary_exposure_and_damage_join(self):
        import numpy as np
        exposure = {"exposures": {
            "block0_items": np.asarray([b"n_fields", b"area_ha", b"latitude", b"longitude"]),
            "block0_values": np.asarray([[1., 2., 46., 8.],
                                         [2., 3., 47., 9.]]),
            "axis1": np.asarray([0, 1]),
        }}
        damage = {
            "coord_exp": np.asarray([[47., 9.], [46., 8.]]),
            "date": np.asarray([100, 200]),
            "imp_mat/indptr": np.asarray([0, 1, 2]),
            "imp_mat/indices": np.asarray([1, 0]),
            "imp_mat/data": np.asarray([1., 1.]),
        }
        coords, observed, missing = pilot.exposure_and_observed(exposure, damage, [100, 200])
        self.assertEqual(coords.shape, (2, 2))
        self.assertEqual(missing, 0)
        self.assertEqual(observed[100].tolist(), [True, False])
        self.assertEqual(observed[200].tolist(), [False, True])

    def test_damage_outside_2021_crop_support_is_not_silently_dropped(self):
        import numpy as np
        exposure = {"exposures": {
            "block0_items": np.asarray([b"n_fields", b"latitude", b"longitude"]),
            "block0_values": np.asarray([[1., 46., 8.]]),
            "axis1": np.asarray([0]),
        }}
        damage = {
            "coord_exp": np.asarray([[47., 9.]]),
            "date": np.asarray([100]),
            "imp_mat/indptr": np.asarray([0, 1]),
            "imp_mat/indices": np.asarray([0]),
            "imp_mat/data": np.asarray([1.]),
        }
        with self.assertRaisesRegex(Blocked, "not in original crop support"):
            pilot.exposure_and_observed(exposure, damage, [100])

    def test_negative_or_zero_crop_field_count_blocks_unreviewed_support(self):
        import numpy as np
        for raw in (-1., 0., 0.5):
            with self.subTest(fields=raw):
                exposure = {"exposures": {
                    "block0_items": np.asarray([b"n_fields", b"latitude", b"longitude"]),
                    "block0_values": np.asarray([[raw, 46., 8.]]),
                    "axis1": np.asarray([0]),
                }}
                damage = {"coord_exp": np.asarray([[46., 8.]]), "date": np.asarray([100]),
                          "imp_mat/indptr": np.asarray([0, 1]), "imp_mat/indices": np.asarray([0]),
                          "imp_mat/data": np.asarray([1.])}
                with self.assertRaises(Blocked):
                    pilot.exposure_and_observed(exposure, damage, [100])


if __name__ == "__main__":
    unittest.main()
