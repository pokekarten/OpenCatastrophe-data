# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No external bytes/DB access: invented loss stages only."""

import copy
import json
import unittest

from research_runners.synthetic_catxl_loss_math_v0 import (
    SyntheticLossInputError, allocate, example,
)


class SyntheticCatXLTests(unittest.TestCase):
    def setUp(self):
        self.positions, self.events, self.treaty = example()

    def run_example(self):
        return allocate(self.positions, self.events, self.treaty)

    def test_fixed_reference_outcome_and_event_order(self):
        r = self.run_example()
        self.assertEqual([x['gross_eur'] for x in r['events']], [100000, 400000, 900000, 600000])
        self.assertEqual([x['pre_aggregate_ceded_eur'] for x in r['events']], [0, 200000, 500000, 400000])
        self.assertEqual([x['ceded_eur'] for x in r['events']], [0, 200000, 500000, 300000])
        self.assertEqual([x['net_eur'] for x in r['events']], [100000, 200000, 400000, 300000])
        self.assertEqual((r['gross_eur'], r['ceded_eur'], r['net_eur']), (2000000, 1000000, 1000000))
        self.assertEqual(r['aggregate_capacity_remaining_eur'], 0)
        self.assertFalse(r['model_input_approved'])
        self.assertFalse(r['reinstatement_premium_modelled'])

    def test_invariant_each_event_and_year(self):
        r = self.run_example()
        for item in r['events']:
            self.assertEqual(item['gross_eur'], item['ceded_eur'] + item['net_eur'])
            self.assertGreaterEqual(item['aggregate_capacity_after_eur'], 0)
        self.assertEqual(r['gross_eur'], r['ceded_eur'] + r['net_eur'])
        self.assertLessEqual(r['ceded_eur'], r['aggregate_capacity_eur'])
        self.assertEqual(sum(self.positions.values()), 3150000)

    def test_deterministic_deepcopy_and_json(self):
        r = self.run_example()
        self.assertEqual(r, allocate(copy.deepcopy(self.positions), copy.deepcopy(self.events), copy.deepcopy(self.treaty)))
        self.assertEqual(json.dumps(r, sort_keys=True), json.dumps(self.run_example(), sort_keys=True))

    def test_invented_loss_cannot_exceed_exposure(self):
        self.events[0]['losses_eur']['SYNTH-01'] = 125001
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_loss_unknown_unit_rejected(self):
        self.events[0]['losses_eur'] = {'SYNTH-13': 1}
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_duplicate_events_rejected(self):
        self.events[1]['event_id'] = self.events[0]['event_id']
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_reversed_event_time_rejected(self):
        self.events[1]['date'] = '2026-11-01'
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_same_day_events_rejected_to_avoid_implicit_order(self):
        self.events[1]['date'] = self.events[0]['date']
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_year_and_vintage_rejected(self):
        for date in ('2025-12-31', '2026-11-01', '2027-01-01', '2026-11-2', 'bad-date'):
            with self.subTest(date=date):
                e = copy.deepcopy(self.events);e[0]['date'] = date
                with self.assertRaises(SyntheticLossInputError):allocate(self.positions,e,self.treaty)

    def test_peril_unknown_rejected(self):
        self.events[0]['peril'] = 'earthquake'
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_amount_types_rejected(self):
        for amount in (-1, 10.1, True, None, '100', 10**14):
            with self.subTest(amount=amount):
                e = copy.deepcopy(self.events);e[0]['losses_eur']['SYNTH-01'] = amount
                with self.assertRaises(SyntheticLossInputError):allocate(self.positions,e,self.treaty)

    def test_real_insurer_and_extra_fields_blocked(self):
        self.treaty['actual_insurer'] = 'a real company'
        with self.assertRaises(SyntheticLossInputError): self.run_example()
        del self.treaty['actual_insurer']
        self.treaty['synthetic_only'] = False
        with self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_undefined_or_paid_reinstatement_pricing_rejected(self):
        for price in ('unknown', 'paid', 'free', 0):
            self.treaty['reinstatement_pricing'] = price
            with self.subTest(price=price), self.assertRaises(SyntheticLossInputError): self.run_example()

    def test_zero_reinstatement_cap(self):
        self.treaty['reinstatements'] = 0
        r = self.run_example()
        self.assertEqual(r['ceded_eur'], 500000)
        self.assertEqual(r['net_eur'], 1500000)

    def test_more_reinstatement_capacity(self):
        self.treaty['reinstatements'] = 2
        r = self.run_example()
        self.assertEqual(r['ceded_eur'], 1100000)
        self.assertEqual(r['net_eur'], 900000)

    def test_treaty_negative_terms_rejected(self):
        for key, value in [('attachment_eur', -1), ('occurrence_limit_eur', 0), ('reinstatements', -1), ('reinstatements', 4), ('currency', 'USD')]:
            with self.subTest(key=key):
                t = copy.deepcopy(self.treaty);t[key] = value
                with self.assertRaises(SyntheticLossInputError):allocate(self.positions,self.events,t)

    def test_no_mutation(self):
        before = copy.deepcopy((self.positions,self.events,self.treaty))
        self.run_example()
        self.assertEqual((self.positions,self.events,self.treaty),before)

    def test_external_sources_do_not_enter_fields(self):
        r = self.run_example()
        self.assertNotIn('source_url',json.dumps(r))
        self.assertNotIn('organization_id',json.dumps(r))
        self.assertNotIn('real_insurer',json.dumps(r))


if __name__ == '__main__':
    unittest.main()
