# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction
import unittest
from research_runners.thresholded_loss_consumer_bounds_v0 import (
    Interval, LossBoundError, event_loss_interval, occurrence_xl_interval,
    weighted_annual_loss_interval, weighted_exceedance_bounds,
)

class ThresholdedLossBoundsTests(unittest.TestCase):
    def test_bound_requires_known_omitted_count_and_maximum(self):
        self.assertEqual(event_loss_interval(retained_loss_eur=1000, omitted_count=3,
                                             max_omitted_eur=2000), Interval(1000, 7000))
        for omitted in (None,True,-1,'3'):
            with self.subTest(omitted=omitted),self.assertRaises(LossBoundError):
                event_loss_interval(retained_loss_eur=1000,omitted_count=omitted,max_omitted_eur=2000)

    def test_layer_may_change_from_zero_to_limit(self):
        e=event_loss_interval(retained_loss_eur=1000,omitted_count=2,max_omitted_eur=2000)
        self.assertEqual(occurrence_xl_interval(e,attachment_eur=2000,limit_eur=1500), Interval(0,1500))

    def test_small_error_near_attachment_can_flip_cession(self):
        e=event_loss_interval(retained_loss_eur=1900,omitted_count=1,max_omitted_eur=200)
        self.assertEqual(occurrence_xl_interval(e,attachment_eur=2000,limit_eur=1000), Interval(0,100))

    def test_fixed_full_cap_protects_upper_recovery(self):
        e=event_loss_interval(retained_loss_eur=10000,omitted_count=100,max_omitted_eur=2000)
        self.assertEqual(occurrence_xl_interval(e,attachment_eur=1000,limit_eur=2000), Interval(2000,2000))

    def test_annual_weighted_zero_year_preserved(self):
        worlds=((Fraction(9,10),Interval(0,0)),(Fraction(1,10),Interval(100,300)))
        self.assertEqual(weighted_annual_loss_interval(worlds),(Fraction(10),Fraction(30)))
        self.assertEqual(weighted_exceedance_bounds(worlds,threshold_eur=200),(Fraction(),Fraction(1,10)))

    def test_strict_exceedance_at_boundaries(self):
        worlds=((Fraction(1,2),Interval(10,20)),(Fraction(1,2),Interval(21,21)))
        self.assertEqual(weighted_exceedance_bounds(worlds,threshold_eur=20),(Fraction(1,2),Fraction(1,2)))
        self.assertEqual(weighted_exceedance_bounds(worlds,threshold_eur=10),(Fraction(1,2),Fraction(1)))

    def test_negative_bool_probability_invalid_interval_fail_closed(self):
        for worlds in (((Fraction(1,2),Interval(0,1)),),
                       ((Fraction(1),Interval(2,1)),),
                       ((True,Interval(0,0)),)):
            with self.subTest(worlds=worlds), self.assertRaises(LossBoundError):
                weighted_annual_loss_interval(worlds)
        with self.assertRaises(LossBoundError):
            occurrence_xl_interval(Interval(1,2),attachment_eur=0,limit_eur=0)

    def test_no_unjustified_overflow_or_model_output(self):
        with self.assertRaises(LossBoundError):
            event_loss_interval(retained_loss_eur=10**16,omitted_count=1,max_omitted_eur=1)
        self.assertEqual(event_loss_interval(retained_loss_eur=0,omitted_count=0,max_omitted_eur=2000), Interval(0,0))

if __name__=='__main__':unittest.main()
