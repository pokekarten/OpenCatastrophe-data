# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests; no original provider bytes, requests, or bulk downloads."""
import hashlib
import io
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch
import unittest

from scripts.probe_hr_dgu_topographic_buildings_atom_v0 import (
    AtomMetadataError, FEED_URL, MAX_XML_BYTES, RIGHTS_TEXT, ZIP_URL,
    REVIEWED_ATOM_SHA256, REVIEWED_ATOM_UPDATED, REVIEWED_ZIP_ADVERTISED_BYTES,
    _NoRedirect, inspect_atom, main,
)


def synthetic_atom(*, rights=RIGHTS_TEXT, updated="2024-03-07T17:05:52.000000+01:00",
                   size="285995484", title=None):
    title = title or "Zgrade u INSPIRE GML 3.2.1 formatu u ETRS89/LAEA projekciji"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f'<id>{FEED_URL}</id><title>Zgrade</title><updated>{updated}</updated>'
        f'<rights>{rights}</rights>'
        '<entry><id>urn:synthetic:entry</id>'
        f'<updated>{updated}</updated><title>{title}</title>'
        f'<link href="{ZIP_URL}" rel="alternate" type="application/x-gmz" '
        f'length="{size}"/></entry></feed>'
    ).encode("utf-8")


class DguTopographicAtomMetadataTest(unittest.TestCase):
    def test_synthetic_provider_shape_never_admitted(self):
        raw = synthetic_atom()
        receipt = inspect_atom(raw)
        self.assertEqual(receipt["atom_feed_url"], FEED_URL)
        self.assertEqual(receipt["feed_original_bytes"], len(raw))
        self.assertEqual(receipt["feed_original_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt["advertised_zip_bytes_not_verified"], 285995484)
        self.assertTrue(receipt["rights_reconciliation_required"])
        self.assertTrue(receipt["distinct_product_identity_from_cadastral_wfs"])
        self.assertFalse(receipt["zip_downloaded"])
        self.assertFalse(receipt["raw_geometry_verified"])
        self.assertFalse(receipt["model_input_admitted"])
        self.assertFalse(receipt["matches_reviewed_original_feed_bytes"])
        self.assertEqual(receipt["reviewed_original_feed_sha256"], REVIEWED_ATOM_SHA256)
        self.assertEqual(receipt["atom_updated_as_declared"], REVIEWED_ATOM_UPDATED)
        self.assertEqual(receipt["advertised_zip_bytes_not_verified"], REVIEWED_ZIP_ADVERTISED_BYTES)

    def test_reject_wrong_feed_identity(self):
        raw = synthetic_atom().replace(FEED_URL.encode(), b"https://example.com/feed")
        with self.assertRaisesRegex(AtomMetadataError, "identity"):
            inspect_atom(raw)

    def test_reject_other_zip_or_origin(self):
        raw = synthetic_atom().replace(ZIP_URL.encode(), b"https://example.com/buildings.zip")
        with self.assertRaisesRegex(AtomMetadataError, "ZIP link"):
            inspect_atom(raw)

    def test_reject_missing_or_changed_rights(self):
        for raw in (
            synthetic_atom(rights="Otvorena dozvola"),
            synthetic_atom(rights=""),
            synthetic_atom().replace(b"<rights>", b"<notice>").replace(b"</rights>", b"</notice>"),
        ):
            with self.subTest(raw=raw[:150]), self.assertRaisesRegex(
                AtomMetadataError, "restriction text"
            ):
                inspect_atom(raw)

    def test_reject_missing_licence_update_timestamp(self):
        for value in ("2024-03-07", "not-a-date", "2024-03-07T17:05:52"):
            with self.subTest(value=value), self.assertRaises(AtomMetadataError):
                inspect_atom(synthetic_atom(updated=value))

    def test_reject_inconsistent_feed_entry_updates(self):
        raw = synthetic_atom().replace(
            b"<entry><id>", b"<entry><id>"
        )
        original = b"<updated>2024-03-07T17:05:52.000000+01:00</updated>"
        parts = raw.split(original)
        self.assertEqual(len(parts), 3)
        raw = original.join(parts[:2]) + b"<updated>2025-01-01T01:01:01+00:00</updated>" + parts[2]
        with self.assertRaisesRegex(AtomMetadataError, "inconsistent"):
            inspect_atom(raw)

    def test_reject_unknown_format_or_size(self):
        for raw in (
            synthetic_atom(title="GML 3.2.1 without declared projection"),
            synthetic_atom().replace(b"application/x-gmz", b"application/json"),
            synthetic_atom(size="0"),
            synthetic_atom(size="-10"),
            synthetic_atom(size="too-big"),
        ):
            with self.subTest(raw=raw[:150]), self.assertRaises(AtomMetadataError):
                inspect_atom(raw)

    def test_reject_stale_or_changed_timestamp_identity(self):
        for updated in (
            "2024-03-07T17:05:52+01:00",
            "2024-03-07T16:05:52.000000+00:00",
            "2025-03-07T17:05:52.000000+01:00",
        ):
            with self.subTest(updated=updated), self.assertRaisesRegex(
                AtomMetadataError, "timestamp drift"
            ):
                inspect_atom(synthetic_atom(updated=updated))

    def test_reject_changed_but_well_formed_advertised_size(self):
        for bytes_declared in ("285995485", "285995483", "1", "999999999999"):
            with self.subTest(size=bytes_declared), self.assertRaisesRegex(
                AtomMetadataError, "byte-size drift"
            ):
                inspect_atom(synthetic_atom(size=bytes_declared))

    def test_live_identity_requires_exact_reviewed_original_bytes(self):
        # A perfectly structured synthetic feed is NOT the original provider
        # byte identity. The live entry point must block rather than claiming
        # proof just because the metadata fields look plausible.
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch(
            "scripts.probe_hr_dgu_topographic_buildings_atom_v0.live_feed",
            return_value=synthetic_atom(),
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--live"])
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("live feed bytes differ from reviewed SHA-256", stderr.getvalue())

    def test_reject_multiple_entries(self):
        raw = synthetic_atom()
        fragment = raw.split(b"<entry>")[1].split(b"</entry>")[0]
        raw = raw.replace(b"</feed>", b"<entry>" + fragment + b"</entry></feed>")
        with self.assertRaisesRegex(AtomMetadataError, "exactly one"):
            inspect_atom(raw)

    def test_reject_xxe_exception_non_atom_oversize(self):
        for raw in (
            b'<!DOCTYPE feed [<!ENTITY injected "problem">]>' + synthetic_atom(),
            b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows/1.1"/>',
            synthetic_atom() + b" " * MAX_XML_BYTES,
        ):
            with self.subTest(raw=raw[:40]), self.assertRaises(AtomMetadataError):
                inspect_atom(raw)

    def test_reject_redirects(self):
        with self.assertRaisesRegex(AtomMetadataError, "redirect denied"):
            _NoRedirect().redirect_request(None, None, 302, "moved", {}, "https://example.net")

    def test_publisher_zip_url_is_not_wfs(self):
        self.assertEqual(ZIP_URL.split("/")[2], "geoportal.dgu.hr")
        self.assertNotIn("uredjenazemlja", ZIP_URL)
        self.assertTrue(ZIP_URL.endswith(".zip"))


if __name__ == "__main__":
    unittest.main()
