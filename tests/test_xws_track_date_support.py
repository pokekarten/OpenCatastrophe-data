# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import tempfile
import unittest
from research_runners.xws_track_date_support import inspect

class TrackTest(unittest.TestCase):
    def test_dates_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'track.csv'
            row='1, "2010-02-27 00:00:00", 0\n'
            p.write_text(row+'1, "2010-02-28 00:00:00", 0\n')
            r=inspect(p)
            self.assertEqual(r['calendar_dates'],['20100227','20100228'])
            self.assertFalse(r['physical_identity_verified'])
            p.write_text(row*2)
            with self.assertRaises(ValueError):inspect(p)
