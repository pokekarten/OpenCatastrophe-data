# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independently synthetic ZIP archive/format negative controls for NOAA IGRA."""

import hashlib
import io
import unittest
import zipfile

from scripts.igra22_zip_original_preflight_v0 import (
    Igra22FormatError,
    MAX_ZIP_BYTES,
    screen_igra22_original_station_zip,
)
from tests.test_igra22_sounding_preflight_v0 import SID, header, level, text_block


def make_zip(*, member=f"{SID}-data.txt", body=None, other=None, compression=zipfile.ZIP_DEFLATED):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(member, text_block() if body is None else body,
                         compress_type=compression)
        if other is not None:
            archive.writestr("other.txt", other)
    return stream.getvalue()


class Igra22OriginalZipPreflightTests(unittest.TestCase):
    def test_original_zip_member_prefix_hashes_are_distinct(self):
        raw = text_block()
        original_zip = make_zip(body=raw)
        r = screen_igra22_original_station_zip(original_zip, station_id=SID)
        self.assertEqual(r["original_zip_sha256"], hashlib.sha256(original_zip).hexdigest())
        self.assertEqual(r["unzipped_member_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(r["original_zip_sha256"], r["unzipped_member_sha256"])
        self.assertEqual(r["screened_prefix_sha256"], r["unzipped_member_sha256"])
        self.assertEqual(r["screened_prefix_soundings"], 1)
        self.assertTrue(r["full_member_scientifically_screened"])
        self.assertEqual(r["commercial_cat_model_admission"], "not_admitted")
        self.assertEqual(r["neon_storage"], "storage_not_verified")

    def test_long_station_series_screens_only_bounded_prefix(self):
        raw = b"".join(text_block(h=header(day=(i % 28) + 1)) for i in range(16))
        r = screen_igra22_original_station_zip(make_zip(body=raw), station_id=SID)
        self.assertEqual(r["screened_prefix_soundings"], 12)
        self.assertEqual(r["unzipped_member_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertFalse(r["full_member_scientifically_screened"])
        self.assertNotEqual(r["screened_prefix_sha256"], r["unzipped_member_sha256"])

    def test_completed_read_ahead_is_not_misclassified_as_science_screen(self):
        # Ten near-cap soundings are screened, then the last complete record
        # is read ahead and rejected for exceeding the text budget. Byte-level
        # ZIP/member identity may be complete, but the science screen is not.
        one = text_block(h=header(levels=500), rows=[level()] * 500)
        raw = one * 11
        r = screen_igra22_original_station_zip(make_zip(body=raw), station_id=SID)
        self.assertLess(r["screened_prefix_bytes"], r["unzipped_member_bytes"])
        self.assertFalse(r["full_member_scientifically_screened"])

    def test_refuse_filename_confusion_bombs_and_bad_science(self):
        cases = [
            (b"", SID),
            (b"PK\x03\x04garbled", SID),
            (b"PK\x03\x04" + b"z" * MAX_ZIP_BYTES, SID),
            (make_zip(member="wrong-data.txt"), SID),
            (make_zip(member=f"../{SID}-data.txt"), SID),
            (make_zip(other=b"junk"), SID),
            (make_zip(body=b""), SID),
            (make_zip(body=b"not a NOAA header\n"), SID),
            (make_zip(body=text_block(h=header(sid="GBM00012345"))), SID),
            (make_zip(body=text_block(rows=[level(wspd=400000)])), SID),
            (make_zip(body=text_block(h=header(levels=3))), SID),
            (make_zip(body=b"B" * 12_582_913, compression=zipfile.ZIP_DEFLATED), SID),
            (make_zip(), "USM00072202"),
            (make_zip(), "../unsafe"),
        ]
        for raw, station_id in cases:
            with self.subTest(raw=raw[:20], station_id=station_id):
                with self.assertRaises(Igra22FormatError):
                    screen_igra22_original_station_zip(raw, station_id=station_id)


if __name__ == "__main__":
    unittest.main()
