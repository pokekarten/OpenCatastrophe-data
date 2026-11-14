# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from research_runners.knmi_historical_event_coverage import window, read_archive

class CoverageTests(unittest.TestCase):
    def test_boundary_and_zero_gust_are_valid(self):
        start=datetime(1999,12,25)
        obs={start+timedelta(hours=i):0 for i in range(1,73)}
        self.assertTrue(window(obs,'19991226')['complete'])
        del obs[start+timedelta(hours=72)]
        obs[start]=20
        self.assertEqual(window(obs,'19991226')['missing_rows'],1)

    def test_missing_value_and_missing_row_are_different(self):
        obs={datetime(1999,12,25,1):None,datetime(1999,12,25,2):0}
        r=window(obs,'19991226')
        self.assertEqual(r['missing_rows'],70)
        self.assertEqual(r['missing_gust_values'],1)
        self.assertEqual(r['valid_gust_hours'],1)
        self.assertFalse(r['complete'])

    def test_changed_original_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'original.zip';p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                read_archive(p,'0'*64,260)
