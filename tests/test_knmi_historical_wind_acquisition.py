# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import io
import unittest
import zipfile
from research_runners.knmi_historical_wind_acquisition import inspect

def package(rows):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('sample.txt','SOURCE: KNMI\nFX = hourly maximum\n# STN,YYYYMMDD,HH,FX\n'+rows)
    return out.getvalue()

class IntakeTests(unittest.TestCase):
    def test_hour24_and_missing_gust(self):
        r=inspect(package('260,19991231,24,200\n260,20000101,1,\n'),260)
        self.assertEqual(r['first_hour_end_utc'],'2000-01-01T00:00:00')
        self.assertEqual(r['missing_fx'],1)
        self.assertEqual(r['missing_hours_between_endpoints'],0)

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            inspect(package('260,19991231,24,200\n'*2),260)

    def test_wrong_station_hour_and_negative_gust(self):
        for row in ['235,19991231,24,200','260,19991231,0,200','260,19991231,24,-1']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                inspect(package(row),260)

    def test_missing_hour_counted(self):
        r=inspect(package('260,19991231,22,200\n260,19991231,24,200'),260)
        self.assertEqual(r['missing_hours_between_endpoints'],1)

    def test_wrong_decade_rejected(self):
        with self.assertRaisesRegex(ValueError, 'requested period'):
            inspect(package('260,19991231,24,200'),260,'1981-1990')

    def test_duplicate_column_rejected(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('sample.txt','# STN,YYYYMMDD,HH,FX,FX\n260,19991231,24,200,0')
        with self.assertRaisesRegex(ValueError, 'Duplicate source columns'):
            inspect(out.getvalue(),260)
