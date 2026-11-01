# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent reproducibility oracle for SQL synthetic GUL pilot.

All values, peril rates and vulnerabilities are INVENTED. No native CAT,
insurance indemnity, treaty or regulatory output is asserted.
"""
import hashlib
import unittest

PREFIX = 'OC_NEON_10K_SYNTH_GUL_V0'
ASSETS = tuple((f'SYNTH-{i:02}', 100000 + 25000 * i) for i in range(1, 13))
EXPECTED = {
    'worlds': 10000, 'assets': 12, 'value': 3150000,
    'events': 1541, 'zero_event_years': 8509,
    'annual_sum': 285494000, 'aal_cents': 2854940,
    'aep99': 342500, 'aep995': 366250,
    'oep99': 333750, 'oep995': 351250,
    'max_annual': 638750, 'wind_events': 1008,
    'flood_events': 533, 'wind_sum': 188021000,
    'flood_sum': 97473000,
}


def digest(s):
    return hashlib.md5(s.encode('ascii')).digest()  # exact byte parity with PostgreSQL md5()


def disc(values, p, q):
    return sorted(values)[(len(values) * p + q - 1) // q - 1]


def compute(assets=ASSETS, *, synthetic=True):
    if not synthetic:
        raise ValueError('real exposures are forbidden in synthetic oracle')
    if (tuple(assets) != ASSETS or len(set(a for a, _ in assets)) != 12 or
            sum(v for _, v in assets) != 3150000):
        raise ValueError('unexpected synthetic fixture, do not silently reclassify')
    ann, biggest = [], []
    count = {'windstorm': 0, 'flood': 0}
    totals = {'windstorm': 0, 'flood': 0}
    zero_event = 0
    for yr in range(10000):
        losses = []
        for peril, threshold in (('windstorm', 26), ('flood', 13)):
            h = digest(f'{PREFIX}|{yr}|{peril}')
            if h[0] >= threshold:
                continue
            intensity = 1 + h[1] % 5
            event = 0
            for asset, value in assets:
                vulnerability = 1 + digest(f'{PREFIX}|local|{yr}|{peril}|{asset}')[2] % 3
                loss_century = value * intensity * vulnerability
                if loss_century % 100:
                    raise ValueError('non-integer EUR damage')
                event += loss_century // 100
            losses.append(event)
            count[peril] += 1
            totals[peril] += event
        ann.append(sum(losses))
        biggest.append(max(losses, default=0))
        zero_event += not bool(losses)
    return {
        'worlds': len(ann), 'assets': len(assets), 'value': sum(v for _, v in assets),
        'events': count['windstorm'] + count['flood'], 'zero_event_years': zero_event,
        'annual_sum': sum(ann), 'aal_cents': sum(ann) * 100 // len(ann),
        'aep99': disc(ann, 99, 100), 'aep995': disc(ann, 995, 1000),
        'oep99': disc(biggest, 99, 100), 'oep995': disc(biggest, 995, 1000),
        'max_annual': max(ann), 'wind_events': count['windstorm'],
        'flood_events': count['flood'], 'wind_sum': totals['windstorm'],
        'flood_sum': totals['flood'],
    }


class TestSyntheticNeonGul10k(unittest.TestCase):
    def test_matches_live_neon_validation_read_only_result(self):
        self.assertEqual(compute(), EXPECTED)

    def test_rejects_changed_exposure_value(self):
        bad = list(ASSETS)
        bad[0] = (bad[0][0], bad[0][1] + 100)
        with self.assertRaises(ValueError):
            compute(tuple(bad))

    def test_rejects_same_total_swapped_asset_values(self):
        swapped = list(ASSETS)
        swapped[0], swapped[1] = (swapped[0][0], swapped[1][1]), (swapped[1][0], swapped[0][1])
        self.assertEqual(sum(amount for _, amount in swapped), 3150000)
        with self.assertRaises(ValueError):
            compute(tuple(swapped))

    def test_rejects_missing_or_empty_assets(self):
        for malformed in ((), ASSETS[:-1]):
            with self.subTest(malformed_count=len(malformed)):
                with self.assertRaises(ValueError):
                    compute(malformed)

    def test_sql_guard_does_not_silently_drop_bad_fixtures(self):
        from pathlib import Path
        sql = (Path(__file__).resolve().parents[1]
               / 'research_runners/sql/neon_synthetic_gul_10k_v0.sql').read_text(encoding='utf-8')
        self.assertIn('FULL JOIN expected_assets', sql)
        self.assertIn('mismatches=0', sql)
        self.assertIn('1 / (CASE WHEN n=12', sql)
        self.assertNotIn('HAVING COUNT(*)=12', sql)

    def test_sql_pins_same_exposure_version_as_synthetic_oed(self):
        from pathlib import Path
        sql = (Path(__file__).resolve().parents[1]
               / 'research_runners/sql/neon_synthetic_gul_10k_v0.sql').read_text(encoding='utf-8')
        for required in (
            "pv.version_label='v0'", "pv.seed=20261101",
            "pv.generation_method='deterministic_independent_synthetic_sql_v0'",
            "pv.source_key IS NULL",
            "pv.assumption_metadata ->> 'synthetic'='true'",
            "pv.assumption_metadata ->> 'model_input_approved'='false'",
            "pv.assumption_metadata ->> 'real_insurer'='false'",
            "pv.assumption_metadata ->> 'external_source_rows_used'='0'",
        ):
            with self.subTest(required=required):
                self.assertIn(required, sql)

    def test_sql_fails_closed_on_extra_versions_and_unfiltered_units(self):
        from pathlib import Path
        sql = (Path(__file__).resolve().parents[1]
               / 'research_runners/sql/neon_synthetic_gul_10k_v0.sql').read_text(encoding='utf-8')
        for required in (
            'COUNT(*) FROM selected_versions',
            'COUNT(*) FROM exposure.portfolio_version v',
            'COUNT(*) FROM raw_assets',
            'selected_version_count=1 AND all_version_count=1',
            'all_unit_count=12 AND n=12 AND unique_ids=12',
            "e.insured_value_currency='EUR'",
            "e.value_basis='invented_smoke_test_value_not_insured_observation'",
            'ST_SRID(e.location)=4326',
        ):
            with self.subTest(required=required):
                self.assertIn(required, sql)

    def test_rejects_non_synthetic_inputs(self):
        with self.assertRaises(ValueError):
            compute(ASSETS, synthetic=False)

    def test_no_double_counting_of_expected_perils(self):
        self.assertEqual(EXPECTED['wind_sum'] + EXPECTED['flood_sum'],
                         EXPECTED['annual_sum'])
        self.assertEqual(EXPECTED['wind_events'] + EXPECTED['flood_events'],
                         EXPECTED['events'])


if __name__ == '__main__':
    unittest.main()
