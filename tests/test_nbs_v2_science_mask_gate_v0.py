# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic negative tests: no real NOAA source bytes or network calls."""
from __future__ import annotations

import math
import unittest

from scripts.nbs_v2_science_mask_gate_v0 import NBSMaskGateError, screen_science_daily_cell


def synthetic(mask=6, speed=18.0):
    return {"dataset_id": "noaacwBlendedWindsDaily", "product_version": "2.0",
            "stream": "science_quality", "cadence": "daily", "units": "m s-1",
            "windspeed": speed, "mask": mask}


class NBSScienceMaskGateTests(unittest.TestCase):
    def test_model_fill_is_never_independent_observation(self):
        item = screen_science_daily_cell(synthetic())
        self.assertEqual(item["cell_provenance"], "model_filled")
        self.assertEqual(item["wind_speed_m_s"], 18.0)
        self.assertFalse(item["independent_observation_verified"])
        self.assertFalse(item["model_input_approved"])

    def test_other_codes_are_unknown_not_automatically_observed(self):
        for mask in (0, 1, 5, 7):
            with self.subTest(mask=mask):
                item = screen_science_daily_cell(synthetic(mask=mask))
                self.assertEqual(item["cell_provenance"], "mask_code_not_independently_reviewed")
                self.assertFalse(item["independent_observation_verified"])

    def test_fill_is_missing_and_not_zero(self):
        for mask,speed in ((-9999, 9), (6, -9999), (-9999, -9999)):
            with self.subTest(mask=mask,speed=speed):
                item = screen_science_daily_cell(synthetic(mask,speed))
                self.assertEqual(item["cell_provenance"], "missing_fill_value")
                self.assertIsNone(item["wind_speed_m_s"])
                self.assertFalse(item["numeric_value_present"])

    def test_mask_is_mandatory(self):
        x=synthetic();del x["mask"]
        with self.assertRaisesRegex(NBSMaskGateError,"mask must"):
            screen_science_daily_cell(x)

    def test_must_be_exact_science_daily_v2_stream(self):
        for key,val in (("dataset_id","noaacwBlendednrtWindsDaily"),
                        ("product_version","1.0"),("stream","nrt"),
                        ("cadence","6hourly"),("units","knots")):
            x=synthetic();x[key]=val
            with self.subTest(field=key),self.assertRaises(NBSMaskGateError):
                screen_science_daily_cell(x)

    def test_nonfinite_boolean_and_negative_nonfill_fail(self):
        for key,val in (("mask",True),("windspeed",False),("mask",math.nan),
                        ("windspeed",math.inf),("mask",-1),("mask",1.5),
                        ("windspeed",-0.5)):
            x=synthetic();x[key]=val
            with self.subTest(field=key,val=repr(val)),self.assertRaises(NBSMaskGateError):
                screen_science_daily_cell(x)


if __name__ == "__main__":
    unittest.main()
