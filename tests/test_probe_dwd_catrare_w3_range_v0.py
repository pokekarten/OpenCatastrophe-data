# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, deterministic gates for the fixed CatRaRE W3 v2026.01 range read."""
import hashlib
import unittest

from scripts.probe_dwd_catrare_w3_range_v0 import (
    DWDRangeBlocked, EXPECTED_CONTENT_RANGE, MAX_BYTES, NoRedirect,
    RANGE_HEADER, SOURCE, URL, verify_csv_prefix,
)


def synthetic_prefix():
    header = ["CatVersion", "KEY_FIELD", "Event_ID"] + [f"Col{n:02d}" for n in range(64)]
    rows = [
        ["W3_Eta_v2026_01", f"W3_Eta_{i:06d}", str(i)] + [str(i * 100 + n) for n in range(64)]
        for i in range(1, 5)
    ]
    csv_text = "\n".join([";".join(header)] + [";".join(v) for v in rows]) + "\n"
    return csv_text.encode("utf-8").ljust(MAX_BYTES, b" ")


class DWDCSVRangeTests(unittest.TestCase):
    def test_valid_immutable_original_prefix_and_sha(self):
        raw = synthetic_prefix()
        result = verify_csv_prefix(
            raw, status=206, content_range=EXPECTED_CONTENT_RANGE, media_type="application/octet-stream")
        self.assertEqual(result["source_id"], SOURCE)
        self.assertEqual(result["response_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["csv_schema_columns"], 67)
        self.assertEqual(result["complete_source_events_examined"], 3)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["provider_bytes_persisted"])

    def test_block_nonpartial_stale_file_and_wrong_media(self):
        raw = synthetic_prefix()
        for status, rng, media in [
            (200, EXPECTED_CONTENT_RANGE, "text/csv"),
            (206, "bytes 0-4095/12410600", "text/csv"),
            (206, "", "text/csv"),
            (206, EXPECTED_CONTENT_RANGE, "text/html"),
        ]:
            with self.subTest(status=status, rng=rng, media=media):
                with self.assertRaises(DWDRangeBlocked):
                    verify_csv_prefix(raw, status=status, content_range=rng, media_type=media)

    def test_no_bulk_download_and_wrong_version_or_schema(self):
        original = synthetic_prefix()
        for bad in [
            original[:-1],
            original + b"x",
            original.replace(b"W3_Eta_v2026_01", b"W3_Eta_v2025_01", 1),
            original.replace(b"KEY_FIELD", b"WRONG_COL", 1),
            original.replace(b"W3_Eta_000001", b"W3_Eta_001111", 1),
        ]:
            with self.assertRaises(DWDRangeBlocked):
                verify_csv_prefix(
                    bad, status=206, content_range=EXPECTED_CONTENT_RANGE, media_type="text/csv")

    def test_no_unreviewed_url_or_redirect():
        self.assertIn("CatRaRE_v2026.01/data/", URL)
        self.assertEqual(RANGE_HEADER, "bytes=0-4095")
        with self.assertRaises(DWDRangeBlocked):
            NoRedirect().redirect_request(None, None, 302, "move", {}, "https://other.net/")

if __name__ == "__main__":
    unittest.main()
