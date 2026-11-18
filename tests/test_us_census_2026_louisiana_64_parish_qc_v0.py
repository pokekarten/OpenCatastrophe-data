# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Purely invented DBF 64-parish source identity and fail-closed cases."""
from __future__ import annotations

import struct
import unittest

from research_runners.us_census_2026_louisiana_64_parish_qc_v0 import (
    _la_positions, Louisiana64Error,
)
from tests.test_us_census_2026_county_zip_audit_v0 import fake_members
from research_runners.us_census_2026_county_zip_audit_v0 import STEM


def invented_64_rows():
    original = fake_members()[f"{STEM}.dbf"]
    header = struct.unpack_from("<H",original,8)[0]
    record = struct.unpack_from("<H",original,10)[0]
    data=bytearray(original[:header])
    struct.pack_into("<I",data,4,64)
    for index in range(64):
        county=f"{index*2+1:03d}".encode()
        data.extend((b" "+b"22"+county+b"22"+county+
                     f"TEST_{index}".encode().ljust(20,b" ")))
    assert len(data)==header+record*64
    return bytes(data)


class Louisiana64SourceTests(unittest.TestCase):
    def test_exact_64_original_identities_are_discovered(self):
        # Synthetic DBF uses 64 odd-numbered Louisiana-looking county FIPS.
        x=invented_64_rows()
        r=_la_positions(x)
        self.assertEqual(len(r),64)
        self.assertEqual(r["22071"],35)
        self.assertEqual(r["22051"],25)
        self.assertEqual(r["22087"],43)

    def test_missing_one_parish_rejected(self):
        x=bytearray(invented_64_rows())
        struct.pack_into("<I",x,4,63)
        with self.assertRaises(Louisiana64Error):
            _la_positions(bytes(x))

    def test_duplicate_parish_code_rejected(self):
        x=bytearray(invented_64_rows())
        header=struct.unpack_from("<H",x,8)[0]
        record=struct.unpack_from("<H",x,10)[0]
        start=header+record
        x[start+1:start+1+10] = x[header+1:header+1+10]
        with self.assertRaises(Louisiana64Error):
            _la_positions(bytes(x))

    def test_foreign_state_source_does_not_count_for_louisiana(self):
        x=bytearray(invented_64_rows())
        header=struct.unpack_from("<H",x,8)[0]
        x[header+1:header+3]=b"35"
        with self.assertRaises(Louisiana64Error):
            _la_positions(bytes(x))

    def test_malformed_geoid_rejected(self):
        x=bytearray(invented_64_rows())
        header=struct.unpack_from("<H",x,8)[0]
        x[header+1+2+3:header+1+2+3+5]=b"22XX1"
        with self.assertRaises(Louisiana64Error):
            _la_positions(bytes(x))

    def test_truncated_original_dbf_blocked(self):
        x=invented_64_rows()[:-60]
        with self.assertRaises((Louisiana64Error,ValueError)):
            _la_positions(x)


if __name__=="__main__":
    unittest.main()
