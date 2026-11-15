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
