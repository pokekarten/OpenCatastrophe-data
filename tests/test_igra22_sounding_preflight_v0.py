# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only IGRA v2.2 physical-level format and adversarial boundary checks."""

import hashlib
import unittest

from scripts.igra22_sounding_preflight_v0 import (
    MAX_TEXT_BYTES, Igra22FormatError, screen_igra22_unzipped_text_bytes,
)

SID = "USM00072201"  # NCEI documentation example; all bytes below are synthetic.


def header(*, sid=SID, y=2025, m=6, day=1, hh=0, rel=9999, levels=1, lat=245000, lon=-813000):
    line = [' '] * 71
    for start, end, value in [(0,1,'#'), (1,12,sid), (13,17,f'{y:04}'),
        (18,20,f'{m:02}'), (21,23,f'{day:02}'), (24,26,f'{hh:02}'),
        (27,31,f'{rel:04}'), (32,36,f'{levels:4}'),
        (37,45,'ncdc-gts'), (46,54,'ncdc-gts'),
        (55,62,f'{lat:7}'), (63,71,f'{lon:8}')]:
        line[start:end] = list(value)
    return ''.join(line)


def level(*, lev1='1', lev2='0', etime=-9999, press=100000, pflag=' ',
          gph=75, zflag=' ', temp=210, tflag=' ', rh=600, dpdp=70,
          wdir=90, wspd=200):
    line = [' '] * 51
    for start, end, value in [(0,1,lev1),(1,2,lev2),(3,8,f'{etime:5}'),
        (9,15,f'{press:6}'), (15,16,pflag), (16,21,f'{gph:5}'),
        (21,22,zflag), (22,27,f'{temp:5}'), (27,28,tflag),
        (28,33,f'{rh:5}'), (34,39,f'{dpdp:5}'),
        (40,45,f'{wdir:5}'), (46,51,f'{wspd:5}')]:
        line[start:end] = list(value)
    return ''.join(line)


def text_block(h=None, rows=None):
    return ('\n'.join([h or header()] + (rows if rows is not None else [level()])) + '\n').encode('ascii')


class Igra22OriginalTextPreflightTests(unittest.TestCase):
    def test_one_sounding_byte_identity_and_nonadmission(self):
        raw = text_block()
        r = screen_igra22_unzipped_text_bytes(raw, station_id=SID)
        self.assertEqual(r['soundings'], 1)
        self.assertEqual(r['levels'], 1)
        self.assertEqual(r['first_date_utc'], '2025-06-01')
        self.assertEqual(r['uncompressed_text_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(r['zip_original_sha256'], 'not_tested')
        self.assertEqual(r['scientific_and_model_admission'], 'not_admitted')

    def test_missing_codes_flags_and_two_soundings(self):
        data = text_block(rows=[level(wspd=-8888, press=-9999, temp=-9999, rh=-9999,
                                      gph=-8888, pflag='A', zflag='B', tflag='A')])
        data += text_block(h=header(day=2, rel=1299), rows=[level(wspd=-9999, lev1='3')])
        r = screen_igra22_unzipped_text_bytes(data, station_id=SID)
        self.assertEqual(r['soundings'], 2)
        self.assertEqual(r['levels_without_wind_speed'], 2)
        self.assertEqual(r['last_date_utc'], '2025-06-02')

    def test_rejects_malformed_source_or_science(self):
        negatives = [
            (text_block(), "INVALID-ID"),
            (b'', SID), (b'<html>internal error</html>', SID),
            (b'\xff'*10, SID), (text_block().replace(b'\n', b'\x0b'), SID),
            (b'Z' * (MAX_TEXT_BYTES + 1), SID),
            (text_block(h=header(sid='GBM00012345')), SID),
            (text_block(h=header(m=13)), SID),
            (text_block(h=header(day=31, m=2)), SID),
            (text_block(h=header(hh=34)), SID),
            (text_block(h=header(rel=2360)), SID),
            (text_block(h=header(levels=2)), SID),
            (text_block(h=header(levels=0)), SID),
            (text_block(rows=[level(wdir=361)]), SID),
            (text_block(rows=[level(wspd=-1)]), SID),
            (text_block(rows=[level(rh=1001)]), SID),
            (text_block(rows=[level(press=111000)]), SID),
            (text_block(rows=[level(dpdp=-1)]), SID),
            (text_block(rows=[level(etime=12360)]), SID),
            (text_block(rows=[level(pflag='Z')]), SID),
            (text_block(rows=[level(lev1='8')]), SID),
            (text_block() + b'BAD ROW\n', SID),
            (text_block().replace(b'\n', b'\n\n', 1), SID),
        ]
        for raw, station in negatives:
            with self.subTest(raw=raw[:50], sid=station):
                with self.assertRaises(Igra22FormatError):
                    screen_igra22_unzipped_text_bytes(raw, station_id=station)


if __name__ == '__main__':
    unittest.main()
