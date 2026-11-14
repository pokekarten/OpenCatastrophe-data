# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""PSMSL source-format negative controls: independently synthetic only."""
from __future__ import annotations

import unittest

from scripts.audit_psmsl_rlr_monthly_v0 import audit_bytes, PSMSLPreflightError


def series(lines=None):
    if lines is None:
        lines = [
            '2024.9583; 7084; 0; 000',
            '2025.0417; -99999; 31; 001',
            '2025.1250; 7063; 99; 011',
        ]
    return ('\n'.join(lines) + '\n').encode('ascii')


class PSMSLRLRMonthlyTests(unittest.TestCase):
    def test_synthetic_monthly_padded_missing_and_octal_quality(self):
        result = audit_bytes(series(), station_id=202)
        self.assertEqual(result['calendar_month_count'], 3)
        self.assertEqual(result['missing_monthly_means'], 1)
        self.assertEqual(result['interpolated_months'], 1)
        self.assertEqual(result['caution_flag_months'], 2)
        self.assertEqual(result['mean_tidal_level_flag_months'], 1)
        self.assertEqual(result['provider_origin_verified'], False)
        self.assertEqual(result['scientific_model_admission'], False)
        self.assertEqual(len(result['input_sha256']), 64)

    def test_all_octal_bits_are_accepted_without_semantic_promotion(self):
        r = audit_bytes(series(['2025.0417; 7000; 0; 777']), station_id=202)
        self.assertEqual((r['caution_flag_months'], r['mean_tidal_level_flag_months']), (1, 1))

    def test_reject_corrupt_or_ambiguous_inputs(self):
        bad = [b'', b'\xff', b'\x00', b'a' * (2 * 1024 * 1024 + 1),
            series([]), series(['2025.0000;7000;0;000']),
            series(['2025.9999;7000;0;000']),
            series(['2025.0417;foo;0;000']),
            series(['2025.0417;7.3;0;000']),
            series(['2025.0417;7000;-1;000']),
            series(['2025.0417;7000;40;000']),
            series(['2025.0417;7000;0;888']),
            series(['2025.0417;7000;0;0010']),
            series(['2025.0417;7000;0']),
            series(['2025.0417;7000;0;000;EXTRA']),
            series(['2025.0417;7000;0;000', '2025.0417;7000;0;000']),
            series(['2025.0417;7000;0;000', '2025.2083;7000;0;000']),
            series(['2025.0417;7000;0;000', '2024.9583;7000;0;000']),
            series(['2025.0417;7000;0;000', '']),
            series(['2024.0417;7000;0;000']) + b'\x00',
        ]
        for idx, item in enumerate(bad):
            with self.subTest(idx=idx), self.assertRaises(PSMSLPreflightError):
                audit_bytes(item, station_id=202)

    def test_reject_station_id_not_claimed_unchanged(self):
        for n in (0, -1, 1000000, True):
            with self.subTest(n=n), self.assertRaises(PSMSLPreflightError):
                audit_bytes(series(), station_id=n)


if __name__ == '__main__':
    unittest.main()
