# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import unittest
from research_runners.hazard_loss_support import assess

class SupportTest(unittest.TestCase):
    def test_missing_day_is_detected(self):
        r=assess('2020-02-08T00:00:00+00:00','2020-02-12T00:00:00+00:00',
                 '2020-02-07T00:00:00+00:00','2020-02-12T00:00:00+00:00')
        self.assertEqual(r['uncovered_start_hours'],24)
        self.assertFalse(r['support_gate_passed'])
    def test_time_coverage_alone_insufficient(self):
        args=['2020-02-07T00:00:00+00:00','2020-02-12T00:00:00+00:00']*2
        self.assertFalse(assess(*args)['support_gate_passed'])
        self.assertTrue(assess(*args,geographic_coverage_verified=True)['support_gate_passed'])
    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):assess(*(['2020-02-07']*4))

    def test_non_boolean_geographic_evidence_cannot_open_support_gate(self):
        args = ['2020-02-07T00:00:00+00:00', '2020-02-12T00:00:00+00:00'] * 2
        for value in ('false', 'true', '0', 1, 0, None, [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'boolean'):
                assess(*args, geographic_coverage_verified=value)

    def test_support_gate_is_strict_boolean_even_with_timezone_offsets(self):
        hazard_start = '2020-02-07T01:00:00+01:00'
        hazard_end = '2020-02-12T00:00:00+00:00'
        loss_start = '2020-02-07T00:00:00+00:00'
        loss_end = '2020-02-12T01:00:00+01:00'
        for confirmed in (True, False):
            with self.subTest(confirmed=confirmed):
                result = assess(hazard_start, hazard_end, loss_start, loss_end,
                                geographic_coverage_verified=confirmed)
                self.assertIs(type(result['support_gate_passed']), bool)
                self.assertIs(result['support_gate_passed'], confirmed)
                self.assertEqual(result['uncovered_start_hours'], 0)
                self.assertEqual(result['uncovered_end_hours'], 0)
